# CHG-20261103-002：外部评审采纳——fexty 条件映射复用、路线与时间表修订

- 状态：completed-scope（映射复用已实证；P0 基线提交待用户确认；实现批次未开始）
- 日期：2026-11-03
- 需求摘要：用户提交外部评审意见；要求先验证"Leviathon 能直接解决多少 BEH-01"。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261103-001](../Plans/PLAN-20261103-001-rathian-review-adoption.md)、[评审简报](../Reference/MHWI-Rathian-Review-Brief-20261103.md)。
- Git：工作区变更，未提交。

## 原因与结果

原行为：BEH-01 按"60 个条件函数全面逆向"规划；344 动作全量映射为目标；时间表 8–12 会话。

当前行为（本轮实测后修订）：

1. **fexty 复用实证**：`default.fexty`（Leviathon commit 1e647f08，本地缓存已有）解析出 45 个 functionType 定义；与本机 60 种 functionType 交叉：**27/58 条件类型命中（46.6%）、1786/2191 条件段使用（81.5%）**；参数形态全部自洽（0x6/0x8 距离、0x16 角度对、0x1E 怒、0x1F 疲、0x70 飞行、0xB8 等级、0x76 部位破坏）。首链冲撞分支 0x1F=fatigued 语义自洽（86 常态/87 疲劳变体）。工具：`Scripts/MHWI/map_thk_function_semantics.py`，产物 `Tools/MHW/rathian-thk-fexty-coverage-20261103.json`。
2. **BEH-03 路线打通**：0xB8=current_quest().is_rank → 可从 THK 等级门控反推下位可达动作，替代"344 全量"口径。
3. **评审工具核实**：`mhw-lmt-engine`（Nexus/wclbox 双源）存在——离线 LMT↔JSON 往返验证 + FSM 动作号→候选槽位；`wwiseutil` 存在（MHW modding wiki 收录）；`MHW-EFX-Editor` 未核实，标待验证。
4. **路线修订**：采纳评审 Phase 0–4；B1 只决定"做什么"，执行层统一由 ActionSpec 驱动；动作覆盖口径改为"任务内可达动作覆盖率"；证据记录增加五维（来源/验证状态/适用范围/具体证据/替换状态）；两处表述收紧（往返一致仅证结构处理；负结果为"已检查范围内未发现"）。

## 修改清单

| 文件 | 修改 | 效果 |
| --- | --- | --- |
| `Scripts/MHWI/map_thk_function_semantics.py` | 新增 | fexty↔functionType 覆盖映射（含条件口径统计） |
| `Tools/MHW/rathian-thk-fexty-coverage-20261103.json` | 新增 | 27/58 覆盖与逐项候选映射 |
| `Docs/Plans/PLAN-20261103-001-rathian-review-adoption.md` | 新增 | 修订路线/时间表/证据维度/ActionSpec |
| `Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md` | BEH-01/BEH-03 行更新 | 社区映射覆盖主干；LR 门控路线 |
| `Docs/Plans/MHWI-Rathian-VM-Semantics-Handoff.md` | 顶部更新注 | R1 降级为定向校验 |

## 接口、事件与资源影响

无代码/资产变更；未修改游戏安装。

## 实际验证

| 检查/命令 | 结果 |
| --- | --- |
| `python Scripts/MHWI/map_thk_function_semantics.py` | 条件覆盖率 27/58 类型、81.5% 使用；参数形态自洽 |
| 公开来源核实 | mhw-lmt-engine ✓、wwiseutil ✓、MHW-EFX-Editor 待验证 |
| `check_docs.py` / `git diff --check` | PASS（见汇总） |

## 风险、遗留与回退

- 社区命名仍为候选语义：27 类须逐项参数校验+定向运行观测后才可进忠实 profile。
- P0 基线提交未执行（涉及用户既有未提交修改分拣，等待用户确认）。
- 回退：删除新增脚本/JSON/PLAN 与三处文档更新即可。

## 已同步文档

[PLAN-20261103-001](../Plans/PLAN-20261103-001-rathian-review-adoption.md)、[核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[VM 交接](../Plans/MHWI-Rathian-VM-Semantics-Handoff.md)、[Plans 索引](../Plans/README.md)、[Changes 索引](README.md)。
