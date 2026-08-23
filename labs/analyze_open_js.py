# -*- coding: utf-8 -*-
"""分析 open.huolala.cn 的 Vue 主 JS：找路由和 API 接口"""
import requests, re

r = requests.get('https://open.huolala.cn/js/main.9cc21fe.js', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
print('大小:', len(r.text))

routes = sorted(set(re.findall(r'path:\s*["\']([^"\']+)["\']', r.text)))
print('=== Vue 路由 ===')
for x in routes[:40]:
    print(' ', x)

print()
apis = sorted(set(re.findall(r'["\'](/[a-zA-Z0-9_/-]{3,60})["\']', r.text)))
print('=== 路径引用 ===')
for a in apis[:40]:
    print(' ', a)

print()
doms = sorted(set(re.findall(r'https?://[a-zA-Z0-9.-]+', r.text)))
print('=== 域名 ===')
for d in doms[:20]:
    print(' ', d)
