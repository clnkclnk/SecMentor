#!/usr/bin/env python3
"""
TechShop 电子商城 — SQL 注入实战靶场
看起来像真实电商网站，藏着多个 SQL 注入点
不提示漏洞位置，用 Burp 自己找
"""
import sqlite3
import os
import html
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from socketserver import ThreadingMixIn

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'techshop.db')

_flags = {
    "search": "FLAG{sqli_search_leaked_2026}",
    "product": "FLAG{sqli_product_detail_2026}",
    "login": "FLAG{sqli_login_bypass_2026}",
}

_collected = set()
_collected_lock = threading.Lock()

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'user',
        phone TEXT,
        address TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL,
        category TEXT,
        description TEXT,
        stock INTEGER DEFAULT 100
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        total_price REAL,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT,
        value TEXT
    )''')
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        users = [
            ('admin', 'Adm1n@TechShop2026', 'admin@techshop.cn', 'admin', '13800001111', '北京市朝阳区科技路1号'),
            ('zhangsan', 'zhang123', 'zhangsan@mail.com', 'user', '13900002222', '上海市浦东新区世纪大道100号'),
            ('lisi', 'lisi456', 'lisi@mail.com', 'user', '13700003333', '广州市天河区珠江新城88号'),
            ('wangwu', 'wang789', 'wangwu@mail.com', 'user', '13600004444', '深圳市南山区科技园路66号'),
            ('alice', 'alice2026', 'alice@techshop.cn', 'manager', '13500005555', '杭州市西湖区文三路200号'),
        ]
        c.executemany('INSERT INTO users (username,password,email,role,phone,address) VALUES (?,?,?,?,?,?)', users)
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        prods = [
            ('MacBook Pro 14"', 14999, '电脑', 'Apple M3 Pro 芯片，18GB 内存，512GB 存储', 50),
            ('iPhone 16 Pro', 8999, '手机', 'A18 Pro 芯片，钛金属设计', 200),
            ('华为 Mate 60 Pro', 6999, '手机', '麒麟9000S，卫星通话', 150),
            ('AirPods Pro 2', 1899, '配件', '主动降噪，自适应通透模式', 300),
            ('机械键盘 K8 Pro', 599, '配件', 'Keychron 87键，蓝牙/有线双模', 500),
            ('4K 显示器 27"', 2499, '电脑', 'IPS 面板，100% sRGB，Type-C 65W', 80),
            ('无线鼠标 MX3', 499, '配件', '罗技旗舰，多设备切换', 400),
            ('Python 编程入门', 69, '书籍', '从零开始学 Python，第三版', 1000),
            ('Web 安全实战', 89, '书籍', '渗透测试方法论与实战案例', 800),
            ('降噪耳机 WH-1000', 2499, '配件', '索尼旗舰降噪，30小时续航', 120),
        ]
        c.executemany('INSERT INTO products (name,price,category,description,stock) VALUES (?,?,?,?,?)', prods)
    c.execute('SELECT COUNT(*) FROM secrets')
    if c.fetchone()[0] == 0:
        secrets = [
            ('db_password', 'TechShop_DB_R00t#2026'),
            ('api_key', 'sk-techshop-live-ak7f9b2e4d1c8a3f'),
            ('admin_backdoor', 'FLAG{sqli_product_detail_2026}'),
            ('internal_note', '搜索功能存在SQL注入漏洞，请尽快修复！'),
        ]
        c.executemany('INSERT INTO secrets (key,value) VALUES (?,?)', secrets)
    conn.commit()
    conn.close()

init_db()

STYLES = '''
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,"Microsoft YaHei",sans-serif; background:#f8fafc; color:#1e293b; min-height:100vh; }
nav { background:#1e293b; color:#fff; padding:12px 30px; display:flex; align-items:center; gap:30px; }
nav .brand { font-size:1.3em; font-weight:600; }
nav a { color:#94a3b8; text-decoration:none; font-size:0.95em; }
nav a:hover { color:#fff; }
.container { max-width:1000px; margin:0 auto; padding:20px; }
h1 { font-size:1.5em; margin-bottom:20px; }
h2 { font-size:1.2em; margin:20px 0 10px; }
.card { background:#fff; border-radius:10px; padding:20px; margin-bottom:15px; border:1px solid #e2e8f0; }
.product-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:15px; }
.product-card { background:#fff; border-radius:10px; padding:18px; border:1px solid #e2e8f0; }
.product-card h3 { font-size:1em; margin-bottom:8px; }
.product-card .price { color:#dc2626; font-size:1.2em; font-weight:600; }
.product-card .cat { color:#64748b; font-size:0.85em; }
.product-card a { color:#2563eb; text-decoration:none; font-size:0.9em; }
input[type=text],input[type=password] { padding:10px 14px; border:1px solid #cbd5e1; border-radius:6px; font-size:1em; width:100%; max-width:350px; }
button { padding:10px 20px; background:#2563eb; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:1em; }
button:hover { background:#1d4ed8; }
.search-bar { display:flex; gap:10px; margin-bottom:20px; }
.search-bar input { flex:1; }
.msg { padding:12px 16px; border-radius:6px; margin:10px 0; }
.msg-error { background:#fef2f2; color:#991b1b; border-left:3px solid #dc2626; }
.msg-success { background:#f0fdf4; color:#166534; border-left:3px solid #22c55e; }
.msg-info { background:#eff6ff; color:#1e40af; border-left:3px solid #3b82f6; }
table { width:100%; border-collapse:collapse; margin:10px 0; font-size:0.9em; }
th { background:#f1f5f9; padding:8px 12px; text-align:left; font-weight:600; }
td { padding:8px 12px; border-bottom:1px solid #e2e8f0; }
.flag-banner { background:linear-gradient(135deg,#065f46,#047857); color:#6ee7b7; padding:18px; border-radius:10px; text-align:center; font-size:1.1em; font-weight:600; margin:15px 0; }
footer { text-align:center; color:#94a3b8; margin-top:30px; padding:20px; font-size:0.85em; }
'''

def render_page(title, body, nav_active='home'):
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - TechShop</title><style>{STYLES}</style></head>
<body>
<nav>
  <span class="brand">TechShop</span>
  <a href="/" style="{'color:#fff;font-weight:600' if nav_active=='home' else ''}">首页</a>
  <a href="/search" style="{'color:#fff;font-weight:600' if nav_active=='search' else ''}">搜索</a>
  <a href="/login" style="{'color:#fff;font-weight:600' if nav_active=='login' else ''}">登录</a>
</nav>
<div class="container">{body}</div>
<footer>TechShop &copy; 2026 | 客服电话: 400-123-4567</footer>
</body></html>'''

class TechShopHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            self._home()
        elif path == '/search':
            self._search(params)
        elif path == '/product':
            self._product(params)
        elif path == '/login':
            self._login_page()
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
        else:
            self.send_error(404)

    def _home(self):
        conn = get_db()
        rows = conn.execute('SELECT id,name,price,category FROM products ORDER BY id LIMIT 10').fetchall()
        conn.close()
        cards = ''
        for r in rows:
            cards += f'''<div class="product-card">
                <h3>{html.escape(r['name'])}</h3>
                <div class="price">&yen;{r['price']:.0f}</div>
                <div class="cat">{html.escape(r['category'])}</div>
                <a href="/product?id={r['id']}">查看详情</a>
            </div>'''
        body = f'<h1>热门商品</h1><div class="product-grid">{cards}</div>'
        self._send(render_page('首页', body, 'home'))

    def _search(self, params):
        q = params.get('q', [''])[0]
        result = ''
        if q:
            conn = get_db()
            try:
                sql = f"SELECT id,name,price,category FROM products WHERE name LIKE '%{q}%' OR category LIKE '%{q}%'"
                rows = conn.execute(sql).fetchall()
                if rows:
                    cards = ''
                    for r in rows:
                        cards += f'''<div class="product-card">
                            <h3>{html.escape(str(r['name']))}</h3>
                            <div class="price">&yen;{r['price']:.0f}</div>
                            <div class="cat">{html.escape(str(r['category']))}</div>
                            <a href="/product?id={r['id']}">查看详情</a>
                        </div>'''
                    result = f'<div class="msg msg-success">找到 {len(rows)} 件商品</div><div class="product-grid">{cards}</div>'
                else:
                    result = '<div class="msg msg-info">未找到匹配商品</div>'
            except Exception as e:
                result = f'<div class="msg msg-error">查询出错: {html.escape(str(e))}</div>'
            conn.close()
        body = f'''<h1>搜索商品</h1>
        <form method="GET" action="/search" class="search-bar">
            <input type="text" name="q" value="{html.escape(q)}" placeholder="搜索商品名称或分类...">
            <button type="submit">搜索</button>
        </form>
        {result}'''
        self._send(render_page('搜索', body, 'search'))

    def _product(self, params):
        pid = params.get('id', [''])[0]
        result = ''
        if pid:
            conn = get_db()
            try:
                sql = f"SELECT * FROM products WHERE id = {pid}"
                row = conn.execute(sql).fetchone()
                if row:
                    result = f'''<div class="card">
                        <h2>{html.escape(row['name'])}</h2>
                        <p style="color:#dc2626;font-size:1.3em;font-weight:600">&yen;{row['price']:.0f}</p>
                        <p style="color:#64748b">分类: {html.escape(row['category'])}</p>
                        <p style="margin-top:10px">{html.escape(row['description'])}</p>
                        <p style="color:#64748b;margin-top:10px">库存: {row['stock']} 件</p>
                    </div>'''
                    # Check if secrets table was accessed
                    try:
                        sec = conn.execute(f"SELECT * FROM secrets WHERE id = {pid}").fetchall()
                        if sec:
                            for s in sec:
                                if 'FLAG' in str(s['value']) or 'flag' in str(s['value']).lower():
                                    with _collected_lock:
                                        _collected.add('product')
                                    result += f'''<div class="flag-banner">FLAG 发现: {html.escape(s['value'])}</div>'''
                    except: pass
                else:
                    result = '<div class="msg msg-info">商品不存在</div>'
            except Exception as e:
                result = f'<div class="msg msg-error">查询出错: {html.escape(str(e))}</div>'
            conn.close()
        body = f'<h1>商品详情</h1>{result}'
        self._send(render_page('商品详情', body, 'home'))

    def _login_page(self):
        body = '''<h1>用户登录</h1>
        <div class="card">
            <form method="POST" action="/login">
                <p style="margin-bottom:10px"><label>用户名</label><br><input type="text" name="username" placeholder="请输入用户名"></p>
                <p style="margin-bottom:10px"><label>密码</label><br><input type="password" name="password" placeholder="请输入密码"></p>
                <button type="submit">登录</button>
            </form>
        </div>'''
        self._send(render_page('登录', body, 'login'))

    def _do_login(self, params):
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        conn = get_db()
        result = ''
        try:
            sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            row = conn.execute(sql).fetchone()
            if row:
                role = '管理员' if row['role'] == 'admin' else '普通用户'
                result = f'''<div class="msg msg-success">登录成功！欢迎，{html.escape(row['username'])}（{role}）</div>
                <div class="card">
                    <h2>用户信息</h2>
                    <table><tr><th>字段</th><th>值</th></tr>
                    <tr><td>用户名</td><td>{html.escape(row['username'])}</td></tr>
                    <tr><td>邮箱</td><td>{html.escape(row['email'])}</td></tr>
                    <tr><td>手机</td><td>{html.escape(row['phone'])}</td></tr>
                    <tr><td>地址</td><td>{html.escape(row['address'])}</td></tr>
                    <tr><td>角色</td><td>{html.escape(row['role'])}</td></tr>
                    </table>
                </div>'''
                if row['role'] == 'admin':
                    with _collected_lock:
                        _collected.add('login')
                    result += f'<div class="flag-banner">{_flags["login"]}</div>'
            else:
                result = '<div class="msg msg-error">用户名或密码错误</div>'
        except Exception as e:
            result = f'<div class="msg msg-error">系统错误: {html.escape(str(e))}</div>'
        conn.close()
        body = f'<h1>登录结果</h1>{result}'
        self._send(render_page('登录', body, 'login'))

    def _show_flags(self):
        with _collected_lock:
            flags = list(_collected)
        body = '<h1>已收集的 FLAG</h1>'
        if not flags:
            body += '<div class="msg msg-info">还没有收集到任何 FLAG，继续探索吧！</div>'
        else:
            for f in flags:
                body += f'<div class="flag-banner">{_flags[f]}</div>'
        body += f'<p style="color:#64748b;margin-top:10px">已收集 {len(flags)}/3 枚 FLAG</p>'
        self._send(render_page('FLAG 收集', body))

    def _send(self, html_content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def main():
    port = 5020
    server = ThreadedHTTPServer(('127.0.0.1', port), TechShopHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║   TechShop 电子商城 — SQL 注入实战靶场        ║
║                                              ║
║   http://127.0.0.1:{port}                    ║
║                                              ║
║   3 枚 FLAG 藏在网站里，自己找               ║
║   /flags 查看 FLAG 收集进度                  ║
║                                              ║
║   提示: 挂 Burp 代理，正常逛网站             ║
║   重点看参数，用推理链判断该试什么             ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 靶场已停止")
        server.server_close()

if __name__ == '__main__':
    main()
