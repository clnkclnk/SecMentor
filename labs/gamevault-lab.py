"""
GameVault - 游戏充值平台
条件竞争进阶靶场
端口 5025

5 个功能，4 个 FLAG：
  1. 提现       — TOCTOU 数值检查
  2. 兑换优惠券  — TOCTOU 状态检查
  3. 转账到储蓄  — Lost Update（读-改-写非原子）
  4. 每日签到    — TOCTOU 状态检查
  5. 限时抢购    — 原子操作（安全，不可竞争）

竞争窗口：100ms（浏览器手动点击几乎不可能成功，需要 Python 并发脚本）
"""

import sqlite3
import time
import os
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

FLAG1 = os.environ.get('GAMEVAULT_FLAG1', 'FLAG{race_withdraw_overspend_2026}')
FLAG2 = os.environ.get('GAMEVAULT_FLAG2', 'FLAG{race_coupon_reuse_2026}')
FLAG3 = os.environ.get('GAMEVAULT_FLAG3', 'FLAG{race_transfer_lost_update_2026}')
FLAG4 = os.environ.get('GAMEVAULT_FLAG4', 'FLAG{race_checkin_multi_2026}')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gamevault.db')


def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=5000")
    return db


def init_db(reset=False):
    db = get_db()
    if reset:
        db.executescript('''
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS coupons;
            DROP TABLE IF EXISTS stock;
            DROP TABLE IF EXISTS transfers;
            DROP TABLE IF EXISTS log;
        ''')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 100,
            savings INTEGER DEFAULT 0,
            last_checkin TEXT,
            checkin_count INTEGER DEFAULT 0,
            flag1 TEXT, flag2 TEXT, flag3 TEXT, flag4 TEXT
        );
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE,
            reward INTEGER,
            used INTEGER DEFAULT 0,
            redeem_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY,
            item TEXT,
            total INTEGER,
            sold INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY,
            amount INTEGER,
            balance_before INTEGER,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY,
            action TEXT,
            detail TEXT,
            created_at REAL
        );
    ''')
    count = db.execute("SELECT COUNT(*) as c FROM users").fetchone()
    if count['c'] == 0:
        db.execute("INSERT INTO users (username, coins) VALUES ('player', 100)")
        db.execute("INSERT INTO coupons (code, reward) VALUES ('GAME100', 100)")
        db.execute("INSERT INTO coupons (code, reward) VALUES ('VIP50', 50)")
        db.execute("INSERT INTO stock (item, total, sold) VALUES ('gpu', 3, 0)")
    db.commit()
    db.close()


init_db()

BASE_HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>GameVault - 游戏充值平台</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #1a1a2e; color: #e0e0e0; }
.nav { background: #16213e; padding: 16px 40px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #534AB7; }
.nav h1 { color: #AFA9EC; font-size: 20px; }
.nav a { color: #AFA9EC; text-decoration: none; margin-left: 20px; font-size: 14px; }
.container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
.card { background: #16213e; border-radius: 12px; padding: 24px; margin-bottom: 20px; border: 1px solid #2C2C4A; }
.card h2 { font-size: 16px; margin-bottom: 16px; color: #AFA9EC; }
.wallet { display: flex; gap: 60px; }
.wallet-item { text-align: center; }
.wallet-value { font-size: 36px; font-weight: bold; color: #fff; }
.wallet-label { font-size: 12px; color: #888; margin-top: 4px; }
.action { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #2C2C4A; }
.action:last-child { border-bottom: none; }
.action-info { flex: 1; }
.action-name { font-size: 14px; font-weight: 500; color: #fff; }
.action-desc { font-size: 12px; color: #888; margin-top: 4px; }
input[type=text], input[type=number] { background: #1a1a2e; border: 1px solid #534AB7; color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 13px; width: 100px; }
.btn { background: #534AB7; color: #fff; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn:hover { background: #7F77DD; }
.btn:disabled { background: #3C3C5A; cursor: not-allowed; }
.msg { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.msg-success { background: #1a3a2e; color: #5DCAA5; }
.msg-error { background: #3a1a1a; color: #F09595; }
.msg-info { background: #1a2a3a; color: #85B7EB; }
.flag-banner { background: #534AB7; color: #fff; padding: 16px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; margin: 16px 0; animation: pulse 1s; }
@keyframes pulse { 0% { transform: scale(0.9); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
.flags { display: flex; gap: 10px; margin-top: 12px; }
.flag-item { flex: 1; padding: 12px; border-radius: 8px; text-align: center; font-size: 12px; }
.flag-done { background: #1a3a2e; color: #5DCAA5; border: 1px solid #0F6E56; }
.flag-pending { background: #1a1a2e; color: #666; border: 1px solid #2C2C4A; }
.coupon-code { background: #1a1a2e; padding: 3px 8px; border-radius: 4px; font-family: Consolas, monospace; color: #AFA9EC; border: 1px solid #2C2C4A; }
.log-entry { font-size: 12px; color: #888; padding: 5px 0; border-bottom: 1px solid #2C2C4A; }
.log-entry:last-child { border-bottom: none; }
.stock-bar { width: 100%; height: 6px; background: #2C2C4A; border-radius: 3px; margin-top: 6px; }
.stock-fill { height: 100%; background: #534AB7; border-radius: 3px; transition: width 0.3s; }
</style>
</head>
<body>
<div class="nav">
    <h1>GameVault</h1>
    <div>
        <a href="/">首页</a>
        <a href="/reset">重置</a>
    </div>
</div>
<div class="container">
    {content}
</div>
</body>
</html>'''


