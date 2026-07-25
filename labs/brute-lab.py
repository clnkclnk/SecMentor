#!/usr/bin/env python3
"""
SecMentor P4.3 - 认证与爆破靶场
================================
功能：
  - Level 1: 弱密码爆破（无任何防护）
  - Level 2: 带速率限制的爆破（体验防御效果）
  - Level 3: Burp Intruder 手工爆破练习

运行方式：python sqli-lab.py（端口 5678）
         本文件与 SQLi 靶场共用同一个服务器，路由在 /brute/ 下
"""

import sqlite3
import json
import html
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

# ============ 全局状态 ============
DB_PATH = "C:\\Users\\clnk\\WorkBuddy\\2026-07-18-16-15-12\\labs\\sqli-lab-data.db"
passed = set()
login_attempts = {}  # IP -> {"count": int, "locked_until": float}
brute_log = []       # 爆破日志记录

# ============ 数据库连接 ============
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """确保数据库存在且包含用户表"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            secret TEXT
        )
    """)
    # 检查是否有数据
    existing = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        test_users = [
            ('admin', 'admin123', 'admin@target.com', 'admin', '管理员密码是 P@ssw0rd!'),
            ('zhangsan', 'zhang123', 'zhangsan@target.com', 'user', '张三的秘密'),
            ('lisi', '123456', 'lisi@target.com', 'user', '李四用了个超弱密码'),
            ('wangwu', 'Wangwu666!', 'wangwu@target.com', 'user', '王五的强密码'),
            ('alice', 'alice001', 'alice@target.com', 'user', 'Alice 的秘密'),
        ]
        cursor.executemany(
            'INSERT OR IGNORE INTO users (username, password, email, role, secret) VALUES (?,?,?,?,?)',
            test_users
        )
        conn.commit()
    conn.close()

# ============ 密码字典（Top 20 弱密码） ============
WORDLIST = [
    "123456", "password", "12345678", "qwerty", "123456789",
    "12345", "1234567", "1234567890", "iloveyou", "admin123",
    "welcome1", "monkey", "dragon", "master", "letmein",
    "login", "abc123", "football", "shadow", "sunshine"
]

