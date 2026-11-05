# CHG-20261025-005：R06剩余三项完整开发

- 状态：completed（开发完成，未编译/测试）。
- 日期：2026-10-25。
- 需求：继续完成R06真实前置拥有者、SpiritI/StepSlash专用入口和原生混合门控/独立时钟，全部开发结束后交付；不进行测试。
- 关联：[PLAN-005](../Plans/PLAN-20261025-005-mhwi-r06-remaining.md)、R06、R-COMBAT-014、MHWI-012/013。
- Git：工作区变更，未提交；保留用户已有的配置、代码、关卡、DataAsset和其他资产修改。

## 原因与结果

B09只有真实来源交接接口，Step/Creep/Shot没有实际调用方，气刃I/踏步斩还有通用表外入口，原生混合门控和帧步长也未落实。B10完成三项开发及资源、输入、HUD和记录接入。当前R06为开发完成、未验证；32行均有开发处理结果，node86维持原图无入边/0记录。

## 修改清单

| 文件/资产完整路径 | 符号/属性 | 原因与结果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacterNativeSources.cpp`（新增） | 来源拥有者、投射器触发、运行时Moveset | 16个精确绑定、规范小中大受击、弹刀34/221、104..112连射、实际实例/令牌和合法续段；115→101、四向翻滚；失控/中断清理 |
| `Source/IntroCpp/MHWI/MHWIContactResponse.h`（新增）、`MHWITrainingTarget.h` | 显式接触接口、大小/弹刀配置 | 不用零伤害和伤害阈值伪造来源类型；属性可由训练目标和其他实现者提供 |
| `Source/IntroCpp/MHWI/MHWINativeSources.h/.cpp`、`MHWIR06SourceData.inl`（新增） | 绑定、事件、common MBD、射击方向/前置变体 | 直接消费提取数据，精确保持原生身份；`ResolveDirectBlendSettings`拒绝未迁移模式，不借用Draw/纳刀Roll |
| `Source/IntroCpp/MHWI/MHWILinkAnimation.h/.cpp` | `ResolveActionEntry` | 全部分支与请求顺序、前置拔刀状态/身份、弱气刃、无请求保留旧载体、中间MBD来源 |
| `Source/IntroCpp/MHWI/MHWINativeLinkMotion.h/.cpp` | `FLinkExecution` | 保留连接bank、支持专用前段和不提交主段状态；末尾停止持有姿态载体 |
| `Source/IntroCpp/MHWI/MHWICharacterLinkMotion.cpp`、`MHWICharacter.h/.cpp` | 实例交接、输入/伤害/接触调用、求值前权重 | 接入真实拥有者、有序入口、同实例续用和自然结束提交；V/D-pad Left；运动/奔跑/转向互斥；中断/暂停/旧回调清理；修正头文件遗留损坏声明 |
| `Source/IntroCpp/MHWI/MHWIAnimInstance.h/.cpp` | 动画代理、`Montage_UpdateWeight` | 捕获当前显示姿态、首帧门控、线性插值、Actor秒×60；根运动新载体全权重，raw overlap未获门控不启用 |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h`、`Source/IntroCpp/MHWIUI/MHWIHUD.cpp` | 输入枚举尾追加、按键/弹药提示 | 原枚举值不改；新增V/D-pad Left，更新前进斩提示 |
| `/Game/MHWI/Animations/R06Remaining/A_w03_00_###`、`A_co00_00_###` | 32个新增AnimSequence | 29段武器bank、3段common，225骨猎人Skeleton，根运动制作设置见[B10现状](../Reference/MHWI-R06-Remaining-Development.md) |
| `Scripts/MHWI/extract_r06_remaining.py`、`export_r06_remaining.py`、`build_r06_remaining_data.py`、`record_r06_remaining_progress.py`（新增） | 固定源提取、源采样制作、生成与台账 | 保存DTI/动作工厂/入口/时钟/AT证据、FBX与来源表，支持后续重建 |
| `Scripts/MHWI/import_r06_staging.py`、`build_native_link_policy.py`、`build_link_runtime_data.py` | 目标目录参数、B10生成落点 | 不覆盖既有资源/制作日志或B09历史；13主段保护及124原序记录保留 |
| `Tools/MHW/native-r06-source-owners.json`、`native-r06-remaining-evidence.json`（新增）、`native-link-motion-policy.json`、`r06-runtime-adapter.json` | 稳定开发证据与部署清单 | 显式区分开发完成、源静态发现、资产制作、未验证；原始启用位与独立时钟可追溯 |

