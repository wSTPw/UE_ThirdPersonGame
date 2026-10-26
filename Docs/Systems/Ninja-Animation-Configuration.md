# Ninja 动画配置（2026-10-20）

状态：**资源已制作并保存，未经完工后验证**。用户明确要求完成后禁止验证，本轮没有构建、蓝图编译检查、PIE、自动化、文档检查、diff检查或完成后的资产读回。MCP制作命令返回的 saved / persisted 仅表示保存步骤结果，不代表动作表现或玩法通过。

## 来源与骨架

- 来源：`/Game/ARPG_Ninja/Animations`，原动画包保持原样。
- 来源骨架：`/Game/ARPG_Ninja/Demo/Mannequin/Character/Mesh/UE4_Mannequin_Skeleton`。
- 来源预览网格：同目录 `SK_Mannequin`。
- 正式网格：`/Game/MyStuff/Model/Robot/Y_Bot`；目标骨架：同目录 `Y_Bot_Skeleton_RootOn`。
- 最初26条Sequence在 `/Game/MyStuff/Animation/Ninja/Sequences`；后续Root Motion适配新增18条在 `/Game/MyStuff/Animation/Ninja/RootMotion`，均为原资产名加 `_YBot`。
- 当前源 / 目标路径、提取设置、BlendSpace样本及蓝图输入见 [Root Motion映射 JSON](../../ArtSource/Animation/NinjaRootMotion-20261020.json)；身体手指链与未改变的通知数值仍见 [首轮映射](../../ArtSource/Animation/NinjaReplacement-20261020.json)，其中IPC与锁根配置属于历史状态。

## 重定向配置

`/Game/MyStuff/Animation/Ninja/Rig` 新建 `IK_Ninja_Source`、`IK_Ninja_YBot`、`RT_NinjaToYBot`。骨盆分别为 Pelvis / Hips，根运动骨均为实际 Root；20条身体与手指链同名显式配对。源手脚与目标骨名不同，不能仅改 Skeleton 指针。源骨架多余 twist / IK 骨没有伪造目标链；目标 weapon_r 保持随右手的原层级。

Retargeter 使用 UE5.8 默认操作栈与独立目标姿态 `Ninja_APose`，通过 chain_to_chain 自动对齐。Root Motion 操作必须显式设置 SourceRoot=Root、TargetRoot=Root、TargetPelvis=Hips，RootMotionSource=CopyFromSourceRoot、RootHeightSource=CopyHeightFromSource；单独设置 Rig.rootMotionBone 并不会自动填充这些操作字段。制作阶段最初空字段警告已通过这次显式配置处理。

按用户后续要求，当前移动使用Rootmotion版本，四个攻击、Throw_A及三条待机输出同样启用根运动提取。26条正式使用的Ninja Sequence配置bEnableRootMotion=true、bForceRootLock=false、RootMotionRootLock=AnimFirstFrame；提取后姿态的根锁到首帧，由CharacterMovement消费真实根轨迹、移动胶囊并处理碰撞与重力。攻击现在会带动角色位移，不能再按首轮“仅模型原地播放”理解。原始资源和IPC输出保留，未伪造Root轨迹；MM尚未接入。

## Root Motion蓝图输入

`/Game/MyStuff/Model/Robot/ABP_Move.RootMotionMode` 从RootMotionFromMontagesOnly改为**RootMotionFromEverything**，以提取BlendSpace和Montage的根运动。原状态机、WeaponAnimType分支及Slot层级保留，EventGraph移除原GetVelocity节点，新增LocomotionContext / Action快照拆分和移动输入力度计算：

```text
InputStrength = clamp(SafeDivide(lengthXY(GetLastMovementInputVector()), Action.MoveScale), 0, 1)
Speed = lengthXY(LocomotionContext.DesiredVelocity) * InputStrength
Direction = CalculateDirection(LocomotionContext.DesiredVelocity, ActorRotation)
```

