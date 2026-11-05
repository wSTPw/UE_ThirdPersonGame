# CHG-20261017-001：项目技术文档与 AI 维护基线

- 状态：completed
- 日期：2026-10-17
- 需求：检查现有项目，建立便于 AI 记录修改、新增技术方案与接口的文档。
- 关联：ADR-0001；本文建立现有核心接口 ID 与问题 ID。
- Git：工作区文档变更，未提交；此前升级和用户的已有修改保留。

## 原因与结果

补齐当前架构、物品/背包、战斗/AI、UI/输入与接口语义，区分旧设计稿、当前实现和未来方案。建立 AGENTS 维护约定、Plans/Changes/ADR 索引和四类模板，以及机器可读模块索引与文档检查工具。

只读编辑器核对确认 MyLevel 的放置玩家实例用 Player0 自动控制、旧玩家路径为 redirector、五份物品资产的真实 ItemID/Action、敌人控制器默认配置等。发现的代码/配置边界记录在 Known-Issues，未在文档任务中修改玩法行为。

## 修改清单与接口影响

| 范围 | 内容 |
| --- | --- |
| 根 AGENTS.md / README.md | 文档入口与后续 AI 同步要求 |
| Docs 的 Architecture / Systems / Interfaces / Development | 当前技术事实、模块职责、调用链与接口边界 |
| Docs 的 Maintenance / Templates / Plans / Changes / Decisions | 维护流程、方案/契约/变更/决策模板与索引 |
| Docs/Reference | modules.json 与有日期的编辑器只读观测快照 |
| Scripts/Docs/check_docs.py | 标准库文档链接与模块/接口引用检查 |
| Docs/Known-Issues.md | 静态发现和待运行验证的问题，带稳定 ID 和验收方向 |

没有改变 C++ 签名、玩法代码、配置、MCP 安装或保存二进制资产。本次提供的接口文档描述真实语义，不等于修复其中指出的边界。

## 实际验证

| 检查 | 实际结果 / 证据 |
| --- | --- |
| 配置、关键头文件与实现、旧方案文档、资源路径只读梳理 | 完成；引用与差异写入各现状页 |
| MCP 原生只读查询 | 成功读取世界设置、GameMode DefaultPawnClass、玩家蓝图与场景实例、物品数据、敌人默认配置；快照在 Reference/editor-observations.json |
| 文档链接与索引检查 | `python Scripts/Docs/check_docs.py` 通过：23 份 Markdown、117 个本地链接、10 个模块条目及编辑器快照 JSON |
| 文档工具 Python 语法 | 使用 Python AST 解析；交付前通过 |
| `git diff --check` | 交付前通过；原有行结束符转换提示不影响检查结果 |
| 本次 C++ 编译 / PIE / 战斗完整运行测试 | 未执行；此次只改文档和文档检查脚本。历史编译/PIE/MCP 结果见 UE58-Upgrade.md，不能视为本次新验证 |

## 风险与回退

编辑器快照有时间和范围限制；类默认值不等于关卡实例，缺失属性也不总是错误。已知问题多为静态发现，修复需独立方案和运行验证。文档检查不解析 C++ ABI、蓝图图表或 Markdown 标题锚点。

回退时仅移除此 CHG 列明的新文档/脚本及根 README 新入口，不恢复或覆盖之前的 UE 升级、插件及用户资源修改。后续如已产生方案/变更记录，应先保留这些历史文件。

## 已同步文档

[技术入口](../README.md)、[架构](../Architecture.md)、[接口](../Interfaces.md)、[维护流程](../Maintenance.md)、[已知问题](../Known-Issues.md)、[记录索引](README.md)。
