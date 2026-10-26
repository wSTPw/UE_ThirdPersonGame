# CHG-20261027-001：R06 / R28 / R30 动画全集覆盖处理与交接

- 状态：partial，R06确定性阻断已修复；R28/R30完成数据层与逐项处置，未实现全部运行覆盖
- 日期：2026-10-27（工作批次B19始于2026-10-26）
- 需求摘要：逐一处理R06/R28/R30的全部动画，不能遗漏；无法处理项注明位置和原因。后续用户要求“不验证，处理完成后交接”，因此交接前未再新增验证。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261026-006](../Plans/PLAN-20261026-006-mhwi-animation-coverage.md)、R06/R28/R30、A01/A04、R-COMBAT-012/014/016、R-ANIM-007/008、MHWI-015
- Git：工作区变更，未提交

## 原因与结果

本次先建立87项处置清单（R06 66、R28 11、R30 10），再实施确定性修复。审计发现R06的主要前置问题不是单纯缺资产，而是武器混合门控只接受`One0=1`，全部主段候选却为`One0=0`，导致动画在播放前被拒绝。R28六候选均有旧Sequence但没有正式过渡消费者；R30六条内部动画资产齐全，但正式DA只选择0–3，四链IK没有运行消费者。

**不能将本记录解释为“全部动画已接入或全部验证通过”。** 每项的当前处置见`Saved/MHWIRestoration/B19-20261026/animation-coverage.json`和`.md`；`Tools/MHW/animation-coverage-decisions.json`保存可复核的状态覆盖。

## R06：已实施的修复与保留缺口

| 修改 | 实际结果 | 边界 |
| --- | --- | --- |
| `ApplyNativeBlend`增加武器`One0=0`的ProjectAdaptation后备 | 不再于播放前失败；以插值帧/60作为项目UE BlendIn秒数，NativeBlendFrames=-1，不启用原生mode1代理或自动尾淡出 | 原生武器mode0 MotionTree/request仍未实现，后备不冒称原版求解 |
| 真实来源的输入分派先于普通Flinch锁 | Impact只允许`ResolveNativeSourceInput`已有的合法恢复出口；其他输入和其他控制锁仍拒绝 | 不全面放开受击输入，不伪造其他来源身份 |
| 菜单阻断 | `SetInputBlocked(true)`清`NativeSourceInput`，`StartResolvedMove`也拒绝阻断期内部提交 | Move/Look完整菜单策略不在本批扩建 |

此前已执行的验证（不是交接前新增验证）：两次UE5.8 Editor构建均`Result: Succeeded`；`pie_r06_repairs.py`首次因结束边界断言误报，修正断言后**14/14通过**，覆盖武器Montage播放、SpiritI入口、受击合法恢复/非法拒绝、StepSlash提交和菜单清理。报告为`Saved/MHWIRestoration/B19-20261026/PIE-r06-repairs.json`，构建日志为同目录`build-r06.log`与`build-animation.log`。

保留项：

- `R06-N86-P0`：原图无入边/0记录，正确处置是继续不可达，不制造入口。
- `R06-N53-P0`、`R06-N60-P0/P1`：node0/node26完整来源拥有者未覆盖，不能因一条恢复路径通过就宣称54/12个身份全覆盖。
- `R06-EXTRA-W03_00_332/333/334`：缺Action78/node51真实前置，保持资产但不别名接入。
- `R06-COMMON-181/182`：缺合格源上下文/入口，未导入、未伪造。
- 其余32引用与32新增片段：代码阻断已修，但没有逐条运行覆盖；原生mode0、R07精确输入及R24/R25/R28依赖继续开放。

## R28：已完成的资产/数据层与未接入项

- 六候选005/006/007/008/014/015均经UE读回：正确猎人Skeleton，时长分别1.0000/1.1667/1.1667/0.9500/1.0500/0.9500秒，Root Motion开启且REF_POSE锁根。原始LMT与游戏安装当前不可用，因此没有把这六条提升为NativeFidelity合格平行资产。
- `UMHWIAnimInstance`新增只读`bAccelerating/bDecelerating/bJustLanded/TurnDirection`及PreviousVelocity，只提供项目状态事实，不改CharacterMovement、输入或既有BlendSpace。
- 预览脚本实际播放六段并产生18张不同哈希截图；随后因磁盘写满，临时PNG已删除。`R28Preview/report.json`已标记图片未保留和`visual_semantics_confirmed=false`，不得把历史路径当成保留证据或最终语义确认。

未接入：`/Game/MHWI/Animations/LongSword/A_w03_00_005/006/007/008/014/015`均没有新增ABP过渡状态。尤其006/007左右转身未完成可靠分配，014/015落地语义也未形成最终映射。`ABP_MHWI_Hunter`未被本批保存修改；原有两张BlendSpace、DA六字段和移动物理保持不变。五个既有基础循环只保留现状，不宣称新增回归完成。

## R30：选择覆盖与IK数据层

- 正式DA的32个招式已枚举：`wg03_00`选择值只有0/1/2/3。004/005没有任何事件或默认选择，正确处置是保留资产、明确无原生入口，不人为添加触发。
- 新增`MHWIEquipmentIKProfile.h`：登记四链root/mid/end、ComponentSpace偏移、足部探测和Alpha配置类型。
- `UMHWIAnimInstance`新增四链目标与Alpha快照：右握柄、特殊纳刀左鞘口和双脚地面检测均在游戏线程生成；普通攻击/空中/死亡门控不启用IK。`FMHWIWeaponAttachmentRuntime::AnimatedGripPoint`改为公共只读计算入口，装配算法本身未改。

