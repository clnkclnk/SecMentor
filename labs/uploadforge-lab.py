# -*- coding: utf-8 -*-
"""
UploadForge —— 文件上传进阶靶场
端口: 5031
主题: 图片上传站点，5 个上传点检查强度递增 + 1 个安全对照。

Level 检查强度（对应第二块讲的 5 种检查）:
  L1 无后端检查          -> 直接上传 shell.py
  L2 扩展名黑名单        -> 大小写 shell.PY 或冷门后缀 shell.phtml
  L3 扩展名白名单+Apache  -> 双扩展名 shell.py.jpg
  L4 Content-Type 检查   -> 改 Content-Type: image/jpeg
  L5 内容检查(magic num) -> 图片马 GIF89a+代码，配合 Nginx 解析漏洞访问执行
  安全对照               -> 内容检查+随机名+不可执行目录，打不动

执行约定（模拟服务器执行上传文件）:
  文件内容里 <\?py ... \?> 标签内的 Python 代码会被"服务器执行"。
  扩展名解析模拟 Web 中间件：Apache 从右往左认扩展名；Nginx 路径以 .py 结尾则前面文件当可执行。
"""
import io
import os
import re
import sqlite3
import contextlib
import uuid
from flask import Flask, request, redirect, send_file, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "uploadforge.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploadforge_uploads")
PORT = 5031

app = Flask(__name__)

FLAGS = {
    "flag1": "FLAG1{upload_no_check_2026}",
    "flag2": "FLAG2{upload_blacklist_bypass_2026}",
    "flag3": "FLAG3{upload_double_ext_2026}",
    "flag4": "FLAG4{upload_contenttype_bypass_2026}",
    "flag5": "FLAG5{upload_imagema_nginx_2026}",
}

EXEC_EXT = ["py", "php", "jsp", "phtml", "php5", "pht", "asp", "aspx"]
BLACKLIST = [".php", ".py", ".jsp", ".asp"]           # L2 黑名单（缺陷：没 lower，漏 .phtml）
WHITELIST = [".jpg", ".png", ".gif"]                  # L3/L5 白名单
MAGIC = {"gif": b"GIF89a", "jpeg": b"\xff\xd8\xff", "png": b"\x89\x50\x4e\x47"}


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, flag1 TEXT, flag2 TEXT, flag3 TEXT, flag4 TEXT, flag5 TEXT)")
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
    db.commit()
    db.close()


def get_flags():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT flag1,flag2,flag3,flag4,flag5 FROM users WHERE id=1").fetchone()
    db.close()
    return row


def set_flag(name):
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET " + name + "=? WHERE id=1", (FLAGS[name],))
    db.commit()
    db.close()


def would_execute(filename):
    """模拟 Web 中间件解析：判断文件会不会被执行"""
    name = filename.lower()
    # Nginx 风格：路径最后一段 .py 结尾 → 前面文件当可执行
    if name.endswith((".py", ".php")):
        return True
    # Apache 风格：从右往左认扩展名
    parts = name.split(".")
    if len(parts) >= 2:
        for ext in reversed(parts[1:]):
            if ext in EXEC_EXT:
                return True
            if ext in ("jpg", "png", "gif", "jpeg", "txt", "bmp"):
                continue
            break
    return False


