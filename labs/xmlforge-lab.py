# -*- coding: utf-8 -*-
"""
XMLForge —— XXE 进阶靶场（漏洞站）
端口: 5032
主题: 企业配置导入系统，用户提交 XML 配置，服务器解析。
      攻击者监听站（xxe-attacker.py）在 5033 端口。

FLAG:
  FLAG1 有回显读文件  -> /parse 解析结果回显，file:// 读 xmlforge_secret.txt
  FLAG2 SSRF 打内网   -> /parse 里 SYSTEM "http://127.0.0.1:5032/internal/flag"
  FLAG3 无回显OOB盲打 -> /parse-blind 不回显，参数实体+外部DTD exfil 到 5033
  安全对照           -> /parse-secure resolve_entities=False 打不动
"""
import os
import re
import sqlite3
from flask import Flask, request, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "xmlforge.db")
PORT = 5032

app = Flask(__name__)

FLAGS = {
    "flag1": "FLAG1{xxe_file_read_2026}",
    "flag2": "FLAG2{xxe_ssrf_internal_2026}",
    "flag3": "FLAG3{xxe_oob_exfil_2026}",
}

# ---------------- 教学模拟 XML 解析器（完整复现 XXE 语义） ----------------
# 真实环境：PHP/Java 的 libxml 默认会展开外部实体。Python lxml 默认安全（libxml2 不执行
# 外部 DTD 参数实体），所以靶场用自写解析器精确模拟 PHP 的行为，教学上等价。

import re
import urllib.request
from urllib.parse import quote


def sim_fetch(url):
    """模拟解析器 fetch：file:// 读本地文件；http:// 发请求返回响应。
    读取失败时返回错误信息（真实解析器会报错并泄露路径）"""
    p = ""
    try:
        if url.startswith("file://"):
            p = url[len("file://"):].lstrip("/")
            if not re.match(r"^[A-Za-z]:", p):
                p = os.path.join(BASE_DIR, p)
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif url.startswith("http://"):
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read().decode("utf-8", "ignore")
    except FileNotFoundError:
        return "[解析错误] 文件不存在: " + p
    except PermissionError:
        return "[解析错误] 权限不足: " + p
    except Exception as e:
        return "[解析错误] " + str(e)
    return ""


class SimXML:
    """教学用 XXE 模拟解析器：内部/外部实体 + 外部 DTD + 参数实体(OOB)"""

    def __init__(self, resolve=True):
        self.resolve = resolve   # False = resolve_entities=False（实体全部不展开）
        self.entities = {}       # 普通实体 name -> (kind, val)  kind: url|val

    def parse(self, xml_text):
        m = re.search(r"<!DOCTYPE\s+\w+\s*\[(.*?)\]>", xml_text, re.S)
        if not m:
            return xml_text
        dtd = m.group(1)
        body = xml_text[:m.start()] + xml_text[m.end():]
        if not self.resolve:
            return body          # 安全版：不处理任何实体
        self._process_dtd(dtd)
        # 替换文档里的 &name;
        for name, (kind, val) in self.entities.items():
            if kind == "url":
                val = sim_fetch(val)
            esc = val.replace("\\", "\\\\").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            body = re.sub(r"&%s;" % name, esc, body)
        return body

    def _process_dtd(self, dtd):
        """处理 DTD 块：定义实体 + 执行参数实体引用"""
        # 1. 普通实体定义 <!ENTITY name SYSTEM "..."> 或 <!ENTITY name "...">
        for mm in re.finditer(r"<!ENTITY\s+(\w+)\s+(SYSTEM\s+)?(\"[^\"]*\"|'[^']*')\s*>", dtd, re.S):
            name, is_sys, val = mm.group(1), mm.group(2), mm.group(3).strip("\"'")
            self.entities[name] = ("url" if is_sys else "val", val)
        # 2. 参数实体定义 <!ENTITY % name SYSTEM "...">
        param = {}
        for mm in re.finditer(r"<!ENTITY\s+%\s*(\w+)\s+(SYSTEM\s+)?(\"[^\"]*\"|'[^']*')\s*>", dtd, re.S):
            name, is_sys, val = mm.group(1), mm.group(2), mm.group(3).strip("\"'")
            param[name] = ("url" if is_sys else "val", val)
        # 3. 按顺序执行 %name; 引用（OOB：加载外部 DTD / 触发 exfil）
        for mm in re.finditer(r"%(\w+);", dtd):
            name = mm.group(1)
            if name not in param:
                continue
            kind, val = param[name]
            if kind == "url":
                fetched = sim_fetch(val)      # 加载外部 DTD（可递归）
                self._process_dtd(fetched)
            else:
                # 值参数实体：可能嵌套 <!ENTITY &#x25; exfil SYSTEM '...%file;...'>
                nested = re.search(r"<!ENTITY\s+&#x25;\s*(\w+)\s+SYSTEM\s+('[^']*'|\"[^\"]*\")", val, re.S)
                if nested:
                    nname, nurl = nested.group(1), nested.group(2).strip("\"'")
                    file_val = ""
                    for src in (param, self.entities):
                        if "file" in src:
                            fk, fv = src["file"]
                            file_val = sim_fetch(fv) if fk == "url" else fv
                            break
                    ex_url = nurl.replace("%file;", quote(file_val))   # URL 编码（真实世界用 URL/DNS 带外）
                    sim_fetch(ex_url)         # 触发 exfil 请求（副作用→5033 收到）


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
         "textarea{width:96%;height:150px;padding:8px;border-radius:6px;border:1px solid #3a4560;background:#0f1320;color:#e6e6e6;font-family:monospace}"
         "input[type=submit]{padding:8px 16px;border:0;border-radius:6px;background:#5ad;color:#06121f;font-weight:bold;cursor:pointer}"
         ".msg{background:#0a0d16;border:1px solid #2d3650;border-radius:6px;padding:10px;margin:8px 0;font-family:monospace;font-size:12px;white-space:pre-wrap;overflow-x:auto}"
         ".hint{color:#888;font-size:12px}")