完整新增动画对象路径、FBX指纹在`Saved/MHWIRestoration/B10-20261025/r06-import-journal.json`，稳定部署清单同时保存在`Tools/MHW/r06-runtime-adapter.json`。正式DA、地图和蓝图本批未保存；角色在BeginPlay复制自己的Moveset后创建运行定义，CDO硬引用新增序列。

## 接口、事件与蓝图影响

MHWI-012的来源接口现在有真实玩法调用；仍需游戏线程、实际匹配的Montage实例、原生身份和撤销令牌，不授予任意输入权限。新增MHWI-013描述接触事实、来源输入/发射与混合生命周期。`EMHWIInput::SlingerBurst`只追加尾值；新增反射枚举、训练属性和接口需要后续完整构建后才能由编辑器识别，本轮按用户要求未构建。无需重命名蓝图类、旧字段或迁移重定向。

`ImpactCancelStart=0`、`RecoilCancelStart=10/60`、`SlingerCancelStart=45/60`、方向阈值0.2、初始弹药30、射击伤害1为项目适配。发射mTrigger第36源帧、动作身份/片段、Phase和MBD来自固定原始文件；不能把项目适配值当原版精确输入/伤害模型。

## 实际开发操作与未执行验证

| 操作 | 环境 | 实际结果 | 证据 |
| --- | --- | --- | --- |
| 固定原程序/非执行text副本静态提取 | 本机Python，仅读原始文件 | 39个来源注册均解析到入口；专用入口/设置回调/时钟消费者保存 | `Saved/MHWIRestoration/B10-20261025/remaining-native-functions.json`、稳定B10 evidence |
| Blender源采样FBX导出 | 项目既有MHWI转换环境 | 完成32段；初次尝试附带common181镜像上下文缺失、182无有效条目而中止，移出非本轮所需附带请求后续作完成 | `ArtSource/ThirdParty/MHWLongSword/R06Remaining-20261025/export-manifest.json`；B10 `export-authoring.log`、`export-completion-authoring.log` |
| `import_r06_staging.run`制作调用 | UE-MCP编辑器制作入口 | 导入并保存32个新增AnimSequence；没有调用PIE或玩法代码 | B10 `r06-import-journal.json`；Skeleton为导入选项信息，非新读回验证 |
| 表与台账生成脚本 | 本机Python | 写入32引用/124记录、164动作/Phase、16绑定及开发交付台账 | B10 `native-link-policy.json`、`runtime-source-data.json`与Tools清单 |
| 编译/UHT、PIE、自动化、语法、文档、diff检查 | 未执行 | 用户明确不测试；不声称通过 | 无本轮测试证据 |

静态源码阅读、提取、代码生成及资源制作属于开发操作，不是测试。B01/B02等历史验证结果仅保留原历史意义。本批代码、反射字段、动画代理和新资源均没有取得编译或运行验证。

## 风险、相邻范围与回退

R-COMBAT-014改为开发已修复、未验证。R07/R08/R09仍承载精确输入/缓存/方向；R24完整受击族及死亡、R25完整弹药/部位/伤害和R28完整移动各自开放，不扩大R06的开发结论。node86是原图结构事实，保持0记录，不作为人为待补入口。

修改前字节及哈希在`Saved/MHWIRestoration/B10-20261025/Backup`、`before-files.json`，HUD补备份位于同目录对应源码路径。回退仅恢复本批覆盖文件；本批新增源码/脚本/证据/文档可逐项撤除，新增32个动画包按导入日志清理。不要对整个工作区执行reset/clean，不覆盖用户之前的资产修改，不撤销B08/B09正式资产。原始MHWI文件、本地转换工具和第三方UE-MCP源码本批未修改。

## 已同步文档

[B10现状](../Reference/MHWI-R06-Remaining-Development.md)、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[32行台账](../Plans/MHWI-Connector-Progress.md)、[文档入口](../README.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)。CSV及资源制作README同步维护。
