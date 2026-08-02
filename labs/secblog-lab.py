#!/usr/bin/env python3
# SecBlog CMS v1.0 — P10 综合靶场 (capstone)
# 纯标准库实现。模拟一个真实公司内部博客系统，内含多个漏洞，需自行发现与利用。
import http.server
import socketserver
import sqlite3
import os
import re
import sys
import json
import html
import urllib.parse
import urllib.request
import subprocess
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "secblog.db")
UPLOAD_DIR = os.path.join(BASE, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SESSIONS = {}  # sid -> username


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);
    CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, body TEXT, author TEXT);
    CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, post_id INTEGER, name TEXT, content TEXT, created TEXT);
    """)
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", ("admin", "admin123", "admin"))
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", ("editor", "editor2026", "editor"))
        c.execute("INSERT INTO posts (title,body,author) VALUES (?,?,?)",
                  ("欢迎来到 SecBlog", "这是公司内部技术博客。我们分享安全研究、产品动态与招聘信息。", "admin"))
        c.execute("INSERT INTO posts (title,body,author) VALUES (?,?,?)",
                  ("2026 安全公告", "本周修复了若干漏洞，建议所有员工尽快更新密码并启用双因素认证。", "admin"))
        c.execute("INSERT INTO posts (title,body,author) VALUES (?,?,?)",
                  ("内部运维手册节选", "数据库与缓存服务仅允许内网访问。Redis 运行在 6379，MySQL 在 3306。", "admin"))
    conn.commit()
    conn.close()


init_db()


class Handler(http.server.BaseHTTPRequestHandler):
    timeout = 10  # 单个连接最多 10 秒，防止卡死读操作永久占用线程
    def log_message(self, *a):
        pass  # 静默日志，避免干扰

    # ---------- 工具 ----------
    def _send(self, code, body, headers=None, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", "SecBlog/1.0 (dev)")
        self.send_header("X-Powered-By", "Python")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _user(self):
        ck = self.headers.get("Cookie", "")
        m = re.search(r"sid=([0-9a-f]+)", ck)
        if m and m.group(1) in SESSIONS:
            return SESSIONS[m.group(1)]
        return None

    def _need_login(self):
        u = self._user()
        if not u:
            self._send(302, "", {"Location": "/admin/login"})
            return None
        return u

    # ---------- GET ----------
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            return self.page_home()
        if path == "/robots.txt":
            return self.page_robots()
        if path == "/about":
            return self.page_about()
        if path.startswith("/article/"):
            return self.page_article(path.split("/")[-1])
        if path in ("/admin/login", "/login"):
            return self.page_login()
        if path == "/admin":
            return self.page_admin()
        if path == "/admin/profile":
            return self.page_profile()
        if path == "/admin/comments":
            return self.page_comments()
        if path == "/admin/ping":
            return self.page_ping_form()
        if path == "/admin/thumb":
            return self.page_thumb_form()
        if path == "/admin/users":
            return self.page_users()
        if path == "/upload":
            return self.page_upload_form()
        if path == "/internal/flag":
            return self.page_internal_flag()
        if path == "/xss-trigger":
            return self.page_xss_trigger()
        return self._send(404, "<h1>404 Not Found</h1><p>页面不存在</p>")

    # ---------- POST ----------
    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", "0"))
        raw_bytes = self.rfile.read(length)
        raw = raw_bytes.decode("utf-8", "ignore")  # 给表单解析用(str)
        form = urllib.parse.parse_qs(raw)

        def g(k):
            return form.get(k, [""])[0]

        if path == "/admin/login":
            return self.post_login(g("username"), g("password"))
        if path == "/api/comment":
            return self.post_comment(g("post_id"), g("name"), g("content"))
        if path == "/admin/ping":
            return self.post_ping(g("host"))
        if path == "/admin/thumb":
            return self.post_thumb(g("url"))
        if path == "/upload":
            return self.post_upload(raw_bytes)  # 上传需要原始字节
        return self._send(404, "<h1>404</h1>")

    # ---------- 页面 ----------
    def page_home(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT id,title,author FROM posts ORDER BY id")
        posts = c.fetchall()
        conn.close()
        body = """<!-- SecBlog v1.0 | backend: sqlite | maintainer: admin -->
