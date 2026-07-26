# -*- coding: utf-8 -*-
"""
P5 任意文件下载 / 路径穿越 (Path Traversal) 靶场
- Level 1: 无防护（直接拼接路径，可被 ../ 穿越）
- Level 2: 防御版（realpath 检查是否越出 base 目录）

启动: python traversal-lab.py  ->  http://127.0.0.1:5002
合法文件放在 SECURE_DIR 下，黑客用 ../ 试图跳出该目录。
"""
import os
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 5002
BASE_DIR = os.path.dirname(os.path.abspath(__file__))      # labs/
SECURE_DIR = os.path.join(BASE_DIR, "secure_files")        # labs/secure_files/ 合法文件区
os.makedirs(SECURE_DIR, exist_ok=True)

# 预置几个"合法文件"供下载
PRESET = {
    "welcome.txt": "欢迎使用 MyCloud 下载中心！\n这是你的私人文件，只能下载这里的文件哦。\n",
    "resume.pdf": "（这里是简历内容占位，实际是个文本文件）\n姓名: 张三\n求职意向: 网络安全工程师\n",
    "report.docx": "（季度报告占位）\nQ2 业绩: 达成 120%\n",
}
for name, content in PRESET.items():
    p = os.path.join(SECURE_DIR, name)
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

PAGE_STYLE = """
<style>
  body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
         background:#0f1117; color:#e6e6e6; max-width:760px; margin:40px auto; padding:0 20px; }
  h1 { font-size:20px; font-weight:600; }
  h2 { font-size:15px; color:#9aa0aa; font-weight:500; margin-top:28px; }
  .card { background:#171a21; border:1px solid #2a2f3a; border-radius:12px; padding:20px; margin:16px 0; }
  .file-list a { color:#7aa2f7; text-decoration:none; display:inline-block; margin:4px 12px 4px 0; }
  label { display:block; font-size:13px; color:#9aa0aa; margin:14px 0 6px; }
  input[type=text] { width:100%; padding:10px 12px; background:#0f1117; border:1px solid #2a2f3a;
                     border-radius:8px; color:#e6e6e6; font-size:14px; font-family:monospace; }
  button { margin-top:14px; padding:9px 18px; background:#7aa2f7; color:#0f1117; border:none;
           border-radius:8px; font-size:14px; font-weight:600; cursor:pointer; }
  button:hover { background:#9ab4fa; }
  .tabs a { display:inline-block; padding:6px 14px; margin-right:8px; border-radius:8px;
            text-decoration:none; color:#9aa0aa; border:1px solid #2a2f3a; font-size:13px; }
  .tabs a.active { background:#1f2530; color:#e6e6e6; border-color:#7aa2f7; }
  .msg { padding:12px 14px; border-radius:8px; font-size:13px; margin:14px 0; line-height:1.5; white-space:pre-wrap; font-family:monospace; }
  .msg.danger { background:#2a1414; border:1px solid #a32d2d; color:#f09595; }
  .msg.ok { background:#14241a; border:1px solid #3b6d11; color:#97c459; }
  .msg.warn { background:#2a2114; border:1px solid #854f0b; color:#fac775; }
  .badge { display:inline-block; padding:2px 8px; border-radius:6px; font-size:12px; margin-left:8px; }
  .badge.vuln { background:#2a1414; color:#f09595; }
  .badge.safe { background:#14241a; color:#97c459; }
  code { background:#0f1117; padding:1px 5px; border-radius:4px; color:#f0a868; }
</style>
"""

NAV = """
<div class="tabs">
  <a href="/?level=1" class="{a1}">Level 1 无防护</a>
  <a href="/?level=2" class="{a2}">Level 2 防御版</a>
</div>
""".replace("{a1}", "{a1}").replace("{a2}", "{a2}")


