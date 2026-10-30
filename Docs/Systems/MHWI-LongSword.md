# MHWI 太刀训练模组

## B20当前实现与运行（2026-10-27）

[B20开发与调试](../Reference/MHWI-B20-Animation-Development-20261027.md)：已修复动态翻滚Montage复制为零时长的播放阻断；六段合格基础过渡与四链TwoBoneIK/Profile已保存并实际运行。014/015已证为翻滚到移动/转身，不是落地片段。目标快照为end/mid骨骼相对偏移，避免IK反馈漂移。两种姿态S/M/L受击恢复12例/95检查通过；其余最终结果见B20报告。完整原生mode0、全来源/Phase、移动物理和原生solver/CTM仍开放，项目适配不冒称原作复刻。下方验收与B19段落保留其历史范围。

## 原版装备挂接修复（2026-10-28，已实现、最终验收由用户进行）

[原版挂接证据与实现](../Reference/MHWI-Native-Mount-20261028.md)已追到独立的 `uWeaponMain`（刀）和 `uWeaponSub`（刀鞘）消费者。挂点来自猎人 LMT 中功能骨 `30/47` 的缩放 Y 通道，数值是选择标记，不是装备的几何拉伸。主装备匹配2、刀鞘匹配3，4为共享；按原始记录顺序和向下取整的源帧采样。选择结果0使用 `bone_002` 背部初始配置，1使用 `bone_047`，2使用 `bone_030`。`bone_030` 是 `bone_008` 的子骨，`bone_047` 是 `bone_012` 的子骨；不能用项目旧的左右手命名代替这条数据关系。

当前 `FMHWIWeaponAttachmentRuntime` 已改为消费实际全身 Montage 的源片段、源帧及基础移动片段，跟随最终猎人姿态中的选中挂接骨。有效动作选择0即背挂，不能被 UE 底层中立姿态的持刀选择覆盖。刀、刀鞘仍保留各自独立骨架；整件挂接与 `wg03_00` 内部手柄动画分别驱动。标准背部初始配置采用原版两条相同记录：功能骨2、源平移(-47,51,-24)、XYZ角(89,-4,41)、比例0.8；手部挂接基础比例1。源骨选择缩放被剥离，比例按原版0.15秒曲线切换。导入坐标的固定旋转由原始 LMT 和 UE 姿态直接验证，不再使用掌心/蒙皮拟合点或逐招交接窗口。

`UMHWIAnimInstance::UpdateEquipmentIK` 的双臂装备 IK 权重保持0，保留源动画手臂姿态，避免用上一帧武器拟合点拉动手腕的反馈。脚部地面约束仍按既有资格运行。蓝图中旧挂接 UPROPERTY 暂保留兼容已保存资产，正式运行挂接不再读取这些拟合参数。此次UE 5.8 Editor构建已通过（10个动作，88.34秒），详细日志见新变更记录；用户最新指定最终验收自行进行，本轮不执行自动PIE握持画面验收，当前静态数据核对不等同于运行握持通过。原生挂点切换约0.15秒旋转补偿尚未实现；原版附加层、部分特殊状态/比例覆盖也未完整接入，不能据此宣称完整切换姿态保真。

[B21旧取证](../Reference/MHWI-Weapon-Mount-Evidence-20261028.md)与[CHG-20261027-007](../Changes/CHG-20261027-007-mhwi-hand-grip-ik.md)保留历史。B21只检查武器侧事件，遗漏猎人骨轨选择标记；其“没有挂点数据、拟合方法成立”的结论已由本次原生消费者证据更正。CHG-007的3750项检查基于旧拟合目标，不能证明刀柄与源动画手部的真实握持正确。

## R06/R28/R30专项验收（2026-10-27）

[专项裁决](../Reference/MHWI-R06-R28-R30-Acceptance-20261027.md)：**三项完整交付均不通过。** R06修复源码可确认，但原生mode0、全来源/逐连接运行仍缺；B19构建与14项PIE等七份报告在当前检出不存在，只保留历史声明。R28六候选未接过渡状态机；R30无预定Profile资产与四链求解节点，现有制作脚本仅创建/绑定配置。87项处置重建及75个不同动画文件存在性已核对，不等于全部运行。编辑器当前退出，本轮未启动游戏/UE/PIE、未编译或保存资产。

## 前次验收（2026-10-26）

[B13/B14/B15更新验收与B16复验](../Reference/MHWI-Acceptance-Update-20261026.md)：验收时的A05/A06已在B16静态修复：登龙合格接触预排至多七段，正式DA已将下劈首击HitLagSeconds置0并清空HelmLand旧七窗；UE 5.8构建、DA保存读回和22项离线检查通过。未运行PIE，运行验收由用户操作。35项总状态不变；A01/A04在B19完成代表性修复，完整来源与运行覆盖仍开放；手柄A02以及R19/R31剩余原版边界仍开放。下方B13、B15及更早段落保留各批次历史范围。

[静态验收报告](../Reference/MHWI-Acceptance-20261026.md)：R06因B12受击锁阻断恢复入口降为部分完成；另发现组合键重发、开启预设影响键鼠、菜单阻断遗漏来源缓存。该历史验收未运行复现。B15已修复A03键盘设备混用及键盘无关键重发；B19已修复A01/A04的代表性路径，完整来源覆盖仍开放，手柄A02仍未处理。历史开发/编译结论不覆盖这些回归；运行调试由用户操作。当前统计以总台账为准。

