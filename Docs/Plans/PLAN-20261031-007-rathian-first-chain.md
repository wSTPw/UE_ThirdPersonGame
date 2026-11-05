# PLAN-20261031-007：雌火龙首条THK到命中的验证链路

- 状态：in-progress；用户已选技术组合，开始实施；完整原作验证尚未通过。
- 日期：2026-10-31。
- 用户需求：采用推荐组合，以忠实还原优先，继续分子代理实施；先完成THK决策→动作→移动→命中，缺数据先解包取证。
- 关联模块 / 接口 / 问题：mhwi-unpack-data、mhwi-rathian-animation、mhwi-longsword；R-DATA-003/004。
- 实施记录：后续新增CHG-20261031-003；此前CHG-002保留“仅方案/raw”的历史范围。

## 现状与目标

[总体方案](PLAN-20261031-002-rathian-restoration-master.md)及003–006细案已交付。当前19 LMT/848动作、300原始资料与73补取资料不证明已闭合决策/碰撞语义。实施前已读取git状态：既有太刀C++、DA、训练地图及文档修改需保留；本轮新入口隔离，不覆盖旧训练场。

用户本轮明确选择：1C原THK/thklst规则驱动，2B原作时间轴，3B Pawn+专用Movement，4B原COL/骨映射+UE连续查询，5A专用C++结算+现有Attribute宿主，6B源数据转换流水线，7B静态分析与受控原作运行对照。后续不得重新要求已获授权的同一选型。

目标选择一个证据最完整的原动作，不预先按中文招式名决定。链路需记录THK源节点/条件/动作请求、ACTP2动作身份、动画bank/slot、位移采样与骨坐标、攻击事件/UID/几何、实际UE接触及状态结果。

## 范围与验收标准

1. 资格：固定工具commit/hash及源文件hash，读取原THK/THKLST；未知指令/原生函数/等级资格明确拒绝，不能把数组下标直接当ActionNo。
2. 动作：有来源的原节点能启动对应动作/片段；验证正反条件或明确尚缺消费者的边界。
3. 位移：Pawn专用组件消费外部原时钟与经资格确认的原轨，位移只消费一次，不用人工平移补根轨。
4. 命中：只用已确认源攻击窗/骨绑定shape；将接触和最终伤害分别验收，MV不能冒充玩家实战扣血。
5. 运行：UE5.8构建与隔离PIE真实动作/接触链；低帧跨窗、旧RunId、中断/EndPlay不产生重复提交。
6. 忠实度：静态/工程验证和原作运行对照分别记录。缺任一核心来源不标完整链路通过，继续定向取证，不能只凭合成夹具宣称原作还原。

## 官方资料与来源边界

