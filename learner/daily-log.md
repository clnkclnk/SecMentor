# SecMentor 学习日志（每日记录）

> 自动汇总于 `learner/daily-log.md`，每天学习后更新并推送
> 总进度：P0~P10 全部通关（745 分）→ 进阶漏洞专题学习中

---

## 2026-08-13 · 知识总结手册补全（晚间）
- 用户反馈：GitHub 上看不到最近学习状态 → 要求进度必须同步 GitHub
- **回填 8/3-8/13 记录并推送**（commit `0b15602`）：新建 `learner/daily-log.md`（人类可读每日日志）+ 追加 13 条 events + 更新 progress.json + 回填脚本
- **知识总结手册补全**：从 P0~P9 扩展到 P0~P10 + 进阶 7 专题（新增"十、进阶专题"覆盖 SQL注入进阶/SSTI/条件竞争/SSRF/XSS/CSRF/SRC实战；"十一、更新后锚点表"含 17 个漏洞的亲手证据）
- 把"学习记录必须同步 learner/ 并 push"写入 MEMORY.md 硬性约定

## 2026-08-13 · CSRF 完成 + 文件上传开始
- **CSRF 双站点靶场 4/4**：BankVault 银行（5029）+ 攻击者站点（5030）
  - FLAG1 GET 转账无防护（`<img>` 触发）
  - FLAG2 POST 改密码无防护（表单自动提交）
  - FLAG3 改邮箱 Referer 检查但空 Referer 放行（no-referrer 绕过）
  - FLAG4 发帖 token 只检查存在不验证值（假 token 绕过）
- **核心理解**：浏览器"请求发往哪就自动带哪的 cookie" + 服务器不验证请求来源 = 信任盲区
- **攻击者侦查流程**：F12 看请求/载荷标签判断 GET-POST/token，Python requests 测 Referer 和 token 校验
- **工具链**：学会 F12 Copy as cURL、Git Bash；踩坑 cmd/PowerShell curl 别名与续行符
- 开始**文件上传**专题（第一块：本质 + 为什么最高危）

## 2026-08-12 · 重新学 XSS（原理五块）+ CSRF 原理
- **XSS 五块原理重学**（当没学过，详细版）：本质（数据与代码混淆）→ 三种类型（反射/存储/DOM）→ 危害五级 → 过滤绕过六手段 → 防御三层
- **Verse 靶场 4/4 再验证**：反射/存储绕script/存储绕事件/DOM 全通关
- 实战洞察：靶场有过滤提示但真实环境没有 → 教"看响应推断过滤"方法论
- **CSRF 原理开始**：本质（借身份发请求）、恶意页面三种载体（img/表单自动提交/伪装按钮）

## 2026-08-11 · XSS 进阶靶场 Verse 4/4 + 重新学 SSRF
- **XSS 进阶靶场 Verse（5028）4/4**：
  - FLAG1 反射型（搜索无过滤）→ FLAG2 存储型（`<img onerror>` 绕 script）
  - FLAG3 存储型（`javascript:` 伪协议绕事件）→ FLAG4 DOM 型（URL `#` + innerHTML）
- 学会判断"反射/存储/DOM"：输入位置 + 是否持久；绕过看"试了之后被删了什么"
- 教学点：`alert()` 同步阻塞 setTimeout → 用 `document.title` 不阻塞验证
- **重新学 SSRF**（当没学过）：本质 → 三种利用形态 → 信息串联攻击链 → 防御
- Git push commit `3501894`（13 个新文件）

## 2026-08-10 · 条件竞争进阶 + SSRF 两个靶场 + 学习全景图
- **GameVault 条件竞争靶场（5025）4/4**：100ms 窗口必须 Python 并发脚本
  - 三种竞争模式：TOCTOU 检查-执行 / Lost Update 读改写 / 原子操作（安全）
  - 学会写 threading 并发脚本、区分能打与不能打的
- **LinkPeek SSRF 靶场（5026）3/3**：内网探测 → 云元数据 → 黑名单绕过（localtest.me）
- **NetPulse SSRF 进阶靶场（5027）建好验证通过**：4 个 FLAG 逻辑链（探内网→读文件→打内网→绕黑名单）
- 生成 **学习方向全景图**（32 个方向 + 5 项贯穿能力，A~F 六类）

## 2026-08-09 · SSTI 进阶 + 条件竞争入门
- **MailForge SSTI 进阶靶场（5023）3/3**：直接 SSTI → 二次注入 → WAF 绕过（attr 过滤器/外部传参）
- 理解 Python 对象模型攀爬链：`__class__.__mro__.__subclasses__().__init__.__globals__`
- **FlashSale 条件竞争靶场（5024）3/3**：TOCTOU 检查-执行间隙并发请求
- 条件竞争核心：不是手速快，是多个请求挤进"检查-执行"窗口

## 2026-08-07 · SSTI 模板注入（WishBox 3/3）
- **SSTI 原理**：输入被模板引擎当代码执行（同属注入类，比 SQL 注入更危险，可直接 RCE）
- **WishBox 靶场（5022）3/3**：`{{7*7}}` 确认 → `{{config}}` 读配置 → Python 对象攀爬 RCE
- 关键发现：Python 3.13 的 warnings 不 import os → 用 `__builtins__['__import__']('os')`
- 盲注第三关确认与登录框无区别，跳过（布尔盲注 + 时间盲注原理已完全掌握）