DesiredVelocity由现有MyAnimInstance在游戏线程按当前输入加速度、MaxSpeed及动作许可生成，静止也能响应输入，避免“实际速度为0→不播放走跑→无根位移”的循环依赖。LastMovementInputVector为Pawn最近消费的世界空间输入；除以MoveScale是为移除输入端已有缩放，防止与DesiredVelocity中的缩放相乘两次。SafeDivide在MoveScale=0时返回0，涵盖动作、背包和死亡锁定；保留摇杆力度并限制斜向输入幅度。Velocity仍表示实际运动，不改变C++快照接口。

蓝图编辑工具在新增节点、设置类型及连线时内部更新生成类，这是制作步骤；本轮没有额外调用compile / validate或运行测试。该输入图及根运动表现未做完工后验证。

### 共享缓存根运动与衔接修复

用户反馈移动不生效、衔接生硬后，制作前诊断确认：跑步源Root终点275cm，YBot输出283.644409cm；提取已启用、模式为Everything、玩家使用正确ABP。问题在共享PoseCache：UpperBodyOnly和DefaultSlot同时读取该缓存，LayeredBoneBlend原先先更新上层，上层姿态权重1但根权重0；底层随后姿态权重也是1。UE5.8 SaveCachedPose等姿态权重时保留首个请求，因而根运动会被上层上下文抑制，虽然走跑姿态仍能播放。

当前AnimGraph的LayeredBoneBlend（GUID `9E7554DD43E41E259DEAA38AF0EF6903`）已设 **Node.bUpdateBasePoseFirst=true**，使底层先以有效根权重更新缓存；bBlendRootMotionBasedOnRootBone仍为true，Spine1上半身过滤和RootMotionFromEverything不变。不要通过给上层强行开启根权重绕过共享缓存顺序。

三个BlendSpace原来输入平滑和样本权重插值均为0，现统一配置：Direction InterpolationTime=0.10秒、Speed=0.16秒、InterpolationType=BSIT_SpringDamper、DampingRatio=1、MaxSpeed=0；TargetWeightInterpolationSpeedPerSec=8、bTargetWeightInterpolationEaseInOut=true。参数用于缓和起停和转向，是未经运行调校的初始值，滤波和权重插值会共同影响响应。

配置已保存，**没有完工后运行验证**；不能据此宣称移动和手感已实测恢复。当前配置增量见 [缓存与衔接映射](../../ArtSource/Animation/NinjaLocomotionFix-20261020.json)，原因和回退见 [CHG-20261020-003](../Changes/CHG-20261020-003-locomotion-root-cache-fix.md)。

## 移动映射

三个现有 BlendSpace 路径保持稳定，ABP_Move 的状态机与 Slot / 骨骼分层沿用原图。

| BlendSpace（均在 `/Game/MyStuff/Model/Robot`） | 速度0 | 速度175 / 525 |
| --- | --- | --- |
| BS_Move | Idle_no_weapon_YBot | 正向Walk / Run_no_weapon_Rootmotion；侧向、后退及斜向使用持武器方向Rootmotion |
| BS_LongSwordMove | Idle1_YBot | Walk / Run的八方向Rootmotion |
| BS_StaffMove | Idle2_YBot | 同上，沿用当前持武器移动分支 |

表内省略共同前缀 `ARPG_Ninja_Anim_UE_`，移动输出均有 `_YBot` 后缀并位于RootMotion目录。每个资产27个样本：9个方向坐标的待机，加9个行走与9个跑步；后退在-180°和180°各一份，其余为-135°、-90°、-45°、0°、45°、90°、135°。Direction轴[-180,180]、8格、bWrapInput=true；Speed轴[0,525]、3格。175 / 525现在是**选择走跑的移动意图坐标**，实际胶囊速度由混合后的真实Root轨迹决定，不保证等于坐标或MaxWalkSpeed；未做运行速度标定。

