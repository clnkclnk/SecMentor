# -*- coding: utf-8 -*-
"""
BankVault 银行 —— CSRF 靶场（受害者站点）
端口: 5029
主题: 银行网站，有转账/改密码/改邮箱/发帖/改手机号功能。
      攻击者站点在 5030 端口（csrf-evil.py），模拟跨站攻击。

FLAG:
  FLAG1 GET 转账     -> /transfer 无防护，img 标签可触发
  FLAG2 POST 改密码  -> /change-password 无防护，表单自动提交可触发
  FLAG3 POST 改邮箱  -> /change-email Referer 检查，但空 Referer 放行（no-referrer 绕过）
  FLAG4 POST 发帖    -> /post token 只检查"存在"不验证值，任意假 token 都过
  安全对照           -> /settings 改手机号，真正验证 token 值，打不动
"""
import os
import re
import sqlite3
import secrets
from flask import Flask, request, session, redirect, render_template_string, make_response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "bankvault.db")
PORT = 5029

app = Flask(__name__)
app.secret_key = "bankvault-csrf-lab-secret-key"
# 跨站 POST 也要带 cookie（本地 localhost 同站，SameSite 不拦；此处显式允许）
app.config["SESSION_COOKIE_SAMESITE"] = None
app.config["SESSION_COOKIE_SECURE"] = False

FLAGS = {
    "flag1": "FLAG1{csrf_get_transfer_2026}",
    "flag2": "FLAG2{csrf_post_password_2026}",
    "flag3": "FLAG3{csrf_referer_bypass_2026}",
    "flag4": "FLAG4{csrf_token_fake_2026}",
}

BANK_HOST = "127.0.0.1:5029"   # 本站标识（Referer 检查用）


def init_db():
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, flag1 TEXT, flag2 TEXT, flag3 TEXT, flag4 TEXT)")
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (1)")
    db.execute("CREATE TABLE IF NOT EXISTS transfers (id INTEGER PRIMARY KEY, to_acc TEXT, amount REAL, ts TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, content TEXT)")
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


STYLE = ("body{font-family:system-ui,Arial,sans-serif;max-width:860px;margin:30px auto;padding:0 16px;"
         "background:#0f1320;color:#e6e6e6}"
         "h1{color:#5ad;margin:0 0 8px}"
         "nav{margin:12px 0;padding:10px;background:#1b2233;border-radius:8px}"
         "nav a{color:#5ad;margin-right:14px;text-decoration:none}"
         ".card{background:#1b2233;border:1px solid #2d3650;border-radius:10px;padding:14px;margin:14px 0}"
         "input[type=text],input[type=password],input[type=number],textarea{padding:8px;border-radius:6px;"
         "border:1px solid #3a4560;background:#0f1320;color:#e6e6e6}"
         "input[type=submit]{padding:8px 16px;border:0;border-radius:6px;background:#5ad;color:#06121f;"
         "font-weight:bold;cursor:pointer}"
         ".flags{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}"
         ".flag{width:48%;box-sizing:border-box;padding:8px;border-radius:8px;font-size:13px}"
         ".on{background:#16351f;color:#7fffa0;border:1px solid #2f7a45}"
         ".off{background:#241b1b;color:#7a5555;border:1px solid #5a3030}"
         ".msg{background:#0a0d16;border:1px solid #2d3650;border-radius:6px;padding:10px;margin:8px 0}"
         ".ok{color:#7fffa0}.err{color:#F09595}.hint{color:#888;font-size:12px}")


