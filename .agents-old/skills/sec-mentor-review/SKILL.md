---
name: sec-mentor-review
description: >-
  Writes SecMentor daily/weekly reviews to journal and events jsonl; updates
  still_fuzzy and recent_events without bloating progress.json. Use on 小结/复盘.
---

# SecMentor 复盘

## 每日

1. 收集完成/卡点/时长  
2. 更新 `path.still_fuzzy`  
3. 结算当日学习分（motivation.md：+5/天等），报「今日分 / 总分 / 称号」  
4. 追加 `daily_review` 到 `learner/events/YYYY-MM.jsonl`  
5. `recent_events` 推入摘要（≤20）  
6. 写 `learner/journal/YYYY-MM-DD.md`（可含当日积分）  
7. **不要**把全文复盘塞进 progress  
8. 有里程碑/升级 → 生成庆祝 HTML（ui Skill）  

## 每周

混测现场出题；调整 `focus_next_week`；写 `week-*.md`；更新 `last_weekly_review`。

## Examples

jsonl 一行：

```json
{"type":"daily_review","at":"2026-07-17T21:00:00+08:00","summary":"http-basics 实验完成，Cookie 仍模糊","topics_touched":["http-basics"],"minutes":55}
```
