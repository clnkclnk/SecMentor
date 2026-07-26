#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LFI (本地文件包含) 靶场
Level 1: 漏洞版 - 用户控制 include 的文件名，且 include = exec()
Level 2: 防御版 - 白名单，只允许 home/about
"""
import os
import io
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")
HOST = "127.0.0.1"
PORT = 5003


class Handler(BaseHTTPRequestHandler):
    def _html(self, body, status=200, title="LFI 靶场"):
        html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:system-ui;max-width:760px;margin:40px auto;padding:0 16px;background:#0f1117;color:#e6e6e6}}
h1{{color:#7ee787}}.ok{{color:#7ee787}}.bad{{color:#ff7b72}}.box{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin:12px 0;white-space:pre-wrap;font-family:ui-monospace,monospace}}
input{{padding:8px;width:300px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#e6e6e6}}
button{{padding:8px 16px;border:0;border-radius:6px;background:#238636;color:#fff;cursor:pointer}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-bottom:8px}}
.badge.v{{background:#ff7b7222;color:#ff7b72;border:1px solid #ff7b72}}
.badge.s{{background:#7ee78722;color:#7ee787;border:1px solid #7ee787}}
code{{background:#0d1117;padding:1px 5px;border-radius:4px;color:#ffa657}}
a{{color:#58a6ff}}</style></head><body>
{body}</body></html>"""
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        level = qs.get("level", ["1"])[0]
        page = qs.get("page", [""])[0]
        if parsed.path in ("/", "/index.html"):
            self._render_home(level, page)
        else:
            self.send_response(404)
            self.end_headers()

    def _render_home(self, level, page):
        if level == "2":
            badge = '<span class="badge s">🛡️ Level 2 · 白名单防御版</span>'
        else:
            badge = '<span class="badge v">⚠️ Level 1 · 漏洞版（include = exec）</span>'

        result_html = ""
        if page:
            if level == "2":
                result_html = self._defended(page)
            else:
                result_html = self._vulnerable(page)

        body = f"""
<h1>📂 LFI 文件包含靶场</h1>
{badge}
<p>模拟 PHP 的 <code>include($_GET['page'])</code>。输入 page 参数，看服务器怎么处理你的文件。</p>
<form method="get">
<input type="hidden" name="level" value="{level}">
<label>page 参数：<input type="text" name="page" value="{page}" placeholder="home 或 about"></label>
<button type="submit">包含！</button>
</form>
<hr style="border-color:#30363d">
{result_html}
<hr style="border-color:#30363d">
<p style="color:#8b949e;font-size:13px">
🧪 试试这些 payload：<br>
• 正常：<code>home</code> / <code>about</code><br>
• 读秘密：<code>../lfi_secret.py</code>（穿越到 pages 外的秘密文件，被当成代码执行）<br>
• RCE：<code>webshell</code>（包含执行系统命令的"页面"，直接拿服务器权限）<br>
切到 Level 2 体验白名单防御：<a href="/?level=2">/?level=2</a>
</p>
"""
        self._html(body)

    def _exec_file(self, target):
        """模拟 include()：读取文件并当作 Python 代码执行，返回执行输出。"""
        with open(target, "r", encoding="utf-8") as f:
            code = f.read()
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            exec(code, {"__name__": "__lfi__", "os": __import__("os")})
            return buf.getvalue()
        finally:
            sys.stdout = old

    def _vulnerable(self, page):
        # ❌ 漏洞版：用户控制 include 路径，且用 exec 执行文件内容
        target = os.path.join(PAGES_DIR, page)
        if not os.path.isfile(target):
            return f'<div class="box bad">❌ 文件不存在：{target}</div>'
        try:
            out = self._exec_file(target)
            return (f'<div class="box"><span class="ok">✅ 已 include 并执行：{page}</span>\n'
                    f'── 执行输出 ──\n{out}</div>')
        except Exception as e:
            return f'<div class="box bad">⚠️ 包含并执行时报错（说明它不是合法代码）：{e}</div>'

    def _defended(self, page):
        # ✅ 白名单：只允许 home / about
        allowed = {"home", "about"}
        if page not in allowed:
            return (f'<div class="box bad">⛔ 拦截！"{page}" 不在白名单（home/about）。\n'
                    f'防御：include 前先校验 page ∈ 白名单。穿越 / 任意文件都进不来。</div>')
        target = os.path.join(PAGES_DIR, page)
        try:
            out = self._exec_file(target)
            return (f'<div class="box"><span class="ok">✅ 白名单通过，已包含：{page}</span>\n'
                    f'── 执行输出 ──\n{out}</div>')
        except Exception as e:
            return f'<div class="box bad">执行出错：{e}</div>'

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    os.makedirs(PAGES_DIR, exist_ok=True)
    home = os.path.join(PAGES_DIR, "home")
    if not os.path.exists(home):
        with open(home, "w", encoding="utf-8") as f:
            f.write('print("欢迎来到首页！这是正常包含的页面。")')
    about = os.path.join(PAGES_DIR, "about")
    if not os.path.exists(about):
        with open(about, "w", encoding="utf-8") as f:
            f.write('print("关于我们：这是一个用 include 拼接的页面。")')
    webshell = os.path.join(PAGES_DIR, "webshell")
    if not os.path.exists(webshell):
        with open(webshell, "w", encoding="utf-8") as f:
            f.write('import os\n'
                    'print("🐚 RCE 成功！当前系统用户：", os.popen("whoami").read().strip())\n')
    secret = os.path.join(BASE_DIR, "lfi_secret.py")
    if not os.path.exists(secret):
        with open(secret, "w", encoding="utf-8") as f:
            f.write('print("🔑 数据库连接密码: SuperSecret123!  —— 这个文件在 pages 目录外，本不该被访问。")')
    print(f"LFI 靶场启动: http://{HOST}:{PORT}/?level=1")
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    srv.serve_forever()
