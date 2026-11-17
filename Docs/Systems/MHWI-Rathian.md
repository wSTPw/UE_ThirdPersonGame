# MHWI 雌火龙

目标：在 UE 5.8 项目里用 em001 雌火龙的真实数据/动画/动作链，还原一场下位单人战斗。
取证结论与未解清单见 [雌火龙取证总账](../Reference/MHWI-Rathian-Evidence.md)；本页只描述**当前实现**。

当前暂停原作取证，基础版已经完成源码、25个独立Basic资产和24项真实PIE验收。完整入口见[当前交接](../Plans/MHWI-Rathian-Handoff.md)、[本轮记录](../Changes/CHG-20261107-002-rathian-basic-assets-pie.md)和[稳定配置/验收清单](../../Tools/MHW/rathian-basic-profile-20261107.json)。玩家使用既有三档受击；火球按用户选择保留工程演出，后续再换原作片段。

玩家短受击的后续修正已通过：[CHG-003](../Changes/CHG-20261107-003-hunter-hit-reaction.md)修复低帧提前结束与首帧旧姿保持。14场景16次运行121断言验证最终玩家骨姿、真实位移和生命周期；原24项保留其当时状态/编号等有限范围。没有修改Basic资产、三档源片或力度。

## 一、两条产品线，不要混为一谈

| 线 | 定位 | 证据资格 | 当前状态 |
| --- | --- | --- | --- |
| **忠实线** | 原作数据 + 原作 THK 决策 | 可宣称"还原" | 数据侧基本到手；THK 语义仅到社区命名候选（81.5% 覆盖），**运行验证为 0** |
| **近似线 B1 / Basic** | em001素材 + 原字段数值代理 + 工程决策/执行 | 工程近似profile | 源码三轮冻结编译/全新Luna审查和主审通过；主项目构建与资产读回、24项PIE/101断言通过 |

Basic基础玩法及本轮资产/运行验收已完成。决策保留 `IMHWIRathianDecisionPolicy` 接口，Pawn只分派策略请求和执行动作；当前没有接入原作THK策略。

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

2026-11-06只读取证补充：已用Luna DevFlow接受一份限定静态报告，原生键查找/回调分段有新字节证据；THK83递交、BITE对象与enter尚未闭合。当前源码仍在本地executor yield后核ID并启项目组件，本轮未修改实现或资产。结论与验收边界见[总账第五节](../Reference/MHWI-Rathian-Evidence.md)，不能把报告ACCEPTED当作原作功能通过。

### 基础近似玩法（15个源码文件）

`Source/IntroCpp/MHWI/Monsters/Approx/`

| 文件 | 职责 |
| --- | --- |
| `MHWIRathianApproxData.{h,cpp}` | 两个UDataAsset：Stats（HP/怒态/巡逻与视距参数）和Moveset（idle/walk/run/death软引用、招式阶段、骨骼盒、窗口/飞行/火球配置） |
| `MHWIRathianDecisionPolicy.h` | `IMHWIRathianDecisionPolicy`与决策快照/动作请求；不在Pawn另建选招器 |
| `MHWIRathianScriptedPolicy.{h,cpp}` | 按距离带、朝向、上一招和冷却选招，必要时转向或接近/后撤 |
| `MHWIRathianDecisionComponent.{h,cpp}` | 资格过滤、有符号atan2角度、策略调用、每招/全局冷却与限频日志 |
| `MHWIRathianApproxStateComponent.{h,cpp}` | 既有发怒累积/持续/衰减近似消费 |
| `MHWIRathianApproxPawn.{h,cpp}` | 巡逻、视距/视角/视线发现、请求分派、阶段Montage、骨盒扫掠、持续Landing、HP与终态死亡 |
| `MHWIRathianApproxAnimInstance.{h,cpp}` | 原生代理图：Standalone序列→idle/walk/run混合→DefaultSlot；死亡序列从0开始且不循环 |
| `MHWIRathianApproxFireball.{h,cpp}` | 延迟生成、socket出射、可见球体、扫掠投射物、一次伤害、明确受击等级与来源清理 |

