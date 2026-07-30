#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 未授权访问 演示靶场 (Web 版)  :5008
Level 1: 无认证 -> 任何命令直接执行（演示未授权访问危害）
Level 2: 需密码 -> 无密码拒绝（演示正确加固）
仅用于授权学习环境，严禁用于真实目标。
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus

HOST = "127.0.0.1"
PORT = 5008

# 模拟 Redis 内存库
DB = {
    "flag": "FLAG{redis_unauth_leaked_2026}",
    "user:1": "alice",
    "session:abc": "token-xxxxx",
}
PASSWORD = "StrongPass#2026"  # Level2 需要的密码


def execute(cmdline):
    parts = cmdline.strip().split()
    if not parts:
        return "(空命令)"
    cmd = parts[0].upper()
    if cmd == "PING":
        return "PONG"
    if cmd == "SET" and len(parts) >= 3:
        DB[parts[1]] = " ".join(parts[2:])
        return "OK"
    if cmd == "GET" and len(parts) >= 2:
        return DB.get(parts[1], "(nil)")
    if cmd == "KEYS":
        return " ".join(DB.keys())
    if cmd == "CONFIG" and len(parts) >= 3 and parts[1].upper() == "GET":
        if parts[2].upper() == "DIR":
            return os.getcwd()
        if parts[2].upper() == "DBFILENAME":
            return "dump.rdb"
        return "(nil)"
    return f"ERR unknown command {cmd}"


PAGE = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:system-ui;max-width:860px;margin:40px auto;padding:0 16px;background:#0f1117;color:#e6e6e6}}
h1{{color:#7ee787;font-weight:500}}code{{background:#0d1117;padding:2px 6px;border-radius:4px;color:#ffa657}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-bottom:8px}}
.badge.v{{background:#ff7b7222;color:#ff7b72;border:1px solid #ff7b72}}
.badge.s{{background:#7ee78722;color:#7ee787;border:1px solid #7ee787}}
.box{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin:12px 0;white-space:pre-wrap;font-family:ui-monospace,monospace;word-break:break-all}}
input{{padding:8px;width:380px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#e6e6e6}}
button{{padding:8px 16px;border:0;border-radius:6px;background:#238636;color:#fff;cursor:pointer;margin:4px 4px 4px 0}}
.note{{font-size:12px;color:#8b949e;margin-top:8px}}a{{color:#58a6ff;text-decoration:none}}</style></head><body>
{body}
</body></html>"""


def render_home(level, pw, cmd, result, denied):
    tag = "漏洞版 Level 1（无认证）" if level != "2" else "防御版 Level 2（需密码）"
    badge = "v" if level != "2" else "s"
    body = f"""
<h1>Redis 未授权访问 靶场</h1>
<span class="badge {badge}">{tag}</span>
<p>这是一个模拟 Redis 服务的控制台。试试这些命令：</p>
<p><code>PING</code> · <code>KEYS *</code> · <code>GET flag</code> · <code>CONFIG GET DIR</code></p>
<form method="get" action="/">
  <input type="hidden" name="level" value="{level}">
  <input type="hidden" name="pw" value="{pw}">
  <input name="cmd" value="{cmd}" placeholder="输入 Redis 命令，如 KEYS *">
  <button type="submit">▶ 执行</button>
</form>
"""
    if denied:
        body += f'<div class="box bad">⛔ 无密码或密码错误：所有命令被拒绝（防御版已修复未授权访问）。</div>'
    elif result is not None:
        leak = ""
        if "flag" in cmd and "GET" in cmd.upper():
            leak = "\n\n[!] 你无需密码就读取到了机密 FLAG —— 这就是未授权访问的危害。"
        if "KEYS" in cmd.upper():
            leak = "\n\n[!] 你无需密码就列光了所有键 —— 业务数据全部暴露。"
        body += f'<div class="box">{result}{leak}</div>'
    body += f"""
<p class="note">真实危害：攻击者拿到未授权 Redis 后，可用 CONFIG SET dir + dbfilename + SAVE 把任意内容写成文件（WebShell / SSH 公钥）→ 直接 RCE。本靶场仅演示读取，不做破坏性写入。</p>
<p><a href="/?level=1">切到 漏洞版 Level 1</a> | <a href="/?level=2">切到 防御版 Level 2</a></p>
"""
    if level == "2":
        body += '<p class="note">防御版需要密码（演示用 <code>StrongPass#2026</code>）。在命令前加密码参数，或用下方输入框。</p>'
    return PAGE.format(title="Redis 未授权访问靶场", body=body)


class Handler(BaseHTTPRequestHandler):
    def _send(self, html, status=200):
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
        pw = unquote_plus(qs.get("pw", [""])[0])
        cmd = unquote_plus(qs.get("cmd", [""])[0])

        denied = False
        result = None
        if cmd:
            if level == "2" and pw != PASSWORD:
                denied = True
            else:
                result = execute(cmd)
        self._send(render_home(level, pw, cmd, result, denied))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Redis 未授权访问靶场启动: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
