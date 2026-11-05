# R06：B06本机连接控制取证（历史边界）

**最新现状见[B07原生执行链和实施](MHWI-Native-LinkMotion-Implementation.md)。下文保留B06当时的取证边界；B07已确认选择/退出/入帧消费者，不再沿通用drive门控推定太刀退出。正式播放适配仍未接入。**

更新：2026-10-25。状态：静态发现；取证工具已实现、待验证；LinkMotion退出和Phase1选择仍取证中。关联[逐连接台账](../Plans/MHWI-Connector-Progress.md)、[通过准则](../Plans/MHWI-Connector-Acceptance.md)。本轮未测试。

## 来源与实现

仅使用本机固定版本EXE和先前取得的本地非可执行代码区；原文件与代码区SHA分别为`c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea`、`9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe`。地址只适用于这一对来源，不套用公开2023版本地址。

[代码源清单](../../Tools/MHW/native-connector-code-sources.json)、[链式读取器](../../Scripts/MHWI/trace_native_connections.py)、[控制事实清单](../../Tools/MHW/native-connector-control-evidence.json)和[汇总入口](../../Scripts/MHWI/native_connector_logic.py)已落地。旧读取器只返回单个展开范围，现明确该语义并取消缺少pdata时默认读取256字节的后备。新读取器沿UNW_FLAG_CHAININFO关联同属范围；未知叶函数保持缺口，仅固定指纹、明确边界的三条叶函数范围列入白名单。未宣称覆盖每个尾跳/无展开片段。

## 已取得的指令事实

| 项目 | 本机定位 | 已确认范围与限制 |
| --- | --- | --- |
| 条件求值阻止字段 | `0x1423fc998`检查当前drive上下文`+0x30`，非零在`0x1423fc9a4`返回false | 通用FSM路径成立；字段不是已确认的太刀完成标志，也不由空条件自动解除 |
| 一条通用解除路径 | VM `0x1423febc9`检查非零；`0x1423febd8`比较配套`+0x34`与0；`0x1423febe4`扣除全局对象`+0x94`；`0x1423febef`写回；`0x1423febf6`正值跳过清零；`0x1423fec08`清零drive `+0x30` | 仅在实际到达该分支时；初值负数或无序比较会跳过。尚未确认全局量单位、所有前驱分支、LinkMotion是否使用。结果非正或无序比较的清零分支还更新owner `+0x2c`位；禁止直接转为秒/帧退出值 |
| 通用drive初始化/重设 | `0x1423fec80`内`0x1423fecdb`清`+0x30`，`0x1423fecde`将`+0x34`写为float -1 | 与上述非负值递减路径不同；不能因此推定连接退出或者Phase重置 |
| 回调绑定和调用 | `0x142458dd0`将update/state/exit函数对象存于process容器`+0x20/+0x28/+0x30`；VM state调用`0x1423feb6a`后未直接把返回值用作完成布尔量 | 具体回调及其副作用仍未找到；容器`+0x30`和drive `+0x30`不是同一个字段 |
| 可选Core钩子 | `0x1423fea76`加载Core `+0xd0`，`0x1423fea93`间接调用 | 具体写入者/目标未定；不能把任意对象同偏移写入认定为此钩子 |
| 本机Phase字段身份 | 类型注册`0x1401e15c0`：名称`0x1433c6598`、DTI `0x145000fc0`；虚表`0x1431c93d0` slot4 `0x140f0c750`返回同一DTI；slot3 `0x14191f7d0`中`0x141920387`加载`mLinkMotionPhase`，`0x141920399`取对象`+0x10c` | 已将本机`nTimelineParam::PlMotionCommon`字段与偏移关联，超出旧公开偏移猜测的证据范围；仍不是Phase选择消费者 |
| Phase对象初始化 | 构造`0x14191f5b0`在`0x14191f619`零写`+0x10c`的qword；同虚表slot5 `0x141921cb0`也在`0x141921d99`零写该处 | 新对象字段清零已确认；slot5实际调用时机、每次动作进入/退出是否重置、缺轨是否继承仍未知。不能将此提升为“缺轨默认0”或P1选择规则 |

## 排除与尚缺链条

Core钩子候选`0x1412b8360`实际循环步长为`0x250`，所观察到的`r9`是对象起点`+0x138`，其`[r9+0xd0]`并不是对象Core `+0xd0`；不能采用。`0x142713070`的候选LEA随后被`xor ecx,ecx`覆盖，`0x142797cd0`候选LEA随后被`xor eax,eax`覆盖，因此对应store实际是零值，旧跨指令常量启发式不成立。其他候选保持未定，未认定为游戏玩家逻辑。

对`+0x10c`进行了展开范围内的指令对齐筛选，留下643个函数候选及181次无展开元数据的位移字节命中；这些数量是候选集合，不是类型正确或消费者完整覆盖的结论。已定位的本机属性注册补足字段布局，但还缺从实际玩家动作对象到此字段的读取、P0/P1比较及MotionNo提交链。不得将相同偏移、参数构造或反射注册当作选择实现。

node60前置Action1003的完整片段仍未绑定；node76前置311的TIML第0帧为1。已确认的新对象清零不证明动作切换时重建对象，因此308/309/310缺轨仍不能判0，也不能据311轨道直接必选367。

下一步先定位实际LinkMotion回调/参数对象，追出drive阻止字段非零写入及对应解除路径，再证明Phase采样、P0/P1选择提交、-1后备与中断清理。所有连接的原退出帧仍为未确认；新增正式连接播放0条。

## 本地交接证据

`Saved/MHWIRestoration/B06-20261025/native-call-path.json`保存函数范围、原字节和事实；`source-logic-evidence.json`保存32条连接及两个Phase节点的逐条证据状态。`hook-candidates.json`、`generic-gate-writers.json`、`generic-unwind-gaps.json`、`phase-offset-aligned-candidates.json`、`phase-local-property-registration.json`、`phase-type-association.json`及`phase-vtable-writers.json`为静态探索原始输出，不作为测试报告；未对候选完备性作保证。

本轮只读取证及生成资料；没有执行游戏代码、修改游戏安装、写Content资产、编译、PIE、语法/文档/diff检查。下一阶段逐项要求见[验收页](../Plans/MHWI-Connector-Acceptance.md)。
