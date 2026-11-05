# CHG-20261024-011：B05左右FSM来源修正与原生连接逻辑取证

- 状态：partial（来源修正已实施、待测试；退出/Phase1仍取证中）
- 日期：2026-10-24
- 需求：继续R06，确认退出/Phase1及361/362；用户最新要求不测试，提供通过准则。
- 关联：[PLAN-009](../Plans/PLAN-20261024-009-mhwi-native-connector-logic.md)、R06/R32/R33；工作区变更，未提交。

## 已实施：左右节点来源修正

B04发现的361/362冲突来自项目来源绑定写反，不能用交换正式动画来处理。原FSM node8名称“左移動斬り”，输入←、Action82；node9为“右移動斬り”，输入→、Action83。原MBD362→128@24、361→127@22，与正式左128/右127一致。

现将`moveset_mapping.json`左袈裟节点/Action改为8/82，右改9/83；同步`author_behavior_corrections._apply_fade_direction_timing`和源映射生成定义。片段、碰撞、窗口、播放速度、输入方向、DA、Montage未安排写入。固定来源清单只更新已修改映射的指纹，原MBD/FSM/LMT指纹不变。修正后静态来源关联32次均一致；**未进行本轮测试**。

## 原生退出/Phase1取证成果与边界

本机原EXE的受保护代码区已只读解码为本地非可执行分析字节，未重建EXE，未写游戏目录，未启动游戏或采集进程。布局/解码流程参考固定提交的[Steamless主作者实现](https://github.com/atom0s/Steamless/blob/cd770bf9749d3e4f438d23ac643917ad1a804257/Steamless.Unpacker.Variant31.x64/Main.cs)及其头布局/AES辅助代码，原文件缓存与归属/许可证保留在本批Saved/Public。它们没有接入项目运行时，不修改第三方工具。

本机源EXE SHA与此前记录一致。`nPlFSM::LinkMotion_W03`字符串本机VA为0x1430b84e0，注册引用0x1400a31a1、函数0x1400a3190；参数构造/DTI引用0x140b200c0、0x144f1a188。`mLinkMotionPhase`本机字符串0x1433c6708、反射引用0x141920387。这些是**构造/注册/反射位置，不是完成谓词或Phase1选择实现**，不能拿它们直接驱动UE。没有把旧2023公开DTI的地址直接套到本机。叶函数缺乏pdata边界时的256字节候选扫描可能越过函数；不据此下消费者结论。

原TIML全局Phase轨道共8条，位于2/4/5/61/62/311/355/356。node60前置node26为段登(拔刀)、Action1003，当前项目映射未覆盖其原生片段；node76前置node65居合气刃，311第0源帧显式LinkMotionPhase=1。308/309/310无该轨不能证明默认0；共享308身体骨轨不能吞掉311独立TIML。**尚未证明初值、重置、采样、提交、缺失后备，以及与MotionNo_Phase1的具体数据流**。

连接段完成谓词仍未解析；新增连接播放0条。原129的29/60退出仍为项目适配，不把源动画长度、空条件或MBD重叠字段冒充原生退出。

## 修改清单

| 文件/符号 | 实施状态 |
| --- | --- |
| [moveset_mapping.json](../../Scripts/MHWI/moveset_mapping.json) | 左node8/82、右node9/83来源已修，待测试；其余动作语义保持 |
| [author_behavior_corrections.py](../../Scripts/MHWI/author_behavior_corrections.py) | 定向来源预检/制作常量同步，待测试 |
| [extract_moveset_mapping.py](../../Scripts/MHWI/extract_moveset_mapping.py) | 重新生成不回退错误节点；保留历史位移证据说明，待测试 |
| [native-connector-sources.json](../../Tools/MHW/native-connector-sources.json) | 当前映射指纹更新；原游戏数据固定指纹保持 |
| [native_connector_logic.py](../../Scripts/MHWI/native_connector_logic.py) | 新增只读取证汇总；区分前置TIML、身体共享和连接段，未知规则仍null；已生成证据，不是测试执行 |
| [逐连接台账](../Plans/MHWI-Connector-Progress.md)及CSV | 32条分别更新状态和下一阶段通过准则；80/81来源修复待测 |

无C++/反射接口改变，无UE资产保存；未执行全量重建。旧B04报告保留原始历史，新的汇总输出写B05。B04验证脚本中的固定“两冲突”预期已经过时，下一阶段须先迁移预期/输出目录，不能复用旧结果作为当前通过。

## 本轮取证与测试状态

`Saved/MHWIRestoration/B05-20261024/`：

- `source-logic-evidence.json`：当前32引用、两个可选阶段节点、全部前置阶段轨道；`tests_executed=false`。
- `native-analysis-qualification.json`、`native-provenance.json`、`native-xrefs.json`、`parameter-xrefs.json`及`asm-*.json`：原EXE/分析字节指纹、只读解码取证和候选汇编。用户追加禁测前已有静态解码往返记录；它不是动画/玩法测试结果。
- `analysis-text.bin`：本地非可执行代码区，保留在Saved，不用于分发或部署。
- `before-files.json`、`asset-baseline.json`、`Backup/`：改动前文件/349资产基线；本轮未执行改后资产比较，不能声称“本轮349哈希检查通过”。
- `implementation-status.json`：当前实施和后置验证状态。

**按用户最新指令，测试、语法检查、编译、PIE、文档检查、diff检查均未执行，全部留下一阶段。** 来源读取、静态反汇编、生成证据和编辑文档属于开发取证，不计为测试通过。

## 下一阶段测试通过准则

逐项详见[验收要求](../Plans/MHWI-Connector-Acceptance.md)，逐连接见台账末列。关键门槛：来源四方一致、正式左右128/127及其他资产保持；重建不回退；原代码区/类型/数据流可复现；node60/76分别证明选择/初值/重置/后备；退出谓词与时钟先明确再启用；启用后才做短PIE检查入口、位移和事件时钟。

未取得原生退出或Phase1规则时，不得将连接标为完整已还原。

## 回退与同步

恢复本批Backup中的三个映射/制作文件及来源清单，移除新增汇总入口；没有安排Content资产写入，不用覆盖资产目录。保留本CHG历史，后续实现另建记录。

已同步[总台账](../Plans/MHWI-Restoration-Progress.md)及CSV、[连接台账](../Plans/MHWI-Connector-Progress.md)及CSV、[系统页](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)、[开发流程](../Development.md)、[模块索引](../Reference/modules.json)及文档/计划/变更索引。状态均区分实施、取证和待测试。
