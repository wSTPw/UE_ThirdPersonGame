# CHG-20261027-005：武器碰撞/加载链证据 JSON 归档到已跟踪目录

- 状态：completed
- 日期：2026-10-27
- 需求摘要：`Saved/MHWIRestoration/B19-20261026/weapon-hit-volume-evidence.json` 被 `.gitignore` 的 `Saved/` 规则排除，未随 CHG-20261026-011 一起入库，但其数据需要长期保留；同批次的 `weapon-collision-loader-chain.json` 属同一问题。
- 关联 PLAN / ADR / 问题 / 接口 ID：CHG-20261026-011、CHG-20261027-002、R18（保持取证中）
- Git：见本次提交

## 原因与结果

**触发条件**：`.gitignore` 第 9 行 `Saved/` 将整个 `Saved/` 目录排除。`Saved/` 是 UE 的暂存目录（日志、自动保存、崩溃报告），按社区惯例整体忽略；两个取证脚本的默认输出路径恰好写在该目录下，导致证据 JSON 生成成功但从未进入版本库。CHG-20261026-011 的“实际验证”表当时已标注“（本机忽略目录）”，未意识到这会丢失版本记录。

**原行为**：证据只存在于本机 `Saved/`，克隆或换机后无法复现当时的数据；CHG-20261027-002 已入库，但它指向的证据文件同样不在库内，形成“文档在、证据不在”的悬空引用。

**当前行为**：把两份 JSON 的字节级副本归档到项目既有的证据目录 `Tools/MHW/`（该目录已有 19 个同类 `*.json` 被跟踪），并把两个脚本的默认输出路径改为该目录，后续重新生成会直接落在已跟踪位置。`Saved/` 下的原始输出保留未删，`Saved/` 仍整体忽略。

不采用 `git add -f` 强行跟踪 `Saved/` 内文件：被忽略目录内的文件无法用 `!` 规则反选，后续每次重新生成都要重复 `-f`，且 `Saved/` 本身就是可被引擎清理的目录，不适合作为唯一副本。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Tools/MHW/weapon-hit-volume-evidence.json` | 新增，97248 字节 | 武器碰撞静态取证结果副本（39 条动作碰撞轨、13 组几何参数、52 条攻击记录）；与 `Saved/` 原件 sha256 一致 |
| `Tools/MHW/weapon-collision-loader-chain.json` | 新增，3862 字节 | `.col` 加载链追踪结果副本（type 1 → `cCollNodePl`，读取链到 `0x1419c2fe0`）；与原件 sha256 一致 |
| `Scripts/MHWI/audit_weapon_hit_volume_evidence.py` | `DEFAULT_OUTPUT` | `Saved/MHWIRestoration/B19-20261026/…` → `Tools/MHW/weapon-hit-volume-evidence.json` |
| `Scripts/MHWI/trace_weapon_collision_loader.py` | `OUTPUT` | `Saved/MHWIRestoration/B19-20261026/…` → `Tools/MHW/weapon-collision-loader-chain.json` |
| `.gitignore` | `Saved/` 上方注释 | 说明被忽略目录内无法用 `!` 反选，入库证据请放 `Tools/MHW/`，防止同类问题复发 |
| `Docs/Changes/CHG-20261026-011-mhwi-weapon-collision-evidence.md` | 实际验证表·证据路径 | 改为指向 `Tools/MHW/` 副本，同时保留原始输出位置说明；测试结论未改 |
| `Docs/Changes/CHG-20261027-002-mhwi-collision-loader-trace.md` | 实际验证表·证据路径 | 同上 |

## 接口、事件与资源影响

无 C++/反射/蓝图/DataAsset/资产改动。两个脚本的默认输出路径变更：显式传入 `--output`（`audit_weapon_hit_volume_evidence.py`）或 `OUTPUT` 常量的旧调用方需注意落点变化；未改动任何函数签名或 JSON 结构。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `python -c "json.load(...)"` 解析两份 JSON | 本机仓库 Python | 通过；`weapon-hit-volume-evidence` 顶层键 `status/sources/join_summary/example/geometry_table/tracks/interpretation_limits/installed_game_override`；`weapon-collision-loader-chain` 顶层键 `status/source/native_code_executed/clnd_type_1/clgm_static_evidence/geometry_candidate/decision/scope` | 命令输出 |
| `sha256sum` 比对 `Saved/` 原件与 `Tools/MHW/` 副本 | 本机 | 两份均一致（`51980d78978d…`、`ec74876ed499…`），确认副本是字节级拷贝而非重新生成 | 命令输出 |
| `git check-ignore -v` | 本机 | 确认排除来源为 `.gitignore:9:Saved/` | 命令输出 |
| `python Scripts/Docs/check_docs.py` | 仓库文档检查 | PASS | 命令输出 |
| `git diff --check` | 本机 | 通过，无空白错误 | 命令输出 |

未执行：未重新运行两个取证脚本（需要指定游戏安装 `F:\PCprogram\Steam\steamapps\common\Monster Hunter World` 与固定版 EXE），因此本次只归档既有结果，不构成对取证结论的复现；未编译、未启动 UE、未 PIE —— 本次无 C++/资产改动，不需要。

## 风险、遗留与回退

- **数据性质未变**：归档的仍是静态取证结论。`weapon-hit-volume-evidence` 的 `interpretation_limits` 与 R18 的“形状/骨骼空间/运行时消费者未闭合”仍成立，不得据此认定武器碰撞已实现。
- **`Saved/` 仍是易失目录**：`Tools/MHW/` 副本现在是唯一受版本控制的副本；若脚本再次运行，需确认输出落在 `Tools/MHW/`。
- **同批次第三份证据未归档**：`Saved/MHWIRestoration/B19-20261026/equipment-ik-profile.json`（743 字节）属 B20/CHG-20261027-004 那批在途工作，本次未纳入。
- **回退**：删除 `Tools/MHW/` 下两份 JSON、还原两个脚本的输出常量和 `.gitignore` 注释、还原两处 CHG 证据路径即可；`Saved/` 原件未删除，数据可恢复。

## 已同步文档

- [CHG-20261026-011 武器碰撞静态取证](CHG-20261026-011-mhwi-weapon-collision-evidence.md)
- [CHG-20261027-002 碰撞加载工厂追踪](CHG-20261027-002-mhwi-collision-loader-trace.md)
- [记录索引](README.md)
