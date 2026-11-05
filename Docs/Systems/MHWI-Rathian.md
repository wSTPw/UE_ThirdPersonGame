# MHWI 雌火龙

目标：在 UE 5.8 项目里用 em001 雌火龙的真实数据/动画/动作链，还原一场下位单人战斗。
取证结论与未解清单见 [雌火龙取证总账](../Reference/MHWI-Rathian-Evidence.md)；本页只描述**当前实现**。

## 一、两条产品线，不要混为一谈

| 线 | 定位 | 证据资格 | 当前状态 |
| --- | --- | --- | --- |
| **忠实线** | 原作数据 + 原作 THK 决策 | 可宣称"还原" | 数据侧基本到手；THK 语义仅到社区命名候选（81.5% 覆盖），**运行验证为 0** |
| **近似线 B1** | 真动画 + 真数值 + 自制决策层 | 只能叫"近似 profile" | 代码落地、UE 5.8 编译通过；**PIE 验收一次没跑过** |

B1 的意义是：在语义闭合前先有一个能打的版本，决策层做成接口 `IMHWIRathianDecisionPolicy`，THK 语义闭合后逐条替换为 `ThkPolicy`，执行层不动。

**架构约束**（[ADR-0002](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md)）：

- 决策与执行分离。决策器只决定"下一步做什么"，动作怎么执行由同一套 ActionSpec 驱动。
- 禁止两套执行逻辑。B1 不得另写动画播放与判定，否则换忠实决策器时会把战斗系统一起推倒。
- 动作覆盖口径 = 已验证动作数 ÷ 实际可达动作数，**不用"344 条全覆盖"**（旧口径已撤回）。

## 二、代码地图

### 首链（忠实线执行骨架，约 1546 行 / 9 文件）

`Source/IntroCpp/MHWI/Monsters/`

| 文件 | 职责 |
| --- | --- |
| `MHWIRathianThkExecutor.{h,cpp}` | THK 指令执行器。未知 functionType **拒绝执行**（设计如此，不要改成猜默认值） |
| `MHWIRathianSourceMovementComponent.{h,cpp}` | 源数据驱动位移 |
| `MHWIRathianSourceCollisionComponent.{h,cpp}` | 源 COL 攻击判定 |
| `MHWIRathianFirstChainPawn.{h,cpp}` | 首链组装（咬击链 83 / 冲撞 86-87） |
| `MHWIRathianFirstChainData.h` | 首链常量与数据结构 |

### 近似线 B1（约 1172 行 / 11 文件）

`Source/IntroCpp/MHWI/Monsters/Approx/`

| 文件 | 职责 |
| --- | --- |
| `MHWIRathianApproxData.{h,cpp}` | 两个 PrimaryDataAsset：Stats（HP3000/发怒 600·80s·×1.15·×1.05）+ Moveset（招式表，动画软引用） |
| `MHWIRathianDecisionPolicy.h` | `IMHWIRathianDecisionPolicy` 接口（UHT 要求 I 前缀） |
| `MHWIRathianScriptedPolicy.{h,cpp}` | 手写规则：角度→转体、距离带→选招、否则接近 |
| `MHWIRathianDecisionComponent.{h,cpp}` | 决策循环 + 动画资格门 + 冷却 + `[Decision]` 日志 |
| `MHWIRathianApproxStateComponent.{h,cpp}` | 发怒累积/持续/衰减 |
| `MHWIRathianApproxPawn.{h,cpp}` | 执行侧：SingleNode 动画 + 攻击窗球扫 + 死亡闭环 + 猎人受击接口 |

## 三、资产现状

| 项 | 状态 |
| --- | --- |
| 动画 | **848 条 AnimSequence**（19 个 LMT，7 个是 16 B 空壳）。逐条类/Skeleton/时长读回通过；旧 24 条时长已按源帧数重导 |
| 本体网格 | `/Game/MHWI/Rathalos/Mesh/SK_EM001_Body`，142 骨 / 4 材质槽 |
| 尾巴网格 | `/Game/MHWI/Rathalos/Mesh/SK_EM001_Tail`，3 骨（独立文件，非本体子网格） |
| 材质 | 4 个（BML+NM+EM、damage），RMT 通道实测 `R→Roughness / G→Metallic`，12 贴图（4 张法线） |
| 骨骼数差异 | Blender 141 → 引擎 142，尾巴 2 → 3，属 FBX 导入新增根骨，**未逐骨核对**；重定向/挂接前必须确认 |
| 路径约定 | 历史资产留 `/Game/MHWI/Rathalos/...`；新运行资源走 `/Game/MHWI/Rathian/...` |

材质已判定**不接** `CMML`（2048²，R/G/B 0.939/0.952/1.0，近似全白无收益）与 `FM`（R/G 恒 0.514/0.505，常量场无细节）。眼睛外 Emissive 全部断开——此前 `NoImage_EM` 白图误接导致整只模型发白。

## 四、当前能力与已知缺陷

B1 用户实测反馈的处置：

