# CHG-20261019-003：动作管理审查与重构方案交付

- 状态：completed（分析和文档交付完成，玩法重构未实施）
- 日期：2026-10-19
- 需求摘要：用户对当前动作管理不满意，要求基于项目给出重构方案。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261019-003](../Plans/PLAN-20261019-003-character-action-refactor.md)；R-COMBAT-001..005、R-INV-004/005、COMBAT-001..006
- Git：工作区文档变更，未提交；保留此前已有源码、配置、Widget 和关卡修改。

## 原因与结果

本次检查当前玩家输入、攻击/连击、物品使用、装备回调、动画通知、属性事件与清理边界，并用 UE-MCP 只读核对相关 DataAsset 和 Montage。方案建议轻量统一动作组件、独立执行身份、统一阶段/取消/结束、有限输入缓冲，以及物品来源预约和结构化提交结果。完整 GAS 作为明确联网/技能/Buff需求下的替代路线。

仅新增方案和已知问题记录，没有创建动作 C++ 类、修改游戏行为、保存蓝图/动画/DataAsset，也没有把计划接口写为已实现 API。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Docs/Plans/PLAN-20261019-003-character-action-refactor.md` | draft 方案 | 当前证据、目标架构、生命周期、冲突规则、接口、阶段迁移与验收标准 |
| `Docs/Plans/README.md` | 方案索引 | 增加 draft 条目并澄清计划/实施状态 |
| `Docs/Known-Issues.md` | R-COMBAT-004/005 | 记录入口限制不一致、缺少实例身份和统一清理的静态风险 |
| `Docs/Systems/Combat-AI.md` | 方案导航 | 链接 draft 方案，当前实现描述保留 |
| `Docs/Changes/README.md` | 交付记录索引 | 本次分析与文档交付留痕 |

## 接口、事件与资源影响

无运行时接口或资源改动。拟定 ActionRequest/Execution/Snapshot/Reserve/Commit 接口仅存在于方案中；模块索引未新增不存在的系统。资产读取返回的 ComboData.WeaponAnimType `(INVALID)` 已在方案中列为工具/枚举值待交叉确认项，未据此自动修改资产。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `git status --short`、router、相关源码搜索/分段读取 | Windows，当前工作区 | 识别既有改动；核实输入/回调/Timer/物品提交路径 | 方案“现状与证据”中的符号和行号 |
| UE-MCP `blueprint.get_cdo_properties` | 已连接 UE5.8 编辑器，只读 | 核实 BP_MyPlayer 输入资产、AttackMontageMap | `/Game/MyStuff/BP/BP_MyPlayer` |
| UE-MCP `asset.read_properties/bulk_read_properties` | 同上，只读 | 核实长剑、火杖、HP/MP药和连击数据完整路径与引用 | `/Game/Data/Items`、`/Game/Data/ComboData/DA_LongSwordComboData` |
| UE-MCP `animation.read_montage` | 同上，只读 | 长剑4段6通知；火球1通知；Drink RateScale=2且1通知；三者无NotifyState | `/Game/MyStuff/Model/Robot/M_LongSwordAttack`、`M_Attack_Fireball`、`M_Drink` |
| 本机引擎源码核对和 Epic 官方文档查阅 | UE5.8 | 核实 MontageInstanceID 通知上下文与原生回调过滤机制；比较GAS职责 | 方案“技术参考” |
| `python Scripts/Docs/check_docs.py` | Windows / Python | PASS：30 个 Markdown、155 个本地链接、10 个模块及 editor snapshot JSON | 控制台 |
| `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` | Windows / Git，沿用本机 LFS filter-process 故障规避 | 退出码0；仅既有 LF→CRLF 提示 | 控制台 |

未执行编译或 PIE，因为本次只读审查和文档设计，没有玩法改动。本次列出的故障为静态发现/风险，不宣称已经运行复现；全部行为验收仍在方案中标为待实施验证。

## 风险、遗留与回退

完整 ABP Slot 链、全部蓝图对旧函数的引用及玩家死亡蓝图补充尚未逐图核对。实际操作手感需在实施 P0 建立基线。回退仅涉及本次新增方案/记录和相关文档条目，不改动此前已完成 UI 或升级工作。

## 已同步文档

- [战斗与AI现状页](../Systems/Combat-AI.md)
- [已知问题](../Known-Issues.md)
- [方案索引](../Plans/README.md)
- [变更记录索引](README.md)
