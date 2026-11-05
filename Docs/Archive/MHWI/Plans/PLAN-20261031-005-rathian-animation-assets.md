# PLAN-20261031-005：雌火龙动画、模型与音画资源实施步骤

- 状态：draft / awaiting-direction；这是细化方案，未创建玩法代码、Montage、动画蓝图或修改资产。
- 日期：2026-10-31。
- 用户需求：总体还原 MHWI 雌火龙，并由子代理细化各部分实施步骤。
- 关联模块：mhwi-rathian-animation、mhwi-unpack-data；新接口为拟议，尚未登记。
- 上级：[总体方案](PLAN-20261031-002-rathian-restoration-master.md)。
- 依赖：[证据流水线](PLAN-20261031-003-rathian-evidence-pipeline.md)、[AI与世界](PLAN-20261031-004-rathian-ai-world.md)、[战斗接入](PLAN-20261031-006-rathian-combat-integration.md)。
- 实施记录：尚未实现；本次只读核对与方案文档由总体 CHG 统一记录。

## 现状与目标

目标固定为 MHWI 普通雌火龙 em001/00；首个验收配置为下位，不能将共享库中的大师位动作自动加入下位招式集。历史目录名 Rathalos 保持，不因名称清理改变资源引用。

| 本轮证据类别 | 可确认内容 | 不覆盖的内容 |
| --- | --- | --- |
| 磁盘/脚本静态发现 | 本体、独立尾巴及各自 Skeleton 文件存在于 Content/MHWI/Rathalos/Mesh；complete_rathian_animations.py 按源动作有效指针、原 bank/slot 导出，源帧数独立设定范围 | 当前编辑器属性、材质实际绑定、姿态正确性 |
| 既有机器证据重读 | Tools/MHW/rathian-animation-completion.json 记录19个 LMT、848有效条目，824新增/24保留；Skeleton 路径与动画集合记录齐全 | 848种战斗招式、全部轨道语义闭合、原作逐帧一致 |
| 2026-10-31修复记录重读 | rathian-legacy-duration-repair.json 与 CHG-001 记录旧24条同路径重导、时长/引用读回通过 | 本轮再次导入或再次运行验收 |
| UE-MCP本轮查询 | 项目 engineAssociation=5.8，但 mode=disconnected、editorConnected=false | 本轮完整资产属性读回、视口或PIE验证 |

已知原路径：

- 本体：/Game/MHWI/Rathalos/Mesh/SK_EM001_Body；Skeleton：/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton。
- 独立尾巴：/Game/MHWI/Rathalos/Mesh/SK_EM001_Tail；Skeleton：/Game/MHWI/Rathalos/Mesh/SK_EM001_Tail_Skeleton。
- 动画：/Game/MHWI/Rathalos/Animations/A_em001_*。具体每条以 manifest 为准，空槽不能补成伪动作。
- 已有材质磁盘文件包括 Ch_EM001_Mt__2、Ch_EM001_Mt__damage、FakeEye_Mt__4、Ch_FakeSphere__3、M_HiddenSlot；“存在”不等于正确材质分配。
- 原模型141骨；历史 UE 抽检含 Armature 根共142轨。骨序号偏移不可凭“加1”直接用于全部消费者，须以名字/父链/变换实证映射。
- 本轮证据子代理已补提73文件共16,446,967 B（声音8、VFX52、任务/区域候选13），73/73尺寸与SHA256复核一致；资源位于Saved/MHWI-Rathian-20261031-PlanEvidence/nativePC，紧凑来源见[本轮解包证据](../../Tools/MHW/rathian-plan-evidence-20261031.json)。声音包含WW事件及em001_se/vo.nbnk，VFX为47 EFX+5 TEX；均为raw阶段，未闭合解码/引用关系与全部共享依赖。

历史材质/隐藏破损槽操作有场景未保存及截图冻结边界，见[CHG-019](../Changes/CHG-20261030-019-mhwi-rathalos-lighting-damage-mesh.md)。不能把整槽从隐藏改可见自动当作正确逐部位破坏表现。

## 官方资料结论、版本与选择门

2026-10-31先搜索 Epic 官方资料，搜索结果显示以下页面为 Unreal Engine 5.8；带版本参数的部分页面直开失败，因而链接使用可检索到的正式路径。实际 API 落地再与安装的5.8头文件对照。

