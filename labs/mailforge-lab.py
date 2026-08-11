#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MailForge - 邮件模板营销平台
SSTI 进阶靶场（端口 5023）

设计要点:
1. 模拟真实 SaaS 邮件营销平台，5 个可输入的功能点
2. 不是所有输入点都有 SSTI — 需要自己判断
3. 3 枚 FLAG，每枚需要不同的推理:
   - ssti_template_finder: 模板编辑器直接 SSTI，从 config 读 FLAG
   - ssti_second_order: 二次注入 — 收件人姓名存入数据库，预览时触发
   - ssti_waf_bypass: API 接口有 WAF 关键词过滤，需要绕过
4. profile 页面是干扰项（安全渲染，无 SSTI）
"""

import os
import html
import sqlite3
from flask import Flask, request, render_template_string, jsonify, redirect, g

app = Flask(__name__)
app.secret_key = 'mailforge_dev_secret_2026'

# ===== FLAG =====
FLAG1 = 'FLAG{ssti_template_finder_2026}'
FLAG2 = 'FLAG{ssti_second_order_2026}'
FLAG3 = 'FLAG{ssti_waf_bypass_2026}'

# FLAG 1 藏在 Flask config 里
app.config['MAILFORGE_FLAG'] = FLAG1
# FLAG 2 只在预览路由的 g 对象里（只有二次注入才能读到）
# FLAG 3 藏在环境变量里（需要 RCE 才能读到）
os.environ['MAILFORGE_SECRET'] = FLAG3

_collected = set()

# ===== 数据库 =====
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mailforge.db')

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    # 插入初始数据让网站看起来真实
    if db.execute('SELECT COUNT(*) as c FROM recipients').fetchone()['c'] == 0:
        db.execute('INSERT INTO recipients (name, email) VALUES (?, ?)', ('张伟', 'zhangwei@example.com'))
        db.execute('INSERT INTO recipients (name, email) VALUES (?, ?)', ('李娜', 'lina@example.com'))
    if db.execute('SELECT COUNT(*) as c FROM templates').fetchone()['c'] == 0:
        db.execute('INSERT INTO templates (title, content) VALUES (?, ?)',
                   ('欢迎邮件', '亲爱的 {{ name }}，欢迎加入 MailForge！'))
    db.commit()
    db.close()

init_db()

# ===== WAF =====
WAF_BLOCKED = ['__', 'config', 'self', 'os', 'import', 'subprocess',
               'popen', 'system', 'eval', 'exec', 'globals', 'builtins',
               'class', 'mro', 'subclasses', 'init']

def waf_check(template_str):
    """检查模板内容是否包含危险关键词"""
    lower = template_str.lower()
    for kw in WAF_BLOCKED:
        if kw in lower:
            return False, kw
    return True, None

# ===== FLAG 检测 =====
def check_flags(rendered):
    global _collected
    result = ''
    for key, flag in [('template', FLAG1), ('second_order', FLAG2), ('waf_bypass', FLAG3)]:
        if key not in _collected and flag in str(rendered):
            _collected.add(key)
            result += f'<div class="flag-banner">{flag}</div>'
    return result

# ===== 页面样式 =====
CSS = '''
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }
  nav { background: #161b22; padding: 12px 30px; display: flex; gap: 20px; align-items: center; border-bottom: 2px solid #30363d; flex-wrap: wrap; }
  nav a { color: #8b949e; text-decoration: none; font-size: 14px; }
  nav a:hover { color: #58a6ff; }
  .brand { font-size: 18px; font-weight: 700; color: #39d353; margin-right: auto; }
  .brand span { color: #8b949e; font-weight: 400; font-size: 13px; }
  .container { max-width: 900px; margin: 25px auto; padding: 0 20px; }
  h1 { color: #39d353; margin-bottom: 15px; font-size: 22px; }
  h2 { color: #8b949e; margin: 12px 0 8px; font-size: 16px; }
  .card { background: #161b22; border-radius: 8px; padding: 20px; margin-bottom: 15px; border: 1px solid #30363d; }
  .stats { display: flex; gap: 15px; margin-bottom: 20px; }
  .stat { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px 20px; flex: 1; text-align: center; }
  .stat-num { font-size: 28px; font-weight: 700; color: #39d353; }
  .stat-label { font-size: 13px; color: #8b949e; }
  input, textarea, select { padding: 8px 12px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; border-radius: 5px; font-size: 14px; width: 100%; margin-bottom: 10px; }
  button { padding: 8px 20px; border: none; background: #39d353; color: #0d1117; border-radius: 5px; font-size: 14px; font-weight: 600; cursor: pointer; }
  button:hover { background: #2da44e; }
  .btn-sm { padding: 4px 12px; font-size: 13px; display: inline-block; }
  a.btn-sm { background: #21262d; color: #c9d1d9; text-decoration: none; border: 1px solid #30363d; border-radius: 5px; }
  .msg { padding: 12px 15px; border-radius: 5px; margin-bottom: 12px; font-size: 14px; }
  .msg-info { background: #0c2233; border-left: 3px solid #58a6ff; }
  .msg-success { background: #122b1f; border-left: 3px solid #3fb950; }
  .msg-error { background: #2d1414; border-left: 3px solid #f85149; }
  .msg-warn { background: #2d2414; border-left: 3px solid #d29922; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; color: #8b949e; font-size: 13px; padding: 8px; border-bottom: 1px solid #30363d; }
  td { padding: 8px; border-bottom: 1px solid #21262d; font-size: 14px; }
  .email-preview { background: #ffffff; color: #333; border-radius: 8px; padding: 25px; margin: 15px 0; }
  .email-header { border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 15px; font-size: 13px; color: #666; }
  .email-body p { margin: 10px 0; line-height: 1.8; }
  .tpl-content { background: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 15px; margin: 10px 0; font-family: monospace; white-space: pre-wrap; color: #c9d1d9; }
  .tpl-rendered { background: #ffffff; color: #333; border-radius: 5px; padding: 15px; margin: 10px 0; }
  .code-block { background: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 12px; font-family: "Consolas", monospace; font-size: 13px; color: #c9d1d9; overflow-x: auto; white-space: pre; }
  .flag-banner { background: linear-gradient(135deg, #39d353, #2da44e); padding: 18px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: 700; color: #0d1117; margin-top: 15px; letter-spacing: 1px; }
  code { background: #21262d; padding: 2px 6px; border-radius: 3px; font-size: 13px; color: #f0883e; }
  footer { text-align: center; padding: 20px; color: #484f58; border-top: 1px solid #30363d; margin-top: 30px; font-size: 13px; }
</style>
'''

def page(title, body, active=''):
    nav_items = [
        ('/', '仪表盘', 'home'),
        ('/templates', '模板', 'templates'),
        ('/templates/new', '新建模板', 'new'),
        ('/recipients', '收件人', 'recipients'),
        ('/preview', '预览', 'preview'),
        ('/profile', '资料', 'profile'),
        ('/docs', 'API文档', 'docs'),
        ('/flags', 'FLAG', 'flags'),
    ]
    nav_html = ''
    for href, label, key in nav_items:
        style = 'color:#39d353;font-weight:600' if active == key else ''
        nav_html += f'<a href="{href}" style="{style}">{label}</a>'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} - MailForge</title>
{CSS}
</head>
<body>
<nav>
  <span class="brand">MailForge <span>v2.1</span></span>
  {nav_html}
</nav>
<div class="container">{body}</div>
<footer>MailForge 邮件模板营销平台 &copy; 2026 | 本系统仅供安全学习使用</footer>
</body></html>'''


# ===== 1. 仪表盘 =====
@app.route('/')
def home():
    db = get_db()
    tpl_count = db.execute('SELECT COUNT(*) as c FROM templates').fetchone()['c']
    rcpt_count = db.execute('SELECT COUNT(*) as c FROM recipients').fetchone()['c']
    db.close()

    body = f'''
    <h1>仪表盘</h1>
    <div class="stats">
        <div class="stat"><div class="stat-num">{tpl_count}</div><div class="stat-label">邮件模板</div></div>
        <div class="stat"><div class="stat-num">{rcpt_count}</div><div class="stat-label">收件人</div></div>
        <div class="stat"><div class="stat-num">0</div><div class="stat-label">已发送</div></div>
        <div class="stat"><div class="stat-num">{len(_collected)}/3</div><div class="stat-label">FLAG</div></div>
    </div>
    <div class="card">
        <h2>快捷操作</h2>
        <p><a href="/templates/new">创建邮件模板</a> — 设计新的邮件模板，支持变量渲染</p>
        <p><a href="/recipients">管理收件人</a> — 添加或查看收件人列表</p>
        <p><a href="/preview">邮件预览</a> — 预览邮件渲染效果</p>
        <p><a href="/profile">个人资料</a> — 编辑你的个人信息</p>
        <p><a href="/docs">API 文档</a> — 查看渲染 API 接口说明</p>
    </div>
    <div class="msg msg-info">
        MailForge 是一个邮件模板营销平台。创建模板、管理收件人、一键预览渲染效果。
    </div>'''
    return page('仪表盘', body, 'home')


# ===== 2. 模板列表 =====
@app.route('/templates')
def templates():
    db = get_db()
    templates = db.execute('SELECT * FROM templates ORDER BY id DESC').fetchall()
    db.close()

    body = '<h1>邮件模板</h1>'
    if not templates:
        body += '<div class="msg msg-info">还没有模板，<a href="/templates/new">创建一个</a></div>'
    else:
        body += '<div class="card"><table><tr><th>ID</th><th>标题</th><th>内容预览</th><th>创建时间</th></tr>'
        for t in templates:
            preview = t['content'][:60] + '...' if len(t['content']) > 60 else t['content']
            body += f'<tr><td>{t["id"]}</td><td>{html.escape(t["title"])}</td><td><code>{html.escape(preview)}</code></td><td>{t["created_at"]}</td></tr>'
        body += '</table></div>'
    body += '<p style="margin-top:15px"><a href="/templates/new"><button class="btn-sm">新建模板</button></a></p>'
    return page('模板', body, 'templates')


# ===== 3. 创建模板 (SSTI 入口 1: 直接渲染) =====
JINJA_EXAMPLE = '{{ name }}'

@app.route('/templates/new', methods=['GET', 'POST'])
def template_new():
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')

        # 保存到数据库
        db = get_db()
        db.execute('INSERT INTO templates (title, content) VALUES (?, ?)', (title, content))
        db.commit()
        db.close()

        try:
            # 漏洞：用户输入的 content 被直接拼到 Jinja2 模板字符串里渲染
            # 正确做法应该用 {{ content }} 占位符 + render_template_string(template, content=content)
            # 但这里直接把 content 拼进了模板字符串
            template_str = '<div class="tpl-rendered">' + content + '</div>'
            rendered = render_template_string(template_str, name='张伟', email='zhangwei@example.com')
            flag_html = check_flags(rendered)
            body = f'''<h1>模板预览</h1>
            <div class="msg msg-success">模板 "{html.escape(title)}" 已保存</div>
            <h2>渲染效果</h2>
            {rendered}
            {flag_html}
            <p style="margin-top:15px"><a href="/templates/new"><button class="btn-sm">再写一个</button></a></p>'''
        except Exception:
            body = f'''<h1>模板预览</h1>
            <div class="msg msg-success">模板 "{html.escape(title)}" 已保存</div>
            <div class="msg msg-error">模板渲染失败，请检查模板内容格式</div>
            <p style="margin-top:15px"><a href="/templates/new"><button class="btn-sm">返回</button></a></p>'''
        return page('模板预览', body, 'new')

    body = f'''
    <h1>创建邮件模板</h1>
    <div class="card">
        <form method="POST" action="/templates/new">
            <p><label>模板标题</label><br>
            <input type="text" name="title" placeholder="例如：欢迎邮件"></p>
            <p><label>模板内容</label><br>
            <textarea name="content" rows="8" placeholder="输入邮件内容..."></textarea></p>
            <button type="submit">保存并预览</button>
        </form>
    </div>
    <div class="msg msg-info">
        提示：模板支持变量语法，例如输入 <code>{JINJA_EXAMPLE}</code> 会在渲染时替换为收件人姓名。
    </div>'''
    return page('创建模板', body, 'new')


# ===== 4. 收件人列表 =====
@app.route('/recipients')
def recipients():
    db = get_db()
    recipients = db.execute('SELECT * FROM recipients ORDER BY id DESC').fetchall()
    db.close()

    body = '<h1>收件人列表</h1>'
    if not recipients:
        body += '<div class="msg msg-info">还没有收件人</div>'
    else:
        body += '<div class="card"><table><tr><th>ID</th><th>姓名</th><th>邮箱</th><th>添加时间</th></tr>'
        for r in recipients:
            body += f'<tr><td>{r["id"]}</td><td>{html.escape(r["name"])}</td><td>{html.escape(r["email"])}</td><td>{r["created_at"]}</td></tr>'
        body += '</table></div>'

    body += '''
    <div class="card">
        <h2>添加收件人</h2>
        <form method="POST" action="/recipients/add">
            <input type="text" name="name" placeholder="姓名">
            <input type="text" name="email" placeholder="邮箱地址">
            <button type="submit">添加</button>
        </form>
    </div>'''
    return page('收件人', body, 'recipients')


# ===== 5. 添加收件人 (只存储，不渲染) =====
@app.route('/recipients/add', methods=['POST'])
def recipient_add():
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    if name and email:
        db = get_db()
        db.execute('INSERT INTO recipients (name, email) VALUES (?, ?)', (name, email))
        db.commit()
        db.close()
    return redirect('/recipients')


# ===== 6. 邮件预览 (SSTI 入口 2: 二次注入) =====
@app.route('/preview')
def preview():
    db = get_db()
    recipient = db.execute('SELECT * FROM recipients ORDER BY id DESC LIMIT 1').fetchone()
    db.close()

    if not recipient:
        return page('预览', '<div class="msg msg-info">请先<a href="/recipients">添加收件人</a></div>', 'preview')

    name = recipient['name']
    email = recipient['email']

    # 只在预览路由中注入 FLAG 2 到 g 对象
    # 模板编辑器和 API 路由都不会设置这个值
    g.mailforge_internal = FLAG2

    # 漏洞：收件人姓名被直接拼进 Jinja2 模板字符串
    # 正确做法应该用 {{ name }} 占位符 + render_template_string(template, name=name)
    # 但这里用字符串拼接把 name 直接嵌入了模板
    template_str = f'''<div class="email-preview">
    <div class="email-header">
        收件人: {name} &lt;{email}&gt;
    </div>
    <div class="email-body">
        <p>亲爱的 {name}，</p>
        <p>感谢您使用 MailForge 邮件服务！您的账户已激活。</p>
        <p>如有疑问，请回复此邮件。</p>
    </div>
</div>'''

    try:
        rendered = render_template_string(template_str)
        flag_html = check_flags(rendered)
        body = f'<h1>邮件预览</h1>{rendered}{flag_html}'
    except Exception:
        body = '<h1>邮件预览</h1><div class="msg msg-error">邮件渲染失败，请检查收件人信息格式</div>'
    return page('预览', body, 'preview')


# ===== 7. API 渲染 (SSTI 入口 3: WAF 绕过) =====
@app.route('/api/v1/render', methods=['POST'])
def api_render():
    data = request.get_json(silent=True)
    if not data or 'template' not in data:
        return jsonify({'error': 'missing "template" field'}), 400

    template = data['template']

    # WAF: 检查模板内容是否包含危险关键词
    passed, blocked_kw = waf_check(template)
    if not passed:
        return jsonify({'error': 'WAF blocked', 'reason': f'keyword filter: {blocked_kw}'}), 403

    try:
        rendered = render_template_string(template)
        flag_html = check_flags(rendered)
        result = {'result': rendered}
        if flag_html:
            result['flag'] = flag_html.replace('<div class="flag-banner">', '').replace('</div>', '').strip()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'render failed', 'detail': str(e)}), 500


# ===== 8. 个人资料 (干扰项: 安全渲染) =====
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        bio = request.form.get('bio', '')
        # 安全：用占位符传参，不直接拼接
        # 即使输入 {{ config }} 也只会显示字面文字，不会执行
        template = '<div class="card"><h2>个人简介</h2><p>{{ bio }}</p></div>'
        rendered = render_template_string(template, bio=bio)
        body = f'<h1>个人资料</h1>{rendered}<div class="msg msg-success">资料已保存</div>'
        return page('资料', body, 'profile')

    body = '''
    <h1>个人资料</h1>
    <div class="card">
        <form method="POST" action="/profile">
            <p><label>用户名</label><br>
            <input type="text" value="admin" disabled></p>
            <p><label>个人简介</label><br>
            <textarea name="bio" rows="3" placeholder="介绍一下自己"></textarea></p>
            <button type="submit">保存</button>
        </form>
    </div>
    <div class="msg msg-info">个人资料会显示在你的公开主页上</div>'''
    return page('资料', body, 'profile')


# ===== 9. API 文档 =====
@app.route('/docs')
def docs():
    curl_example = '''curl -X POST http://127.0.0.1:5023/api/v1/render \\
  -H "Content-Type: application/json" \\
  -d '{"template": "Hello!"}&#39;'''

    body = f'''
    <h1>API 文档</h1>
    <div class="card">
        <h2>POST /api/v1/render</h2>
        <p>渲染邮件模板，返回渲染后的内容。支持 Jinja2 模板语法。</p>

        <h2>请求</h2>
        <div class="code-block">POST /api/v1/render
Content-Type: application/json

{{
  "template": "Hello {JINJA_EXAMPLE}!"
}}</div>

        <h2>响应</h2>
        <div class="code-block">{{
  "result": "Hello 张伟!"
}}</div>

        <h2>错误响应</h2>
        <div class="code-block">{{
  "error": "WAF blocked",
  "reason": "keyword filter: config"
}}</div>

        <h2>安全说明</h2>
        <div class="msg msg-warn">
            系统已启用 WAF（Web 应用防火墙），会自动检测模板中的危险关键词并拦截。<br>
            如果模板包含危险关键词，API 返回 403 并提示被拦截的关键词。<br><br>
            可以用 URL 查询参数传递额外变量，例如：<br>
            <code>/api/v1/render?debug=1</code>
        </div>
    </div>
    <div class="card">
        <h2>curl 测试示例</h2>
        <div class="code-block">{curl_example}</div>
    </div>
    <div class="card">
        <h2>Jinja2 模板全局对象</h2>
        <p>MailForge 使用 Jinja2 模板引擎（Flask 内置）。模板中可以使用以下全局对象：</p>
        <table>
            <tr><th>对象</th><th>说明</th></tr>
            <tr><td><code>config</code></td><td>Flask 应用配置字典</td></tr>
            <tr><td><code>request</code></td><td>当前 HTTP 请求对象</td></tr>
            <tr><td><code>session</code></td><td>用户会话对象</td></tr>
            <tr><td><code>g</code></td><td>请求级别的全局命名空间（每个路由可以往里面存数据）</td></tr>
            <tr><td><code>url_for</code></td><td>URL 生成函数</td></tr>
        </table>
        <div class="msg msg-info">
            注意：不同路由可能往 <code>g</code> 对象里存不同的数据。某个路由存的东西，其他路由不一定有。
        </div>
    </div>'''
    return page('API文档', body, 'docs')


# ===== 10. FLAG 进度 =====
@app.route('/flags')
def flags():
    body = '<h1>FLAG 收集进度</h1>'
    if not _collected:
        body += '<div class="msg msg-info">还没有收集到任何 FLAG。这个网站藏着 3 枚 FLAG，分布在不同深处。</div>'
    else:
        body += f'<div class="msg msg-success">已收集 {len(_collected)}/3 枚 FLAG</div>'

    flag_info = [
        ('template', FLAG1, '模板编辑器', '在"新建模板"页面，模板内容会被渲染。模板引擎能访问什么？'),
        ('second_order', FLAG2, '???', '数据存入数据库时不会触发，但在另一个页面渲染时才会执行。想想收件人姓名去了哪里。'),
        ('waf_bypass', FLAG3, 'API 接口', 'API 有 WAF 拦截危险关键词。如果关键词不能写在模板里，能不能从别的地方传入？'),
    ]

    for key, flag, location, hint in flag_info:
        if key in _collected:
            body += f'<div class="flag-banner">{flag}</div>'
        else:
            body += f'<div class="card"><h2>未解锁</h2><p><strong>位置:</strong> {location}</p><p><strong>线索:</strong> {hint}</p></div>'

    body += '<div class="card"><h2>提示</h2><p>不是所有输入点都有漏洞。试过的输入点如果没反应，换一个试试。</p><p>每个 FLAG 对应不同的 SSTI 技巧：直接注入、二次注入、WAF 绕过。</p></div>'
    return page('FLAG', body, 'flags')


if __name__ == '__main__':
    print(f"[*] MailForge 邮件模板营销平台启动: http://127.0.0.1:5023")
    print(f"[*] 3 枚 FLAG，难度递增")
    print(f"[*] FLAG 1: 模板编辑器直接 SSTI")
    print(f"[*] FLAG 2: 二次注入")
    print(f"[*] FLAG 3: API WAF 绕过")
    app.run(host='127.0.0.1', port=5023, debug=False)
