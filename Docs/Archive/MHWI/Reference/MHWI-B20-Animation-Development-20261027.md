# B20：翻滚入口、基础过渡与四链 IK

本批按用户最新授权进行开发、编译及真实PIE，覆盖此前“运行由用户操作”的安排。基线为`02a72404a5301c4b313e651b148775fca54193dc`；开始时已有专项验收文档修改，已保留。方案见[PLAN-20261027-001](../Plans/PLAN-20261027-001-mhwi-remaining-animation-development.md)。

## 已实施

### R06：动态载体与真实来源

实际调试发现，运行时翻滚模板长度为`1.333333373`秒，但`DuplicateObject`复制到PIE角色后的载体长度为零；引擎`Montage_PlayInternal`拒绝非正长度。B19的mode0后备不能解决这个独立问题。

`MHWICharacterLinkMotion.cpp::CopyNativePlaybackMontage`对动态模板改用UE的`CreateSlotAnimationAsDynamicMontage`工厂重建；仅接受单Slot、完整单段、一次循环、单位段速率及无Montage通知的已支持模板，不手填长度。正式Montage仍使用原复制路径。新载体由角色UPROPERTY持有，连接提交与直接播放共用此处理。

R28新增消费者后，014/015已是真实姿态拥有者。`PrepareNativeLink`不再让已结束翻滚的缓存优先覆盖它们；只读`GetLastNativeEntryDiagnostic`记录实际目标/前置身份、源bank/motion/frame/phase和首段/主段，不提供强制写状态入口。`GetLastMoveStartFailure`用于定位播放拒绝；`GetNaturalRollCompletionSerial`只在拔刀翻滚自然结束时递增，中断不算完成。

### R28：六段合格源与实际 AnimGraph

新[原生消费者证据](../../Tools/MHW/native-locomotion-evidence.json)从固定EXE及分析.text重建19个函数和6个绑定：

| 源片段 | 已证明的原生拥有者/选择 |
| --- | --- |
| w03_00_005 | WALK Action1小角度入口 |
| w03_00_006/007 | WALK转向入口，按水平叉积符号选择 |
| w03_00_008 | WALK_END Action2入口直接请求 |
| w03_00_014 | DODGE_TO_MOVE Action65入口直接请求 |
| w03_00_015 | DODGE_TO_TURN Action66构造+0x30，通用入口消费 |

**014/015是翻滚到移动/转身，不是落地动画。** WALK角门限由W03P文件`0x18c=70°`经参数加载器写`+0x348`，再由入口乘deg2rad比较。没有按文件名猜左右/落地语义。

六段均完成源骨轨采样、FBX回读及导入，目标目录为`/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_005`等六个完整同前缀资产，Skeleton为`/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton`。REF_POSE、force root lock；角色只从Montage提取根运动，因此这些基础过渡不叠加额外位移。

`UMHWIAnimInstance::UpdateLocomotionTransition`根据真实加速度意图、地面/拔刀状态和自然翻滚完成事实选择片段及显式时间。实际SequenceEvaluator与布尔混合接在既有基础BlendSpace之后、DefaultSlot之前。攻击、受击、菜单、空中、死亡撤销过渡；时间结束返回基础循环。完整原生FSM、移动速度/物理及落地分支未在本批猜配，UE状态适配与源绑定分开记录。

### R30：Profile与四条实际求解链

已保存并绑定`/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile`。实际`/Game/MHWI/Blueprints/ABP_MHWI_Hunter`具有四个TwoBoneIK节点，姿态顺序为：基础循环/过渡 → DefaultSlot → LocalToComponent → 左脚 → 右脚 → 右臂 → 左臂 → ComponentToLocal → 输出。

| 链 | root / mid / end |
| --- | --- |
| 左臂 | bone_006 / 007 / 008 |
| 右臂 | bone_010 / 011 / 012 |
| 左脚 | bone_014 / 015 / 016 |
| 右脚 | bone_018 / 019 / 020 |

Effector、JointTarget分别是相对**本次基础姿态end/mid骨骼**的偏移，节点目标空间为BCS_BoneSpace；不把上帧求解后的绝对骨骼位置再次作为本帧目标。无拉伸、保持末端相对旋转。Profile极向配置仍为项目component-space偏移，游戏线程转换成骨骼偏移后供图消费。

