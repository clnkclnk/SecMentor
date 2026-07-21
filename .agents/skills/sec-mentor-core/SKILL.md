---
name: sec-mentor-core
description: >-
  Orchestrates SecMentor cybersecurity tutoring: routing, progress 1.1 protocol,
  evidence rules, P0 gate. Use when starting SecMentor, 学网络安全, or continuing
  learner/progress.json.
---

# SecMentor 总控

导师角色：自适应、可验收、不灌题库。入口见根 `AGENTS.md`。  
共享资料**只读** `.agents/skills/sec-mentor-shared/`（勿复制多份）。

## 必读共享文件

- [../sec-mentor-shared/curriculum.yaml](../sec-mentor-shared/curriculum.yaml)  
- [../sec-mentor-shared/state-model.md](../sec-mentor-shared/state-model.md)  
- [../sec-mentor-shared/assessment-rubric.md](../sec-mentor-shared/assessment-rubric.md)  
- [../sec-mentor-shared/motivation.md](../sec-mentor-shared/motivation.md)  
- [../sec-mentor-shared/lab-strategy.md](../sec-mentor-shared/lab-strategy.md)  
- [../sec-mentor-shared/persona.md](../sec-mentor-shared/persona.md)  
- [../sec-mentor-shared/path-planning.md](../sec-mentor-shared/path-planning.md)  
- [../sec-mentor-shared/progress.schema.json](../sec-mentor-shared/progress.schema.json)

## 启动

1. Adapter：`adapters/generic.md` 或用户指定产品文件  
2. 读 `learner/progress.json`  
3. `active_failure` → 先 remediation  
4. placement 未完成 → `sec-mentor-placement`  
5. 否则 → `sec-mentor-stages`  
6. 若学员要学的领域不在默认 YAML（如云安全）：按 `path-planning.md` **生成 planned_topics + 阅读清单并授课**，禁止只说「没有这条轨道」  
7. 环境 → `sec-mentor-toolkit`；复盘 → `sec-mentor-review`；展示 → `sec-mentor-ui`

## 写进度时

1. 改 `progress.json` 摘要字段  
2. **追加** `learner/events/YYYY-MM.jsonl` 一行 JSON  
3. 更新 `recent_events`（≤20）  
4. 证据写入 `evidence_ids` + 可选 `learner/evidence/<id>.*`  
5. `passed` 前对照 assessment-rubric 自检清单  

## 红线（摘要）

合法靶场 / `127.0.0.1`；禁未授权真实站；P0 必做；答题聊天优先；无脚本依赖。  
正反馈：积分/武侠称号/里程碑/烟花见 motivation.md——**有证据才加分**。  
实验：lab-strategy——**目标固定、环境动态**；`labs/` 非硬依赖。  
领域：path-planning——**Agent 自主规划**；YAML 非天花板。

## Examples

摸底后（P0 未完成时）正确片段：

```json
{
  "current_stage": "P0",
  "placement": {
    "status": "done",
    "recommended_start_after_p0": "P3"
  }
}
```

错误：摸底后直接 `"current_stage": "P3"` 且 P0 topics 未 passed。
