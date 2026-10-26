# Motion Matching：Root Motion 动画资源清单

- 日期：2026-10-19。
- 状态：按用户要求暂停 MM 正式接入，待用户处理资源后另行继续；当前角色仍使用原 ABP_Move。
- 依据：[本轮动画实查](MM-P5-Audit-20261019.md)、[动作重构方案](PLAN-20261019-003-character-action-refactor.md)。

## 先处理哪些

先提供**长剑姿态的一套移动动画**即可，不必同时处理空手、法杖、攻击和喝药。以下路径统一位于 `/Game/MyStuff/Model/Robot/SwordAnim/`；文件名是本项目已经存在的资产，不代表它们的 Root Motion 均已逐条核查合格。

| 优先级 | 动画 | 已有资产名称 | 资源要求 |
| --- | --- | --- | --- |
| P0 | 向前走循环 | `Walk_Loop_F_0_Seq_YBot` | Root 有连续前移，速度与脚步对应；循环姿势衔接自然 |
| P0 | 向前跑循环 | `Run_Loop_F_0_Seq_YBot` | 同上；本轮已确认这两条原资源 Root 平移为零，需要补源数据 |
| P0 | 向前走起步 / 刹停 | `Walk_Start_F_0_Seq_YBot`、`Walk_Stop_F_0_Seq_YBot` | 保留真实加速 / 减速的距离和速度变化，不用匀速平移代替 |
| P0 | 向前跑起步 / 刹停 | `Run_Start_F_0_Seq_YBot`、`Run_Stop_F_0_Seq_YBot` | 同上；Hips 重心摆动不能代替整体运动 |
| P0 | 原地左 / 右转90° | `Turn_90_L_Seq_YBot`、`Turn_90_R_Seq_YBot` | Root 有相应角度旋转，可不产生平移 |
| P0 | 原地左 / 右转180° | `Turn_180_L_Seq_YBot`、`Turn_180_R_Seq_YBot` | 本轮实查右转180°已有 Root 旋转0→180°，优先核验，不必盲目重做 |
| P1 | 后退、左右横移、斜向走跑循环 | `Walk_Loop_*_Seq_YBot`、`Run_Loop_*_Seq_YBot` 的方向变体 | Root 轨迹方向与角色实际移动一致；先补四向，再补斜向 |
| P1 | 对应方向起步 / 刹停 | `Walk_Start_*`、`Walk_Stop_*`、`Run_Start_*`、`Run_Stop_*` | 对应上表循环方向；开始和结束姿势匹配 |
| P1 | 运动中90° / 180°急转、折返 | 按原始动画内容选择或新增，不以现有 Turn 文件名认定已有 | 必须包含运动中的转向与减速再加速，原地 Turn 不能完全替代 |
| P2 | 战斗移动姿态扩展 | `Walk_Combat_*`、`Run_Combat_*`、`Turn_Combat_*` 等实际存在的资源 | 普通长剑试点通过后再扩充；维持武器姿态一致 |

最小前向试点约为 **10条移动/转向 + 1条 Idle**。这个数量只覆盖前向起停和原地转身，不代表全方向移动已完整。Idle 如 `Idle_Seq_YBot` 可以原地，不必人为制造位移，但须采用相同骨架。

## 交付格式与验收

1. 使用当前 `Y_Bot_Skeleton_RootOn` 骨架，或交付可重定向的原始 FBX。当前顶层根骨为 `Root`，脚骨为 `LeftFoot` / `RightFoot`；不要直接采用 `foot_l` / `foot_r` 的假设。
2. 整体移动距离与朝向要在 **Root 轨迹**中，身体重心运动保留在 Hips；关闭提取后应能看到角色按真实运动距离移动。仅勾 Enable Root Motion 不能补出缺失数据。
3. 保持 UE 单位 cm、cm/s，方向、比例和骨架尺度一致。循环动画要有连续累计的根位移和可衔接的姿势，不要把每帧 Root 都清零。
4. 起停与急转保留真实速度变化，尤其不要根据测得的平均速度给所有动画统一加一条直线轨迹。
5. 建议放到新目录 `/Game/MyStuff/Animation/MotionMatching/SourceRM` 或保留独立原始文件，避免覆盖当前正式移动资源；资源到齐后再由 AI 检查每帧轨迹、设置、建索引及做游戏内对照。
6. 本轮不要求改 `M_LongSwordAttack`、`M_Attack_Fireball`、`M_Drink` 的 Root Motion；它们继续通过 Montage 和动作组件结算。跳跃/落地暂时沿用原分支。

动画中拥有 Root Motion 数据，不等于将来必须让动画驱动胶囊。正式接入仍需统一 CharacterMovement 与动画根运动的权限；请先保留原始轨迹数据，由接入阶段决定运行时提取方式。

官方依据：[UE5.8 Motion Matching](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)、[Root Motion](https://dev.epicgames.com/documentation/en-us/unreal-engine/root-motion-in-unreal-engine)。前者的移动示例要求动画含根运动并启用相关属性；本清单的具体数量、方向覆盖和优先级是针对本项目的实施建议。
