# MHWI 逐路由取消校准

更新：2026-10-24。状态：**校准数据与定向制作脚本已实现；正式资产保存及 PIE 结果以本轮变更记录为准。**

这套窗口是项目调校。原始 LMT 的输入轨道边界、碰撞段、FSM 出口和公开原作者资料约束调校；未知的 BIG_FLAGS 位并未获得逐输入含义，不声称下表为原作解码帧。目标主段起帧保持现状，连接片段仍未整段串入。

## 问题与实施边界

此前所有派生共用“最后伤害段结束后2帧”窗口，普通连击、见切、翻滚、袈裟、特殊纳刀会在同一时刻开放。袈裟被过早截断、居合气刃很早退出、翻滚后出刀偏晚，以及登龙着地不能接特殊纳刀，均与这个统一窗口有关。

新增 FMHWIRoute.CancelStart/CancelEnd，分别为负时沿用招式级窗口。项目制作脚本只复制并修改 Routes，不重建招式、Montage 或片段。既有 hit/counter/drawn 前提和路线顺序保留；左右袈裟仍需运行时根据移动和镜头选择。

## 实施矩阵

单位为60 FPS下当前源 Montage 帧，播放倍率前。`—`表示本轮无该显式路线；`禁用`为不可到达的9999秒窗口并抑制通用回退。普通栏按 Light / Thrust / Spirit / HelmBreaker 顺序，只有既有路线会填入。

| 招式 | 普通派生 | 见切 | 特殊纳刀 | 翻滚 | 袈裟 |
| --- | --- | --- | --- | --- | --- |
| StepSlash | LIGHT: 70–130；THRUST: 70–130；SPIRIT: 70–130；HELM_BREAKER: 70–130 | 68–130 | 70–130 | 70–130 | 70–130 |
| OverheadSlash | LIGHT: 65–130；THRUST: 65–130；SPIRIT: 70–130；HELM_BREAKER: 70–130 | 62–130 | 65–130 | 70–130 | 65–130 |
| Thrust | LIGHT: 38–128；THRUST: 38–128；SPIRIT: 38–128；HELM_BREAKER: 38–128 | 35–128 | 38–128 | 38–128 | 38–128 |
| RisingSlash | LIGHT: 42–100；THRUST: 42–100；SPIRIT: 42–100；HELM_BREAKER: 42–100 | 31–100 | 42–100 | 42–100 | 42–100 |
| SpiritI | LIGHT: 59–110；THRUST: 59–110；SPIRIT: 59–110 | 59–110 | 59–110 | 59–110 | 59–110 |
| SpiritII | LIGHT: 44–118；THRUST: 44–118；SPIRIT: 44–118 | 43–118 | 44–118 | 54–118 | 62–118 |
| SpiritIII | LIGHT: 110–160；SPIRIT: 110–160 | 97–160 | 97–160 | 110–160 | 110–160 |
| SpiritStepSlash | LIGHT: 64–114；SPIRIT: 58–114 | 46–114 | 58–114 | 64–114 | 64–114 |
| FadeSlash | LIGHT: 56–96；THRUST: 56–96；SPIRIT: 56–96；HELM_BREAKER: 56–96 | 56–96 | 56–96 | 76–96 | 76–96 |
| FadeSlashLeft | LIGHT: 50–86；THRUST: 50–86；SPIRIT: 50–86；HELM_BREAKER: 50–86 | 50–86 | 50–86 | 72–86 | 72–86 |
| FadeSlashRight | LIGHT: 50–88；THRUST: 50–88；SPIRIT: 50–88；HELM_BREAKER: 50–88 | 50–88 | 50–88 | 72–88 | 72–88 |
| ForesightSlash | LIGHT: 90–160；SPIRIT: 90–160 | 90–160 | 90–160 | 110–160 | 110–160 |
| SpiritThrust | — | 130–181 | 130–181 | 140–181 | 140–181 |
| IaiSlash | LIGHT: 60–130；THRUST: 60–130；SPIRIT: 50–130；HELM_BREAKER: 50–130 | 50–130 | 50–130 | 60–130 | 60–130 |
| DrawSlash | LIGHT: 70–130；THRUST: 70–130；SPIRIT: 70–130；HELM_BREAKER: 70–130 | 68–130 | 70–130 | 70–130 | 70–130 |
| SpiritComboThrust | LIGHT: 38–128；THRUST: 38–128；SPIRIT: 38–128 | 35–128 | 38–128 | 38–128 | 38–128 |
| SpiritComboRisingSlash | LIGHT: 42–100；THRUST: 42–100；SPIRIT: 42–100 | 31–100 | 42–100 | 42–100 | 42–100 |
| SpiritRoundslash | — | 禁用 | 50–100 | 50–128 | 禁用 |
| IaiSpiritSlash | SPIRIT: 70–174；HELM_BREAKER: 70–174 | 禁用 | 120–174 | 150–174 | 禁用 |
| SpecialSheathe | LIGHT: 65–269；SPIRIT: 65–269 | — | — | 65–269 | — |
| Roll | LIGHT: 35–78 | 禁用 | 禁用 | 42–78 | 禁用 |
| RollStepSlash | LIGHT: 49–129 | 49–129 | 49–129 | 49–129 | 49–129 |
| HelmLand | — | 91–112 | 17–80 | 91–144 | — |

