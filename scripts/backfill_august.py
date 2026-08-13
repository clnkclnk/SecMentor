# -*- coding: utf-8 -*-
"""回填 8/5-8/13 进阶学习记录到 progress.json + events/2026-08.jsonl"""
import json
import os

BASE = r"C:\Users\clnk\WorkBuddy\2026-07-18-16-15-12"
PROGRESS = os.path.join(BASE, "learner", "progress.json")
EVENTS = os.path.join(BASE, "learner", "events", "2026-08.jsonl")

# 8 月进阶事件（按时间排序，旧的在前）
new_events = [
    {"type": "advanced_topic_passed", "ts": "2026-08-05T21:30:00+08:00", "data": {"topic": "sqli-advanced", "lab": "TechShop", "flags": "3/3", "summary": "SQL注入进阶 TechShop 3/3：搜索报错触发 + UNION 偷 secrets + 登录绕过"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-06T20:52:00+08:00", "data": {"topic": "blind-sqli", "lab": "BlindBox", "flags": "2/3", "summary": "盲注进阶 BlindBox：布尔盲注(页面差异) + 时间盲注(响应延迟) 原理完全掌握，第三关跳过"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-07T22:31:00+08:00", "data": {"topic": "ssti", "lab": "WishBox", "flags": "3/3", "summary": "SSTI 模板注入 WishBox 3/3：{{7*7}}确认 → {{config}}读配置 → Python对象攀爬RCE（__builtins__路径）"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-09T20:00:00+08:00", "data": {"topic": "ssti-advanced", "lab": "MailForge", "flags": "3/3", "summary": "SSTI 进阶 MailForge 3/3：直接SSTI + 二次注入 + WAF绕过(attr过滤器/外部传参)"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-09T21:03:00+08:00", "data": {"topic": "race-conditions", "lab": "FlashSale", "flags": "3/3", "summary": "条件竞争 FlashSale 3/3：TOCTOU 检查-执行间隙并发请求（积分负数/限购多件/超卖）"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-10T19:00:00+08:00", "data": {"topic": "race-advanced", "lab": "GameVault", "flags": "4/4", "summary": "条件竞争进阶 GameVault 4/4：100ms窗口需Python并发脚本，三种模式(TOCTOU/Lost Update/原子操作)"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-10T20:30:00+08:00", "data": {"topic": "ssrf", "lab": "LinkPeek", "flags": "3/3", "summary": "SSRF LinkPeek 3/3：内网探测 + 云元数据169.254 + 黑名单绕过(localtest.me)"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-10T21:58:00+08:00", "data": {"topic": "ssrf-advanced", "lab": "NetPulse", "flags": "4/4", "summary": "SSRF 进阶 NetPulse 4/4：逻辑链（探内网→file读文件→密码打Redis→绕黑名单）"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-11T19:00:00+08:00", "data": {"topic": "xss-advanced", "lab": "Verse", "flags": "4/4", "summary": "XSS 进阶 Verse 4/4：反射 + 存储绕script + 存储绕事件 + DOM型(hash+innerHTML)"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-12T22:28:00+08:00", "data": {"topic": "xss-relearn", "lab": "Verse", "flags": "4/4", "summary": "XSS 五块原理重学（本质/三种类型/危害/过滤绕过/防御）+ 实战推断过滤方法论"}},
    {"type": "advanced_topic_passed", "ts": "2026-08-13T19:00:00+08:00", "data": {"topic": "csrf", "lab": "BankVault+Evil", "flags": "4/4", "summary": "CSRF 双站点靶场 4/4：GET转账img + POST表单自动提交 + no-referrer绕Referer + 假token；完成攻击者侦查流程"}},
    {"type": "advanced_topic_started", "ts": "2026-08-13T21:35:00+08:00", "data": {"topic": "file-upload-advanced", "summary": "文件上传漏洞学习开始：本质（webshell RCE）+ 为什么最高危"}},
]

# ---------- 1. 追加 events jsonl ----------
with open(EVENTS, "a", encoding="utf-8") as f:
    for e in new_events:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print("events/2026-08.jsonl 已追加", len(new_events), "条")

# ---------- 2. 更新 progress.json ----------
with open(PROGRESS, "r", encoding="utf-8") as f:
    prog = json.load(f)

# 新事件摘要（recent_events 用的 summary 字段）
new_summaries = [
    {"type": "advanced_topic_passed", "ts": "2026-08-13T19:00:00+08:00",
     "summary": "CSRF 双站点靶场 4/4：GET转账img + POST表单自动提交 + no-referrer绕过 + 假token。完成攻击者侦查流程（F12/Python测Referer与token）。+进阶，P0~P10后第7个进阶专题"},
    {"type": "advanced_topic_passed", "ts": "2026-08-12T22:28:00+08:00",
     "summary": "XSS 五块原理重学完成 + Verse 4/4 再验证。掌握反射/存储/DOM识别、六种过滤绕过、防御三层。"},
    {"type": "advanced_topic_passed", "ts": "2026-08-11T19:00:00+08:00",
     "summary": "XSS 进阶 Verse 4/4：反射 + 存储绕script + 存储绕事件 + DOM型。SSRF 重学四块原理。"},
    {"type": "advanced_topic_passed", "ts": "2026-08-10T21:58:00+08:00",
     "summary": "SSRF 进阶 NetPulse 4/4 逻辑链 + LinkPeek 3/3 + GameVault 条件竞争 4/4。生成学习方向全景图（32方向）。"},
    {"type": "advanced_topic_passed", "ts": "2026-08-09T21:03:00+08:00",
     "summary": "SSTI 进阶 MailForge 3/3（含WAF绕过）+ 条件竞争 FlashSale 3/3。"},
    {"type": "advanced_topic_passed", "ts": "2026-08-07T22:31:00+08:00",
     "summary": "SSTI WishBox 3/3：{{7*7}}→{{config}}→Python对象攀爬RCE。盲注第三关跳过（原理已掌握）。"},
    {"type": "advanced_topic_passed", "ts": "2026-08-06T20:52:00+08:00",
     "summary": "盲注进阶 BlindBox：布尔盲注 + 时间盲注原理掌握。修复 progress.json 完整性。"},
    {"type": "advanced_topic_passed", "ts": "2026-08-05T21:30:00+08:00",
     "summary": "SQL注入进阶 TechShop 3/3：UNION偷secrets + 登录绕过。"},
    {"type": "advanced_topic_started", "ts": "2026-08-03T20:29:00+08:00",
     "summary": "货拉拉 SRC 启动：读测试规范 + Burp 配置 + 信息收集（发现 watch-dog/static/mdap-app 等子域名）。同步 SecMentor 框架到上游。"},
]

# recent_events 前插新事件，保持 20 条
old_recent = prog.get("recent_events", [])
# 去掉最旧的（P0~P2 时代的）以腾空间：保留 2026-07-20 之后的事件 + 新事件
old_recent = [e for e in old_recent if e.get("ts", "") >= "2026-07-20T20:30:00"]
prog["recent_events"] = new_summaries + old_recent
prog["recent_events"] = prog["recent_events"][:20]

# streak：8/9-8/13 连续 5 天
prog["streak"] = {"days": 5, "last_study_date": "2026-08-13"}

# path 记录进阶方向
prog["path"]["advanced_topics"] = [
    "sqli-advanced", "blind-sqli", "ssti", "ssti-advanced", "race-conditions",
    "race-advanced", "ssrf", "ssrf-advanced", "xss-advanced", "csrf"
]
prog["path"]["current_advanced"] = "file-upload-advanced"

# updated_at
prog["updated_at"] = "2026-08-13T21:47:00+08:00"

with open(PROGRESS, "w", encoding="utf-8") as f:
    json.dump(prog, f, ensure_ascii=False, indent=2)

print("progress.json 已更新（recent_events=%d 条, streak=%s）" % (len(prog["recent_events"]), prog["streak"]["last_study_date"]))
