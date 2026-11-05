# PLAN-20261102-002：雌火龙近似 profile（B1：真动画+真数值+自制决策层）

- 状态：in-progress；用户 2026-11-02 下令开工。AP-0~AP-4 代码已落地并通过 UE5.8 构建（见 [CHG-20261102-004](../Changes/CHG-20261102-004-rathian-approx-implementation.md)）；AP-5 PIE 验收待用户执行。
- 日期：2026-11-02。
- 用户需求：以"分层合流"推进——先用真动画+真数值+手写决策把"能打一场像样的雌火龙"跑起来；决策层接口化，未来 THK 语义闭合（R1/R2）后逐条替换为原作规则。
- 关联模块 / 接口 / 问题：mhwi-rathian-first-chain、enemy-ai、mhwi-rathian-animation；[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md) BEH/NUM/ANIM 各项。
- 上级方案：[总体方案](PLAN-20261031-002-rathian-restoration-master.md)；与 [首条链路](PLAN-20261031-007-rathian-first-chain.md) 共用执行框架。
- 实施记录：[CHG-20261102-003](../Changes/CHG-20261102-003-rathian-approximate-profile-plan.md)。

## 现状与目标

### 本轮新增数据源（2026-11-02 静态实证）

| 数据 | 内容 | 证据 |
| --- | --- | --- |
| **原生动作注册表** | 344 条 `{名字, 运行时ID, vtable}`（ID 10~212，无空缺），散布多张分系统表（地面战/飞行/气球/骑乘等各持独立 ID 序列） | `Saved/MHWI-Rathian-FirstChain/action-registry-dump-20261102.json` |
| **ActionDumps 编号非运行时命名空间** | 同名动作在 dump 与注册表间无统一偏移（BITE 83→84、DASH_BITE2 86→87、ROLLING_TAIL_ATTACK2_L 75→101）；THK emit id ↔ 注册表 id 的映射需逐动作核验 | 同上+ActionDumps em001.txt 对照 |
| 动作构造器模式 | `mov qword [reg+0x1E0], packed`（133 站点，含噪声）；解码 `slot=packed&0x1FF; bank=(packed>>12)&0xF` 在消费端 0x141c0158a 实证 | `scan_thk_action_ctors.py` |
| 未闭合 | 注册表 id ↔ motion packed 的桥（构造器 desc 是方法表，不含注册表 vtable；.data vtable 运行时填充）——归入 R1（Ghidra xref）或 R2（运行时 dump）收益 | 本轮探针记录 |

### 既有可复用资产

- 848 条 AnimSequence（原路径 `/Game/MHWI/Rathalos/Animations/A_em001_XX_YYY`）+ Skeleton + 模型/材质；`rathian-source-motion-map-20261102.json` 提供 bank/slot→资产全量映射。
- 首链执行框架：`AMHWIRathianFirstChainPawn` + `UMHWIRathianSourceMovementComponent`（外部原时钟位移）+ `UMHWIRathianSourceCollisionComponent` + `FMHWIRathianThkExecutor`（UE5.8 编译通过）。
- 全套已证数值（[LR 数据页](../Reference/MHWI-Rathian-LR-Data-20261030.md)）：HP 3000 基础、12 肉质、7 硬直阈值、发怒 600/80s/×1.15、疲劳 70s/耐力 500–600、异常/陷阱/捕获全套。
- 玩家侧：太刀 SweepWindow/延迟 shell + `UAttributeComponent` 伤害宿主。

## 范围与验收标准

| 层 | 内容 | 忠实度标注 |
| --- | --- | --- |
| 动画层 | 招式播放用已导入原作动画，时长/采样为导入回读真值 | evidenced（资产身份）/ 招式↔动画的映射部分 approximated（见 AP-1） |
| 数值层 | 伤害/肉质/发怒/疲劳/异常用已证原值 | evidenced 字段直接用；消费语义未证处（如发怒 ×1.15 的作用点）标 approximated-consumption |
| **决策层** | 招式选择/连段/地空切换/取消窗口为手写规则 | **approximated（本方案核心让步）** |
| 验收 | 固定脚本+自由 PIE：猎人 vs 雌火龙完整交战——接近/咬击/冲撞/转尾/火球/吼叫/起飞降落/怒/疲劳/受击/死亡闭环；太刀回归不破坏 | 每帧决策可解释（日志带距离/怒值/规则命中行） |

**红线**：任何批次不得把 approximated 决策写成"原作行为"；总还原状态不因 B1 完成而提升。

## 技术方案

### 决策层接口化（分层合流的落点）