def render(content_html="", notice=""):
    flags = get_flags()
    fc = lambda n: "on" if flags[n] else "off"
    fk = lambda n: "✅" if flags[n] else "🔒"
    nav = ("<nav><a href='/'>首页</a> <a href='/transfer'>转账</a> <a href='/change-password'>改密码</a> "
           "<a href='/change-email'>改邮箱</a> <a href='/post'>发帖</a> <a href='/settings'>设置</a> "
           "<a href='/attacker-hint'>攻击者站点</a> <a href='/reset'>重置</a></nav>")
    login_bar = ("<p class='hint'>未登录</p>") if not session.get("logged_in") else (
        "<p class='hint'>已登录：admin（会话 cookie 已发放）</p>")
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>BankVault 银行</title><style>" + STYLE + "</style></head><body>"
            "<h1>BankVault 银行</h1>" + login_bar +
            "<div class='flags'>"
            "<div class='flag " + fc('flag1') + "'>FLAG1 GET转账 " + fk('flag1') + "</div>"
            "<div class='flag " + fc('flag2') + "'>FLAG2 POST改密码 " + fk('flag2') + "</div>"
            "<div class='flag " + fc('flag3') + "'>FLAG3 绕Referer " + fk('flag3') + "</div>"
            "<div class='flag " + fc('flag4') + "'>FLAG4 假token发帖 " + fk('flag4') + "</div>"
            "</div>" + nav +
            (("<div class='msg ok'>" + notice + "</div>") if notice else "") +
            content_html + "</body></html>")


def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get("logged_in"):
            return render("<div class='card'><h3>请先登录</h3><form method='post' action='/login'>"
                          "<input type='text' name='username' placeholder='用户名' value='admin'> "
                          "<input type='password' name='password' placeholder='密码'> "
                          "<input type='submit' value='登录'></form>"
                          "<p class='hint'>测试账号 admin / admin123</p></div>")
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap


@app.route("/")
def index():
    if not session.get("logged_in"):
        return render("<div class='card'><h3>请先登录</h3>"
                      "<form method='post' action='/login'>"
                      "<input type='text' name='username' value='admin'> "
                      "<input type='password' name='password' placeholder='密码'> "
                      "<input type='submit' value='登录'></form>"
                      "<p class='hint'>测试账号 admin / admin123</p></div>")
    return render("<div class='card'><h3>欢迎回来，admin</h3>"
                  "<p>使用上方导航试试各个功能。任务：</p>"
                  "<ol>"
                  "<li>先正常玩一遍各功能，理解它们怎么工作</li>"
                  "<li>打开 <b>攻击者站点</b>（端口 5030），访问里面的页面</li>"
                  "<li>观察银行的账号被借了身份、操作了什么</li>"
                  "<li>回来看 FLAG 是否点亮</li>"
                  "</ol>"
                  "<p class='hint'>攻击者站点入口：http://127.0.0.1:5030/</p></div>")


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if u == "admin" and p == "admin123":
        session["logged_in"] = True
        session["csrf_token"] = secrets.token_hex(16)   # 真正的 token
        return redirect("/")
    return render("", notice="登录失败")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- FLAG1：GET 转账，无任何防护 ----------
@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    notice = ""
    if request.method == "POST":
        to = request.form.get("to", "")
        amount = request.form.get("amount", "")
        notice = f"转账成功：向 {to} 转 {amount} 元"
        if to == "attacker" and amount.isdigit() and int(amount) >= 100:
            set_flag("flag1")
            notice += " [FLAG1]"
    elif request.args.get("to"):
        # GET 转账 —— 危险设计！img 标签、链接都能触发
        to = request.args.get("to", "")
        amount = request.args.get("amount", "")
        notice = f"转账成功（GET）：向 {to} 转 {amount} 元"
        if to == "attacker" and amount.isdigit() and int(amount) >= 100:
            set_flag("flag1")
            notice += " [FLAG1]"
    content = ("<div class='card'><h3>转账</h3>"
               "<form method='post' action='/transfer'>"
               "<input type='text' name='to' placeholder='收款人' value='friend'> "
               "<input type='number' name='amount' placeholder='金额' value='100'> "
               "<input type='submit' value='转账'>"
               "</form>"
               "<p class='hint'>注意：这个功能同时支持 GET 方式调用（?to=xxx&amp;amount=xxx）</p>"
               "</div>")
    return render(content, notice)


# ---------- FLAG2：POST 改密码，无防护 ----------
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    notice = ""
    if request.method == "POST":
        new_pwd = request.form.get("new_password", "")
        notice = f"密码已修改为：{new_pwd}"
        if new_pwd == "hacked123":
            set_flag("flag2")
            notice += " [FLAG2]"
    content = ("<div class='card'><h3>修改密码</h3>"
               "<form method='post' action='/change-password'>"
               "<input type='password' name='new_password' placeholder='新密码'> "
               "<input type='submit' value='确认修改'>"
               "</form></div>")
    return render(content, notice)


