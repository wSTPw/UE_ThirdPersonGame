# PLAN-20261107-001：雌火龙基础可玩战斗

- 状态：completed（基础工程profile；资产/PIE由PLAN-002接续并已完成）
- 日期：2026-11-07
- 用户需求：暂停原作逆向取证，先实现巡逻、发现目标并依出招逻辑移动、攻击、HP、击飞及死亡；基础招式小咬、龙车、单火球、甩尾起飞接落地；动画衔接流畅、体积碰撞合理。
- 关联模块：mhwi-rathian-approx；近似玩法层，保留忠实线原始资料。
- 实施记录：基础13文件经冻结UE5.8构建、全新Luna审查/主审ACCEPTED后核hash合入；后续速度/落地修复、资产及24项PIE已完成。代码阶段历史见[CHG-001](../Archive/MHWI/Changes/CHG-20261107-001-rathian-basic-combat.md)，完整结果见[CHG-002](../Changes/CHG-20261107-002-rathian-basic-assets-pie.md)和[当前交接](MHWI-Rathian-Handoff.md)。
- 阶段边界：代码阶段按当时“不启动UE”指令停止；随后用户已授权更新交接后启动UE，继续[PLAN-002](PLAN-20261107-002-rathian-basic-assets-pie.md)。历史启动尝试未就绪，不当作运行验证。

## 现状与目标

实施前 `Source/IntroCpp/MHWI/Monsters/Approx/` 只有近身咬击、简易接近/转向、前方球扫与死亡冻结；没有巡逻、完整移动动画、火球、空中连段或死亡动画。`UAnimInstance::StaticClass()` 配合反复 SetAnimation 的播放方式没有稳定的待机/移动底层图。用户工作树有大量既有修改，本任务不覆盖训练地图和太刀数据。

本次是可调的基础玩法，不将决策距离、攻击窗、伤害、击飞或动画选型写成已证原作规则。利用既有 em001 动画与模型，以实际播放校对用途。

## 范围与验收标准

1. 无目标时在出生点周围或指定点巡逻，站立/行走有连续姿态；视距、视角和视线成立后发现目标。
2. 按招式距离与角度带选择招式；需要时接近、转向或调整距离；前摇后停止追踪转向，攻击有可躲避空间。目标死亡/丢失后退出战斗，死亡期间不再决策。
3. 五项基础表现：小咬、龙车、单火球、甩尾起飞、落地；尾翻与起飞/落地组成完整连段，空中保持高度变化和落地收尾。
4. 近战采用随骨骼更新的有向盒体积扫掠/重叠，窗口内每目标每窗口至多一次；窗口跨帧仍检测，遮挡墙体不穿透命中。火球为可见、可躲避、受场景阻挡的单发投射物。
5. 伤害接现有 Attribute/IncomingDamageResponse；闪避/反击成功不额外击飞，普通命中按招式给出受击等级与受控击退/击飞。
6. HP 可读取并有现场可见反馈，归零只进入一次死亡：取消当前攻击、判定、移动与后续出招，播放死亡并保持末姿。
7. 新建专用测试关卡，不覆盖 `/Game/MHWI/Maps/L_MHWI_Training` 或 `DA_MHWI_LongSword`。完整构建、蓝图/资产读回、PIE 跑状态与五类攻击、死亡中断及目标丢失。

## 技术方案

沿用现有 Approx Pawn、数据资产及可替换策略接口。Pawn 持有巡逻/战斗/执行状态，策略只根据距离、角度、上一招等快照选择。每次攻击有独立运行编号、阶段和命中去重集合；所有 UObject、Actor、伤害和委托在游戏线程操作。

使用原生 AnimInstance + 官方 FAnimInstanceProxy 自定义根图，待机/移动序列由 TwoWayBlend 连续混合后进入 DefaultSlot，攻击使用动态 Montage 并按阶段混合衔接。动画引用由数据资产配置，避免把未知槽位硬定为原作动作。必要时制作选中动画的原位副本，保留源资产。

