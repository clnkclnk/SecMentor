# 验收 Rubric（禁止纯主观 0～3）

## 通过门槛（topic → passed）

必须同时满足：

1. 至少 1 条证据：`type` ≠ `self_report`，且 `result=passed`  
2. `independence` ≠ `over_assisted`  
3. `mastery` ≥ `apply`  
4. 学员能用自己的话复述「做了什么 / 为什么」  

核心 topic 额外：至少 1 条 `mastery=transfer`（换参数名、换路径或换表述的同类任务）。

## 课中检查 vs 验收

| 类型 | 用途 | 能否单独 passed |
|------|------|-----------------|
| 口头/选择抽查 | 调讲解 | 否 |
| 实验观察 | 主证据 | 是（达 apply） |
| 迁移变体 | 核心加固 | 核心 topic 需要 |

## 打分映射（可选写入 skills_radar）

| mastery | radar 约分 |
|---------|------------|
| none | 0 |
| recall | 1 |
| understand | 2 |
| apply | 2.5 |
| transfer | 3 |

旧字段 `score` 0～3 **停用**；用 `mastery` + `evidence_ids`。

## Agent 自检（写 passed 前）

- [ ] 证据不是「学员说会了」一句话  
- [ ] 有可贴回的输出/现象描述（或 artifact 路径）  
- [ ] 未在本轮提供完整通关答案后立即标 passed  
- [ ] 依赖 topic 已 passed/waived  
- [ ] 已追加 events jsonl 并更新 recent_events  