## B19 R06/R28/R30动画覆盖处置（2026-10-27）

[方案](../Plans/PLAN-20261026-006-mhwi-animation-coverage.md)、[交接记录](../Changes/CHG-20261027-001-mhwi-animation-coverage.md)。R06修复武器`One0=0`播放前拒绝（项目UE BlendIn后备）、真实受击来源合法恢复和菜单来源缓存/内部提交阻断；此前两次构建Succeeded、代表性PIE 14/14通过。原生mode0、缺来源身份及32引用逐条运行仍未完成，N86继续不可达。

R28六候选只完成UE资产读回和移动事实数据层；`bAccelerating/bDecelerating/bJustLanded/TurnDirection`已加入AnimInstance，但005/006/007/008/014/015没有接入ABP过渡，左右转身/落地语义不猜配。R30正式DA 32招选择值只有0/1/2/3，004/005保留但无原生入口；新增项目IK Profile类型与四链目标快照，**没有创建Profile资产或ABP TwoBoneIK节点**，四链仍无运行消费者。87项逐项处置见`Saved/MHWIRestoration/B19-20261026/animation-coverage.json`；后续按用户要求不验证，未再新增编译、PIE或文档检查。

## B15 PC键盘适配（2026-10-26）

[方案](../Plans/PLAN-20261026-003-mhwi-keyboard-adaptation.md)、[变更记录](../Changes/CHG-20261026-006-mhwi-keyboard-adaptation.md)。仅调整键盘/鼠标及HUD：LMB/RMB/Ctrl及四种官方组合替代R/F/G/Q/C直达快捷键；E仅在拔刀时纳刀，纳刀RMB不触发突刺，Shift按姿态冲刺或请求纳刀。键盘与手柄使用独立Action、Held和边沿，`bOriginalInputPreset`不再改变键盘语义；组合要求本帧有新成员边沿，无关键不重发旧组合。新增只读请求序号/最后命令诊断，不改变出招许可。静态源码与手势模型49项PASS；本机无可用UE5.8，**未编译、未运行PIE**。手柄A02、过渡动画和其他战斗机制不在本批。

## B16 B14实施收尾（2026-10-26）

[B14方案](../Plans/PLAN-20261026-002-mhwi-evidenced-mechanics.md)、[变更记录](../Changes/CHG-20261026-005-mhwi-evidenced-mechanics.md)。修复A06：一次真实下劈接触即按首延迟/间隔/上限预排七段队列，段记录共享接触目标的弱引用及目标相对点；既有计时循环在低帧下会结算所有已到期条目。正式`/Game/MHWI/Data/DA_MHWI_LongSword`现已把下劈首击hit lag归零并移除`HelmLand`直接七段。预览幂等/全字段保护、正式保存读回、磁盘SHA一致和22项离线校验均通过；UE 5.8 Editor构建成功，**未运行PIE**。多目标选择、取消、空间/部位与真实运行时序不宣称完成。

## B17离线静态取证收尾（2026-10-26）

[逐项取证报告](../Reference/MHWI-Forensic-Completion-20261026.md)、[变更记录](../Changes/CHG-20261026-009-mhwi-forensic-completion.md)。指定安装EXE指纹与固定分析源匹配；归档清单48/48 SHA匹配，19个续查函数快照19/19重追踪匹配。确认当前安装有5个相关`nativePC`覆盖：两个COL覆盖解析后改动击退字段，三个居合延迟SHLP覆盖增加32字节且语义未解码。R07/R09/R10/R13/R18/R19/R20/R21/R29/R30均完成本轮离线证据归纳，但因条件/空间/目标/伤害/求解或运行时序仍有开放边界，台账状态不变。未改玩法，未启动游戏/UE/PIE。

## B13取证更新（2026-10-26）

续查按用户额度前保存要求归档：输入缓存/执行双许可、转向20行表、耐力扣除消费者和原部位肉质表已补证，19函数快照与解析器见[B13续查保存点](../Reference/MHWI-Outstanding-Evidence-20261026.md)。完整取证尚未完成，玩法未改。

[消费者证据与剩余缺口](../Reference/MHWI-Outstanding-Evidence-20261026.md)：确认Q名义每6秒扣5%、回旋合格接触锁存后update/exit提交、登龙/居合接触后shell延迟、普通回避13帧保护计时、特殊纳刀3.5秒等待。**B13当时取证未完成且未修改正式玩法。** B12的两处依据已被推翻：10秒暂停颜色衰减，0.4秒是登龙shell延迟；R-COMBAT-017待运行；A05/A06静态问题由B16处理。下方B12及更早开发记录保留历史含义，不能覆盖本次更正。运行调试由用户操作。

## B12全台账处置（2026-10-26）