每招配置阶段动画、攻击窗口、骨骼盒、伤害代理、击飞向量、移动速度/飞行高度、前摇追踪截止和恢复时间。死亡最高优先级；取消与 EndPlay 清理运行态和委托。投射物独立 Actor，忽略来源、限制生命周期，扣血和击飞仅消费一次。使用现有引擎模块，仅新增 AnimGraphRuntime 依赖，不改第三方工具。

### 官方机制与适用版本

- UE 5.8 动态 Montage、Slot 与混合：[Animation Montage](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine)。
- UE 5.8 形状扫掠：[Traces Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/traces-in-unreal-engine---overview)。
- UE 5.8 原生动画图扩展以本机 `Engine/Source/Runtime/Engine/Public/Animation/AnimInstanceProxy.h` 的 GetCustomRootNode/GetCustomNodes 为准；Standalone SequencePlayer 支持运行时设置序列，避免折叠字段在非编辑器构建不可变。
- UE 5.8 [Montage实例身份](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/FAnimMontageInstance)和[活跃实例查找](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UAnimInstance/GetActiveInstanceForMontage?lang=en-US)：实例有独立ID；不再活跃的查找返回空。自然结束/中断须消费实例回调，不能用停止后GetPosition的零值猜结束。具体移除行为见本机AnimInstance.cpp:3696–3710。
- 上述资料只支持 UE 实现机制，基础玩法参数均为工程配置，不证明 MHWI 原作规则。

## 接口与数据迁移

保留 Approx Pawn/Data/Policy 类名及现有组件属性。新增数据字段默认安全关闭未配置动作，配置一次不得重复回血/重复绑定。新增显式目标与请求招式接口用于独立测试，必须遵守死亡/忙碌/资源有效性约束。既有严格首链与原作证据文件不改。父代理负责独立资产配置与原始源码合并，Luna 只改合同工作副本。

## 实施步骤与依赖

1. 冻结当前 Source 快照和接口约束，Luna 实现基础执行、动画图、盒判定及火球。
2. 主代理在独立验证项目编译；固定检查通过后新的 Luna 只读审查，主代理按快照批准，再逐文件核原始 hash 合入。
3. 筛选并播放现有动画，配置新基础 Moveset/Stats 和专用关卡，核对全路径、骨架、时长、骨骼名、播放与根位移。
4. PIE 验证巡逻/发现/按距离出招/五类攻击/HP与击飞/墙体遮挡/目标丢失/死亡中断；保存实际报告与截图。

## 验证计划

| 场景 | 方法 | 期望与边界 |
| --- | --- | --- |
| C++/反射 | 独立验证工程 UBT Editor 构建，再原项目构建 | 编译通过不等于玩法通过 |
| 动画 | 资产读回及有限姿态预览 | 骨架一致、实际移动、无参考姿态跳变、合理起落 |
| 基础循环 | 专用关卡 PIE | Patrol→发现→移动/转向→攻击→恢复；失去目标可回巡逻 |
| 判定 | 受控距离、攻击窗、墙体和重复采样 | 盒体可见且只在窗口生效，单次去重，投射物遮挡 |
| 死亡 | 攻击/飞行中扣至0，重复伤害 | 一次死亡、判定与移动终止、死亡末姿保持 |

实际结果已写CHG-002：24项PIE/101断言通过；未覆盖完整闪避/反击/霸体回归、原作逐帧视觉对照和忠实THK/COL。本批工程火球演出由用户明确接受。

## 风险与回退

源动画语义不完整，需播放校对；根轨可能双重位移，优先原位副本和单一 Actor 位移责任。飞行落地必须处理地面探测和中断。所有新资产单独目录，原 Source 合入前校验基线；回退只恢复本批修改文件和新基础资产，不 reset/清理用户工作树。

## 文档同步清单

更新 MHWI-Current、MHWI-Rathian、modules.json、Known-Issues 相关近似玩法状态与 Changes/README；新建 CHG 记录实际构建/PIE结果和未验证项。
