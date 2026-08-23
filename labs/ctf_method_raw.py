# -*- coding: utf-8 -*-
"""Raw socket CTFB 探测：确保方法名 CTFB 字面传"""
import socket
import re

host = 'challenge-90c29f8090155cad.sandbox.ctfhub.com'
port = 10800


def raw_request(method, path='/index.php'):
    s = socket.create_connection((host, port), timeout=12)
    s.settimeout(12)
    req = (
        f'{method} {path} HTTP/1.1\r\n'
        f'Host: {host}:10800\r\n'
        'Connection: close\r\n'
        'User-Agent: Mozilla/5.0\r\n'
        'Accept: */*\r\n\r\n'
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
        return None
    s.close()
    return resp


tests = [
    'CTFB',
    'CTF',  # 对照
    'POST',  # 对照
    'GET',
    'ctfb',  # 小写
]

for m in tests:
    r = raw_request(m)
    if r is None:
        print(f'{m}: 超时')
        continue
    head, _, body = r.partition(b'\r\n\r\n')
    first = head.split(b'\r\n')[0].decode(errors='ignore') if head else '(no)'
    flags = re.findall(rb'ctfhub\{[^}]+\}|flag\{[^}]+\}|FLAG\{[^}]+\}', body, re.I)
    print(f'{m:<6} {first} len={len(body)} flags={flags[:1] if flags else "无"}')
    if flags:
        print(f'  🏁 完整: {body.decode(errors="ignore")}')
    elif b'CTF' in body or b'flag' in body:
        print(f'  包含 CTF/flag: {body[:300].decode(errors="ignore")}')