```
AMHWIRathianFirstChainPawn（复用，扩展为可装配）
  └─ UMHWIRathianDecisionComponent（新，接口宿主）
       ├─ IMHWIRathianDecisionPolicy（UInterface）
       │    ├- Evaluate(ContextSnapshot) -> ActionRequest   // 每决策帧/动作结束时调用
       │    ├- MHWIRathianScriptedPolicy（B1 实现：手写规则表）
       │    └- MHWIRathianThkPolicy（未来：R1 闭合后接 FMHWIRathianThkExecutor）
       └─ UMHWIRathianApproxStateComponent（怒/疲劳/耐力/异常计时，读 DA_RathianApproxStats）
```

- `ScriptedPolicy` 规则输入：目标距离/角度、当前怒值/疲劳、耐力、上一动作、随机权重；输出：`ActionRequest{RegistryName, MintCondition}`。执行侧经注册表名→招式表→动画路径启动（沿用 ActionRunId/PlaybackGeneration 契约）。
- 决策规则全部数据化（`DA_RathianApproxMoveset` 内权重/距离段表），便于未来逐条替换为 THK 规则并 diff。

### 数据资产

| 资产 | 内容 | 来源标注 |
| --- | --- | --- |
| `DA_RathianApproxStats` | HP/肉质/硬直/发怒/疲劳/异常全套 | evidenced（LR 数据页 §3） |
| `DA_RathianApproxMoveset` | 每招式：注册表真名+id、THK id（unknown 占位）、动画路径、时长、位移类型、手写选择权重/距离段 | 名字/ID=evidenced（注册表）；动画映射=已解 83 用真映射，其余 approximated；权重=approximated |

首批招式候选（注册表真名，≈12 个）：BITE(84)、DASH_BITE2(87)、DASH_BITE_TIRED(88)、ROLLING_TAIL_ATTACK_L/R、TAIL_SPIN 系、FIRE_BALL/FIRE_BREATH 系（以注册表实际名为准）、ROAR 系、TAKE_OFF/LANDING、WALK/DASH/GLIDE、IDLE 系。

## 实施步骤与依赖

| 步骤 | 内容 | 验收门 |
| --- | --- | --- |
| AP-0 | 招式名单冻结：从注册表 dump 选首批 ≈12 招式，逐条登记名字/ID/表归属；动画映射缺口清单（已解 83，其余手工指定并标 approximated） | 每招式四元组（名/ID/动画/数值引用）齐或显式 unknown |
| AP-1 | 两个 DataAsset 制作（C++ 类型+资产保存读回） | 蓝图读回字段一致 |
| AP-2 | 决策组件+接口+ScriptedPolicy（含状态组件） | 固定情境夹具：同输入同输出，日志可解释 |
| AP-3 | 播放/位移闭环：复用首链 Movement/Collision，接 AnimSequence 播放与根位移 | 单招式播放+位移+取消干净 |
| AP-4 | 伤害桥接：怪物攻击窗→玩家 IncomingDamageResponse；玩家命中→怪物肉质/HP（复用 C1 桥设计，桥接 UAttributeComponent） | 一击一提交；太刀回归不破坏 |
| AP-5 | 完整 PIE 验收+决策日志审查+太刀回归矩阵 | 上表验收项全过；CHG 记录 |

依赖：AP-1~2 可并行于 R1 取证；AP-3 依赖 AP-1；AP-4 依赖既有战斗桥设计（PLAN-006 C1，未实施部分按需最小化）。

## 验证计划

| 场景 | 方法 | 期望 | 边界 |
| --- | --- | --- | --- |
| 构建 | UE5.8 IntroCppEditor 构建 | 新类型通过 | ≠玩法通过 |
| 决策夹具 | 固定距离/怒值输入→请求断言 | 规则表命中可解释 | 不证明原作 |
| 招式回放 | 12 招式逐个 PIE 播放+取消 | 无残留窗/双位移 | 动画映射 approximated 项单独列 |
| 交战 | 自由战斗 3 分钟×3 次 | 怒/疲劳/死亡闭环、无卡死 | 决策分布不对照原作 |
| 回归 | 太刀五项+训练木桩 | 既有行为不变 | — |
| 文档 | check_docs.py；git diff --check | 通过 | — |

## 风险与回退

- 动画映射 approximated 项可能"动作名对但动画观感不对"——播放验收时逐招人工确认，错配回退到待定池。
- 发怒 ×1.15 等消费语义未证：先按字面乘在怪物伤害出口，标注 approximated-consumption；R1/E05 闭合后修正。
- 回退：新代码全部在 `MHWI/Monsters/Approx/` 新目录与两个 DA；删除即回退，不影响首链与既有资产。

## 文档同步清单

实施批次更新：Combat-AI/雌火龙现状页、Interfaces（决策接口）、modules.json（Approx 入口）、Known-Issues（映射缺口）、每批 CHG。本方案交付记录见 [CHG-20261102-003](../Changes/CHG-20261102-003-rathian-approximate-profile-plan.md)。