## 三、资产现状

| 项 | 当前状态 |
| --- | --- |
| 原动画 | 848条AnimSequence；旧24条时长修正保留，本轮只读每片9时刻RAW采样，不修改原片 |
| 本体/骨架 | /Game/MHWI/Rathalos/Mesh/SK_EM001_Body 及 SK_EM001_Body_Skeleton，142骨/4材质槽；UE层级已实读，尚未与Blender逐骨映射 |
| 尾巴网格 | /Game/MHWI/Rathalos/Mesh/SK_EM001_Tail，3骨独立资产，本轮Basic使用本体骨轨 |
| 材质 | 4个、12贴图，既有RMT的R→Roughness/G→Metallic；本轮未编辑 |
| Basic资源 | /Game/MHWI/Rathian/Basic/ 下20动画副本、2DA、2BP、1地图，共25包；14片活动、6片早期候选不引用 |
| 坐标/地面 | 网格+Y前向；Body相对Yaw=-90、Z=-142；球根半径140、平地中心Z142，2cm工程间隙 |
| 骨名/盒 | 头bone_003、颌004、髋000、尾140..146；无bone_head。小咬颌盒、龙车头身双盒、尾翻142/144/146三盒 |
| 源数据保护 | 875文件最终hash不变，包括848原片、模型材质和用户已有脏训练地图/太刀DA |

材质既有配置不接CMML/FM，眼睛外Emissive已断开；本轮未重做该材质结论。

完整对象路径和全部阶段属性见稳定清单。正式资源：
- /Game/MHWI/Rathian/Basic/Blueprints/BP_RathianBasic，原生父类 /Script/IntroCpp.MHWIRathianApproxPawn。
- /Game/MHWI/Rathian/Basic/Blueprints/BP_RathianBasicGameMode，父类 /Script/Engine.GameModeBase，默认玩家 /Game/MHWI/Blueprints/BP_MHWI_Hunter。
- /Game/MHWI/Rathian/Basic/Data/DA_RathianBasic_Stats、DA_RathianBasic_Moveset。
- /Game/MHWI/Rathian/Basic/Maps/L_RathianBasic。

| 用途 | 活动源片与处理 |
| --- | --- |
| Idle / Walk / Run / Death | 00_003 / 健康00_007 / 00_067 / 03_031；残血00_065已撤下 |
| 小咬 / 龙车 | 02_001的BiteSmooth；00_003前摇→00_067冲刺→02_001的ChargeRecoverySmooth |
| 火球 | 00_081的SpitWindup/Release，去XY退步；仍为用户接受的工程张口演出，未证原作站地单火球 |
| 尾翻 / 起飞 | 08_002分段，Actor负责飞行高度 |
| 落地 / 恢复 | 08_005分为LandingDescend/Recovery；旧08_103悬空末姿不再使用 |

Armature是带90°旋转的导入根，bone_root为子骨；顶层Root Motion为0不足以证明原位。副本逐帧重建142骨轨，地面片段保留子根Z；飞行片段去除子根XYZ避免Actor重复升降，其他骨姿保留。20片1915根键读回符合处理公式；11个源片的曲线/通知/同步标记/骨属性为0，脚本预检后才允许裁片。RateScale保持1。

## 四、当前能力与验证边界

