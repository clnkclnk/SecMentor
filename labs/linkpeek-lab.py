"""
LinkPeek - 网页链接预览服务
SSRF 服务端请求伪造靶场
端口 5026

三个 FLAG：
  FLAG1 基础 SSRF   — 通过 /preview 访问本机内部接口 /internal/flag
  FLAG2 云元数据   — 通过 /preview 访问 /internal/metadata（模拟云元数据服务）
  FLAG3 绕过黑名单 — 通过 /safe-fetch 绕过内网黑名单，访问 /internal/admin

核心思路：找到一个"服务器会去访问我给的 URL"的功能，把它引向本机/内网。
"""

import os
import sqlite3
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

FLAG1 = os.environ.get('LINKPEEK_FLAG1', 'FLAG{ssrf_hit_internal_service_2026}')
FLAG2 = os.environ.get('LINKPEEK_FLAG2', 'FLAG{ssrf_cloud_metadata_2026}')
FLAG3 = os.environ.get('LINKPEEK_FLAG3', 'FLAG{ssrf_blacklist_bypass_2026}')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkpeek.db')
INTERNAL_HEADER = {'X-Internal-Request': 'LinkPeek'}


def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS flags (
        id INTEGER PRIMARY KEY, f1 TEXT, f2 TEXT, f3 TEXT)''')
    if not db.execute("SELECT * FROM flags WHERE id=1").fetchone():
        db.execute("INSERT INTO flags (id) VALUES (1)")
    db.commit()
    db.close()


init_db()


def record_flag(col, value):
    db = get_db()
    db.execute(f"UPDATE flags SET {col}=? WHERE id=1", (value,))
    db.commit()
    db.close()


def get_flags():
    db = get_db()
    row = db.execute("SELECT * FROM flags WHERE id=1").fetchone()
    db.close()
    return row


BASE_HTML = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>LinkPeek</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,"Microsoft YaHei",sans-serif; background:#1a1a2e; color:#e0e0e0; }
.nav { background:#16213e; padding:16px 40px; border-bottom:2px solid #534AB7; }
.nav h1 { color:#AFA9EC; font-size:20px; }
.container { max-width:900px; margin:30px auto; padding:0 20px; }
.card { background:#16213e; border-radius:12px; padding:24px; margin-bottom:20px; border:1px solid #2C2C4A; }
.card h2 { font-size:16px; margin-bottom:16px; color:#AFA9EC; }
input[type=text] { background:#1a1a2e; border:1px solid #534AB7; color:#fff; padding:10px 12px; border-radius:6px; font-size:14px; width:70%; }
.btn { background:#534AB7; color:#fff; border:none; padding:10px 24px; border-radius:6px; cursor:pointer; font-size:14px; }
.btn:hover { background:#7F77DD; }
.result { background:#1a1a2e; border:1px solid #2C2C4A; border-radius:8px; padding:16px; margin-top:16px; font-family:Consolas,monospace; font-size:12px; white-space:pre-wrap; word-break:break-all; max-height:300px; overflow:auto; color:#97C459; }
.flags { display:flex; gap:10px; margin-top:12px; }
.flag-item { flex:1; padding:12px; border-radius:8px; text-align:center; font-size:12px; }
.flag-done { background:#1a3a2e; color:#5DCAA5; border:1px solid #0F6E56; }
.flag-pending { background:#1a1a2e; color:#666; border:1px solid #2C2C4A; }
.banner { background:#534AB7; color:#fff; padding:14px; border-radius:8px; text-align:center; font-size:16px; font-weight:bold; margin:16px 0; }
.hint { font-size:12px; color:#888; margin-top:10px; }
</style></head>
<body>
<div class="nav"><h1>LinkPeek</h1></div>
<div class="container">{content}</div>
</body></html>'''


def render(content):
    return render_template_string(BASE_HTML.replace('{content}', content))


@app.route('/')
def index():
    f = get_flags()
    f1 = f['f1'] is not None
    f2 = f['f2'] is not None
    f3 = f['f3'] is not None
    html = f'''
    <div class="card">
        <h2>网页链接预览</h2>
        <p style="font-size:13px;color:#888;margin-bottom:14px">输入一个网址，LinkPeek 帮你抓取网页内容并预览。</p>
        <form method="GET" action="/preview">
            <input type="text" name="url" placeholder="https://example.com" value="">
            <button class="btn" type="submit">预览</button>
        </form>
        <p class="hint">试试输入一个公开网站，看看服务器返回了什么。</p>
    </div>
    <div class="card">
        <h2>FLAG 收集</h2>
        <div class="flags">
            <div class="{'flag-done' if f1 else 'flag-pending'} flag-item">FLAG 1<br>{'已获得' if f1 else '未获得'}</div>
            <div class="{'flag-done' if f2 else 'flag-pending'} flag-item">FLAG 2<br>{'已获得' if f2 else '未获得'}</div>
            <div class="{'flag-done' if f3 else 'flag-pending'} flag-item">FLAG 3<br>{'已获得' if f3 else '未获得'}</div>
        </div>
    </div>
    '''
    if f1:
        html += f'<div class="banner">{FLAG1}</div>'
    if f2:
        html += f'<div class="banner">{FLAG2}</div>'
    if f3:
        html += f'<div class="banner">{FLAG3}</div>'
    return render(html)


