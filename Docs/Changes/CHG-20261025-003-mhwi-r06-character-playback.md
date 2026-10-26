# B08：R06角色播放接入、原生112主段与时钟隔离

- 状态：partial（角色接入及两项正式迁移已实施；完整原版前置玩法和混合仍有缺口；未编译/测试）
- 日期：2026-10-25
- 需求：自主完成R06可确认的选择、退出、主段入帧；不猜参数、不测试，逐条同步台账。
- 关联：[实施方案](../Plans/PLAN-20261025-003-mhwi-r06-character-playback.md)、R-COMBAT-014、R-ANIM-008、MHWI-001。
- Git：工作区变更，未提交；保留已有大量无关修改。

## 原因与结果

B07只有未被角色调用的控制核心与26段平行库。本批新增`MHWICharacterLinkMotion.cpp`并接入StartResolvedMove、Tick、MontageEnded、FinishMove和输入/受击路径。实际来源片段/源帧在清理旧执行前采样；连接阶段独立播放并隔离主招事件；结束后一次性按MBD入帧提交主段，费用不重扣。CDO硬引用26个连接资源，新增反射字段尚未编译。

原生注册表证明插入突刺ID71/cKijinStab的主段是112。它与105明确共享原LMT物理曲线表，但TIML独立；已制作/导入112，新增正式Montage并迁移SpiritComboThrust。上挑Action80采用自定义119→107入口，已单独实施。B07遗漏的MBD第0行回退、TIML transition1整数键复制、前向结束的预测flags均已补入。

原生类型调查同时否定了两个临时适配：Draw(002)不能当node43/CreepSingleMotion；纳刀Roll不能当node27/Step系列。未保留这些猜测映射。原生KijinComboShot、Step与Creep前置玩法仍未实现，逐连接状态明确记录这些缺口；没有借用现有招式凑覆盖。

## 修改清单