[全量矩阵](../Reference/MHWI-Ledger-Disposition-20261026.md)、[本批记录](../Changes/CHG-20261026-002-mhwi-ledger-sweep.md)。本批逐项处理35项：R11停止把10秒“不衰减”字段加到颜色T；R15补登龙空中126首击（COL #28，源碰撞25–112）；R22新增结构化命中结果；R24新增受击S/M/L控制状态；R26禁止非登龙/翻滚地面动作在Falling启动；R27新增UI输入阻断；R31新增表现hit lag与命中事件；R01/R05/R08新增原版手柄预设（默认关）、同帧手势解析与居合适配路线标记；R33新增51项静态基准。代码增量编译通过，**未运行PIE**；正式DA仅改`SpiritHelmBreaker`一窗与`IaiSpiritSlash`两条适配位。下方B10/B08及更早段落保留其当时含义。

## R06当前交付（2026-10-25，B10）

[B10现状](../Reference/MHWI-R06-Remaining-Development.md)：R06剩余三项开发全部完成，未编译/测试。实际受击Step、弹刀Creep、KijinComboShot/Slinger拥有者已通过原生身份和真实Montage实例接入；SpiritI/StepSlash专用入口全分支、有序请求、MotionTree/request混合门控、线性姿态插值及独立Actor时钟已实现。新增32段动画，CDO硬引用并在BeginPlay建立角色独立运行定义，未保存正式DA/地图/蓝图。node86保持无入边/0记录。开发结果见[本批记录](../Changes/CHG-20261025-005-mhwi-r06-remaining.md)与[32行台账](../Plans/MHWI-Connector-Progress.md)；下方B08/B07及历史验证保留其当时含义。

## B08当前连接播放实现

角色已消费R06连接核心，使用源帧Phase、原生前向结束flags、原MBD默认行与主段入帧。Action71主段已纠正为112并保存正式资产；RollStepSlash改引完整101，129由连接控制器调度；311独立TIML不会被共享308骨轨吞掉。上挑固定119→107按原自定义入口实现。未编译/测试。Step/Creep/KijinComboShot等前置玩法未接入，混合权重仍有缺口，完整R06未关闭；详见[B08现状](../Reference/MHWI-R06-Character-Playback.md)和[逐连接台账](../Plans/MHWI-Connector-Progress.md)。以下既有批次段落保留其历史范围，当前状态以B08为准。

更新：2026-10-25。源素材、现有 Ninja 角色和此独立训练模组是三个不同层次。资源获取历史见 [素材记录](../Changes/CHG-20261022-001-mhw-longsword-source-assets.md)，实施范围见 [方案](../Plans/PLAN-20261022-001-mhwi-longsword-module.md)。

同日[批判性审查](../Reference/MHWI-Restoration-Review.md)记录了修复前349资产文件、32定义/149路由/29个Montage的快照。用户已授权按[逐项开发台账](../Plans/MHWI-Restoration-Progress.md)推进完整原版还原。B01现已保存原生基础数值与五处既有路线修正，当前32定义/148路由/29个Montage；详见[本批记录](../Changes/CHG-20261024-007-mhwi-native-basics.md)。完整四色居合追加命中、命中空间、Q衰减及精确取消等仍未完成，不能将B01或历史PIE通过等同于完整还原。

最新B02已修复气刃踏步18/28弱强消费、A/B接气刃插入上挑、插入上挑R的III/I原序分支，并删除插入突刺的自定B出口；当前32定义/149路由/29个Montage，见[B02记录](../Changes/CHG-20261024-008-mhwi-spirit-branches.md)。B01的低槽拒绝属于当时适配，已被新证据纠正；所有窗口数值仍为既有项目调校。

首阶段完成源采样修复和独立武器内部动画：36段合格平行动画导入、27处正式 Montage 段引用替换；六条武器 Sequence 按19个源事件运行。该阶段边界见 [采样/公开资料说明](../Reference/MHWI-Native-Fidelity-Implementation.md)、[CHG-20261024-002](../Changes/CHG-20261024-002-mhwi-native-fidelity-implementation.md)；后续最新状态如下。

后续实施已扩展独立防御窗、逐输入取消窗和连续握柄/刀鞘交接；三条有色居合Montage依据共享骨轨证明改用合格Native308，累计30组正式段引用迁移。[CHG-20261024-003](../Changes/CHG-20261024-003-mhwi-defense-routes-transfer.md)区分已经运行验证的防御与尚待完整验收的视觉/路由。用户现改为参数优先：[批处理说明](../Reference/MHWI-Native-Parameter-Pipeline.md)提供425字段、164动作和4条IK链的统一数据库，21处支持属性已直接从原始W03P批量导入；停止以逐动画目测为主路径。

2026-10-23 已实现见切/气刃突刺映射、气刃插入续接、右键循环、持刀翻滚出口、转向窗口和登龙物理阶段；最终 C++ 构建、重启后四套真实PIE回归通过，正式资产已保存。[资料核对](../Reference/MHWI-LongSword-Behavior-Research.md) 区分源 FSM/TIML 事实与未知运动参数；[本轮记录](../Changes/CHG-20261023-001-mhwi-behavior-implementation.md) 记录验证范围，未声称原版逐帧一致。

B07已取得玩家加载器→连接表→Phase精确选择→动画结束→MBD主段入帧执行链，控制核心与124条身份记录已写入Source；26个源采样片段已导入`/Game/MHWI/Animations/R06Staging`。**AMHWICharacter尚未消费新核心，正式新增调度0条，R06未完成**。主片段105/112原生构造绑定、MBD混合和根运动/武器/事件时钟适配继续开发。见[实施现状](../Reference/MHWI-Native-LinkMotion-Implementation.md)、[本批记录](../Changes/CHG-20261025-002-mhwi-link-motion-core.md)及[逐连接台账](../Plans/MHWI-Connector-Progress.md)。本轮未编译或测试。