- [Epic UE5.8 Pawn/Movement示例](https://dev.epicgames.com/documentation/unreal-engine/quick-start-guide-to-components-and-collision-in-unreal-engine-cpp?lang=en-US)：PawnMovement组件与安全移动是承载候选；具体API以本机5.8头文件为准。
- [Epic UE5.8 Traces](https://dev.epicgames.com/documentation/unreal-engine/traces-with-raycasts-in-unreal-engine)：支持对象/通道与形状查询，不证明COL业务语义。
- [Epic UE5.8 Skeletal Mesh动画](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-assets-in-unreal-engine)：支持动画资产/AnimBP播放；时间与姿态到原作的映射仍需证据。
- [Leviathon维护者实现](https://github.com/AsteriskAmpersand/Leviathon)：THK/THKLST语言与参考编解码工具；不是Capcom官方消费者规范，不能从反编译成功推导执行等价。

## 技术方案

三个子代理实际实施：evidence负责THK/首条动作资格和源数据；combat_animation负责动作/动画/原轨采样及PawnMovement组件；ai代理本批负责碰撞/攻击窗/源几何与运行组件。主代理整合动作身份、原时钟、数据资格、独立Pawn与验证脚本，并负责构建/PIE和文档。

新运行目录Source/IntroCpp/MHWI/Monsters；源脚本Scripts/MHWI；原始工具缓存/批次在新的Saved隔离目录，精简证据在Tools/MHW。新资源候选/Game/MHWI/Rathian，原848动画保留历史/Game/MHWI/Rathalos路径。原作安装只读，既有第三方工具不改。

原时钟由动作执行唯一推进；Movement和Collision按传入的前后时间处理，不各自Tick重算。SourceProfile、EncounterGeneration、ActionRunId、PlaybackGeneration、LoopIteration、TargetSpawnId语义沿总方案。声明时间单位/坐标basis和资格证据，unknown不能填默认0。

## 接口与数据迁移

| 入口 | 当前 | 本批目标 | 影响 |
| --- | --- | --- | --- |
| THK源 | 已提105THK及thklst，语义未闭合 | 固定解析工具、输出一条可追溯节点链与资格结果 | 新解析器/证据，未知拒绝 |
| 原轨 | 已有FBX/AnimSequence | 新Movement消费源采样及显式原时钟 | 新Pawn，不改旧角色 |
| COL | 已读攻击字段，几何/事件待闭合 | 源形状/骨/事件映射与接触结果 | 新组件，未知不造shape |
| Attribute伤害 | 当前旧角色直接扣血 | 本批有来源时接专用结算；未闭合公式只报contact，不假设倍率 | 暂不改现有猎人主击/shell，完整双向桥接后续批次 |
| 验证资源 | 无独立雌火龙运行链 | 隔离测试场/动态夹具，正式路径与父类保存后读回 | 不保存旧训练地图 |

## 实施步骤与依赖

1. 固定基线、工具及本轮ADR选择记录。
2. 并行：THK/动作身份、源动画与位移、COL事件/骨几何取证。先以实际源ID协同，再编译一条动作数据。
3. 实施拒绝未知/旧身份的Movement、Collision和Pawn执行适配；一切样例数据标清源数据或纯工程夹具。
4. 整合真实源链，构建IntroCppEditor；若资格未闭合，构建基础设施并继续取证，不自动将夹具替代源链。
5. 启动独立验证场，实际采样THK结果/动作位置/位移/shape接触/提交结果；正常帧及跨窗/取消针对检查。
6. 固定原作条件进行对照，若访问或工具条件不足，记录具体缺口及证据，不冒称此次运行验证。
7. CHG记录实际结果，更新现状/接口/modules/问题与索引；目标未完整达成仍标partial。

## 验证计划

| 场景 | 方法 | 通过条件 | 边界 |
| --- | --- | --- | --- |
| 解析资格 | 固定工具/源hash、单条节点与损坏/未知拒绝 | 来源与关键字段可重建 | 不代表消费者已证 |
| 运行代码 | UE5.8 IntroCppEditor构建/UHT | 新类通过，旧内容未覆盖 | 不代表玩法通过 |
| 独立UE链 | 实际PIE事件与位置/接触记录 | 原节点→动作→移动→接触均可定位 | 工程夹具单列 |
| 原作对照 | 固定版本/任务/状态/装备/动作采样 | 原作与UE对照逐项通过 | 未运行保持待验 |
| 生命周期 | 旧RunId、逆时、阻挡、跨窗、中断、死亡/退出 | 无迟到提交/双移动/重复伤害 | 针对本批 |
| 文档 | python Scripts/Docs/check_docs.py；git diff --check | 本轮引用/清单/补丁有效 | 不代替上表 |

## 风险与回退

最大风险为THK函数/动作映射、原时钟及COL几何未闭合；优先取证，不通过经验数值绕过。源读取和新缓存均隔离；只撤销本批新代码/配置/资源引用，不整体回退已有太刀、地图和848动画。UObject写操作在游戏线程；异步回调核对弱引用/RunId/World生命周期。

## 文档同步清单

本轮更新总方案路线状态、ADR、Plans/Changes索引；实装后新增雌火龙链路现状、真实接口及模块入口、Known-Issues。历史CHG-002不改成实装记录。所有实际验证记新CHG。