未完成：`/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile`尚未创建，`/Game/MHWI/Blueprints/ABP_MHWI_Hunter`尚未写入TwoBoneIK节点，因此四条链仍无实际运行消费者。`author_equipment_ik.py`只是待执行制作入口，不是已执行资产迁移。原生solver坐标、极向、限位、manager字段和CTM仍未解码；项目数据层不能称为R30完成。

## 修改清单

| 文件/资产完整路径 | 修改原因与效果 |
| --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacterLinkMotion.cpp` | 武器mode0项目混合后备，覆盖直接主段/连接前段/连接后主段/来源四个调用点 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | 来源输入分派、菜单清缓存、内部提交阻断 |
| `Source/IntroCpp/MHWI/MHWICharacterNativeSources.cpp` | 仅允许真实Impact合法恢复出口，保留其他控制锁 |
| `Source/IntroCpp/MHWI/MHWIAnimInstance.h/.cpp` | R28只读移动事实；R30四链目标/Alpha快照 |
| `Source/IntroCpp/MHWI/MHWIWeaponAttachment.h` | 公开项目握点计算，不修改装配行为 |
| `Source/IntroCpp/MHWI/MHWIEquipmentIKProfile.h` | 新增项目IK Profile类型，未创建对应资产 |
| `Scripts/MHWI/audit_animation_coverage.py`、`Tools/MHW/animation-coverage-decisions.json` | 87项全集、状态和未处理原因台账 |
| `Scripts/MHWI/pie_r06_repairs.py` | R06代表性运行用例；已执行14项通过 |
| `Scripts/MHWI/pie_r28_preview.py` | 六候选真实播放预览入口；临时图片已清理 |
| `Scripts/MHWI/author_equipment_ik.py` | Profile/ABP CDO待执行制作入口，未执行 |
| `Scripts/MHWI/mcp_animation.mjs` | 编辑器驱动入口；依赖已清理，复用前需恢复 |

没有保存Content资产、DA、Montage、Sequence、BlendSpace、蓝图或地图。ABP只在`Saved/MHWIRestoration/B19-20261026/Backup`保留修改前备份。

## 接口、事件与资源影响

新增MHWI-015只读动画状态/IK快照接口；既有`RequestInput`签名、公开战斗返回语义和六条武器SingleNode事件未变。`ApplyNativeBlend`只扩展后备，不放宽`ResolveDirectBlendSettings`对原生合格路径的判断。R28/R30新增UPROPERTY需要后续构建和蓝图读回才能投入运行；本批交接不把源码存在当成资产生效。

## 实际验证与交接前停止项

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| R06构建 | Succeeded | `Saved/MHWIRestoration/B19-20261026/build-r06.log` |
| R28/R30数据层构建 | Succeeded | `Saved/MHWIRestoration/B19-20261026/build-animation.log` |
| R06代表性PIE | 14/14通过 | `Saved/MHWIRestoration/B19-20261026/PIE-r06-repairs.json` |
| R28六候选UE读回 | Skeleton/时长/RootMotion/REF_POSE一致 | `Saved/MHWIRestoration/B19-20261026/editor-api.json` |
| R30正式DA枚举 | 32招，选择值0/1/2/3 | `Saved/MHWIRestoration/B19-20261026/weapon-motion-coverage.json` |
| 覆盖台账 | 87项，无缺`.uasset`；状态各异，不是87项通过 | `Saved/MHWIRestoration/B19-20261026/animation-coverage.json` |
| 交接前新增编译/PIE/截图/check_docs/git diff --check | **按用户“不验证”要求未再执行** | 无 |

磁盘曾降至0字节并造成一次`ENOSPC`。仅清理本批临时预览PNG和本次npm生成的`Tools/ue-mcp/node_modules`（约33MB，可经`npm ci --prefix Tools/ue-mcp --ignore-scripts --no-audit --no-fund`恢复），未删除历史日志、工程资产、源码、文档或`.workbuddy`。空间恢复后完成交接记录。编辑器当前未保持运行。

## 风险、遗留与回退

- 最大风险是把“后备能播放”写成“原生mode0完成”、把“Profile类型存在”写成“四链IK生效”、把“Sequence存在”写成“过渡已接入”。交接文档均按未实现范围保留状态。
- 源码修改前备份位于`Saved/MHWIRestoration/B19-20261026/Backup/Source/IntroCpp/MHWI`；ABP备份位于同目录`Backup/Content/MHWI/Blueprints`。按B19差异回退，不覆盖B14/B15/B16。
- 后续如继续，顺序应为：恢复MCP依赖→R28确认语义并接ABP→执行R30 Profile/ABP制作→逐条PIE，而不是把本批未做项标为完成。

## 已同步文档

[方案](../Plans/PLAN-20261026-006-mhwi-animation-coverage.md)、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[连接台账](../Plans/MHWI-Connector-Progress.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[方案索引](../Plans/README.md)、[记录索引](README.md)及2026-10-27工作日志。
