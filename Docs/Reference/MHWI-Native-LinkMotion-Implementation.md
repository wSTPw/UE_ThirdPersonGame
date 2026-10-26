# R06 B07：原生连接选择、退出与入帧实施现状

> B07历史实施快照。当前角色消费、112主段、MBD第0行回退和源类型修正见[B08现状](MHWI-R06-Character-Playback.md)；下文“角色未接入”等描述仅对B07成立。

更新：2026-10-25。**部分实施，未测试；正式角色新增连接调度0条。** 原生控制核心和数据已写入源码，26个独立片段已导出、导入平行动画库；`AMHWICharacter`尚未调用新核心，不能将本页理解为完整还原完成。

## 直接来源与执行链

固定原EXE SHA256 `c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea`；本地非可执行分析区SHA256 `9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe`。未运行游戏、注入进程或修改原安装。指令和明确叶函数范围保存在[消费者证据](../../Tools/MHW/native-link-motion-consumer-evidence.json)，不是运行验证结果。

| 原生链条 | 已确认行为 | C++落点 / 边界 |
| --- | --- | --- |
| 玩家资源加载`14118a0c0` → `14118d560` | 把LinkMotion扁平化到目标动作连接表；从连接首个出口取得目标ActionSet。ActionNo经过武器/通用表映射，源动作展开所有身份；目标取映射首个身份。普通回退身份为group3/ActionNo | 生成器读取本机表，生成124条有序匹配记录；FSM节点只用于诊断，禁止直接拿1001等ActionNo当原生动作ID |
| `14118da05..a33` / `14118dab8..ae6` → `141781190` | 分别写MotionNo、MotionNo_Phase1，负数省略；目标表每项16字节：前置group/id、片段、phase | `FindLink`精确比较目标、前置group/id和Phase；首次命中；没有P1→P0后备。武器默认源集合的额外group1/P0广播记录也保留 |
| 动作开始`141784090` / `1417845e0` | 读取玩家前置身份`+628c/+6290`和PlMotionCommon`+10c`，命中播放`c000 | (clip & 1ff)`、动作phase写0；不命中直接主段 | `FLinkExecution::Begin`只负责控制请求，不推测UE混合时间或动作费用 |
| 动作更新`141787000` / `141787950` | phase0等待玩家virtual+2b0；为真才调用`1417896e0`提交主段 | `Advance`接受真实动画层结束事实；同一代次仅提交一次。`Cancel`使旧回调代次失效。不是固定秒数或通用FSM倒计时 |
| uPlayer virtual+2b0 → `141bfd260` → `1423b8bf0` | 原生动画层flags & 5；玩家可选附加结束路径受`+6f2b`控制 | `IsMotionEnded`保留flags1/4及可选附加条件。UE适配端尚未把Montage生命周期映射成这一事实，不能拿UE默认BlendOut当原生谓词 |
| `141fbc8d0`绑定common对象 → `142248894` → `1424a7e50` → `1424a7f50` → `1424a7cf0` | 动画TIML重绑定在求值新轨道前遍历参数对象virtual+28；PlMotionCommon slot5 `141921cb0`在`141921d99`清`+10c` | **已确认这条重绑定路径缺轨时归零**。不是仅凭构造函数推定每次动作都重建。核心接收实际采样Phase，不另造TIML整数插值器 |
| `141c007f0` → `141c00930..9fa` → `141c014f0` | 按目标、前片段、来源bank、可选前片段帧上限匹配MBD；runtime row+28 → request+18为startFrame；按原顺序匹配 | `FindBlend`与317个原匹配块。未命中保留“无MBD覆盖”，不补0帧/默认倍率；其他插值/重叠原值原样保留，尚未证明等价UE秒数 |

本批排除了继续追通用cAIFSM drive +30作为这条太刀连接退出依据的必要性；B06通用门控发现仍有历史含义，但不是上述玩家执行链。不得把控制对象的phase0/1和TIML的mLinkMotionPhase混为同一变量。

