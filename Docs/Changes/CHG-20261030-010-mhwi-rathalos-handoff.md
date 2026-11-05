# CHG-20261030-010：新增火龙未解项交接文档

- 状态：completed（文档）
- 日期：2026-10-30
- 需求摘要：用户要把剩余未解项交给其他 AI 接手，需要一份自包含的交接文档。
- 关联：[数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)、[方案](../Plans/PLAN-20261030-003-mhwi-rathian-datamine.md)、[CHG-009](CHG-20261030-009-mhwi-pbc-actp2-probe.md)

## 原因与结果

剩余工作（`em_pbc` 语义、`actp2` 伤害）依赖大量试错经验，而这些经验散在 4 篇文档与三份变更记录里。新接手者若只读数据页，极可能重复两条已否决的路线（用 `shlp` 拿伤害、按 44 字节切 `em_pbc`）。

新增 [交接文档](../Plans/MHWI-Rathian-Datamine-Handoff.md)，按"能直接干活"组织：30 秒摘要 → 已完成且可复用的边界 → 三个未解项（含已确认的结构事实与建议下一步）→ **明确否决的路线表** → 环境与可复制命令 → 必须遵守的规则 → 什么算解出来。

关键是把负结果写成正面清单：`shlp` 无伤害字段、`44` 切分被排除、`em_dmg` 不是数值表、`Health 3000` 不是任务血量、不要直接采信 `00`=下位。

## 修改清单

| 文件完整路径 | 修改内容 |
| --- | --- |
| `Docs/Plans/MHWI-Rathian-Datamine-Handoff.md` | 新增交接文档 |
| `Docs/README.md` | 快速阅读表新增"接手火龙未解项"一行 |
| `Docs/Changes/README.md` | 新增本条索引 |

## 实际验证

| 操作 | 结果 |
| --- | --- |
| 文档内 commit/路径/SHA 逐项核对 | commit 原写漏末位 `c`，已按 `mhw-editor-sources.json` 修正为 `b6ff379b13079a4abb99490590fb05dfe6851bbc` |
| `python Scripts/Docs/check_docs.py` | 见下 |
| `git diff --check -- Docs` | 见下 |

未验证项：交接文档中的命令未在本轮重跑（与[流程页](../Reference/MHWI-Unpacking-Workflow.md)一致，均标注为参考命令）；文档不改变任何数据结论。

## 风险与回退

- 交接文档会随进展过期；后续批次应更新本文件或在其顶部注明被哪篇取代。
- 回退：删除该文档、`Docs/README.md` 对应行与本条记录。

## 已同步文档

- [火龙未解项交接](../Plans/MHWI-Rathian-Datamine-Handoff.md)
- [技术入口](../README.md)
- [记录索引](README.md)