def render_page(content):
    return render_template_string(BASE_HTML.replace('{content}', content))


@app.route('/')
def index():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    stock = db.execute("SELECT * FROM stock WHERE item='gpu'").fetchone()
    coupons = db.execute("SELECT * FROM coupons WHERE used=0").fetchall()
    logs = db.execute("SELECT * FROM log ORDER BY id DESC LIMIT 15").fetchall()

    flag1 = user['flag1'] is not None
    flag2 = user['flag2'] is not None
    flag3 = user['flag3'] is not None
    flag4 = user['flag4'] is not None

    today = time.strftime('%Y-%m-%d')
    checked_in = user['last_checkin'] == today

    stock_pct = (stock['sold'] / stock['total']) * 100 if stock['total'] > 0 else 100

    coupon_html = ", ".join(
        f"<span class='coupon-code'>{c['code']}</span> ({c['reward']}积分)"
        for c in coupons
    ) if coupons else "暂无可用优惠券"

    log_html = "".join(
        f"<div class='log-entry'>{time.strftime('%H:%M:%S', time.localtime(l['created_at']))} - {l['action']} - {l['detail']}</div>"
        for l in logs
    ) if logs else "<div class='log-entry' style='color:#555'>暂无记录</div>"

    html = f'''
    <div class="card">
        <div class="wallet">
            <div class="wallet-item">
                <div class="wallet-value">{user['coins']}</div>
                <div class="wallet-label">积分余额</div>
            </div>
            <div class="wallet-item">
                <div class="wallet-value">{user['savings']}</div>
                <div class="wallet-label">储蓄账户</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>功能大厅</h2>

        <div class="action">
            <div class="action-info">
                <div class="action-name">提现</div>
                <div class="action-desc">将积分提现到外部账户</div>
            </div>
            <form method="POST" action="/withdraw" style="display:flex;gap:8px;align-items:center">
                <input type="number" name="amount" placeholder="金额" value="100" min="1" style="width:80px">
                <button class="btn" type="submit">提现</button>
            </form>
        </div>

        <div class="action">
            <div class="action-info">
                <div class="action-name">转账到储蓄</div>
                <div class="action-desc">将 80 积分转入储蓄账户</div>
            </div>
            <form method="POST" action="/transfer">
                <button class="btn" type="submit">转入 80</button>
            </form>
        </div>

        <div class="action">
            <div class="action-info">
                <div class="action-name">每日签到</div>
                <div class="action-desc">{"今日已签到" if checked_in else "签到可获得 50 积分"}</div>
            </div>
            <form method="POST" action="/checkin">
                <button class="btn" type="submit" {"disabled" if checked_in else ""}>签到</button>
            </form>
        </div>

        <div class="action">
            <div class="action-info">
                <div class="action-name">兑换优惠券</div>
                <div class="action-desc">可用: {coupon_html}</div>
            </div>
            <form method="POST" action="/redeem" style="display:flex;gap:8px;align-items:center">
                <input type="text" name="code" placeholder="输入码" style="width:100px">
                <button class="btn" type="submit">兑换</button>
            </form>
        </div>

        <div class="action">
            <div class="action-info">
                <div class="action-name">限时抢购 - GPU</div>
                <div class="action-desc">限量 {stock['total']} 件，已售 {stock['sold']} 件</div>
                <div class="stock-bar"><div class="stock-fill" style="width:{stock_pct}%"></div></div>
            </div>
            <form method="POST" action="/flashbuy">
                <button class="btn" type="submit" {"disabled" if stock['sold'] >= stock['total'] else ""}>抢购</button>
            </form>
        </div>
    </div>

    <div class="card">
        <h2>FLAG 收集</h2>
        <div class="flags">
            <div class="{"flag-done" if flag1 else "flag-pending"} flag-item">FLAG 1<br>{"已获得" if flag1 else "未获得"}</div>
            <div class="{"flag-done" if flag2 else "flag-pending"} flag-item">FLAG 2<br>{"已获得" if flag2 else "未获得"}</div>
            <div class="{"flag-done" if flag3 else "flag-pending"} flag-item">FLAG 3<br>{"已获得" if flag3 else "未获得"}</div>
            <div class="{"flag-done" if flag4 else "flag-pending"} flag-item">FLAG 4<br>{"已获得" if flag4 else "未获得"}</div>
        </div>
    </div>

    <div class="card">
        <h2>活动记录</h2>
        {log_html}
    </div>
    '''

    if flag1:
        html += f'<div class="flag-banner">{FLAG1}</div>'
    if flag2:
        html += f'<div class="flag-banner">{FLAG2}</div>'
    if flag3:
        html += f'<div class="flag-banner">{FLAG3}</div>'
    if flag4:
        html += f'<div class="flag-banner">{FLAG4}</div>'

    db.close()
    return render_page(html)


