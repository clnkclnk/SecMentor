#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令注入 (Command Injection) 靶场  :5007
Level 1: 漏洞版 - 用户输入直接拼进命令行，且不校验分隔符 -> 可注入执行任意命令
Level 2: 防御版 - 白名单(只允许IP) + 参数化(shell=False) -> 注入失效
"""
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus

HOST = "127.0.0.1"
PORT = 5007


def split_shell(cmd):
    """简易 shell 拆分（教学用，跨平台一致）：按 ; 和 & 顺序执行。"""
    return [p.strip() for p in re.split(r"[;&]", cmd) if p.strip()]


def exec_vulnerable(user_input):
    """漏洞版：把用户输入拼进命令行，并模拟 shell 顺序执行分隔出的各段。"""
    command = "ping -n 1 " + user_input
    parts = split_shell(command)
    lines = [f"[构造命令] {command}", ""]
    for p in parts:
        try:
            r = subprocess.run(p, shell=True, capture_output=True, text=True, timeout=6)
            lines.append(f"$ {p}\n{(r.stdout + r.stderr).strip()}")
        except Exception as e:
            lines.append(f"$ {p}\n[执行错误] {e}")
    return "\n".join(lines)


def exec_safe(user_input):
    """防御版：白名单(只允许IP格式) + 参数化(不开 shell) -> 分隔符直接失效。"""
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", user_input):
        return ("[构造命令] ping -n 1 " + user_input + "\n\n"
                "[安全拒绝] host 不是合法 IP 格式，已拒绝。\n"
                "不执行任何命令（防御：白名单 + 参数化 shell=False）。")
    try:
        r = subprocess.run(["ping", "-n", "1", user_input], capture_output=True, text=True, timeout=6)
        return f"[构造命令] ping -n 1 {user_input}（参数化，不开 shell）\n\n{r.stdout + r.stderr}"
    except Exception as e:
        return f"[执行错误] {e}"


PAGE = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:system-ui;max-width:840px;margin:40px auto;padding:0 16px;background:#0f1117;color:#e6e6e6}}
h1{{color:#7ee787;font-weight:500}}code{{background:#0d1117;padding:2px 6px;border-radius:4px;color:#ffa657}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-bottom:8px}}
.badge.v{{background:#ff7b7222;color:#ff7b72;border:1px solid #ff7b72}}
.badge.s{{background:#7ee78722;color:#7ee787;border:1px solid #7ee787}}
.box{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin:12px 0;white-space:pre-wrap;font-family:ui-monospace,monospace;word-break:break-all}}
input{{padding:8px;width:440px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#e6e6e6}}
button{{padding:8px 16px;border:0;border-radius:6px;background:#238636;color:#fff;cursor:pointer;margin:4px 4px 4px 0}}
a{{color:#58a6ff;text-decoration:none}}</style></head><body>
{body}
<script>
function load(v){{ document.getElementById('host').value = v; }}
</script>
</body></html>"""


def render_home(level, host):
    body = f"""
<h1>命令注入靶场</h1>
<span class="badge {'v' if level!='2' else 's'}">{'漏洞版 Level 1' if level!='2' else '防御版 Level 2'}</span>
<p>功能：输入一个 IP，服务器会执行 <code>ping -n 1 &lt;你输入的IP&gt;</code> 并返回结果。</p>
<p>思考：如果把 <code>;</code> 或 <code>&amp;</code> 混进输入，会发生什么？</p>
<form method="get" action="/ping">
  <input type="hidden" name="level" value="{level}">
  <input id="host" name="host" value="{host}" placeholder="例如 127.0.0.1">
  <button type="submit">▶ 执行 ping</button>
</form>
<p>
  <button onclick="load('127.0.0.1')">载入: 正常 127.0.0.1</button>
  <button onclick="load('127.0.0.1; whoami')">载入: 注入 127.0.0.1; whoami</button>
</p>
<p><a href="/?level=1">切到 漏洞版 Level 1</a> | <a href="/?level=2">切到 防御版 Level 2</a></p>
"""
    return PAGE.format(title="命令注入靶场", body=body)


def render_result(level, host, result, badge):
    tag = "漏洞版 Level 1（执行了用户输入拼接的命令）" if badge == "vuln" else "防御版 Level 2（白名单 + 参数化）"
    body = f"""
<h1>执行结果</h1>
<span class="badge {'v' if badge=='vuln' else 's'}">{tag}</span>
<p>你提交的 host 参数：<code>{host}</code></p>
<div class="box">{result}</div>
<p><a href="/?level={level}">← 返回</a> | <a href="/?level=1">切到 漏洞版</a> | <a href="/?level=2">切到 防御版</a></p>
"""
    return PAGE.format(title="执行结果", body=body)


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
        host = unquote_plus(qs.get("host", [""])[0])
        if parsed.path in ("/", "/index.html"):
            self._send(render_home(level, host))
        elif parsed.path == "/ping":
            if level == "2":
                self._send(render_result("2", host, exec_safe(host), "safe"))
            else:
                self._send(render_result("1", host, exec_vulnerable(host), "vuln"))
        else:
            self._send("<h1>404</h1>", 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"命令注入靶场启动: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
