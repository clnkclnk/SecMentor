# 产品适配器（薄层）

不要靠「目录里有没有 CLAUDE.md」猜测当前产品——本仓库**固定带有** `CLAUDE.md`。

| 文件 | 用途 |
|------|------|
| `generic.md` | 默认：任何读 `AGENTS.md` 的 Agent |
| `claude-code.md` | Claude Code |
| `cursor.md` | Cursor |
| `codex.md` | Codex |
| `workbuddy.md` | WorkBuddy 等 |

主控只认：`.agents/skills/` + `learner/`；`labs/` 可选示例。  
适配器只补充：该产品如何打开文件、是否方便渲染 HTML、能力差异一句。