@app.route('/withdraw', methods=['POST'])
def withdraw():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()

    try:
        amount = int(request.form.get('amount', 0))
    except ValueError:
        db.close()
        return render_page('<div class="msg msg-error">请输入有效金额</div><a href="/" class="btn">返回</a>')

    if amount <= 0:
        db.close()
        return render_page('<div class="msg msg-error">金额必须大于 0</div><a href="/" class="btn">返回</a>')

    if user['coins'] < amount:
        db.close()
        return render_page(f'<div class="msg msg-error">余额不足！当前 {user["coins"]}，需要 {amount}</div><a href="/" class="btn">返回</a>')

    time.sleep(0.1)

    db.execute("UPDATE users SET coins = coins - ? WHERE id=1", (amount,))
    db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
               ('提现', f'-{amount}', time.time()))
    db.commit()

    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    if user['coins'] < 0:
        db.execute("UPDATE users SET flag1 = ? WHERE id=1", (FLAG1,))
        db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
                   ('FLAG', 'FLAG1 已获得', time.time()))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/transfer', methods=['POST'])
def transfer():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    amount = 80

    if user['coins'] < amount:
        db.close()
        return render_page(f'<div class="msg msg-error">余额不足！需要 {amount} 积分</div><a href="/" class="btn">返回</a>')

    time.sleep(0.1)

    old_coins = user['coins']
    new_coins = old_coins - amount
    db.execute("UPDATE users SET coins = ? WHERE id=1", (new_coins,))
    db.execute("UPDATE users SET savings = savings + ? WHERE id=1", (amount,))
    db.execute("INSERT INTO transfers (amount, balance_before, created_at) VALUES (?, ?, ?)",
               (amount, old_coins, time.time()))
    db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
               ('转账到储蓄', f'-{amount}', time.time()))
    db.commit()

    raced = db.execute(
        "SELECT balance_before, COUNT(*) as c FROM transfers GROUP BY balance_before HAVING c > 1"
    ).fetchall()
    if raced:
        db.execute("UPDATE users SET flag3 = ? WHERE id=1", (FLAG3,))
        db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
                   ('FLAG', 'FLAG3 已获得', time.time()))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/redeem', methods=['POST'])
def redeem():
    db = get_db()
    code = request.form.get('code', '').strip().upper()

    coupon = db.execute("SELECT * FROM coupons WHERE code=?", (code,)).fetchone()
    if not coupon:
        db.close()
        return render_page('<div class="msg msg-error">优惠券码无效</div><a href="/" class="btn">返回</a>')

    if coupon['used']:
        db.close()
        return render_page('<div class="msg msg-error">优惠券已使用</div><a href="/" class="btn">返回</a>')

    time.sleep(0.1)

    db.execute("UPDATE coupons SET used=1, redeem_count = redeem_count + 1 WHERE code=?", (code,))
    db.execute("UPDATE users SET coins = coins + ? WHERE id=1", (coupon['reward'],))
    db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
               ('兑换', f'{code} +{coupon["reward"]}', time.time()))
    db.commit()

    coupon = db.execute("SELECT * FROM coupons WHERE code=?", (code,)).fetchone()
    if coupon['redeem_count'] >= 2:
        db.execute("UPDATE users SET flag2 = ? WHERE id=1", (FLAG2,))
        db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
                   ('FLAG', 'FLAG2 已获得', time.time()))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/checkin', methods=['POST'])
def checkin():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    today = time.strftime('%Y-%m-%d')

    if user['last_checkin'] == today:
        db.close()
        return render_page('<div class="msg msg-error">今日已签到</div><a href="/" class="btn">返回</a>')

    time.sleep(0.1)

    db.execute("UPDATE users SET coins = coins + 50, last_checkin = ?, checkin_count = checkin_count + 1 WHERE id=1",
               (today,))
    db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
               ('签到', '+50', time.time()))
    db.commit()

    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    if user['checkin_count'] >= 2:
        db.execute("UPDATE users SET flag4 = ? WHERE id=1", (FLAG4,))
        db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
                   ('FLAG', 'FLAG4 已获得', time.time()))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/flashbuy', methods=['POST'])
def flashbuy():
    db = get_db()

    cursor = db.execute("UPDATE stock SET sold = sold + 1 WHERE item='gpu' AND sold < total")

    if cursor.rowcount == 0:
        db.close()
        return render_page('<div class="msg msg-error">已售罄！</div><a href="/" class="btn">返回</a>')

    db.execute("INSERT INTO log (action, detail, created_at) VALUES (?, ?, ?)",
               ('抢购', 'GPU x1', time.time()))
    db.commit()

    db.close()
    return redirect('/')


@app.route('/reset')
def reset():
    init_db(reset=True)
    return redirect('/')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5025, debug=False, threaded=True)
