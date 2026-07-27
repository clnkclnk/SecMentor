#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSRF (服务端请求伪造) 靶场
Level 1: 漏洞版 - 服务器按用户给的 URL 去请求，不做任何限制（可被利用访问内网）
Level 2: 防御版 - 白名单，只允许访问指定外域，内网/本地一律拒绝
端口: 5004
"""
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
PORT = 5004


def fetch_url(url, timeout=4):
    """模拟 SSRF 的 fetch 行为：服务器去请求用户指定的 URL。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SecMentor-SSRF-Lab/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            text = data[:1200].decode("utf-8", errors="replace")
            return True, f"HTTP {resp.status} | 返回 {len(data)} 字节\n\n{text}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP 错误 {e.code}: {e.reason}"
    except Exception as e:
        return False, f"请求失败：{e}"


class Handler(BaseHTTPRequestHandler):
    def _html(self, body, status=200, title="SSRF 靶场"):
        html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<style>
body{{font-family:system-ui;max-width:840px;margin:40px auto;padding:0 16px;background:#0f1117;color:#e6e6e6}}
h1{{color:#7ee787}} h3{{color:#e6e6e6}} .ok{{color:#7ee787}} .bad{{color:#ff7b72}}
.box{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin:12px 0;white-space:pre-wrap;font-family:ui-monospace,monospace;word-break:break-all}}
input{{padding:8px;width:440px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#e6e6e6}}
button{{padding:8px 16px;border:0;border-radius:6px;background:#238636;color:#fff;cursor:pointer}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-bottom:8px}}
.badge.v{{background:#ff7b7222;color:#ff7b72;border:1px solid #ff7b72}}
.badge.s{{background:#7ee78722;color:#7ee787;border:1px solid #7ee787}}
code{{background:#0d1117;padding:1px 5px;border-radius:4px;color:#ffa657}}
a{{color:#58a6ff}}
</style></head><body>
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
        url = qs.get("url", [""])[0]

        if parsed.path == "/secret":
            self._show_secret()
        elif parsed.path == "/meta":
            self._show_meta()
        elif parsed.path == "/redis":
            self._show_redis()
        elif parsed.path in ("/", "/index.html"):
            self._render_home(level, url)
        else:
            self.send_response(404)
            self.end_headers()

    def _show_secret(self):
        # 内部密钥接口：本应只有服务器/内网能访问
        body = '<div class="box ok">🔐 内部密钥接口 (模拟内网服务) 返回：\nFLAG{ssrf_internal_access_2026_gotcha}</div>'
        self._html(body)

    def _show_meta(self):
        # 模拟云元数据服务（真实 AWS/GCP 在 169.254.169.254）
        body = ('<div class="box ok">☁️ 云元数据接口 (模拟 169.254.169.254) 返回：\n'
                'ami-id = i-0abc123def456\n'
                'instance-id = i-0abc123def456\n'
                'secret-access-key = AKIA_SSRF_DEMO_KEY_****\n'
                '→ 真实环境下这就是云厂商临时凭证，能直接操控整朵云</div>')
        self._html(body)

    def _show_redis(self):
        # 模拟本机 Redis（真实在 127.0.0.1:6379）
        body = ('<div class="box ok">🗄️ 本机 Redis 接口 (模拟 127.0.0.1:6379) 返回：\n'
                'PING\n'
                '*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$10\r\npwned_ssrf\r\n'
                '→ 真实环境下可直接写入恶意 key / 窃取数据</div>')
        self._html(body)

    def _render_home(self, level, url):
        if url:
            if level == "2":
                # 防御版：白名单校验
                allowed_hosts = {"example.com", "cdn.trusted.net", "secmentor.demo"}
                parsed_url = urlparse(url)
                host = (parsed_url.hostname or "").lower()
                # 拦截内网/本地地址
                if host in ("127.0.0.1", "localhost") or host.startswith("169.254") \
                        or host.startswith("192.168") or host.startswith("10.") or host == "":
                    body = (f'<span class="badge v">Level 2 · 防御版</span>'
                            f'<h1>🚫 请求被拦截</h1>'
                            f'<div class="box bad">目标主机 <code>{host or "(空)"}</code> 属于内网/本地地址，已被白名单策略拒绝。</div>'
                            f'<p class="bad">这就是 SSRF 防御：只允许访问白名单外域，内网/本地一律拒绝。</p>')
                    self._html(body)
                    return
                if host not in allowed_hosts:
                    body = (f'<span class="badge v">Level 2 · 防御版</span>'
                            f'<h1>🚫 请求被拦截</h1>'
                            f'<div class="box bad">主机 <code>{host}</code> 不在白名单（{", ".join(allowed_hosts)}）内，已拒绝。</div>')
                    self._html(body)
                    return
            # Level 1 或白名单通过
            ok, result = fetch_url(url)
            if level == "1":
                badge = '<span class="badge v">Level 1 · 漏洞版（服务器任意发请求）</span>'
            else:
                badge = '<span class="badge s">Level 2 · 防御版（白名单通过）</span>'
            cls = "ok" if ok else "bad"
            body = (f'{badge}'
                    f'<h1>📡 服务器已替你请求：<code>{url}</code></h1>'
                    f'<div class="box {cls}">{result}</div>'
                    f'<p>↑ 看，服务器真的跑去请求了你给的地址，并把结果带了回来。</p>')
            self._html(body)
            return

        # 首页（没给 url）
        hint = "漏洞版" if level == "1" else "防御版"
        body = f'''<span class="badge v">Level {level} · {hint}</span>
<h1>SSRF 靶场 · 让服务器当你的内网代理</h1>
<p>在下方填入一个 URL，让服务器替你去请求它，并把结果返回给你。</p>
<form method="get">
  <input type="hidden" name="level" value="{level}">
  <input type="text" name="url" placeholder="http://127.0.0.1:5004/secret" value="">
  <button type="submit">▶ 让服务器去请求</button>
</form>

<h3>🔥 试试这些（Level 1 漏洞版下全部成功）：</h3>
<div class="box">
# 1. 借服务器身份访问"内部密钥接口"（模拟内网服务）
http://127.0.0.1:5004/secret

# 2. 借服务器身份访问"云元数据"（真实是 169.254.169.254）
http://127.0.0.1:5004/meta

# 3. 借服务器身份访问"本机 Redis"（真实是 127.0.0.1:6379）
http://127.0.0.1:5004/redis
</div>
<p>切到 <a href="/?level=2">Level 2 防御版</a> 再打同样的 URL，看被怎么拦截。</p>
'''
        self._html(body)

    def log_message(self, fmt, *args):
        pass  # 安静


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"SSRF 靶场已启动: http://{HOST}:{PORT}/?level=1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
