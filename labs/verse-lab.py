# -*- coding: utf-8 -*-
"""
Verse 社区论坛 —— XSS 进阶靶场
端口: 5028
主题: 一个小社区，有搜索、留言板、个人简介、欢迎页等功能。
      5 个功能点：4 个有 XSS 漏洞（三种类型 + 多种绕过），1 个安全对照。

FLAG:
  FLAG1 反射型  -> /search?q= 搜索框无过滤，直接 <script>
  FLAG2 存储型  -> /board 留言板过滤 <script>，用 <img onerror> 绕过
  FLAG3 存储型  -> /profile 简介过滤 <script>+事件，用 javascript: 伪协议绕过
  FLAG4 DOM型   -> /welcome 前端 JS 读 hash 写 innerHTML
  安全对照      -> /about 正确转义，无法注入
"""
import os
import re
import sqlite3
import time
from flask import Flask, request, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "verse.db")
PORT = 5028

app = Flask(__name__)

FLAGS = {
    "flag1": "FLAG1{xss_reflected_search_2026}",
    "flag2": "FLAG2{xss_stored_board_bypass_2026}",
    "flag3": "FLAG3{xss_stored_bio_javascript_2026}",
    "flag4": "FLAG4{xss_dom_welcome_2026}",
}


def init_db():
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, flag1 TEXT, flag2 TEXT, flag3 TEXT, flag4 TEXT)")
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
    db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, content TEXT, ts REAL)")
    db.execute("CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, bio TEXT)")
    db.execute("INSERT OR IGNORE INTO profiles (id, bio) VALUES (1, '这个人很懒，什么都没留')")
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
    db.execute("UPDATE users SET " + name + "=? WHERE id=1", (FLAGS[name],))
    db.commit()
    db.close()


def get_messages():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    rows = db.execute("SELECT content,ts FROM messages ORDER BY id DESC LIMIT 20").fetchall()
    db.close()
    return rows


def add_message(content):
    db = sqlite3.connect(DB)
    db.execute("INSERT INTO messages (content,ts) VALUES (?,?)", (content, time.time()))
    db.commit()
    db.close()


def get_bio():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT bio FROM profiles WHERE id=1").fetchone()
    db.close()
    return row["bio"]


def set_bio(bio):
    db = sqlite3.connect(DB)
    db.execute("UPDATE profiles SET bio=? WHERE id=1", (bio,))
    db.commit()
    db.close()


def filter_board(content):
    """留言板：只过滤 <script> 标签，其他不管"""
    return re.sub(r'</?script>', '', content, flags=re.I)


def filter_bio(content):
    """个人简介：过滤 <script> + 所有事件处理器 onXXX=，但不防 javascript: 伪协议"""
    content = re.sub(r'</?script', '', content, flags=re.I)
    content = re.sub(r'on\w+\s*=', '', content, flags=re.I)
    return content


STYLE = ("body{font-family:system-ui,Arial,sans-serif;max-width:860px;margin:30px auto;padding:0 16px;"
         "background:#0f1320;color:#e6e6e6}"
         "h1{color:#5ad;margin:0 0 8px}"
         "nav{margin:12px 0;padding:10px;background:#1b2233;border-radius:8px}"
         "nav a{color:#5ad;margin-right:14px;text-decoration:none}"
         ".card{background:#1b2233;border:1px solid #2d3650;border-radius:10px;padding:14px;margin:14px 0}"
         "input[type=text],textarea{padding:8px;border-radius:6px;border:1px solid #3a4560;background:#0f1320;color:#e6e6e6}"
         "input[type=submit]{padding:8px 16px;border:0;border-radius:6px;background:#5ad;color:#06121f;font-weight:bold;cursor:pointer}"
         ".flags{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}"
         ".flag{width:48%;box-sizing:border-box;padding:8px;border-radius:8px;font-size:13px}"
         ".on{background:#16351f;color:#7fffa0;border:1px solid #2f7a45}"
         ".off{background:#241b1b;color:#7a5555;border:1px solid #5a3030}"
         ".msg{background:#0a0d16;border:1px solid #2d3650;border-radius:6px;padding:10px;margin:8px 0}"
         ".result{white-space:pre-wrap;background:#0a0d16;border:1px solid #2d3650;border-radius:8px;padding:12px;"
         "margin-top:10px;font-family:monospace;font-size:13px}"
         "code{background:#0a0d16;padding:2px 5px;border-radius:4px}")


def render(content_html=""):
    flags = get_flags()
    fc = lambda n: "on" if flags[n] else "off"
    fk = lambda n: "✅" if flags[n] else "🔒"
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>Verse 社区</title><style>" + STYLE + "</style></head><body>"
            "<h1>Verse 社区</h1>"
            "<p style='color:#888;margin:0 0 10px'>一个小而暖的论坛 · 搜索 / 留言 / 个人主页</p>"
            "<div class='flags'>"
            "<div class='flag " + fc('flag1') + "'>FLAG1 反射型 " + fk('flag1') + "</div>"
            "<div class='flag " + fc('flag2') + "'>FLAG2 存储型·绕script " + fk('flag2') + "</div>"
            "<div class='flag " + fc('flag3') + "'>FLAG3 存储型·绕事件 " + fk('flag3') + "</div>"
            "<div class='flag " + fc('flag4') + "'>FLAG4 DOM型 " + fk('flag4') + "</div>"
            "</div>"
            "<nav>"
            "<a href='/'>首页</a> <a href='/search'>搜索</a> <a href='/board'>留言板</a> "
            "<a href='/profile'>个人简介</a> <a href='/welcome'>欢迎页</a> <a href='/about'>关于</a> "
            "<a href='/reset'>重置</a>"
            "</nav>"
            + content_html +
            "</body></html>")


