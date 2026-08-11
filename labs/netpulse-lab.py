# -*- coding: utf-8 -*-
"""
NetPulse 内网监控平台 —— SSRF 进阶靶场（有逻辑链）
端口: 5027
主题: 你输入一个 URL，服务器替你去检查"这个网站是否在线"，返回状态。
      这个"替你访问 URL"的功能就是 SSRF 入口。

逻辑链:
  FLAG1 基础内网探测  -> 访问 /internal/status 拿到内网地图 + 提示读本地文件
  FLAG2 协议升级 file -> 用 file:// 读本地 netpulse_secret.txt，拿到 Redis 密码 + FLAG2
  FLAG3 信息串联      -> 用读到的密码访问 /internal/redis?pwd=xxx 打内网 Redis，拿 FLAG3
  FLAG4 黑名单绕过    -> /safe 拦 127.0.0.1/localhost，用 localtest.me 域名绕过访问 /internal/secret
"""
import os
import sqlite3
import time
from urllib.parse import urlparse, parse_qs

import requests
from flask import Flask, request, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "netpulse.db")
SECRET_FILE = os.path.join(BASE_DIR, "netpulse_secret.txt")
PORT = 5027
REDIS_PWD = "redispass_2026"

app = Flask(__name__)

# ----------------------------- 数据库 -----------------------------
def init_db():
    db = sqlite3.connect(DB)
    db.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            flag1 TEXT, flag2 TEXT, flag3 TEXT, flag4 TEXT
        )"""
    )
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
    db.commit()
    db.close()


def get_flags():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT flag1,flag2,flag3,flag4 FROM users WHERE id=1").fetchone()
    db.close()
    return row


def set_flag(name):
    db = sqlite3.connect(DB)
    db.execute(f"UPDATE users SET {name}=? WHERE id=1", (f"FLAG_{name}",))
    db.commit()
    db.close()


def add_history(url, snippet):
    db = sqlite3.connect(DB)
    db.execute(
        "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, url TEXT, snippet TEXT, ts REAL)"
    )
    db.execute(
        "INSERT INTO history (url, snippet, ts) VALUES (?,?,?)",
        (url[:300], snippet[:200], time.time()),
    )
    db.commit()
    db.close()


# ----------------------------- 页面模板 -----------------------------
PAGE = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>NetPulse 内网监控平台</title>
<style>
 body{font-family:system-ui,Arial,sans-serif;max-width:820px;margin:40px auto;padding:0 16px;background:#0f1320;color:#e6e6e6}
 h1{color:#5ad}
 .card{background:#1b2233;border:1px solid #2d3650;border-radius:10px;padding:16px;margin:16px 0}
 input[type=text]{width:70%;padding:8px;border-radius:6px;border:1px solid #3a4560;background:#0f1320;color:#e6e6e6}
 button{padding:8px 16px;border:0;border-radius:6px;background:#5ad;color:#06121f;font-weight:bold;cursor:pointer}
 .result{white-space:pre-wrap;background:#0a0d16;border:1px solid #2d3650;border-radius:8px;padding:12px;margin-top:10px;font-family:monospace;font-size:13px;max-height:240px;overflow:auto}
 .flags{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
 .flag{width:48%;box-sizing:border-box;padding:10px;border-radius:8px;font-weight:bold}
 .on{background:#16351f;color:#7fffa0;border:1px solid #2f7a45}
 .off{background:#241b1b;color:#7a5555;border:1px solid #5a3030}
 a{color:#5ad}
 code{background:#0a0d16;padding:2px 5px;border-radius:4px}
</style></head>
<body>
<h1>NetPulse 内网监控平台</h1>
<p>输入任意网址，服务器替你检查该站点是否在线，并返回状态摘要。</p>

<div class="flags">
  <div class="flag {{'on' if flags.flag1 else 'off'}}">FLAG 1 · 基础内网探测 {{'✅' if flags.flag1 else '🔒'}}</div>
  <div class="flag {{'on' if flags.flag2 else 'off'}}">FLAG 2 · 协议升级 file:// {{'✅' if flags.flag2 else '🔒'}}</div>
  <div class="flag {{'on' if flags.flag3 else 'off'}}">FLAG 3 · 串联打内网 Redis {{'✅' if flags.flag3 else '🔒'}}</div>
  <div class="flag {{'on' if flags.flag4 else 'off'}}">FLAG 4 · 黑名单绕过 {{'✅' if flags.flag4 else '🔒'}}</div>
</div>

<div class="card">
  <h3>① 网站监控（/monitor）</h3>
  <form method="get" action="/monitor">
    <input type="text" name="url" placeholder="https://example.com" value="{{url or ''}}">
    <button type="submit">检查在线状态</button>
  </form>
  {% if monitor_result %}<div class="result">{{monitor_result}}</div>{% endif %}
</div>

<div class="card">
  <h3>② 安全监控（/safe，已加黑名单防护）</h3>
  <form method="get" action="/safe">
    <input type="text" name="url" placeholder="https://example.com" value="{{safe_url or ''}}">
    <button type="submit">安全检查</button>
  </form>
  {% if safe_result %}<div class="result">{{safe_result}}</div>{% endif %}
</div>

<p><a href="/history">查看服务器访问历史 →</a> &nbsp;|&nbsp; <a href="/reset">重置账号</a></p>
</body></html>"""


