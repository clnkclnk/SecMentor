---
name: sec-mentor-toolkit
description: >-
  Guides Yakit/Burp and dynamic lab environments for SecMentor. Labs folder is
  optional examples; no pinned images or topic hard-binds. Use for 环境/代理/Docker/靶场.
---

# SecMentor 工具与环境

先读 [../sec-mentor-shared/lab-strategy.md](../sec-mentor-shared/lab-strategy.md)。

## 原则

- 学员本机执行；无强制脚本。  
- **不钉**镜像/工具版本。  
- `labs/` = 可选示例，启动失败就换，不阻塞课程。  
- 代理入门优先 Yakit 或学员已有 Burp。  
- 破解/逆向话题可学，勿抢跑主线。  

## 组织实验（动态）

1. 从今日 topic 的 outcomes 写出教学目标  
2. 按 lab-strategy 选环境（已有 → labs 示例 → 常见靶场 → 最小自建）  
3. 学员确认：能访问、有响应  
4. 做任务 → 迁移验收 → 写证据（可注明实际 `env`）  

## Examples

```text
今日目标：理解查询参数如何出现在请求里并影响响应。
环境：你机器若已有 httpbin/DVWA 可用它们；否则可试 labs/http-observation，拉不下来我们就换。
先打开页面，把能看到的首页/JSON 贴一下，确认环境活着再继续。
```
