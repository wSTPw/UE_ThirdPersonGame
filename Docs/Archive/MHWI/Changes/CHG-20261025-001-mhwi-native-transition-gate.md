# CHG-20261025-001：B06链式函数、连接门控及本机Phase字段

- 状态：partial，工具已实现、待验证；具体LinkMotion退出与Phase1选择仍取证中。
- 日期：2026-10-25。
- 需求摘要：沿原生代码优先追阻止字段写入/解除及Phase1选择，确定即实现，不猜参数、不测试。
- 关联：[PLAN-20261025-001](../Plans/PLAN-20261025-001-mhwi-native-transition-gate.md)、R06、MHWI-010；无新接口。
- Git：工作区变更，未提交；保留用户已有源码/资产修改。

## 原因与结果

旧原生读取器只取单个pdata范围并在未知叶函数默认读256字节，可能遗漏拆分分支或跨界。新增固定来源指纹、CHAININFO关联和显式叶范围读取，汇总写B06，保留B04/B05报告。

本机代码确认通用FSM的drive `+0x30`非零阻止条件求值，并找到一条以配套`+0x34`递减到耗尽后清零的通用路径及初始化清零路径；LinkMotion写入端和具体使用关系仍未知。另以本机类型/虚表/属性绑定确认`mLinkMotionPhase`属于PlMotionCommon `+0x10c`，构造与slot5有零写；动作重置、缺轨后备和P1选择仍未知。具体地址和边界见[控制取证现状](../Reference/MHWI-Native-Connector-Control.md)。

## 修改清单

| 文件/资产完整路径 | 符号/落点 | 原因与效果 |
| --- | --- | --- |
| `E:/Unreal Projects/IntorCpp/Scripts/MHWI/native_control_evidence.py` | Image.function/string_xrefs | 缺pdata不再伪造256字节函数，显式单范围语义 |
| `E:/Unreal Projects/IntorCpp/Scripts/MHWI/trace_native_connections.py` | NativeTrace/run | 展开链、指纹、显式叶范围及8项事实；未运行原生代码 |
| `E:/Unreal Projects/IntorCpp/Tools/MHW/native-connector-code-sources.json` | 地址/指纹/三条叶范围 | 本机固定版本来源与已观察边界，待下一阶段独立复核 |
| `E:/Unreal Projects/IntorCpp/Tools/MHW/native-connector-control-evidence.json` | 通用VM及参数事实 | 保留weapon_exit_rule/phase_selection_rule为null |
| `E:/Unreal Projects/IntorCpp/Scripts/MHWI/native_connector_logic.py` | run | 接入通用解除/重设、Phase布局和初始化证据；逐32引用保留未确认状态 |
| `E:/Unreal Projects/IntorCpp/Docs/Plans/MHWI-Connector-Progress.md`及同名CSV | 全32引用 | 逐条同步B06状态、下一步和通过门槛，保留B05左右修复待测状态 |

## 接口、事件与资源影响

无UE反射字段、玩法接口、蓝图或正式资源变化；新增正式连接0条，未制作退出帧或Phase1选择参数。离线Image.function缺少pdata时由默认读取变为抛出ValueError；string_xrefs保留缺边界记录并标记null。历史临时脚本若依赖该后备需迁移，不应绕过来源保护。

## 实际验证

未执行任何测试、编译、PIE、语法、文档或diff检查，遵循用户要求。没有本轮Content全量哈希比较。已执行的是只读静态原生代码提取及源资料汇总，产物在`Saved/MHWIRestoration/B06-20261025/`；均标记tests_executed=false，不能写为通过。开发初次提取因逐项线性查找过慢而中止，改用集合成员查找后完成提取；这不是测试结果。

下一阶段通过准则覆盖函数分段/边界、原字节事实、通用递减及初始化边界、本机Phase类型/清零、每条退出和两个Phase节点的选择/后备/中断，见[验收页](../Plans/MHWI-Connector-Acceptance.md)。旧B04测试输出只保留历史。

## 风险、遗留与回退

R06仍开放。时间单位、具体LinkMotion写入/解除、可选Core钩子目标和P1选择提交链未定；相同字段偏移不证明同一对象。资料工具也未测试，不应拿通用事实自动生成正式播放规则。

回退时恢复`Saved/MHWIRestoration/B06-20261025/Backup/`中的两个原读取/汇总入口及现状文档，移除本批新增读取器/两份代码与事实清单/新文档条目即可；无需恢复Content。保留B05来源修复和B04原MBD接入。Saved证据可保留；未修改安装文件。

## 已同步文档

[总台账](../Plans/MHWI-Restoration-Progress.md)、[逐连接台账](../Plans/MHWI-Connector-Progress.md)、[通过准则](../Plans/MHWI-Connector-Acceptance.md)、[系统现状](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[入口](../README.md)、[开发流程](../Development.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)。
