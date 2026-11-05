# CHG-20261102-001：雌火龙方案完整性核对、音画细案补全与四模块并行实施

- 状态：completed-scope（本轮四工作包与文档交付完成；P1 关联表多数环节按证据保持 unknown，原作语义未闭合）
- 日期：2026-11-02
- 需求摘要：用户要求核对雌火龙还原方案四大板块（行为逻辑/数值/动画模型/音效特效）完整性，缺失项先列清单再补全；确认后按模块分派子代理并行实施，汇总进度与遗留。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md)、PLAN-20261031-002/003~007、ADR-0002；核对结论见[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)。
- Git：工作区变更，未提交。

## 原因与结果

静态核对结论：方案文档结构完整（所有缺口有编号工作包与通过门）；音效与特效板块最薄（仅 raw 文件，零清点/零映射/零 UE 资产）；另有首链实施无 CHG、索引缺行等文档缺口。本轮按用户流程执行：核对→补全→四模块并行实施→汇总。

结果：

1. 核对与补全：新增完整性核对页（四大板块缺失项编号 BEH/NUM/ANIM/AV + 文档缺口 DOC-01~05）、音画配置细案（PLAN-20261102-001 A5x 节，含事件映射表 schema 与 Epic UE5.8 官方来源）、补录 [CHG-20261031-003](CHG-20261031-003-rathian-first-chain.md)、修 Handoff 标题笔误、补 Plans/Changes 索引与 modules.json 首链模块登记。
2. P1 行为链路（W1）：5 动作关联表落地。动作 83（BITE）全链闭合：ACTP2 #15 → LMT bank2/slot1（原生 MOTION_ENCODING 常量 0x2001 解码）→ `/Game/MHWI/Rathalos/Animations/A_em001_02_001`（2.1667s）→ COL uid=32/attack_index=7（窗口 0–23 帧候选）；75/76/86/87 的 LMT/UE/COL 无逐动作证据，保持 unknown。
3. P2 音画（W3/E08）：73/73 文件路径/尺寸/SHA 与既有清单一致；395 个唯一事件名候选（VFX 353/声音 8/任务 34，均 raw）；NBNK 未解码；事件映射表骨架落地（395 候选行+8 必需事件 unknown 行）。
4. P3 数值（W4/C3.1）：分段结算原型脚本落地，肉质表与发怒 ×1.15 为 evidenced，斩味/技能/任务倍率/取整 unavailable 显式跳过；样例输出 MV=30 两例（21.0 / 24.15 未取整，工程样例非原作期望）。
5. P4 动画（W3/A0）：848/848 源映射表落地（12 有效 bank，qualification 全 unknown）；chain 证据无行级 bank/slot 映射字段，5 动作 linked_native_actions 均未回填（不猜测）。
6. 构建验证：首链 1546 行代码 UE5.8 编译链接**通过**。修复两处：`MHWIRathianFirstChainPawn.cpp(32)` 旧成员名 `bUseUpdateRateOptimizations`→`bEnableUpdateRateOptimizations`（UE5.8 SkinnedMeshComponent.h:933）；陈旧 PDB/lib（LNK1201/LNK1136）清除后链接成功。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md` | 新增 | 四大板块完整性核对与缺失项清单 |
| `Docs/Plans/PLAN-20261102-001-rathian-completeness-parallel.md` | 新增 | 本轮方案+音画细案 A5x+工作包定义 |
| `Docs/Changes/CHG-20261031-003-rathian-first-chain.md` | 新增（补录） | 首链实施记录（依既有证据静态核对） |
| `Docs/Plans/MHWI-Rathian-Datamine-Handoff.md` | 标题笔误"雌雌火龙"→"雌火龙" | DOC-04 修复 |
| `Docs/Plans/README.md`、`Docs/Changes/README.md`、`Docs/Reference/modules.json` | 索引行+模块登记 | DOC-02/03 修复 |
| `Source/IntroCpp/MHWI/Monsters/MHWIRathianFirstChainPawn.cpp` | 第 32 行 URO 成员名 | UE5.8 编译修复 |
| `Scripts/MHWI/correlate_rathian_first_chain_actions.py` | 新增（P1） | 5 动作关联表构建+自检；self-check 改用临时输出不触碰正式交付 |
| `Scripts/MHWI/rathian_damage_pipeline_stages.py` | 新增（P3） | 分段结算原型 |
| `Scripts/MHWI/build_rathian_source_motion_map.py` | 新增（P4） | 源映射表构建 |
| `Saved/MHWI-Rathian-FirstChain/action-asset-correlation-20261102.json` | 新增 35,189 B | P1 产出（5 行，逐行 evidence） |
| `Saved/MHWI-Rathian-FirstChain/damage-pipeline-sample-20261102.json` | 新增 | P3 样例输出 |
| `Tools/MHW/rathian-audio-vfx-inventory-20261102.json` | 新增 | P2 清点（73 文件+395 候选） |
| `Tools/MHW/rathian-source-motion-map-20261102.json` | 新增 329,205 B | P4 映射（848 行） |
| `Docs/Reference/MHWI-Rathian-AudioVFX-Map-20261102.md` | 新增 | P2 映射表骨架 |

## 接口、事件与资源影响

无既有公开签名/蓝图/DA 变更。新增三个独立脚本与四个数据文件；`Content/`、848 动画、太刀与训练场资产未动。用户既有未提交修改（太刀 C++/DA/地图等）保持原样。P2 产出为只读清点，raw 文件零写入。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| UE5.8 构建 IntroCppEditor Win64 Development | 本机 UE5.8 | 首次失败 C2039→修复后链接失败 LNK1201/1136→清陈旧 PDB/lib 后 **Result: Succeeded**（4.69s 增量） | `Saved/MHWI-Rathian-FirstChain/build-introcppeditor-20261102.log` |
| P1 自检 | Python | 3/3 通过（CRC 篡改拒绝、常量解码一致性、unknown 纪律）；修复后两连跑通过；json.load 复核 5/5 | `action-asset-correlation-20261102.json` |
| P2 核对 | Python 只读 | 73/73 路径/尺寸/SHA 一致；check_docs 新 md 零链接错误 | `rathian-audio-vfx-inventory-20261102.json` |
| P3 自检 | Python | PASS；两连跑输出逐字节一致 | `damage-pipeline-sample-20261102.json` |
| P4 自检 | Python | 848/848、字段完整、无重复 (bank,slot) | `rathian-source-motion-map-20261102.json` |
| 文档检查 | `python Scripts/Docs/check_docs.py`；`git diff --check` | CHG-20261102-001 落盘后 0 错误；空白检查通过 | 本记录 |
| PIE/原作对照/编辑器资产读回 | — | 未执行（编辑器未接、原作未启动；属后续批次门） | — |

## 风险、遗留与回退

遗留（对应核对页编号）：BEH-01~05（THK VM 语义、原生注册表、LR 资格、优先级表、其余链路）；NUM-01~06（任务倍率、公式、部位映射、PBC 耐久、气绝三套语义、断尾后毒）；ANIM-02~06（播放层、破坏映射、_fs 语义、染色/LOD、原作对照）；AV-03~06（NBNK/EFX 解码、UE 资产、镜头证据）。P1 中 75/76/86/87 的 LMT/UE/COL、P4 的行级动作关联均因证据缺失保持 unknown，后续取证闭合后由脚本重跑补齐（脚本已支持显式字段检测）。

回退：删除上表新增文件与文档行即完全回退本轮；`MHWIRathianFirstChainPawn.cpp` 的单行改名可回退但会导致 UE5.8 编译失败，不建议。构建日志与 PDB 清理不影响任何用户数据。

## 已同步文档

[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[Plans 索引](../Plans/README.md)、[Changes 索引](README.md)、[modules.json](../Reference/modules.json)、[PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md) 状态、[CHG-20261031-003](CHG-20261031-003-rathian-first-chain.md)。