@app.route('/preview')
def preview():
    url = request.args.get('url', '').strip()
    if not url:
        return render('<div class="card"><p>请输入网址</p><a class="btn" href="/">返回</a></div>')
    content = do_fetch(url, add_internal_header=True)
    # 检测是否命中内部 FLAG
    if FLAG1 in content:
        record_flag('f1', FLAG1)
    if FLAG2 in content:
        record_flag('f2', FLAG2)
    return render(f'''
    <div class="card">
        <h2>预览结果</h2>
        <p style="font-size:13px;color:#888;margin-bottom:8px">抓取: {url}</p>
        <div class="result">{content}</div>
        <p class="hint"><a href="/" style="color:#AFA9EC">← 返回</a></p>
    </div>''')


@app.route('/safe-fetch')
def safe_fetch():
    url = request.args.get('url', '').strip()
    if not url:
        return render('<div class="card"><p>请输入网址</p><a class="btn" href="/">返回</a></div>')
    # 黑名单防护：只检查主机名部分，阻止访问内网地址
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or '').lower()
    blocked = ['127.0.0.1', 'localhost', '169.254', '0.0.0.0']
    for b in blocked:
        if b in host:
            return render(f'''
            <div class="card">
                <h2>安全拦截</h2>
                <div class="result" style="color:#F09595">请求被拦截：检测到内网/本地地址 ({b})</div>
                <p class="hint"><a href="/" style="color:#AFA9EC">← 返回</a></p>
            </div>''')
    content = do_fetch(url, add_internal_header=True)
    if FLAG3 in content:
        record_flag('f3', FLAG3)
    return render(f'''
    <div class="card">
        <h2>安全抓取结果</h2>
        <p style="font-size:13px;color:#888;margin-bottom:8px">抓取: {url}</p>
        <div class="result">{content}</div>
        <p class="hint"><a href="/" style="color:#AFA9EC">← 返回</a></p>
    </div>''')


def do_fetch(url, add_internal_header=False):
    headers = INTERNAL_HEADER if add_internal_header else {}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        text = r.text
        if len(text) > 3000:
            text = text[:3000] + '\n...[内容截断]'
        return f'[HTTP {r.status_code}]\n{text}'
    except Exception as e:
        return f'[抓取失败] {type(e).__name__}: {e}'


# ---- 内部接口：仅允许带内部 header 的请求（模拟内网隔离）----
@app.route('/internal/flag')
def internal_flag():
    if request.headers.get('X-Internal-Request') != 'LinkPeek':
        return '拒绝访问：此接口仅应用服务器内部可调用'
    record_flag('f1', FLAG1)
    return FLAG1


@app.route('/internal/metadata')
def internal_metadata():
    if request.headers.get('X-Internal-Request') != 'LinkPeek':
        return '拒绝访问：此接口仅应用服务器内部可调用'
    record_flag('f2', FLAG2)
    meta = (
        'AWS metadata service (169.254.169.254) 模拟\n'
        '==========================================\n'
        'ami-id: ami-0abc123\n'
        'instance-id: i-0xyz789\n'
        'iam/security-credentials/linkpeek-role:\n'
        '{\n'
        '  "AccessKeyId": "AKIA_SSRF_DEMO_2026",\n'
        '  "SecretAccessKey": "ssrf-demo-secret-key-987654321",\n'
        f'  "Token": "{FLAG2}"\n'
        '}\n'
    )
    return meta


@app.route('/internal/admin')
def internal_admin():
    if request.headers.get('X-Internal-Request') != 'LinkPeek':
        return '拒绝访问：此接口仅应用服务器内部可调用'
    record_flag('f3', FLAG3)
    return (
        '=== LinkPeek 内部管理面板 (仅内网) ===\n'
        'status: OK\n'
        'version: 2.4.1\n'
        'debug: enabled\n'
        f'admin_token: {FLAG3}\n'
    )


@app.route('/reset')
def reset():
    db = get_db()
    db.execute("UPDATE flags SET f1=NULL, f2=NULL, f3=NULL WHERE id=1")
    db.commit()
    db.close()
    return render('<div class="card"><p>已重置 FLAG</p><a class="btn" href="/">返回</a></div>')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5026, debug=False, threaded=True)
