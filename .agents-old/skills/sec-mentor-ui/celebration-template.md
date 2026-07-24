# 庆祝页模板要点

生成完整单文件 HTML 到 `learner/ui/celebration-YYYY-MM-DD.html`（或带 milestone id）。

## 必须展示

- 标题（里程碑名或「升级！」）  
- `points_delta` / `points_total` / 当前 `title`  
- 一句具体成就（来自 pending_celebration.message）  
- 底部：「关闭后继续学习」  

## 动画（内联，无外链）

任选或组合，持续约 2.5～4 秒后可循环缓停：

1. **烟花**：canvas 或纯 CSS 粒子（墨蓝 `#1B365D` + 暖金 `#c4a35a` + 纸色，忌彩虹disco）  
2. **礼炮**：两侧彩带/三角形向上喷再落下（CSS `@keyframes`）  
3. **数字跳动**：总分从旧值滚到新值（短 JS）  

背景仍用 `#f5f4ed`；主按钮墨蓝。不要音效自动播放。

## 最小结构示意

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SecMentor · 庆祝</title>
  <style>
    :root { --paper:#f5f4ed; --ink:#1B365D; --gold:#c4a35a; }
    body { margin:0; min-height:100vh; background:var(--paper);
      font-family:"Songti SC","Noto Serif SC",Georgia,serif; color:#2a2a28;
      display:grid; place-items:center; overflow:hidden; }
    .card { text-align:center; padding:2rem; z-index:2; position:relative; }
    h1 { color:var(--ink); margin:0 0 .5rem; font-size:1.8rem; }
    .pts { font-size:2.4rem; color:var(--ink); font-variant-numeric:tabular-nums; }
    .burst { position:fixed; inset:0; pointer-events:none; z-index:1; }
    /* 在此写 confetti / fireworks keyframes */
  </style>
</head>
<body>
  <canvas class="burst" id="fx"></canvas>
  <div class="card">
    <h1><!-- 标题 --></h1>
    <p class="pts">+<!-- delta --> · 总分 <!-- total --></p>
    <p><!-- message --></p>
    <p><!-- 称号 --></p>
  </div>
  <script>
    // 简单烟花：随机点向四周扩散，用 ink/gold
  </script>
</body>
</html>
```

Agent 生成时把占位换成真实数字；烟花 JS 写全，勿留 `// TODO`。
