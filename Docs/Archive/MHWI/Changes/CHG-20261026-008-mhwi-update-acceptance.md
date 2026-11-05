# CHG-20261026-008：MHWI B13/B14/B15更新验收

- 状态：completed，审查及文档更新完成；整体交付不通过
- 日期：2026-10-26
- 需求摘要：验收更新工作，运行调试继续由用户操作。
- 关联：PLAN-20261026-002/003；R10/R11/R13/R16/R19/R21/R31/R32；R-COMBAT-014～019。
- Git：审查基线`c09f248`，本次文档工作区变更未提交。

## 原因与结果

B14/B15及编译修复已提交，现状文档仍大量停留在B13“玩法未改”和B15“未编译”。本轮按当前源码及固定字节复核：B15键盘静态49项与B13初始证据重建通过，历史编译成功；B14正式DA仍与B12逐字节一致、缺迁移保存报告，登龙一次接触仅入队一段。新增验收A05/A06并保留A01、手柄A02、A04，整体验收不通过。

## 修改清单

| 文件/符号 | 原因与效果 |
| --- | --- |
| `Docs/Reference/MHWI-Acceptance-Update-20261026.md` | 当前验收、两项P1、复查证据及更正后的用户运行标准 |
| `Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Systems/MHWI-LongSword.md` | 新增当前裁决与B14实施边界，保留历史批次原意 |
| `Docs/Known-Issues.md` | R-COMBAT-017/018按当前源码/资产更新；新增019记录登龙补排缺失 |
| `Docs/README.md`、`Docs/Reference/MHWI-Acceptance-20261026.md`、方案/变更索引 | 连接最新结论，防止使用旧U06/U07预期；登记B14方案实际状态 |

## 接口、事件与资源影响

无。未修改C++、脚本实现、Content、蓝图、DA、Montage、地图或接口签名；未启动/关闭编辑器。开始时工作区干净。当前DA与B12指纹一致，只据相同字节的历史快照判断旧窗口，未冒充此次UE资产属性读取。

## 实际验证

| 命令/检查 | 实际结果 | 证据 |
| --- | --- | --- |
| `python -B Scripts/MHWI/build_outstanding_evidence.py` | PASS：18函数、113动作、18资源；不含19函数续查统一重建 | `Saved/MHWIRestoration/Acceptance-Update-20261026/b13-rebuild.json` |
| `verify_keyboard_adaptation.main()`，报告重定向 | PASS：49项静态/模型，未改断言 | 同目录`keyboard-static.json` |
| `verify_evidenced_mechanics.py --da <B14 authored.json>` | FAIL：缺正式保存报告，12项源值检查后返回1 | 同目录`b14-snapshot.json` |
| 当前源码/DA指纹、Git跟踪数量、历史构建日志只读 | DA与B12一致；构建历史Succeeded/20.08秒；四目录已有跟踪文件 | 同目录`offline-evidence.json`、`historical-build.txt` |

`python -B Scripts/Docs/check_docs.py`通过：117份Markdown、990条本地链接、12模块；`git diff --check`通过。新增文件另做尾空白检查通过；这些检查不验证玩法。未重新编译、运行游戏/UE/PIE、保存或迁移资产。首次验收51项、B15历史结果均未冒充本轮玩法验证。

## 风险、遗留与回退

A05/A06需开发及正式DA迁移后复验；A01、手柄A02、A04、十项完整取证及B14缺失CHG仍开放。35项总状态不提升。原验收U06/U07过时预期由最新报告覆盖，历史记录不重写。

回退仅恢复本次修改文档并删除两份新增文档；改前备份在`Saved/MHWIRestoration/Acceptance-Update-20261026/Backup`。本次无玩法/资产变更可回退，不撤销B14/B15或用户提交。

## 已同步文档

[最新验收](../Reference/MHWI-Acceptance-Update-20261026.md)、[首次验收入口](../Reference/MHWI-Acceptance-20261026.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[系统页](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[技术入口](../README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
