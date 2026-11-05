# CHG-20261031-003：雌火龙首条 THK→动作→移动→碰撞链路实施（补录）

- 状态：partial（链路代码与静态取证已落地；构建/PIE/原作对照未通过，VM 语义未闭合）
- 日期：2026-10-31（实施批次）；2026-11-02 补录。补录依据既有证据文件与源码静态核对，未重跑解析。
- 需求摘要：按用户已选技术组合（1C 原THK规则驱动/2B 原作时间轴/3B Pawn+专用Movement/4B 原COL骨映射+UE连续查询/5A 专用C++结算+Attribute宿主/6B 源数据转换流水线/7B 静态分析+受控对照），实施 [PLAN-20261031-007](../Plans/PLAN-20261031-007-rathian-first-chain.md) 首条验证链路。
- 关联 PLAN / ADR / 问题 / 接口 ID：PLAN-007、[ADR-0002](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md)、R-DATA-003/004。
- Git：工作区变更，未提交。

## 原因与结果

PLAN-007 要求"实施记录：后续新增 CHG-20261031-003"；该记录此前缺失，本文档按既有证据补录。

结果（静态发现与既有证据）：

1. THK 解析资格**通过**：Leviathon 固定 commit `1e647f08`，105 THK/2 thklst 全量解析，1795 节点/13015 段字节重编码一致；负例自检（signature/version/node_pointer/segment_count/truncated_core 损坏样本）全部正确拒绝。边界：格式一致≠VM/业务语义。
2. 首链候选已提取（`Tools/MHW/rathian-thk-chain-evidence.json`）：咬击 `ACTION::BITE`(id 83, thklst#55/node200, ACTP2 #15)、冲撞分支 `DASH_BITE2`(86)/`DASH_BITE_TIRED`(87, if functionType0x1f 二选一)、转尾 `ROLLING_TAIL_ATTACK2_L/R`(75/76)；5 动作完成 ACTP2 记录关联，调用方节点/源偏移可追。
3. 原生 VM 关键地址已离线 hash 锁定提取（vm_tick 0x1423fe8d0 等，仅分析字节，未执行原生代码）。
4. 首链 UE 运行代码落地 `Source/IntroCpp/MHWI/Monsters/`（见下表），独立入口，不改旧 EnemyBase/训练场。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/Monsters/MHWIRathianThkExecutor.h/.cpp` | `FMHWIRathianThkInstruction/Program/QueryResult/Decision`、`FMHWIRathianThkExecutor`（非 UObject） | THK 字节码执行器：拒绝未知指令/旧身份，受控执行已证节点链 |
| `Source/IntroCpp/MHWI/Monsters/MHWIRathianSourceMovementComponent.h/.cpp` | `UMHWIRathianSourceMovementComponent : UPawnMovementComponent`、`FMHWIRathianSourceMotionSample`、`FMHWIRathianQualifiedSourceMotion` | Pawn 专用移动：消费外部原时钟与资格确认的原轨，位移单次消费 |
| `Source/IntroCpp/MHWI/Monsters/MHWIRathianSourceCollisionComponent.h/.cpp` | `UMHWIRathianSourceCollisionComponent : UActorComponent`、`FMHWIRathianSourceContact` | 源碰撞：按传入前后时间产出接触候选，不自主 Tick 重算 |
| `Source/IntroCpp/MHWI/Monsters/MHWIRathianFirstChainPawn.h/.cpp` | `AMHWIRathianFirstChainPawn : APawn` | 首链验证 Pawn：装配骨架/Movement/Collision，动作执行闭环 |
| `Source/IntroCpp/MHWI/Monsters/MHWIRathianFirstChainData.h` | `UMHWIRathianFirstChainData : UDataAsset`（BlueprintType） | 首链数据资产类型定义 |
| `Scripts/MHWI/extract_rathian_thk_chain.py` | THK/thklst→链路提取（Leviathon 驱动） | 产出链证据 JSON |
| `Scripts/MHWI/extract_rathian_chain_motion.py`、`extract_rathian_chain_collision.py` | 链路动作/碰撞侧提取 | 支撑 action→LMT/COL 关联 |
| `Tools/MHW/rathian-thk-chain-evidence.json` | 证据文件（794KB：sources/counts/qualification/thklst/action_correlations/first_chain/tables/normal_form/unresolved/self_checks/native） | 紧凑证据与来源 hash |
| `Saved/MHWI-Rathian-FirstChain/`（Leviathon/THK/Dependencies，忽略目录） | construct-2.10.70、bite-normal-form.json、thk-all-raw.json | 隔离工作区，不随仓库交接 |

## 接口、事件与资源影响

新增独立入口，不改既有公开签名：旧 `EnemyBase/EnemyAIController`、`AMHWICharacter::SweepWindow/EmitDelayedShell`、`UAttributeComponent::ApplyDamage` 均未动。`UMHWIRathianFirstChainData` 为新 UDataAsset 类型；无 UE 资产保存记录，蓝图/DA 配置与读回待实施批次。`Source/IntroCpp/MHWI/Monsters/` 为新编译单元（Build.cs 无显式排除即纳入默认模块编译）。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| THK 解析资格（含负例自检） | 离线 Python+Leviathon 1e647f08 | 通过：105/2 文件、13015 段重编码一致；5 类损坏样本正确拒绝 | `Tools/MHW/rathian-thk-chain-evidence.json` `qualification/self_checks` |
| 动作关联 | 离线静态 | 5 动作（75/76/83/86/87）ACTP2 记录唯一匹配；资格=维护者历史 ActionDump+CRC，当前注册表另证 | 同上 `action_correlations` |
| UE 构建（IntroCppEditor） | UE 5.8 | **补录时未执行**；2026-11-02 由 [PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md) 主代理补跑，结果见其 CHG | — |
| PIE/原作对照 | — | 未执行（编辑器未接、原作未启动） | — |

## 风险、遗留与回退

- 遗留：THK 条件函数语义（`functionType0x1f` 等）、当前原生动作注册表、LR 资格、COL 几何/骨映射闭合、任务倍率与最终伤害（对应核对页 BEH-01~05、NUM-01~02）。
- 回退：删除 `Source/IntroCpp/MHWI/Monsters/`、三个提取脚本与证据 JSON、`Saved/MHWI-Rathian-FirstChain/`；不影响旧训练场/太刀/848 动画。提取产物可保留作证据。
- VM 执行器只运行"已证节点链"，未知指令拒绝；不宣称原作自动决策等价。

## 已同步文档

补录时同步：[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[Plans 索引](../Plans/README.md)（补 PLAN-007 行）、`Docs/Reference/modules.json`（Monsters 入口）、[Known-Issues](../Known-Issues.md) 如有新条目。本 CHG 为补录，PLAN-007 与 CHG-20261031-002 原文保留。
