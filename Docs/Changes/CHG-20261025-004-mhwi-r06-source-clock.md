# CHG-20261025-004：R06真实来源交接、主段保护与统一入帧

- 状态：partial；**用户要求的完整R06尚未完成，不是只缺测试**。
- 日期：2026-10-25
- 需求摘要：完整完成MHWI台账R06，开发后不测试。
- 关联：[PLAN-20261025-004](../Plans/PLAN-20261025-004-mhwi-r06-completion.md)、R06、MHWI-012、R-ANIM-008、R-COMBAT-014。
- Git：工作区变更，未提交。

## 原因与结果

B08的连接准备只在选中连接时消费MBD；无连接则固定主段0帧。连接推进还把Montage秒乘60当作源帧，清理与新播放会使用不同参数重复停止旧载体。此次统一直入/连接后的MBD入帧和事件初始化，按真实段倍率转换连接源时钟，并提供实际来源实例的精确身份交接接口。

所有R06目标终点已追加原生注册/工厂/实例入口证据，编译期13绑定防止错误资产被当成已确认主段。但来源接口尚无Step/Creep/KijinComboShot正式玩法调用方；另发现气刃I及踏步斩有通用连接表之外的专用分支，原生混合仍受未迁移的MotionTree/request标志及独立时钟控制。因此R06继续部分实施，逐32行标明剩余开发，没有伪造“开发完成/只待验收”。

## 修改清单

| 文件 | 符号/效果 |
| --- | --- |
| [MHWICharacter.h](../../Source/IntroCpp/MHWI/MHWICharacter.h)、[MHWICharacter.cpp](../../Source/IntroCpp/MHWI/MHWICharacter.cpp) | 来源令牌/实例持有、入口源时钟、旧载体失败清理；在实际入帧求倍率/事件状态 |
| [MHWICharacterLinkMotion.cpp](../../Source/IntroCpp/MHWI/MHWICharacterLinkMotion.cpp) | Bind/Release、Prepare/Begin/Commit、InitializeMainEventClock；连接与主段使用实际源帧/入帧，原生绑定保护 |
| [MHWILinkAnimation.h](../../Source/IntroCpp/MHWI/MHWILinkAnimation.h)、[MHWILinkAnimation.cpp](../../Source/IntroCpp/MHWI/MHWILinkAnimation.cpp) | ResolveIdentityLink、IsKnownSourceIdentity、MotionPosition、GetNativeMainMotion；未知目标无表保持直入，未知来源不绑定 |
| [MHWILinkRuntimeData.inl](../../Source/IntroCpp/MHWI/MHWILinkRuntimeData.inl) | 13个原生主段绑定；164动作/Phase/连接武器键沿原数据生成 |
| [extract_r06_completion.py](../../Scripts/MHWI/extract_r06_completion.py) | 固定指纹54函数/12目标原生动作提取；分清DTI虚表和实例虚表；保留自定义入口及混合门控缺口 |
| [build_native_link_policy.py](../../Scripts/MHWI/build_native_link_policy.py)、[build_link_runtime_data.py](../../Scripts/MHWI/build_link_runtime_data.py) | 输出改为B09，消费补齐的主段绑定；历史资产报告不当本次验证；资产制作状态与运行验证状态分开 |
| [record_r06_completion_progress.py](../../Scripts/MHWI/record_r06_completion_progress.py) | 同步32行CSV/MD及总CSV，保留来源调用方/自定义入口/混合门控开放项 |
| [native-main-motion-bindings.json](../../Tools/MHW/native-main-motion-bindings.json)、[native-r06-completion-evidence.json](../../Tools/MHW/native-r06-completion-evidence.json)、[native-link-motion-policy.json](../../Tools/MHW/native-link-motion-policy.json) | 现状证据及13绑定；124原始有序记录保留，node86不增加可达入口 |

