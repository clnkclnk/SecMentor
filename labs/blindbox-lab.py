#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BlindBox 盲盒商城 - 盲注靶场
端口: 5021

设计要点:
1. 关闭所有 SQL 错误回显（统一返回"系统繁忙"）
2. 登录框: 成功/失败页面明显不同（布尔盲注入口）
3. 订单查询: 无论真假都返回"查询完成"（时间盲注入口）
4. FLAG 藏在 secrets 表，必须用盲注逐字符偷出

3枚 FLAG:
  - blind_bool_login_2026   (布尔盲注 - 登录框)
  - blind_time_order_2026   (时间盲注 - 订单查询)
  - blind_combo_vip_2026    (综合盲注 - 会员卡查询)
"""

import sqlite3
import threading
import html
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blindbox.db')

FLAGS = {
    "bool_login": "FLAG{blind_bool_login_2026}",
    "time_order": "FLAG{blind_time_order_2026}",
    "combo_vip": "FLAG{blind_combo_vip_2026}",
}

_collected = set()
_collected_lock = threading.Lock()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        role TEXT,
        phone TEXT,
        address TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        order_no TEXT UNIQUE,
        amount REAL,
        status TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vip_cards (
        id INTEGER PRIMARY KEY,
        card_no TEXT UNIQUE,
        user_id INTEGER,
        level TEXT,
        points INTEGER,
        expire_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY,
        key TEXT,
        value TEXT
    )''')

    # 只在空库时插入数据
    if c.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        users = [
            (1, 'admin', 'Adm1n#Sec2026', 'admin@blindbox.cn', 'admin', '13800001111', '北京市朝阳区盲盒路1号'),
            (2, 'alice', 'Alice@2026', 'alice@blindbox.cn', 'member', '13900002222', '上海市浦东新区盒子街2号'),
            (3, 'bob', 'B0b#Pass!', 'bob@blindbox.cn', 'member', '13700003333', '深圳市南山区拆盒巷3号'),
            (4, 'vip_user', 'V1p#Secret!', 'vip@blindbox.cn', 'vip', '13600004444', '广州市天河区隐藏款大道4号'),
        ]
        c.executemany('INSERT INTO users VALUES (?,?,?,?,?,?,?)', users)

        orders = [
            (1, 1, 'BLD20260801001', 299.00, 'paid', '2026-08-01 10:23:00'),
            (2, 1, 'BLD20260802002', 1580.00, 'shipped', '2026-08-02 14:45:00'),
            (3, 2, 'BLD20260803003', 89.00, 'paid', '2026-08-03 09:12:00'),
            (4, 3, 'BLD20260804004', 3299.00, 'delivered', '2026-08-04 16:30:00'),
            (5, 4, 'BLD20260805005', 9999.00, 'paid', '2026-08-05 20:00:00'),
        ]
        c.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)', orders)

        vip_cards = [
            (1, 'VIP20260001', 1, 'gold', 8500, '2027-12-31'),
            (2, 'VIP20260002', 2, 'silver', 3200, '2027-06-30'),
            (3, 'VIP20260003', 4, 'diamond', 50000, '2028-01-01'),
        ]
        c.executemany('INSERT INTO vip_cards VALUES (?,?,?,?,?,?)', vip_cards)

        secrets = [
            (1, 'bool_login_flag', FLAGS['bool_login']),
            (2, 'time_order_flag', FLAGS['time_order']),
            (3, 'combo_vip_flag', FLAGS['combo_vip']),
        ]
        c.executemany('INSERT INTO secrets VALUES (?,?,?)', secrets)

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def render_page(title, body, nav_active=''):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} - BlindBox 盲盒商城</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #1a1a2e; color: #eee; line-height: 1.6; }}
  nav {{ background: #16213e; padding: 15px 30px; display: flex; gap: 25px; align-items: center; border-bottom: 2px solid #0f3460; }}
  nav a {{ color: #a8b2d1; text-decoration: none; font-size: 15px; }}
  nav a:hover {{ color: #e94560; }}
  .brand {{ font-size: 20px; font-weight: 700; color: #e94560; margin-right: auto; }}
  .container {{ max-width: 900px; margin: 30px auto; padding: 0 20px; }}
  h1 {{ color: #e94560; margin-bottom: 20px; }}
  h2 {{ color: #0f3460; margin: 15px 0; color: #a8b2d1; }}
  .card {{ background: #16213e; border-radius: 10px; padding: 25px; margin-bottom: 20px; border: 1px solid #0f3460; }}
  input, button {{ padding: 10px 15px; border: 1px solid #0f3460; background: #1a1a2e; color: #eee; border-radius: 5px; font-size: 14px; }}
  input {{ width: 100%; margin-bottom: 10px; }}
  button {{ background: #e94560; border: none; cursor: pointer; color: white; font-weight: 600; }}
  button:hover {{ background: #c73650; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
  th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #0f3460; }}
  th {{ color: #e94560; }}
  .msg {{ padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
  .msg-success {{ background: #1b3a2a; border-left: 4px solid #2ecc71; }}
  .msg-error {{ background: #3a1b1b; border-left: 4px solid #e74c3c; }}
  .msg-info {{ background: #1b2a3a; border-left: 4px solid #3498db; }}
  .msg-warning {{ background: #3a301b; border-left: 4px solid #f39c12; }}
  .flag-banner {{ background: linear-gradient(135deg, #e94560, #0f3460); padding: 20px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: 700; color: white; margin-top: 15px; letter-spacing: 1px; }}
  footer {{ text-align: center; padding: 20px; color: #555; border-top: 1px solid #0f3460; margin-top: 40px; }}
  .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
  .product {{ background: #16213e; padding: 15px; border-radius: 8px; border: 1px solid #0f3460; }}
  .product h3 {{ color: #e94560; font-size: 16px; }}
  .price {{ color: #2ecc71; font-size: 18px; font-weight: 700; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; }}
  .badge-gold {{ background: #f39c12; color: #1a1a2e; }}
  .badge-silver {{ background: #95a5a6; color: #1a1a2e; }}
  .badge-diamond {{ background: #3498db; color: white; }}
</style>
</head>
<body>
<nav>
  <span class="brand"> BlindBox</span>
  <a href="/" style="{'color:#e94560;font-weight:600' if nav_active=='home' else ''}">首页</a>
  <a href="/login" style="{'color:#e94560;font-weight:600' if nav_active=='login' else ''}">登录</a>
  <a href="/order" style="{'color:#e94560;font-weight:600' if nav_active=='order' else ''}">订单查询</a>
  <a href="/vip" style="{'color:#e94560;font-weight:600' if nav_active=='vip' else ''}">会员卡</a>
  <a href="/flags" style="{'color:#e94560;font-weight:600' if nav_active=='flags' else ''}">FLAG 收集</a>
</nav>
<div class="container">{body}</div>
<footer>BlindBox 盲盒商城 &copy; 2026 | 客服热线: 400-888-BLIND</footer>
</body></html>'''


class BlindBoxHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静默日志

    def _send(self, html_content, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == '/':
            self._home()
        elif path == '/login':
            self._login_page()
        elif path == '/order':
            self._order_page()
        elif path == '/vip':
            self._vip_page()
        elif path == '/flags':
            self._show_flags()
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/login':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = parse_qs(body)
            self._do_login(params)
        elif parsed.path == '/order':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = parse_qs(body)
            self._do_order_query(params)
        elif parsed.path == '/vip':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = parse_qs(body)
            self._do_vip_query(params)
        else:
            self.send_error(404)

    def _home(self):
        body = '''<h1>欢迎来到 BlindBox 盲盒商城</h1>
        <div class="msg msg-info"> 最新活动: 隐藏款盲盒概率 UP！VIP 会员享 8 折优惠 </div>
        <div class="product-grid">
            <div class="product"><h3>星空系列盲盒</h3><p>抽取神秘宇宙主题手办</p><p class="price">¥99</p></div>
            <div class="product"><h3>赛博朋克系列</h3><p>未来科技风限定款</p><p class="price">¥159</p></div>
            <div class="product"><h3>复古机械系列</h3><p>蒸汽朋克齿轮工艺</p><p class="price">¥299</p></div>
            <div class="product"><h3>神秘隐藏款</h3><p>概率 1/144 的传说级</p><p class="price">¥999</p></div>
        </div>
        <div class="card">
            <h2>会员特权</h2>
            <p> 银卡会员: 95 折</p>
            <p> 金卡会员: 8 折 + 优先发货</p>
            <p> 钻石会员: 7 折 + 隐藏款保底 + 专属客服</p>
        </div>'''
        self._send(render_page('首页', body, 'home'))

    def _login_page(self):
        body = '''<h1>会员登录</h1>
        <div class="card">
            <form method="POST" action="/login">
                <p><label>用户名</label><br><input type="text" name="username" placeholder="输入用户名"></p>
                <p><label>密码</label><br><input type="password" name="password" placeholder="输入密码"></p>
                <button type="submit">登录</button>
            </form>
        </div>
        <div class="msg msg-info"> 还不是会员？今日注册送新手盲盒一个！</div>'''
        self._send(render_page('登录', body, 'login'))

    def _do_login(self, params):
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        conn = get_db()
        result = ''
        try:
            # 漏洞点：字符串拼接
            sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            row = conn.execute(sql).fetchone()
            if row:
                role_label = {'admin': '管理员', 'member': '普通会员', 'vip': 'VIP 会员'}.get(row['role'], '未知')
                result = f'''<div class="msg msg-success"> 登录成功！欢迎回来，{html.escape(row['username'])}（{role_label}） </div>
                <div class="card">
                    <h2>账户信息</h2>
                    <table>
                        <tr><th>用户名</th><td>{html.escape(row['username'])}</td></tr>
                        <tr><th>邮箱</th><td>{html.escape(row['email'])}</td></tr>
                        <tr><th>手机</th><td>{html.escape(row['phone'])}</td></tr>
                        <tr><th>地址</th><td>{html.escape(row['address'])}</td></tr>
                        <tr><th>等级</th><td>{html.escape(role_label)}</td></tr>
                    </table>
                </div>'''
                # 检查是否用盲注拿到了 flag
                if 'bool_login' not in _collected:
                    # 只有真正查到 secrets 表的 bool_login_flag 才算
                    # 这里用一个侧面检测：如果 SQL 里包含 secrets 相关子查询且成功
                    lowered = sql.lower()
                    if 'secrets' in lowered and 'bool_login' in lowered:
                        _collected.add('bool_login')
                        result += f'<div class="flag-banner">{FLAGS["bool_login"]}</div>'
            else:
                # 失败页面 - 和成功页面明显不同
                result = '<div class="msg msg-error"> 用户名或密码错误，请重试 </div>'
        except Exception:
            # 关键：不返回任何 SQL 错误信息！只返回通用提示
            result = '<div class="msg msg-warning"> 系统繁忙，请稍后再试 </div>'
        conn.close()
        body = f'<h1>登录结果</h1>{result}'
        self._send(render_page('登录', body, 'login'))

    def _order_page(self):
        body = '''<h1>订单查询</h1>
        <div class="card">
            <form method="POST" action="/order">
                <p><label>订单号</label><br><input type="text" name="order_no" placeholder="例如 BLD20260801001"></p>
                <button type="submit">查询</button>
            </form>
        </div>
        <div class="msg msg-info"> 输入订单号查询物流状态。查询完成后会显示"查询完成" </div>'''
        self._send(render_page('订单查询', body, 'order'))

    def _do_order_query(self, params):
        order_no = params.get('order_no', [''])[0]
        conn = get_db()
        result = ''
        try:
            # 漏洞点：字符串拼接
            sql = f"SELECT * FROM orders WHERE order_no = '{order_no}'"
            t0 = time.time()
            row = conn.execute(sql).fetchone()
            elapsed = time.time() - t0
            # 关键设计：无论查到没查到，都返回完全相同的页面
            # 用户无法通过页面内容判断真假，只能靠响应时间
            result = '<div class="msg msg-info"> 查询完成，订单正在处理中 </div>'
            # 时间盲注检测：响应时间 > 2秒 + SQL 包含对 secrets 表的子查询
            lowered = sql.lower()
            if elapsed > 1.5 and 'secrets' in lowered:
                if 'time_order' not in _collected:
                    _collected.add('time_order')
                    result += f'<div class="flag-banner">{FLAGS["time_order"]}</div>'
        except Exception:
            # 不回显错误，保持和成功时完全一样的页面
            result = '<div class="msg msg-info"> 查询完成，订单正在处理中 </div>'
        conn.close()
        body = f'<h1>订单查询结果</h1>{result}'
        self._send(render_page('订单查询', body, 'order'))

    def _vip_page(self):
        body = '''<h1>会员卡查询</h1>
        <div class="card">
            <form method="POST" action="/vip">
                <p><label>卡号</label><br><input type="text" name="card_no" placeholder="例如 VIP20260001"></p>
                <button type="submit">查询</button>
            </form>
        </div>
        <div class="msg msg-info"> VIP 会员专享：查询会员卡积分与等级 </div>'''
        self._send(render_page('会员卡', body, 'vip'))

    def _do_vip_query(self, params):
        card_no = params.get('card_no', [''])[0]
        conn = get_db()
        result = ''
        try:
            sql = f"SELECT * FROM vip_cards WHERE card_no = '{card_no}'"
            row = conn.execute(sql).fetchone()
            if row:
                level_label = {'gold': '金卡', 'silver': '银卡', 'diamond': '钻石卡'}.get(row['level'], '未知')
                badge_class = f'badge-{row["level"]}'
                result = f'''<div class="msg msg-success"> 会员卡有效 </div>
                <div class="card">
                    <h2>卡片信息 <span class="badge {badge_class}">{html.escape(level_label)}</span></h2>
                    <table>
                        <tr><th>卡号</th><td>{html.escape(row['card_no'])}</td></tr>
                        <tr><th>等级</th><td>{html.escape(level_label)}</td></tr>
                        <tr><th>积分</th><td>{row['points']}</td></tr>
                        <tr><th>到期日</th><td>{html.escape(row['expire_at'])}</td></tr>
                    </table>
                </div>'''
            else:
                result = '<div class="msg msg-error"> 会员卡无效或不存在 </div>'
            # 综合盲注检测
            lowered = sql.lower()
            if 'secrets' in lowered and 'combo_vip' in lowered:
                if 'combo_vip' not in _collected:
                    _collected.add('combo_vip')
                    result += f'<div class="flag-banner">{FLAGS["combo_vip"]}</div>'
        except Exception:
            result = '<div class="msg msg-warning"> 系统繁忙，请稍后再试 </div>'
        conn.close()
        body = f'<h1>会员卡查询结果</h1>{result}'
        self._send(render_page('会员卡', body, 'vip'))

    def _show_flags(self):
        with _collected_lock:
            flags = list(_collected)
        body = '<h1>FLAG 收集进度</h1>'
        if not flags:
            body += '<div class="msg msg-info"> 还没有收集到任何 FLAG，继续探索吧！</div>'
        else:
            body += f'<div class="msg msg-success"> 已收集 {len(flags)}/3 枚 FLAG </div>'
            for f in flags:
                body += f'<div class="flag-banner">{FLAGS[f]}</div>'
        body += '<div class="card"><h2>提示</h2><p> 这里的 FLAG 不会直接显示在页面上 </p><p> 你需要用盲注技术，从 secrets 表里把它们"问"出来 </p><p> 每个功能点的"信号"不同，需要不同的盲注策略 </p></div>'
        self._send(render_page('FLAG 收集', body, 'flags'))


def main():
    init_db()
    port = 5021
    server = HTTPServer(('127.0.0.1', port), BlindBoxHandler)
    print(f"[*] BlindBox 盲盒商城启动: http://127.0.0.1:{port}")
    print(f"[*] 3 枚 FLAG 藏在 secrets 表，需要盲注偷出")
    print(f"[*] 功能点: 登录 / 订单查询 / 会员卡查询")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 关闭服务")
        server.server_close()


if __name__ == '__main__':
    main()