| 能力 | 当前实现与实际验证 |
| --- | --- |
| 巡逻/发现/移动 | 出生点附近巡逻、玩家0视距/视角/视线发现；统一策略决定接近/转向/出招。实测巡逻333.21945cm/s、接近最高1248.35003cm/s，平地维持Z142 |
| 四招与动画 | Native idle/walk/run→DefaultSlot；阶段Montage核运行/阶段/实例身份，自然结束衔接，中断不推进。四招均实际启动、命中并结束，死亡动画非循环且保持末姿 |
| 骨盒判定 | 骨骼局部有向盒、跨帧窗口裁剪、平移/旋转子步、阶段内每目标一次、来源→盒→目标遮挡；躲空、墙后不伤害和真实0.2s帧跨窗通过 |
| 单火球 | socket延迟生成，一次发射/结算，静态墙阻挡，来源死亡清理；基础可见球体，不是原作火焰VFX |
| 玩家受击 | 小咬Small、火球Medium、龙车/尾翻Large；两种持刀状态实际motion分别70/71/72和61/62/63，尾翻上抛高于龙车 |
| HP/死亡 | HP3000；实际伤害20/30/35/40，初始化不回血/复活；地面/空中死亡及拒绝再出招通过，死亡末姿保持 |
| 持续Landing | 丢失目标、动画中断、顶棚受阻均接地再恢复；正常尾翻峰值Z977.6、受顶棚阻挡峰值308.16，最终均Z142；空中死亡保持Dead |
| 验收 | 3轮代码各有冻结编译/新Luna审查/主审、原项目离线构建；最终二进制上24项真实PIE、101断言通过，未将启动成功代替用例通过 |

击飞仅在现有Attribute实际扣血、角色存活且非反击霸体时执行。小咬前向/上抛300/0、火球550/260、龙车850/380、尾翻600/620cm/s；实际水平速度还受玩家既有动作影响。盒体、窗口、伤害、飞行和决策值均标EngineeringFixture，不能据本轮PIE宣称原作COL/THK或LR资格闭合。

ConfigureApprox一次性幂等，更换数据需新建/重生Pawn。原生类默认值是未完整配置模板，正式运行使用Basic蓝图/地图。地图为平地基础场景，未验证NavMesh绕障、多人、全部闪避/反击/霸体回归、长期游玩或原作逐帧视觉对照；本轮正常连段与有限中断采样不等于每帧观感穷举。

忠实首链问题仍开放，Basic运行通过不替代其修复（详见[总账](../Reference/MHWI-Rathian-Evidence.md)第六节）：
- R-DATA-007：移动与碰撞未核共享单位/速率/来源/clip身份。
- R-COMBAT-013：按Actor后写覆盖较早精确TOI，首尾轴一致不证明中间纯平移。
- R-ANIM-013：旧首链InPlaceSequence缺根轨资格，Basic新副本没有迁移该首链配置。
- R-AI-003：strict resolver仍缺原生条件provider，动作结束未接ResumeAfterAction。
## 五、UE 5.8 API 差异（编译时踩过）

| 旧写法 | 5.8 正确写法 |
| --- | --- |
| `SkinnedMeshComp->bUseUpdateRateOptimizations` | `bEnableUpdateRateOptimizations` |
| `SetAnimation(Seq, bLoop)` 两参 | `SetAnimation(Seq)` 单参 |
| `Comp->SetPlaying(false)` | `Comp->Stop()` |
| UObject 接口类名任意 | 必须 `I` 前缀，如 `IMHWIRathianDecisionPolicy` |
| `TSoftObjectPtr<UAnimSequence>(TEXT("..."))` | `TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("...")))` |
| `PlayAnimMontage`（组件方法） | 使用匹配的AnimInstance图及DefaultSlot，再调用 `AnimInstance->Montage_Play`；不向普通AnimInstance调用SingleNode的SetAnimation |
| 手工拼 `FAnimSegment` | `UAnimMontage::CreateSlotAnimationAsDynamicMontage(...)` |
| `Montage_GetIsPlaying` | `Montage_IsPlaying` |

运行时动态 Montage 必须挂 `UPROPERTY(Transient)`，否则二次 GC 后悬空。

## 六、怎么跑

运行：打开 /Game/MHWI/Rathian/Basic/Maps/L_RathianBasic 后Play，使用已配置蓝图。玩家初始约50m外，可先看巡逻再靠近。不要用旧原生summon入口替代Basic。

资产读回脚本为 Scripts/MHWI/author_rathian_basic.py；真实PIE脚本为 Scripts/MHWI/pie_rathian_basic.py，每例独立PIE，以最终case_status及PIE-<case>.json为准。author_clips遇到已有目标会拒绝，不要为验证重新覆盖整套创建。完整调用顺序与结果见当前交接。


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