<!doctype html><html><head><meta charset=utf-8><title>SecBlog</title></head><body>
<h1>SecBlog — 公司内部技术博客</h1>
<p>致力于分享安全研究、产品动态与内部资讯。</p>
<ul>"""
        for pid, title, author in posts:
            body += f"<li><a href='/article/{pid}'>{html.escape(title)}</a> <small>by {html.escape(author)}</small></li>"
        body += "</ul><hr><p><a href='/robots.txt'>robots.txt</a> · <a href='/about'>关于</a> · <a href='/admin/login'>后台登录</a></p></body></html>"
        self._send(200, body)

    def page_robots(self):
        self._send(200,
                   "User-agent: *\nDisallow: /admin/\nDisallow: /api/internal/\n"
                   "# 运维备注: 内部调试接口 /internal/flag 仅服务器本地进程可访问\n",
                   ctype="text/plain; charset=utf-8")

    def page_about(self):
        self._send(200, "<h1>关于 SecBlog</h1><p>本系统由内部运维团队维护，运行于内网环境。</p><p><a href='/'>返回首页</a></p>")

    def page_article(self, pid):
        if not pid.isdigit():
            return self._send(404, "<h1>404</h1>")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT title,body FROM posts WHERE id=?", (int(pid),))
        post = c.fetchone()
        c.execute("SELECT name,content,created FROM comments WHERE post_id=? ORDER BY id DESC", (int(pid),))
        comments = c.fetchall()
        conn.close()
        if not post:
            return self._send(404, "<h1>404</h1>")
        body = f"<h1>{html.escape(post[0])}</h1><p>{html.escape(post[1])}</p><hr><h3>评论区</h3>"
        for name, content, created in comments:
            # 漏洞: 评论内容未过滤，直接渲染 => 存储型 XSS
            body += f"<div style='border:1px solid #ccc;padding:8px;margin:6px'><b>{html.escape(name)}</b> 说：{content}<br><small>{html.escape(created)}</small></div>"
        body += f"""<h3>发表评论</h3><form method=post action=/api/comment>
        文章ID:<input name=post_id value='{pid}'><br>
        昵称:<input name=name><br>
        评论:<textarea name=content rows=4 cols=40></textarea><br>
        <button>提交评论</button></form><p><a href='/'>返回</a></p>"""
        self._send(200, body)

    def page_login(self):
        self._send(200, """<h1>后台登录</h1>
<form method=post action=/admin/login>
用户:<input name=username><br>
密码:<input name=password type=password><br>
<button>登录</button></form>
<p style='color:#888'>演示站点 · 管理员账号: <b>admin</b> · 忘记密码? 试试常见弱口令字典</p>
<p><a href='/'>返回首页</a></p>""")

    def page_admin(self):
        u = self._need_login()
        if not u:
            return
        self._send(200, f"""<h1>后台控制台 — 欢迎 {html.escape(u)}</h1>
<ul>
<li><a href='/admin/profile'>个人资料</a></li>
<li><a href='/admin/users'>用户列表</a></li>
<li><a href='/admin/comments'>评论管理</a></li>
<li><a href='/admin/ping'>网络诊断(测试主机连通性)</a></li>
<li><a href='/admin/thumb'>缩略图生成(输入任意URL)</a></li>
<li><a href='/upload'>上传头像</a></li>
</ul>
<p><a href='/'>返回首页</a></p>""")

    def page_profile(self):
        u = self._need_login()
        if not u:
            return
        self._send(200, f"""<h1>{html.escape(u)} 的个人资料</h1>
