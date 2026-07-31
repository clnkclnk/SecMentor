#!/usr/bin/env python3
# MySQL 安全入门靶场（用 sqlite3 模拟业务数据库）
# 演示中间件/数据库两类典型配置错误：
#   模式① 未授权访问：接口无 token 校验即可拖库
#   模式② 弱口令：admin/123456 直接登进后台
# 用法: python mysql-lab.py [port]   默认 5009
import sqlite3, json, sys, http.server, socketserver, urllib.parse

DB_PATH = "mysql_lab.db"

PAGE = """
<!doctype html><html lang=zh><head><meta charset=utf-8>
<title>MySQL 安全靶场</title>
<style>body{font-family:system-ui,Arial,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;background:#0f1117;color:#e6e6e6}
h1{color:#ff5c5c}h2{color:#7fd1ff;border-bottom:1px solid #333;padding-bottom:6px}
code{background:#1c2230;padding:2px 6px;border-radius:4px;color:#9ff}
pre{background:#1c2230;padding:12px;border-radius:8px;overflow:auto}
.lev{border:1px solid #333;border-radius:8px;padding:12px 16px;margin:10px 0}
.vuln{border-color:#ff5c5c}.secure{border-color:#3ad29f}
.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:10px;margin-right:6px}
.t-vuln{background:#ff5c5c22;color:#ff8a8a}.t-sec{background:#3ad29f22;color:#7ff0c8}</style></head>
<body>
<h1>MySQL 安全入门靶场 (:5009)</h1>
<p>本靶场用 sqlite 模拟一个业务数据库（users 表 + secrets 表）。两套接口对比演示 MySQL 类服务的典型配置错误。</p>

<div class=lev.vuln><b><span class=tag.t-vuln>漏洞版</span>Level 1：弱口令 + 未授权</b>
<h2>① 弱口令登录</h2>
<pre>POST /vuln/login?user=admin&pass=123456</pre>
<p>用弱口令直接登进后台，服务端返回 token=admin-session。</p>
<h2>② 未授权拖库（无需任何 token）</h2>
<pre>GET /vuln/users        # 列出全部用户含明文密码</pre>
<pre>GET /vuln/secret?k=flag   # 直接拿走 FLAG</pre>
</div>

<div class=lev.secure><b><span class=tag.t-sec>防御版</span>Level 2：强密码 + 鉴权</b>
<h2>① 拒绝弱口令</h2>
<pre>POST /secure/login?user=admin&pass=123456   # 返回"密码太弱，拒绝"</pre>
<h2>② 接口需 admin token，否则 403</h2>
<pre>GET /secure/users?token=admin-session</pre>
<pre>GET /secure/secret?token=admin-session</pre>
</div>
<p style=color:#888>提示：先打 Level1 体验危害，再对比 Level2 防御。</p>
</body></html>
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS secrets")
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    c.execute("INSERT INTO users (username,password,role) VALUES ('admin','123456','admin')")
    c.execute("INSERT INTO users (username,password,role) VALUES ('alice','Passw0rd!2026','user')")
    c.execute("INSERT INTO users (username,password,role) VALUES ('bob','qwe123','user')")
    c.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY, k TEXT, v TEXT)")
    c.execute("INSERT INTO secrets (k,v) VALUES ('flag','FLAG{mysql_weak_pwd_pwned_2026}')")
    c.execute("INSERT INTO secrets (k,v) VALUES ('db_config','host=127.0.0.1;port=3306;user=root;pass=EmptyPass')")
    conn.commit()
    conn.close()

class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, as_json=False):
        self.send_response(code)
        ct = "application/json; charset=utf-8" if as_json else "text/html; charset=utf-8"
        self.send_header("Content-Type", ct)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            if path in ("/", ""):
                self._send(200, PAGE)
            elif path == "/vuln/users":
                rows = c.execute("SELECT id,username,password,role FROM users").fetchall()
                self._send(200, json.dumps(rows, ensure_ascii=False), True)
            elif path == "/vuln/secret":
                k = qs.get("k", ["flag"])[0]
                v = c.execute("SELECT v FROM secrets WHERE k=?", (k,)).fetchone()
                self._send(200, json.dumps({"k": k, "v": v[0] if v else None}, ensure_ascii=False), True)
            elif path == "/secure/users":
                token = qs.get("token", [""])[0]
                if token != "admin-session":
                    self._send(403, json.dumps({"error": "未授权：需要 admin token"}, ensure_ascii=False), True)
                else:
                    rows = c.execute("SELECT id,username,role FROM users").fetchall()
                    self._send(200, json.dumps(rows, ensure_ascii=False), True)
            elif path == "/secure/secret":
                token = qs.get("token", [""])[0]
                if token != "admin-session":
                    self._send(403, json.dumps({"error": "未授权"}, ensure_ascii=False), True)
                else:
                    v = c.execute("SELECT v FROM secrets WHERE k='flag'").fetchone()
                    self._send(200, json.dumps({"flag": v[0]}, ensure_ascii=False), True)
            else:
                self._send(404, "not found")
        finally:
            conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else ""
        qs = urllib.parse.parse_qs(body) if body else urllib.parse.parse_qs(parsed.query)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            if path == "/vuln/login":
                user = qs.get("user", [""])[0]
                pw = qs.get("pass", [""])[0]
                row = c.execute("SELECT role FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
                if row:
                    self._send(200, json.dumps({"token": "admin-session", "role": row[0], "msg": "登录成功（弱口令生效）"}, ensure_ascii=False), True)
                else:
                    self._send(401, json.dumps({"error": "用户名或密码错误"}, ensure_ascii=False), True)
            elif path == "/secure/login":
                user = qs.get("user", [""])[0]
                pw = qs.get("pass", [""])[0]
                if len(pw) < 8 or pw.isdigit():
                    self._send(400, json.dumps({"error": "密码太弱，拒绝（防御：强制强密码策略）"}, ensure_ascii=False), True)
                    return
                row = c.execute("SELECT role FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
                if row:
                    self._send(200, json.dumps({"token": "admin-session", "role": row[0], "msg": "登录成功（强密码）"}, ensure_ascii=False), True)
                else:
                    self._send(401, json.dumps({"error": "登录失败"}, ensure_ascii=False), True)
            else:
                self._send(404, "not found")
        finally:
            conn.close()

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    init_db()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5009
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
        print(f"MySQL lab running on http://127.0.0.1:{port}")
        httpd.serve_forever()
