#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WishBox 心愿盒 - SSTI 模板注入靶场
端口: 5022

设计要点:
1. 看起来像正常的在线许愿平台
2. 用户输入被直接拼到 Jinja2 模板字符串里（SSTI 漏洞）
3. 3 枚 FLAG 难度递增:
   - ssti_math_2026: 确认 SSTI 存在（执行模板表达式）
   - ssti_config_2026: 读取 Flask 配置（SECRET_KEY）
   - ssti_rce_2026: RCE 读取环境变量
"""

import os
import html
from flask import Flask, request, render_template_string

app = Flask(__name__)

# FLAG 藏在三个地方，难度递增
FLAG_MATH = 'FLAG{ssti_math_2026}'
FLAG_CONFIG = 'FLAG{ssti_config_2026}'
FLAG_RCE = 'FLAG{ssti_rce_2026}'

# FLAG 2 藏在 Flask SECRET_KEY 里（通过 config 读取）
app.secret_key = FLAG_CONFIG

# FLAG 3 藏在环境变量里（需要 RCE 才能读到）
os.environ['WISHBOX_SECRET'] = FLAG_RCE

_collected = set()

PAGE_STYLE = '''
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }
  nav { background: #161b22; padding: 15px 30px; display: flex; gap: 25px; align-items: center; border-bottom: 2px solid #30363d; }
  nav a { color: #8b949e; text-decoration: none; font-size: 15px; }
  nav a:hover { color: #58a6ff; }
  .brand { font-size: 20px; font-weight: 700; color: #f0b429; margin-right: auto; }
  .container { max-width: 800px; margin: 30px auto; padding: 0 20px; }
  h1 { color: #f0b429; margin-bottom: 20px; }
  h2 { color: #8b949e; margin: 15px 0; }
  .card { background: #161b22; border-radius: 10px; padding: 25px; margin-bottom: 20px; border: 1px solid #30363d; }
  input, textarea, button { padding: 10px 15px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; border-radius: 5px; font-size: 14px; }
  input, textarea { width: 100%; margin-bottom: 10px; }
  button { background: #f0b429; border: none; cursor: pointer; color: #0d1117; font-weight: 600; }
  button:hover { background: #d99e1f; }
  .msg { padding: 15px; border-radius: 5px; margin-bottom: 15px; }
  .msg-info { background: #0c2233; border-left: 4px solid #58a6ff; }
  .msg-success { background: #122b1f; border-left: 4px solid #3fb950; }
  .msg-error { background: #2d1414; border-left: 4px solid #f85149; }
  .wish-card { background: linear-gradient(135deg, #1a1f35, #0d1117); border: 1px solid #30363d; border-radius: 12px; padding: 30px; margin: 15px 0; text-align: center; }
  .wish-card .wish-text { font-size: 18px; color: #e6edf3; margin: 15px 0; font-style: italic; }
  .wish-card .wish-deco { color: #f0b429; font-size: 24px; }
  .namecard { background: #161b22; border: 2px solid #f0b429; border-radius: 10px; padding: 25px; margin: 15px 0; }
  .namecard .nc-name { font-size: 22px; color: #f0b429; font-weight: 700; }
  .namecard .nc-title { font-size: 14px; color: #8b949e; margin-top: 5px; }
  .flag-banner { background: linear-gradient(135deg, #f0b429, #d4541f); padding: 20px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: 700; color: #0d1117; margin-top: 15px; letter-spacing: 1px; }
  footer { text-align: center; padding: 20px; color: #484f58; border-top: 1px solid #30363d; margin-top: 40px; }
</style>
'''

def render_page(title, body, nav_active=''):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} - WishBox</title>
{PAGE_STYLE}
</head>
<body>
<nav>
  <span class="brand">WishBox</span>
  <a href="/" style="{'color:#f0b429;font-weight:600' if nav_active=='home' else ''}">首页</a>
  <a href="/wish" style="{'color:#f0b429;font-weight:600' if nav_active=='wish' else ''}">写心愿</a>
  <a href="/namecard" style="{'color:#f0b429;font-weight:600' if nav_active=='namecard' else ''}">名片</a>
  <a href="/flags" style="{'color:#f0b429;font-weight:600' if nav_active=='flags' else ''}">FLAG</a>
</nav>
<div class="container">{body}</div>
<footer>WishBox 心愿盒 &copy; 2026 | 让每一个心愿都被看见</footer>
</body></html>'''


def check_flags(content, rendered):
    """检测用户是否通过 SSTI 读取到了 FLAG"""
    global _collected
    result = ''
    # FLAG 1: 确认 SSTI 存在 - 用户输入了模板语法且被引擎执行了
    # 判断标准：输入包含 {{ 或 {%，但渲染后这些语法消失了（被执行了）
    if 'math' not in _collected:
        if ('{{' in content or '{%' in content) and '{{' not in rendered and '{%' not in rendered:
            _collected.add('math')
            result += f'<div class="flag-banner">{FLAG_MATH}</div>'
    # FLAG 2: 读取了 config（输出包含 FLAG_CONFIG 的值）
    if 'config' not in _collected and FLAG_CONFIG in rendered:
        _collected.add('config')
        result += f'<div class="flag-banner">{FLAG_CONFIG}</div>'
    # FLAG 3: RCE 读取了环境变量（输出包含 FLAG_RCE 的值）
    if 'rce' not in _collected and FLAG_RCE in rendered:
        _collected.add('rce')
        result += f'<div class="flag-banner">{FLAG_RCE}</div>'
    return result


@app.route('/')
def home():
    body = '''<h1>欢迎来到 WishBox 心愿盒</h1>
    <div class="msg msg-info">在这里写下你的心愿，让它被世界看见</div>
    <div class="card">
        <h2>功能介绍</h2>
        <p> <strong>写心愿</strong> — 写下你的心愿，生成精美心愿卡</p>
        <p> <strong>名片</strong> — 生成你的专属电子名片</p>
    </div>
    <div class="card">
        <h2>今日精选心愿</h2>
        <div class="wish-card">
            <div class="wish-deco">"</div>
            <div class="wish-text">愿世界和平，代码无 bug</div>
            <div class="wish-deco">"</div>
        </div>
    </div>'''
    return render_page('首页', body, 'home')


@app.route('/wish', methods=['GET', 'POST'])
def wish():
    if request.method == 'POST':
        content = request.form.get('content', '')
        try:
            # 漏洞：用户输入直接拼到 Jinja2 模板字符串
            template = '''<div class="wish-card">
  <div class="wish-deco">"</div>
  <div class="wish-text">''' + content + '''</div>
  <div class="wish-deco">"</div>
</div>'''
            rendered = render_template_string(template)
            flag_html = check_flags(content, rendered)
            body = f'<h1>你的心愿卡</h1>{rendered}<div class="msg msg-success">心愿卡已生成！分享给朋友吧</div>{flag_html}'
        except Exception:
            body = '<h1>你的心愿卡</h1><div class="msg msg-error">心愿格式有误，请重新输入</div>'
        return render_page('心愿', body, 'wish')

    body = '''<h1>写心愿</h1>
    <div class="card">
        <form method="POST" action="/wish">
            <p><label>写下你的心愿</label><br>
            <textarea name="content" rows="4" placeholder="例如：祝我逢考必过"></textarea></p>
            <button type="submit">生成心愿卡</button>
        </form>
    </div>
    <div class="msg msg-info">你的心愿会显示在精美卡片上</div>'''
    return render_page('写心愿', body, 'wish')


@app.route('/namecard', methods=['GET', 'POST'])
def namecard():
    if request.method == 'POST':
        name = request.form.get('name', '')
        title = request.form.get('title', '')
        try:
            # 漏洞：用户输入直接拼到 Jinja2 模板字符串
            template = '''<div class="namecard">
  <div class="nc-name">''' + name + '''</div>
  <div class="nc-title">''' + title + '''</div>
</div>'''
            rendered = render_template_string(template)
            flag_html = check_flags(name + title, rendered)
            body = f'<h1>你的名片</h1>{rendered}{flag_html}'
        except Exception:
            body = '<h1>你的名片</h1><div class="msg msg-error">名片信息有误，请重新输入</div>'
        return render_page('名片', body, 'namecard')

    body = '''<h1>生成名片</h1>
    <div class="card">
        <form method="POST" action="/namecard">
            <p><label>姓名</label><br>
            <input type="text" name="name" placeholder="你的名字"></p>
            <p><label>头衔</label><br>
            <input type="text" name="title" placeholder="例如：全栈工程师"></p>
            <button type="submit">生成名片</button>
        </form>
    </div>
    <div class="msg msg-info">预览你的专属电子名片</div>'''
    return render_page('名片', body, 'namecard')


@app.route('/flags')
def flags():
    body = '<h1>FLAG 收集进度</h1>'
    if not _collected:
        body += '<div class="msg msg-info">还没有收集到任何 FLAG。这个网站有什么秘密？自己找找看</div>'
    else:
        body += f'<div class="msg msg-success">已收集 {len(_collected)}/3 枚 FLAG</div>'
        flag_map = {'math': FLAG_MATH, 'config': FLAG_CONFIG, 'rce': FLAG_RCE}
        for key in ['math', 'config', 'rce']:
            if key in _collected:
                body += f'<div class="flag-banner">{flag_map[key]}</div>'
            else:
                body += f'<div class="msg msg-info">??? 未解锁</div>'
    body += '<div class="card"><h2>提示</h2><p>这个网站有两个功能点可以输入文字</p><p>想想你的输入会怎么被处理</p><p>如果你学过 SQL 注入，这里有没有类似的东西？</p></div>'
    return render_page('FLAG', body, 'flags')


if __name__ == '__main__':
    print(f"[*] WishBox 心愿盒启动: http://127.0.0.1:5022")
    print(f"[*] 3 枚 FLAG 藏在不同深处")
    app.run(host='127.0.0.1', port=5022, debug=False)
