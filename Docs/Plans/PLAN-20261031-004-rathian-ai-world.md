# PLAN-20261031-004：雌火龙 AI、移动与狩猎状态细化方案

- 状态：draft / 待选择技术方向；本文件是实施步骤，不代表玩法已实现。
- 日期：2026-10-31
- 用户需求：总体还原 MHWI 雌火龙，分子代理细化实现步骤，缺数据时定向解包。
- 关联模块 / 接口 / 问题：enemy-ai、mhwi-longsword、mhwi-rathian-animation；既有 AI-001/002/003、MHWI-001；R-AI-001/002。
- 主方案：[总体方案](PLAN-20261031-002-rathian-restoration-master.md)；前置：[原作证据管线](PLAN-20261031-003-rathian-evidence-pipeline.md)。
- 实施记录：尚未实现；本次仅官方资料检索、项目源码与文档静态核对、方案编写。未编译、未启动原作、未执行 PIE、未保存 UE 资产。

## 现状与目标

### 官方结论（Epic UE 5.8，2026-10-31 检索）

| 正式来源 | 可支持的机制 | 无法据此得出的原作结论 |
| --- | --- | --- |
| [StateTree Overview](https://dev.epicgames.com/documentation/unreal-engine/overview-of-state-tree-in-unreal-engine?lang=en-US)、[Quick Start](https://dev.epicgames.com/documentation/unreal-engine/statetree-quick-start-guide) | 层级状态、条件、任务与转移可以组织 AI；同一活动状态内任务并行，任务完成可触发转移 | 不证明雌火龙采用 StateTree，也不给出怒/疲优先级、概率或招式表 |
| [Behavior Tree Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/behavior-tree-in-unreal-engine---overview) | UE 提供事件驱动 BT、Blackboard 与中断机制 | 不证明任意 Selector 顺序能复现原作决策 |
| [AI Perception](https://dev.epicgames.com/documentation/unreal-engine/ai-perception-in-unreal-engine?lang=en-US) | 组件接收 Sight/Hearing/Damage 等刺激，回调供项目处理 | 不提供原作发现距离、记忆、仇恨与换目标公式 |
| [Navigation System](https://dev.epicgames.com/documentation/unreal-engine/navigation-system-in-unreal-engine?lang=en-US) | 地表碰撞生成 NavMesh，路径和代价可供地面代理使用 | 不证明地表 NavMesh 能完成自由空中寻路，也不给出原作区域迁移线路 |
| [Movement Components](https://dev.epicgames.com/documentation/unreal-engine/movement-components-in-unreal-engine?lang=en-US) | CharacterMovement 支持 Walking/Flying/Falling 等模式和根运动输入 | Flying 是运动模式，不是雌火龙飞行控制律或三维路径求解器 |

以上机制各有适用条件；Epic 没有可直接套用的 MHWI 雌火龙完整实现。表中页面检索结果标示 UE 5.8；带 `application_version=5.8` 的部分页面本次打开失败，因此保留实际成功检索地址。落地 API 仍须对照本机 UE 5.8 头文件。

### 项目现状证据（本次静态核对）

- [EnemyAIController.cpp](../../Source/IntroCpp/EnemyAIController.cpp) 当前是 Tick 驱动 Patrol / Chase / Attack / Dead，攻击范围与冷却来自 UEnemyData，不含雌火龙的多动作决策、飞行或狩猎生命周期。
- 同文件 OnPossess 内创建默认感知子对象，对应 [R-AI-002](../Known-Issues.md)。这是静态风险，本次没有运行复现。R-AI-001 的 Dummy 控制器为 null 是历史编辑器快照，本次未再次读 CDO。
- [EnemyBase.cpp](../../Source/IntroCpp/EnemyBase.cpp) 用单个 AttackMontage；播放失败时直接执行伤害。不能把此回退移植为原作忠实规则。
- [ShooterStateTreeUtility.cpp](../../Source/IntroCpp/Variant_Shooter/AI/ShooterStateTreeUtility.cpp) 已有模板 StateTree 任务及弱执行上下文用法；它操作 ShooterNPC，不是雌火龙系统。
- [IntroCpp.Build.cs](../../Source/IntroCpp/IntroCpp.Build.cs) 已声明 AIModule、StateTreeModule、GameplayStateTreeModule；[uproject](../../IntroCpp.uproject) 已启用 StateTree/GameplayStateTree。项目具备依赖不等于雌火龙已接通。
- [雌火龙动画库](../Systems/MHWI-Rathian-Animations.md) 记录 848 条 AnimSequence、历史目录 `/Game/MHWI/Rathalos/Animations`，工具未创建雌火龙 Montage/AI/动画蓝图。848 是多 bank 有效片段数，不能等同 848 个招式或 LR 动作集合。
- [既有采集方案](PLAN-20261030-003-mhwi-rathian-datamine.md) 记录 em001/00 的 THK×105 与 thklst；它们是怪物 AI 取证入口，不能套用太刀 wp FSM。此数量引用已有采集记录；本子任务未重解包。

### 原作事实、缺口和目标

首个验收 profile 为 MHWI 普通雌火龙 `em001/00` 的下位单人场景；上位、大师和任务倍率另做 profile。`00` 目录本身不证明下位专属，HR/MR 专有动作不得混入 LR 资格表。

[LR 数据页](../Reference/MHWI-Rathian-LR-Data-20261030.md) 已报告发怒、耐力、状态等字段和完整读取边界；例如发怒 Duration 80、LR 疲劳时长 70、捕获比例字段 30%。这些是带上游命名的静态参数证据，不自动证明计时起点、暂停条件、捕获组合条件和事件优先顺序。AI 选择、连段约束、头部/尾部朝向、取消条件、怒疲互斥/共存、区域迁移仍需消费者链或受控观测。

目标是每个可执行决策都能追溯到原文件、字段消费者或原作运行样本；开发夹具和估算参数明确标注，不能进入忠实 profile 的最终验收。

## 范围与验收标准

按依赖分三层交付，不用完整生态阻塞最早战斗验证：

| 层级 | 内容 | 完成条件 |
| --- | --- | --- |
| A：单区战斗 | 发现/丢失/追击、原作合格动作选择、转身、地空切换、怒/疲/受控状态、死亡 | 相同原作场景下，动作资格、提交朝向和打断顺序可对照；未知决策不伪造通过 |
| B：完整狩猎闭环 | 陷阱/麻醉/捕获、失去战斗、受伤退场、进食/休息/回巢、区域连接 | 具备地图、任务、状态和触发证据；捕获与死亡互斥，场景卸载无残留任务 |
| C：扩展生态 | 多目标切换、其他怪物/争斗、地形互动、HR/MR、调查等任务差异 | 每项另有源数据和场景；单体战斗通过不能替代生态还原 |

死亡、捕获及 EndPlay 属于最早必须设计的终结清理；B 层仅推迟捕获完整规则与生态内容，不推迟资源释放。

## 技术方案

### 必须由用户选择的候选

| 候选 | 有出处的能力与项目契合点 | 代价与忠实度边界 | 进入条件 |
| --- | --- | --- | --- |
| A：StateTree + C++ 动作/移动执行组件 | Epic StateTree 层级状态/事件；项目已启用相应模块 | 便于查看行为与任务生命周期，但需要把 THK 决策重建为等价条件；手工选择器可能改变概率和顺序 | 选择该承载方式；最小 THK→动作链、取消/优先级已闭合 |
| B：Behavior Tree + C++ 执行组件 | Epic BT/Blackboard/中断；已有 AIModule | 目标/导航组织直观；持续动作需要额外 RunId 与 abort 清理，需新建 BT/Blackboard；不能继承简单追击即认为完成 | 选择该承载方式；对等价中断和连段制定回归 |
| C：THK/thklst 解释或编译为可重放策略 + UE 执行适配 | 原作主载体来自本机采集记录；UE C++/Actor/组件可承载执行 | 原始条件、函数与随机源可能未闭合；解析成功不等于执行器正确。工程与取证投入最高，没有 Epic 官方原作兼容解释器 | 选择该路线；维护者格式与本机消费者核验闭合，未知 opcode 拒绝执行 |

推荐将 A 作为当前评估首选，以复用项目已有依赖；这只是方案建议，未经用户选择不新建运行类、StateTree、BT 或解释器。A/B 都可消费经证实的 THK 规则，但不能借此宣称原生重放。若高保真验收要求精确选择分布且 THK 不能等价翻译，应重新评估 C。此处没有确定最终技术方向。

下文的逻辑契约适用于三个候选；StateTree 任务名仅为选择 A 后的拟议落点。

### 所有权与数据流（拟议）

`任务/等级配置 → 原作行为条件和观测快照 → 决策策略 → 动作请求 → 动作执行/运动/攻击 → 结果事件 → 决策策略`。

- `AMHWIMonsterCharacter` 持有组件与引用，`AMHWIMonsterAIController` 管理感知、目标和路径请求；均拟放 `Source/IntroCpp/MHWI/Monsters/`，当前不存在，不修改旧 EnemyBase 继承关系来暗中替换训练目标。
- 拟议 `UMHWIMonsterStateComponent` 是 HP 引用、怒/耐力/控制状态、终结状态的唯一业务所有者。AI 图和 AnimInstance 读快照，不另扣耐力、计时或写 HP。
- 拟议 `UMHWIMonsterDecisionComponent` 消费策略快照，只请求动作。`UMHWIMonsterActionComponent` 独占当前 ActionRunId、动作时钟和结束原因，承接动画/攻击工作包。请求被拒绝时不能先消耗资源或改变模式。
- 拟议 `UMHWIMonsterMovementComponent` 或 CharacterMovement 的最小适配负责位移；具体基类由动画根运动核验与官方 API 可用性决定。规划阶段不同时写 ActorLocation、CMC 速度和动画根位移。
- 拟议 `UMHWIMonsterEncounterSubsystem` 在 B 层管理区域/任务终态；首版可只提供单区上下文。状态不能放在关卡蓝图定时器中分散维护。

这些类名与分工是项目方案推断，不是 Epic 或 Capcom 的既定架构。

### 逻辑状态与移动边界

行为逻辑可按 `NonCombat / Investigate / Engage / Controlled / Relocate / Terminal` 组织，`Engage` 再按 `Ground / Takeoff / Air / Landing` 分层。怒、疲劳、受伤和部位状态作为独立事实字段；没有原作依据前，不强行把它们做成互斥顶层状态。是否压制另一状态、何时触发吼叫/退场，由可追溯的优先级表裁决。

地面：NavMesh 只输出通行路径与期望方向，追击走跑和转身沿经核实的动作策略执行。起步、停步、转身、攻击提交有明确朝向写权限；攻击提交后是否可追踪及追踪角速率必须来自原作。不要直接复用 EnemyAIController::SetFocus 的持续目标朝向作为所有动作的规则。

空中：区分短时动作驱动腾空与跨区飞行。前者可在合格的根运动/Flying 适配下 sweep 移动；后者需要原作路线/区域连接及路径可达证据。固定飞行航点/样条、三维导航或手工补线都属于有代价的另选方案，不在本阶段默认添加第三方飞行插件。Landing 必须先核对地面与落点有效性，恢复地面导航后才允许地面动作。

地面 NavMesh 无路、飞行 sweep 受阻、目标失效时，返回可诊断 Failure/Blocked；不能瞬移、穿墙、补播攻击或以无限重试掩盖。允许的原作退避/转身/滞空动作有证据后再绑定。

### 取消、优先级和终态

每次请求生成新的 `ActionRunId`；完成/打断回调携带该身份。旧回调、旧路径请求或旧帧通知不得结束新动作。动作自然结束、条件拒绝、自愿取消、受控打断、死亡、捕获、OwnerEnded 必须分开记录。

同一帧发生受击、怒阈值到达、麻痹/倒地、致死、捕获条件和动作结束时，先收集事件，再由有证据的优先级表裁决；当前缺少该表，不能编造原作次序。工程层可先保证 Terminal 幂等、单一入口与无悬挂请求，但这只是项目安全契约。

终结执行顺序拟为：锁定终态与失效 RunId → 停止决策/路径请求 → 关闭尚未提交攻击与持续命中窗口 → 解除动作拥有的朝向/移动控制 → 播放合格终态表现 → 按任务规则广播一次结果。已生成投射物是否继续存在需原作证据，不能一律随母体死亡删除。销毁/卸载时解绑感知、动作、属性、路径委托与计时器；异步回调使用弱对象身份并回到游戏线程。

捕获是任务终态，不是把 HP 直接扣到零。拟议规则组合需要 HP 比例、陷阱状态、麻醉累积及免疫/等级/任务例外逐项核实；不能只用静态 30% 字段直接 Capture。回巢也不能等同于低血量触发，触发条件与目的地区域仍待原作证据。

## 接口与数据迁移

以下均为拟议新契约，当前不变更既有 AI-001/002/003 和训练目标接口。

| 接口 / 数据 | 单位与返回语义 | 调用方 / 所有权 | 迁移顺序 |
| --- | --- | --- | --- |
| `FMHWIMonsterContextSnapshot` | 位置 cm、距离 cm、速度 cm/s、角度 deg；原作单位保留源值及显式换算；对象用弱引用 | 状态组件生成，决策读取；含 SourceProfile、EncounterGeneration | 先固定字段版本与证据来源 |
| `TryStartAction(ActionId, Context) -> StartResult` | Accepted/Busy/Ineligible/MissingEvidence/InvalidAsset/Terminal；只 Accepted 创建 RunId | 决策调用，动作组件提交资源和模式 | 接动画/战斗工作包后验证失败不生效 |
| `OnActionFinished(RunId, Reason)` | 仅当前 RunId 可改变决策；Completed 不等于必然命中 | 动作组件广播一次，AI 按证据转移 | 验证重复/延迟回调拒绝 |
| `RequestMove(Goal, Mode) -> RequestId` | cm；结果独立报告 Reached/Blocked/Aborted/Invalid；RunId/请求身份隔离 | 控制器/移动适配独占请求 | 先地面后地空/跨区 |
| `ApplyStatusEvent(Source, Value, Frame)` | 保留来源单位、累计/持续语义和时钟域；拒绝未知 profile | 战斗提交，状态组件归并 | 先记录后绑定真实消费者语义 |
| `TryCommitTerminal(Reason) -> bool` | 首个合法提交 true；重复 false；不等于捕获条件判定 | 状态组件唯一写入，任务系统观察 | 第一轮即接 EndPlay/死亡，捕获随后完善 |
| 行为资格和优先级表 | SourceHash、THK节点、条件、ActionId、rank资格、证据等级；未知项不可用于忠实 profile | 证据管线生产，AI策略消费 | 原值/解析/业务映射分层，不人工猜概率 |

拟议资产根为 `/Game/MHWI/Rathian/AI/`、`/Game/MHWI/Rathian/Data/`，名称均待方向选择后新建；现有动画实际路径继续引用 `/Game/MHWI/Rathalos/...`，不因怪物身份纠正搬移历史资产。新 Blueprint 的完整路径、父类、AIControllerClass、AutoPossessAI、组件及实际默认值必须在创建后读回，当前没有这些资产的核验结论。

## 实施步骤与依赖

| 步骤 | 输入与具体操作 | 输出与独立验收门 | 依赖 / 阻塞 |
| --- | --- | --- | --- |
| AI-00 冻结原作 profile | 固定 exe/归档指纹、普通 em001/00、LR任务ID与人数；登记 nativePC 覆盖；提取 thklst→THK 引用闭包 | 行为源清单、任务配置与覆盖差异表；身份不混 em002 | 证据工作包；任务ID/倍率不明则 profile 未合格 |
| AI-01 提取决策最小链 | 解码 thklst 表项、THK节点/条件/动作调用；连到 ACTP2/LMT/碰撞 UID；保存偏移/原值/源码版本 | 一条发现→接近→转身→动作→收尾链有逐边出处；unknown 计数可追踪 | 不以节点可读代替条件消费者语义 |
| AI-02 选择承载路线 | 比较 A/B/C 与已经闭合的链、需人工翻译的范围、维护成本；由用户确定方向后记录 | 明确选项及边界；长期选择新增 ADR | 在此之前不创建运行框架 |
| AI-03 建立隔离角色入口 | 新增怪物 Character/Controller/状态与动作接口；构造期建立默认组件，Possess 只注入配置；创建测试专用 BP | 只生成一个控制器；重复 Possess/UnPossess 无重复委托；不改训练场默认目标 | 主方案基础组件与资产已合格 |
| AI-04 接感知与目标上下文 | 添加敌我/可攻击资格过滤；配置来自合格 profile；分开保存本帧可见、最后位置和记忆有效期 | 可见、遮挡、丢失、目标死亡/销毁均有正确事件；无跨墙自动命中 | Perception 是适配机制，原作参数仍须取证 |
| AI-05 接地面移动和朝向权限 | 建大型代理 NavMesh 夹具；验证胶囊/身体真实尺寸；路径事件驱动行走/转身/停步，不逐帧重发同一路径 | 直路、窄路、不可达、悬崖和移动中打断；模型不因双位移漂移 | 动画根运动与比例工作包 |
| AI-06 完成一条战斗垂直链 | 先选证据最完整的单招，资格检查→转身/瞄准→启动→锁定/允许修正→执行→结束；失败返回原因 | 强制选择夹具与真实自动选择分开验收；同输入输出顺序可重放 | 动画、判定和伤害工作包 |
| AI-07 扩展动作与连段 | 按来源资格表批量接入地面/空中招式、连段约束、冷却/体力代价；记录所有候选与拒绝原因 | 每个 LR动作有正反例、取消点、连段入口/出口；不猜顺序或权重 | AI-01 必须覆盖该动作，未经核实保留禁用 |
| AI-08 接怒/疲/控制状态 | 先纯数据模拟，再绑定受击/动作消耗/时间；逐项核实时钟起点/暂停/重置及状态仲裁 | 阈值上下界、同帧多事件、速度/伤害倍率只应用一次；无永久锁定 | 仅参数已读不够，需触发与优先级证据 |
| AI-09 地空迁移 | 分别接起飞、空中停留/动作、被击落、落地；验证模式切换、重力/碰撞、Nav重接 | 天花板/斜坡/台阶/落点失效及空中死亡可结束；无地空双执行 | 原轨迹、模式与动作语义闭合 |
| AI-10 单区死亡与捕获 | 死亡第一轮就接；随后补陷阱/麻醉/捕获合法性、已捕获免疫与任务结果 | 致死、捕获竞争、重复事件和卸载均只出一个终态结果 | 捕获完整消费者/任务证据；不得凭30%独自完成 |
| AI-11 生态与跨区 | 补地图区域连接、可达路线、进食/休息、受伤退场/回巢；替换单区 encounter 夹具 | 导航中打断/卸载、回巢追击/恢复等实际场景；原作证据覆盖 | 地图与任务数据，单体战斗通过后进行 |
| AI-12 系统回归与文档 | 原作样本对比、低帧/长战斗、销毁/重开；汇总决策轨迹与来源覆盖 | 逐项验收报告，不用编译/冒烟替代忠实度通过 | 只运行与改动相称的检查 |

任务所有权、源时间和碰撞不由 AI 子任务重新实现；它们由主方案统一契约，各工作包对齐同一个 RunId 和 SourceProfile。

## 验证计划

本表是实施后的计划；本次没有执行这些玩法验证。

| 场景 | 方法 / 命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 源链验证 | 拟新增 `Scripts/MHWI/verify_rathian_behavior_sources.py`；独立重新读 THK/thklst 原字节与指纹，不从正式DA反生成预期 | 所有声明支持节点/动作身份可回溯；未知 opcode/缺引用拒绝 | 静态通过不证明决策运行等价 |
| 最小构建 | 按 [Development](../Development.md) 使用 UE5.8 Build.bat 构建 IntroCppEditor Win64 Development；涉及反射后再编译新蓝图 | UHT/UBT/新蓝图无相关失败 | 不证明玩法正确 |
| 感知/导航 | 真实 PIE：可见→遮挡→失效、地面可达/不可达、重复Possess | 明确事件/请求ID；无旧回调污染新行为 | 参数须来自合格原作 profile |
| 动作与状态交叉 | 强制动作夹具测试转身/commit/受击/麻痹/倒地/怒疲/地空迁移/死亡 | 可用与禁止情形成对覆盖；资源与所有权只结算一次 | 强制动作不验证自动选择概率 |
| 原作对照 | 相同版本、任务、位置/朝向、HP/怒疲/体力条件，多次采样记录 SourceProfile/候选/结果/帧时间 | 比较资格、序列、时序和分布；随机轨迹不要求无依据的逐次一致 | 原作记录缺项继续标待验证 |
| 低帧/长战斗 | 60/30/10FPS；事件跨帧、连续多轮怒疲、反复起落/捕获重开 | 无重复命中/卡死/泄漏；时间误差阈值由主方案统一 | 性能目标与原作保真度分别报告 |
| 文档 | `python Scripts/Docs/check_docs.py`；`git diff --check` | 新文档链接和格式可维护 | 不编译/不运行原作 |

建议诊断行包含 EncounterGeneration、Frame/SourceTime、RankProfile、SourceNode、Target、候选及拒绝原因、ActionRunId、移动请求ID、状态事件与终结理由。日志用于调试，正式玩家流程不展示原文件/偏移等实现细节。

## 风险与回退

- 最大缺口是 THK 条件/原生函数、随机与等级资格的业务解释；仅结构解码后直接写手工概率会产生无法核验的 AI。缺证据的招式保持未合格，取证优先于猜测。
- StateTree 多任务完成/退出、BT abort 或原生解释器跳转都可能引起重入；业务提交由组件持有，图退出只释放其拥有的请求。细 API 需按 UE5.8 实际头文件确认，不能照旧版签名照抄。
- 大型身体/翅膀与胶囊、Nav代理尺寸不一致会造成穿墙；根轨迹、运动碰撞与身体伤害判定分别验收。
- 回退按新测试地图/蓝图→新数据引用→新运行源码逆序撤销，恢复本批前资产指纹；不触碰既有用户未提交资产。原作/归档只读，提取产物可以保留作证据，不将采集逆转为删除游戏文件。
- 当前本地玩法，不声明多人同步、回放一致性或存档兼容已经实现；未来加入这些能力需单独方案。

## 文档同步清单

本次父代理统一更新 Plans/Changes 索引并记录方案交付；本子任务只新增此页。实施后再同步 Combat-AI 当前现状页、独立雌火龙系统文档、Interfaces 的真实新契约、modules.json 新入口和 Known-Issues，并逐阶段新增 CHG。未实现的拟议路径、资产和符号不要登记成当前模块能力。
