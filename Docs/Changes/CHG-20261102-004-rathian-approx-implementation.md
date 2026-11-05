# CHG-20261102-004：B1 近似 profile 实施批次一（AP-0~AP-4 代码落地）

- 状态：partial（代码全部落地、UE5.8 构建通过；PIE 交战验收与太刀回归待执行——用户操作）
- 日期：2026-11-02
- 需求摘要：用户下令开工 [PLAN-20261102-002](../Plans/PLAN-20261102-002-rathian-approximate-profile.md)；本轮完成 AP-0~AP-4 全部代码与构建验证。
- 关联 PLAN / ADR / 问题 / 接口 ID：PLAN-20261102-002、[CHG-20261102-003](CHG-20261102-003-rathian-approximate-profile-plan.md)、[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)。
- Git：工作区变更，未提交。

## 原因与结果

原行为：B1 仅有方案，无任何近似 profile 代码。

当前行为（AP-0~AP-4 全部落地）：

1. **AP-0 冻结名单**：v1 招式表四元组写入代码默认值——BITE（注册表 84/THK 83/动画 A_em001_02_001 已证/攻击窗 COL 候选 0–0.3833s/MV=30 代理）可玩；DASH_BITE2(87/86)、DASH_BITE_TIRED(88/87)、ROLLING_TAIL_ATTACK2_L/R(101/102) 已登记但动画 Unavailable——决策组件资格门自动跳过，编辑器指派动画后即启用。
2. **AP-1 数据资产类型**：`UMHWIRathianApproxStatsData`（HP3000/发怒 600-80s-×1.15-×1.05，逐字段忠实度标注）与 `UMHWIRathianApproxMovesetData`。
3. **AP-2 决策层**：`IMHWIRathianDecisionPolicy` 接口 + `UMHWIRathianScriptedPolicy`（无状态规则：角度>30°转体、距离带选攻击、否则接近）+ `UMHWIRathianDecisionComponent`（快照构建/动画资格过滤/冷却/决策日志）+ `UMHWIRathianApproxStateComponent`（发怒累积/持续/倍率，受击 1:1 累积为近似消费）。
4. **AP-3/4 执行体**：`AMHWIRathianApproxPawn`——复用训练靶发现方式（ECC_Pawn 命中代理球+AttributeComponent），SingleNode 动画播放，攻击窗前方球扫对玩家 `ApplyDamage`（自动走 `IIncomingDamageResponse` 拦截链，见切/翻滚不被破坏），受击死亡闭环（死亡停决策/停移动/关碰撞响应）。接近/转体/冷却为工程夹具参数并标注。
5. **构建**：UE5.8 IntroCppEditor Win64 Development **Result: Succeeded**。修复过程：接口实现类需 I 前缀（UHT 规则）、`SetAnimation` 单参/`Stop()` 替代 5.8 变更、`FSoftObjectPath` 包装字符串构造、UBA 存储服务写损坏用 `-NoUBA` 绕开（LNK1201/1136 根因）。

## 修改清单

| 文件/资产完整路径 | 类/符号 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxData.h/.cpp` | `UMHWIRathianApproxStatsData`、`UMHWIRathianApproxMovesetData`、`FMHWIRathianApproxMove`、`EMHWIRathianApproxQualification` | AP-0/1：数据资产与忠实度标注 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianDecisionPolicy.h` | `UMHWIRathianDecisionPolicy`(UInterface)、`IMHWIRathianDecisionPolicy`、`FMHWIRathianDecisionContext`、`FMHWIRathianActionRequest` | AP-2：可替换决策接口 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianScriptedPolicy.h/.cpp` | `UMHWIRathianScriptedPolicy` | AP-2：v1 手写规则 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxStateComponent.h/.cpp` | `UMHWIRathianApproxStateComponent` | 发怒状态宿主 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianDecisionComponent.h/.cpp` | `UMHWIRathianDecisionComponent` | 决策宿主与资格门 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxPawn.h/.cpp` | `AMHWIRathianApproxPawn` | AP-3/4：执行体 |

## 接口、事件与资源影响

新增独立 Approx/ 目录（可整体删除回退）；不改首链/太刀/训练靶任何签名。玩家命中怪物：怪物自带 `UAttributeComponent`+ECC_Pawn 代理球，`SweepWindow` 既有路径无需改动即生效。怪物攻击玩家：`ApplyDamage` 正值走玩家 `IIncomingDamageResponse`（翻滚/见切拦截不被破坏）。零配置运行：PIE 中 `summon /Script/IntroCpp.MHWIRathianApproxPawn` 即自动自配置（内建 evidenced 资产路径与默认四元组）。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| UE5.8 构建 | Build.bat IntroCppEditor Win64 Development | **Result: Succeeded**（-NoUBA；3.32s 增量） | `Saved/MHWI-Rathian-FirstChain/build-approx-20261102.log` |
| PIE 交战验收（AP-5） | 编辑器 | **未执行**——用户操作：PIE 内 summon 后近身战斗，观察日志 `[RathianApprox][Decision]`/`hit` 行 | — |
| 太刀回归矩阵 | 编辑器 PIE | **未执行**（待用户） | — |

## 风险、遗留与回退

- 遗留：4 个招式动画待指派（编辑器填 `Animation` 属性即启用）；移动中无移动动画（姿态冻结，工程夹具局限）；死亡无专用表现；伤害代理 ≠ 实战公式（NUM-02）；肉质乘数未接入（NUM-03）。
- 已知局限：接近/攻击位移为代码驱动（原位动画+代码移动候选），轨迹非原作；发怒累积规则近似。
- 回退：删除 `Source/IntroCpp/MHWI/Monsters/Approx/` 整目录即完全回退；不影响首链/太刀/训练靶。
- UBA 环境问题：`C:\ProgramData\Epic\UnrealBuildAccelerator` 写入失败是本机构建工具链问题（与项目无关），后续构建建议带 `-NoUBA` 或修复 UBA 服务。

## 已同步文档

[B1 方案](../Plans/PLAN-20261102-002-rathian-approximate-profile.md)状态、[Plans 索引](../Plans/README.md)、[Changes 索引](README.md)、[modules.json](../Reference/modules.json)（Approx 入口）。
