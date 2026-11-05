# 见切回砍前派生窗口取证（2026-10-30）

- 状态：精确原作窗口待取证；本项玩法未修改。
- 用户要求：必须先证实原作精确窗口，再修复回砍前特殊纳刀/气刃突刺。
- [本轮方案](../Plans/PLAN-20261030-001-mhwi-five-controls.md)
- [可复查证据](../../Tools/MHW/foresight-window-evidence-20261030.json)
- [提取脚本](../../Scripts/MHWI/extract_foresight_window_evidence.py)

## 已核实事实

直接重读固定指纹的原FSM和LMT：见切为node28 / Action86 / motion140；node28→45的条件108包含 `R+△`。特殊纳刀开始是node61 / Action98，共享来源node62 / Action1013通过条件232的 `居合斬り` 进入。原始FSM名称正常，旧timing-native-full报告中的乱码不能用来命名新接口。

140输入轨有25、40、47、70、90、110、160源帧的变化。`mFlag` bit14和`mFlag2` bit8在25–47有早期候选段；`mFlag` bit15及`mFlag2` bit9在40–47有早期候选段。这里的区间只按前键保持解释，不是已解码原生执行许可。

固定EXE的137命令映射表 `0x143eeabf0` 中，command24对应执行bit15/缓存bit14，command53对应执行bit73/缓存bit72。数值正好覆盖上述候选位，但没有证据允许把24/53直接命名成两种目标动作。

继续检查了 `R+△` 字符串 `0x1430b9864` 的消费者：名称解析器 `0x140b2e4e0` 在 `0x140b2ed81` 返回属性索引52。属性索引不是输入命令ID；不能用52、24或53之间的数值关联代替调用链证据。

## 官方机制与边界

Epic [UE 5.8 Animation Notifies](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine)说明Branching Point提供同步的玩法切换能力。该资料只支持UE实现机制，不证明MHWI窗口。当前项目已有取消路由系统；本轮不另选动画架构。

REA成功读取本机EXE并确认SHA；原生trace缺少配置好的分析provider（Ghidra/IDA等）。本轮继续使用已有固定指纹的Capstone静态提取工具；没有执行原游戏、注入、改安装文件或把原PE加密代码当解码证据。

## 剩余缺口与处置

还缺FSM属性 `R+△` / `居合斬り` 到具体输入命令的绑定，transition5位字段求值及缓存/执行生命周期，或原游戏逐帧观察。**不能以25、40、47候选帧修改正式见切派生。** 按用户要求保留问题开放；其余四项修复独立推进。

## 本轮验证

脚本直接校验原FSM/LMT/EXE/分析字节指纹并提取数据，实际运行结果见本页链接的JSON。该结果是离线静态取证，不是游戏运行或窗口验收通过。回退仅删除本轮独立报告和脚本；玩法及资产未变。