工作区原有大量Source/Content/配置修改已在开始时辨明；没有重置Git、回退用户内容或保存Content资产。`MHWIAnimInstance.h/.cpp`的工作中尾权重分支已恢复为B09开始时的原字节；正式结果不包含未经证明门控的自动尾淡出。

## 接口、事件与资产影响

新增MHWI-012游戏线程C++来源接口，未新增Blueprint可调用入口。`BindNativeActionSource`返回非零绑定令牌，0表示失败；必须提供正在播放的实际Montage实例与原生已知group/action。消费时重新取该实例源帧，失效不回读陈旧位置；Release仅对当前令牌生效。它不取代输入、取消、资源资格，也不把缺失前置玩法视为已经实现。

Source新增瞬态UObject持有字段，需要后续完整编译/UHT和重载；没有改变DataAsset反射结构、现有资产路径或事件签名。连接→主段不重扣成本、不广播第二次动作开始。旧动作在物理换片前先逻辑失效，新播放失败会停止旧载体。原生Main绑定失败或不能转换入帧时拒绝替换当前动作。

## 实际执行与未执行

| 操作 | 实际结果 | 证据 |
| --- | --- | --- |
| 初始`git status --short`及项目/源文件读取 | 辨明用户既有修改；只读开发定位 | 开始时工具输出；B09备份清单 |
| 修改前逐文件字节备份与SHA256 | 已保存Source/MHWI、Scripts/MHWI、Docs、Tools/MHW受影响基线 | `Saved/MHWIRestoration/B09-20261025/Backup`、`before-files.json` |
| `python Scripts/MHWI/extract_r06_completion.py` | 只读原文件静态提取54函数、12目标动作，补13主段绑定；非测试 | `completion-native-functions.json`、稳定Tools证据 |
| `python Scripts/MHWI/build_native_link_policy.py` | 生成32引用/124记录；本次不写资产 | `Saved/MHWIRestoration/B09-20261025/native-link-policy.json` |
| `python Scripts/MHWI/build_link_runtime_data.py` | 生成164动作、原Phase/武器键与13主段绑定；非校验命令 | `runtime-source-data.json`及编译期表 |
| `python Scripts/MHWI/record_r06_completion_progress.py` | 写B09交接台账，R06_complete=false；非测试 | 32行MD/CSV及总CSV |
| MCP `project.get_status` / `blueprint.read` | 为开发定位确认项目`E:/Unreal Projects/IntorCpp`及`/Game/MHWI/Blueprints/ABP_MHWI_Hunter`父类`MHWIAnimInstance`；未启动PIE或保存蓝图 | 本轮只读工具输出 |
| 编译、UHT、蓝图编译、PIE、自动化、语法、文档、diff检查 | **全部未执行，遵照用户要求** | 无本批通过报告 |

原代码静态读取中的候选/缺失叶边界不作为原生执行证明。B01至B08历史测试没有重跑或引用为此次通过。脚本运行和生成数量不等于源码/玩法正确性已验证。

## 遗留与回退

1. 接入node26/27 Step、43 Creep及66..75等来源的实际玩法拥有者；当前API没有这些生产调用方。
2. 迁移SpiritI/StepSlash专用入口，补151等原片段及玩家状态/身份优先级，不能用表内131/152等覆盖全部路径。
3. 查清MotionTree/request启用位、曲线、owner+6c步长及中断中的混合；已有插值帧→UE时间仍是适配，完整原生权重未完成。
4. 上述开发完成后再按用户后续安排编译/验收。本轮没有宣称全R06已实现。

恢复本批修改文件时使用B09备份，保留用户此前已存在的修改。新增B09计划/记录/现状页、提取/台账脚本及新证据文件可单独移除；B08正式资产未改，不需要回退Content。

## 已同步文档

[B09现状](../Reference/MHWI-R06-Completion-Development.md)、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[逐连接台账](../Plans/MHWI-Connector-Progress.md)、[下一阶段准则](../Plans/MHWI-Connector-Acceptance.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)、[文档入口](../README.md)。
