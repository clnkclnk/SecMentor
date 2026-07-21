# SecMentor UI · Kami 风格约束

视觉参考：[tw93/Kami](https://github.com/tw93/Kami)（紙）——「Good content deserves good paper。」  
本文件是**裁剪后的交互页约束**，不是完整 Kami 文档系统；不要求安装 Kami 插件。若学员要导出精美 PDF/长文，可另装 Kami Skill。

## 适用页面

- 摸底/课中选择题  
- 今日任务卡、阶段进度、路径选择  
- 每日/每周小结的 HTML 呈现  

## 调色（唯一强调色）

| Token | 值 | 用途 |
|-------|-----|------|
| `--kami-paper` | `#f5f4ed` | 页面背景（羊皮纸，忌纯白） |
| `--kami-ink` | `#1B365D` | 唯一强调色：标题点缀、选中边框、主按钮、进度填充 |
| `--kami-body` | `#2a2a28` | 正文 |
| `--kami-muted` | `#6b6560` | 次要说明（暖灰，略带黄褐） |
| `--kami-line` | `#ddd8ce` | 分割线 / 未选边框 |
| `--kami-card` | `#faf9f4` | 卡片/选项底（比纸面略亮） |
| `--kami-warn-bg` | `#f3efe3` | 提示条背景 |

禁止：第二强调色、霓虹、紫粉渐变、厚重投影、玻璃拟态、仪表盘炫光。

## 字体

- 中文优先衬线层级：有「仓耳今楷 / TsangerJinKai02」可用则用；否则 `Songti SC`、`Noto Serif SC`、`Georgia` 回退。  
- 仓耳今楷个人学习可用；勿把商业授权字体打进仓库分发。  
- 等宽仅用于预览答案串：`ui-monospace, Menlo, monospace`。  
- 不要用 Inter / Roboto / 系统默认无衬线当主标题。

## 版式

- 读起来像**一页纸**，不是后台仪表盘。  
- 最大内容宽约 `40～42rem`；留白充足。  
- 圆角克制（约 8～12px）；细线分隔；无多层阴影（最多极淡一层或不使用）。  
- 一页一事：答题页不要塞统计墙。

## 交互适配（Kami 原文没有，SecMentor 必加）

Kami 偏印刷文档；本项目页面有点选，故允许：

- 选项按钮：未选 `--kami-card` + `--kami-line`；选中描边/浅底用 `--kami-ink`  
- 底部 dock：同纸色半透明，顶部分割线，放「下载 / 复制」  
- 进度条：轨道暖灰，填充仅用 `--kami-ink`  
- 仍须 inbox 回传控件（见主 SKILL）

## CSS 变量骨架（生成页时内联）

```css
:root {
  --kami-paper: #f5f4ed;
  --kami-ink: #1B365D;
  --kami-body: #2a2a28;
  --kami-muted: #6b6560;
  --kami-line: #ddd8ce;
  --kami-card: #faf9f4;
}
body {
  margin: 0;
  color: var(--kami-body);
  background: var(--kami-paper);
  font-family: "TsangerJinKai02", "Songti SC", "Noto Serif SC", Georgia, serif;
  line-height: 1.55;
}
```

## 与完整 Kami 的边界

| 做 | 不做 |
|----|------|
| 借用纸色、墨蓝、衬线、克制排版 | 引入 Kami 全套 PDF/WeasyPrint 流水线（除非用户另装） |
| 交互题、任务卡、进度条 | 把答题页做成八模板文档之一硬套 |
| 单文件 HTML 可本地打开 | 依赖外网 CSS 框架或必须在线字体才能用 |