def render(content_html=""):
    flags = get_flags()
    fc = lambda n: "on" if flags[n] else "off"
    fk = lambda n: "✅" if flags[n] else "🔒"
    return ("<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
            "<title>XMLForge 配置中心</title><style>" + STYLE + "</style></head><body>"
            "<h1>XMLForge 配置中心</h1>"
            "<p style='color:#888;margin:0 0 8px'>提交 XML 配置，服务器解析并返回</p>"
            "<div class='flags'>"
            "<div class='flag " + fc('flag1') + "'>FLAG1 读文件 " + fk('flag1') + "</div>"
            "<div class='flag " + fc('flag2') + "'>FLAG2 SSRF " + fk('flag2') + "</div>"
            "<div class='flag " + fc('flag3') + "'>FLAG3 OOB盲打 " + fk('flag3') + "</div>"
            "</div>"
            "<nav><a href='/'>首页</a> <a href='/parse'>解析(有回显)</a> "
            "<a href='/parse-blind'>解析(无回显)</a> <a href='/parse-secure'>安全版</a> "
            "<a href='/attacker'>攻击者站</a> <a href='/reset'>重置</a></nav>"
            + content_html + "</body></html>")


def xml_form(action, note):
    return ("<div class='card'><h3>提交 XML</h3>"
            "<form method='post' action='" + action + "'>"
            "<textarea name='xml' placeholder='&lt;?xml version=&quot;1.0&quot;?&gt;...'></textarea><br>"
            "<input type='submit' value='解析'></form>"
            "<p class='hint'>" + note + "</p></div>")


@app.route("/")
def index():
    content = ("<div class='card'><h3>欢迎</h3><p>这是一个企业配置导入系统，提交 XML 配置让服务器解析。</p>"
               "<ol>"
               "<li><b>/parse</b>：解析并<b>回显</b>结果（有回显）</li>"
               "<li><b>/parse-blind</b>：解析但<b>不回显</b>（盲打入口）</li>"
               "<li><b>/parse-secure</b>：安全版（对照）</li>"
               "<li>攻击者监听站：<code>http://127.0.0.1:5033/</code>（evil.dtd + OOB 接收）</li>"
               "</ol>"
               "<p class='hint'>3 个 FLAG：读文件 / SSRF / OOB 盲打</p></div>")
    return render(content)


@app.route("/parse", methods=["GET", "POST"])
def parse():
    if request.method == "POST":
        xml = request.form.get("xml", "")
        try:
            # 漏洞版：模拟解析器展开实体（等价 PHP libxml 默认行为）
            result = SimXML(resolve=True).parse(xml)
        except Exception as e:
            result = "[解析错误] " + str(e)
        # FLAG 检测：解析结果回显含 FLAG 内容
        if "FLAG1" in result:
            set_flag("flag1")
        if "FLAG2" in result:
            set_flag("flag2")
        return render(xml_form("/parse", "有回显：解析结果会显示出来") +
                      "<div class='msg'>解析结果：\n" + result + "</div>")
    return render(xml_form("/parse", "有回显：解析结果会显示出来"))


@app.route("/parse-blind", methods=["GET", "POST"])
def parse_blind():
    if request.method == "POST":
        xml = request.form.get("xml", "")
        try:
            # 漏洞版但不回显：解析过程触发外部 DTD / exfil（数据带外传到 5033）
            SimXML(resolve=True).parse(xml)
        except Exception:
            pass
        return render(xml_form("/parse-blind", "无回显：解析成功只显示『已处理』，数据去哪了？") +
                      "<div class='msg'>已处理（解析完成，不显示结果）</div>")
    return render(xml_form("/parse-blind", "无回显：解析成功只显示『已处理』"))


@app.route("/parse-secure", methods=["GET", "POST"])
def parse_secure():
    if request.method == "POST":
        xml = request.form.get("xml", "")
        try:
            # 防御版：resolve_entities=False，实体全部不展开（根治）
            result = SimXML(resolve=False).parse(xml)
        except Exception as e:
            result = "[解析错误] " + str(e)
        return render(xml_form("/parse-secure", "安全版：resolve_entities=False，实体不会被展开") +
                      "<div class='msg'>解析结果：\n" + result + "</div>")
    return render(xml_form("/parse-secure", "安全版：resolve_entities=False，实体不会被展开"))


@app.route("/internal/flag")
def internal_flag():
    # SSRF 目标（外部直接访问也可以，但教学上通过 XXE SSRF 打）
    return "内部接口数据: " + FLAGS["flag2"] + " (只有服务器本机能访问的服务)"


@app.route("/attacker")
def attacker_page():
    content = ("<div class='card'><h3>攻击者监听站</h3>"
               "<p>OOB 盲打需要攻击者服务器，打开：</p>"
               "<p><code>http://127.0.0.1:5033/</code></p>"
               "<p>那里有 <code>/evil.dtd</code>（恶意 DTD）和 exfil 接收记录。</p>"
               "<p class='hint'>提交到 /parse-blind 的 XML 指向 evil.dtd，数据会被带外传到 5033</p></div>")
    return render(content)


@app.route("/reset")
def reset():
    db = sqlite3.connect(DB)
    db.execute("UPDATE users SET flag1=NULL,flag2=NULL,flag3=NULL WHERE id=1")
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