右掌对齐实际带权武器握点，特殊纳刀时左掌对齐鞘口；脚部检测地形高度相对胶囊当前地面高度的差，平地偏移为零，保留基础步态抬脚。战斗/受击压制四链，特殊纳刀保持只启用双臂；空中/菜单/死亡全部清零。握点、探测尺寸、Alpha及UE双骨求解是明确的项目适配，不能冒称原生solver。

## 实际验证与证据保存

本机证据统一位于`Saved/MHWIRestoration/B20-20261027/`，包含源码/资产备份、源指纹、导入读回、图连接、构建日志、PIE成功和失败报告。正式[图配置清单](../../Tools/MHW/b20-animation-graph.json)记录交付资产的角色GUID、空间、骨名及30条连接；它不是独立确定性重建器。

- `extract_locomotion_consumers.py`：固定源指纹，19函数、6绑定重建比对通过。
- `build_outstanding_evidence.py`：默认113动作、18函数/18资源快照比对通过；可选动作bank扩展没有改变旧默认结果。
- `verify_outstanding_followup.py`：19/19续查函数一致。
- 最终`pie_remaining_animation.py`：60 FPS上限34项、15 FPS上限34项、多视角37项通过，包含实际移动、两次真实翻滚、014/015到R06的Action65/66来源诊断、特殊纳刀双臂、双脚地形及门控。左脚与右脚分别在常规/低帧运行中测量。
- `pie_r06_impact_matrix.py`：两种姿态 × S/M/L × Light/Spirit，共12例、95项通过（含真实来源身份/源motion检查）。原失败夹具因连续根运动走出有限平台，逐帧证据显示最后一例已在`z≈-1955`坠落；现在每个地面用例回起点并等待真实着地，未放宽地面招式门控。
- 最终二进制`pie_r06_repairs.py`：14项通过，覆盖播放、合法/非法恢复与菜单缓存。
- `pie_weapon_transfer.run(max_fps=30)`：178类断言、3750次逐帧检查通过，实际内部动画0–3、源骨姿态/握点、特殊纳刀/居合、中断/死亡后旧事件均覆盖。非strict模式保留既有hold73适配，不能证明原生event80完整消费。
- 手臂测试使用瞬态AnimInstance Profile副本改变极向，验证实际肘骨响应并恢复；脚部使用visibility-only瞬态地形夹具。测试不保存正式DA/Profile。

截图冻结只用于多角度姿态检查，不能验证原作节奏或3.5秒计时。旧14项报告与本批重跑分别保存；失败的夹具/API/业务诊断均保留，不删除后宣称首次通过。

## 仍不能宣称原作完整还原的边界

| 条目 | 本批未补造的对象 |
| --- | --- |
| R06 | 原生mode0 MotionTree/request仍是项目BlendIn后备；N53/N60全部来源/Phase与32引用尚不能用代表性测试认证；332/333/334缺Action78/node51真实前置；N86无入边/0记录继续不可达 |
| R28 | 已接通六段明确来源；完整原生移动FSM、速度/物理与独立落地入口未闭合，不能把014/015当落地替代 |
| R30 | 原生solver限位/极向、manager匿名字段、坐标变换与CTM未完全解码；004/005内部武器动画保留，未制造触发 |

纠正此前专项验收的一处范围误判：`co00_00_181/182`是B10制作时附带尝试、明确非必需的失败请求，[B10报告](MHWI-R06-Remaining-Development.md)已写明“不计本轮缺失资源”。B20重查后排除为必需缺口；不能拿其他bank中同编号条目作别名补齐。27个其他公共来源的静态拥有者包括地震/风压/起身/道具/限制解除，不能自动等同当前六种受击源。

当前三项均有实际开发和运行证据，R30由“取证中”推进为“部分完成”；整项忠实还原继续保留上述缺口，不将项目适配、静态证明或代表性运行泛化为全部通过。

六份最终PIE共3964次检查（包含重复逐帧断言），精简原报告、全部不同断言及指纹保存在[受版本控制的运行证据](../../Tools/MHW/b20-animation-runtime-evidence.json)。构建、静态源重建、实际资产读回、保护DA指纹和三张唯一文件名截图一并定位。早期截图虽然功能断言通过，但视觉检查发现旧文件/空视角，已排除；最终独立相机三角度逐张查看保留同一保持姿态。运行期间训练地图发生额外保存，归属未确认，当前字节与Git基线已备份于B20/ObservedMap，未擅自覆盖共享地图。