| 正式来源 | 官方能力结论 | 本项目使用条件 |
| --- | --- | --- |
| [FBX动画导入](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-animations-using-fbx-in-unreal-engine) | 动画导入可指定既有 Skeleton | 骨架及坐标需先核验；不自动证明第三方转换保真 |
| [Root Motion](https://dev.epicgames.com/documentation/en-us/unreal-engine/root-motion-in-unreal-engine) | 可提取根骨运动并驱动角色；提取模式由 AnimInstance 配置 | em001根轨身份及重力/地空运动语义尚待资格核验 |
| [Animation Montage](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine) | 支持组织片段、分段播放和事件 | Montage只是UE播放机制，不能决定原作招式连接/取消 |
| [Animation Notifies](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine) | 可同步通知、持续窗口、声音和粒子事件 | 原始事件到Notify的映射需独立证据，不能靠目测任意填帧 |
| [Motion Warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine) | 提供面向目标的根运动修正窗口 | 修正会改变轨迹，须选择采用条件及允许误差 |
| [Animation Insights](https://dev.epicgames.com/documentation/unreal-engine/animation-insights-in-unreal-engine) | 可观察姿态、Montage与事件时间线 | 用于诊断UE执行，不证明原作行为 |

Epic没有“MHWI雌火龙还原”可直接套用方案。以下是有出处机制上的项目候选，最终随总体方案选择，不在本文件擅自定案。

| 决策 | 候选及成本 | 建议与待选项 |
| --- | --- | --- |
| 位移所有者 | UE Character+根运动：复用现有播放/移动；受Character胶囊、步行/重力规则约束。Pawn+专用移动消费原轨：更直接控制多足/地空运动；需补地面约束、碰撞滑移、导航桥接。原位动画+代码移动：实现快；轨迹与足滑需单独验证 | 先对一个突进、一个后空翻、一个起落动作做资格比较；随主方案选移动载体 |
| 时间线载体 | Montage+数据事件：易编辑，但独立源时钟/叠层可能不一一对应。原生动作播放器适配：保留多时钟与复合层，研发和调试成本高 | 优先验证“数据事件驱动+UE播放适配”候选；未知时钟不得硬归一为Montage秒 |
| 目标对齐 | 保留源轨；或限定Motion Warping对齐目标/落点 | 忠实度验收先保留原轨作基线；有原作转向/落点证据后决定允许修正范围 |

## 范围与验收标准

本部分分五类资产：完好/破损模型、动作与合成层、位移、动作事件、声音/特效/镜头。完整还原还包括受击/失衡/倒地/怒吼/疲劳/死亡/捕获与生态动作，不能以主要攻击动画通过代替这些项目完成。首阶段只启用已确认下位资格的动作。

交付门：

1. 所有被启用动作均能追溯源bank、slot、文件SHA、帧数、合成层、原生动作绑定和UE对象路径；未知字段明确 unknown。
2. 同一动作实例的姿态、位移、碰撞事件和表现事件有明示时间映射，不因显示帧率改变总位移或重复触发。
3. 打断、动作切换、死亡、销毁和地图退出清理事件监听及循环音效/VFX；旧实例回调不能影响新动作。
4. 断尾和逐部位破损按确认的原作网格/部位映射展示，并同步影响战斗形状；不能只隐藏整条尾巴造成时序脱节。
5. 资源保存、重新加载、引用读回、真实PIE与原作对照分别记录；任何一项通过都不能代替其他项。

## 技术方案与拟议数据契约

下列类名、字段和路径均为待选设计，不是现状接口。

| 拟议类型/落点 | 内容与所有者 | 约束 |
| --- | --- | --- |
| Source/IntroCpp/MHWI/Monsters/MHWIMonsterMotionData.h | FMHWIMonsterMotionId 保存 SourceHash、Bank、Slot、NativeActionId及可信等级 | CRC候选名与原生绑定ID分开；不以数组下标代ActionNo |
| Source/IntroCpp/MHWI/Monsters/MHWIMonsterAnimationComponent.* | 只持有本次动作播放Token、层权重、时间换算与绑定委托 | 主逻辑在游戏线程；UObject强/弱引用按所有权配置 |
| 同目录 FMHWIMonsterMotionEvent | 事件来源/原偏移、源时间单位、窗口端点、循环迭代、碰撞/音效/VFX引用 | 未解语义不得默认填0后启用；不同时间域显式换算 |
| 拟 /Game/MHWI/Rathian/Data/DA_Rathian_MotionMap | 已合格动作的软引用与源证据链接 | 新配置可用Rathian目录；已有Rathalos资产原路径引用 |
| 拟 /Game/MHWI/Rathian/Animation/ABP_Rathian | 完好/破损骨架驱动、确认的层合成、Slot、姿态输出 | 碰撞消费的是经过验证的姿态，不得用未更新骨缓存 |
| 拟 /Game/MHWI/Rathian/Presentation | 新建声音、Niagara与事件配置 | 原资源格式未支持时另列“表现近似”，不能标原作保真 |

848条导入的60FPS是现有转换采样设置；对多帧条目旧工具预期时长为(frame_count-1)/60。它不自动证明原作逻辑帧为60Hz、原始所有事件也是60帧/秒，单帧占位时长亦不得理解为一段完整动作。

动作运行Token与AI/战斗共同定义，至少包含EncounterGeneration、ActionRunId、PlaybackGeneration、MotionId与LoopIteration。动画组件不自主决定发怒、硬直或重新选招，只发布经身份校验的结果。战斗权威时间轴负责伤害，Notifies可作为表现和可观察适配点；若最终选Notify为伤害窗口入口，也必须以同一Token、跨帧补发和取消协议验收。

## 实施步骤与依赖

### A0 资源快照与资格检查

1. 在用户选定路线后，连接现有5.8编辑器，核对项目路径/PID，列出相关资产类、完整路径、Skeleton、骨父链、轨数、时长、采样率、RootMotion设置、Montage引用和材质槽；不根据文件名判断。
2. 从848条源清单选每个有效bank的普通/单帧/长时动作及关键攻击代表，分别比对首/中/末帧骨变换、边界姿态、根轨和源->UE坐标。
3. 新输出 source-motion-map.json、asset-baseline.json、每条失败原因；保留源hash、工具固定版本、转换参数。现有旧24条已修复时长，不能再以旧4.15秒为统一基线。
4. 失败条目留在隔离库，不改848条源身份。只有被功能引用的动作满足资格后才能进入正式配置。

验收：同一SourceHash+Bank+Slot仅有一个清晰源身份；同源采样复现误差有明确报告，不能仅凭轨数通过。

### A1 动作语义与复合轨道

1. 与证据包连接 ACTP2/THK动作请求、LMT/MBD动画选择、TIML/AT事件、COL攻击UID及SHLP引用，生成可追溯关系表。
2. 将中文“咬击/甩尾/突进/后空翻/火球/吼叫”等仅作为工作分组；必须绑定证据确认的ID，不能按动画外观给所有槽强行命名。
3. 核验 _fs、NeedsParent、常量轨、功能骨、独立尾巴Skeleton和眼部等通道是否为叠加/局部层；未解时禁止把其单独播放当完整动作。
4. 分出待机/移动/转向、攻势、受击/倒地/起身、怒疲劳、起飞飞行降落、生态/死亡捕获六组并建立覆盖清单。

验收：首个动作链有可复现的“选择→片段→事件→碰撞UID”连接，未映射集合留存；不要求虚构全库语义。

### A2 模型、材质与部位形态

1. 固定模型尺寸、坐标、枢轴与骨架，不用缩放角色来补错误坐标；记录原生单位到UE厘米的依据。
2. 对材质反照率、法线、粗糙度/遮罩/透明、眼部和翼膜分别建立中性光及固定曝光对照；Actor材质覆盖与网格默认槽都读回。
3. 取证 PBC/网格组/渲染节点映射，决定“按mesh section隐藏”“分组件替换”或“预拆完好/破损网格”等可选方式及drawcall/维护成本；等数据与用户方向闭合后实施。
4. 核对独立尾巴资源到底用于断尾掉落还是其他状态，不因名称就自动挂到身体形成重复几何。
5. 启用前预加载并核验破损、断尾、尾根封口及掉落物等必要资源；战斗提交发布一次带身份的部位结果。表现失败记录并重试/降级显示，不回滚已经提交的HP/耐久或改变逻辑破坏状态；必要资源未合格的配置不通过完整验收。

验收：每个确认部位单独切换、重复事件不重复生成断尾Actor；碰撞体更新与视觉状态一致。

### A3 播放与位移最小样例

1. 实现已选播放器适配及运动所有者，只接待机、走/转身、一段突进、起落/后空翻样例，先禁伤害。
2. 用同一源时间区间推进姿态与位移；地面碰撞截断、坡面、高差、空中Z位移分别记录，防止代码位移和根运动双重叠加。
3. 明确冻结/暂停、倍速、循环、向后Seek、跨段播放与混合期间哪个源时钟前进；跨大帧推进分段覆盖所有已到事件。
4. Blend参数先从原作MBD/消费者取证；缺失时可提出UE近似候选，必须单独标近似而不写成原值。

验收：10/30/60FPS与受控卡顿下总位移、结束姿态、事件序列一致到约定容差；碰墙不瞬移、起落不漂移。

### A4 动作与战斗事件对接

1. 使用战斗包统一ActionRunId，将shape启停、shell发射、状态允许窗口和朝向锁定作为有来源的事件。
2. 纯表现Notify只读取状态；伤害确认不能从“粒子出现”或“动画到这个姿势”推断。
3. 每次蒙太奇结束/BlendOut、动作失败/打断、重启、死亡与EndPlay都撤销旧Token、解绑委托、关闭shape，处理回调重入。
4. 新动作已启动后，旧Montage结束回调必须被代次校验拒绝。

验收：打断点前/中/后分别测试，不残留已撤销的攻击窗、待发射事件或附着循环实例；已经发射的shell独立按原作生命周期验收，不一律随动作结束销毁。

### A5 声音、VFX与镜头

1. 从动作/素材引用递归收集脚步、振翅、吐息/火球、尾击、吼叫、呼吸/疲劳、受击破损、断尾、死亡等所需音效/VFX。现有em001目录内特效文件不代表共享音库与纹理已齐。
2. 复用本轮已补提的声音8文件和VFX52文件，按E08工作包继续解析事件引用、编码/特效依赖；新增缺项才定向补提。声音事件库、音频编码、特效格式不可直接转用时，列原作事件时刻与UE重建候选。
3. 选定候选后导入音频/衰减和Niagara资源，附着到经确认骨骼/局部矩阵；连发火球每次发射有独立事件身份。
4. 循环呼吸/振翅与蒙太奇退出绑定；传送/卸载清理附着实例。镜头震动、hit stop、吼叫影响分别来自其证据，表现不额外驱动伤害。
5. 明确“事件忠实、资源近似”或“原资源转换”两种验收等级；近似资源不能让完整还原总状态变成完成。

验收：每个事件一次、方位/空间音符合骨骼与镜头关系；音画误差阈值需基于原作采样能力约定，不任意承诺逐帧。

## 接口与迁移

| 当前入口/资源 | 拟目标 | 调用方影响 | 顺序 |
| --- | --- | --- | --- |
| 848条原路径AnimSequence | 原位保留，增加独立语义map | 现有工具与引用继续可用 | 先快照→资格→新增配置 |
| 本体/尾巴独立Skeleton | 记录准确骨/部位映射后再决定组合方式 | 新怪物Blueprint/AnimInstance | 先数据→后组件装配 |
| 尚未有证据证明正式雌火龙播放器 | 新动画适配组件承接AI动作Token | AI只请求，不自行改骨姿态 | 播放无伤害样例→事件接线 |
| 破损隐藏槽历史操作 | 分部位状态驱动 | 战斗破坏事件与材质/mesh一致 | 先原作映射→后表现 |

本轮没有实际迁移。新增反射类型时按游戏线程、UFUNCTION动态委托及UE5.8头文件规范处理；资源异步回调使用弱引用、取消请求和执行代次，不能将裸指针跨加载期保存。

## 验证计划

| 场景 | 方法/拟命令 | 期望 | 边界 |
| --- | --- | --- | --- |
| 文档 | python Scripts/Docs/check_docs.py；git diff --check | 链接与空白无新增问题 | 不证明资产行为 |
| 资源集合 | 复用并扩展 Scripts/MHWI/verify_rathian_completion.py，只读模式 | bank/slot/路径/类/Skeleton/时长一致 | 旧工具不能证明语义 |
| 姿态/根轨 | 源采样对UE骨变换、固定镜头多视角及误差报告 | 已启用动作按约定容差 | 原作运行对照另列 |
| 事件边界 | 10/30/60FPS、333ms推进、倍速/循环/中断 | 有序、去重、取消清理 | 拟新增专项PIE |
| 部位形态 | 单部位破损、重复断尾、死亡期间事件 | 无重复几何、视觉碰撞一致 | PBC映射未解前不能验收 |
| 性能 | Animation Insights/Unreal Insights | 记录骨更新、组件和特效成本 | 不预设没有测量的帧预算 |

上述为未来计划。本轮未编译、启动编辑器、保存资产、执行PIE或原作逐帧观测；73文件提取/哈希复核由证据子代理执行，不能当作上述资源语义或运行检查通过。

## 风险与回退

先保留旧资源和引用，新增配置/蓝图/测试地图隔离；每批导入或修改前记录SHA与备份。回退只恢复本批改动资产及其配置引用，不对整个Content执行恢复，不覆盖现有用户未提交文件。第三方转换器固定版本；若需修改第三方工具，另记本地补丁和升级成本。原作位移/复合层缺口会阻塞忠实度验收，不能用任意调速/目测补帧掩盖。

## 文档同步清单

实施批次分别更新 MHWI-Rathian-Animations 现状、模块索引、相关接口、Known-Issues与新CHG。历史848补齐及旧24修复记录保留原含义；当前方案只新增计划，不把未完成播放器写入现状页。
