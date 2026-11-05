# PLAN-20261027-002：MHWI 忠实还原重构审查与选型

- 状态：draft
- 日期：2026-10-27
- 用户需求：用户认为 MHWI 当前实现方向和复杂度已不可接受，希望提出重构方案；目标经确认是**忠实还原原版 MHWI**。所有技术方向须先搜索对应社区官方已有方案，不得未经用户选择擅自定案。
- 关联模块 / 接口 / 问题：`mhwi-longsword`；R06、R28、R30、R-COMBAT-010、R-ANIM-003/007/008 等现状条目
- 实施记录：尚未实施。本文是审查与选型提案，不授权玩法重写、资产迁移或删除。

## 现状与目标

### 已核实的项目事实

- 工程为 UE 5.8，一个 `IntroCpp` Runtime 模块；`IntroCpp.Build.cs` 目前没有声明 `GameplayAbilities` 模块依赖。`.uproject` 启用了 GameplayAbilities 插件，不等于 MHWI 已采用 GAS。
- `Source/IntroCpp/MHWI/` 有 22 个 C++ 文件。`MHWICharacter.cpp` 为 2,032 行；`AMHWICharacter` 的实现包含输入映射/组合解析、移动意图和转向、武器姿态、招式选择/播放、动作时间推进、命中扫掠、缓冲输入、气刃资源与衰减、空中登龙链、受击/死亡及延迟追加伤害等职责。头文件有 40 条 `UPROPERTY` 和 36 条 `UFUNCTION` 声明。
- `MHWIMovesetData.h` 有 125 条 `UPROPERTY`。`FMHWIMoveDefinition` 同时保存动画、窗口/派生、费用、反击/无敌、转向、装备动作与空中动作适配等字段。
- `Scripts/MHWI/` 当前有 125 个 Python、5 个 JSON 和 1 个 MJS 文件；`Content/MHWI/` 有 416 个文件。数量本身不能判定为污染：其中包含源数据提取、验证、资产制作、运行检查及其证据，需先标明每项是否为正式依赖、一次性工具或历史产物。
- 本轮盘点时 `git status --short` 有 54 条路径，覆盖源码、脚本、文档和 `.uasset/.umap`。这些现存工作区改动必须按用户工作保护，不能在重构时直接清理或回退。
- 当前现状页将 MHWI 明确作为独立训练模组。B20 已记录若干项目侧消费者及 PIE 结果；同时保留 R06 原生连接来源/Phase 覆盖、原生移动 FSM/物理、原生 IK solver 语义等未闭合边界。已实现的 UE 适配不能自动视为原作实现。

以上事实显示职责集中、数据契约宽、来源证据与运行适配并存，足以支持开展重构审查；它们**不能单独证明**某一特定架构就是正确答案，也不能说明现有 131 个脚本或 416 个资产都应删除。

### 目标与硬边界

1. 以可追溯的原作行为为唯一玩法目标，不把“手感相近”或“可玩”替代逐项还原。
2. 每项运行行为应区分原作已证事实、UE 适配、未解语义；未知值不得以猜测补齐。
3. 保留原始证据、已验证资产和可复现制作步骤；重构顺序不得让生成器覆盖原始数据或掩盖来源。
4. 不先迁移到某个框架，也不先删代码/资产/脚本。先完成目录与依赖审计，再由用户选择目标边界。
5. 此计划不承诺多人、存档、跨项目复用或可运行时启停；若这些目标新增，必须重新评估候选。

## 官方 UE 5.8 方案调查

以下为 Epic 官方资料查到的引擎能力，不是对 MHWI 重构架构的自动裁决。官方资料不能替代原作行为取证。