| 文件/资产路径 | 符号或属性 | 效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp`、`MHWICharacterLinkMotion.cpp` | Prepare/Begin/Advance/CommitNativeMain；NativeLinkExecution、NativeTimelineMotion及硬引用 | 角色消费连接核心；连接期间不推进主招；中断/旧回调失效；311独立时间线 |
| `Source/IntroCpp/MHWI/MHWILinkAnimation.h/.cpp`、`MHWILinkRuntimeData.inl` | 原生身份等价匹配、源段坐标、Step Phase、ForwardEndFlags | 只使用提取数据；真实bank/片段/帧参与选择；不同别名结果拒绝接入 |
| `Source/IntroCpp/MHWI/MHWINativeLinkMotion.h/.cpp`、`MHWINativeLinkMotionData.inl` | MBD原始第0行回退、BeginExplicitConnector | 纠正默认行遗漏，支持已证明的上挑自定义入口 |
| `Scripts/MHWI/build_link_runtime_data.py`、`extract_link_runtime_evidence.py`、`build_native_link_policy.py` | 数据/指令提取 | 原生动作表、112绑定、Phase/退出证据；B08输出独立保存，不覆盖B07历史 |
| `Scripts/MHWI/native_animation_source.py`、`export_r06_staging.py`、`export_r06_main.py`、`import_r06_staging.py` | shared_curve_owner；独立制作参数 | 只对同物理曲线表及同姿态头的明确所有者放行，不为其他NeedsParent片段猜基姿态 |
| `Scripts/MHWI/author_r06_runtime.py`、`Tools/MHW/r06-runtime-adapter.json` | 两项正式迁移及日志 | RollStepSlash去掉固定129；SpiritComboThrust使用112 |
| `Scripts/MHWI/author_assets.py`、`author_behavior_corrections.py` | 历史大批次重建保护 | 避免再次恢复旧复合前缀和105插入突刺绑定；定向入口继续保留 |
| `/Game/MHWI/Animations/R06Staging/A_w03_00_112` | AnimSequence | 新导入原生共享骨轨112；并未覆盖105或旧NativeFidelity资源 |
| `/Game/MHWI/Montages/M_SpiritComboThrustNative` | 单段来源112 | 新正式插入突刺Montage，保留既有量值及窗口 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | SpiritComboThrust.Montage、RollStepSlash定义 | 插入突刺换112；翻滚踏步斩完整101主段、时间坐标转换；其余30招定义未改 |
| `Tools/MHW/native-main-motion-bindings.json`、`native-link-motion-policy.json` | 原生证据与当前策略 | 112/107入口证明、共享曲线所有者、32引用与124记录 |
| `Scripts/MHWI/record_r06_runtime_progress.py`及逐连接MD/CSV | 32条实现状态和通过准则 | 不将源表、源码接入、前置玩法缺失、不可达和运行通过混写 |

## 接口、事件与资源影响

未改公开Blueprint函数签名；AMHWICharacter新增私有反射资源引用和运行状态，必须在下一阶段编译/重载。新C++文件由Source模块正常编译入口发现，不改参考副本或第三方插件。角色的主动作身份和费用仍只提交一次；连接阶段禁止主招命中、取消、防御窗提前生效，主段跳入时不从0补播已跳过事件。动作输入/取消窗仍保留现有项目适配，不冒称R07已还原。

RollStepSlash坐标换算使用迁移前真实段StartPos、AnimStartTime、AnimPlayRate及Sequence RateScale，记录于日志。原M_RollStepSlash复合资产不删除、不覆盖；正式定义改引完整101。原生插值帧数用于UE边界，保留原UE曲线；未把原生overlap字段解释成旧Montage停播时长。完全等价的原生混合和根运动权重仍需继续取证。

## 实际制作与调查（不是测试）

| 操作 | 实际结果 | 证据 |
| --- | --- | --- |
| 原FSM/LMT/MBD、固定EXE分析区读取与表生成 | 32引用/124记录；主段112入口、Phase整数键及第0行回退已取得指令证据 | `Saved/MHWIRestoration/B08-20261025/runtime-native-functions.json`、`runtime-source-data.json` |
| 读取正式DA及相关Montage段作为开发输入 | 发现三色居合均复用308骨轨；原RollStepSlash为129+裁剪101；原插入突刺引用105 | 角色接入前MCP Python读取输出；未做读回验收 |
| 无测试导出112 | 首次受NeedsParent保护阻止；取得原文件同曲线表所有者105后另目录成功导出1段 | `R06Main-20261025/export-manifest.json`、`R06MainShared-20261025/export-manifest.json` |
| 导入112及保存两项正式迁移 | 新AnimSequence、新Montage和DA保存成功；未读回/运行 | `native-main-import.json`、`roll-main-migration.json`、`native-thrust-migration.json`（B08目录） |

**按用户要求，没有执行编译、测试、PIE、姿态比较、FBX回导、文档检查或git diff检查。** 资产制作日志不是验收通过证据；旧测试没有记作本次测试。

## 遗留、下一阶段与回退

完整边界和逐项通过准则见[B08现状](../Reference/MHWI-R06-Character-Playback.md)、[逐连接台账](../Plans/MHWI-Connector-Progress.md)和[验收页](../Plans/MHWI-Connector-Acceptance.md)。先编译反射与源码；再验证真实消费、源帧预测/尾帧、112主段、311 Phase、129去重、左右映射和中断。原生Step、Creep、KijinComboShot前置玩法没有因连接表就绪而实现，必须先接真实身份再验收这些行。混合曲线/overlap与UE权重仍不等价确认，R06完整还原不能关闭。

整批资产回退：恢复`Saved/MHWIRestoration/B08-20261025/Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset`；仅回退112绑定可使用`Backup-Thrust`中的中间DA。新增112/Montage可保留为不引用的平行资产。回退角色新增调用/成员及本批独立C++文件，并撤销MBD第0行/显式入口改动；不要重置整个工作区。去除`Tools/MHW/r06-runtime-adapter.json`前应先恢复与历史制作入口兼容的定义，否则旧脚本会重建旧前缀。原游戏安装、源blend、源LMT/MBD均未写入。

## 已同步文档

[系统现状](../Systems/MHWI-LongSword.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[逐项开发台账](../Plans/MHWI-Restoration-Progress.md)、逐连接MD/CSV、验收页及文档/计划/变更索引。B07现状页添加B08后继说明，历史CHG保留原含义。