## 2026-08-06 · 盲注进阶（BlindBox）
- **盲注原理**：真实环境关闭报错/不回显 → 布尔盲注（页面差异当信号）+ 时间盲注（响应延迟当信号）
- **BlindBox 盲盒商城（5021）**：登录框布尔盲注 + 订单查询时间盲注通关
- 二分查找优化：线性 26 次 → 二分 5 次；`unicode(substr())` 逐字符偷数据
- 修复 progress.json 数据完整性（745 分 = Level 3 入室弟子）

## 2026-08-05 · SQL 注入进阶（TechShop 3/3）
- **TechShop 商城靶场（5020）3/3**：搜索报错触发 → UNION 偷 secrets 表 → 登录绕过
- 理解：`%` 通配符 vs `=` 精确匹配、`--` 注释、UNION 列数对齐
- 方法论：查表名 → 排优先级 → 查结构 → 查数据（4 步）

## 2026-08-04 · 货拉拉 SRC 侦察 + 教学方式确立
- **教学方式确立**（重要）：绝不喂答案、不做过家家靶场；真实感多漏洞靶场 + 用户自己发现 + 教练讲透 WHY
- **货拉拉 SRC 侦察**：eapi/api.map 靠 Burp history 抓流量；ltl.huolala.cn 可交互深挖

## 2026-08-03 · 框架同步 + 货拉拉 SRC 启动
- **同步 SecMentor 框架到上游 yhy0 最新版**：git remote upstream + fetch，commit `9d3c6d0`
- 踩坑：沙盒 Temp 目录不跨命令持久；Git 连 GitHub 需 `-c http.proxy=` 直连
- **货拉拉 SRC 启动**：读测试规范（1 积分=10 元；严重 5000-8000 元）；Burp 代理配置 + 信息收集
  - 发现子域名：watch-dog/static/mdap-app/api.map/eapi 等
  - 发现接口：/api/v2/collect、/schema/*、/website/latestApp?appId=

---
## 2026-07-18 · SecMentor 启动（第一天）
- **摸底评估**：计算机应用技术专科/专升本上岸，C/Python 入门级，零安全基础
- **P0 通关**：授权边界（伦理）+ 学习循环
- **P1 通关**：网络与计算机基础（IP/端口/DNS/TCP/HTTP/进程文件权限）— 145 分
- 安装 WSL2 中

## 2026-07-19 · Linux 环境搭建
- **P2**：WSL2 安装配置，准备 Ubuntu 终端环境

## 2026-07-20 · Linux 与 Web 前置
- **P2 通关**：Linux shell 命令（ls/pwd/cd/cat/curl）+ Docker 隔离环境
- **P3 开始**：HTTP 请求响应、Cookie/Session 登录态机制

## 2026-07-21 · Web 请求模型
- **P3**：客户端-服务端模型（POST Body → 302 → Set-Cookie 全流程）

## 2026-07-22 · Burp 与 HTTPS
- **P3**：Burp 代理抓包（拦截/修改/Forward）
- **P3**：HTTPS/TLS 证书与中间人原理 — 345 分

## 2026-07-23 · DevTools + XSS 基础
- **P3 通关**：Web 浏览器工具 + F12 DevTools
- **P4 XSS 通关**：反射型/存储型/DOM型/Cookie 窃取 4 关 — 395 分

## 2026-07-24 · SQL 注入基础
- **P4 SQL 注入通关**：报错信号 → 逻辑运算 → 登录绕过 → UNION 偷数据 → 参数化防御 — 420 分

## 2026-07-25 · 认证/CSRF/文件上传
- **P4**：认证基础/弱口令/爆破 + Burp Intruder
- **P4 CSRF 通关**：构造 CSRF 攻击 HTML + Token 防护验证 — 445 分
- **P4 文件上传通关**：上传 shell.py 落地 WebShell 触发 RCE — 470 分
- **P5**：文件下载 + 路径穿越（`..\..` 穿越读文件）— 495 分

## 2026-07-26 · 文件类漏洞全通关
- **P5 通关**：文件上传/文件下载/文件包含（LFI）+ 路径穿越，5 个文件类漏洞 — 520 分
- **P6 SSRF 开始**

## 2026-07-27 · SSRF
- **P6 SSRF 通关**：借服务器身份访问内网资源 + 泄露云密钥 — 545 分

## 2026-07-28 · XXE 原理
- **P6 XXE**：XML 外部实体 = 路径穿越（读文件）+ SSRF（发请求）合体

## 2026-07-29 · XXE + 反序列化
- **P6 XXE 通关**：file:// 读 hosts + 读秘密配置 + http:// 打内网拿 FLAG — 570 分
- **P6 反序列化通关**：恶意 pickle 对象还原瞬间执行 whoami — 595 分

## 2026-07-30 · RCE + Redis
- **P6 RCE 通关**：ping 输入框 `; whoami` 命令注入 — 620 分
- **P9 Redis 未授权通关**：KEYS * 列光全部键 + GET flag 无需密码 — 645 分

## 2026-07-31 · 中间件漏洞共性
- **P9 通关**：中间件漏洞三大共性（未授权/弱口令/危险功能暴露）+ MySQL 弱口令未授权拖库 — 670 分

## 2026-08-01 · 休息一天

## 2026-08-02 · 🎓 P10 毕业考通关！
- **SecBlog 综合靶场 6/6 FLAG 全部通关**：
  - 弱口令 admin/123456 → 命令注入 `& whoami` → SSRF 探 Redis → SSRF 内部接口 → 上传绕过（双扩展名 .py.jpg）→ 存储型 XSS
- **+75 分，总分 745，Level 3 入室弟子，P0~P10 基础阶段全部完成！**
- 之后进入进阶专题（见上方 8/3 起记录）