| 官方方案 | 官方资料实际覆盖内容 | 对本项目可能有帮助的范围 | 需要用户选择/核对的部分 |
| --- | --- | --- | --- |
| Actor Components | Epic 将组件定义为可附加给 Actor 的功能单元，可用于拆分输入、AI 等概念行为；[Basic Components](https://dev.epicgames.com/documentation/en-us/unreal-engine/basic-components-in-unreal-engine)；[Gameplay Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-in-unreal-engine) | 可评估将 `AMHWICharacter` 中有清晰生命周期/状态所有权的职责分离，同时保持同一 Runtime 模块 | 需要先界定组件对动作主时钟、输入许可、命中事件和中断提交的所有权；不能只是机械搬函数 |
| Gameplay Modules | 模块是单独 DLL；可改善链接/迭代，但增加模块会增加导出宏、接口和依赖管理，Epic 明确指出 gameplay 是否值得拆分取决于团队需求；[Gameplay Modules](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-modules-in-unreal-engine) | 如果 MHWI 需要独立编译、复用或明确依赖边界，可评估独立 Runtime 模块 | 目前只有单模块且主要是本地独立训练地图；是否值得承担 UHT、Build.cs、蓝图类迁移和模块导出成本未知 |
| Game Features / Modular Gameplay | 官方方案用于建立可独立启停的 feature plugin；Add Components 通过组件承载 feature 行为；[Game Features and Modular Gameplay](https://dev.epicgames.com/documentation/unreal-engine/game-features-and-modular-gameplay-in-unreal-engine) | 若用户需要把 MHWI 当可选、可启停的独立功能，或未来在多模式/项目复用，可调研 | 当前没有已确认的动态启停/多项目复用需求；不能因为“隔离”听起来合适就默认引入插件生命周期 |
| Gameplay Ability System (GAS) | Ability 可管理多阶段动作、成本、冷却、输入、动画、打断与属性交互；也包含网络能力；[Using Gameplay Abilities](https://dev.epicgames.com/documentation/unreal-engine/using-gameplay-abilities-in-unreal-engine?lang=en-US)、[Understanding GAS](https://dev.epicgames.com/documentation/en-us/unreal-engine/understanding-the-unreal-engine-gameplay-ability-system) | 可作为动作所有权与取消生命周期的候选，对照现有招式/窗口/成本系统做小范围映射评估 | GAS 不会自动还原原生 TIML/FSM 时序；当前本地玩法是否值得引入其对象/任务/标签模型尚无证据。插件启用但源码未依赖，不能当成迁移决定 |
| Animation Blueprint Linking | Anim Layer Interface / Linked Anim BP 可将 AnimGraph 子图分层、替换或分配给不同子图；[Using Animation Blueprint Linking](https://dev.epicgames.com/documentation/unreal-engine/using-animation-blueprint-linking-in-unreal-engine) | 可用于隔离移动、武器或姿态图逻辑，前提是确认当前 ABP 的真实图和所有权 | 该方案负责动画图复用/组织，不拥有招式输入、连接资格、伤害时序等玩法权威状态 |
| Data Assets / Primary Data Assets | `UDataAsset` 保存系统数据；`UPrimaryDataAsset` 增加 Primary Asset ID 与 bundle，可手动加载/卸载；[Data Assets](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-assets-in-unreal-engine)、[Asset Management](https://dev.epicgames.com/documentation/unreal-engine/asset-management-in-unreal-engine) | 用于评估招式数据按类别拆分、资产引用和加载生命周期 | 官方资料不要求把所有 `UDataAsset` 升成 Primary；需先确定是否需要 Asset Manager 的手动加载、卸载、bundle 或 cook 管理 |

## 候选方向（未选择）

| 候选 | 适用条件 | 主要代价/未知 | 当前状态 |
| --- | --- | --- | --- |
| 在单一 Runtime 模块内用组件分离职责 | 主要问题是角色类职责集中，而不需要独立分发/启停 | 状态所有权和跨组件事件必须重新定义；组件数量和接口成本需控制 | 待用户选定审查 |
| 将 MHWI 放进独立 Runtime 模块或普通插件 | 需要编译隔离、复用，或把 MHWI 作为工程可管理的独立代码包 | C++ 模块依赖、导出宏、蓝图父类/资产引用迁移；并不自动拆分内部职责 | 待用户选定审查 |
| 将 MHWI 做成 Game Feature | 需要运行时/编辑器 feature 注册与启停，或独立发行 | 增加 GameFeatureData、生命周期动作及组件接收器要求；当前需求未证明必要 | 待用户选定审查 |
| 将动作执行重构到 GAS | 招式生命周期、取消、资源成本与事件语义可映射到 GAS，且实证迁移不会丢失原始时序 | 高迁移面；Native source/Phase/连接规则需另行表示；需构建可回退的代表性样例 | 待官方 API 与项目动作逐条映射后再决定 |
| 只整理 AnimGraph 与数据资产，保留 C++ 动作权威 | 主要问题是图和配置难维护，动作状态机仍保留项目/原生适配 | 无法单独解决 Character 类中的输入/战斗/资源职责集中 | 作为局部候选，不能宣称是总重构 |

这些候选可组合，且目前没有证据支持一口气全选。除用户明确方向外，先对比组件边界与依赖图，再提交架构裁决；不直接改写。

## 阶段计划与决策门

| 阶段 | 工作 | 通过条件 |
| --- | --- | --- |
| 0. 保护现状 | 以当前工作区为基线，单独登记已修改的源码、生成证据、正式资产和临时资产；不 reset、不批量删除 | 能区分本次重构前已有内容与后续变更；资产来源/指纹可追溯 |
| 1. 做只读结构审计 | 对每个 C++ 类型、运行状态、Montage/DA、AnimBP、导入数据和脚本记录生产者、消费者、来源证据、运行状态、是否正式使用；特别标出重复生成器、历史脚本和丢失报告 | 产出有路径/符号/资产引用的依赖图与“保留/待确认/可退役候选”清单；不以文件数量判定污染 |
| 2. 用户选择架构候选 | 比较“单模块组件化 / 独立模块或普通插件 / Game Feature / GAS 作用域 / 仅动画和数据整理”，针对候选核对 UE 5.8 官方 API 与实际依赖；说明哪些选择只是可用、哪些已有证据证明适配 | 用户明确批准一个候选或组合；若官方资料与原生取证均不足，保持待定 |
| 3. 选一条已证据闭合的垂直切片 | 由用户从完整来源证据中指定一个端到端案例，保留原行为结果，比较重构前后输入资格、源身份/帧、费用、命中事件和中断收尾 | 自动/静态和 PIE 验收范围由用户确认；无来源记录或当前运行基线不完整时不作为试点 |
| 4. 分批迁移 | 每批只移动已通过的责任边界，更新 C++/反射/蓝图/DA 迁移表；保留未闭合功能当前适配并标明，不在重构名义下补猜机制 | 每批有已验证用例与回退点；接口、委托顺序和资产路径保持可审计 |
| 5. 退役冗余 | 仅在依赖审计证明无正式消费者、证据可重建且用户确认后，归档/删除重复脚本、过期数据与实现 | 相关蓝图/脚本/编辑器消费者已查；正式资产与原始证据的来源未丢失 |

## 范围、接口与验收标准

- 本次草案覆盖 MHWI 训练模组结构和其 C++/蓝图/数据/工具边界；不包含实际玩法改写。
- 首个实施批次必须遵守原生时钟、帧号与 UE 时间适配分开记录；要求每个行为能追到源表/函数/帧区间以及 UE 消费者。无法证明的部分维持 `unverified`，不可因重构而提升完成状态。
- 若迁移动作状态所有权，须列清输入资格、主动作身份/Phase、Montage 段落时钟、费用扣除时刻、命中/追加事件次数、取消/死亡/切图/旧回调处理与蓝图调用方；不能仅用“动画能播放”验收。
- 保留现有 B20 已验证范围为回归基线，但其适配不冒称原生实现；R06/R28/R30 尚未闭合项继续单列。
- 当前没有足够证据设置完整重构的接口与验收矩阵。阶段 1 完成后应补充接口/资产清单；用户选定架构前，不写最终目标类图或数据格式。

## 验证计划

下表是未来实施门槛，不代表已经执行。当前交付只做文档与规则更新。

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 文档一致性 | `python Scripts/Docs/check_docs.py`、`git diff --check` | 文档链接/格式与补丁无空白错误 | 当前文档修改 |
| 依赖核对 | 源码静态调用搜索、UE 资产/蓝图引用读回 | 清单中的每项有实际消费者和父类/引用证据 | 需用户批准结构审计范围后执行 |
| 候选架构试点 | UE 5.8 最小编译与指定 PIE 真实输入路径 | 保持同等原作来源、时序、资源与事件结果 | 需先选架构与垂直切片 |
| 整体重构回归 | 按原作行为台账逐行执行静态/构建/PIE 验收 | 已闭合项无回归，未解项仍明确标记 | 需先完成台账与验收范围 |

## 风险与回退

- 当前工作区有 54 条既有修改路径。本方案不假设它们属于同一批已完成提交，不覆盖其文件或资产。开始实施前应由用户确认采用的工作区基线/快照范围。
- UE 反射类改名/拆分会影响蓝图父类、软引用、DataAsset 和资产重定向；必须先盘点完整 `/Game/...` 路径并验证读回，再迁移。
- 以大量新抽象替换一个大类可能扩大接口面；只按已识别责任边界和用户选择验证。
- 将未知原生语义“适配掉”会永久遮蔽还原缺口；对未知行为不得删除原始证据或覆盖字段。
- 每个批次需保留迁移前源码/资产映射和独立回退点；未迁移资产不得由新生成器覆盖。

## 文档同步清单

- 方案选择后再更新 [MHWI 现状页](../Systems/MHWI-LongSword.md)、[接口契约](../Interfaces.md)、[问题清单](../Known-Issues.md) 和 [模块索引](../Reference/modules.json)。
- 实施后按批次新增 CHG，记录源证据链接、源码/反射/资产影响、实际验证、未验证边界与回退。
- 架构取舍只有在用户批准、候选论证与试点证据齐全后，才新增 ADR；本文阶段不创建 ADR。

## 决策前须由用户确认

1. 以上候选中的哪一种作为首个受控试点，或是否要求先完成第 1 阶段只读清单后再选？
2. 是否把原作取证工具和可再生成的 JSON/脚本全部视为重构资产的一部分，还是只保留被正式玩法/验收引用的最小集合？
3. 首个端到端回归希望覆盖哪项已证据闭合的太刀行为？

在这些选择收到回复前，不迁移类/模块、不改资产、不重写机制、不清理脚本。
