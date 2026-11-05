# R06 B09：真实来源交接、统一入帧与主段绑定

更新：2026-10-25。**部分实施；用户要求的完整R06尚未达成。未编译、未测试。** 本页接续[B08角色接入](MHWI-R06-Character-Playback.md)，不能把新增接口、静态证据或未调用的来源管线记为前置玩法已经实现。

## 已实现的开发修改

- `PrepareNativeLink`在清理旧动作前取实际Montage实例的bank/motion/frame。没有连接匹配时也消费原MBD专用行/序列化第0行，直入主段不再固定从0开始。无法读取真实实例时拒绝切换，不使用陈旧位置冒充当前来源。
- `InitializeMainEventClock`统一直接入口及连接后入口。入帧前的武器键只建立状态；过去的命中、转向、取消区间不从0补算。初始播放倍率在实际入帧求值，费用仍只在动作开始提交一次。
- 连接的Montage秒数和原始源帧分开保存。入帧经过实际段裁剪、段倍率及Sequence RateScale转换；连接结束预测与152武器事件按源帧推进，不再假定`Montage秒×60`永远等于源帧。
- 切换时先使旧动作代次失效，由新Montage播放统一停止旧组/根运动实例。取消了清理阶段与播放阶段使用不同混出参数的重复停止；若新片段创建/播放失败，`NativeRetiringMontage`负责停止尚未交出的旧载体。没有修改正式Montage包。
- 新增游戏线程C++接口`BindNativeActionSource/ReleaseNativeActionSource`。真实Step/Creep/Shot拥有者可交接精确group/action、实际Montage实例和当前源帧，返回非零撤销令牌；陈旧令牌、错实例、未知身份和失效来源不生效。该接口**不授予取消/输入许可，也没有新增这些玩法的调用方**。
- 对全部R06目标终点补充本机注册表→DTI注册→工厂→实例虚表→入口/更新证据。编译期表现在包含13个主段绑定（含既有插入上挑），连接准备阶段拒绝实际资产与原生主段不符。DTI自身4槽虚表与动作实例虚表分开处理；共享DTI不折叠不同原生ActionID。

来源：[主段绑定](../../Tools/MHW/native-main-motion-bindings.json)、[B09静态事实](../../Tools/MHW/native-r06-completion-evidence.json)、[提取入口](../../Scripts/MHWI/extract_r06_completion.py)。54个函数范围保存在`Saved/MHWIRestoration/B09-20261025/completion-native-functions.json`，不是测试结果。反汇编范围内的跳转表数据不视为可执行指令依据；缺失叶函数边界仍明确保留。

## 新确认的完整开发缺口

| 缺口 | 已取得的证据 | 仍必须实现 |
| --- | --- | --- |
| 来源玩法 | 原生身份表及已绑定实例交接接口；原node26/27是Step，43是Creep，66..75含KijinComboShot | 实际玩法拥有者播放自己的正确片段，并在合法输入/退出时调用接口。现有Draw/纳刀Roll不得充当这些来源；接口存在不能关闭逐行缺口 |
| 气刃I专用入口 | `1417fe610`按玩家状态、当前/前置身份选择113/116/126/130/132/152，再进入通用入口 | 继续证明所读玩家状态和两套身份的消费者并迁移完整优先级；仅从连接表选择152/132不足以代替该入口 |
| 踏步斩专用入口 | `1417fed20`设置主段101；特定group1来源103/110/115走显式151，其他路径还会调用通用入口后再次判阶段 | 证明`+76aa`状态与动作phase消费者，接入151及分支状态；不能把131对所有来源无条件套用 |
| 混合门控与时钟 | `142255820`的request/MotionTree标志分别控制插值与尾淡出；`142253250`的overlap在启用时等待源帧超过endpoint-overlap；`1422564f0`按独立步长推进；虚表slot15调用点读取owner+6c | 查清各片段MotionTree/request启用位、曲线与owner+6c量纲，再在UE根运动/姿态求值前消费。UE5.8的`Montage_UpdateWeight`有合适接点，但仅凭MBD数值自动启用尾淡出会改变错误路径 |

曾在工作区接入自动尾淡出分支，继续追到启用门控后已撤除；最终源码没有启用猜测的尾权重模型。正式行为继续使用现有UE混合适配。不能将“所有主段终点已证明”扩大为“所有自定义入口、来源玩法和原生混合已实现”。

## 资产、重建与生命周期

没有新增/保存Content资产。B08的`/Game/MHWI/Data/DA_MHWI_LongSword`、`/Game/MHWI/Montages/M_SpiritComboThrustNative`、完整101及26个`/Game/MHWI/Animations/R06Staging/A_w03_00_###`沿用。为确定源码接入位置只读读取`/Game/MHWI/Blueprints/ABP_MHWI_Hunter`，实际父类为`MHWIAnimInstance`；旧二进制不能证明此次源码生效。

当前源提取/生成顺序为`extract_r06_completion.py` → `build_native_link_policy.py` → `build_link_runtime_data.py`。生成B09资料，不再覆盖B08历史输出。接口调用在游戏线程进行；来源Montage硬引用仅在绑定期间持有，失控/死亡/动作清理撤销绑定；原撤销令牌不能清除新绑定。node86保持无入边/0匹配记录。

## 本次未执行与回退

按用户要求，不运行编译、PIE、自动化、语法、文档或diff检查。上述脚本运行只提取原始资料并生成开发数据，没有运行游戏代码或测试断言。未来验收见[逐连接台账](../Plans/MHWI-Connector-Progress.md)与[通过准则](../Plans/MHWI-Connector-Acceptance.md)。

修改前字节与SHA256位于`Saved/MHWIRestoration/B09-20261025/Backup`和`before-files.json`。按B09修改清单逐文件恢复即可，不回退用户此前未提交内容；新增的B09文档、提取/台账脚本及证据文件可单独撤除。B08资产不需要回退。