def render(flags=None, **kw):
    if flags is None:
        flags = get_flags()
    return render_template_string(PAGE, flags=flags, **kw)


# ----------------------------- 路由 -----------------------------
@app.route("/")
def index():
    return render()


@app.route("/monitor")
def monitor():
    url = request.args.get("url", "")
    if not url:
        return render(monitor_result="请输入要监控的 URL")
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    result = ""

    if scheme in ("http", "https"):
        try:
            r = requests.get(url, timeout=5, headers={"User-Agent": "NetPulse-Monitor/1.0"})
            result = f"[状态码 {r.status_code}]\n" + r.text[:500]
        except Exception as e:
            result = f"访问失败: {type(e).__name__}: {e}"
        # 内部接口检测
        if parsed.hostname in ("127.0.0.1", "localhost") and parsed.port == PORT:
            path = parsed.path
            if path == "/internal/status":
                set_flag("flag1")
                result += "\n[+] 检测到内网状态接口，FLAG1 已记录"
            if path == "/internal/redis":
                pwd = parse_qs(parsed.query).get("pwd", [None])[0]
                if pwd == REDIS_PWD:
                    set_flag("flag3")
                    result += "\n[+] Redis 密码正确，已访问内网 Redis 服务，FLAG3 已记录"
                else:
                    result += "\n[-] 内网 Redis 服务要求密码（pwd 参数）"

    elif scheme == "file":
        # 协议升级：读取服务器本地文件，但限制只能读本应用目录内
        fpath = parsed.path
        if fpath.startswith("/"):
            fpath = fpath[1:]
        abspath = os.path.abspath(fpath)
        if abspath.startswith(BASE_DIR):
            try:
                with open(abspath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                result = f"[本地文件内容 {abspath}]\n" + content[:800]
                if abspath == SECRET_FILE:
                    set_flag("flag2")
                    result += "\n[+] 读取到本地敏感配置文件，FLAG2 已记录"
            except Exception as e:
                result = f"读文件失败: {e}"
        else:
            result = "[拦截] 文件读取被限制在本应用目录内（防止任意文件读取）"

    else:
        result = f"[未知协议 {scheme}] 本监控仅支持 http / https / file 协议"

    add_history(url, result)
    return render(url=url, monitor_result=result)


@app.route("/safe")
def safe():
    url = request.args.get("url", "")
    if not url:
        return render(safe_result="请输入要安全检查的 URL")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    blocked = ["127.0.0.1", "localhost", "0.0.0.0", "[::1]", "169.254"]
    # 黑名单：检查主机名是否命中内网
    if any(b in host for b in blocked):
        return render(safe_url=url, safe_result="[拦截] 黑名单禁止访问内网地址")
    # 即使域名解析到本机（如 localtest.me -> 127.0.0.1），主机名本身不在黑名单则放行
    try:
        r = requests.get(
            url, timeout=5, headers={"User-Agent": "NetPulse-Safe/1.0", "X-NetPulse-Internal": "true"}
        )
        result = f"[状态码 {r.status_code}]\n" + r.text[:500]
        if parsed.path == "/internal/secret":
            set_flag("flag4")
            result += "\n[+] 绕过黑名单访问内部管理接口，FLAG4 已记录"
    except Exception as e:
        result = f"访问失败: {type(e).__name__}: {e}"
    add_history(url, result)
    return render(safe_url=url, safe_result=result)


@app.route("/internal/status")
def internal_status():
    # 只有服务器自己（SSRF）能稳定访问；外部直连也能看，但这是内网地图
    data = {
        "services": {
            "redis_sim": "127.0.0.1:6379 (本靶场用 /internal/redis 模拟, 需密码)",
            "secret_config_file": "服务器本地文件 netpulse_secret.txt",
            "secret_api": "/internal/secret (需内部请求头)",
        },
        "hint": "SSRF 不只是访问内网 HTTP。试试 file:// 协议读取本地配置文件 "
        "netpulse_secret.txt，里面藏着打内网 Redis 的密码。",
    }
    return data


@app.route("/internal/redis")
def internal_redis():
    pwd = request.args.get("pwd", "")
    if pwd == REDIS_PWD:
        return f"Redis OK\nFLAG3{{ssrf_chain_redis_internal_2026}}\n(模拟内网 Redis 被成功访问)"
    return "NOAUTH Authentication required.", 401


@app.route("/internal/secret")
def internal_secret():
    if request.headers.get("X-NetPulse-Internal") == "true":
        return "FLAG4{ssrf_blacklist_bypass_netpulse_2026}\n[内部管理接口] 仅允许内部请求访问"
    return "拒绝访问：仅允许内部请求（缺少 X-NetPulse-Internal 头）", 403


@app.route("/history")
def history():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    rows = db.execute("SELECT url,snippet,ts FROM history ORDER BY id DESC LIMIT 20").fetchall()
    db.close()
    html = "<h2>服务器访问历史</h2><p>服务器替你访问过的地址（半回显，可用于盲 SSRF 验证）：</p><ul>"
    for r in rows:
        html += f"<li><code>{r['url']}</code><br><small>{r['snippet']}</small></li>"
    html += "</ul><p><a href='/'>返回</a></p>"
    return html


@app.route("/reset")
def reset():
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag1=NULL,flag2=NULL,flag3=NULL,flag4=NULL WHERE id=1")
    db.execute("DROP TABLE IF EXISTS history")
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
