---
name: sec-mentor-ui
description: >-
  SecMentor HTML for progress cards (Kami) and celebration pages with fireworks
  when points/milestones unlock. Quizzes stay chat-first. Use for 进度, 积分板,
  烟花庆祝, 里程碑.
---

# SecMentor 交互呈现

## 渠道优先级

1. **聊天**答题与日常鼓励（报今日分/总分）  
2. HTML：**积分进度卡**（Kami 纸面）  
3. HTML：**庆祝页**（烟花/礼炮，见 [celebration-template.md](celebration-template.md)）  
4. HTML 答题 + inbox（可选，非默认）

## 进度/积分卡（日常）

展示且必须与 `progress.json` 一致：

- 称号 `motivation.title` / level  
- 总分、今日分、距下一称号还差多少  
- streak 天数  
- 当前 stage / topic  
- 最近解锁的里程碑（1～2 个）  

风格：[kami-theme.md](kami-theme.md)。

## 庆祝页（正反馈高潮）

触发见 [../sec-mentor-shared/motivation.md](../sec-mentor-shared/motivation.md)：升级、里程碑、单次大额加分。  

1. 读 `motivation.pending_celebration`  
2. 按 [celebration-template.md](celebration-template.md) 生成完整可开的 HTML（烟花/礼炮动画写全）  
3. 请学员打开；聊天同步「+分 / 新称号」  
4. 清空 `pending_celebration`  

`preferences.celebrations === false` 时只聊天祝贺，不生成动画页。

## Examples

开场一句：  
「今天 +15，总分 65。已是「崭露头角」，再 55 分便「声名鹊起」。」