## 依据与置信度

- 原素材：`wp03_action.fsm`、`w03_00.lmt`。源路径、SHA-256、每条输入轨道原始键值、碰撞帧、FSM 目标节点/条件编号保留在 [校准 JSON](../../Scripts/MHWI/transition_calibration.json)。`source_outgoing_links` 只证明有出口，不能把 ActionNo 当动画号，也不能从出口存在推出精确起帧。
- 原作者公开资料：[Peppo 居合教程](https://www.youtube.com/watch?v=q92OLi711IA) 及其引用的 [Deathcream / MoonBunnie 太刀页](https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5HFkHnEP74gD-SCVta9syb9GaF1_nSmMFgV4hxvZt9iu4HmfhGlP2KbnIbC-cAx5kkvsd8L7oB0Uy/pubhtml/sheet?headers=false&gid=82408715)。本轮使用已缓存的原作者说明和数据页；不声称逐帧测量在线视频。该表提供反击/无敌和资源参数，不提供下表所有取消帧。
- 精确事实：源输入轨道在哪一帧改变、碰撞在哪一段、FSM 有哪些出口，以及项目当前正式主段的长度。中等置信度：这些边界可约束动画进入恢复阶段的节奏。项目调校：选择哪个边界开放哪个具体输入、路线尾部截止，以及禁用旧通用出口。
- 例：后退袈裟输入轨道首次活动56帧，左右50帧；二阶段变化分别76/72帧。项目采用50/56帧开放攻击类派生，72/76帧开放翻滚。不能反过来把这项选择作为“已解码输入位”的证明。
- 居合气刃 mFlag2 在40/70帧变化，mFlag 在120/150变化，旧统一窗口39帧过早。项目分为Spirit/Helm70、特纳刀120、翻滚150；成功反击后的差异取消仍未单独标定。
- 气刃III保留三段伤害，不将25–50帧之间的候选中段取消扩成整段自由取消。回旋后仅保留特纳刀/翻滚；居合气刃禁止直接见切/袈裟；翻滚只开放恢复出刀与再次翻滚。禁用行为是本轮对旧通用回退的收敛，尚需用户实操评价。

## 制作与验收

1. 编译并重启编辑器以载入 FMHWIRoute.CancelStart/CancelEnd。
2. `python Scripts/MHWI/author_transition_calibration.py --validate` 只检验 JSON 结构与原始文件指纹，不写资产。
3. 编辑器 Python 导入 [author_transition_calibration.py](../../Scripts/MHWI/author_transition_calibration.py)，先 `run(save=False)` 查看全量前后矩阵，再由协调代理串行执行 `run(save=True)`。
4. 制作前按完整 `/Game/MHWI/Montages/M_...`、别名与长度核对。缺字段、PIE、陈旧长度、丢失既有路线或原文件指纹变化均终止，所有预检完成前不改正式 UObject。
5. 首次写入备份为 `Saved/MHWIImport/TransitionCalibration-20261024/Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset`；制作/读回报告为同目录 `author-transition-calibration.json`。备份已有则保留。
6. 运行验收应覆盖窗口前/内/后输入、0.3秒缓存过期、10 FPS跨窗、动态左右袈裟、气刃插入身份、翻滚持刀前提、见切命中+反击前提、登龙真实着地后派生，以及中断/死亡后过期缓存。数据制作脚本不自行启动PIE或宣布运行通过。

## 回退与未解决项

关闭编辑器后恢复上述 DataAsset 首次写入备份；恢复前比较保存报告的 SHA-256，保留其后用户手动调整。回退路线数据时可继续保留新增字段的默认-1兼容行为。

本轮不把当前 SourcePlayRates 当原作可执行时钟的完整解码，不新增连接片段、不猜主段入帧、不改登龙物理与伤害、不接触原游戏进程。精确原版逐路由帧、反击成功/失败的差异取消和连续动作姿态接触仍有缺口。
