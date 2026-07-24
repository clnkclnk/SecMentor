---
id: L03-cookie-wristband
title: Cookie 与 Session：客栈的腰牌
covers: [cookie-session]
persona: [beginner, practitioner]
minutes: 15
lab_hint: 任意带登录的靶场或本地 demo；浏览器 Application → Cookies
fun_tone: wuxia
---

## 钩子

HTTP 天生「健忘」：每封信彼此独立，账房不记得你上一秒是谁。  
于是客栈发明了**腰牌**：你登录成功后，账房发一块牌；下次你亮牌，就算还是你。  
这块牌，常常就是 Cookie；牌背后登记的那本册子，常常叫 Session。  
偷腰牌 ≈ 冒充你——所以会话相关漏洞，杀伤力大、故事也好懂。

（停：等学员说「继续」）

## 片 1 · Cookie：浏览器替你保管的小纸条

- 服务端用 `Set-Cookie` 发腰牌  
- 之后同站请求，浏览器自动把 Cookie 塞进请求头  
- 常见属性（先混脸）：`HttpOnly`（JS 不好偷）、`Secure`（只走 HTTPS）、`SameSite`（跨站要不要带）

你不需要一次背完属性表；先会在 DevTools 里**找到 Cookie、看名字、看值是否像随机串**。

（停：等学员说「继续」）

## 片 2 · Session：牌上写的是编号，不是整个人

常见模式：

- Cookie 里只放 `sessionid=一串随机`  
- 真正的「用户是谁、购物车有啥」存在服务端内存/Redis/文件里  

所以：

- **偷到 sessionid** → 可能直接冒充（会话劫持）  
- **猜得到/固定得住 sessionid** → 会话固定等经典坑（后面专题再挖）

（停：等学员说「继续」）

## 片 3 · 和安全的直觉连接

学完腰牌，你应该自动多问三句：

1. 退出登录有没有让牌作废？  
2. 牌会不会被 XSS 偷走（有没有 HttpOnly）？  
3. 换一个账号登录，牌变了没有？

这三句比背定义有用。

（停：等学员说「继续」）

## 今日微任务

登录某个合法练习站（或自己的测试环境）：

1. 在浏览器 Application/Storage 里找到会话相关 Cookie，记下**名字**（不要发完整敏感值到公开场合）  
2. 退出登录后再看：这条 Cookie 是否消失或变化  
3. 用一句话回答：你的站点更像「牌上写编号」还是「牌上塞了很多用户信息」？

## 阅读（可选，最多 1 条）

- [MDN：HTTP Cookie](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Cookies) — 读到「Cookie 的用途」即可。

## 过关一句话

能说清：**Cookie 是腰牌、Session 常是账房名册**；并知道丢腰牌为什么危险。