def run_webshell(filepath):
    """模拟服务器执行上传文件：提取 <\?py ... \?> 标签内代码并执行"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return "[读取失败] " + str(e)
    m = re.search(r"<\?py(.*?)\?>", content, re.S)
    if not m:
        return "[非WebShell] 文件内容里没有 <?py ?> 标签"
    code = m.group(1)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {"__builtins__": __builtins__})
        return buf.getvalue()
    except Exception as e:
        return "[执行错误] " + str(e)


# ---------------- 页面 ----------------
STYLE = ("body{font-family:system-ui,Arial,sans-serif;max-width:860px;margin:30px auto;padding:0 16px;"
         "background:#0f1320;color:#e6e6e6}"
         "h1{color:#5ad;margin:0 0 8px}"
         "nav{margin:12px 0;padding:10px;background:#1b2233;border-radius:8px}"
         "nav a{color:#5ad;margin-right:12px;text-decoration:none}"
         ".card{background:#1b2233;border:1px solid #2d3650;border-radius:10px;padding:14px;margin:14px 0}"
         ".flags{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}"
         ".flag{width:31%;box-sizing:border-box;padding:8px;border-radius:8px;font-size:12px}"
         ".on{background:#16351f;color:#7fffa0;border:1px solid #2f7a45}"
         ".off{background:#241b1b;color:#7a5555;border:1px solid #5a3030}"
         ".msg{background:#0a0d16;border:1px solid #2d3650;border-radius:6px;padding:10px;margin:8px 0;font-family:monospace;font-size:13px;white-space:pre-wrap}"
         ".ok{color:#7fffa0}.err{color:#F09595}.hint{color:#888;font-size:12px}")


def render(content_html=""):
    flags = get_flags()
    fc = lambda n: "on" if flags[n] else "off"
    fk = lambda n: "✅" if flags[n] else "🔒"
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>UploadForge 图片站</title><style>" + STYLE + "</style></head><body>"
            "<h1>UploadForge 图片站</h1>"
            "<p style='color:#888;margin:0 0 8px'>上传你的图片素材 · 5 个上传点 + 1 个安全对照</p>"
            "<div class='flags'>"
            "<div class='flag " + fc('flag1') + "'>L1 无检查 " + fk('flag1') + "</div>"
            "<div class='flag " + fc('flag2') + "'>L2 黑名单 " + fk('flag2') + "</div>"
            "<div class='flag " + fc('flag3') + "'>L3 白名单+解析 " + fk('flag3') + "</div>"
            "<div class='flag " + fc('flag4') + "'>L4 Content-Type " + fk('flag4') + "</div>"
            "<div class='flag " + fc('flag5') + "'>L5 内容检查+图片马 " + fk('flag5') + "</div>"
            "</div>"
            "<nav>"
            "<a href='/'>首页</a> "
            "<a href='/level/1'>L1</a> <a href='/level/2'>L2</a> <a href='/level/3'>L3</a> "
            "<a href='/level/4'>L4</a> <a href='/level/5'>L5</a> "
            "<a href='/secure'>安全对照</a> <a href='/reset'>重置</a>"
            "</nav>"
            + content_html + "</body></html>")


def upload_form(action, note):
    return ("<div class='card'><h3>上传图片</h3>"
            "<form method='post' action='" + action + "' enctype='multipart/form-data'>"
            "<input type='file' name='file' accept='.jpg,.png,.gif'> "
            "<input type='submit' value='上传'>"
            "</form><p class='hint'>" + note + "</p></div>")


# ---------------- 路由 ----------------
@app.route("/")
def index():
    content = ("<div class='card'><h3>欢迎来到 UploadForge</h3>"
               "<p>这是一个图片上传站点，有 5 个上传点，检查强度递增。任务：</p>"
               "<ol>"
               "<li>每个上传点想方设法传一个 <b>可执行文件</b>（.py 后缀或能被解析执行）</li>"
               "<li>传成功的文件，访问 <code>/uploads/&lt;文件名&gt;</code> 会看到服务器执行结果</li>"
               "<li>执行约定：文件内容里 <code>&lt;?py ... ?&gt;</code> 标签内的 Python 代码会被执行</li>"
               "<li>每个 Level 的检查方式和绕过思路写在对应页面</li>"
               "</ol>"
               "<p class='hint'>先看 L1 页面的说明，按顺序打</p></div>")
    return render(content)


@app.route("/level/<int:n>")
def level_page(n):
    hints = {
        1: ("L1：后端没有任何检查。前端虽然限制了 .jpg，但那是摆设。直接上传可执行文件。", "无检查"),
        2: ("L2：后端扩展名黑名单拦了 .php/.py/.jsp/.asp。想想黑名单的常见缺陷（大小写？冷门后缀？）。", "黑名单"),
        3: ("L3：白名单只允许 .jpg/.png/.gif。但服务器解析文件时是 Apache 风格（从右往左认扩展名）。", "白名单+Apache解析"),
        4: ("L4：检查请求头的 Content-Type 必须是 image/*。这个头是谁发的？能不能改？", "Content-Type 检查"),
        5: ("L5：检查文件真实内容（图片 magic number）+ 白名单。试试图片马，然后想：怎么让它执行？（Nginx 解析漏洞：/uploads/xxx.gif/x.py）", "内容检查+图片马"),
    }
    note, title = hints.get(n, ("", ""))
    content = ("<div class='card'><h3>Level " + str(n) + " · " + title + "</h3>"
               "<p>" + note + "</p></div>"
               + upload_form("/level/%d/upload" % n,
                             "上传成功后访问 /uploads/文件名 执行验证"))
    return render(content)


def do_upload(level, checks):
    """通用上传处理。checks 是检查函数列表，返回 (ok, msg)"""
    if "file" not in request.files:
        return render(upload_form("/level/%d/upload" % level, "请选择文件"))
    f = request.files["file"]
    if not f or not f.filename:
        return render(upload_form("/level/%d/upload" % level, "文件名为空"))
    filename = f.filename
    for check in checks:
        ok, msg = check(filename, f)
        if not ok:
            return render(upload_form("/level/%d/upload" % level, msg))
    # 存盘（保留用户文件名，模拟真实漏洞场景）
    level_dir = os.path.join(UPLOAD_DIR, "level%d" % level)
    os.makedirs(level_dir, exist_ok=True)
    filepath = os.path.join(level_dir, os.path.basename(filename))
    f.save(filepath)
    # 判断文件是否"会被执行" → 触发对应 FLAG
    if would_execute(filename):
        set_flag("flag%d" % level)
        return render(upload_form("/level/%d/upload" % level, "") +
                      "<div class='msg ok'>上传成功！这个文件会被服务器执行 ✅ 访问 /uploads/level%d/%s 看结果</div>" % (level, filename))
    return render(upload_form("/level/%d/upload" % level, "") +
                  "<div class='msg'>上传成功，但这是普通文件（不会被执行），去 /uploads/level%d/%s 看看</div>" % (level, filename))


@app.route("/level/1/upload", methods=["POST"])
def upload_l1():
    # L1：无任何检查
    return do_upload(1, [])


@app.route("/level/2/upload", methods=["POST"])
def upload_l2():
    # L2：黑名单（缺陷：不转小写直接匹配 → shell.PY 大写绕过；也漏冷门后缀 .phtml）
    def check(filename, f):
        for b in BLACKLIST:
            if filename.endswith(b):
                return False, "被拦截：扩展名在黑名单里（" + b + "）"
        return True, ""
    return do_upload(2, [check])


@app.route("/level/3/upload", methods=["POST"])
def upload_l3():
    # L3：白名单（只看结尾扩展名）
    def check(filename, f):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in WHITELIST:
            return False, "被拦截：只允许 " + " ".join(WHITELIST)
        return True, ""
    return do_upload(3, [check])


@app.route("/level/4/upload", methods=["POST"])
def upload_l4():
    # L4：Content-Type 检查（检查文件部分的 Content-Type，用户可控）
    def check(filename, f):
        ct = f.content_type or ""
        if "image/" not in ct:
            return False, "被拦截：文件 Content-Type 必须是 image/*，当前是 " + ct
        return True, ""
    return do_upload(4, [check])


@app.route("/level/5/upload", methods=["POST"])
def upload_l5():
    # L5：magic number 内容检查 + 白名单
    def check(filename, f):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in WHITELIST:
            return False, "被拦截：只允许 " + " ".join(WHITELIST)
        head = f.read(6)
        f.seek(0)
        if not any(head.startswith(m) for m in MAGIC.values()):
            return False, "被拦截：文件内容不是合法图片（magic number 不匹配）"
        return True, ""
    return do_upload(5, [check])


@app.route("/secure", methods=["GET", "POST"])
def secure():
    note = ("安全对照：正确的防御 = 内容检查(magic number) + 随机文件名 + 不可执行目录。<br>"
            "你试试能不能绕——这个上传点应该打不动。")
    if request.method == "POST":
        if "file" not in request.files:
            return render("<div class='card'><h3>安全对照</h3><p>" + note + "</p></div>"
                          + upload_form("/secure", "请选择文件"))
        f = request.files["file"]
        filename = f.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in WHITELIST:
            return render("<div class='card'><h3>安全对照</h3><p>" + note + "</p></div>"
                          + upload_form("/secure", "被拦截：只允许图片扩展名"))
        head = f.read(6)
        f.seek(0)
        if not any(head.startswith(m) for m in MAGIC.values()):
            return render("<div class='card'><h3>安全对照</h3><p>" + note + "</p></div>"
                          + upload_form("/secure", "被拦截：内容不是合法图片"))
        # 随机文件名 + 存到不可执行目录
        new_name = uuid.uuid4().hex + ext
        os.makedirs(os.path.join(UPLOAD_DIR, "secure"), exist_ok=True)
        f.save(os.path.join(UPLOAD_DIR, "secure", new_name))
        return render("<div class='card'><h3>安全对照</h3><p>" + note + "</p></div>"
                      + upload_form("/secure", "") +
                      "<div class='msg'>上传成功但被随机改名（" + new_name + "），你无法预测文件名，也无法触发执行 ✅ 正确防御</div>")
    return render("<div class='card'><h3>安全对照</h3><p>" + note + "</p></div>"
                  + upload_form("/secure", ""))


@app.route("/uploads/<path:filename>")
def uploaded(filename):
    p = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(p):
        # 文件存在：直接访问。可执行扩展名 → 执行 webshell；否则当普通文件返回
        if would_execute(filename):
            return "<pre>" + run_webshell(p) + "</pre>"
        return send_file(p)
    # 文件不存在 → Nginx 解析漏洞模拟：/uploads/xxx.gif/x.py 把 xxx.gif 当代码执行
    parts = filename.split("/")
    if len(parts) >= 2 and parts[-1].endswith((".py", ".php")):
        real_path = "/".join(parts[:-1])
        real_p = os.path.join(UPLOAD_DIR, real_path)
        if os.path.exists(real_p):
            set_flag("flag5")
            return ("<div class='msg ok'>[Nginx 解析漏洞] " + real_path +
                    " 被当 Python/PHP 解析执行</div><pre>" + run_webshell(real_p) + "</pre>")
    return "文件不存在", 404


@app.route("/reset")
def reset():
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag1=NULL,flag2=NULL,flag3=NULL,flag4=NULL,flag5=NULL WHERE id=1")
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