## 运行入口与资产

在编辑器打开 `/Game/MHWI/Maps/L_MHWI_Training` 后 Play。地图的 `DefaultGameMode` 为 `/Game/MHWI/Blueprints/BP_MHWI_TrainingGameMode`，默认 Pawn 为 `/Game/MHWI/Blueprints/BP_MHWI_Hunter`，父类 `AMHWICharacter`；HUD 为原生 `AMHWIHUD`。原项目菜单、Ninja 角色和默认地图保留。

| 完整资产路径 | 用途 |
| --- | --- |
| `/Game/MHWI/Character/SK_MHWI_Hunter` | 原素材六部件统一的 225 骨猎人；Skeleton 为同目录 `SK_MHWI_Hunter_Skeleton` |
| `/Game/MHWI/Weapons/SK_MHWI_LongSword`、`/Game/MHWI/Weapons/SK_MHWI_Scabbard` | 独立武器/刀鞘骨架，按角色骨挂接，不用 Leader Pose 共享错误编号 |
| `/Game/MHWI/Animations/LongSword/A_w03_00_###` | 全部 164 条有效太刀动作，保留源序号；未映射条目不表示已接入玩法 |
| `/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_###`、`NativeFidelity/Common/A_co00_00_###` | 新采样平行库36段；正式Montage累计迁移30组引用，三色309/310/311依据共享骨轨证明复用Native308；原Skeleton和基础移动BlendSpace不变 |
| `/Game/MHWI/Animations/Weapons/A_wg03_00_000..005` | swo001独立骨架的六段内部动画；正式DA的WeaponMotions及每招WeaponMotionEvents驱动，非整件武器挂点数据 |
| `/Game/MHWI/Animations/Common/A_co00_00_001`、`203`、`090`、`130` | 正式纳刀待机、步行、跑步、翻滚；后三项使用同目录完整前缀。034/035 是攀爬上下行，037 是明显低姿态循环，均不再用于地面走跑；039/089 为保留的对照资源 |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter` | 父类 `UMHWIAnimInstance`；Speed 驱动纳刀/拔刀两个 BlendSpace，经 bSheathed 混合后进入 DefaultSlot |
| `/Game/MHWI/Animations/BS_MHWI_Drawn`、`/Game/MHWI/Animations/BS_MHWI_Sheathed` | 基础速度混合与 0.14 秒输入平滑 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | `UMHWIMovesetData`，32 个招式定义，包括姿态/颜色变体、两条气刃插入身份和翻滚踏步斩 |
| `/Game/MHWI/Montages/M_*` | 太刀招式全身根运动 Montage；居合按气刃颜色选不同源动画 |
| `/Game/MHWI/Materials/M_MHWI_Surface`、`MI_*` | 18 个原部件材质实例，连接原颜色/法线；71 张贴图保留来源目录，尚未还原完整原版 shader |

训练场有三个原生 `AMHWITrainingTarget`，**当前地图默认均为被动木桩**，普通连招练习不会受到周期伤害；目标有真实属性血量，不使用仅显示的假命中计数。此前 `MHWI_CounterTarget` 默认每 4 秒攻击一次、造成 12 点伤害，容易被误认为自身攻击扣血，现已在[训练场修正](../Changes/CHG-20261022-005-mhwi-training-damage.md)关闭。

需要见切/居合反击练习时，在场景中选中目标（如 `MHWI_CounterTarget`），于 Details 的 MHWI 分类勾选 `Enable Attacks`，再 Play。距离内会按 `AttackInterval` 周期、提前 `TelegraphSeconds` 显示预警并造成 `Damage`；不是目标被打时立即反伤。取消勾选即恢复被动。此修改仅改变当前训练地图和地图生成脚本的配置，原生 `AMHWITrainingTarget` 类本身的缺省值仍为 true；手工新增原生目标时应明确设置该属性。

## 操作与派生

| 输入 | 行为与前置条件 |
| --- | --- |
| WASD / 鼠标 | 移动/观察 |
| Shift | 纳刀空闲时按住奔跑；拔刀时通过普通输入许可请求纳刀，不绕过动作窗口 |
| 原版手柄预设 | `bOriginalInputPreset`仅影响手柄，默认关闭。键盘始终走独立PC组合解析；手柄A02旧组合重发仍未修，RT+A/跨帧窗和全局仲裁仍无源 |
| E | 仅拔刀状态请求纳刀；纳刀时不伪造成使用道具或拔刀。手柄和直接`RequestInput(ToggleSheathe)`保持既有语义 |
| 左键 / 右键 | 纳刀左键拔刀；纳刀右键不提交突刺。拔刀左键纵斩循环、右键突刺；突刺后左键接上挑，上挑右键接突刺。B01删除了原项目右键无限循环的新增突刺出口 |
| W + 左键 | 持刀前进斩WalkOnSlash，原生7的115→101专用入口 |
| 左键 + 右键，配合移动输入 | 袈裟；镜头水平朝向把移动输入转换到世界方向，相对选择前角色右轴决定左/右，无输入或死区内默认后退。之后 Ctrl 接气刃踏步斩，再接气刃 III |
| V / 手柄D-pad Left | 气刃连段合法窗口进入投射器连射；方向随移动意图，源第36帧发射并扣弹药；随后Ctrl续气刃段。精确输入/伤害仍为项目适配 |
| Ctrl | 拔刀后气刃 I → II → III → 大回旋；逐段消耗槽，大回旋命中升色并最终纳刀 |
| 气刃 I/II 后左键或右键 | 分别插入突刺/上挑，使用独立 `SpiritComboThrust` / `SpiritComboRisingSlash` 身份；再按 Ctrl 继续气刃 II/III，保留普通突刺/上挑的其他出口 |
| 气刃踏步后左键/右键；插入上挑后Ctrl | 两种输入都接气刃插入上挑；Ctrl先判断目标气刃III完整槽成本，够则III，不够后备I，I保留弱斩。插入突刺仅A接普通上挑，移除自定B出口 |
| 攻击后 Ctrl + 右键 | 见切：区分低槽/正常保护，消耗剩余槽；成功反击仍须回斩真实命中才补满槽并允许Ctrl回旋。B01将左键出口修为踏步斩；B11按原FSM补齐右键→突刺、Ctrl+左键→登龙突刺（复用Light适配窗1.5–2.6667，精确帧仍属R07） |
| 攻击后 Ctrl + Space | 特殊纳刀并定格持刀姿态最多 3.5 秒（B13已证明原等待计时，完整保持/播放仍待取证）；左键居合二连，Ctrl 居合气刃，Space 翻滚 |
| 居合气刃 | 命中反击窗口保留气刃等级；未成功反击消耗一级，采用 Iceborne 语义 |
| Ctrl + 左键，升空后再按攻击 | 需白刃以上；气刃突刺命中后上升并进入物理滞空。空中左键/右键/Ctrl或其组合请求下劈；173 自身播放到 25/60 秒才提交快速下砸和七段授权。B12补空中首击126 MV（COL #28，源碰撞25–112帧）；B16将0.4秒用于首段shell延迟，一次合格接触预排七段，正式DA已清空HelmLand旧窗。无空中攻击或提交前过早落地，不结算七段、不降色；本行为尚未PIE验证 |
| Space，随后左键 | 纳刀/拔刀分别使用相应根运动翻滚；只在设定窗口免伤。持刀翻滚窗口或结束后 0.15 秒内左键接 `RollStepSlash`；纳刀对应拔刀斩。中断、死亡、收刀和过期会清除恢复上下文 |

气刃槽0–100；白/黄/红伤害系数1.05/1.1/1.2，基础持续195/135/60秒。B14当前实现Q名义每6秒扣5%，回旋合格命中后在退出提交清Q、升色并刷新颜色余量及10秒暂停；这两段资格/时序仍待运行确认，技能与完整时钟边界见[B13证据](../Reference/MHWI-Outstanding-Evidence-20261026.md)。气刃I/II/III/回旋消耗15/15/20/25，I不足槽可弱斩；B02确认气刃踏步20是强化消费：不足20时允许18弱斩且不扣槽，够20使用28并扣20，两者命中回槽10。数据均直接取原COL/W03P，消费语义由无槽记录和一手攻击表互证。居合二连真实命中回槽15秒、反击后命中30秒；登龙实际下劈提交后非红10秒/红15秒回槽，速率100/15每秒。取消窗仍为项目调校，完整伤害/部位/技能模型尚未还原。

B01从原COL直接恢复14招既有窗口的动作基值/回槽，包括气刃III的14+19+34、居合二连18+13；三种袈裟左键出口改接突刺。`FMHWIHitWindow.SpiritLevelDamage`为空时兼容旧Damage，有配置时按该动作启动捕获的颜色选择基值，再应用现有倍率。居合气刃首击为无/白/黄/红17/19/31/39；登龙空中首击MV126，延迟shell按颜色10/15/25，0.4秒起、0.05秒间隔、最多七段；有色居合接触后0.5秒追加白/黄/红55/72/86。B16已保存正式DA并移除HelmLand旧直接七窗。1.3部位伤害公式、刀刃空间、目标/部位选择和原版完整HP公式仍未还原；上述shell未运行验证。

防御独立半开窗口：见切正常反击0..33/60、无敌0..45/60；起始槽不足10时无反击、仅0..13/60基础无敌，回斩实际扣血才满槽。居合斩5帧；居合气刃反击12帧，无敌无色12/有色14帧。见切/居合成功给1/2秒霸体，减伤50%但实际扣血，死亡仍发生；显式中断清霸体，普通派生保留。当前无回避性能/衣装扩窗，不能把这些基础窗扩称全部原作技能配置。

## 调度、根运动与伤害契约

实现入口：[MHWICharacter.h](../../Source/IntroCpp/MHWI/MHWICharacter.h)、[MHWICharacter.cpp](../../Source/IntroCpp/MHWI/MHWICharacter.cpp)、[动作数据](../../Source/IntroCpp/MHWI/MHWIMovesetData.h)。独立角色只有一个前台动作，不同时驱动旧 `AMyPlayerCharacter.Actions`。请求与事件契约见 [MHWI-001 / DAMAGE-001](../Interfaces.md)。

- 基础移动由 CharacterMovement 驱动，移动动画锁根；所有动画锁根使用 REF_POSE 保留导入根骨旋转基底。攻击与翻滚保留 Root Motion。登龙上升 171 临时 Flying 保留垂直根轨迹；Air/Strike 的 172/173 忽略零根轨迹，改用 Falling 物理速度/重力。整条链只保存一次移动/根运动快照，着地、打断、死亡或退出时恢复。
- 普通动作/派生在 Montage 0..0.12 秒内按镜头相对移动意图有限转向，默认最多 25°、360°/秒；只动相机无移动输入不转身。前后 Montage 区间求交，低帧跨过整个窗口仍处理。见切返回段另有 46..68/60 秒、45°预算；袈裟/翻滚不叠加通用转向。以上角度、速度和窗口是项目调校，不是已解码的原版常数。
- 登龙阶段为 Rise → Air → 可选 Strike → Land；起跳命中、下劈提交与真实着地分别驱动，不能靠完整动画时长串联。`Landed()` 只记录着地事实/执行序号，Tick 在安全边界切段；Air/Strike 禁止从中立 `StartMove` 绕过合法链直接启动。这两条Montage禁用自动混出，长落差时暂停在尾帧保持姿态，由落地退出。
- 命中、派生、反击以 Montage 秒数为准，源 TIML 帧按 60 FPS 转换。窗口检查使用前后帧区间交集，窗口内每个目标只扣一次；多段有独立去重集合，槽收益每窗口一次。
- 普通近战使用随胶囊根位移的球形前向扇区扫掠，`WeaponMesh`/`ScabbardMesh`碰撞关闭；它不是原作刀刃几何复刻。B19只读取证已将太刀39条`CollisionTimelineObject`动作轨全部关联到`wp03.col`时间UID，确认攻击记录引用13组几何参数；续查将`CLND`类型1解到节点工厂类`cCollNodePl`，但`CLGM`字段含义、几何形状、骨骼空间和消费者仍未知，因此原作数据当前不可直接用于忠实碰撞实现，见[B19武器碰撞取证](../Reference/MHWI-Weapon-Collision-Evidence-20261026.md)。登龙突刺记录真实扣血目标并以弱引用沿合法空中派生传递；下劈合格接触会排入最多七段延迟shell，正式HelmLand不再有直接伤害窗。打断/死亡/退出会清登龙阶段标记，碰撞场景和PIE仍未覆盖。
- `RequestInput` 活跃期间返回 true 只表示缓冲，不保证派生成功；0.3 秒缓冲仍需满足取消窗口、资源和命中/反击条件。缓冲记录实际收到输入的Montage位置，不能在结束回调中追溯命中已经关闭的历史窗口；低帧补算只检查真实跨越的尾段。`StartMove` 仅空闲时可启动，供蓝图/验证调用；正常操作经过 RequestInput。
- 动作拥有执行序号和 Montage 实例身份；死亡、UnPossessed、EndPlay、外部结束按同一清理路径处理，避免旧回调结束新动作。
- 属性伤害在扣血前经过 `IIncomingDamageResponse`，由当前翻滚/见切/居合窗口拦截；未实现接口的原角色保持既有路径。此为本地玩法，未做网络复制。
- B12起每次命中先构造 `FMHWIResolvedHit`（MoveId/Window/ColRecordIndex/MV/颜色/弱斩/反击/FinalDamage），再按原公式扣血；`GetLastResolvedHit` 可蓝图读取。斩味/会心/部位阶段显式为 `Unavailable`，不伪造倍率。
- 命中后按窗口 `HitLagSeconds` 冻结动作与武器表现时钟（不冻结槽/颜色计时）；`OnHitResolved(SourceTime, WindowIndex, ColRecordIndex)` 为后续音效/特效/相机提供唯一命中事件。登龙首击的正式DA值已改为0；0.4秒供延迟shell首段，不再作该首击表现冻结。真实hitstop/音效/刀光/相机仍未实现或验证。
- 受击 S/M/L 挂载时进入 `EMHWIControlState` 对应状态，拒绝新输入并清 Pending/Helm 请求；受击结束回 Free，死亡置 Dead；此全程锁定同时阻断B10受击恢复派生（A01）。`SetInputBlocked` 仅部分门控动作输入，遗漏NativeSourceInput撤销及内部提交检查（A04），也未门控移动/视角，完整菜单接入待完成。
- 非登龙、非翻滚的地面动作不能在 `Falling` 状态启动；空中行为必须走显式分支，避免从中立输入绕过合法链。

## B03基础循环采样迁移

正式DA的idle/walk/run/sheathed_idle/sheathed_walk/sheathed_run及两张BlendSpace六样本现采用`/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_001`、`A_w03_00_004`和`Common/A_co00_00_001`、`A_co00_00_203`、`A_co00_00_090`。源采样/FBX合格证据、Skeleton/时长及导入来源经重新核对。保持REF_POSE强制锁根、既有倍率和180/420速度；这些速度/倍率/混合仍是项目适配。五段循环迁移及短移动冒烟通过，起停/转身/落地、原版速度/逐帧对照仍待开发。定向入口为[author_locomotion_fidelity.py](../../Scripts/MHWI/author_locomotion_fidelity.py)，详情见[B03记录](../Changes/CHG-20261024-009-mhwi-locomotion-animation.md)。

2026-10-26 B18 解析 `w03_00.lmt` 的005/006/007/008/014/015头字段；它们尚未列入NativeFidelity资格清单，编号不能直接当起步/停步/转向语义。新增[补充证据](../Reference/MHWI-R28-R30-Evidence-20261026.md)及[移动过渡方案](../Plans/PLAN-20261026-004-mhwi-locomotion-transitions.md)，R28仍部分完成。

## B05连接原生逻辑与来源修正

原FSM名称/箭头/Action与MBD明确一致：左128/node8/Action82、右127/node9/Action83。B05已修正来源表及两个制作/生成入口；正式左右动画、窗口和操作没有安排修改。361→127@22、362→128@24的来源冲突由此消除，状态为待测试。原EXE代码区已只读取得；311前置LinkMotionPhase=1已收集，但退出/Phase1初值、重置、选择、后备及提交时钟尚未取得完整指令证据，新增连接0条。最新要求不测试；见[CHG-011](../Changes/CHG-20261024-011-mhwi-native-connector-logic.md)和[下一阶段通过准则](../Plans/MHWI-Connector-Acceptance.md)。

## B04连接动画取证进度（历史）

原`w03_00.mbd`已解析30连接节点32次引用的主段startFrame表；此前仅查FSM/TIML而遗漏MBD。已有129→101的48帧制作参数改为直接读原文件，正式动画原值未变。361/362分别指向127@22/128@24，与项目左右映射冲突；118另有目标112候选。连接退出、Phase1选择及混合消费者尚未查清，未新增连接播放，已有129的29/60退出仍属项目适配。每条状态见[连接台账](../Plans/MHWI-Connector-Progress.md)，实际验证见[CHG-010](../Changes/CHG-20261024-010-mhwi-connector-evidence.md)。

## 来源与再制作

2026-10-24 新增[完整源审计](../Reference/MHWI-Source-Fidelity-Audit.md)和[分阶段方案](../Plans/PLAN-20261023-001-mhwi-source-fidelity.md)。本次保留164动作的全部19类TIML、90个FSM节点和307条条件/连接；旧五类过滤器遗漏954个事件组。正式32招Montage仅覆盖原生30个连接节点的32次片段引用中的129，其余31次未调度。源输入位含义、主段入帧/优先级、角度索引和变速插值仍未完整解码，当前每招统一取消窗/0.3秒缓存、直接主段混合与固定转向均属项目适配。本次编辑器只读核对没有改变这些正式行为。

[moveset_mapping.json](../../Scripts/MHWI/moveset_mapping.json) 保留源 FSM 条件、TIML 碰撞启停、MotionSpeed 和姿态推断。FSM ActionNo 与 LMT MotionNo 不同，不能混用。取消/反击/无敌帧尚未从原始标志完整解码；MotionSpeed 采用本地线性插值。武器来源矩阵见 [weapon_attachment.json](../../Scripts/MHWI/weapon_attachment.json)。

2026-10-23 映射为 `M_ForesightSlash` → `/Game/MHWI/Animations/LongSword/A_w03_00_140`、`M_SpiritThrust` → `/Game/MHWI/Animations/LongSword/A_w03_00_170`；碰撞窗口分别为 70..80/60 秒、84..97/60 秒。左右袈裟按UE真实位移纠正为 `M_FadeSlashLeft` → 128/node8/action82、`M_FadeSlashRight` → 127/node9/action83（B05修正此前来源节点/Action写反，片段不换），来源/窗口/速度随片段迁移，不能用源root X符号直接当UE角色左右。持刀翻滚连接 `M_RollStepSlash` 使用完整 129（0..29/60 秒）接 101（48..150/60 秒），总长 2.183333 秒；早期通过源骨姿态端点扫描选择48；B04原MBD确认129→101的startFrame字段也为48，制作入口已直接读原表。新制作/端点核对入口为 [author_behavior_corrections.py](../../Scripts/MHWI/author_behavior_corrections.py)、[audit_behavior_links.py](../../Scripts/MHWI/audit_behavior_links.py)，后者不保存 Blender 源文件。定向修正可分别调用 `fade_direction_corrections()` / `aerial_montage_corrections()`，不会重建动画段。

`UMHWIMovesetData` 的物理初值为向上 700、向前 200 cm/s、重力 1250 cm/s²、快速下降 3000 cm/s，提交时刻 25/60 秒。它们是项目初值，尚未证明与原版参数组、单位和倍率一一对应；当前重力通过默认世界 980 cm/s² 的比例换算，自定义重力体积需另验。Air/Strike 的转向调整攻击朝向，尚不重算水平漂移速度。

[import_assets.py](../../Scripts/MHWI/import_assets.py) 分批导入，[export_common.py](../../Scripts/MHWI/export_common.py) 默认导出正式四条通用 FBX，也可在 `--` 后指定源片段，仅补充指定文件。[author_assets.py](../../Scripts/MHWI/author_assets.py) 制作基础材质、Montage、Data、角色和训练场。脚本可能重写同名新资产，执行前先保留人工编辑。已存在训练地图不会被 training_map() 重建。

运行证据在 `Saved/MHWIImport`；[pie_behavior_corrections.py](../../Scripts/MHWI/pie_behavior_corrections.py) 提供 ground/direction/air/lifecycle 定向套件，读取正式 DA 并注入实际 Enhanced Input，报告 `PIE-behavior-<suite>.json`。旧 [pie_moveset.py](../../Scripts/MHWI/pie_moveset.py) 的自动登龙时序假设已过时，不能原样作为本轮回归通过依据；[pie_smoke.py](../../Scripts/MHWI/pie_smoke.py) 仅覆盖基础移动/根运动/扣血。执行与结果须以本轮变更记录为准，脚本存在或启动成功不代表通过。

最终整套报告 `PIE-behavior-all.json` 在新二进制/磁盘重载资产上通过，覆盖普通RMB六连、三轮气刃插入、持刀/纳刀翻滚、17种袈裟输入（含同帧按下/松开）、普通/派生转向、空挥/无输入/提交前落地/主动七段、5000cm高落差尾帧保持、中断/死亡和取消窗口前后输入。记录410条断言（含重复逐帧采样，非410个独立场景）；10 FPS方向另通过104条。最终自然Air约1.407秒，主动下劈红刃168伤害分7次、降一级；这些是当前项目参数下的实测，非原版精确标定。

完整原版特效/音效、染色层与毛发 shader、斜坡/空战/骑乘/飞翔爪、逐招原始取消帧和联网均未还原。当前是可继续调校的独立地面太刀模组。

## 武器与刀鞘骨架、挂接现状（2026-10-28）

刀 `/Game/MHWI/Weapons/SK_MHWI_LongSword` 和刀鞘 `/Game/MHWI/Weapons/SK_MHWI_Scabbard` 保留独立源骨架，通过猎人挂接骨变换移动整件组件，不使用 Leader Pose。`WeaponMesh` 的 AnimationSingleNode 消费配套 `wg03_00` 六条内部动画与源事件；其中武器自身 `bone_002` 是手柄内部骨，与猎人背部功能骨2同号但不是同一骨架，不能混用。

源骨选择器和原版初始配置已替代 [attachment_fit.json](../../Scripts/MHWI/attachment_fit.json) 的运行拟合、掌心标记和猜测交接窗口。正式动作按所播放 Sequence 的源身份与帧查询，实际挂接骨遵循 `30/47/2` 选择；所有权可在动作内切换。详见[原版挂接证据](../Reference/MHWI-Native-Mount-20261028.md)。旧制作脚本和旧蓝图字段仍可能保留历史拟合值，不能据此推断当前运行位置；此次未重写原 FBX 或 SkeletalMesh 比例。

原版手臂 IK solver、CTM、完整附加层/状态消费者仍未完整复刻。B18的四条源骨链与八项 IK 文件指纹仍是有效资源证据，但不构成原算法运行证明。当前双臂关闭项目装备 IK，源手臂直接驱动挂接骨；脚部保留地面约束。此次真实握持、拔纳刀和居合视觉验收按用户最新指令由用户操作；本轮不执行自动视觉验收，历史45项或3750项拟合检查不再作为当前验收依据。

## 动画映射修正（2026-10-22）

本次用户对照指出气刃 II 与上挑互换，现为 `/Game/MHWI/Montages/M_SpiritII` → `A_w03_00_106`，`M_RisingSlash` → `A_w03_00_107`。气刃 II 源碰撞窗口为 33–41 帧，上挑为 22–29 帧；DataAsset 的命中秒数、取消入口与片段长度同步调整，保留两招各自伤害、消耗和派生语义。不是只交换 HUD 名称。源静态表的旧标签是推断，本次依据用户识别与 UE 姿态对照纠正。

纳刀 BlendSpace 正式样本为 0 cm/s 的 001、180 cm/s 的 203、420 cm/s 的 090；203/090 的源平均水平速度约 135.04/365.51 cm/s，Sequence RateScale 为 1.332921/1.149071。保持 CharacterMovement 移动、REF_POSE 锁根和 0.14 秒混合平滑。034/035 的根轨迹为竖直攀爬，不能再按 LoopFrame=0 推断为地面走跑。

局部修正使用 `author_assets.animation_corrections()`，保留其他动作调校。先用 MCP `animation.set_montage_sequence` 替换两条 Montage 的段，并用 `animation.set_blend_sample` 更新纳刀 BlendSpace 第 1/2 项，再运行该函数同步窗口与数据。`moveset()` 也采用新映射，但已存在 Montage 的序列需显式替换。

[pie_animation_corrections.py](../../Scripts/MHWI/pie_animation_corrections.py) 使用真实 Enhanced Input 执行走跑、六次左键和完整气刃链，并将双腕/头部的运行姿态与修正后的源 Sequence 对照。验证结果、初次失败及回退见 [修正记录](../Changes/CHG-20261022-004-mhwi-animation-corrections.md)。预览脚本必须复制 Unreal Map 后制作临时数据，避免零消耗预览值残留到正式动作。

训练场安全配置由 `author_assets.passive_training_targets()` 对当前已打开训练地图定向更新，禁止在 PIE 中保存默认值；新地图生成也将三个目标设为被动。[pie_training_damage.py](../../Scripts/MHWI/pie_training_damage.py) 的 `run('verify')` 不会强制关掉目标，先检查保存的默认值，再验证范围内站立、近战自身血量、目标真实扣血，以及运行夹具中显式开启目标攻击后的外部伤害与见切拦截。
