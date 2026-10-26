# 已知问题与验证边界

基线日期：2026-10-17。本页为现有实现的技术债与待核对项，不是已经修复的清单。`open` 是已从源码/配置发现的差异；“静态发现”不冒充运行复现。优先级仅建议修复次序，实际范围由用户需求决定。

| ID / 状态 | 证据与影响 | 后续方案与验收关注 |
| --- | --- | --- |
| R-INV-001 / open，高 | [AddItem](../Source/IntroCpp/InventoryComponent.cpp) 叠加/填部分槽后遇满包直接 false，未回滚且可能跳过统计/事件。Pickup 仍保留世界物品，存在重复获得风险。静态发现 | 预检容量后提交，或改成明确报告实际添加数；测试部分堆叠 + 无空格 |
| R-INV-002 / open，高 | 同文件 AddItem 用成功调用次数递增 CurrentItemCount，RemoveItem 按调用减；SetItemAt 不重算；Weight 只累计 Inventory、不含移到快捷栏的物品。计数/重量不是完整一致的拥有量。静态发现 | 先确定快捷栏所有权与总重量定义，再统一重算或维护；测试只堆叠、跨格、多次搬移 |
| R-INV-003 / open，高 | DropItem 在 ItemClass 不存在/Spawn 失败后仍 RemoveItemAt。静态发现 | Spawn 成功后才提交扣除或返回结构化结果；验证失败不丢物 |
| R-INV-004 / partial，高 | [动作实施](Changes/CHG-20261019-005-character-actions-implementation.md) 已统一玩家使用入口，提交返回 Applied/ConsumedQuantity/Partial；不再双扣快捷栏，使用事件在消费前保存ID。4项库存事务自动化通过。独立 RemoveItemAt 的旧事件构造不属于这次使用提交路径，仍需整改 | 保留独立移除/丢弃事件问题；自定义 Legacy Execute(false) 的外部副作用不可视为可回滚 |
| R-INV-005 / open，高 | SwapItems/SortItems 不维护 EquippedSlotIndex；按 ID 移除与快捷栏同步不完整；两条拖拽实现对占用目标处理不同，归还 AddItem 的失败结果未处理。静态发现 | 统一迁移/交换入口及装备标识；验证守恒、失败回退和正确武器 |
| R-ITEM-001 / open，中 | [RegisterItemData](../Source/IntroCpp/ItemDataSubsystem.cpp) 覆盖映射但不清 LoadedCache；扫描完成标志只允许一次自动扫描。静态发现 | 明确热注册/替换语义；测试同 ID 替换后读到哪个对象 |
| R-COMBAT-001 / fixed | [动作实施](Changes/CHG-20261019-005-character-actions-implementation.md) 移除 PendingUse 状态，来源预约含容器/索引/ID/数量/版本，动作全程锁公共库存写入；中断/死亡/EndPlay统一结束。原来源、最后一件、失败不扣自动化及真实喝药/中断PIE已验证 | 当前为全局锁，动作中拾取也拒绝；未来槽级并发预约是单独优化 |
| R-COMBAT-002 / fixed | 同记录：Deferred Spawn 在激活前设置标准火球的 Damage、Owner、Instigator和方向；真实PIE已检查非零伤害覆盖写入、一次扣蓝 | 实际目标扣血/碰撞过滤仍沿用投射物原实现，未全面测所有自定义投射物 |
| R-COMBAT-003 / fixed | Chain NotifyState动画时间窗口、窗口前150ms单条缓冲、窗口内立即登记；333ms低帧/边界自动化通过，长剑4段6命中真实PIE通过 | 尚未完成30/60/120FPS全套视觉手感对照；窗口可在Montage调参 |
| R-COMBAT-004 / partial | 请求已统一检查Dead/UI/Busy，直接玩家使用入口同样受限，组件订阅OnCharacterDeath；自动化覆盖许可/死亡重入。OnDamaged尚未被角色接为通用硬直中断，未逐图审计自定义受击BP | 普通受击继续沿用原反馈；有硬直逻辑时显式调用Interrupt，后续独立Facing/霸体规则仍需设计 |
| R-COMBAT-005 / fixed | 三个Notify保留EventReference，验证Mesh/Montage/Instance/事件索引及代次；统一Finish，无旧玩家动作Timer。10项自动化覆盖重复/旧实例/旧段/缺提交/OwnerEnded，真实Montage通知及中断PIE通过 | 同实例无缝跳段未启用，保守采用每段新实例；视觉Blend质量仍需人工体验 |
| R-COMBAT-006 / fixed | MHWI 默认训练木桩每4秒自动造成12伤害，容易在练习时被误认自伤；运行委托确认为 MHWITrainingTarget_0，角色空闲也掉血。现训练地图与生成脚本默认三个目标均被动 | [训练场修正](Changes/CHG-20261022-005-mhwi-training-damage.md)：普通/气刃10动作玩家满血、目标扣268；显式开启目标后真实扣血与见切拦截通过。原生类缺省仍 true，手工新增目标需明确设置 EnableAttacks |
| R-COMBAT-007 / fixed | 正式DA32定义与最终C++构建通过；新进程整套PIE通过三轮气刃I插突刺续II、II插上挑续III，独立普通RMB六连，持刀RollStepSlash/纳刀DrawSlash、过期/中断出口；真实输入与正式成本未置零 | [实施记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)：窗口关闭后输入曾会在结束回调追溯派生，现修复并通过窗口内/后对照；全部四向翻滚视觉、资源不足的完整矩阵尚未穷举 |
| R-COMBAT-008 / fixed-project-tuning | 镜头相对移动意图、早段/返回段转向和袈裟选择已落地。最终PIE通过14种镜头/输入的真实左右/后退位移、普通/派生转向及无方向只动镜头不转身；127/128片段及来源/窗口已同步交换 | [本轮记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)：原版精确角度仍未标定，当前25°等为项目调校；空中转向改变攻击朝向但不重算水平漂移，返回段与所有方向的视觉手感仍可继续标定 |
| R-MM-001 / resources-provided-mm-pending | 2026-10-19原走跑Root平移全0，Hips无可替代累计位移；2026-10-20用户已提供ARPG_Ninja，当前完成IPC移动与动作替换，Rootmotion版本尚未做MM专项审计或正式接入 | [原资源需求](Plans/MM-RootMotion-Resource-Checklist.md)、[历史实查](Plans/MM-P5-Audit-20261019.md)、[Ninja现状](Systems/Ninja-Animation-Configuration.md)；未新建MM资产，资源存在不表示轨迹库已就绪 |
| R-ANIM-001 / unverified-per-user | 2026-10-20 Ninja替换及后续Root Motion适配已保存：18条新Rootmotion输出、26条正式Sequence根提取、三个移动BS、ABP移动意图输入和RootMotionFromEverything；四段5命中与左手施法保留 | 胶囊位移/碰撞、停止与转向融合、摇杆力度、攻击位移、姿态/握持、命中帧与出口未做完工后验证；旧6命中PIE脚本不适用；M_Drink缺新资源继续沿用。见 [Root Motion记录](Changes/CHG-20261020-002-ninja-root-motion.md) |
| R-ANIM-002 / config-fixed-runtime-pending | 用户报告Root Motion走跑不移动、衔接生硬。静态定位：共享PoseCache在上层先被零根权重上下文占用；三个BS输入/权重平滑均为0。已保存底层优先更新及0.10/0.16秒输入平滑、8/s权重过渡 | 未运行修复后的PIE或测试，效果待确认；[缓存修复](Changes/CHG-20261020-003-locomotion-root-cache-fix.md)。不能关闭根骨分层权重来替代缓存顺序修复 |
| R-ANIM-003 / integrated-ground-module-verified | [MHWI 独立训练模组](Systems/MHWI-LongSword.md)：164 太刀、9 通用动画，4条 Common 正式接入，另有对照/保留源片段；猎人/武器、独立角色/ABP/Data/HUD/训练图已导入；此前完整 C++ 构建通过 | 此前取消验证限制后，移动/根运动/反击/居合/气刃完整链/登龙七段已实际通过；[武器位置修正](Changes/CHG-20261022-003-mhwi-weapon-attachment.md)另通过45项检查。完整原版 shader、特效、刀刃逐骨扫掠和精确取消帧未还原；没有替换原 Ninja |
| R-ANIM-004 / fixed | 原纳刀 walk 误用向上 171.58cm 的攀爬 034；气刃II/上挑源标签反置；连续左键拔刀斩后跳过纵斩。现为站立走跑 203/090、气刃II 106/上挑107，Left 出口接纵斩 | [动画修正](Changes/CHG-20261022-004-mhwi-animation-corrections.md)：39项真实输入/姿态/命中PIE与12项磁盘重载检查通过；其他源招式仍需逐项语义对照，历史模组测试不等于全部动作外观正确 |
| R-ANIM-005 / fixed | 正式M_SpiritThrust为170、M_ForesightSlash为140，窗口84..97/60与70..80/60及制作源同步；新进程真实输入/源姿态对照、空挥/命中登龙和训练目标见切拦截通过 | [实施记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)，源依据见[研究](Reference/MHWI-LongSword-Behavior-Research.md)；其他源招式仍需逐项语义对照 |
| R-ANIM-006 / fixed-project-tuning | Rise根运动、Air/Strike Falling、二次攻击及25/60提交、真实落地/恢复均已通过最终PIE。无输入Air约1.407秒；主动七段/降一级、提交前落地零七段零降色、中断/死亡通过；5000cm高落差尾帧保持73次采样通过 | [本轮记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)：低顶/斜坡/目标顶部、自定义重力体积待专项验证，物理初值尚未与原版参数组/单位一一标定；未声称原版逐帧一致 |
| R-ANIM-007 / implemented-awaiting-user-acceptance | 本轮补齐纳刀攻击/大回旋收刀、居合最终双掌接触和握点连续转移，直接派生不再中间重置内部姿态；原始六条内部动画/19事件保留。按用户要求未做最终UE运行调试，视觉等待用户验收；原生IK/初始装配和全身体穿插仍有边界 | [位置收尾](Changes/CHG-20261024-005-mhwi-weapon-placement.md)、[交接说明](Reference/MHWI-Weapon-Transfer-Fitting.md)；73帧保持仍不消费80帧事件，CMS不是挂点数据 |
| R-ANIM-008 / partial-current | B10已接真实来源调用方；B12历史编译成功。2026-10-26静态验收发现受击锁阻断恢复派生，R06仍未完成 | [当前验收A01](Reference/MHWI-Acceptance-20261026.md)、[逐连接状态](Plans/MHWI-Connector-Progress.md)；运行由用户操作，node86继续不可达 |
| R-ANIM-009 / partial | 新采样36段、正式引用累计30组；三色309/310/311与308共享完整骨轨块的705时刻比较差0，正式三色Montage已复用Native308并保留颜色速度/事件。通用NeedsParent求值和基础移动迁移仍未完成 | [实施记录](Changes/CHG-20261024-003-mhwi-defense-routes-transfer.md)：共享块适配不等于全部父姿态语义已解；不声称全库/所有视觉问题解决 |
| R-COMBAT-009 / partial | 独立防御窗、23招148个逐输入项目窗口已落地；原始W03P已批量解码并向21处属性导入。299条输入轨/961key保留完整mask/value/control，但transition5与具体接受/执行/缓存消费仍未知 | [原始参数路线](Reference/MHWI-Native-Parameter-Pipeline.md)：原生参数优先；未知位不写成取消帧，匿名ActionParam不猜作登龙物理；速度继续线性 |
| R-COMBAT-010 / partial-restoration | B01已保存源数值/五处路线修正；B11补见切B→突刺与R+A→登龙突刺；B12完成全台账逐项处置：R11停止把10s加到颜色T、R15补登龙空中126首击、R22结构化命中、R24受击S/M/L控制状态、R26 Falling门控、R27输入阻断、R31 hit lag/命中事件、R01/R05/R08原版手柄预设与同帧手势。Q衰减、回旋清槽时点、10s的Q消费者、居合追加shell、真实刀刃/部位空间及完整主角动作仍开放 | [逐项状态台账](Plans/MHWI-Restoration-Progress.md)、[B12矩阵](Reference/MHWI-Ledger-Disposition-20261026.md)、[B12记录](Changes/CHG-20261026-002-mhwi-ledger-sweep.md)；代码增量编译通过但未运行PIE；[33项审查](Reference/MHWI-Restoration-Review.md)保留修复前快照，不再当最新值 |
| R-COMBAT-014 / reopened-static，P1 | B10已交付真实来源/专用入口/混合；B12历史编译成功。但受击Flinch状态使RequestInput和RequestNativeSourceInput全拒绝，FinishMove清来源后才解锁；真实Step来源恢复不可达 | [验收A01](Reference/MHWI-Acceptance-20261026.md)；R06降为部分完成，未运行复现、未修复；需区分硬直与合法恢复许可 |
| R-COMBAT-015 / open-static，P2 | 原版预设按Held状态判断组合，无关的新边沿也能重发旧组合；同一CommandAction共享键鼠/手柄，开启预设后键鼠组合也改变 | [验收A02/A03](Reference/MHWI-Acceptance-20261026.md)；R01/R08仍部分完成，未运行复现、未修复 |
| R-COMBAT-016 / open-static，P1 | SetInputBlocked未清NativeSourceInput；TickNativeSource仍可经StartResolvedMove提交缓存派生，Move/Look也未检查阻断位 | [验收A04](Reference/MHWI-Acceptance-20261026.md)；R27仅部分接口，完整菜单接入与缓存撤销未完成，未运行复现、未修复 |
| R-TEST-005 / pending-next-stage | B04验证脚本固定“两处来源冲突”历史预期，B05来源修复后已过时；旧输出目录还指向B04 | 下一阶段先迁移预期与输出目录，再执行相称检查；不得覆盖历史或冒称本轮通过 |
| R-ANALYSIS-001 / implemented-pending-tests | 单pdata范围遗漏CHAININFO从属段；缺元数据默认256字节可能跨界。B06新增链式读取器并移除盲读后备，显式叶范围待复核 | [控制现状](Reference/MHWI-Native-Connector-Control.md)、[通过准则](Plans/MHWI-Connector-Acceptance.md)；不要将反汇编范围收集当作完整消费者覆盖 |
| R-COMBAT-013 / historical-B04 | 连接入帧原MBD此前漏读；现已解析30节点32引用并将既有129入口48接原值。361/362的127/128目标与项目左右映射冲突，118另有112候选；退出/Phase1/混合消费者仍未知 | [逐连接状态](Plans/MHWI-Connector-Progress.md)、[CHG-010](Changes/CHG-20261024-010-mhwi-connector-evidence.md)：新增连接0条，未改正式资产；不得将片段末采样帧或空条件当退出依据 |
| R-COMBAT-012 / partial-B03 | 基础循环曾仍引用旧采样；B03已迁移五段合格NativeFidelity、DA六字段及BlendSpace六样本，保留既有锁根/倍率/速度 | [CHG-009](Changes/CHG-20261024-009-mhwi-locomotion-animation.md)：7.766秒真实移动通过；原版速度、起停/转身/落地、IK及复杂地形仍开放 |
| R-COMBAT-011 / fixed-B02-scope | B01曾将气刃踏步20强化成本当作启动门槛；现依据原COL弱/强记录和原W03P恢复不足槽18/免费、够槽28/扣20。另修A/B→气刃插入上挑、R按原序够槽III/不足I，移除插入突刺自定B出口 | [B02记录](Changes/CHG-20261024-008-mhwi-spirit-branches.md)：完整构建和18秒短冒烟通过；窗口与连接精确性仍开放，未声称完整还原 |
| R-TEST-004 / fixed-commandlet-guard | B01首次命令行预览调用LevelEditorSubsystem的PIE状态查询，在无UI进程触发原生访问异常，保存前发生，正式DA哈希未变。命令行分支跳过该UI调用后预览/保存/编译蓝图成功 | [B01记录](Changes/CHG-20261024-007-mhwi-native-basics.md)保留失败日志和重试结果；正常编辑器仍保留PIE写入门控 |
| R-TEST-003 / mitigated，根因待确认 | 自动资源回归曾在PIE启动boot_start发生Engine访问异常，栈含重复Slate/Python启动路径及音频设备超时；测试回调已加防重入。临时-nosound和恢复普通音频启动后均通过资源615断言，未复现；不能据此证明唯一原生根因 | [批处理记录](Changes/CHG-20261024-004-mhwi-native-parameter-pipeline.md)：原日志/CrashContext已保留；未将崩溃场次记为通过，不修改游戏玩法来迎合夹具 |
| R-AI-001 / needs-verification，高 | 只读编辑器快照：BP_Enemy_Dummy CDO 的 AIControllerClass=null，虽然 AutoPossessAI=PlacedInWorldOrSpawned。未逐项核对关卡实例或执行 AI 运行测试 | 先读实例配置、控制器实际类型，再验证导航/感知/追击/攻击，不能只凭类存在判断接通 |
| R-AI-002 / open，高 | [EnemyAIController::OnPossess](../Source/IntroCpp/EnemyAIController.cpp) 在运行阶段 CreateDefaultSubobject 创建感知组件；构造期默认子对象与运行期创建边界需要整改/验证。静态发现，未触发运行复现 | 构造期创建并在 OnPossess 配参数，或采用正确运行期 NewObject/注册流程；验证重复 Possess |
| R-UI-001 / open，中 | [InventoryUI](../Source/IntroCpp/UW_InventoryUI.cpp) 创建网格写死 20 格；组件 MaxSlots 可调。静态发现 | 根据实际容量生成，验证非 20 格 |
| R-UI-002 / open，中 | InventoryUI::SetInventoryComponent 重复 AddUObject，没有先移除旧组件订阅；NativeDestruct 只解绑按钮。StatusBar 的重复注入也需验证。静态发现 | 明确 Widget 重挂与重绑生命周期，保存句柄/RemoveAll/唯一绑定，测试反复开关和换组件 |
| R-ENTRY-001 / needs-verification，中 | MyLevel 依赖放置玩家实例 AutoPossessPlayer=Player0，默认 GameMode 仍指模板 Pawn；Start 界面创建链与所有资产 Notify 未逐一审查。已核对局部配置 | 在改变出生/切关/联机入口前明确生成与控制策略，按实际运行验证 |
| R-ENGINE-001 / needs-verification，低 | 升级阶段记录的引擎启动自检有 13 条 Condition failed，安装新 MCP 前后均存在；插件有弃用警告。历史证据见 [升级记录](UE58-Upgrade.md) | 如需干净启动日志另行定位；不把已通过的启动/PIE/MCP 冒烟扩展为全量测试通过 |

跨系统限制：尚无完整持久化、多端复制或 Buff 运行系统；EnemyAIController 的目标筛选仅依据 AttributeComponent 等现有条件。上述扩展都应先建功能方案，不能只添加一个字段就标记功能完成。

修复问题时保留 ID，将状态改为 fixed，附对应 CHG 记录和真实验证结果；不要直接删除已被方案引用的问题条目。
