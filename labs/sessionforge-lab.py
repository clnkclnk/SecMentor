# -*- coding: utf-8 -*-
"""
SessionForge —— 反序列化进阶靶场
端口: 5034
主题: 会话恢复系统。用户提交 base64 的 pickle 数据，服务器还原"用户对象"。

入口:
  /restore           POST data=base64(pickle)  无保护直接 loads     → FLAG1
  /restore-cookie    Cookie session_data       Cookie 里的 pickle   → FLAG2
  /restore-limited   POST data=base64(pickle)  find_class 黑名单     → FLAG3（绕过用 nt.system）
  /restore-secure    POST data+sig             HMAC 签名校验         → 安全对照（打不动）

正常还原对象: dict 用户数据 {"name":..., "vip":...}
恶意 payload: __reduce__ 返回 (subprocess.check_output, ("whoami",)) → 还原 = 命令输出
FLAG 触发: 还原对象非 dict（代码被执行了）→ set flag；limited 检查标记文件 rce_marker.txt
"""
import base64
import hashlib
import hmac
import io
import os
import pickle
import sqlite3
from flask import Flask, request, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "sessionforge.db")
PORT = 5034

app = Flask(__name__)

SECRET = "sessionforge-secret-key-2026"          # HMAC 签名密钥（只存服务器）
MARKER = os.path.join(BASE_DIR, "rce_marker.txt")  # FLAG3 命令执行标记文件

FLAGS = {
    "flag1": "FLAG1{deser_pickle_rce_2026}",
    "flag2": "FLAG2{deser_cookie_rce_2026}",
    "flag3": "FLAG3{deser_blacklist_bypass_2026}",
}

# find_class 黑名单（FLAG3：漏了 nt 模块——os 在 Windows 的底层实现）
BLACKLIST_MODULES = {"os", "subprocess", "sys", "builtins", "posix", "eval", "exec"}


def init_db():
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, flag1 TEXT, flag2 TEXT, flag3 TEXT)")
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
    db.commit()
    db.close()


def get_flags():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT flag1,flag2,flag3 FROM users WHERE id=1").fetchone()
    db.close()
    return row


def set_flag(name):
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET " + name + "=? WHERE id=1", (FLAGS[name],))
    db.commit()
    db.close()


# ---------------- 正常用户数据（服务端"本人"会生成什么） ----------------
def make_normal_user():
    return {"name": "alice", "vip": False, "balance": 100}


# ---------------- 受限 Unpickler（黑名单） ----------------
class LimitedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module in BLACKLIST_MODULES:
            raise pickle.UnpicklingError("被拦截: 模块 %s 在黑名单" % module)
        return super().find_class(module, name)


# ---------------- 签名 ----------------
def sign(data_b64):
    sig = hmac.new(SECRET.encode(), data_b64.encode(), hashlib.sha256).hexdigest()
    return data_b64 + "." + sig


def verify(data_b64, sig):
    expect = hmac.new(SECRET.encode(), data_b64.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expect, sig)


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
         "input[type=text]{width:70%;padding:8px;border-radius:6px;border:1px solid #3a4560;background:#0f1320;color:#e6e6e6;font-family:monospace}"
         "input[type=submit]{padding:8px 16px;border:0;border-radius:6px;background:#5ad;color:#06121f;font-weight:bold;cursor:pointer}"
         ".msg{background:#0a0d16;border:1px solid #2d3650;border-radius:6px;padding:10px;margin:8px 0;font-family:monospace;font-size:12px;white-space:pre-wrap}"
         ".hint{color:#888;font-size:12px}")


def render(content_html=""):
    flags = get_flags()
    fc = lambda n: "on" if flags[n] else "off"
    fk = lambda n: "✅" if flags[n] else "🔒"
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>SessionForge 会话恢复</title><style>" + STYLE + "</style></head><body>"
            "<h1>SessionForge 会话恢复系统</h1>"
            "<p style='color:#888;margin:0 0 8px'>提交序列化数据，恢复你的用户会话</p>"
            "<div class='flags'>"
            "<div class='flag " + fc('flag1') + "'>FLAG1 无保护 " + fk('flag1') + "</div>"
            "<div class='flag " + fc('flag2') + "'>FLAG2 Cookie入口 " + fk('flag2') + "</div>"
            "<div class='flag " + fc('flag3') + "'>FLAG3 黑名单绕过 " + fk('flag3') + "</div>"
            "</div>"
            "<nav><a href='/'>首页</a> <a href='/restore'>恢复(无保护)</a> "
            "<a href='/restore-cookie'>Cookie入口</a> <a href='/restore-limited'>限类版</a> "
            "<a href='/restore-secure'>签名版</a> <a href='/reset'>重置</a></nav>"
            + content_html + "</body></html>")


def data_form(action, note):
    return ("<div class='card'><h3>提交序列化数据（base64）</h3>"
            "<form method='post' action='" + action + "'>"
            "<input type='text' name='data' placeholder='base64 的 pickle 数据' style='width:96%'> "
            "<input type='submit' value='恢复'>"
            "</form><p class='hint'>" + note + "</p></div>")


