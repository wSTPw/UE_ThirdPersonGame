# CHG-20261030-001：删除旧 UEBridgeMCP 插件的遗留归档

- 状态：completed
- 日期：2026-10-30
- 需求摘要：用户要求删除旧的 UEBridgeMCP 插件遗留物。该插件在 UE5.8 升级时已卸载，仅剩 `Saved/Upgrade-UE58/UEBridgeMCP-retired.zip` 一份源码归档。
- 关联 PLAN / ADR / 问题 / 接口 ID：无（工具链清理，不涉及玩法需求）
- Git：见本次提交

## 原因与结果

**触发条件**：`Docs/UE58-Upgrade.md` 记录旧 `UEBridgeMCP` 插件在升级 UE5.8 时已卸载，旧源码与 Git 元数据归档于 `Saved/Upgrade-UE58/UEBridgeMCP-retired.zip`（581 个条目、解压 6.4MB、含 `.gitattributes`/`README`/`UEBridgeMCP.uplugin`）。用户要求删除这份遗留归档。

**原行为**：该 zip 是旧插件的**唯一**副本——git 历史中的 `Plugins/UEBridgeMCP` 只是无内容的 gitlink（父提交 `8e99c3d` 已移除该链接），磁盘全盘检索无第二份 `UEBridgeMCP.uplugin`。保留它意味着旧插件的回退路径仍然存在。

**当前行为**：zip 已永久删除，`Saved/Upgrade-UE58/` 由 7.6MB 降至 3.6MB（剩余为 UE5.8 升级期的构建/编辑器/PIE 日志与 JSON 证据，未动）。旧插件副本不再存在，回退旧桥接需重新获取上游源码。

**删除方式说明**：本环境安全策略禁止 `Add-Type`（运行时编译 .NET）与 COM 对象实例化，两条回收站删除路径均被拦截，因此为直接删除（不经回收站），已由用户明确确认。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Saved/Upgrade-UE58/UEBridgeMCP-retired.zip` | 旧插件源码归档（4102286 字节） | 按用户要求永久删除；不可恢复 |
| `Docs/UE58-Upgrade.md` | 「升级变更」中旧插件卸载条目 | 原文写「恢复归档在 …zip」，改为记录该归档已于 2026-10-30 永久删除，并说明回退需重新获取上游源码 |

## 接口、事件与资源影响

无。当前在用的 `Plugins/UE_MCP_Bridge`（1.4.7）与 `Tools/ue-mcp` 未改动，`IntroCpp.uproject` 插件段未改动，`Saved/Upgrade-UE58/` 其余日志与 JSON 未改动。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 删除前确认归档内容 `zipfile.namelist()` | 本机 Python | 581 条目、解压 6.4MB，首项 `.gitattributes`、含 `UEBridgeMCP.uplugin`，确认为旧插件源码归档 | 命令输出 |
| 删除前确认副本唯一性 `find /e /d -iname UEBridgeMCP.uplugin` | 本机 | 无任何结果；`git rev-list … Plugins/UEBridgeMCP` 对应对象为 gitlink、无文件内容 | 命令输出 |
| 删除 `rm -f Saved/Upgrade-UE58/UEBridgeMCP-retired.zip` | 本机 | 文件已不存在；目录 28 项、3.6MB | 命令输出 |
| `python Scripts/Docs/check_docs.py` | 仓库文档检查 | PASS | 命令输出 |
| `git diff --check` | 本机 | 通过 | 命令输出 |

未执行：未验证旧插件在新环境中是否还能编译——归档已删除，无法验证；不影响当前工程（`Plugins/UE_MCP_Bridge` 仍在用且 2026-10-30 有运行记录）。未编译、未 PIE：本次无 C++/资产改动。

## 风险、遗留与回退

- **回退不可能**：旧插件源码已永久删除，没有回收站副本，也没有备份目录。若新桥接出现无法解决的问题，只能重新获取 `UEBridgeMCP` 上游源码。
- 当前插件不受影响：`Plugins/UE_MCP_Bridge` 仍在 `IntroCpp.uproject` 中启用，插件自身的 `Saved/UE_MCP_Bridge/` 与 `Intermediate`/`Binaries`（663MB 构建产物）未清理，属另一事项。
- 如需回收磁盘，下一步可清理 `Plugins/UE_MCP_Bridge` 的 `Intermediate`（424MB）与 `Binaries`（239MB），源码与 `.uplugin` 保留即可重新构建。

## 已同步文档

- [UE5.8 升级记录](../UE58-Upgrade.md)
- [记录索引](README.md)