def render_home(level, msg=""):
    secure = ""
    for name in PRESET:
        secure += f'<a href="/download?file={html.escape(name)}&level={level}">📄 {html.escape(name)}</a>'
    level_label = ("无防护" if level == "1" else "防御版")
    badge = '<span class="badge vuln">⚠ 可被穿越</span>' if level == "1" else '<span class="badge safe">🛡 已加固</span>'
    a1 = "active" if level == "1" else ""
    a2 = "active" if level == "2" else ""
    nav = NAV.format(a1=a1, a2=a2)
    hint = ("试试合法文件，再用 <code>..\\..\\..\\..\\..\\..Windows\\system32\\drivers\\etc\\hosts</code> 跳出目录读系统文件！"
            if level == "1" else
            "就算你传 <code>..\\..\\..\\Windows\\system32\\drivers\\etc\\hosts</code>，也会被 realpath 检查拦住。")
    return f"""<!doctype html><html><head><meta charset="utf-8">{PAGE_STYLE}</head><body>
<h1>📁 MyCloud 文件下载中心 <span class="badge {'vuln' if level=='1' else 'safe'}">{level_label}</span></h1>
{nav}
<div class="card">
  <h2>合法文件（点一下就能下载）</h2>
  <div class="file-list">{secure}</div>
</div>
<div class="card">
  <h2>自定义下载（黑客入口）</h2>
  <form method="GET" action="/download">
    <input type="hidden" name="level" value="{level}">
    <label>文件名 / 路径</label>
    <input type="text" name="file" placeholder="例如: report.docx  或  ../../../../etc/passwd" value="">
    <button type="submit">下载</button>
  </form>
  <p style="color:#7a808a;font-size:12px;margin-top:10px">{hint}</p>
</div>
{msg}
<p style="color:#5f5e5a;font-size:12px">靶场地址: http://{HOST}:{PORT} ｜ 合法文件区: labs/secure_files/</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 安静

    def _send(self, body, code=200, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        level = qs.get("level", ["1"])[0]

        if u.path in ("/", "/index.html"):
            self._send(render_home(level))
            return

        if u.path == "/download":
            filename = qs.get("file", [""])[0]
            level = qs.get("level", ["1"])[0]
            if not filename:
                self._send(render_home(level, '<div class="msg warn">请输入文件名</div>'))
                return
            if level == "2":
                self._handle_safe(filename, level)
            else:
                self._handle_vuln(filename, level)
            return

        self._send(render_home(level, '<div class="msg warn">未知路径</div>'), 404)

    def _handle_vuln(self, filename, level):
        # 漏洞版：直接拼接，无任何过滤 —— 真实去读归一化后的路径
        target = os.path.join(SECURE_DIR, filename)
        abs_path = os.path.abspath(target)
        if os.path.isfile(abs_path):
            try:
                with open(abs_path, "rb") as f:
                    content = f.read()
                if len(content) > 4000:
                    content = content[:4000]
                decoded = content.decode(errors="replace") + "\n... (内容过长，已截断) ..."
                in_base = abs_path == os.path.realpath(SECURE_DIR) or abs_path.startswith(
                    os.path.realpath(SECURE_DIR) + os.sep)
                if in_base:
                    msg = f'<div class="msg ok">✅ 合法文件下载成功:\n{html.escape(decoded)}</div>'
                else:
                    msg = (f'<div class="msg danger">🔴 路径穿越成功！读到了越界文件:\n'
                           f'{html.escape(abs_path)}\n\n' + html.escape(decoded) + '</div>')
            except Exception as e:
                msg = f'<div class="msg danger">🔴 穿越成功但读取失败: {html.escape(str(e))}</div>'
        else:
            msg = (f'<div class="msg warn">文件不存在: <code>{html.escape(abs_path)}</code>\n'
                   f'（提示: Windows 上用 <code>..\\..\\..\\..\\..\\..Windows\\system32\\drivers\\etc\\hosts</code>）</div>')
        self._send(render_home(level, msg))

    def _handle_safe(self, filename, level):
        # 防御版：realpath 后检查是否仍在 SECURE_DIR 内
        real_target = os.path.realpath(os.path.join(SECURE_DIR, filename))
        real_base = os.path.realpath(SECURE_DIR)
        if real_target == real_base or real_target.startswith(real_base + os.sep):
            if os.path.isfile(real_target):
                with open(real_target, "rb") as f:
                    decoded = f.read().decode(errors="replace")
                msg = f'<div class="msg ok">✅ 合法文件下载成功:\n{html.escape(decoded)}</div>'
                self._send(render_home(level, msg))
                return
            msg = f'<div class="msg ok">✅ 合法文件下载成功。</div>'
            self._send(render_home(level, msg))
        else:
            msg = (f'<div class="msg danger">🛡 路径穿越被拦截！\n'
                   f'归一化后目标: <code>{html.escape(real_target)}</code>\n'
                   f'不在允许目录 <code>{html.escape(real_base)}</code> 内，已拒绝。</div>')
            self._send(render_home(level, msg))


if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[*] 路径穿越靶场已启动: http://{HOST}:{PORT}")
    srv.serve_forever()
