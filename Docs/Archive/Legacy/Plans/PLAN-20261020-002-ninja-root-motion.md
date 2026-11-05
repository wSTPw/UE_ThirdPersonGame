# PLAN-20261020-002：Ninja Root Motion 适配

- 状态：implemented（制作保存完成，未做完工后验证）
- 日期：2026-10-20
- 用户需求：动画使用Root Motion版本并适配；沿用完工后禁止验证要求。
- 关联模块 / 接口：player-combat、character-actions；ACTION-004。
- 实施记录：[CHG-20261020-002](../Changes/CHG-20261020-002-ninja-root-motion.md)。

## 现状与目标

上一轮接入IPC原地移动，攻击Sequence强制锁根且未提取根运动。制作前读取ABP_Move.RootMotionMode=RootMotionFromMontagesOnly，EventGraph用GetVelocity计算Speed和Direction。直接切Rootmotion会造成速度驱动播放与动画驱动速度互相等待。

目标：正式移动改用18条Rootmotion源片段的新YBot输出，攻击使用已有真实Root轨迹；将ABP选择输入改为受动作许可限制的DesiredVelocity，启用RootMotionFromEverything，让CharacterMovement消费动画位移、处理碰撞和重力。

## 技术方案与接口迁移

- 使用现有RT_NinjaToYBot重定向18条Rootmotion移动资源，不改原包与上一轮IPC输出。
- 移动、待机和新动作输出enableRootMotion=true、forceRootLock=false、AnimFirstFrame。提取根运动后姿态根锁定，位移交胶囊执行；不将同一轨迹同时叠加到模型。
- 三个BlendSpace保持既有坐标与路径，仅用Rootmotion版本替换18种移动样本；坐标速度代表移动意图，不等同实际根轨迹速度。
- ABP事件图的Speed / Direction从LocomotionContext.DesiredVelocity推导，实际Velocity继续供其他消费者读取。DesiredVelocity已有动作/UI/死亡MoveScale限制，避免动作期间底层继续跑步。
- ABP RootMotionMode改RootMotionFromEverything，使BlendSpace和Montage都可提取。保持现有Slot层级与命中、Chain/Cancel、伤害配置。
- 不新增MM Schema/Database。Root Motion驱动与Motion Matching选片是不同阶段。

## 实施步骤与依赖

备份本轮覆盖资源与ABP；读取实际依赖；重定向Rootmotion版本；制作根提取设置、BlendSpace与ABP输入；保存并同步现状和CHG。

## 验证计划

遵照用户要求不做完工后验证，不执行构建、显式编译检查、PIE、自动化、资产读回、文档检查或diff检查。蓝图制作工具自身的必要生成类更新若发生，记录为制作步骤，不冒充额外验证。

## 风险与回退

Root Motion会改变移动实际速度和攻击位移；动态碰撞、动画融合、输入停止、重定向比例及落地表现均未运行检查。备份保存在本轮Saved目录；关闭编辑器恢复本轮备份，新增18条资源可按映射列表移除。保留上一轮历史记录，不用Git reset覆盖工作区。

## 文档同步清单

Ninja配置、Combat-AI、UI-Assets、Interfaces、modules.json、Known-Issues、Plans/Changes索引和本轮CHG。
