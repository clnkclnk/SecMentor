"""
CSRF 教学靶场 v2 — 简洁版
单端口银行 + 你手写的攻击HTML文件
运行: python csrf-lab-v2.py
访问: http://127.0.0.1:5000
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3, secrets, html, urllib.parse
from datetime import datetime

DB = None
SESSION_TOKENS = {}  # session_id -> csrf_token（服务端存储，攻击者拿不到）

def get_db():
    global DB
    if DB is None:
        DB = sqlite3.connect(":memory:", check_same_thread=False)
        DB.row_factory = sqlite3.Row
    return DB

def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance REAL DEFAULT 10000)")
    db.execute("CREATE TABLE IF NOT EXISTS transfers (id INTEGER PRIMARY KEY AUTOINCREMENT, from_user TEXT, to_account TEXT, amount REAL, time TEXT, is_csrf INTEGER DEFAULT 0, note TEXT)")
    # 只在表为空时插入
    if not db.execute("SELECT count(*) FROM users").fetchone()[0]:
        db.execute("INSERT INTO users VALUES ('alice', 'alice123', 10000)")
        db.execute("INSERT INTO users VALUES ('bob', 'bob123', 5000)")
    db.commit()

# ============ 页面渲染 ============

def render_login_page():
    return """<!DOCTYPE html>