def restore_and_show(data_b64, flag_name, is_limited=False):
    """公共还原逻辑：loads + 检测 + 显示"""
    try:
        raw = base64.b64decode(data_b64)
    except Exception as e:
        return render(data_form(request.path, "") + "<div class='msg'>base64 解码失败: " + str(e) + "</div>")
    try:
        if is_limited:
            result = LimitedUnpickler(io.BytesIO(raw)).load()
        else:
            result = pickle.loads(raw)
    except Exception as e:
        return render(data_form(request.path, "") + "<div class='msg'>反序列化错误: " + str(e) + "</div>")
    # 检测：还原对象不是 dict（正常用户数据）→ 代码被执行了
    if not isinstance(result, dict):
        set_flag(flag_name)
        return render(data_form(request.path, "") +
                      "<div class='msg'>⚠️ 还原出非预期对象（正常应是 dict 用户数据）：\n" + repr(result) + "</div>")
    return render(data_form(request.path, "") +
                  "<div class='msg'>还原成功，用户数据：\n" + repr(result) + "</div>")


@app.route("/")
def index():
    content = ("<div class='card'><h3>欢迎</h3>"
               "<p>这是一个会话恢复系统：提交 base64 的 pickle 数据，服务器还原你的用户对象。</p>"
               "<p>正常数据长这样（服务端生成，base64 编码）：</p>"
               "<p style='font-family:monospace;background:#0a0d16;padding:8px;border-radius:6px'>"
               + base64.b64encode(pickle.dumps(make_normal_user())).decode() + "</p>"
               "<p class='hint'>四个入口：无保护 / Cookie 入口 / 限类版 / 签名版（对照）。每个页面有提示</p></div>")
    return render(content)


@app.route("/restore", methods=["GET", "POST"])
def restore():
    note = "无保护：直接 pickle.loads 用户数据。想想还原瞬间会发生什么？"
    if request.method == "POST":
        return restore_and_show(request.form.get("data", ""), "flag1")
    return render(data_form("/restore", note))


@app.route("/restore-cookie", methods=["GET", "POST"])
def restore_cookie():
    note = "入口是 Cookie（session_data）。浏览器会自动带 Cookie，用 Python requests 或 F12 设置后再访问。"
    if request.method == "POST":
        return restore_and_show(request.form.get("data", ""), "flag2")
    data = request.cookies.get("session_data", "")
    if data:
        return restore_and_show(data, "flag2")
    return render(data_form("/restore-cookie", note) +
                  "<div class='card'><h3>Cookie 入口测试</h3>"
                  "<p>给浏览器设置 Cookie：<code>session_data=&lt;你的payload&gt;</code> 后访问本页。</p>"
                  "<p>Python: <code>requests.get(url, cookies={'session_data': 'payload'})</code></p></div>")


@app.route("/restore-limited", methods=["GET", "POST"])
def restore_limited():
    note = "限类版：find_class 黑名单拦了 os / subprocess / sys / builtins / posix。"
    if request.method == "POST":
        # FLAG3 检测：命令执行的标记文件是否存在（payload 用黑名单外的模块写文件）
        if os.path.exists(MARKER):
            set_flag("flag3")
        result_html = restore_and_show(request.form.get("data", ""), "flag3", is_limited=True)
        if os.path.exists(MARKER):
            try:
                os.remove(MARKER)
            except Exception:
                pass
        return result_html
    return render(data_form("/restore-limited", note) +
                  "<div class='card'><h3>提示</h3>"
                  "<p>os 被拦了，但 <code>os.system</code> 在 Windows 上的底层模块是什么？"
                  "（黑名单漏了它）</p>"
                  "<p>试试让它执行 <code>echo PWNED &gt; rce_marker.txt</code> 这类命令。</p></div>")


@app.route("/restore-secure", methods=["GET", "POST"])
def restore_secure():
    note = "签名版：HMAC-SHA256 签名校验。没有正确签名的数据直接拒绝。"
    if request.method == "POST":
        data = request.form.get("data", "")
        sig = request.form.get("sig", "")
        if not verify(data, sig):
            return render(data_form("/restore-secure", note) +
                          "<div class='msg'>拒绝：签名校验失败（伪造数据无法通过）</div>")
        return restore_and_show(data, "flag1")   # 有签名才走到 loads（此处不应被触发）
    return render(data_form("/restore-secure", note) +
                  "<div class='card'><h3>签名版说明</h3>"
                  "<p>服务端：<code>data + 点 + HMAC(secret, data)</code>，验签通过才反序列化。</p>"
                  "<p>你没有 secret，伪造的数据签名对不上 → 拒绝。</p></div>")


@app.route("/reset")
def reset():
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag1=NULL,flag2=NULL,flag3=NULL WHERE id=1")
    db.commit()
    db.close()
    if os.path.exists(MARKER):
        os.remove(MARKER)
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
