# SecMentor 学习日志（每日记录）

> 自动汇总于 `learner/daily-log.md`，每天学习后更新并推送
> 总进度：P0~P10 全部通关（745 分）→ 进阶漏洞专题学习中

---

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
## 更早记录
- 2026-07-18 ~ 08-02：P0~P10 基础全部通关（毕业考 745 分，Level 3 入室弟子）
- 完整里程碑见 `learner/progress.json` 和 `learner/events/*.jsonl`