## 数据、代码与资产落点

- [原生表生成器](../../Scripts/MHWI/build_native_link_policy.py)直接读取固定版本原EXE的数据区及原FSM/LMT/MBD；无测试入口、无游戏代码执行。输出[完整策略数据](../../Tools/MHW/native-link-motion-policy.json)和[编译期表](../../Source/IntroCpp/MHWI/MHWINativeLinkMotionData.inl)。30节点、32引用、124条身份匹配记录；node86无入边，不虚构记录。
- [控制接口](../../Source/IntroCpp/MHWI/MHWINativeLinkMotion.h)、[实现](../../Source/IntroCpp/MHWI/MHWINativeLinkMotion.cpp)：全部使用原生帧/原生身份；不反射新字段、不改现有蓝图接口、DataAsset或正式Montage。主动画ID由实际动作调用者提供，避免把项目105/112映射当原生构造证明。
- [无测试导出入口](../../Scripts/MHWI/export_r06_staging.py)：原生采样到`ArtSource/ThirdParty/MHWLongSword/R06Staging-20261025/`，26个FBX，NeedsParent阻止0个。没有导入验证模块、姿态比较或FBX回导测试。原NativeFidelity清单不变。
- [独立导入入口](../../Scripts/MHWI/import_r06_staging.py)：26个`/Game/MHWI/Animations/R06Staging/A_w03_00_###`，实际类AnimSequence，使用`/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton`；RootMotion启用、RootLock REF_POSE、ForceRootLock false。结果来自制作调用日志，不是读回验收。没有覆盖已有包或保存正式动作数据。
- 制作证据：`ArtSource/ThirdParty/MHWLongSword/R06Staging-20261025/export-manifest.json`及`Saved/MHWIRestoration/B07-20261025/r06-import-journal.json`。C++尚未编译，动画尚未做源采样/导入/运行验证。

## 各条适用规则及剩余实施

全部32行见[逐连接台账](../Plans/MHWI-Connector-Progress.md)。361为右袈裟127@22、362为左袈裟128@24，沿用B05来源修复；本轮导入并不改变左右正式资产。node76的308/309/310缺轨和311显式1已经有绑定重置依据，分别应选择357/P0和367/P1；骨轨复用不能吞掉311独立TIML。node60前置Action1003已展开12个原生身份，仍须取得每个身份实际播放的片段/帧时钟。

必须继续的开发工作（不是要求先测试）：

1. 从原生动作注册/构造端取得实际主片段，优先node23的105/112双候选；不能只凭项目映射关闭。已保存`weapon-action-record-function.json`、`weapon-action-table-initializer.json`和常量传播候选；它们还不是类型正确的主片段证明。
2. 实现`AMHWICharacter`播放适配，传入实际原生动作身份和采样Phase，调用本批控制核心；以原生连接/主段各自源帧统一根运动、独立武器、命中和取消事件。尚未接入，不能称“已实现但仅差测试”。
3. 查清MBD插值/重叠字段的下游消费者再写UE混合规则；连接本身的MBD起帧也须按前一真实motion匹配，不能全部强行从0开始。129既有复合Montage必须避免再套连接前缀；主段入帧不重扣费用、不补播跳过的命中窗口。
4. 完成上述开发后再进入用户指定的下一阶段验证。node86原图不可达，保留结构而不制造操作入口。

## 下一阶段通过准则

复核固定来源/叶边界、124记录的加载顺序和别名展开；逐条覆盖准确前置身份/Phase、P1缺项直入主段、负片段省略、第一次结束只提交一次、中断/旧代次不提交、原MBD目标/前片段/bank/帧阈值和入帧。每条还需证明实际角色消费路径、根位移连续、武器及命中/取消时钟一致。导出/导入成功、源文件存在、C++代码存在均不能单独判通过。详见[验收页](../Plans/MHWI-Connector-Acceptance.md)。
