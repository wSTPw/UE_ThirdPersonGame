# 项目导航

> 本文件是 Obsidian vault 首页，仅用于导航，不承载技术内容。项目规范见 [AGENTS.md](AGENTS.md)，技术文档入口见 [Docs/README.md](Docs/README.md)。

## 常用入口

| 我想… | 去哪 |
| --- | --- |
| 接手项目、按任务找文档 | [Docs/README.md](Docs/README.md)（任务路由表） |
| 看 MHWI 现在做到哪一步 | [MHWI 当前开发计划](Docs/Plans/MHWI-Current.md) |
| 看太刀系统现状 | [MHWI 太刀训练模组](Docs/Systems/MHWI-LongSword.md) |
| 看雌火龙现状 | [MHWI 雌火龙](Docs/Systems/MHWI-Rathian.md) |
| 查太刀数值/挂接/碰撞结论 | [太刀取证总账](Docs/Reference/MHWI-LongSword-Evidence.md) |
| 查雌火龙数据/AI/动画结论 | [雌火龙取证总账](Docs/Reference/MHWI-Rathian-Evidence.md) |
| 查解包流程与数据 | [解包数据与工具链](Docs/Systems/MHWI-Unpack-Data.md) |
| 查已知问题 | [Known-Issues](Docs/Known-Issues.md) |
| 查最近改动 | [变更记录索引](Docs/Changes/README.md) |
| 查接口契约 | [Interfaces](Docs/Interfaces.md) |
| 查已归档的历史 | [Archive](Docs/Archive/README.md)（只读，不作现状依据） |

## Docs 目录地图

- `Docs/Systems/` — 系统现状：太刀、雌火龙、背包、战斗 AI、UI 等
- `Docs/Reference/` — 取证结论总账、模块索引、编辑器快照
- `Docs/Plans/` — 活跃方案（当前只有 MHWI-Current）
- `Docs/Changes/` — 最近 5 条变更记录
- `Docs/Decisions/` — 架构决策记录（ADR）
- `Docs/Templates/` — 文档模板
- `Docs/Archive/` — 冻结历史（MHWI 与 Legacy 两个分区）

## 使用约定

- 现状写 `Systems/`，结论写 `Reference/`，过程写 `Changes/`，计划写 `Plans/`。**不要把批次流水账塞进现状页。**
- 报告被推翻时直接修正主文档并留一条 `Changes/`，不要把新旧结论并列堆在同一页。
- 完成的方案移入 `Docs/Archive/`，`Plans/` 只留活跃项。
- 新文档命名遵循 `AGENTS.md`（`PLAN-`/`CHG-YYYYMMDD-NNN-主题`）。
- 链接用相对 Markdown 链接；改完运行 `python Scripts/Docs/check_docs.py`。
- 以下目录已从 Obsidian 搜索与图谱中排除：Content、Binaries、Intermediate、Saved、DerivedDataCache、Config、.vs、Plugins、ArtSource、Tools、Source、C++ Source、.workbuddy。
- 解包工具文档在 `Tools/MHW/README.md`（已排除目录，链接仍可跳转）。
