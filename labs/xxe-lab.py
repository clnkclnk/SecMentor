#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XXE (XML 外部实体注入) 靶场
Level 1: 漏洞版 - lxml 开启外部实体解析（file:// 读本地文件 + http:// 打内网）
Level 2: 防御版 - 关闭外部实体解析（安全）

启动：python xxe-lab.py  →  http://127.0.0.1:5005/?level=1
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from lxml import etree

HOST = "127.0.0.1"
PORT = 5005
BASE = os.path.dirname(os.path.abspath(__file__))

# 准备一个"服务器上的敏感文件"，用于演示 file:// 读文件
SECRET_FILE = os.path.join(BASE, "xxe_secret.txt")
if not os.path.exists(SECRET_FILE):
    with open(SECRET_FILE, "w", encoding="utf-8") as f:
        f.write("DB_PASSWORD=Sup3rS3cret!2026\nAPI_KEY=ak_live_8f3c2d9b1e77\n(这是服务器上的敏感配置文件)\n")

NORMAL_XML = """<?xml version="1.0"?>
<user>
  <name>alice</name>
</user>"""

TEMPLATE = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>XXE 靶场</title>
<style>
body{font-family:system-ui;max-width:880px;margin:36px auto;padding:0 16px;background:#0f1117;color:#e6e6e6}
h1{color:#7ee787;font-size:20px;margin-bottom:4px}
h3{color:#e6e6e6;font-size:15px;margin-top:18px}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-bottom:8px}
.badge.v{background:#ff7b7222;color:#ff7b72;border:1px solid #ff7b72}
.badge.s{background:#7ee78722;color:#7ee787;border:1px solid #7ee787}
.box{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px;margin:12px 0;white-space:pre-wrap;font-family:ui-monospace,monospace;word-break:break-all;font-size:13px}
.ok{color:#7ee787}.bad{color:#ff7b72}
.hint{color:#9da7b3;font-size:13px;line-height:1.6}
textarea{width:100%;height:180px;background:#0d1117;color:#e6e6e6;border:1px solid #30363d;border-radius:6px;padding:10px;font-family:ui-monospace,monospace;font-size:13px}
button.sub{margin-top:8px;padding:8px 18px;border:0;border-radius:6px;background:#238636;color:#fff;cursor:pointer;font-size:14px}
.pill{display:inline-block;background:#21262d;border:1px solid #30363d;border-radius:6px;padding:6px 10px;margin:4px 6px 4px 0;font-family:ui-monospace,monospace;font-size:12px;cursor:pointer;color:#58a6ff}
.pill:hover{border-color:#58a6ff}
code{background:#0d1117;padding:1px 5px;border-radius:4px;color:#ffa657}
</style></head><body>
__BODY__
<script>
function loadPayload(n){
  const p = {
    1: '<?xml version="1.0"?>\\n<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///C:/Windows/System32/drivers/etc/hosts"> ]>\\n<user><name>&xxe;</name></user>',
    2: '<?xml version="1.0"?>\\n<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "xxe_secret.txt"> ]>\\n<user><name>&xxe;</name></user>',
    3: '<?xml version="1.0"?>\\n<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "http://127.0.0.1:5005/internal"> ]>\\n<user><name>&xxe;</name></user>'
  };
  document.querySelector('textarea[name=xml]').value = p[n];
}
</script>
</body></html>"""


def build_page(level, submitted="", result="", ok=True):
    if level == "2":
        badge = '<span class="badge s">防御版 Level 2</span>'
        mode = "<b style='color:#7ee787'>关闭外部实体解析</b>"
    else:
        badge = '<span class="badge v">漏洞版 Level 1</span>'
        mode = "<b style='color:#ff7b72'>开启外部实体解析</b>"
    ta = submitted if submitted else NORMAL_XML
    res_cls = "ok" if ok else "bad"
    res_txt = result if result else "（提交后在这里显示）"
    body = f'''
<h1>XXE 靶场 · {badge}</h1>
<p class="hint">把 XML 粘贴到下面，提交后服务器会用 {mode} 的解析器处理。这就是 XXE 漏洞的「武器台」——你亲手写 payload。</p>

<h3>① 提交你的 XML 武器</h3>
<form method="post" action="/parse?level={level}">
  <textarea name="xml">{ta}</textarea>
  <br><button type="submit" class="sub">▶ 让服务器解析</button>
</form>
<p class="hint" style="margin-top:10px">一键载入现成武器（点完再提交）：</p>
<button type="button" class="pill" onclick="loadPayload(1)">载入: 读系统 hosts</button>
<button type="button" class="pill" onclick="loadPayload(2)">载入: 读靶场秘密</button>
<button type="button" class="pill" onclick="loadPayload(3)">载入: SSRF 打内网</button>

<h3>② 解析结果</h3>
<div class="box {res_cls}">{res_txt}</div>
'''
    return TEMPLATE.replace("__BODY__", body)


def parse_xml(xml_text, level):
    if not xml_text.strip():
        return ("（请粘贴 XML 再提交）", True)
    try:
        data = xml_text.encode("utf-8")
        if level == "2":
            parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
            root = etree.fromstring(data, parser)
            content = "".join(root.itertext())
            return ("[防御版] 解析成功，但外部实体未被展开（安全）:\n" + content[:500], True)
        else:
            parser = etree.XMLParser(resolve_entities=True, no_network=False, load_dtd=True)
            base = "file:///" + BASE.replace("\\", "/") + "/"
            root = etree.fromstring(data, parser, base_url=base)
            content = "".join(root.itertext())
            return ("[漏洞版] 外部实体已展开！解析结果:\n" + content[:1500], True)
    except Exception as e:
        msg = str(e).splitlines()[0][:300]
        if level == "2":
            return ("[防御版] 外部实体被拒绝 ✅\n错误: " + msg, True)
        return ("[漏洞版] 解析出错: " + msg, False)


class Handler(BaseHTTPRequestHandler):
    def _send(self, html, status=200, ctype="text/html"):
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/internal":
            self._send("🔐 内部接口(仅服务器内网可访问):\nFLAG{xxe_reached_internal_service_2026}\n(真实场景: 这是 Redis / 数据库 / 云元数据)",
                       ctype="text/plain")
            return
        qs = parse_qs(parsed.query)
        level = qs.get("level", ["1"])[0]
        self._send(build_page(level))

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        level = qs.get("level", ["1"])[0]
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        posted = parse_qs(raw)
        xml_in = posted.get("xml", [""])[0]
        result, ok = parse_xml(xml_in, level)
        self._send(build_page(level, xml_in, result, ok))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"XXE 靶场启动: http://{HOST}:{PORT}/?level=1")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