# ============ 页面模板 ============
BASE_STYLE = """
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif; background:#0f0f1a; color:#e0e0e0; min-height:100vh; padding:24px; }
.container { max-width:900px; margin:0 auto; }
h1 { font-size:28px; margin-bottom:8px; color:#fff; }
.subtitle { color:#888; margin-bottom:32px; }
.card { background:#1a1a2e; border-radius:12px; padding:24px; margin-bottom:20px; border:1px solid #2a2a4a; }
.card h2 { font-size:18px; color:#a78bfa; margin-bottom:16px; }
.btn { display:inline-block; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:600; cursor:pointer; border:none; font-size:14px; }
.btn-primary { background:#667eea; color:#fff; }
.btn-primary:hover { background:#5a6fd6; }
.btn-success { background:#34d399; color:#fff; }
.btn-danger { background:#ef4444; color:#fff; }
.btn-disabled { background:#444; color:#888; cursor:not-allowed; }
input[type="text"], input[type="password"] { width:100%; max-width:300px; padding:10px 14px; background:#0f0f1a; border:1px solid #3a3a60; border-radius:8px; color:#fff; font-size:14px; margin:8px 0; }
input:focus { outline:none; border-color:#667eea; }
label { display:block; margin-bottom:4px; color:#aaa; font-size:13px; }
table { width:100%; border-collapse:collapse; margin-top:12px; }
th, td { padding:10px 12px; text-align:left; border-bottom:1px solid #2a2a4a; font-size:13px; }
th { color:#a78bfa; font-weight:600; }
.pass-banner { background:linear-gradient(90deg,#34d399,#10b981); color:#000; padding:12px 20px; border-radius:8px; font-weight:bold; margin:16px 0; text-align:center; }
.error-msg { background:rgba(239,68,68,0.15); color:#f87171; padding:12px 16px; border-radius:8px; border-left:4px solid #ef4444; margin:12px 0; }
.success-msg { background:rgba(52,211,153,0.15); color:#34d399; padding:12px 16px; border-radius:8px; border-left:4px solid #34d399; margin:12px 0; }
.warning-msg { background:rgba(251,191,36,0.15); color:#fbbf24; padding:12px 16px; border-radius:8px; border-left:4px solid #fbbf24; margin:12px 0; }
.sql-preview { background:#16163a; padding:12px 16px; border-radius:8px; font-family:'Consolas','Courier New',monospace; font-size:13px; color:#c084fc; margin:12px 0; overflow-x:auto; white-space:pre-wrap; word-break:break-all; }
.level-nav { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:20px; }
.level-btn { padding:8px 16px; border-radius:8px; border:1px solid #3a3a60; background:#1a1a2e; color:#aaa; cursor:pointer; font-size:13px; transition:all 0.2s; }
.level-btn.active { border-color:#667eea; color:#667eea; background:rgba(102,126,234,0.1); }
.level-btn.done { border-color:#34d399; color:#34d399; opacity:0.7; }
.level-btn.locked { opacity:0.4; cursor:not-allowed; }
.progress-bar { height:6px; background:#2a2a4a; border-radius:3px; margin:20px 0; overflow:hidden; }
.progress-fill { height:100%; background:linear-gradient(90deg,#667eea,#a78bfa); transition:width 0.5s; }
.stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin:16px 0; }
.stat-card { background:#12122a; padding:16px; border-radius:10px; text-align:center; border:1px solid #2a2a4a; }
.stat-value { font-size:28px; font-weight:bold; color:#667eea; }
.stat-label { font-size:12px; color:#888; margin-top:4px; }
.log-entry { font-family:monospace; font-size:12px; padding:6px 10px; border-bottom:1px solid #1a1a2e; display:flex; justify-content:space-between; align-items:center; }
.log-success { color:#34d399; }
.log-fail { color:#f87171; }
.log-warn { color:#fbbf24; }
code { background:#1a1a2e; padding:2px 6px; border-radius:4px; color:#c084fc; font-size:13px; }
</style>
"""

def build_page(title, content):
    nav_buttons = ""
    levels = [
        ("1", "Level 1 🔴 弱密码爆破", "brute", 1 in passed),
        ("2", "Level 2 🟡 速率限制", "rate-limit", 2 in passed),
        ("3", "Level 3 🟠 爆破日志分析", "analysis", 3 in passed),
    ]
    for lid, lname, lurl, done in levels:
        cls = "done" if done else "active" if lurl == title.split()[0].lower().replace("-","") or (title=="认证与爆破靶场" and lid=="1") else ""
        nav_buttons += f'<a href="/brute/{lurl}" class="level-btn {cls}">{lname}</a>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SecMentor — 认证与爆破靶场</title>{BASE_STYLE}</head><body>
