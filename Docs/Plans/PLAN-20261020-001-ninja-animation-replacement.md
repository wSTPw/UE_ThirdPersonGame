# PLAN-20261020-001：Ninja 动画替换

- 状态：implemented（资产制作与保存完成，按用户要求未做完工后验证）
- 日期：2026-10-20
- 用户需求：检查 UE MCP；将 `Content/ARPG_Ninja/Animations` 新动画替换到当前角色，完工后禁止验证。
- 关联模块 / 接口 / 问题：player-combat、character-actions；ACTION-*、COMBAT-*；R-MM-001。
- 实施记录：[CHG-20261020-001](../Changes/CHG-20261020-001-ninja-animation-replacement.md)。

## 现状与目标

修改前 MCP 已连接 IntroCpp UE5.8，桥接协议两端均为2、pluginStale=false。正式角色使用 YBot RootOn 骨架，ABP_Move 的三个移动分支使用 BS_Move、BS_LongSwordMove、BS_StaffMove。新 Ninja 动画使用独立的 UE4_Mannequin_Skeleton，不能直接替换 Skeleton 指针。

目标是将可对应的待机、行走、跑步和四段剑攻击重定向到 YBot，并接入现有 BlendSpace / Montage。保留原角色模型、动作组件和上半身 Slot 分层。新包缺少同语义动作时保留原动画并明确记录，不能用不相关动作冒充喝药。此次只替换实际使用的动画，包内未接入的攀爬、闪避等不新增玩法。

## 范围与验收标准

- 创建独立 Ninja→YBot IK Rig / Retargeter 与输出目录，保存源包原始资源。
- 替换三个移动 BlendSpace 的样本，增加行走速度层；长剑 Combo01..04 重新按新片段长度配置。
- 动画通知仍由 Montage 提交；连段 / 取消窗口和 ComboData.SubHits 数量随资源迁移。
- 施法若采用 Throw 动作作为抛射手势，明确它是近似表现；没有新喝药动作则保留现有 M_Drink。
- 用户明确禁止完工后验证：不执行构建、蓝图编译检查、PIE、自动化、文档检查、diff 检查或完成后的资产读回。修改过程中的参数校验、依赖读取与保存属于资源制作步骤，不报告为运行验证。

## 技术方案

使用 UE MCP 原生 IK 重定向工具，单独创建源 / 目标 Rig，按真实骨名设置 pelvis / Hips 为重定向根，root / Root 为根运动骨，身体与手指链显式映射；新命名姿态处理 UE4 A Pose 与 YBot T Pose 差异。IPC 资源供现有 CharacterMovement 驱动的移动分支；Rootmotion 版本保留为后续 MM 资源，正式 MM 不在此次自动开启。

输出放 `/Game/MyStuff/Animation/Ninja`。现有 BlendSpace 路径保持稳定。长剑 Montage 路径及 Combo01..04、Attack Slot 保持稳定；替换片段并重排节段、命中与动作窗口，连击数值配置同步迁移。火球保留 UpperBodyOnly Slot 和唯一 CastCommit。

## 接口与数据迁移

| 路径 / 接口 | 当前 | 目标 | 影响 |
| --- | --- | --- | --- |
| `/Game/MyStuff/Model/Robot/BS_Move` | 原基础移动样本 | Ninja 无武器待机 / 移动 | ABP 原分支继续使用 |
| `/Game/MyStuff/Model/Robot/BS_LongSwordMove`、`BS_StaffMove` | 原 SwordAnim 样本 | Ninja 持武器移动 | 原 WeaponAnimType 选择不变 |
| `/Game/MyStuff/Model/Robot/M_LongSwordAttack` | 原4片段 / 6命中 | Ninja ComboA1..4及匹配时间 | 同步 ComboData |
| ACTION 通知 / 请求 | 原 C++ 签名 | 不变 | 仅动画时序配置变化 |

## 实施步骤与依赖

1. 只读定位骨架、完整路径、现有引用和工具参数。
2. 备份本次覆盖的已有资源，记录初始 Git 状态。
3. 制作独立 IK 资产，重定向需要的片段。
4. 写入移动、攻击与匹配的施法引用、通知和窗口，保存目标资源。
5. 更新现状页、接口资产说明、模块索引和 CHG；完成后停止，不做验证。

## 验证计划

按用户指令本轮不安排完工后验证。仅记录制作命令返回与未覆盖内容，不沿用2026-10-19测试作为新资源通过的证据。

## 风险与回退

重定向姿态、握持位置、命中帧和移动步幅未经运行核对。已有用户修改包括两个原 Walk 动画，不覆盖它们。覆盖资源先复制到本轮 Saved 备份；回退时关闭编辑器并恢复该备份，只移除本轮新增资产，不回退整个工作区。

## 文档同步清单

Combat-AI、UI-Assets、Interfaces、modules.json、Known-Issues、Plans / Changes 索引及本轮 CHG。