# ---------- FLAG3：POST 改邮箱，Referer 检查但空 Referer 放行 ----------
@app.route("/change-email", methods=["GET", "POST"])
@login_required
def change_email():
    notice = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        referer = request.headers.get("Referer", "")
        # 检查 Referer：非空时必须包含本站，为空则放行（缺陷！）
        if referer and BANK_HOST not in referer:
            notice = f"拒绝：来源不合法（Referer: {referer[:50]}）"
            return render("", notice)
        notice = f"邮箱已修改为：{email}"
        if email == "attacker@evil.com":
            set_flag("flag3")
            notice += " [FLAG3]"
    content = ("<div class='card'><h3>修改邮箱</h3>"
               "<form method='post' action='/change-email'>"
               "<input type='text' name='email' placeholder='新邮箱'> "
               "<input type='submit' value='确认修改'>"
               "</form>"
               "<p class='hint'>本功能检查了 Referer 来源，只允许本站发起的请求</p>"
               "</div>")
    return render(content, notice)


# ---------- FLAG4：POST 发帖，token 只检查"存在"不验证值 ----------
@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    notice = ""
    if request.method == "POST":
        content = request.form.get("content", "")
        token = request.form.get("csrf_token", "")
        # 缺陷：只检查 token 字段"存在且非空"，不验证值是否匹配会话
        if not token:
            notice = "CSRF 校验失败：缺少 token"
            return render("", notice)
        notice = f"发帖成功：{content[:30]}"
        if "csrfdemo" in content:
            set_flag("flag4")
            notice += " [FLAG4]"
    real_token = session.get("csrf_token", "")
    content = ("<div class='card'><h3>论坛发帖</h3>"
               "<form method='post' action='/post'>"
               "<input type='hidden' name='csrf_token' value='" + real_token + "'>"
               "<input type='text' name='content' placeholder='内容' style='width:60%'> "
               "<input type='submit' value='发布'>"
               "</form>"
               "<p class='hint'>本功能有 CSRF token（藏在表单里）</p>"
               "</div>")
    return render(content, notice)


# ---------- 安全对照：改手机号，真 token 校验 ----------
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    notice = ""
    if request.method == "POST":
        phone = request.form.get("phone", "")
        token = request.form.get("csrf_token", "")
        if token != session.get("csrf_token", ""):
            notice = "拒绝：CSRF token 校验失败（token 不匹配）"
            return render("", notice)
        notice = f"手机号已修改为：{phone}（安全操作，token 真校验）"
    real_token = session.get("csrf_token", "")
    content = ("<div class='card'><h3>修改手机号（安全演示）</h3>"
               "<form method='post' action='/settings'>"
               "<input type='hidden' name='csrf_token' value='" + real_token + "'>"
               "<input type='text' name='phone' placeholder='新手机号'> "
               "<input type='submit' value='确认修改'>"
               "</form>"
               "<p class='hint'>这个功能真正验证了 token 值，攻击者页面打不动——对照用</p>"
               "</div>")
    return render(content, notice)


# ---------- 提示页：告诉用户攻击者站点地址 ----------
@app.route("/attacker-hint")
def attacker_hint():
    content = ("<div class='card'><h3>攻击者站点</h3>"
               "<p>攻击者控制了一个恶意网站，地址：</p>"
               "<p><code>http://127.0.0.1:5030/</code></p>"
               "<p>保持本站登录状态，去访问攻击者站点，观察会发生什么。</p>"
               "<p class='hint'>提示：浏览器会自动把本站的 cookie 带上，服务器以为是你本人操作</p></div>")
    return render(content)


@app.route("/reset")
def reset():
    session.clear()
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag1=NULL,flag2=NULL,flag3=NULL,flag4=NULL WHERE id=1")
    db.execute("DELETE FROM transfers")
    db.execute("DELETE FROM posts")
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
