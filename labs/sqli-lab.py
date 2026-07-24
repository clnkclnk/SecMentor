#!/usr/bin/env python3
"""
SQL Injection 最小化靶场 - 不需要 Docker
使用 Python + SQLite，直接运行即可体验 SQL 注入

运行方式: python sqli-lab.py
然后打开浏览器访问 http://127.0.0.1:5678
"""

import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import html

# ============ 数据库初始化（全局共享连接） ============
import tempfile
import os

# 使用临时文件数据库（跨请求共享数据）
_temp_dir = tempfile.gettempdir()
_DB_FILE = os.path.join(_temp_dir, 'sqli_lab.db')
DB_PATH = _DB_FILE

_global_conn = None
_db_lock = threading.Lock()

def get_db():
    """获取数据库连接（线程安全）"""
    global _global_conn
    with _db_lock:
        if _global_conn is None:
            _global_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            _global_conn.row_factory = sqlite3.Row
        return _global_conn

def init_db():
    """创建靶场数据库并插入测试数据"""
    conn = get_db()
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            secret TEXT
        )
    ''')

    # 创建商品表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL,
            category TEXT,
            description TEXT
        )
    ''')

    # 插入测试用户（模拟真实数据）— 只在表为空时插入
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        test_users = [
            ('admin', 'admin123', 'admin@target.com', 'admin', '管理员密码是 P@ssw0rd!'),
            ('zhangsan', 'zhang123', 'zhangsan@target.com', 'user', '张三的秘密：银行卡号 6222021234567890123'),
            ('lisi', 'lisi456', 'lisi@target.com', 'user', '李四的秘密：手机验证码永远填 123456'),
            ('wangwu', 'wang789', 'wangwu@target.com', 'user', '王五的秘密：公司内网密码 InnerSecr3t'),
            ('alice', 'alice001', 'alice@target.com', 'user', 'Alice 的秘密：VPN 密码 Vpn$ecret99'),
        ]
        cursor.executemany(
            'INSERT INTO users (username, password, email, role, secret) VALUES (?,?,?,?,?)',
            test_users
        )

    # 插入测试商品 — 只在表为空时插入
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        test_products = [
            ('iPhone 16 Pro', 8999, '电子产品', '最新款苹果手机'),
            ('华为 Mate 60', 6999, '电子产品', '国产旗舰手机'),
            ('MacBook Pro', 14999, '电脑', '专业笔记本'),
            ('机械键盘', 299, '外设', '青轴机械键盘'),
            ('无线鼠标', 149, '外设', '蓝牙5.0鼠标'),
            ('Python 入门书', 59, '书籍', '从零开始学Python'),
            ('SQL 必知必会', 79, '书籍', '数据库经典教材'),
            ('安全帽', 35, '劳保用品', '工地必备'),
        ]
        cursor.executemany(
            'INSERT INTO products (name, price, category, description) VALUES (?,?,?,?)',
            test_products
        )

    conn.commit()
    print(f"[*] 数据库初始化完成：5 个用户 + 8 个商品 ({DB_PATH})")

# 全局初始化一次
init_db()


# ============ 靶场页面 HTML ============