## 长剑连击

正式入口仍为 `/Game/MyStuff/Model/Robot/M_LongSwordAttack`，Attack Slot、Combo01..04、原动作定义和武器引用保持稳定；四个片段替换为 Attack_ComboA1..4_YBot。RateScale=1，BlendIn=0.08秒、BlendOut=0.10秒，完整时长约4.2秒。Section锚定实际片段，不沿用旧7秒Montage的绝对时间。

下列窗口和命中时间均为**相对本段的动画秒**，是本轮制作配置，未经过PIE或视觉调校：

| Section | Montage起点约 | 片段长度约 | MeleeHit | Chain | Cancel |
| --- | --- | --- | --- | --- | --- |
| Combo01 | 0 | 0.983333 | 0.283333、0.516667 | 0.45–0.75 | 0.77–0.95 |
| Combo02 | 0.983333 | 1.166667 | 0.266667 | 0.35–0.85 | 0.90–1.10 |
| Combo03 | 2.150000 | 0.866667 | 0.183333 | 0.25–0.60 | 0.63–0.83 |
| Combo04 | 3.016667 | 1.183333 | 0.383333 | 0.50–0.90 | 0.93–1.15 |

五个命中使用 `/Script/IntroCpp.AnimNotify_MeleeHit`；八个窗口使用 `/Script/IntroCpp.AnimNotifyState_ActionWindow`，分别设置Window=Chain / Cancel。所有NextSection=None，由动作组件的输入缓冲决定连段。

`/Game/Data/ComboData/DA_LongSwordComboData` 同步：原6次命中改为5次，分布由1/1/2/2变为2/1/1/1。首段BaseDamage=15、SubHits=[0.5x,0.5x]；第二段20×1；第三段15×2；第四段25×2。保留每段累计配置伤害15/20/30/50、合计115；球扫、偏移、击退、物品成本与冷却保持原数据。这里只说明配置算术，不代表实际命中或目标扣血验证。

## 火球与保留资源

`/Game/MyStuff/Model/Robot/M_Attack_Fireball` 使用重定向后的 Throw_A_YBot，长度约0.566667秒，UpperBodyOnly Slot不变，BlendIn / Out均0.1秒。唯一 `/Script/IntroCpp.AnimNotify_Fireball` 放在11/60秒（约0.183333）。此资源是左手投掷的施法替代表现，故 `/Game/Data/Items/Weapons/DA_WP_FireStaff.WeaponFireSocketName` 从RightHand改为LeftHand；不添加新投射物或改变施法结算接口。

新包没有同语义喝药资源，`/Game/MyStuff/Model/Robot/M_Drink` 继续使用原动画和唯一ItemCommit。未接入的跳跃、攀爬、闪避、处决等不因资源包存在而成为玩法能力。旧Sequence资源保留供回退，未覆盖用户原有两个Walk动画修改，也未替换敌人、模板角色或角色模型。

## 记录与回退

初次替换见 [CHG-20261020-001](../Changes/CHG-20261020-001-ninja-animation-replacement.md)，后续Root Motion适配见 [CHG-20261020-002](../Changes/CHG-20261020-002-ninja-root-motion.md)。首轮7个备份在 `Saved/NinjaAnimationReplacement-20261020/Before`；本轮12个备份（ABP、3个BS、8个原Ninja Sequence）在 `Saved/NinjaRootMotion-20261020/Before`，保存日志在同目录authoring-log.json。Saved是本机临时证据，清理前另存所需备份。

只回退Root Motion时先关闭编辑器，恢复本轮12个备份，再通过编辑器按Root Motion映射移除新增18条Sequence；如需退回Ninja替换之前，再恢复首轮7个备份。不得混用两个阶段备份或reset整个工作区。2026-10-19的41项PIE断言和旧6命中证据仅对旧资产基线成立；旧脚本不包含当前Root Motion行为，不能直接用于验收。
