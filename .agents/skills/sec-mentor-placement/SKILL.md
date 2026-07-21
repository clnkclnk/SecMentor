---
name: sec-mentor-placement
description: >-
  Runs SecMentor placement via chat-first interview and dynamic quizzes; sets
  recommended_start_after_p0 while keeping current_stage at P0. Use on 摸底/重测
  or placement.status not done.
---

# SecMentor 摸底

## 规则

- 先判 [../sec-mentor-shared/persona.md](../sec-mentor-shared/persona.md)：`beginner` / `practitioner` / `hunter`。  
- **hunter**：经历用自然语言一次说清即可，**禁止**再开 8 题访谈 + 5 题试卷；最多 1～2 个澄清问题。  
- **beginner**：可完整访谈 + 短测。  
- 摸底结束：`placement.status=done`，`recommended_start_after_p0`，写入 `path.persona` / `path.mode`。  
- **`current_stage` 保持 `P0`** 直到 P0 过；hunter 的 P0 用极简确认（见 persona.md），勿布置长作文验收。  
- 免修：`waived` + 轻量抽检，勿假装深层 passed。

## 流程

### beginner / practitioner

1. 经历访谈 → 2. 短测 → 3. 决策 → 4. 写盘加分 → 5. 进 P0（完整或略缩）

### hunter（默认：安全岗/红队/SRC/明确挖洞）

1. 学员一段话说清背景与目标（含授权：SRC/自建租户）  
2. 导师用 ≤10 行确认档案：persona=hunter、mode=lab-first、recommended_start_after_p0、本周 1～2 个云/挖洞焦点  
3. **不**刷能力桶试卷（除非学员要求）  
4. 写盘加分 → **立刻**做 hunter 极简 P0（贴 scope 要点 + 一句 Agent 边界）→ 过了就上第一个实战任务  

默认骨架 [../sec-mentor-shared/curriculum.yaml](../sec-mentor-shared/curriculum.yaml)。  
学员目标若是云安全等：按 [../sec-mentor-shared/path-planning.md](../sec-mentor-shared/path-planning.md) 写入 `path.domain` + `planned_topics` + `reading_list`；**同一会话给出规划并开始教第一块知识**，不要等「以后有云轨道」。

## Examples

```text
学员：五年安全岗，腾讯云运营，红队，要挖京东云 SRC
→ persona: hunter, mode: lab-first, recommended_start_after_p0: P3（或云专题）
→ 不出 1A2B 试卷
→ P0：请贴 SRC scope 三条要点 + 确认 Agent 不越权
→ 下一步：租户内第一个云面任务（不是再问答）
```
