"""
文件上传漏洞教学靶场
单端口，两个等级：
  Level 1 (无防护)   : 原样保存，.py 文件可被"执行" (模拟WebShell RCE)
  Level 2 (白名单防护): 只允许图片，重命名，拒绝脚本

运行: python upload-lab.py
访问: http://127.0.0.1:5001
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, html, secrets, uuid

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def render_home():
    return """<!DOCTYPE html>
<html><head><title>文件上传靶场</title>
<style>
* { box-sizing:border-box; margin:0; }
body { font-family:system-ui; background:#0f172a; color:#e2e8f0; min-height:100vh; padding:40px; }
h1 { color:#f8fafc; margin-bottom:8px; }
.sub { color:#94a3b8; margin-bottom:30px; font-size:14px; }
.card { background:#1e293b; border-radius:12px; padding:24px; max-width:600px; margin-bottom:20px; }
label { display:block; color:#94a3b8; font-size:14px; margin-bottom:8px; }
input[type=file] { width:100%; padding:12px; background:#0f172a; border:2px solid #334155; border-radius:8px; color:#fff; margin-bottom:16px; }
button { padding:12px 28px; background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff; border:none; border-radius:8px; font-size:15px; cursor:pointer; font-weight:bold; }
button:hover { opacity:.9; }
.tabs { display:flex; gap:12px; margin-bottom:24px; }
.tab { padding:8px 18px; border-radius:8px; background:#1e293b; color:#94a3b8; cursor:pointer; font-size:14px; text-decoration:none; }
.tab.active { background:#6366f1; color:#fff; }
.msg { padding:14px; border-radius:8px; margin-bottom:16px; font-size:14px; }
.success { background:rgba(16,185,129,.15); color:#34d399; border:1px solid rgba(16,185,129,.3); }
.error { background:rgba(239,68,68,.15); color:#f87171; border:1px solid rgba(239,68,68,.3); }
.code { background:#0f172a; padding:14px; border-radius:8px; font-family:monospace; font-size:13px; color:#a5b4fc; margin:10px 0; white-space:pre-wrap; }
ul { margin:10px 0 0 20px; color:#cbd5e1; font-size:14px; line-height:1.8; }
</style></head><body>
<h1>文件上传漏洞靶场</h1>
<p class="sub">上传的文件会被保存到 uploads/ 目录。试试传个"木马"会发生什么。</p>

<div class="tabs">
<a href="/?level=1" class="tab active">Level 1 无防护</a>
<a href="/?level=2" class="tab">Level 2 白名单防护</a>
</div>

<div class="card">
<h3 style="margin-bottom:16px;color:#e2e8f0">上传文件</h3>
<form method="POST" action="/upload" enctype="multipart/form-data">
<input type="hidden" name="level" value="1">
<label>选择一个文件</label>
<input type="file" name="file" required>
<button type="submit">上传</button>
</form>
</div>

<div class="card">
<h3 style="margin-bottom:12px;color:#e2e8f0">试着传这个 WebShell：</h3>
<div class="code"># 保存为 shell.py
import os
print("命令执行结果:")
print(os.popen("whoami").read())
print(os.popen("dir").read())</div>
<p style="color:#94a3b8;font-size:13px">把上面代码存成 <code>shell.py</code>，上传后访问 <code>/uploads/shell.py</code> 看效果。</p>
</div>

<div id="msg-area"></div>
</body></html>"""

def render_level2_home():
    return render_home().replace(
        '<a href="/?level=1" class="tab active">Level 1 无防护</a>',
        '<a href="/?level=1" class="tab">Level 1 无防护</a>'
    ).replace(
        '<a href="/?level=2" class="tab">Level 2 白名单防护</a>',
        '<a href="/?level=2" class="tab active">Level 2 白名单防护</a>'
    ).replace(
        '<input type="hidden" name="level" value="1">',
        '<input type="hidden" name="level" value="2">'
    ).replace(
        '<p class="sub">上传的文件会被保存到 uploads/ 目录。试试传个"木马"会发生什么。</p>',
        '<p class="sub">🛡️ 本关只允许 .jpg/.png/.gif/.pdf，且随机重命名。传 .py 会被拒绝。</p>'
    )

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/uploads/"):
            self._serve_upload(self.path[len("/uploads/"):])
            return
        level = "1"
        if "level=2" in self.path:
            level = "2"
        page = render_level2_home() if level == "2" else render_home()
        self._html(page)

    def do_POST(self):
        if not self.path.startswith("/upload"):
            self.send_response(404); self.end_headers(); return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        boundary = self.headers.get("Content-Type", "").split("boundary=")[-1].strip()
        level = "1"
        filename, content, fields = self._parse_multipart(body, boundary)
        if fields.get("level") == "2":
            level = "2"

        if not filename:
            self._show_result(level, '<div class="msg error">❌ 没有收到文件</div>')
            return

        # Level 2: 白名单 + 重命名
        if level == "2":
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".jpg", ".png", ".gif", ".pdf"):
                self._show_result(level, f'<div class="msg error">🛡️ 白名单拦截！拒绝后缀 <code>{html.escape(ext)}</code>（只允许 .jpg/.png/.gif/.pdf）</div>')
                return
            safe_name = uuid.uuid4().hex + ext  # 随机重命名
            self._save(safe_name, content)
            self._show_result(level, f'<div class="msg success">✅ 上传成功（白名单通过，已随机重命名为 <code>{safe_name}</code>，无法执行）</div>')
            return

        # Level 1: 原样保存（漏洞！）
        self._save(filename, content)
        if filename.endswith(".py"):
            url = f"http://127.0.0.1:5001/uploads/{filename}"
            self._show_result(level, f'''<div class="msg error">
            ⚠️ <strong>WebShell 已落地！</strong> 文件 <code>{html.escape(filename)}</code> 被原样保存。<br>
            访问 <a href="/uploads/{html.escape(filename)}" style="color:#f87171">{url}</a> 即可执行其中的代码！
            </div>''')
        else:
            self._show_result(level, f'<div class="msg success">✅ 文件 <code>{html.escape(filename)}</code> 已保存</div>')

    # --- 工具 ---
    def _parse_multipart(self, body, boundary):
        delimiter = ("--" + boundary).encode()
        parts = body.split(delimiter)
        filename = ""
        content = b""
        fields = {}
        for part in parts:
            if b"filename=" in part:
                # 提取文件名
                fn_start = part.find(b'filename="') + 10
                fn_end = part.find(b'"', fn_start)
                filename = part[fn_start:fn_end].decode(errors="ignore")
                # 提取内容（跳过头部空行）
                content_start = part.find(b"\r\n\r\n") + 4
                content_end = part.rfind(b"\r\n")
                content = part[content_start:content_end]
            elif b"name=" in part and b"filename=" not in part:
                # 普通表单字段（无文件）
                n_start = part.find(b'name="') + 6
                n_end = part.find(b'"', n_start)
                name = part[n_start:n_end].decode(errors="ignore")
                v_start = part.find(b"\r\n\r\n") + 4
                v_end = part.rfind(b"\r\n")
                value = part[v_start:v_end].decode(errors="ignore")
                fields[name] = value
        return filename, content, fields

    def _save(self, name, content):
        with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
            f.write(content)

    def _serve_upload(self, name):
        path = os.path.join(UPLOAD_DIR, os.path.basename(name))
        if not os.path.exists(path):
            self.send_response(404); self.end_headers(); return
        # 模拟 WebShell 执行：如果是 .py 就执行并返回输出
        if name.endswith(".py"):
            import subprocess
            try:
                result = subprocess.run(
                    ["C:\\Users\\clnk\\.workbuddy\\binaries\\python\\versions\\3.13.12\\python.exe", path],
                    capture_output=True, text=True, timeout=5
                )
                output = result.stdout + result.stderr
            except Exception as e:
                output = f"执行错误: {e}"
            body = f"""<!DOCTYPE html><html><head><title>RCE!</title>
<style>body{{font-family:monospace;background:#0f172a;color:#34d399;padding:30px}}
h1{{color:#f87171}}.out{{background:#000;padding:20px;border-radius:8px;white-space:pre-wrap}}</style>
</head><body>
<h1>💀 WebShell 远程代码执行成功！</h1>
<p>这是服务器执行你上传的 {html.escape(name)} 的输出：</p>
<div class="out">{html.escape(output)}</div>
</body></html>"""
            self._html(body)
        else:
            # 普通文件，直接下载/显示
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())

    def _html(self, content):
        body = content.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _show_result(self, level, msg_html):
        """上传完成后直接显示结果（不跳转，避免消息丢失）"""
        page = render_home() if level == "1" else render_level2_home()
        # 把消息插入到 msg-area div 前
        page = page.replace('<div id="msg-area"></div>', '<div id="msg-area">' + msg_html + '</div>')
        self._html(page)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 5001), Handler)
    print("文件上传靶场: http://127.0.0.1:5001")
    server.serve_forever()
