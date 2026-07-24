# 正反馈：积分 · 里程碑 · 鼓励 · 庆祝

目标：让学员**每天看到数字在涨**，关键节点有仪式感；鼓励要具体，不空洞吹捧。  
积分**不能**代替证据：没达标证据就加分 = 禁止。

## progress 字段

```json
{
  "motivation": {
    "points_total": 0,
    "points_today": 0,
    "points_today_date": "2026-07-17",
    "level": 1,
    "title": "初出茅庐",
    "milestones_unlocked": [],
    "last_encouragement_at": null,
    "pending_celebration": null
  }
}
```

跨日：若 `points_today_date` ≠ 今天 → `points_today = 0` 并更新日期。

## 加分表（有证据才加）

| 事件 | 分 | 说明 |
|------|---:|------|
| 完成当日学习（有实质推进） | +5 | 每天最多 1 次 |
| topic → `partial`（micro 有产出） | +8 | |
| topic → `passed`（mastery≥apply） | +25 | |
| 额外 `transfer` 证据 | +15 | 同 topic 只加一次 |
| 完成一次动手实验并验收（任意合法环境） | +20 | 与 passed 可叠加；不要求用仓库 labs/ |
| 纵向项目交付物齐 | +40 | 每阶段一次 |
| 连续学习第 3/7/14/30 天 | +10/20/40/80 | streak 里程碑 |
| 摸底完成 | +15 | |
| P0 全部通过 | +30 | |

扣分：无。失败不扣分，只给补课鼓励。

## 等级称号（武侠风，由总分推导）

| 总分 | level | title |
|-----:|------:|-------|
| 0–49 | 1 | 初出茅庐 |
| 50–119 | 2 | 崭露头角 |
| 120–229 | 3 | 声名鹊起 |
| 230–379 | 4 | 名动一方 |
| 380–579 | 5 | 一代宗师 |
| 580+ | 6 | 大宗师 |

升级时必须触发庆祝（见下）。鼓励用语可带一点江湖味，但别油腻，仍要说清加分原因。

## 里程碑（解锁一次，记入 milestones_unlocked）

| id | 条件 | 庆祝文案方向 |
|----|------|--------------|
| `ms-first-login` | 摸底完成 | 档案建立 |
| `ms-p0-clear` | P0 全 passed | 契约达成 |
| `ms-first-lab` | 任意 lab 验收通过 | 实验室开门 |
| `ms-first-passed` | 首个非 P0 topic passed | 首胜 |
| `ms-streak-3` | streak.days ≥ 3 | 三连击 |
| `ms-streak-7` | streak.days ≥ 7 | 一周养成 |
| `ms-stage-p3` | P3 stage done | Web 前置通关 |
| `ms-first-transfer` | 首次 transfer 证据 | 迁移高手 |
| `ms-vertical-p3` | P3 纵向项目完成 | 第一份案件卷宗 |

## 鼓励（对话里，要具体）

频率建议：

- 每次**有效加分**后：1～2 句，点明加了多少、为何（「这次是你自己对照了响应，+25」）。  
- 卡住/失败：鼓励 + 下一步线索，**不提扣分**。  
- 若距 `last_encouragement_at` > 1 天且今日有学习：开场先报「今日积分 / 总分 / 离下一称号差多少」。  
- 禁止每句话都夸；禁止假进度庆祝。

## 庆祝动画（HTML）

当解锁里程碑、升级、或单次 +≥25 时：

1. 设 `motivation.pending_celebration`：

```json
{
  "kind": "milestone",
  "id": "ms-first-lab",
  "title": "实验室开门",
  "points_delta": 20,
  "points_total": 85,
  "message": "你完成了第一个合法靶场验证。"
}
```

2. 生成 `learner/ui/celebration-<date>.html`（模板见 ui Skill），含烟花/礼炮级 CSS 动画。  
3. 请学员浏览器打开看一眼；然后把 `pending_celebration` 置 `null`。  
4. 聊天里同步短庆祝 + 分数。

普通进度卡仍用 Kami 纸面；**庆祝页允许更欢快**（烟花），但仍保持单强调色墨蓝 + 羊皮纸底，不要霓虹糊屏。
