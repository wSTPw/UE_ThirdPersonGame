# CHG-20261025-002：B07原生连接控制核心与26段平行库

- 状态：partial。控制核心/原生数据/平行动画已实现；角色播放适配尚未实现，R06未完成；未测试。
- 日期：2026-10-25。
- 需求：沿已确认的原生执行链落实连接选择、退出和主动画入帧；不猜参数、不测试，每条同步状态与下一阶段通过准则。
- 关联：[PLAN-20261025-002](../Plans/PLAN-20261025-002-mhwi-r06-native-consumer.md)、R06、R-COMBAT-014、R-ANIM-008；MHWI内部实现，不新增蓝图接口。
- Git：工作区变更，未提交。大量原有修改保留。

## 原因与结果

B06追到通用cAIFSM门控和Phase元数据，但不能证明玩家如何使用LinkMotion。B07找到玩家加载器将节点转换成目标动作连接表的实际链条；选择按前置原生group/id和PlMotionCommon采样Phase精确匹配，无Phase1→0后备；连接阶段等待动画层结束谓词，再调用主段播放，MBD消费者提供主段startFrame。MotionNo负数在加载时省略，node86无入边不产生调度。

已把确认规则写入独立C++控制核心，生成32引用/124身份记录/317MBD匹配块；26段原生采样FBX已导出并导入独立动画库。**AMHWICharacter没有调用新核心，正式新增连接调度0条。** 主片段105/112、混合字段下游及根运动/武器/事件时钟适配仍是开发工作，不能将此批记为完整还原或“只差测试”。

## 修改清单

路径均相对项目根`E:/Unreal Projects/IntorCpp/`。

| 文件/资产路径 | 符号/属性 | 原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWINativeLinkMotion.h/.cpp` | FindLink、FindBlend、IsMotionEnded、FLinkExecution | 原生帧和身份的控制请求；保留无MBD覆盖；原生结束才提交主段；中断/过期回调代次保护；无新反射字段 |
| `Source/IntroCpp/MHWI/MHWINativeLinkMotionData.inl` | LinkEntries、BlendEntries | 编译期原值表，避免运行时JSON加载/cook路径假设；源身份内先P0/P1，保持加载顺序 |
| `Scripts/MHWI/build_native_link_policy.py` | build、write_cpp | 读固定原EXE数据表和FSM/LMT/MBD，生成数据；不调用旧build的往返断言或测试入口 |
| `Tools/MHW/native-link-motion-policy.json`、`native-link-motion-consumer-evidence.json` | 原始值、源指纹、关键指令片段和明确叶边界 | 原生选择、结束谓词、Phase重绑定清零及MBD请求可定位；静态证据不等于运行验证 |
| `Scripts/MHWI/export_r06_staging.py` | main | 无测试导出；不导入验证模块、不回导FBX、不改原blend或NativeFidelity清单；NeedsParent仍拒绝猜补 |
| `ArtSource/ThirdParty/MHWLongSword/R06Staging-20261025/` | 26个FBX、export-manifest.json | 独立源采样片段；制作结果，未验证 |
| `Scripts/MHWI/import_r06_staging.py` | run | 只新增独立AnimSequence包；既有包拒绝覆盖；不修改正式动作表/蒙太奇 |
| `/Game/MHWI/Animations/R06Staging/A_w03_00_###` | 26 AnimSequence；导入指定Skeleton `/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton` | RootMotion true，RootLock REF_POSE，ForceRootLock false；制作调用返回成功，未读回测试 |

## 接口与蓝图影响

新增内部C++头文件接口，输入必须是已解析的实际原生动作身份/Phase/主片段/源帧，不允许用FSM枚举或UE秒数冒充。没有UCLASS/USTRUCT/UFUNCTION迁移，没有修改角色、既有DataAsset、正式Montage、蓝图、关卡或第三方插件。新增平行资产暂未被正式Moveset引用。

## 实际执行与未验证项

| 操作 | 实际结果 | 证据 |
| --- | --- | --- |
| 原EXE/本地非可执行区静态读取和原资源解析 | 提取原生控制事实、身份与MBD数据；未运行原游戏 | `Tools/MHW/native-link-motion-consumer-evidence.json`；`Saved/MHWIRestoration/B07-20261025/`静态片段 |
| `python Scripts/MHWI/build_native_link_policy.py`（数据制作） | 32引用、124身份记录；生成C++原值表；不是测试通过 | `Tools/MHW/native-link-motion-policy.json` |
| 便携Blender后台执行`export_r06_staging.py`（动画制作） | 26导出、0个NeedsParent阻止；没有姿态验证或FBX回导 | `ArtSource/ThirdParty/MHWLongSword/R06Staging-20261025/export-manifest.json` |
| 编辑器启动、ExecutePythonCommandEx执行`import_r06_staging.run()`（资产制作） | 返回imported26、tests_executed=false、formal_moveset_changed=false；没有PIE | `Saved/MHWIRestoration/B07-20261025/r06-import-journal.json` |

按用户要求，没有C++编译、PIE、自动化、语法、姿态/回导、文档检查或git diff检查；没有将历史结果记作本批通过。上一轮编辑器调用曾因自动审批服务用量失败，本轮同一正常访问已恢复并成功完成制作，不再作为当前阻止原因。Epic工具集不可用，改用已读取本机声明的PythonScriptLibrary公开调用制作资产。

## 遗留与回退

继续开发：原生动作构造/主片段（105/112）；MBD混合下游消费者；角色适配的动画结束事实、源采样Phase、连接/主段根运动、武器/命中/取消时钟及既有129前缀防重复。node86不补造可达性。通过准则逐32引用和B07验收表同步，所有测试留到下一阶段。

修改前文档/工具备份见`Saved/MHWIRestoration/B07-20261025/Backup/`及`before-files.json`。本批新增C++/数据/制作脚本可单独回退；原角色行为未改。若回退素材，只移除本批新建R06Staging源目录和独立资产目录，不触碰原NativeFidelity、正式动画、Moveset或原游戏安装。操作前核对目录归属和后来是否新增引用。

## 已同步文档

[实施现状](../Reference/MHWI-Native-LinkMotion-Implementation.md)、[B06历史边界标记](../Reference/MHWI-Native-Connector-Control.md)、[逐连接MD/CSV](../Plans/MHWI-Connector-Progress.md)、[通过准则](../Plans/MHWI-Connector-Acceptance.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[系统现状](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[技术入口](../README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