@app.route("/")
def index():
    content = ("<div class='card'><h3>欢迎来到 Verse</h3>"
               "<p>这是一个小社区。试试这些功能：</p>"
               "<ul>"
               "<li><a href='/search'>搜索</a> — 搜点东西</li>"
               "<li><a href='/board'>留言板</a> — 给社区留句话</li>"
               "<li><a href='/profile'>个人简介</a> — 改改你的主页</li>"
               "<li><a href='/welcome'>欢迎页</a> — 个性化欢迎语</li>"
               "<li><a href='/about'>关于</a> — 看看这个页为什么打不动</li>"
               "</ul>"
               "<p style='color:#888;font-size:13px'>提示：每个功能的过滤强度不一样，有的可能没有漏洞。</p>"
               "</div>")
    return render(content)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    # 漏洞：直接拼 q 进 HTML，无转义（反射型 XSS）
    result_html = ("<div class='result'>搜索结果: " + q + "</div>") if q else ""
    # 检测 FLAG1：q 里出现 <script 标签
    if "<script" in q.lower():
        set_flag("flag1")
    content = ("<div class='card'><h3>搜索</h3>"
               "<form method='get' action='/search'>"
               "<input type='text' name='q' value='" + q + "' placeholder='搜点啥'> "
               "<input type='submit' value='搜索'>"
               "</form>" + result_html + "</div>")
    return render(content)


@app.route("/board", methods=["GET", "POST"])
def board():
    if request.method == "POST":
        c = request.form.get("content", "")
        filtered = filter_board(c)
        add_message(filtered)
        return redirect("/board")
    msgs = get_messages()
    msg_html = ""
    for m in msgs:
        msg_html += "<div class='msg'>" + m["content"] + "</div>"
    # 检测 FLAG2：留言含 img+onerror（绕过 script 过滤成功注入事件标签）
    for m in msgs:
        cl = m["content"].lower()
        if "<img" in cl and "onerror" in cl:
            set_flag("flag2")
            break
    content = ("<div class='card'><h3>留言板</h3>"
               "<form method='post' action='/board'>"
               "<input type='text' name='content' placeholder='留句话' style='width:70%'> "
               "<input type='submit' value='发布'>"
               "</form>"
               "<p style='color:#888;font-size:12px'>系统已过滤 script 标签</p>"
               "</div>" + msg_html)
    return render(content)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        bio = request.form.get("bio", "")
        filtered = filter_bio(bio)
        set_bio(filtered)
        return redirect("/profile")
    bio = get_bio()
    # 检测 FLAG3：bio 含 javascript: 伪协议（绕过事件过滤）
    if "javascript:" in bio.lower():
        set_flag("flag3")
    content = ("<div class='card'><h3>个人简介</h3>"
               "<form method='post' action='/profile'>"
               "<textarea name='bio' style='width:70%;height:80px' placeholder='介绍一下自己'>" + bio + "</textarea><br>"
               "<input type='submit' value='保存'>"
               "</form>"
               "<p style='color:#888;font-size:12px'>系统已过滤 script 标签和事件处理器</p>"
               "</div>"
               "<div class='card'><h3>你的主页预览</h3>"
               "<div class='msg'>" + bio + "</div></div>")
    return render(content)


@app.route("/welcome")
def welcome():
    content = ("<div class='card'><h3>个性化欢迎语</h3>"
               "<p>在 URL 后加 <code>#欢迎语</code>，页面会显示你的欢迎语。</p>"
               "<p>例如：<code>/welcome#你好世界</code></p>"
               "<div id='welcome-msg' class='msg'>（等待 URL hash）</div>"
               "<div id='flag4-box' class='result' style='display:none'></div>"
               "</div>"
               "<script>"
               "(function(){"
               "var hash=location.hash.slice(1);"
               "if(hash){"
               "var msg=decodeURIComponent(hash);"
               "document.getElementById('welcome-msg').innerHTML=msg;"
               "}"
               "setTimeout(function(){"
               "var injected=document.querySelectorAll('#welcome-msg img,#welcome-msg svg,#welcome-msg iframe').length>0"
               "||document.querySelector('#welcome-msg [onerror]')"
               "||document.querySelector('#welcome-msg [onload]');"
               "if(injected){"
               "fetch('/dom-flag-callback').then(function(r){return r.text();}).then(function(t){"
               "document.getElementById('flag4-box').style.display='block';"
               "document.getElementById('flag4-box').innerHTML=t;"
               "});"
               "}"
               "},300);"
               "})();"
               "</script>")
    return render(content)


@app.route("/dom-flag-callback")
def dom_flag_callback():
    set_flag("flag4")
    return FLAGS["flag4"] + " [+] 检测到 DOM 注入，FLAG4 已记录"


@app.route("/about")
def about():
    note = request.args.get("note", "")
    # 安全：正确转义（HTML 实体编码）
    safe = (note.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#x27;"))
    result_html = ("<div class='result'>你的留言: " + safe + "</div>") if note else ""
    content = ("<div class='card'><h3>关于 Verse</h3>"
               "<p>Verse 是一个安全的小社区。本页正确转义了所有输出。</p>"
               "<form method='get' action='/about'>"
               "<input type='text' name='note' placeholder='试试输入 &lt;script&gt;'> "
               "<input type='submit' value='提交'>"
               "</form>" + result_html +
               "<p style='color:#7fffa0'>这里无论你输入什么，都不会执行。</p>"
               "</div>")
    return render(content)


@app.route("/reset")
def reset():
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag1=NULL,flag2=NULL,flag3=NULL,flag4=NULL WHERE id=1")
    db.execute("DELETE FROM messages")
    db.execute("UPDATE profiles SET bio='这个人很懒，什么都没留' WHERE id=1")
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