<div class="container">
<div class="header" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
<h1>🔐 认证与爆破靶场</h1><span style="color:#667eea;font-weight:bold">P4.3 Auth & Brute Force</span></div>
<p class="subtitle">理解认证机制 · 体验爆破攻击 · 学习防御策略</p>
<div class="level-nav">{nav_buttons}</div>
{content}
<footer style="margin-top:32px;text-align:center;color:#555;font-size:12px">
SecMentor Lab — 仅用于安全学习，请勿用于非法用途</footer>
</div></body></html>"""


# ============ 页面渲染函数 ============
def render_brute_home():
    stats = f"""
    <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">{len(passed)}</div><div class="stat-label">已通过关卡</div></div>
        <div class="stat-card"><div class="stat-value">{len(brute_log)}</div><div class="stat-label">总尝试次数</div></div>
        <div class="stat-card"><div class="stat-value">{len(WORDLIST)}</div><div class="stat-label">字典条目数</div></div>
        <div class="stat-card"><div class="stat-value">5</div><div class="stat-label">目标用户数</div></div>
    </div>
    """
    tips = """
    <div class="card">
        <h2>📋 实验指南</h2>
        <table>
            <tr><th>关卡</th><th>内容</th><th>学习目标</th></tr>
            <tr><td>Level 1 🔴</td><td>弱密码爆破</td><td>体验无防护时爆破有多容易</td></tr>
            <tr><td>Level 2 🟡</td><td>速率限制</td><td>理解防御措施如何阻止自动化攻击</td></tr>
            <tr><td>Level 3 🟠</td><td>日志分析</td><td>学会从日志中发现爆破行为</td></tr>
        </table>
    </div>
    <div class="card">
        <h2>🎯 今日目标</h2>
        <p style="color:#aaa;line-height:1.8">
        1️⃣ 在 Level 1 中用<strong>字典攻击</strong>猜出 <code>lisi</code> 的密码（提示：他用了一个 Top 10 弱密码）<br>
        2️⃣ 在 Level 2 中体验<strong>速率限制</strong>的效果——快速连续尝试会被锁定<br>
        3️⃣ 在 Level 3 中查看<strong>爆破日志</strong>，识别出哪些是正常登录、哪些是攻击行为<br><br>
        💡 <strong>核心认知</strong>：爆破不是黑客电影里的炫技——它是最简单、最暴力的攻击方式，
        但正因为简单，所以<strong>极其常见</strong>。防御也不复杂：<strong>强密码 + 限制尝试次数 + MFA</strong>。
        </p>
    </div>
    """
    return build_page("认证与爆破靶场", stats + tips)


def render_level1():
    """Level 1: 无防护的弱密码爆破"""
    banner = '<div class="pass-banner">Level 1 通过! 你成功爆破出了 lisi 的密码！</div>' if 1 in passed else ''
    
    result_html = ""
    if 1 in passed:
        result_html = f"""
        <div class="success-msg">
        <strong>🎉 爆破成功！</strong><br>
        目标用户：<code>lisi</code> &nbsp;|&nbsp; 
        破解出的密码：<code style="color:#fbbf24;font-size:16px">123456</code><br><br>
        <strong>思考：</strong>这个密码在弱密码排行榜上排第 <strong>第 3 位</strong>！
        约 70% 的用户使用 Top 10000 密码之一。这就是为什么字典攻击如此有效。
        </div>"""

    return build_page("Level 1 弱密码爆破", f"""
    {banner}
    <div class="card">
        <h2>🔴 Level 1 — 弱密码爆破（无任何防护）</h2>
        <p style="color:#888;margin-bottom:16px">
        目标：用户 <code>lisi</code> 使用了一个非常弱的密码。<br>
        你的任务：用下面的登录框，<strong>手动或自动</strong>尝试猜出他的密码。<br>
        提示：密码就在最常见的 Top 20 弱密码列表里。
        </p>
        
        <form method="POST" action="/brute/login" style="margin:20px 0">
            <label>用户名</label>
            <input type="text" name="username" value="lisi" placeholder="输入用户名">
            <label>密码</label>
            <input type="password" name="password" placeholder="输入密码（试试常见弱密码）">
            <button type="submit" name="level" value="1" class="btn btn-primary" style="margin-top:12px">🔓 尝试登录</button>
        </form>
        
        {result_html}
        
        <div class="card" style="background:#12122a;margin-top:20px">
            <h2 style="font-size:15px;color:#888">📖 Top 20 弱密码参考（点击可快速填入）</h2>
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px">
            """ + "".join(f'<button onclick="document.querySelector(\'[name=password]\').value=\'{pw}\'" style="padding:4px 10px;border-radius:4px;border:1px solid #333;background:#1a1a2e;color:#aaa;cursor:pointer;font-size:12px">{pw}</button>' for pw in WORDLIST) + """
            </div>
        </div>
    </div>
    """)


def render_level2():
    """Level 2: 有速率限制的爆破"""
    banner = '<div class="pass-banner">Level 2 通过! 你体验了速率限制的防御效果！</div>' if 2 in passed else ''
    
    # 检查当前IP是否被锁定
    client_ip = "demo"  # 演示模式
    lock_info = login_attempts.get(client_ip, {})
    is_locked = lock_info.get("locked_until", 0) > time.time()
    remaining = int(lock_info.get("locked_until", 0) - time.time()) if is_locked else 0
    
    lock_warning = ""
    if is_locked:
        lock_warning = f'''<div id="lock-box" class="error-msg" style="position:relative;overflow:hidden">
            ⚠️ 账户已被临时锁定！
            <span id="countdown"><strong>{remaining}</strong></span> 秒后解锁...
            <div style="margin-top:8px;height:4px;background:#3a1a1a;border-radius:2px;overflow:hidden">
                <div id="lock-bar" style="height:100%;background:linear-gradient(90deg,#ef4444,#f87171);border-radius:2px;transition:width 1s linear;width:{max(0,remaining/30*100)}%"></div>
            </div>
        </div>
        <script>
        (function(){{
            var sec = {remaining};
            var box = document.getElementById('lock-box');
            var cd = document.getElementById('countdown');
            var bar = document.getElementById('lock-bar');
            var form = box.closest('.card').querySelector('form');
            if(form){{ form.style.opacity='0.4'; form.style.pointerEvents='none'; }}
            var timer = setInterval(function(){{
                sec--;
                if(sec <= 0){{
                    clearInterval(timer);
                    box.innerHTML = '✅ 锁定已解除！你现在可以继续尝试了。';
                    box.style.background='rgba(52,211,153,0.15)';
                    box.style.borderColor='#34d399';
                    box.style.color='#34d399';
                    if(form){{ form.style.opacity='1'; form.style.pointerEvents='auto'; }}
                    return;
                }}
                cd.innerHTML = '<strong>' + sec + '</strong>';
                bar.style.width = Math.max(0, sec/30*100) + '%';
            }}, 1000);
        }})();
        </script>'''
    
    result_html = ""
    if 2 in passed:
        result_html = """
        <div class="success-msg">
        <strong>✅ 速率限制体验完成！</strong><br>
        你应该已经感受到了：<br>
        • 连续失败几次后，账户被<strong>临时锁定</strong><br>
        • 锁定期间无法继续尝试<br>
        • 这就是为什么爆破攻击在实际中往往需要<strong>很长时间</strong><br><br>
        <strong>现实中的防御：</strong>大多数网站会在 5-10 次失败后锁定 15-30 分钟。
        </div>"""

    return build_page("Level 2 速率限制", f"""
    {banner}
    <div class="card">
        <h2>🟡 Level 2 — 速率限制（有防护的爆破）</h2>
        <p style="color:#888;margin-bottom:16px">
        这次登录功能有<strong>速率限制</strong>：<br>
        • 同一 IP 连续失败 <strong>3 次</strong> → 锁定 <strong>30 秒</strong><br>
        • 锁定期间所有请求都会被拒绝<br><br>
        你的任务：快速连续输入错误密码，体验被锁定的感觉。然后用正确密码登录。
        </p>
        
        {lock_warning}
        
        <form method="POST" action="/brute/login" style="margin:20px 0">
            <label>用户名</label>
            <input type="text" name="username" value="admin" placeholder="输入用户名">
            <label>密码</label>
            <input type="password" name="password" placeholder="正确密码是 admin123">
            <button type="submit" name="level" value="2" class="btn btn-primary" style="margin-top:12px">🔓 尝试登录</button>
        </form>
        
        {result_html}
        
        <div class="warning-msg" style="margin-top:16px">
        <strong>💡 提示：</strong>先故意输错 3 次（比如输 111、222、333），观察锁定提示。等 30 秒后再用正确密码 <code>admin123</code> 登录。
        </div>
    </div>
    """)


def render_level3():
    """Level 3: 爆破日志分析"""
    banner = '<div class="pass-banner">Level 3 通过! 你能识别爆破行为了！</div>' if 3 in passed else ''
    
    # 生成模拟日志（如果没有真实日志的话）
    log_entries = brute_log if brute_log else generate_demo_logs()
    
    logs_html = ""
    for entry in log_entries[-30:]:  # 显示最近30条
        ts = entry.get("time", "")
        user = entry.get("user", "")
        pwd_mask = entry.get("pwd_mask", "")
        ip = entry.get("ip", "")
        status = entry.get("status", "")
        css_class = "log-success" if status == "SUCCESS" else ("log-warn" if "LOCKED" in status else "log-fail")
        logs_html += f'<div class="log-entry {css_class}"><span>[{ts}] {user}@{ip} → {pwd_mask} → {status}</span></div>'
    
    analysis_btn = ""
    if 3 not in passed and len(brute_log) >= 5:
        analysis_btn = '<form method="GET" action="/brute/analyze" style="margin-top:16px"><button class="btn btn-success">🔍 分析这些日志</button></form>'
    
    result_html = ""
    if 3 in passed:
        result_html = """
        <div class="success-msg">
        <strong>🎉 日志分析完成！</strong><br>
        你学会了识别爆破行为的几个关键特征：<br>
        ✓ <strong>高频次</strong>：短时间内大量失败请求<br>
        ✓ <strong>单用户聚焦</strong>：只针对一个用户名反复尝试<br>
        ✓ <strong>固定来源</strong>：来自同一 IP 地址<br>
        ✓ <strong>最终成功</strong>：大量失败后突然成功 = 密码被破<br>
        </div>"""

    return build_page("Level 3 日志分析", f"""
    {banner}
    <div class="card">
        <h2>🟠 Level 3 — 爆破日志分析</h2>
        <p style="color:#888;margin-bottom:16px">
        作为安全工程师，你需要能从日志中<strong>识别出爆破行为</strong>。<br>
        下面是系统的登录日志（包含你之前的所有尝试）。
        </p>
        
        <div class="card" style="background:#0a0a1a;max-height:400px;overflow-y:auto">
        <div style="padding:8px;font-size:12px;color:#666;border-bottom:1px solid #2a2a4a">
        时间 | 用户@IP | 密码 | 结果</div>
        {logs_html}
        </div>
        
        {analysis_btn}
        {result_html}
        
        <div class="card" style="background:#12122a;margin-top:16px">
            <h2 style="font-size:15px;color:#888">🔍 爆破行为识别要点</h2>
            <table style="font-size:13px">
                <tr><th>特征</th><th>正常登录</th><th>爆破攻击</th></tr>
                <tr><td>频率</td><td>每天几次</td><td style="color:#f87171">每分钟几十~几百次</td></tr>
                <tr><td>用户名</td><td>各种用户</td><td style="color:#f87171">固定一个（如admin）</td></tr>
                <tr><td>密码变化</td><td>每次相同/偶尔错</td><td style="color:#f87171">每次都不同</td></tr>
                <tr><td>来源IP</td><td>分散各地</td><td style="color:#f87171">单一IP或同类段</td></tr>
                <tr><td>结果模式</td><td>大部分成功</td><td style="color:#f87171">大量失败+突然成功</td></tr>
            </table>
        </div>
    </div>
    """)


def generate_demo_logs():
    """生成演示用的爆破日志"""
    demo = []
    base_time = time.time() - 300  # 5分钟前
    for i in range(20):
        t = base_time + i * 2  # 每2秒一次
        pwd = WORDLIST[i] if i < len(WORDLIST) else f"guess_{i}"
        success = (pwd == "123456")  # lisi的密码
        demo.append({
            "time": datetime.fromtimestamp(t).strftime("%H:%M:%S"),
            "user": "lisi",
            "pwd_mask": "*" * len(pwd),
            "ip": "192.168.1.100",
            "status": "SUCCESS" if success else "FAILED"
        })
    return demo


# ============ 登录处理逻辑 ============
def handle_login(params, level):
    """处理登录请求，根据关卡应用不同的安全策略"""
    username = params.get("username", [""])[0]
    password = params.get("password", [""])[0]
    client_ip = "127.0.0.1"  # 简化处理
    
    # 记录日志
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "user": username,
        "pwd_mask": "*" * len(password),
        "ip": client_ip,
        "status": ""
    }
    
    # ===== Level 2: 速率限制 =====
    if level == 2:
        now = time.time()
        info = login_attempts.setdefault(client_ip, {"count": 0, "locked_until": 0})
        
        # 检查是否被锁定
        if info["locked_until"] > now:
            log_entry["status"] = "LOCKED"
            brute_log.append(log_entry)
            return f'<div class="error-msg">⚠️ 账户已被锁定！请在 <strong>{int(info["locked_until"] - now)}</strong> 秒后重试。</div>', False
        
        # 尝试登录
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            log_entry["status"] = "SUCCESS"
            brute_log.append(log_entry)
            login_attempts[client_ip] = {"count": 0, "locked_until": 0}  # 成功则重置
            if 2 not in passed:
                passed.add(2)
            return f'''<div class="success-msg">✅ 登录成功！欢迎回来，<strong>{html.escape(user['username'])}</strong>！
                <table style="margin-top:12px"><tr><td>角色</td><td>{html.escape(user['role'])}</td></tr>
                <tr><td>邮箱</td><td>{html.escape(user['email'])}</td></tr></table>
                </div>''', True
        else:
            # 失败计数
            info["count"] += 1
            log_entry["status"] = f"FAILED ({info['count']}/3)"
            brute_log.append(log_entry)
            
            if info["count"] >= 3:
                info["locked_until"] = now + 30  # 锁定30秒
                return f'<div class="error-msg">❌ 密码错误！<br><strong>⚠️ 已连续失败 3 次，账户锁定 30 秒！</strong></div>', False
            
            return f'<div class="error-msg">❌ 密码错误！已失败 {info["count"]}/3 次</div>', False
    
    # ===== Level 1: 无任何防护（直接查询） =====
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        log_entry["status"] = "SUCCESS"
        brute_log.append(log_entry)
        
        # Level 1 特殊条件：以 lisi 身份登录
        if username == "lisi" and 1 not in passed:
            passed.add(1)
        
        extra = ""
        if username == "lisi":
            extra = '''<div class="pass-banner">Level 1 通过! 你成功爆破出了 lisi 的密码：123456</div>'''
        
        return f'''{extra}<div class="success-msg">✅ 登录成功！欢迎，<strong>{html.escape(user['username'])}</strong>！
            <table style="margin-top:12px"><tr><td>角色</td><td>{html.escape(user['role'])}</td></tr>
            <tr><td>邮箱</td><td>{html.escape(user['email'])}</td></tr>
            <tr><td>秘密</td><td style="color:#f87171">{html.escape(user['secret'])}</td></tr></table>
            </div>''', True
    else:
        log_entry["status"] = "FAILED"
        brute_log.append(log_entry)
        return '<div class="error-msg">❌ 登录失败：用户名或密码错误</div>', False


# ============ HTTP 请求处理器 ============
class BruteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/brute/" or path == "/brute":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_brute_home().encode())
            
        elif path == "/brute/brute":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_level1().encode())
            
        elif path == "/brute/rate-limit":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_level2().encode())
            
        elif path == "/brute/analysis":
            if 3 not in passed:
                passed.add(3)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_level3().encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/brute/login":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            params = parse_qs(body)
            
            level = int(params.get("level", ["1"])[0])
            result_html, success = handle_login(params, level)
            
            # 根据来源返回对应页面
            referer = self.headers.get("Referer", "")
            if "rate-limit" in referer:
                page = render_level2()
            elif "analysis" in referer:
                page = render_level3()
            else:
                page = render_level1()
            
            # 把登录结果注入页面（简单替换）
            page = page.replace('<form method="POST"', result_html + '<form method="POST"')
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 静默 HTTP 日志


# ============ 启动服务器 ============
if __name__ == "__main__":
    init_db()
    
    # 复用 5678 端口（和 SQLi 靶场共享）
    server = HTTPServer(("127.0.0.1", 5678), BruteHandler)
    print("=" * 50)
    print("  SecMentor 认证与爆破靶场已启动")
    print("  URL: http://127.0.0.1:5678/brute/")
    print("  Level 1: http://127.0.0.1:5678/brute/brute")
    print("  Level 2: http://127.0.0.1:5678/rate-limit")
    print("  Level 3: http://127.0.0.1:5678/brute/analysis")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 服务器已停止")
        server.server_close()