<p>角色: admin</p>
<p>内部标记: FLAG{{secblog_weakpwd_admin_2026}}</p>
<p><a href='/admin'>返回控制台</a></p>""")

    def page_users(self):
        u = self._need_login()
        if not u:
            return
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT username,role FROM users")
        rows = c.fetchall()
        conn.close()
        body = "<h1>用户列表</h1><ul>"
        for name, role in rows:
            body += f"<li>{html.escape(name)} — {html.escape(role)}</li>"
        body += "</ul><p><a href='/admin'>返回</a></p>"
        self._send(200, body)

    def page_comments(self):
        u = self._need_login()
        if not u:
            return
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT name,content,created FROM comments ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        body = "<h1>评论管理(管理员视图)</h1>"
        for name, content, created in rows:
            # 漏洞: 管理员查看评论也未过滤 => 管理员访问即触发存储型 XSS
            body += f"<div style='border:1px solid #eee;padding:6px'>{html.escape(name)}: {content} <small>({html.escape(created)})</small></div>"
        body += "<p><a href='/admin'>返回</a></p>"
        self._send(200, body)

    def page_ping_form(self):
        u = self._need_login()
        if not u:
            return
        self._send(200, """<h1>网络诊断</h1>
<p>输入目标主机，服务器会执行 ping 测试并返回结果。</p>
<form method=post action=/admin/ping>目标主机:<input name=host placeholder='如 8.8.8.8' style='width:300px'><button>测试</button></form>
<p><a href='/admin'>返回</a></p>""")

    def page_thumb_form(self):
        u = self._need_login()
        if not u:
            return
        self._send(200, """<h1>缩略图生成</h1>
<p>输入一个 URL，服务器会代为抓取内容（模拟生成网页缩略图）。</p>
<form method=post action=/admin/thumb>URL:<input name=url style='width:500px' placeholder='http://example.com'><button>生成</button></form>
<p><a href='/admin'>返回</a></p>""")

    def page_upload_form(self):
        u = self._need_login()
        if not u:
            return
        self._send(200, """<h1>上传头像</h1>
<form method="post" action="/upload" enctype="multipart/form-data"><input type="file" name="avatar"><button>上传</button></form>
<p><small>允许格式: png / jpg / gif</small></p>
<p><a href='/admin'>返回</a></p>""")

    def page_internal_flag(self):
        # 该接口仅允许服务器自身(内部进程)访问。外部直接访问应被拒绝。
        if self.headers.get("X-Internal") == "secblog-server":
            return self._send(200, "FLAG{secblog_ssrf_internal_2026}")
        return self._send(403, "<h1>403 Forbidden</h1><p>该接口仅限内部服务调用。</p>")

    def page_xss_trigger(self):
        # 当存储型 XSS 脚本在受害者(管理员)浏览器执行并向本接口发起请求时触发
        self._send(200, "FLAG{secblog_xss_stored_2026}  <-- 存储型 XSS 已在受害者浏览器成功执行!")

    # ---------- POST 处理 ----------
    def post_login(self, user, pwd):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (user, pwd))
        row = c.fetchone()
        conn.close()
        if row:
            sid = os.urandom(8).hex()
            SESSIONS[sid] = user
            self._send(302, "", {"Location": "/admin", "Set-Cookie": f"sid={sid}; Path=/; Max-Age=3600"})
        else:
            self._send(200, "<h1>登录失败</h1><p>用户名或密码错误。</p><p><a href='/admin/login'>重试</a></p>")

    def post_comment(self, pid, name, content):
        if not pid.isdigit():
            return self._send(400, "bad post_id")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id,name,content,created) VALUES (?,?,?,?)",
                  (int(pid), name, content, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        self._send(302, "", {"Location": f"/article/{pid}"})

    def post_ping(self, host):
        u = self._need_login()
        if not u:
            return
        try:
            # 漏洞: 用户输入直接拼接进 shell 命令行 => 命令注入
            # 注意: 中文 Windows 下 ping 输出为 GBK 编码, 必须用字节读取再 gbk 解码, 否则崩溃
            out = subprocess.run(f"ping -n 1 {host}", shell=True, capture_output=True, timeout=8)
            raw = (out.stdout or b"") + (out.stderr or b"")
            result = raw.decode("gbk", errors="replace")
        except Exception as e:
            result = f"执行出错: {e}"
        self._send(200, f"""<h2>诊断结果</h2>
