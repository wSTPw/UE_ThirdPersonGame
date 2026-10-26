# CHG-20261020-002：Ninja Root Motion 适配

- 状态：completed（资源与蓝图制作保存完成，未经完工后验证）
- 日期：2026-10-20
- 需求摘要：动画使用Root Motion版本并适配；沿用上一轮“完工后禁止验证”。
- 关联：[PLAN-20261020-002](../Plans/PLAN-20261020-002-ninja-root-motion.md)、ACTION-002/004、R-ANIM-001、R-MM-001。
- Git：工作区变更，未提交。

## 原因与结果

上一轮接入IPC移动，攻击锁根但不提取。此次切换18条真正命名为Rootmotion的移动源资源，重定向到YBot，启用根运动提取；原攻击轨迹也交给CharacterMovement移动胶囊。ABP此前用实际Velocity决定播放速度，Root Motion在静止时可能无法起步，所以改为移动意图驱动，并保留模拟摇杆力度与动作/UI/死亡输入限制。

## 修改清单

| 路径 | 修改 |
| --- | --- |
| `/Game/MyStuff/Animation/Ninja/RootMotion` | 新增18条Sequence：8方向Walk/Run与无武器正向Walk/Run，源为 `/Game/ARPG_Ninja/Animations/ARPG_Ninja_Anim_UE_*_Rootmotion`，输出同名加_YBot |
| `/Game/MyStuff/Animation/Ninja/Sequences/ARPG_Ninja_Anim_UE_Idle1_YBot`、`Idle2_YBot`、`Idle_no_weapon_YBot`（共同前缀同上） | 待机输出启用根提取，零轨迹不人为添加位移 |
| 同目录 `ARPG_Ninja_Anim_UE_Attack_ComboA1_YBot`..`Attack_ComboA4_YBot`、`ARPG_Ninja_Anim_UE_Throw_A_YBot` | 从强制锁根且不提取，改为提取真实Root轨迹 |
| 上述26条正式Ninja Sequence | bEnableRootMotion=true、bForceRootLock=false、RootMotionRootLock=AnimFirstFrame |
| `/Game/MyStuff/Model/Robot/BS_Move`、`BS_LongSwordMove`、`BS_StaffMove` | 将现有IPC移动样本引用换为Rootmotion；保留各27样本、方向/速度坐标及Wrap |
| `/Game/MyStuff/Model/Robot/ABP_Move` | RootMotionFromEverything；移除GetVelocity选片源，增加快照拆分、输入力度与SafeDivide；保留状态机及Slot |
| [NinjaRootMotion-20261020.json](../../ArtSource/Animation/NinjaRootMotion-20261020.json) | 当前完整资源映射、根设置、81样本、蓝图节点ID及公式 |

共新增18个UE资产，覆盖12个既有UE资产（ABP、3个BS、8个旧Ninja输出）。原包、IPC输出、三个IK资产、Montage通知/窗口和ComboData伤害配置未改。攻击自身的真实根位移现在生效，命中位置随胶囊改变；不是只变视觉姿态。

## 接口与数据影响

C++及反射签名不变。蓝图Speed现为：

```text
lengthXY(DesiredVelocity)
    * clamp(SafeDivide(lengthXY(GetLastMovementInputVector()), Action.MoveScale), 0, 1)
```

Direction用DesiredVelocity与ActorRotation计算。现有NativeUpdateAnimation已将动作许可与MoveScale放进DesiredVelocity；Move入口又缩放输入，故输入力度先除MoveScale，避免0.5变成0.25。SafeDivide在0时返回0。速度坐标175/525用于选走跑，真实速度由Root轨迹决定；MoveScale控制主动输入/底层走跑，不是攻击根位移的缩放器。

CharacterMovement负责消费根运动、碰撞及物理模式；本轮没有手动SetActorLocation叠加轨迹。Root Motion不是Motion Matching，Schema/Database仍未创建。

## 制作证据与未验证项

| 操作 | 实际结果 |
| --- | --- |
| 修改前MCP及依赖读取 | 连接当前IntroCpp UE5.8；RootMotionMode原为RootMotionFromMontagesOnly，ABP事件图原为GetVelocity，BS各27样本 |
| 原生batch_retarget_animations | requested/created=18/18；目标20条链全部映射，输出保存成功 |
| bulk_set_properties根提取制作 | 26资产、78提交属性；26保存成功、0失败；52个实际变更属性，其余已为目标值 |
| 三个populate_blendspace | 返回成功并保存，各27样本，无失败样本 |
| 蓝图制作 | 新增8个业务节点、移除旧GetVelocity；3+6+4条连线制作均成功；布局与最终RootMotionMode写入保存，persisted=true |
| 工具内部生成类更新 | add_node、set_node_property、connect_pins_batch、delete_node原生处理器内部调用CompileBlueprint并保存，作为编辑实现步骤；没有调用单独compile/compile_all/validate |
| 完工后验证 | **未执行**：无C++构建、PIE、自动化、显式蓝图编译检查、资产读回、文档检查或diff检查，遵照用户指令 |

原生bulk写入回包附带属性旧值/新值，是同一制作调用的返回信息，没有追加完工后的读回。完整日志在 `Saved/NinjaRootMotion-20261020/authoring-log.json`。没有用2026-10-19的旧测试结果作为此次通过证明。

## 风险、遗留与回退

R-ANIM-001保留：实际移动速度、碰撞、输入停止/转向融合、攻击位移、姿态与命中效果均未运行核对；原固定时序PIE脚本尚未适配。M_Drink继续使用原资源。R-MM-001保持正式MM待接入。

本轮12个资产备份在 `Saved/NinjaRootMotion-20261020/Before/Content/...`；包含修改前ABP与根运动关闭的8个Ninja输出。回退时关闭编辑器，恢复这12个备份，再按映射通过编辑器移除新增18条Rootmotion输出，即回到首轮IPC版本；不要误用更早的首轮备份或reset整个工作区。Saved属于本机临时证据，清理前另存需要的备份。

## 已同步文档

[当前Ninja配置](../Systems/Ninja-Animation-Configuration.md)、[战斗](../Systems/Combat-AI.md)、[UI资产](../Systems/UI-Assets.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。历史CHG-20261020-001及首轮映射保留原含义，当前根设置以本记录和Root Motion映射为准。
