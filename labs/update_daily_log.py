# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path('learner')

# ===== 1. daily-log.md：只追加 8/16-8/24 =====
dl = (BASE / 'daily-log.md').read_text(encoding='utf-8')
append = """
## 2026-08-16 · 货拉拉 SRC 实战重启
- 休息两天后重启，从「没思路」找抓手：确认 SRC 工具链（Burp+F12+Python+AI 副驾）
- 货拉拉 SRC 资产大扩展：点菜单抓真实流量，Filter=huolala.cn 看 Burp history
- 新发现子域/主域：open.huolala.cn（开放平台）、sign-sdk-v.huolala.cn（签名 SDK）、dappweb-api.huolala.cn、www.hllep.com（企业版独立域）等
- mdap-app/website/latestApp 测试：appId 枚举发现可跨业务线访问（司机端数据），但 hint 哥哥说「内部版本+解包逆向」才算 — 该发现不构成有效漏洞
- 学习教训：异常 ≠ 漏洞，必须验证「实际危害」（数据敏感度 × 访问控制缺陷）

## 2026-08-17 · 实战续 + 顿悟
- 货拉拉 SRC 续：open.huolala.cn 开放平台 — JS 路由分析发现完整接口地图（/ajax/developer/check/account = 手机号枚举候选）
- 创建应用 No.1793「测试」[沙箱]：状态待审核，等密钥（直到 8/24 仍未过）
- 顿悟：「脚本就是我的手」— 脚本直接发 HTTP 请求，服务器只认请求不认网页（攻击者不必用网页 UI）

## 2026-08-18 ~ 2026-08-19 · 休息

## 2026-08-20 · 重新开始 SRC
- 没思路 + 刷抖音偷懒，用户主动回来重启
- 资产再次确认：open.huolala.cn 开放平台 + www.hllep.com 企业版
- 沙箱应用仍未审核（催也无用）

## 2026-08-21 · 沙箱+合并 + 状态
- 货拉拉应用 No.1793「测试」沙箱仍在待审核
- 主动以「合并」动作尝试构造攻击面：拼菜单抓取 /open.huolala.cn 控制台 → 找到完整路由/API 列表，失败
- 当天完整资产地图 16+ 子域

## 2026-08-22 ~ 2026-08-23 · LFI + CTF 实战
- LFI HCTF WarmUp 实战解题：发现「源文件提示 → include源码 → 白名单 + mb_substr 截断 ? → 路径穿越」完整链
  - 最终 payload：file=source.php?/../../../../ffffllllaaaagggg（打 /source.php 不是 /，flag 文件无 .php 后缀）
  - FLAG: CTF2{7d4d75fc-f792-4839-bf4a-4b8a34d8ba10}
- CTFHub HTTP Method 题：环境实例 bug（服务器不返回 flag，所有 200 是「提示页」），需要重置实例
- CTFHub 推荐顺序：CTFHub 技能树（按漏洞分类，最贴合已学）> BUUCTF（经典真题）> NSSCTF（新题）

## 2026-08-24 · CTFHub 基础认证
- CTFHub 基础认证题：HTTP Basic Auth 401 + WWW-Authenticate: Basic realm='Do u know admin ?'
  - 第一次爆破：admin/123456 看似通过（200+flag），但提交失败 → 彩蛋 flag（环境到期提示页里的 ctfhub{b644d27...}）
  - **用户怀疑 123456 一直是对的** → 严谨反思 Python 代码 bug
  - 重置环境 → 新实例 challenge-72c419619eb1cc4c → admin/dragon 命中
  - **FLAG: ctfhub{361a79a93e0167a91223334f}**
- 重要教训：环境到期陷阱（所有请求返回提示页+彩蛋 flag）→ 正确流程必须先确认环境状态 + 判断 flag 排除彩蛋/占位
- 工具：labs/basic_auth_brute.py + labs/brute_rigorous.py（严谨版）
- 用户反馈三条（直接采纳）：① 不用老是图省事推 Python（除非他主动问）② 不要评论时间/进度 ③ 教学讲清「为什么」不甩代码

---
"""
if '2026-08-16' not in dl:
    (BASE / 'daily-log.md').write_text(dl + append, encoding='utf-8')
    print('daily-log.md 已追加 8/16-8/24')
else:
    print('daily-log.md 已有 8/16 内容')