<pre>{html.escape(result)}</pre>
<p>服务器内部标记(你已获得命令执行权限): FLAG{{secblog_cmdi_root_2026}}</p>
<p><a href='/admin/ping'>返回</a></p>""")

    def post_thumb(self, url):
        u = self._need_login()
        if not u:
            return
        # 漏洞: SSRF — 服务器替用户发起请求，未限制内网地址
        try:
            p = urllib.parse.urlparse(url)
            host = (p.hostname or "").lower()
            port = p.port or (443 if p.scheme == "https" else 80)
            is_internal = (host in ("127.0.0.1", "localhost", "0.0.0.0")
                           or host.startswith("169.254")
                           or host.endswith(".internal"))
            if is_internal:
                if port == 6379 or "redis" in host:
                    return self._send(200, "探测到内网 Redis 服务 (6379) 处于开放/未授权状态!<br>FLAG{secblog_ssrf_found_redis_2026}")
                if p.path.startswith("/internal"):
                    # 模拟服务器以本机身份访问受限内部接口
                    return self._send(200, "服务器以内部身份访问受限接口成功:<br>FLAG{secblog_ssrf_internal_2026}")
                return self._send(200, f"成功访问内网服务 {html.escape(url)}<br>(模拟) 返回: SecBlog 内部服务响应")
            # 外部 URL: 真实抓取(带超时)
            data = urllib.request.urlopen(url, timeout=4).read(1500)
            return self._send(200, f"外部内容(截断):<br><pre>{html.escape(data.decode('utf-8','ignore'))}</pre>")
        except Exception as e:
            return self._send(200, f"请求失败(可能外网不可达或被拦截): {html.escape(str(e))}")

    def post_upload(self, raw):
        u = self._need_login()
        if not u:
            return
        ct = self.headers.get("Content-Type", "")
        m = re.search(r"boundary=(.*)", ct)
        if not m:
            return self._send(400, "无效的上传请求")
        boundary = m.group(1).encode()
        parts = raw.split(b"--" + boundary)
        fname = None
        content = None
        for part in parts:
            if b"filename=" in part:
                fm = re.search(rb'filename="([^"]*)"', part)
                if fm:
                    fname = fm.group(1).decode("utf-8", "ignore")
                idx = part.find(b"\r\n\r\n")
                if idx != -1:
                    content = part[idx + 4:]
                    if content.endswith(b"\r\n"):
                        content = content[:-2]
        if fname is None:
            return self._send(400, "未找到文件")
        # 漏洞1: 扩展名黑名单(可被绕过: .phtml / 大小写 / 双扩展名等)
        blocked = (".php", ".py", ".jsp", ".asp", ".sh", ".phtml")
        lower = fname.lower()
        is_blocked = any(lower.endswith(b) for b in blocked)
        # 漏洞2: 文件名未过滤路径穿越字符
        save_path = os.path.join(UPLOAD_DIR, fname)
        if is_blocked:
            return self._send(200, f"<h1>上传被拦截</h1><p>不允许的扩展名: {html.escape(fname)}</p><p><a href='/upload'>返回</a></p>")
        if content is None:
            content = b""
        try:
            with open(save_path, "wb") as f:
                f.write(content)
            msg = f"文件已保存: {save_path}"
            flag_note = "<p>服务器内部标记(你绕过了上传限制): FLAG{secblog_upload_bypass_2026}</p>"
        except Exception as e:
            msg = f"保存失败: {e}"
            flag_note = ""
        self._send(200, f"<h1>上传结果</h1><p>{html.escape(msg)}</p>{flag_note}<p><a href='/upload'>返回</a></p>")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5010
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", port), Handler) as httpd:
        print(f"[*] SecBlog CMS v1.0 running on http://127.0.0.1:{port}")
        httpd.serve_forever()
