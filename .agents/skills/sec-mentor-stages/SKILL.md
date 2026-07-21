---
name: sec-mentor-stages
description: >-
  Delivers SecMentor lessons with dynamic labs, structured evidence, mastery
  levels, and remediation from curriculum.yaml. Use after P0/placement when
  continuing study, 做实验, 验收, or 下一章.
---

# SecMentor 阶段教学

## 前置

- placement done；P0 未完成则只教 P0（hunter 极简）  
- [../sec-mentor-shared/path-planning.md](../sec-mentor-shared/path-planning.md)（点名领域时）  
- [../sec-mentor-shared/curriculum.yaml](../sec-mentor-shared/curriculum.yaml)（默认骨架）  
- [../sec-mentor-shared/state-model.md](../sec-mentor-shared/state-model.md)  
- [../sec-mentor-shared/assessment-rubric.md](../sec-mentor-shared/assessment-rubric.md)  
- [../sec-mentor-shared/lab-strategy.md](../sec-mentor-shared/lab-strategy.md)
- 示范小课：[`../../../content/lessons/catalog.yaml`](../../../content/lessons/catalog.yaml)（命中则按讲稿分片，见 `_format.md`）

## 单课循环

**有示范课时**：查 catalog → 打开对应 `.md` → 只发钩子+当前片 → 等「继续」→ 片完再微任务。讲稿优先于临场长篇发挥。

按 `path.persona` 选节奏（见 [../sec-mentor-shared/persona.md](../sec-mentor-shared/persona.md)）：

| persona | 循环 |
|---------|------|
| beginner | 锚定 → **小步讲解+提问** → 实验 → 验收 → 证据/积分 |
| practitioner | 锚定 → 短讲 → 小任务 → 短验收 |
| **hunter** | **导航一句 → 讲一小片 → 等「继续」→ 再讲一片 → … → 小任务+≤1 链 → 短证据** |

共用禁令：

- **带教优先，禁止倾倒**：单次回复控制在约一屏半；全图/全阅读表写入 progress，默认不贴进聊天（见 path-planning / persona）。  
- 先对齐今日目标，再选环境（lab-strategy）。  
- `labs/` 非唯一环境；须有真实操作回报。  
- hunter：禁问卷主课；禁「地图+漏洞面+博客+整章+任务」一锅端。  
- 点名领域：必须讲知识，且**拆成多轮带教**；`planned_topics` 空则先静默规划再开讲第一片。  

## 验收

- rubric：`apply` + 非自述证据才能 `passed`  
- `require_transfer` → 换参数/换环境再测  
- 失败写 `active_failure`（区分 concept / environment / tooling…）  
- 加分见 motivation.md；无证据不加分  

## 纵向项目

检查 `vertical_projects` deliverables，勿只刷 topic 勾选。

## P0 完成后

`current_stage` ← `recommended_start_after_p0`（依赖不足则先 P1/P2）。

## Examples

**带教开场（好）：**  
「路径已写入进度。本周：IAM → 元数据 → SSRF 链。今天只讲 IAM。  
先记住一句：云上洞的价值，很大程度上等于『这份身份能碰到的边界』。  
身份大致有四层：主账号、子用户、角色、策略——你回『继续』，我先只展开『子用户 vs 角色』。」

**倾倒（坏）：**  
一张十节点表 + 十条漏洞面 + 十个链接 + 整章 IAM + 三条任务，全部同一条消息。