| 问题 | 状态 |
| --- | --- |
| 龙浮空 | 已加 `LineTrace` 贴地，**待 PIE 复验** |
| 不会移动 | 已解阻并加位移；**移动时无迈步动画**（姿态冻结，明示的工程夹具） |
| 头不看向玩家 | 已加朝向插值，待复验 |
| 攻击动画无前后衔接 | 已用运行时 Montage + 混合，待复验 |
| 角色受击无反馈 | 已实现 `IMHWIContactResponse`，接上猎人原生 `StartNativeImpact` 受击等级链 |

> 这五项在 2026-11-02 当晚**从未编译成功**（源文件 21:18 改，21:21 构建 `Result: Failed`，DLL 仍是 19:49 旧版）。11-04 修掉 4 类错误后实测 `Result: Succeeded`。**但 PIE 至今没跑过**，不能当已验证。

首链静态审查发现的验收前必处理项（详见 [总账](../Reference/MHWI-Rathian-Evidence.md) 第六节）：

- R-DATA-007：移动容许 Seconds/NativeTicks，碰撞只容许 NativeFrames，Pawn 只按时长映射后直接传同一数值，**不核对单位/速率/来源/clip 身份**
- R-COMBAT-013：同一胶囊的 map 按 Actor 键写入，区间末重叠会无条件覆盖较早的精确 TOI；首尾轴一致不证明中间骨轨纯平移
- R-ANIM-013：`InPlaceSequence` 只验骨架/时长；旧导出保留 `bone_root` 平移，导入未明设根提取/锁根；该 bank 历史抽检是 181 而非 001
- R-AI-003：strict 条件 resolver 只查工程条件；到 EndTime 直接 `Thk.Cancel`，未接 `ResumeAfterAction`

## 五、UE 5.8 API 差异（编译时踩过）

| 旧写法 | 5.8 正确写法 |
| --- | --- |
| `SkinnedMeshComp->bUseUpdateRateOptimizations` | `bEnableUpdateRateOptimizations` |
| `SetAnimation(Seq, bLoop)` 两参 | `SetAnimation(Seq)` 单参 |
| `Comp->SetPlaying(false)` | `Comp->Stop()` |
| UObject 接口类名任意 | 必须 `I` 前缀，如 `IMHWIRathianDecisionPolicy` |
| `TSoftObjectPtr<UAnimSequence>(TEXT("..."))` | `TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("...")))` |
| `PlayAnimMontage`（组件方法） | `Body->SetAnimation(Montage)` |
| 手工拼 `FAnimSegment` | `UAnimMontage::CreateSlotAnimationAsDynamicMontage(...)` |
| `Montage_GetIsPlaying` | `Montage_IsPlaying` |

运行时动态 Montage 必须挂 `UPROPERTY(Transient)`，否则二次 GC 后悬空。

## 六、怎么跑

构建（**必须带 `-NoUBA`**）：

```powershell
& 'E:/UE/UE_5.8/Engine/Build/BatchFiles/Build.bat' IntroCppEditor Win64 Development `
  '-Project=E:/Unreal Projects/IntorCpp/IntroCpp.uproject' -WaitMutex -NoHotReloadFromIDE -NoUBA
```

本机两个构建坑（已排查，非项目代码问题）：

1. **UBA 存储服务写损坏**：不带 `-NoUBA` 会出 LNK1201/LNK1136，且 UBT 日志可能完全没有诊断输出（静默失败）。
2. **陈旧链接产物**：莫名 LNK 错误时先杀 `mspdbsrv`，删 `Binaries/Win64/UnrealEditor-IntroCpp.{dll,pdb,exp}` 与 `Intermediate/Build/Win64/x64/UnrealEditor/Development/IntroCpp/UnrealEditor-IntroCpp.lib` 后重建。

复现脚本（`Scripts/MHWI/`，均带 `--self-check`）：

| 脚本 | 作用 |
| --- | --- |
| `extract_rathian_thk_chain.py` | THK 链路提取（105 表 / 1795 节点 / 13015 段） |
| `extract_rathian_chain_motion.py` / `_collision.py` | 动作 / 碰撞分支提取 |
| `correlate_rathian_first_chain_actions.py` | 5 动作 → ACTP2 → LMT → UE 动画 → COL 关联表 |
| `map_thk_function_semantics.py` | fexty ↔ 本机 functionType 覆盖映射 |
| `disasm_thk_native_semantics.py` | 原生 VM 静态反汇编 |
| `scan_thk_jump_tables.py` | 跳转表穷举（**负结果**，别重跑） |
| `build_rathian_source_motion_map.py` | 848 动画 → 源槽位映射表 |
| `rathian_damage_pipeline_stages.py` | 伤害分段结算原型 |

## 七、接手先看什么

1. 本页 + [取证总账](../Reference/MHWI-Rathian-Evidence.md) 第六节未解清单
2. [ADR-0002](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md) 架构决策与"不得伪造完成"红线
3. `Docs/Known-Issues.md` 的 R-DATA/R-COMBAT/R-ANIM/R-AI 条目

**红线**：不得把社区命名当已证；不得把近似层行为写成"还原了雌火龙"；不得覆盖工作区里未提交的资产。
