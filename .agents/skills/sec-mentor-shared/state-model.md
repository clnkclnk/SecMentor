# SecMentor 状态与证据模型

权威课程数据：同目录 [curriculum.yaml](curriculum.yaml)。  
进度摘要：`learner/progress.json`（保持小）。  
完整事件：`learner/events/YYYY-MM.jsonl`（只追加）。  
证据文件：`learner/evidence/<evidence_id>.*`（可选附件）。

## Topic 状态机

```text
locked → available → in_progress → partial | passed | failed
                              ↘ skipped | deferred | waived
```

| 状态 | 含义 |
|------|------|
| `locked` | 依赖未满足 |
| `available` | 可开始 |
| `in_progress` | 进行中 |
| `partial` | 做了 micro 切片或未完成验收 |
| `passed` | 至少达到 `apply`（见下） |
| `failed` | 本轮验收未过（可升 `fail_count`） |
| `skipped` | optional 主动跳过 |
| `deferred` | 延后 |
| `waived` | 摸底抽检后免修实讲（仍建议轻量抽检记录证据） |

`passed` 要求：`mastery` ∈ {`apply`,`transfer`}，且有至少 1 条非纯自述证据。  
核心 topic（`curriculum.yaml` 里 `require_transfer: true`）另需至少 1 次 `transfer` 级证据。

## 掌握层级 mastery

| 级别 | 含义 | 可否标 passed |
|------|------|----------------|
| `none` | 未证明 | 否 |
| `recall` | 能记住术语/步骤名 | 否 |
| `understand` | 能解释原因 | 否 |
| `apply` | 能完成同类任务 | **是（基础通过）** |
| `transfer` | 能处理陌生变体 | 是；核心 topic 建议必备 |

## 证据对象（写入 evidence 文件或嵌在事件里）

每条证据必须能区分「自述」与「观察到的输出」。

```json
{
  "id": "ev-20260717-001",
  "type": "lab_observation",
  "source": "terminal_output",
  "task_id": "http-observation-01",
  "topic_id": "http-basics",
  "observed_at": "2026-07-17T20:30:00+08:00",
  "result": "passed",
  "independence": "guided",
  "mastery": "apply",
  "artifact": "learner/evidence/ev-20260717-001.txt",
  "summary": "学员修改查询参数并解释状态码变化"
}
```

| 字段 | 允许值 |
|------|--------|
| `type` | `quiz` / `oral` / `lab_observation` / `artifact` / `self_report` |
| `source` | `chat` / `terminal_output` / `browser_note` / `file` / `inbox` |
| `independence` | `independent` / `guided` / `over_assisted` |
| `result` | `passed` / `failed` / `partial` |

规则：

- 仅有 `self_report` **不能**把 topic 标为 `passed`。  
- `over_assisted` 的通过证据最多记到 `understand`，需再来一次 `guided` 或 `independent` 才能 `apply`。  
- Agent 给完整答案后学员照抄 → 标 `over_assisted`，不得直接 `passed`。

## 失败分类 active_failure

| category | 处理 |
|----------|------|
| `concept_gap` | 按 `curriculum.yaml` remediation 回退 topic |
| `tooling_failure` | 停主线，修工具/代理，不计入概念 fail 或单独计 |
| `environment_failure` | 停主线，修 Docker/端口；不机械回退章节 |
| `careless_error` | 同 topic 再试，不一定回退 |
| `instruction_misunderstanding` | 换讲解方式，同 topic |
| `over_assisted` | 降低提示，要求独立再做 |

`fail_count`：仅 `concept_gap` / 明确知识向失败累加。≥2 → 进入 remediation_topics，原 topic 保持 `in_progress` 或 `failed`，`resume_topic` 记录回来点。

## 事件写入（无脚本时由 Agent 手写，须遵守）

1. 追加一行到 `learner/events/YYYY-MM.jsonl`（当月文件）。  
2. 把同一事件摘要 push 进 `progress.recent_events`，保留最多 20 条。  
3. 更新 `progress.updated_at`。  
4. **禁止**把全部历史塞回 `progress.json`。

事件类型示例：`placement_completed` / `topic_passed` / `topic_failed` / `evidence_recorded` / `daily_review` / `remediation_started`。

## P0 与摸底

- 摸底结束后：`current_stage` **必须仍为 `P0`**（若未完成 P0）。  
- 写入 `placement.recommended_start_after_p0`（如 `P3`）。  
- P0 全部 required topic `passed` 后，再把 `current_stage` 设为推荐起点（并解锁依赖）。

## 每日选题

1. 若 `active_failure` 非空 → 先做 remediation。  
2. 若 `path.still_fuzzy` 非空 → 优先其中 topic（可 micro）。  
3. 否则按 `curriculum.yaml` 依赖取下一 `available` required topic。  
4. 时间紧 → `micro: true` + `partial`，不假装 passed。
