# PLAN-20261031-006：雌火龙战斗、碰撞、部位与太刀集成实施步骤

- 状态：draft / awaiting-direction；未实现怪物战斗、伤害公式或部位系统。
- 日期：2026-10-31。
- 用户需求：完整还原MHWI雌火龙，子代理编写分部分实施步骤。
- 关联模块：mhwi-longsword、character-actions、mhwi-unpack-data；拟议新接口未登记。
- 上级：[总体方案](PLAN-20261031-002-rathian-restoration-master.md)。
- 依赖：[原作证据](PLAN-20261031-003-rathian-evidence-pipeline.md)、[AI/世界状态](PLAN-20261031-004-rathian-ai-world.md)、[动画资源](PLAN-20261031-005-rathian-animation-assets.md)。
- 实施记录：尚未实现；本轮静态调查和文档交付由总体CHG记录。

## 现状与目标

范围为MHWI普通雌火龙em001/00，下位首个验收profile；全局动作/碰撞库混有等级相关记录，不能全部启用作下位招式。目标是太刀玩家和雌火龙双向命中、原作时序/几何/结算、部位和状态反馈形成闭环，随后扩展等级和完整狩猎机制。

本轮实际源码核对：

| 源码/符号 | 当前行为 | 对实现的影响 |
| --- | --- | --- |
| AMHWICharacter::AdvanceAction / SweepWindow | 使用当前/上次时间相交的DamageWindows；根前方球扫与侧向补扫；WindowIndex内Actor级去重 | 已有跨帧窗口检查，但不是原作刀刃轨迹与怪物部位几何 |
| AMHWICharacter::SweepWindow | 取目标UAttributeComponent、标记命中过后直接ApplyDamage；仅保存接触位置，不保留BoneName/PartId | 给怪物单独新增肉质组件不会自动接入；必须改双方交点 |
| AMHWICharacter::EmitDelayedShell | 登龙/居合延迟命中保存目标弱引用及Actor相对接触点，发射时仍直接ApplyDamage | 主击与延迟击都需统一桥接，避免绕过肉质或二次扣血 |
| FMHWIResolvedHit | 记录MV/颜色/弱派生/反击/最终值；Sharpness/Affinity/Part可标Unavailable | 当前FinalDamage不含完整MHWI公式；不能将现有数值称原作最终伤害 |
| UAttributeComponent::ApplyDamage | 调用IncomingDamageResponse拦截/调整，再扣血与广播；致死不再广播OnDamaged | 新战斗提交须复用/桥接此入口，重入和死亡顺序需保护 |
| IIncomingDamageResponse / AMHWICharacter | 处理翻滚、见切/居合、反击后减伤等；现接口只有float及Instigator | 缺攻击几何、伤害类型/状态/反应元数据，不能从一个float推全部后果 |
| IMHWIContactResponse | 返回接触大小和弹刀与否，参数级别为Actor | 需要部位化接触结果；不能以0伤害推断弹刀 |
| AMHWITrainingTarget | 训练木桩Attribute与定时范围伤害 | 保留兼容回归；木桩不是雌火龙AI或攻击 |

以上为静态发现，不等同本轮PIE通过。准确当前入口是SweepWindow与EmitDelayedShell，不应引用不存在的PerformHit作为实施位置。实际构建入口为Source/，不改参考副本C++ Source/。

原作数据已有基础HP3000、12行肉质、7组硬直原值、断尾阈值原值、怒疲劳/状态字段，以及342条ACTP2记录、70条COL攻击记录（主35+shell35）。这些来自本地固定归档/社区模板读取：