LAB_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SQL Injection 靶场</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: -apple-system, "Microsoft YaHei", sans-serif;
        background: #0f172a;
        color: #e2e8f0;
        min-height: 100vh;
        padding: 20px;
    }
    .container { max-width: 900px; margin: 0 auto; }
    h1 {
        text-align: center;
        color: #f8fafc;
        font-size: 1.8em;
        margin-bottom: 8px;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 0.9em;
        margin-bottom: 30px;
    }

    /* 关卡导航 */
    .level-nav {
        display: flex;
        gap: 10px;
        margin-bottom: 25px;
        flex-wrap: wrap;
        justify-content: center;
    }
    .level-btn {
        padding: 10px 20px;
        border: 2px solid #334155;
        border-radius: 8px;
        background: #1e293b;
        color: #94a3b8;
        cursor: pointer;
        font-size: 0.95em;
        transition: all 0.2s;
    }
    .level-btn:hover { border-color: #3b82f6; color: #e2e8f0; }
    .level-btn.active {
        border-color: #3b82f6;
        background: #1e3a5f;
        color: #60a5fa;
        font-weight: bold;
    }
    .level-btn.passed {
        border-color: #22c55e;
        background: #14532d;
        color: #4ade80;
    }

    /* 关卡区域 */
    .level-section {
        background: #1e293b;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid #334155;
        display: none;
    }
    .level-section.active { display: block; }

    .level-title {
        color: #f8fafc;
        font-size: 1.2em;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #334155;
    }
    .level-desc {
        color: #94a3b8;
        line-height: 1.7;
        margin-bottom: 20px;
        font-size: 0.95em;
    }
    .hint-box {
        background: #1e3a5f;
        border-left: 3px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
        font-size: 0.9em;
    }
    .hint-box strong { color: #60a5fa; }

    /* 表单 */
    .form-row {
        display: flex;
        gap: 12px;
        align-items: center;
        margin-bottom: 15px;
        flex-wrap: wrap;
    }
    label { color: #cbd5e1; min-width: 80px; }
    input[type="text"], input[type="password"] {
        flex: 1;
        min-width: 200px;
        padding: 10px 14px;
        border: 1px solid #475569;
        border-radius: 6px;
        background: #0f172a;
        color: #e2e8f0;
        font-size: 1em;
    }
    input:focus { outline: none; border-color: #3b82f6; }
    button.submit-btn {
        padding: 10px 24px;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 1em;
        transition: background 0.2s;
    }
    button.submit-btn:hover { background: #1d4ed8; }

    /* 结果区域 */
    .result-area {
        margin-top: 20px;
        border-radius: 8px;
        overflow: hidden;
    }
    .result-tabs {
        display: flex;
        background: #0f172a;
        border-radius: 8px 8px 0 0;
        overflow: hidden;
    }
    .result-tab {
        padding: 10px 20px;
        cursor: pointer;
        color: #94a3b8;
        border: none;
        background: transparent;
        font-size: 0.9em;
        transition: all 0.2s;
    }
    .result-tab.active {
        background: #1e293b;
        color: #e2e8f0;
        border-bottom: 2px solid #3b82f6;
    }
    .result-content {
        background: #0f172a;
        padding: 16px;
        border-radius: 0 0 8px 8px;
        max-height: 350px;
        overflow-y: auto;
        font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
        font-size: 0.88em;
        line-height: 1.6;
        white-space: pre-wrap;
        word-break: break-all;
    }
    .sql-preview {
        background: #1a0a2e;
        color: #e879f9;
        padding: 12px 16px;
        border-radius: 6px;
        margin-top: 15px;
        font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
        font-size: 0.88em;
        border: 1px solid #7c3aed;
    }
    .sql-preview strong { color: #c084fc; }

    /* 通过提示 */
    .pass-banner {
        background: linear-gradient(135deg, #065f46, #047857);
        color: #6ee7b7;
        padding: 15px 20px;
        border-radius: 8px;
        margin-top: 20px;
        text-align: center;
        font-weight: bold;
        font-size: 1.05em;
        animation: fadeIn 0.5s ease;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 0.88em;
    }
    th {
        background: #334155;
        color: #e2e8f0;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
    }
    td {
        padding: 8px 12px;
        border-bottom: 1px solid #334155;
        color: #cbd5e1;
    }
    tr:hover td { background: #1e293b; }

    .error-msg {
        color: #fca5a5;
        background: #450a0a;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 3px solid #ef4444;
    }
    .success-msg {
        color: #6ee7b7;
        background: #052e16;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 3px solid #22c55e;
    }
    .warning-msg {
        color: #fcd34d;
        background: #451a03;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 3px solid #f59e0b;

    }

    .progress-bar {
        display: flex;
        gap: 4px;
        margin-bottom: 25px;
        justify-content: center;
    }
    .progress-dot {
        width: 40px;
        height: 6px;
        border-radius: 3px;
        background: #334155;
        transition: background 0.3s;
    }
    .progress-dot.passed { background: #22c55e; }
    .progress-dot.current { background: #3b82f6; }

    footer {
        text-align: center;
        color: #475569;
        margin-top: 30px;
        font-size: 0.85em;
    }
</style>
</head>
<body>
<div class="container">
    <h1>🔥 SQL Injection 靶场</h1>
    <p class="subtitle">手工注入练习 — 理解原理比背 payload 更重要</p>

    <div class="progress-bar" id="progressBar"></div>

    <div class="level-nav" id="levelNav">
        <!-- 动态生成 -->
    </div>

    <!-- Level 1: 报错信号 -->
    <div class="level-section active" id="level1">
        <h2 class="level-title">Level 1 🔴 发现报错信号</h2>
        <div class="level-desc">
            在搜索框中输入内容，观察返回结果。<br>
            <strong>目标：</strong>找到一个能让页面报错的输入，证明这里可能存在 SQL 注入。
        </div>
        <div class="hint-box">
            <strong>💡 提示：</strong>还记得片2讲的吗？什么字符能破坏 SQL 语句结构？试试在正常输入后面加一个特殊字符。
        </div>
        <form method="GET" action="/search">
            <div class="form-row">
                <label>搜索商品:</label>
                <input type="text" name="q" value="{search_q}" placeholder="输入要搜索的商品名称...">
                <button type="submit" class="submit-btn">搜索</button>
            </div>
        </form>
        {level1_result}
    </div>

    <!-- Level 2: 逻辑运算注入 -->
    <div class="level-section" id="level2">
        <h2 class="level-title">Level 2 🟡 逻辑运算 — 让所有数据都出来</h2>
        <div class="level-desc">
            你已经确认了搜索功能存在 SQL 注入。<br>
            <strong>目标：</strong>利用逻辑运算符，让搜索结果返回<strong>所有商品</strong>（而不只是你搜的那个）。
        </div>
        <div class="hint-box">
            <strong>💡 提示：</strong>想想 `OR` 和 `'1'='1'` —— 怎么让 WHERE 条件对每一行都为真？
        </div>
        <form method="GET" action="/search">
            <div class="form-row">
                <label>搜索商品:</label>
                <input type="text" name="q" value="{search_q}" placeholder="输入你的 payload...">
                <button type="submit" class="submit-btn">搜索</button>
            </div>
        </form>
        {level2_result}
    </div>

    <!-- Level 3: 绕过登录 -->
    <div class="level-section" id="level3">
        <h2 class="level-title">Level 3 🟠 绕过登录 — 不用密码进后台</h2>
        <div class="level-desc">
            这是一个登录表单。正常情况下你需要知道正确的用户名和密码才能登录。<br>
            <strong>目标：</strong>以 <code>admin</code> 身份登录（不需要知道 admin 的密码）。
        </div>
        <div class="hint-box">
            <strong>💡 提示：</strong>登录框背后的 SQL 大概是：<br>
            <code>SELECT * FROM users WHERE username='你的输入' AND password='你的密码'</code><br>
            怎么让密码验证被「绕过」？
        </div>
        <form method="POST" action="/login">
            <div class="form-row">
                <label>用户名:</label>
                <input type="text" name="username" value="{login_user}" placeholder="输入用户名...">
            </div>
            <div class="form-row">
                <label>密码:</label>
                <input type="password" name="password" value="{login_pass}" placeholder="输入密码...">
                <button type="submit" class="submit-btn">登录</button>
            </div>
        </form>
        {level3_result}
    </div>

    <!-- Level 4: 联合查询偷数据 -->
    <div class="level-section" id="level4">
        <h2 class="level-title">Level 4 🔴 联合查询 — 偷取其他表的数据</h2>
        <div class="level-desc">
            你已经能控制查询逻辑了。现在更进一步：<br>
            商品表里只有商品信息，但数据库里还有一张 <code>users</code> 表，里面存着<strong>用户的秘密信息</strong>。<br>
            <strong>目标：</strong>通过搜索功能，查出 <code>users</code> 表中所有人的 <strong>username 和 secret</strong> 字段。
        </div>
        <div class="hint-box">
            <strong>💡 提示：</strong>SQL 的 <code>UNION SELECT</code> 可以把两张表的查询结果拼在一起。<br>
            先确定原查询返回几列（可以用 <code>ORDER BY 1</code> / <code>ORDER BY 2</code> ... 试），然后用 UNION SELECT 把 users 表的数据拼出来。
        </div>
        <form method="GET" action="/search">
            <div class="form-row">
                <label>搜索商品:</label>
                <input type="text" name="q" value="{search_q}" placeholder="输入 UNION 注入 payload...">
                <button type="submit" class="submit-btn">搜索</button>
            </div>
        </form>
        {level4_result}
    </div>

    <!-- Level 5: 防御修复 -->
    <div class="level-section" id="level5">
        <h2 class="level-title">Level 5 🛡️ 防御修复 — 让注入失效</h2>
        <div class="level-desc">
            你现在是一个安全工程师，老板让你修复这个搜索功能的 SQL 注入漏洞。<br>
            <strong>目标：</strong>切换到「安全模式」搜索，证明之前的 payload 全部失效。
        </div>
        <div class="hint-box">
            <strong>💡 提示：</strong>安全模式使用了参数化查询。试试把前面关卡用过的 payload 再输一遍，看看会发生什么。
        </div>
        <div style="display:flex; gap:15px; margin-bottom:20px;">
            <form method="GET" action="/search_safe">
                <div class="form-row">
                    <label style="min-width:auto; color:#22c55e;">🔒 安全搜索:</label>
                    <input type="text" name="q" value="{safe_q}" placeholder="输入任何 payload...">
                    <button type="submit" class="submit-btn" style="background:#16a34a;">安全搜索</button>
                </div>
            </form>
        </div>
        {level5_result}
    </div>

    <footer>
        <p>⚠️ 本靶场仅用于学习目的 | 所有数据均为虚构 | 请勿用于非法用途</p>
    </footer>
</div>

<script>
// 关卡状态管理
const levels = [1, 2, 3, 4, 5];
let passedLevels = new Set({passed_levels});

function renderNav() {
    const nav = document.getElementById('levelNav');
    nav.innerHTML = levels.map(l => {
        const cls = passedLevels.has(l) ? 'level-btn passed' :
                     l === {current_level} ? 'level-btn active' : 'level-btn';
        const icon = passedLevels.has(l) ? '✅ ' : '';
        return `<button class="${cls}" onclick="showLevel(${l})">${icon}Level ${l}</button>`;
    }).join('');
}

function renderProgress() {
    const bar = document.getElementById('progressBar');
    bar.innerHTML = levels.map(l => {
        let cls = 'progress-dot';
        if (passedLevels.has(l)) cls += ' passed';
        else if (l === {current_level}) cls += ' current';
        return `<div class="${cls}"></div>`;
    }).join('');
}

function showLevel(n) {
    document.querySelectorAll('.level-section').forEach(s => s.classList.remove('active'));
    document.getElementById('level' + n).classList.add('active');
    renderNav();
}

renderNav();
renderProgress();
</script>
</body>
</html>'''


# ============ HTTP 请求处理器 ============

class SQLiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """静默日志"""
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.serve_lab_page(params)
        elif path == '/search':
            self.handle_search(params)
        elif path == '/search_safe':
            self.handle_search_safe(params)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(body)
            self.handle_login(params)
        else:
            self.send_error(404)

    def serve_lab_page(self, params):
        """渲染主页面"""
        # 从 cookie 读取已通过的关卡
        cookie_header = self.headers.get('Cookie', '')
        passed = set()
        if 'sqli_passed' in cookie_header:
            for part in cookie_header.split(';'):
                if 'sqli_passed=' in part:
                    vals = part.split('=')[1].strip()
                    if vals:
                        passed = set(int(x) for x in vals.split(',') if x.isdigit())

        current = min([x for x in range(1, 6) if x not in passed], default=5)
        passed_list = str(list(passed))

        page = LAB_HTML.replace('{search_q}', '') \
                       .replace('{login_user}', '') \
                       .replace('{login_pass}', '') \
                       .replace('{safe_q}', '') \
                       .replace('{level1_result}', '') \
                       .replace('{level2_result}', '') \
                       .replace('{level3_result}', '') \
                       .replace('{level4_result}', '') \
                       .replace('{level5_result}', '') \
                       .replace('{passed_levels}', passed_list) \
                       .replace('{current_level}', str(current))

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))

    def handle_search(self, params):
        """处理搜索请求 — 有漏洞的版本（字符串拼接）"""
        q = params.get('q', [''])[0]
        passed = self._get_passed()

        result_html = ''
        sql_preview = ''
        pass_banner = ''

        try:
            conn = get_db()
            cursor = conn.cursor()

            # ⚠️ 漏洞代码：直接拼接用户输入到 SQL 中
            sql = f"SELECT * FROM products WHERE name LIKE '%{q}%'"
            sql_preview = f'<div class="sql-preview"><strong>执行的 SQL：</strong><br>{html.escape(sql)}</div>'

            cursor.execute(sql)
            rows = cursor.fetchall()

            if rows:
                table = '<table><tr><th>ID</th><th>名称</th><th>价格</th><th>分类</th></tr>'
                for r in rows:
                    table += f'<tr><td>{r["id"]}</td><td>{html.escape(str(r["name"]))}</td><td>{r["price"]}</td><td>{html.escape(str(r["category"]))}</td></tr>'
                table += '</table>'
                result_html = f'<div class="success-msg">找到 {len(rows)} 条结果</div>{table}'
            else:
                result_html = '<div class="warning-msg">未找到匹配的商品</div>'

            # 共享连接，不关闭

            # ====== 关卡检测 ======
            # Level 1: 触发过 SQL 错误（单引号导致语法错误）
            if "'" in q and 1 not in passed:
                # 如果有单引号且没出错（SQLite 宽容），检查是否有异常行为
                if 'error' in result_html.lower() or 'syntax' in sql_preview.lower():
                    pass
                # 单引号就触发 Level 1 通过（因为这是正确的探测方式）
                passed.add(1)
                pass_banner = '<div class="pass-banner">Level 1 通过! 你发现了报错信号 — 单引号可以破坏 SQL 结构</div>'

            # Level 2: 返回了全部 8 条商品（OR 1=1 成功）
            if len(rows) == 8 and 2 not in passed:
                passed.add(2)
                pass_banner += '<div class="pass-banner">Level 2 通过! 逻辑运算成功 — 你让所有数据都出来了!</div>'

            # Level 4: 结果中包含 users 表的数据（UNION 成功）
            user_keywords = ['admin', 'zhangsan', 'lisi', 'P@ssw0rd', '银行卡']
            result_text = result_html.lower()
            if any(kw.lower() in result_text for kw in user_keywords) and 4 not in passed:
                passed.add(4)
                pass_banner += '<div class="pass-banner">Level 4 通过! 联合查询成功 — 你偷到了其他表的数据!</div>'

        except Exception as e:
            error_msg = str(e)
            result_html = f'<div class="error-msg">SQL Error: {html.escape(error_msg)}</div>'
            sql_preview = f'<div class="sql-preview"><strong>执行的 SQL（出错）：</strong><br>{html.escape(sql)}</div>'

            # Level 1: 触发了 SQL 报错
            if "'" in q and 1 not in passed:
                passed.add(1)
                pass_banner = '<div class="pass-banner">Level 1 通过! 你触发了 SQL 报错 — 这就是注入信号!</div>'

        self._send_lab_page(q, '', '', '', result_html + sql_preview + pass_banner, '', passed)

    def handle_search_safe(self, params):
        """处理搜索请求 — 安全版本（参数化查询）"""
        q = params.get('q', [''])[0]
        passed = self._get_passed()

        result_html = ''
        sql_preview = ''
        pass_banner = ''

        try:
            conn = get_db()
            cursor = conn.cursor()

            # ✅ 安全代码：参数化查询
            sql = "SELECT * FROM products WHERE name LIKE ?"
            search_pattern = f'%{q}%'
            sql_preview = f'<div class="sql-preview"><strong>执行的 SQL（参数化）：</strong><br>{html.escape(sql)}<br><strong>参数值：</strong>{html.escape(repr(search_pattern))}</div>'

            cursor.execute(sql, (search_pattern,))
            rows = cursor.fetchall()

            if rows:
                table = '<table><tr><th>ID</th><th>名称</th><th>价格</th><th>分类</th></tr>'
                for r in rows:
                    table += f'<tr><td>{r["id"]}</td><td>{html.escape(str(r["name"]))}</td><td>{r["price"]}</td><td>{html.escape(str(r["category"]))}</td></tr>'
                table += '</table>'
                result_html = f'<div class="success-msg">找到 {len(rows)} 条结果（安全模式下只做精确匹配）</div>{table}'
            else:
                result_html = '<div class="warning-msg">未找到匹配的商品（你的 payload 被当作普通文本处理了）</div>'

            # 共享连接，不关闭

            # Level 5: 在安全模式下尝试注入 → 证明失效了
            dangerous_chars = ["'", '"', 'OR', 'AND', '--', 'UNION', '=', '1=1']
            has_injection_attempt = any(c.upper() in q.upper() for c in dangerous_chars)
            if has_injection_attempt and len(rows) != 8 and 5 not in passed:
                passed.add(5)
                pass_banner = '<div class="pass-banner">Level 5 通过! 参数化查询防御成功 — 你的 payload 已失效!</div>'

        except Exception as e:
            result_html = f'<div class="error-msg">(安全模式) 查询异常: {html.escape(str(e))}</div>'

        self._send_lab_page('', '', '', q, result_html + sql_preview + pass_banner, '', passed)

    def handle_login(self, params):
        """处理登录请求 — 有漏洞的版本"""
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        passed = self._get_passed()

        result_html = ''
        sql_preview = ''
        pass_banner = ''

        try:
            conn = get_db()
            cursor = conn.cursor()

            # ⚠️ 漏洞代码：拼接用户名和密码
            sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            sql_preview = f'<div class="sql-preview"><strong>执行的 SQL：</strong><br>{html.escape(sql)}</div>'

            cursor.execute(sql)
            rows = cursor.fetchall()

            if rows:
                user = rows[0]
                role_badge = '👑 管理员' if user['role'] == 'admin' else '👤 普通用户'
                result_html = f'''<div class="success-msg">登录成功! {role_badge}</div>
                    <table>
                        <tr><th>字段</th><th>值</th></tr>
                        <tr><td>用户名</td><td>{html.escape(user['username'])}</td></tr>
                        <tr><td>邮箱</td><td>{html.escape(user['email'])}</td></tr>
                        <tr><td>角色</td><td>{html.escape(user['role'])}</td></tr>
                        <tr><td>秘密</td><td style="color:#f87171">{html.escape(user['secret'])}</td></tr>
                    </table>'''

                # Level 3: 以 admin 身份登录成功
                if user['username'] == 'admin' and 3 not in passed:
                    passed.add(3)
                    pass_banner = '<div class="pass-banner">Level 3 通过! 登录绕过成功 — 你以 admin 身份进入了系统!</div>'
            else:
                result_html = '<div class="error-msg">登录失败：用户名或密码错误</div>'

        except Exception as e:
            result_html = f'<div class="error-msg">SQL Error: {html.escape(str(e))}</div>'
            sql_preview = f'<div class="sql-preview"><strong>执行的 SQL（出错）：</strong><br>{html.escape(sql)}</div>'

        self._send_lab_page('', username, password, '', result_html + sql_preview + pass_banner, '', passed)

    def _get_passed(self):
        """从 cookie 读取已通过关卡"""
        cookie_header = self.headers.get('Cookie', '')
        passed = set()
        if 'sqli_passed' in cookie_header:
            for part in cookie_header.split(';'):
                if 'sqli_passed=' in part:
                    vals = part.split('=')[1].strip()
                    if vals:
                        passed = set(int(x) for x in vals.split(',') if x.isdigit())
        return passed

    def _send_lab_page(self, search_q, login_user, login_pass, safe_q, level_result, extra, passed):
        """发送完整页面"""
        passed_list = str(list(passed))
        current = min([x for x in range(1, 6) if x not in passed], default=5)

        page = LAB_HTML.replace('{search_q}', html.escape(search_q)) \
                       .replace('{login_user}', html.escape(login_user)) \
                       .replace('{login_pass}', html.escape(login_pass)) \
                       .replace('{safe_q}', html.escape(safe_q)) \
                       .replace('{level1_result}', level_result if current >= 1 else '') \
                       .replace('{level2_result}', level_result if current == 2 else '') \
                       .replace('{level3_result}', level_result if current == 3 else '') \
                       .replace('{level4_result}', level_result if current == 4 else '') \
                       .replace('{level5_result}', level_result if current == 5 else '') \
                       .replace('{passed_levels}', passed_list) \
                       .replace('{current_level}', str(current))

        cookie_val = ','.join(str(x) for x in sorted(passed))
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Set-Cookie', f'sqli_passed={cookie_val}; Path=/')
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))


# ============ 启动服务器 ============

def main():
    port = 5678
    server = HTTPServer(('127.0.0.1', port), SQLiHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║     SQL Injection 靶场已启动                   ║
║                                              ║
║   浏览器打开: http://127.0.0.1:{port}          ║
║                                              ║
║   共 5 关:                                    ║
║   L1 发现报错  →  L2 逻辑运算  →  L3 绕过登录  ║
║   L4 联合查询  →  L5 防御修复                  ║
║                                              ║
║   按 Ctrl+C 停止                              ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 靶场已停止")
        server.server_close()


if __name__ == '__main__':
    main()
