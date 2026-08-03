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
3. **跑 `python3 scripts/validate_progress.py`**：若 fail，先把进度修合规再开课（补 jsonl / 补 evidence 文件 / 重算称号），别在坏数据上继续教  
4. **motivation 自洽**：若 `level`/`title` 与 `points_total` 不符（按 motivation.md 表），或 `pending_celebration.points_total` 与实际不符，启动时按表重算（只校正档位，不加分不减分；不符的 `pending_celebration` 置 null 或重发）  
5. `active_failure` → 先 remediation  
6. placement 未完成 → `sec-mentor-placement`  
7. 否则 → `sec-mentor-stages`  
8. 若学员要学的领域不在默认 YAML（如云安全）：按 `path-planning.md` **生成 planned_topics + 阅读清单并授课**，禁止只说「没有这条轨道」  
9. 环境 → `sec-mentor-toolkit`；复盘 → `sec-mentor-review`；展示 → `sec-mentor-ui`

## 写进度时

1. 改 `progress.json` 摘要字段（**含 `updated_at`**，不得落后于最新事件 ts）  
2. **追加** `learner/events/YYYY-MM.jsonl` 一行 JSON（与 recent_events 同一 ts）  
3. 更新 `recent_events`（≤20，每条含 `type`/`ts`/`summary`）  
4. **证据落盘**：`evidence_ids` 里每个 id 必须对应真实文件或 jsonl `evidence_recorded` 事件（禁只塞 id 不写文件）  
5. `passed` 前对照 assessment-rubric 自检清单  
6. 跑 `python3 scripts/validate_progress.py`，**fail 先修后教**  

## 红线（摘要）

合法靶场 / `127.0.0.1`；禁未授权真实站；P0 必做；答题聊天优先；无脚本依赖。  
正反馈：积分/武侠称号/里程碑/烟花见 motivation.md——**有证据才加分**。  
实验：lab-strategy——**目标固定、环境动态**；`labs/` 非硬依赖。  
领域：path-planning——**Agent 自主规划**；YAML 非天花板。

## 阶段顺序（引导）

默认按 curriculum 的 stage 顺序教：当前 stage 的 required topic 稳了再进下一 stage。跨 stage 前看一眼当前 stage 还有没有 required 没过（如 XSS 属 P7，P3 没清时不宜提前）。`planned_topics` 登记的自定义 topic 不受此限。

## 收尾

当日 session 结束前走一遍 `sec-mentor-review`：写 `learner/journal/YYYY-MM-DD.md` + 追加 `daily_review` 事件 + 推 `recent_events` + 更新 `still_fuzzy`。**最后再跑一次 `scripts/validate_progress.py` 确保 progress 落盘合规**。这样新 session 才能续上「今天卡哪、什么还模糊」，而不只看到通过流水。

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