- 原值读取与结构往返证明文件解析边界；原名、等级资格、部位映射、最终公式/取整和运行消费者尚未全部闭合。
- HP3000不是任一任务最终HP。12行肉质不得直接按猜测命名头/翼/尾。
- COL type2攻击原值不是玩家实战扣血，70不是70种已确认下位招。
- PBC字段2006/2007不能当耐久；ACTP2的mLoopTime不等于整个倒地/口水硬时长。
- 原作本机可能存在nativePC覆盖；归档基线和当前安装覆盖必须区分，避免以Mod行为作为原版。
- 本轮证据子代理已补提73个外部raw文件（声音8、VFX52、任务/区域候选13），紧凑来源见[本轮解包证据](../../Tools/MHW/rathian-plan-evidence-20261031.json)。这不代表火球音画/任务倍率语义闭合，也未证明候选任务就是首个LR验收任务。

## 官方结论、版本与技术选择

先搜索了Epic正式资料，检索结果为UE5.8；以下结论仅支持UE实现机制，不支持Capcom机制或MHWI数值。

| 官方直接来源 | 可用机制 | 本项目需要补的依据 |
| --- | --- | --- |
| [Collision Overview](https://dev.epicgames.com/documentation/unreal-engine/collision-in-unreal-engine---overview?lang=en-US) | 对象/查询通道与Block/Overlap/Ignore响应 | 原作shape、骨附着与接触规则 |
| [Traces Overview](https://dev.epicgames.com/documentation/unreal-engine/traces-in-unreal-engine---overview?lang=en-US) | 按通道/对象类型进行空间查询 | 采样步长、旋转路径和多部位选择规则 |
| [Physics Asset Editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/physics-asset-editor-in-unreal-engine) | 骨骼网格物理体/约束及碰撞编辑 | 自动生成物理体不保证原作受击体 |
| [Data Assets](https://dev.epicgames.com/documentation/unreal-engine/data-assets-in-unreal-engine?application_version=5.8) | 类型化配置与PrimaryAsset管理能力 | 项目数据schema、缺失处理与版本迁移 |
| [Animation Notifies](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine) | 动画事件及持续窗口 | 原作事件ID/窗口与取消语义 |

可选路线需随总体技术方向由用户选定，当前只给有出处的机制与代价：

| 决策 | 候选 | 取舍/条件 |
| --- | --- | --- |
| 怪物受击体 | PhysicsAsset骨体；或独立QueryOnly骨附着shape；或显式原生几何求交层 | 前两者工具成熟；独立shape便于原生ID映射但组件/更新成本需测。自定义求交最可控，需实现并验证全部几何/扫掠 |
| 攻击碰撞 | UE逐骨shape Sweep；或原生shape轨采样+专用求交；或Overlap简化 | Sweep可复用查询，但单次线段不能覆盖长尾旋转弧。专用求交成本高。Overlap近似只能标阶段原型，不能直接过忠实度门 |
| 伤害宿主 | 保留Attribute扣血+类型化前置结算；或迁入GAS | 前者更贴当前项目、改动较小；GAS提供通用属性/效果工具，但需迁移猎人/木桩/敌人及验证，不因“官方存在”就自动选定 |
| 数值缺口 | 阻塞未合格招式；或明确“近似profile”允许玩法试验 | 忠实验收只能接受有证据链的阶段。允许近似需单独标识且不能混入原作期望 |

建议候选为保留当前HP宿主、增加类型化接触/结算适配，并以合格原生几何驱动UE查询；它是项目推断，待用户选定，不是官方指定方案。

## 状态所有权与拟议数据契约

以下文件/类是拟议落点，新增前先与主方案统一命名，避免AI和战斗各持一份怒气/耐力/倒地状态。共同身份使用EncounterGeneration、ActionRunId、PlaybackGeneration、LoopIteration和TargetSpawnId；当前执行由动作组件唯一持有，动画/碰撞/AI只携带它的授权身份。部位累计若独立拆Parts组件，则Combat提交到Parts而不复制第二份计数；HP唯一写入仍在Attribute。

| 拟议所有者 | 内容 | 不能重复持有 |
| --- | --- | --- |
| UMHWIMonsterCombatComponent | 当前生命profile、部位累计、异常累积、合法攻击Token、结算账本；HP最终写入唯一Attribute | AI不另扣HP、另算毒/破坏阈值 |
| UMHWIMonsterStateComponent或主方案统一状态宿主 | 怒/疲劳/受限/倒地/终态与优先级事实；当前动作只读动作组件快照 | Combat只提交状态事件，不创建第二套状态机 |
| UMHWIMonsterCollisionComponent | 骨/shape映射、已更新姿态样本、查询候选与接触原始事实 | 不决定怒气和AI下一招 |
| 动画组件 | 动作/循环/层的播放Token和源时间映射 | 不直接ApplyDamage |
| 猎人战斗桥 | SweepWindow/EmitDelayedShell→类型化Resolve→统一HP提交 | 旧直接扣血与新结算只能选一条执行 |

拟新增Source/IntroCpp/MHWI/Monsters/：

- MHWIMonsterCombatTypes.h：FMHWIAttackContext、FMHWIContactFacts、FMHWIDamageBreakdown、FMHWIHitCommitResult。
- MHWIMonsterCombatComponent.*、MHWIMonsterCollisionComponent.*、MHWIMonsterPartsComponent.*（是否拆组件待统一选定）。
- MHWIMonsterData.h：基础/任务profile、部位/肉质/阈值、动作窗口、shape与原字段来源。

每次攻击上下文至少带：

- SourceHash、MonsterVariant/Rank/QuestProfile、ActionId、MotionBank/Slot、CollisionUID/Record、WindowId；
- EncounterGeneration、ActionRunId、LoopIteration、HitGroup/RehitPolicy、ShellInstanceId；
- 源开始/结束及源时钟单位、物理/属性/异常类型、原始攻击标量、击退/防御/状态元数据；
- 攻击者/目标弱引用、骨骼和shape/部位ID、接触点/法线/扫掠时间；unknown字段显式缺失。

TryResolveContact返回至少Rejected、Deflected、EvadedOrCountered、Applied、Unavailable、StaleExecution；UnchangedHP不能同时代表弹刀、反击、无效目标和缺数据。结果保存每段来源状态；Unavailable不静默补倍率1后声称原作正确。

去重键的工程候选为(ActionRunId,LoopIteration,HitGroup,TargetSpawnId)，是否还需PartId、shell子段或再命中周期由原作规则决定。不能一律以每个Part各扣一次，也不能沿用全动作Actor一次去重吞掉应有连击。

所有伤害、累计、委托和Actor修改在游戏线程。发布外部委托前先记账并建立本次提交状态；回调后重查对象、当前执行代次和存活。动态委托目标UFUNCTION，EndPlay撤销引用/监听/形状/Timer。

## 双向伤害与状态的拆分原则

### 猎人→怪物

分开保存物理、属性、异常、气绝/夺气、部位耐久、切断、怒气累计等通道。拟pipeline为“武器/动作原值→确认的技能与状态修正→接触/弹刀→肉质与属性肉质→任务/怪物修正→原作取整→HP及各累计结果”，具体乘法顺序、上限和逐段取整仍要由原作消费者/运行测试闭合，不能把这个依赖顺序当成已确认公式。

太刀当前窗口Damage/MV、颜色和弱派生/反击可作为已知阶段输入；斩味、会心、武器面板/真实攻击、动作属性倍率、技能等若未实现，单列Unavailable或留在明确近似profile。不能直接将现有FinalDamage再乘肉质就称完整原作伤害。

延迟登龙/居合必须定义并取证“继承哪些攻击快照、何时选择肉质/部位、目标移动/断尾后如何处置、动作退出是否取消”；原实现的Actor相对点不是原生部位锚点证明。

### 怪物→猎人

分开处理攻击标量、任务攻击倍率、怒/疲劳资格、物理/属性、防御与减伤、异常累积、反应/击退、无敌/见切/居合/霸体。现有IncomingDamageResponse只接float，不能丢失原攻击上下文。拟引入带Context的桥接，但继续让现有许可/反击结果决定是否提交HP，防止反击消费后新模块仍追加异常或击退。

毒、火异常、吼叫、风压、震动、拘束可能有非HP通道；不能因COL Motion_Value=0就丢弃，也不能把数值为正的任何攻击一律当可反击。无敌与状态阻断关系须分别取证，当前方案不猜。

### 部位与全身状态

硬直、倒地、口水硬、气绝、麻痹、睡眠、毒、爆破、耐力/疲劳和怒气分别持有累计/计时，但由统一状态优先级决定能否打断。部位破坏、断尾、HP死亡可同击触发，事务顺序需根据原作证据确定；工程上至少要求幂等、只提交一次且日志可重建。不能将所有阈值共用一个“stagger条”。

## 细化实施步骤与依赖

### C0 冻结基线与攻击/部位资格

1. 保存现有太刀、训练木桩及动画数据快照，确认源游戏EXE/归档/nativePC覆盖指纹。
2. 读取原解析器与完整报告，建立AttackId→动作条件/源时间窗→COL UID→shape→BoneId→PartId/HitzoneRow及等级白名单。
3. 任务profile单独保存HP、攻击、部位耐久/状态倍率、体型、任务资格；基础值与任务倍率不能混写。
4. 将未解骨映射/时间窗/攻击资格/公式阶段列入阻塞表；先选择一条证据完整招式闭环，不按日文名字或观感猜。
5. 对技能/装备依赖固定首个猎人测试loadout，明确原作伤害对照环境，避免以不同武器/防具对比。

验收：每个启用攻击及部位均有唯一来源与测试条件；unknown不能被导入器默默置零。

### C1 单部位无AI双向闭环

1. 新建专用测试地图及雌火龙Actor候选，保留当前训练场。装配合格本体、统一HP宿主和一个已确认部位，不先启用自由AI。
2. 在当前SweepWindow的ApplyDamage之前引入类型化可选桥；支持怪物走新结算，旧木桩/其他目标维持原行为。
3. EmitDelayedShell使用同桥，不能出现主击新公式、延迟击旧公式。接触结果统一返回是否命中、HP变化、反击/弹刀、回槽许可与反馈事件。
4. 临时以无伤害trace显示碰撞候选和所选部位，验证身体多shape同时接触仅按原作选择规则提交一次。
5. 用一个已确认怪物攻击通过现有IncomingDamageResponse命中猎人；反击/翻滚拦截结果返回怪物桥，防止二次扣血。

验收：一击一个提交ID、一次HP变化；缺部位映射拒绝并报原因；木桩兼容无新增伤害；主击/延迟击路径一致。

### C2 原作碰撞与跨帧推进

1. 分离移动阻挡胶囊、受击体、攻击体和观察/感知体，定义独立查询通道及响应矩阵。
2. 将原生骨/形状局部坐标转换为UE骨空间，并在最终已评估姿态后取样；记录根轨、骨姿和查询先后顺序。
3. 每个有效窗口覆盖整个上次到当前源时间区间；窄窗口被10FPS跨过仍应取样。运动采样同时考虑骨端旋转弧、源轨变速与攻击形状半径，不能只扫当前两端直线。
4. Sweep返回多body后先解析Part/Hitzone，按原作规则排序/合并，再进入唯一结算；命中地面/墙时的阻断也独立核验。
5. 为多段尾击、左右翼/身体接触、突进连击、火球/爆炸等记录HitGroup和再命中规则。重复Notify、旧代次回调或同shape多返回不重复伤害。
6. 动作取消/受击/死亡/捕获/EndPlay立即撤销token并关闭攻击shape；跨帧补发只适用于仍合法执行区间，不追发已取消伤害。

验收：10/30/60FPS、333ms大步、暂停/倍速、目标高速穿越、尾巴弧扫、同一目标多部位、多个目标、打断边界矩阵；原生geometry未闭合时只能通过工程适配级验收。

### C3 完整数值分段与接触反应

1. 先实现可重放的纯数据结算，逐段输出输入、倍率、取整点、来源与结果，使用原文件及独立实机样本作为期望。
2. 玩家物理/属性/状态分开；斩味/会心/技能/颜色/弱派生/反击等逐项资格导入，不把未实现标成功。
3. 怪物伤害使用已选任务及怒状态的原值/倍率，防御/耐性/反击/霸体入口每段只应用一次。
4. 弹刀/硬软接触、hit stop、火花/血效、回槽/命中派生均读取同一明确结果，不能用HP是否减少替代所有接触语义。
5. 修正延迟命中部位锚点与快照策略；目标销毁、断尾、切换地图/动作、死亡后剩余队列的处理依来源规则实现并可观察。

验收：同一确定loadout/任务/部位，逐阶段及最终整数与独立原作样本一致；缺任何阶段仍标partial。

### C4 部位、破坏与断尾

1. 取证并固定HitzoneRow↔受击shape↔FlinchGroup↔BreakGroup↔SeverGroup↔网格组；PBC未知常量不入阈值字段。
2. 分别累计HP、部位硬直、破坏和切断，阈值/继承/重置/重复触发规则由消费者及运行样本闭合。
3. 同次提交发出统一部位事件，动画切破损/断尾形态，碰撞撤销对应体/更新尾击几何，AI只观察状态变化。
4. 尾巴Actor单次生成、落点/碰撞/剥取资格单独处理；断尾后的毒与攻击影响须原作证据确认，不能按常识直接删毒。
5. 同帧死亡/断尾/倒地、重复网络式回调或同执行多shape接触均通过提交ID防重入。

验收：每个可破部位原作前后状态、重复命中、断尾后尾击命中范围/状态结果、掉落物一次性。未支持的部位明确列缺口。

### C5 怒、疲劳与异常/受限状态

1. 战斗模块只计算源确认的累计变化，将“达到怒/气绝/部位硬直”等请求交统一状态宿主；AI决定下一动作但不改原始累计。
2. 分开实现毒/麻痹/睡眠/气绝/爆破、耐力消耗/恢复、疲劳、发怒、口水硬、各类倒地。持续时间包含进/循环/退场时不能用单个mLoopTime代替。
3. 逐一闭合衰减时钟、重复阈值增加/上限、状态重叠/覆盖、睡眠唤醒、击倒时累计保留、怒疲劳并存与动作退出规则。
4. 用确定时间轴处理到期tick；卡顿补算毒跳，不能一帧只跳一次导致总伤害与帧率相关。
5. 陷阱类型/耐性递减/怒疲劳影响及捕获“低血+有效陷阱+麻醉状态”等条件分别取证，捕获不是HP降至阈值自动死亡。

验收：状态首次/重复、阈值边界、重叠、死亡清理及低FPS；原字段Stun/Dizziness/Concussion未区分前不能合并成一个气绝系统。

### C6 火球、场地与完整狩猎扩展

1. 从SHLP/SHLL与事件绑定确认吐息、单/多发火球的发射时刻、附着矩阵、速度/轨迹、寿命、碰撞/爆炸、再命中和属性状态；不能用通用项目火球默认值替代。
2. Shell Actor只负责飞行与查询，使用同一战斗提交接口；“生成命中爆炸”和“爆炸Overlap”不能各扣一次。
3. 飞行/落地、吼叫/风压/震动、拘束、生态捕食、区域地形、睡眠回巢与任务终止依主方案接入。
4. 完整MHWI场景还需乘骑、钩爪/软化/撞墙、投射器/闪光/音爆/粪/环境陷阱、地盘争夺、剥取/奖励/任务倍率与UI；各机制先列原作资格及实现依赖，再分阶段。没有这些项目的完整验收，只能声称“下位单怪战斗范围完成”。

验收：火球碰墙/击中/超时一次回收，地形与玩家防御反应一致；完整狩猎扩展单列通过项，不让首个闭环掩盖总范围。

## 接口与迁移顺序

| 现有接口 | 拟议迁移 | 蓝图/调用方影响 |
| --- | --- | --- |
| SweepWindow / EmitDelayedShell | 两者共同构造AttackContext并走可选类型化Resolve | 保留旧目标fallback，不能两条路径同时ApplyDamage |
| UAttributeComponent::ApplyDamage | 继续作为唯一HP写入或按最终所选架构迁移 | 先做重入/死亡事件顺序回归，再扩新组件 |
| IIncomingDamageResponse::InterceptIncomingDamage / AdjustIncomingDamage | 增加携带攻击上下文的桥，旧签名兼容 | 动态反射签名/蓝图实现须完整核对，不直接改名破坏引用 |
| IMHWIContactResponse | 新部位接触接口/重载候选，保留旧Actor级接触fallback | 不能让返回0HP默认弹刀或硬直 |
| FMHWIResolvedHit | 增加可选部位/元素/状态/来源阶段与结果类型 | 新字段兼容默认Unavailable，旧序列化与HUD读者核验 |
| 拟 /Game/MHWI/Rathian/Data | 基础Profile、QuestProfile、AttackMap、PartsMap | 先建源map→编译类型→备份/导入→保存读回→切测试地图 |

新增公开接口的返回语义、单位、事件顺序、线程/生命周期要求需同步Docs/Interfaces.md和模块索引。本轮没有改变以上任何签名或蓝图。

## 验证计划

| 验证层 | 拟操作 | 必须证明 |
| --- | --- | --- |
| 本批文档 | python Scripts/Docs/check_docs.py；git diff --check | 新增链接、索引、空白无问题 |
| 源解析/数据 | 重读固定hash、字段/ID映射、损坏/未知拒绝、独立期望 | 原文结构和导入资格，不自动代表运行 |
| C++/反射 | 按Docs/Development.md最小IntroCppEditor Win64 Development构建、相关蓝图编译 | 类型/签名兼容；编译通过不等于战斗通过 |
| 算法与回调 | 针对原作独立样本的结算、重入/旧Token/死亡测试 | 一次提交与正确阶段结果 |
| 双向真实PIE | 拟 Scripts/MHWI/pie_rathian_combat.py | 部位接触、扣血、反击、回槽、打断、shell、销毁 |
| 帧率/边界 | 10/30/60FPS+333ms步进，端点±epsilon，倍速/循环 | 不漏窄窗口/毒跳、不重复、取消不追发 |
| 原作对照 | 固定版本/任务/loadout/状态/部位、同步录像与可重复事件日志 | 最终值、时序、轨迹/接触与反应；样本覆盖明确 |
| 回归 | 太刀普通/气刃/见切/居合/登龙、木桩、地图退出 | 新怪物桥不破坏现有玩法，历史测试不直接写本次通过 |

只为有意义的机制和高风险边界新增测试，不编写仅复述实现的测试。本战斗子任务仅阅读源码/证据与MCP状态，没有编译、运行PIE、原作执行或保存资产；另由证据子代理完成73个raw文件定向提取与哈希复核。

## 风险与回退

主要风险为骨映射错误导致假命中、任务倍率叠加、主击与shell双扣、反击消费后仍追加状态、同帧死亡/破坏回调重入、组件销毁后异步回调以及曲线插值隐藏低帧漏判。使用阶段Token、单一结算、数据资格门和可重放分段日志将问题定位到源数据/适配/运行三层。

首阶段新地图与配置隔离，新增入口显式opt-in；回退关闭怪物profile与测试地图、恢复本批接口变更及资产备份。不能git checkout整个工作区，不能覆盖用户已有太刀/地图修改，也不能修改游戏安装。第三方UE-MCP/转换器无需为本方案变更。

## 文档同步清单

实施后更新战斗与AI、MHWI太刀、雌火龙动画/新怪物现状、接口及模块索引、Known-Issues并新建每批CHG。数据/动作/部位仍未知的条目在台账中保留，不将静态源值、编译通过或工程原型误写为原作忠实运行完成。
