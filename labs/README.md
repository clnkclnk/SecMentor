# labs/ — 可选示例库（非课程硬依赖）

这里的 compose/README **可复用、可忽略**。  
教学以 topic 的 **outcomes + 验收** 为准；Agent 按 `lab-strategy.md` 动态选环境。

| 示例 id | covers（能力标签，松散） |
|---------|-------------------------|
| http-observation | http-basics, burp-intro, browser-devtools |
| path-traversal | file-download, file-include, path-traversal |
| sql-injection-basic | sqli-manual, sqli-principle |

约定：

- 不钉镜像版本；启动失败就换环境，不必改课程  
- 无强制脚本；学员执行，导师根据现象写证据  
- **不要**在 `curriculum.yaml` 里写死 `topic → 本目录`  
- 新示例只需 `lab.yaml`（含 `covers`）+ compose/README，供 Agent 挑选
