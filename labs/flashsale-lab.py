"""
FlashSale - 闪购商城靶场
条件竞争（Race Condition）练习
端口 5024

3 个 FLAG：
1. 积分竞争 — 余额变负
2. 限购竞争 — 限购 1 件但买了多件
3. 限量竞争 — 限量 5 件但卖出更多
"""

import sqlite3
import time
import os
from flask import Flask, request, render_template_string, redirect, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'flashsale_dev_2026'

FLAG1 = os.environ.get('FLASHSALE_FLAG1', 'FLAG{race_balance_negative_2026}')
FLAG2 = os.environ.get('FLASHSALE_FLAG2', 'FLAG{race_limit_bypass_2026}')
FLAG3 = os.environ.get('FLASHSALE_FLAG3', 'FLAG{race_stock_oversold_2026}')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flashsale.db')


def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def init_db(reset=False):
    db = get_db()
    if reset:
        db.executescript('''
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS purchases;
            DROP TABLE IF EXISTS stock;
            DROP TABLE IF EXISTS lottery;
        ''')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            points INTEGER DEFAULT 100,
            flag1 TEXT,
            flag2 TEXT,
            flag3 TEXT
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT UNIQUE,
            total INTEGER,
            sold INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS lottery (
            user_id INTEGER PRIMARY KEY,
            plays INTEGER DEFAULT 0
        );
    ''')
    db.execute("INSERT INTO users (username, points) VALUES ('player', 100)")
    db.execute("INSERT INTO stock (product, total, sold) VALUES ('mega', 5, 0)")
    db.execute("INSERT INTO lottery (user_id, plays) VALUES (1, 0)")
    db.commit()
    db.close()


init_db()

BASE_HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>FlashSale 闪购商城</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f5f5; color: #333; }
.nav { background: #e63946; padding: 16px 40px; display: flex; justify-content: space-between; align-items: center; }
.nav h1 { color: #fff; font-size: 20px; }
.nav a { color: #fff; text-decoration: none; margin-left: 20px; font-size: 14px; }
.container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
.card { background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h2 { font-size: 18px; margin-bottom: 16px; color: #1d3557; }
.points-display { font-size: 36px; font-weight: bold; color: #e63946; }
.points-label { font-size: 14px; color: #888; }
.product { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid #eee; }
.product:last-child { border-bottom: none; }
.product-name { font-size: 16px; font-weight: 500; }
.product-desc { font-size: 13px; color: #888; margin-top: 4px; }
.product-price { font-size: 18px; color: #e63946; font-weight: bold; margin-right: 16px; }
.btn { background: #e63946; color: #fff; border: none; padding: 8px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn:hover { background: #c1121f; }
.btn:disabled { background: #ccc; cursor: not-allowed; }
.msg { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.msg-success { background: #d4edda; color: #155724; }
.msg-error { background: #f8d7da; color: #721c24; }
.msg-info { background: #d1ecf1; color: #0c5460; }
.flag-banner { background: #e63946; color: #fff; padding: 16px; border-radius: 8px; text-align: center; font-size: 20px; font-weight: bold; margin: 20px 0; animation: pulse 1s; }
@keyframes pulse { 0% { transform: scale(0.9); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
.stock-bar { width: 100%; height: 8px; background: #eee; border-radius: 4px; margin-top: 8px; }
.stock-fill { height: 100%; background: #e63946; border-radius: 4px; transition: width 0.3s; }
.flags { display: flex; gap: 12px; margin-top: 16px; }
 flag-item { flex: 1; padding: 12px; border-radius: 8px; text-align: center; font-size: 13px; }
.flag-done { background: #d4edda; color: #155724; }
.flag-pending { background: #f8f9fa; color: #888; }
code { background: #f1f3f5; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 13px; }
</style>
</head>
<body>
<div class="nav">
    <h1>FlashSale 闪购商城</h1>
    <div>
        <a href="/">首页</a>
        <a href="/lottery">抽奖</a>
        <a href="/reset">重置账号</a>
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
    user = db.execute("SELECT * FROM users WHERE username='player'").fetchone()
    stock = db.execute("SELECT * FROM stock WHERE product='mega'").fetchone()
    purchases = db.execute("SELECT * FROM purchases WHERE user_id=?", (user['id'],)).fetchall()

    flag1 = user['flag1'] is not None
    flag2 = user['flag2'] is not None
    flag3 = user['flag3'] is not None

    stock_pct = (stock['sold'] / stock['total']) * 100 if stock['total'] > 0 else 100

    product_a_purchases = len([p for p in purchases if p['product'] == 'A'])
    product_b_purchases = len([p for p in purchases if p['product'] == 'B'])
    product_c_purchases = len([p for p in purchases if p['product'] == 'C'])

    html = f'''
    <div class="card">
        <span class="points-label">我的积分</span><br>
        <span class="points-display">{user['points']}</span>
    </div>

    <div class="card">
        <h2>商品列表</h2>

        <div class="product">
            <div>
                <div class="product-name">商品 A - 积分商城</div>
                <div class="product-desc">100 积分/件，用积分购买</div>
            </div>
            <div style="display:flex;align-items:center">
                <span class="product-price">100 pts</span>
                <form method="POST" action="/buy_a">
                    <button class="btn" type="submit">购买</button>
                </form>
            </div>
        </div>

        <div class="product">
            <div>
                <div class="product-name">商品 B - 限购商品</div>
                <div class="product-desc">每人限购 1 件，已购买 {product_b_purchases} 件</div>
            </div>
            <div style="display:flex;align-items:center">
                <span class="product-price">免费</span>
                <form method="POST" action="/buy_b">
                    <button class="btn" type="submit" {"disabled" if product_b_purchases > 0 else ""}>领取</button>
                </form>
            </div>
        </div>

        <div class="product">
            <div>
                <div class="product-name">商品 C - 限量闪购</div>
                <div class="product-desc">全场限量 {stock['total']} 件，已售 {stock['sold']} 件</div>
                <div class="stock-bar"><div class="stock-fill" style="width:{stock_pct}%"></div></div>
            </div>
            <div style="display:flex;align-items:center">
                <span class="product-price">免费</span>
                <form method="POST" action="/buy_c">
                    <button class="btn" type="submit" {"disabled" if stock['sold'] >= stock['total'] else ""}>抢购</button>
                </form>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>购买记录</h2>
        {"".join(f"<div>商品 {p['product']} - 购买时间: {time.strftime('%H:%M:%S', time.localtime(p['created_at']))}</div>" for p in purchases) if purchases else "<div style='color:#888'>暂无购买记录</div>"}
    </div>

    <div class="card">
        <h2>FLAG 收集</h2>
        <div class="flags">
            <div class="{"flag-done" if flag1 else "flag-pending"}" style="flex:1;padding:12px;border-radius:8px;text-align:center;font-size:13px;">
                FLAG 1<br>{"已获得" if flag1 else "未获得"}
            </div>
            <div class="{"flag-done" if flag2 else "flag-pending"}" style="flex:1;padding:12px;border-radius:8px;text-align:center;font-size:13px;">
                FLAG 2<br>{"已获得" if flag2 else "未获得"}
            </div>
            <div class="{"flag-done" if flag3 else "flag-pending"}" style="flex:1;padding:12px;border-radius:8px;text-align:center;font-size:13px;">
                FLAG 3<br>{"已获得" if flag3 else "未获得"}
            </div>
        </div>
    </div>
    '''

    if flag1:
        html += f'<div class="flag-banner">{FLAG1}</div>'
    if flag2:
        html += f'<div class="flag-banner">{FLAG2}</div>'
    if flag3:
        html += f'<div class="flag-banner">{FLAG3}</div>'

    db.close()
    return render_page(html)


@app.route('/buy_a', methods=['POST'])
def buy_a():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username='player'").fetchone()

    # 检查积分
    if user['points'] < 100:
        db.close()
        return render_page('<div class="msg msg-error">积分不足！需要 100 积分。</div><a href="/" class="btn">返回</a>')

    # 模拟数据库写入延迟（这就是竞争窗口）
    time.sleep(0.5)

    # 扣减积分
    db.execute("UPDATE users SET points = points - 100 WHERE username='player'")
    db.execute("INSERT INTO purchases (user_id, product, created_at) VALUES (?, 'A', ?)", (user['id'], time.time()))
    db.commit()

    user = db.execute("SELECT * FROM users WHERE username='player'").fetchone()

    # 检查是否余额变负
    if user['points'] < 0:
        db.execute("UPDATE users SET flag1 = ? WHERE username='player'", (FLAG1,))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/buy_b', methods=['POST'])
def buy_b():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username='player'").fetchone()

    # 检查是否已购买
    count = db.execute("SELECT COUNT(*) as c FROM purchases WHERE user_id=? AND product='B'", (user['id'],)).fetchone()['c']
    if count >= 1:
        db.close()
        return render_page('<div class="msg msg-error">每人限购 1 件，您已购买过！</div><a href="/" class="btn">返回</a>')

    # 模拟延迟
    time.sleep(0.5)

    # 记录购买
    db.execute("INSERT INTO purchases (user_id, product, created_at) VALUES (?, 'B', ?)", (user['id'], time.time()))
    db.commit()

    count = db.execute("SELECT COUNT(*) as c FROM purchases WHERE user_id=? AND product='B'", (user['id'],)).fetchone()['c']
    if count >= 2:
        db.execute("UPDATE users SET flag2 = ? WHERE username='player'", (FLAG2,))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/buy_c', methods=['POST'])
def buy_c():
    db = get_db()
    stock = db.execute("SELECT * FROM stock WHERE product='mega'").fetchone()

    # 检查库存
    if stock['sold'] >= stock['total']:
        db.close()
        return render_page('<div class="msg msg-error">已售罄！</div><a href="/" class="btn">返回</a>')

    # 模拟延迟
    time.sleep(0.5)

    # 扣库存
    db.execute("UPDATE stock SET sold = sold + 1 WHERE product='mega'")
    db.execute("INSERT INTO purchases (user_id, product, created_at) VALUES (1, 'C', ?)", (time.time(),))
    db.commit()

    stock = db.execute("SELECT * FROM stock WHERE product='mega'").fetchone()
    if stock['sold'] > stock['total']:
        db.execute("UPDATE users SET flag3 = ? WHERE username='player'", (FLAG3,))
        db.commit()

    db.close()
    return redirect('/')


@app.route('/lottery')
def lottery():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username='player'").fetchone()
    lot = db.execute("SELECT * FROM lottery WHERE user_id=?", (user['id'],)).fetchone()
    db.close()

    html = f'''
    <div class="card">
        <h2>幸运抽奖</h2>
        <p style="margin-bottom:16px;color:#666">每人每天限抽 1 次。已抽 {lot['plays']} 次。</p>
        <form method="POST" action="/draw">
            <button class="btn" type="submit" {"disabled" if lot['plays'] >= 1 else ""}>抽奖</button>
        </form>
    </div>
    <a href="/" class="btn">返回首页</a>
    '''
    return render_page(html)


@app.route('/draw', methods=['POST'])
def draw():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username='player'").fetchone()
    lot = db.execute("SELECT * FROM lottery WHERE user_id=?", (user['id'],)).fetchone()

    if lot['plays'] >= 1:
        db.close()
        return render_page('<div class="msg msg-error">今天已抽过奖了！</div><a href="/lottery" class="btn">返回</a>')

    time.sleep(0.5)

    db.execute("UPDATE lottery SET plays = plays + 1 WHERE user_id=?", (user['id'],))
    db.commit()

    lot = db.execute("SELECT * FROM lottery WHERE user_id=?", (user['id'],)).fetchone()

    html = ''
    if lot['plays'] >= 2:
        html += '<div class="msg msg-success">恭喜！您抽中了特殊奖品！</div>'
        html += f'<div class="flag-banner">{FLAG3}</div>'
    elif lot['plays'] == 1:
        html += '<div class="msg msg-info">谢谢参与！</div>'

    html += '<a href="/lottery" class="btn">返回</a>'
    db.close()
    return render_page(html)


@app.route('/reset')
def reset():
    init_db(reset=True)
    return redirect('/')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5024, debug=False, threaded=True)