<html><head><title>SecureBank - 登录</title>
<style>
* { box-sizing:border-box; margin:0; }
body { font-family:system-ui; background:#0f172a; color:#e2e8f0; min-height:100vh; display:flex; align-items:center; justify-content:center; }
.card { background:#1e293b; border-radius:16px; padding:40px; width:360px; box-shadow:0 25px 50px rgba(0,0,0,.5); }
h1 { text-align:center; margin-bottom:30px; font-size:24px; color:#f8fafc; }
label { display:block; margin-bottom:6px; font-size:14px; color:#94a3b8; }
input { width:100%; padding:12px; border:2px solid #334155; border-radius:8px; background:#0f172a; color:#fff; font-size:15px; margin-bottom:18px; outline:none; transition:.2s; }
input:focus { border-color:#6366f1; }
button { width:100%; padding:14px; background:linear-gradient(135deg,#6366f1,#8b5cf6); color:white; border:none; border-radius:8px; font-size:16px; cursor:pointer; font-weight:bold; transition:.2s; }
button:hover { transform:scale(1.02); box-shadow:0 4px 15px rgba(99,102,241,.4); }
.msg { padding:12px; border-radius:8px; margin-bottom:18px; text-align:center; font-size:14px; }
.error { background:rgba(239,68,68,.15); color:#f87171; border:1px solid rgba(239,68,68,.3); }
.hint { text-align:center; margin-top:20px; font-size:13px; color:#64748b; }
</style></head><body>
<div class="card">
<h1>🏦 SecureBank</h1>
<div id="msg-area"></div>
<form method="POST" action="/login">
<label>用户名</label><input name="username" placeholder="输入用户名" required autofocus>
<label>密码</label><input name="password" type="password" placeholder="输入密码" required>
<button type="submit">登 录</button>
</form>
<p class="hint">测试账号: alice / alice123</p>
</div></body></html>"""

def render_dashboard(username, balance, transfers, level=1, token=""):
    rows = ""
    for t in reversed(transfers[-10:]):
        tag = ' <span style="color:#ef4444;font-weight:bold">🔴CSRF!</span>' if t['is_csrf'] else ''
        rows += f"<tr><td>{t['time']}</td><td>{t['to_account']}</td><td>¥{t['amount']:,.2f}</td><td>{t['note']}{tag}</td></tr>"

    token_html = ""
    if level == 2 and token:
        token_html = f'<input type="hidden" name="csrf_token" value="{token}"><p style="font-size:12px;color:#94a3b8;margin-top:8px">🛡️ Token防护已启用: <code>{token}</code></p>'

    return f"""<!DOCTYPE html>
<html><head><title>SecureBank - {username}的账户</title>
<style>
* {{ box-sizing:border-box; margin:0; }}
body {{ font-family:system-ui; background:#0f172a; color:#e2e8f0; }}
.nav {{ background:#1e293b; padding:12px 24px; display:flex; gap:16px; align-items:center; border-bottom:1px solid #334155; }}
.nav a {{ color:#94a3b8; text-decoration:none; padding:6px 14px; border-radius:6px; font-size:14px; }}
.nav a.active {{ background:#6366f1; color:#fff; }}
.container {{ max-width:800px; margin:30px auto; padding:0 20px; }}
.card {{ background:#1e293b; border-radius:12px; padding:24px; margin-bottom:20px; }}
.balance-box {{ text-align:center; padding:30px; background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:12px; margin-bottom:24px; border:1px solid #334155; }}
.balance-amount {{ font-size:48px; font-weight:bold; color:#10b981; }}
.balance-label {{ color:#64748b; margin-top:8px; }}
form {{ display:flex; flex-wrap:wrap; gap:12px; align-items:end; }}
form label {{ font-size:13px; color:#94a3b8; min-width:80px; }}
form input {{ padding:10px 14px; border:2px solid #334155; border-radius:8px; background:#0f172a; color:#fff; font-size:14px; outline:none; }}
form input:focus {{ border-color:#6366f1; }}
.btn-danger {{ padding:10px 28px; background:linear-gradient(135deg,#dc2626,#ef4444); color:white; border:none; border-radius:8px; font-size:15px; cursor:pointer; font-weight:bold; }}
.btn-danger:hover {{ opacity:.9; }}
table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
th, td {{ padding:12px; text-align:left; border-bottom:1px solid #334155; font-size:14px; }}
th {{ color:#94a3b8; font-weight:600; font-size:13px; text-transform:uppercase; }}
.msg {{ padding:14px; border-radius:8px; margin-bottom:16px; }}
.success {{ background:rgba(16,185,129,.15); color:#34d399; border:1px solid rgba(16,185,129,.3); }}
.error {{ background:rgba(239,68,68,.15); color:#f87171; border:1px solid rgba(239,68,68,.3); }}
.welcome {{ font-size:20px; margin-bottom:4px; }}
.sub {{ color:#64748b; font-size:14px; }}
</style></head><body>
<div class="nav">
<a href="/dashboard">🏠 首页</a>
<a href="/dashboard" class="active">💰 转账 (Level {level})</a>
<a href="/logout">🚪 退出</a>
</div>
<div class="container">
<div class="balance-box">
<div class="balance-amount">¥{balance:,.2f}</div>
<div class="balance-label">{username} 的账户余额</div>
</div>

<div id="msg-area"></div>

<div class="card">
<div class="welcome">欢迎回来, <strong style="color:#a78bfa">{html.escape(username)}</strong>!</div>
<p class="sub">{'🔒 Token防护模式' if level == 2 else '⚠️ 无防护模式 — 容易受到CSRF攻击'}</p>

<form method="POST" action="/transfer">
<label>收款人</label>
<input name="to_account" value="hacker" placeholder="收款人用户名">
<label>金额</label>
<input name="amount" value="3000" type="number" min="1" step="0.01">
{token_html}
<button type="submit" class="btn-danger">确认转账</button>
</form>
</div>

<div class="card">
<h3 style="margin-bottom:12px;color:#e2e8f0">📋 转账记录</h3>
<table><tr><th>时间</th><th>收款人</th><th>金额</th><th>备注</th></tr>
{rows or '<tr><td colspan="4" style="text-align:center;color:#64748b;padding:20px">暂无记录</td></tr>'}
</table>
</div>
</div></body></html>"""

# ============ 请求处理 ============

class BankHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        path = self.path.rstrip("/") or "/"
        
        if path in ("/", "/login"):
            self._html(render_login_page())
        elif path == "/dashboard":
            self._require_login(lambda u: self._show_dashboard(u))
        elif path == "/logout":
            self._redirect("/", cookies=[("session_id", ""), ("username", "")])
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = self.path.rstrip("/") or "/"

        if path == "/login":
            self._do_login()
        elif path == "/transfer":
            self._do_transfer()
        else:
            self.send_response(404)
            self.end_headers()

    # --- 工具方法 ---

    def _html(self, content):
        body = content.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, url, cookies=None):
        self.send_response(302)
        self.send_header("Location", url)
        if cookies:
            for name, val in cookies:
                if val:
                    self.send_header("Set-Cookie", f"{name}={val}; Path=/; HttpOnly")
                else:
                    self.send_header("Set-Cookie", f"{name}=; Path=/; Max-Age=0")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _cookie(self, name):
        for c in self.headers.get("Cookie", "").split(";"):
            c = c.strip()
            if c.startswith(name + "="):
                return c.split("=", 1)[1]
        return None

    def _require_login(self, handler):
        uname = self._cookie("username")
        if not uname:
            self._redirect("/login")
        else:
            handler(uname)

    def _get_level(self, user):
        # alice 用 Level 1 (无防护), bob 用 Level 2 (Token)
        return 1 if user == "alice" else 2

    # --- 业务逻辑 ---

    def _do_login(self):
        length = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(length).decode())
        user = data.get("username", [""])[0]
        pwd = data.get("password", [""])[0]

        db = get_db()
        row = db.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd)).fetchone()

        if row:
            sid = f"{user}_{secrets.token_hex(6)}"
            token = secrets.token_hex(8)
            SESSION_TOKENS[sid] = token  # 服务端存一份，攻击者拿不到
            self._redirect("/dashboard", cookies=[
                ("session_id", sid),
                ("username", user)
            ])
        else:
            page = render_login_page()
            err = '<div class="msg error">❌ 用户名或密码错误！提示: alice / alice123</div>'
            page = page.replace('<div id="msg-area"></div>', f'<div id="msg-area">{err}</div>')
            self._html(page)

    def _show_dashboard(self, username):
        db = get_db()
        balance = db.execute("SELECT balance FROM users WHERE username=?", (username,)).fetchone()["balance"]
        transfers = db.execute("SELECT * FROM transfers WHERE from_user=? ORDER BY id", (username,)).fetchall()
        level = self._get_level(username)
        # Level 2 用服务端存储的 token，而不是每次随机生成
        sid = self._cookie("session_id")
        token = SESSION_TOKENS.get(sid, "") if level == 2 else ""
        self._html(render_dashboard(username, balance, [dict(t) for t in transfers], level, token))

    def _do_transfer(self):
        uname = self._cookie("username")
        if not uname:
            self._redirect("/login")
            return

        length = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(length).decode())
        to_acc = data.get("to_account", [""])[0]
        try:
            amount = float(data.get("amount", ["0"])[0])
        except ValueError:
            amount = 0

        # ===== Level 2 Token 校验 =====
        level = self._get_level(uname)
        if level == 2:
            sid = self._cookie("session_id")
            submitted = data.get("csrf_token", [""])[0]
            expected = SESSION_TOKENS.get(sid, "")
            if submitted != expected:
                # Token 不对 → 拒绝！这就是防御生效的地方
                msg = "🛡️ <strong>Token 验证失败！请求被拒绝。</strong><br>这很可能是一 次 CSRF 攻击——攻击者拿不到你的 Token。"
                cls = "error"
                balance = get_db().execute("SELECT balance FROM users WHERE username=?", (uname,)).fetchone()["balance"]
                transfers = get_db().execute("SELECT * FROM transfers WHERE from_user=? ORDER BY id", (uname,)).fetchall()
                page = render_dashboard(uname, balance, [dict(t) for t in transfers], level, expected)
                page = page.replace('<div id="msg-area"></div>', f'<div id="msg-area"><div class="msg {cls}">{msg}</div></div>')
                self._html(page)
                return

        referer = self.headers.get("Referer", "")
        is_csrf = "bank.com" not in referer and "127.0.0.1:5000" not in referer

        db = get_db()
        balance = db.execute("SELECT balance FROM users WHERE username=?", (uname,)).fetchone()["balance"]

        if amount <= 0:
            msg, cls = "❌ 金额无效！", "error"
        elif amount > balance:
            msg, cls = f"❌ 余额不足！当前余额 ¥{balance:,.2f}", "error"
        else:
            db.execute("UPDATE users SET balance=balance-? WHERE username=?", (amount, uname))
            db.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, to_acc))
            note = "CSRF攻击!" if is_csrf else "正常转账"
            db.execute("INSERT INTO transfers(from_user,to_account,amount,time,is_csrf,note) VALUES(?,?,?,?,?,?)",
                      (uname, to_acc, amount, datetime.now().strftime("%H:%M:%S"), 1 if is_csrf else 0, note))
            db.commit()
            new_bal = db.execute("SELECT balance FROM users WHERE username=?", (uname,)).fetchone()["balance"]
            msg = f"✅ 转账成功！¥{amount:,.2f} → {to_acc} | 余额: ¥{new_bal:,.2f}"
            if is_csrf:
                msg += f' <span style="color:#ef4444;font-weight:bold">[🔴检测到CSRF攻击!]</span>'
            cls = "success"

        level = self._get_level(uname)
        balance = db.execute("SELECT balance FROM users WHERE username=?", (uname,)).fetchone()["balance"]
        transfers = db.execute("SELECT * FROM transfers WHERE from_user=? ORDER BY id", (uname,)).fetchall()
        page = render_dashboard(uname, balance, [dict(t) for t in transfers], level)
        box = f'<div class="msg {cls}">{msg}</div>'
        page = page.replace('<div id="msg-area"></div>', f'<div id="msg-area">{box}</div>')
        self._html(page)

    def log_message(self, format, *args):
        pass  # 静默日志


# ============ 启动 ============
if __name__ == "__main__":
    init_db()
    server = HTTPServer(("127.0.0.1", 5000), BankHandler)
    print("""
╔════════════════════════════════════════╗
║   🏦 SecureBank CSRF 教学靶场 v2       ║
║                                        ║
║   银行: http://127.0.0.1:5000          ║
║   账号: alice / alice123              ║
║         bob   / bob123                ║
║                                        ║
║   alice → Level 1 无防护 (CSRF可攻击)  ║
║   bob   → Level 2 Token防护           ║
╚════════════════════════════════════════╝
""")
    server.serve_forever()
