# MHWI 源采样修复、武器轨道与后续校准

更新：2026-10-24。现状入口为 [太刀模组](../Systems/MHWI-LongSword.md)，本轮结果为 [CHG-20261024-002](../Changes/CHG-20261024-002-mhwi-native-fidelity-implementation.md)。[此前调查](MHWI-Source-Fidelity-Audit.md) 保留当时历史结论。

本文以下描述CHG-002采样阶段的边界。后续已实施独立防御窗/逐路由窗口、连续交接和三色共享骨轨适配，见 [CHG-003](../Changes/CHG-20261024-003-mhwi-defense-routes-transfer.md)；用户随后改为[原始参数批处理](MHWI-Native-Parameter-Pipeline.md)，21处支持属性已直接从W03P生成。下文“尚未写入/保留旧库”等是该阶段当时状态，不代替当前系统页。

## 已实施的资源与时钟

项目转换器使用只读、固定指纹的 wowo MHW Anim Tools CPU 原生采样模块（MIT），不注册 Blender 插件、不修改源 LMT/源 blend/第三方代码。225 骨生产层级、绑定和旧 REF_POSE 根基底保留；平行 FBX 附临时 225 三角形绑定参考皮肤，UE 仅导入动画。逐整数帧及子帧矩阵、四元数、根轨迹和 FBX 重读分别校验，不以旧转换器输出作为正确性标准。

36 段合格动画导入 `/Game/MHWI/Animations/NativeFidelity/{LongSword,Common}/A_<源编号>`，正式 Montage 共替换27处段引用。Montage 名称、裁剪、播放倍率、通知和玩法数值保留。Common034/035/037 等仅是平行对照，基础 BlendSpace 和待机引用仍使用旧库；不得再次把攀爬034/035当走跑。309/310/311 含 NeedsParent 标志，缺失外部基姿态，仍用原正式动画，不能凭静止绑定补齐后宣称正确。根骨中间曲线可以因修复采样而区别于旧库；UE 验收直接对照源采样，旧库仅比较起止位移和兼容轴向。

当前 swo001 的 EVWP `mMotNo=0` 及其他型号对照支持 `wg03_00` 家族，7骨绑定与静态武器一致。六条内部 Sequence 在 `/Game/MHWI/Animations/Weapons/A_wg03_00_000..005`，共255帧。它们主要修改 `bone_002` 手柄区域，不提供整刀相对手掌的挂接变换；刀鞘无该骨，不能套同一轨道。

正式32招数据新增19个源武器事件，例：拔刀002第18帧→2，纳刀003第40帧→3，特殊纳刀306第73帧→3/第80帧→0，居合307..311第0帧→2/第8帧→1。时间统一换为当前 Montage 段秒；颜色变体的有效事件须一致才允许共用。事件用猎人进度触发，武器片段按真实 Actor 秒运行并保持尾姿，不将源秒误当倍率变化后的实际时间。保持/中断/死亡等契约见 [MHWI-006](../Interfaces.md#mhwi独立太刀与预伤害)。

特殊纳刀当前仍在73/60秒冻结；内部3可继续收完，**没有消费未来的第80帧事件**。低帧推进也限制在73帧，不能先触发80再倒回73。是否应推进到另一原作阶段尚无充分证据。整件武器手/背/左手换父骨仍为项目拟合方案，比例0.7未改；双手交接/全过程穿插并未全部解决。

EVWP 的位置/旋转字段为零，而当前 swo001 和 saya001 的 sheathed scale 原值也为零。模板“收纳缩放”标签不足以确定零的运行含义；未据此隐藏整刀和刀鞘。切勿把这些零值写成“已证明单位缩放”。

## 改用公开资料校准

用户拒绝原作进程采集后，后续采用公开资料及 UE 内可重复动作录像/采样。Peppo 的 [居合教程](https://www.youtube.com/watch?v=q92OLi711IA) 直接引用 Deathcream / MoonBunnie 的 [General Data Sheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5HFkHnEP74gD-SCVta9syb9GaF1_nSmMFgV4hxvZt9iu4HmfhGlP2KbnIbC-cAx5kkvsd8L7oB0Uy/pubhtml) 和 [Weapon Attack Tables](https://docs.google.com/spreadsheets/d/e/2PACX-1vTEYb4wGpijtIpFVopiYl1V83m48d7g1AHmTwOBKJ5RXdlz1sfxCyEmnhbgHLWQsGiXnodyBsUlPzc3/pubhtml)。研究者说明数据基于解包、代码和可行的实测；该资料不是 Capcom 官方完整动作状态机。

2026-10-24 已读取并缓存两个太刀页、Info 与教程说明，保存在 `Saved/MHWIImport/NativeFidelity-20261024/PublicCalibration/`。主要可用事实如下，**尚未作为新玩法数值写入**：

| 公开事实 | 当前用途/边界 |
| --- | --- |
| 60 FPS下居合斩无敌/反击5帧；居合气刃无色12/12帧，有色14/12帧 | 无敌窗与成功反击窗需独立；不能继续混成一个闭区间。原表有色无敌窗注明13.50补丁变化 |
| 见切正常反击33帧，无敌45帧起并随技能改变；槽不足10%时反击0帧 | 需要显式槽阈值与技能前提；不以动画碰撞窗口推导 |
| 特殊纳刀最长保持3.5秒；白/黄/红持续195/135/60秒 | 保持上限已有3.5；项目颜色仍300/180/60，未在本轮静默修改 |
| 居合/登龙回槽约6.67%每秒，持续时间随反击/颜色改变 | 项目回槽当前仍为简化值，应单独迁移并测试 |

上述数字来自 [太刀 General Data 页](https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5HFkHnEP74gD-SCVta9syb9GaF1_nSmMFgV4hxvZt9iu4HmfhGlP2KbnIbC-cAx5kkvsd8L7oB0Uy/pubhtml/sheet?headers=false&gid=82408715)。[太刀 Attack Table 页](https://docs.google.com/spreadsheets/d/e/2PACX-1vTEYb4wGpijtIpFVopiYl1V83m48d7g1AHmTwOBKJ5RXdlz1sfxCyEmnhbgHLWQsGiXnodyBsUlPzc3/pubhtml/sheet?headers=false&gid=362236353) 可核对动作值、槽消耗和反击备注。两表**不含每条连招的完整取消起止/连接片段起帧**；录像可约束节奏，不能把估测帧写成原始解码事实。

后续顺序：先分离无敌/反击窗并修正确定的资源规则，再逐招建立有出处的输入/派生窗口，最后按公开录像调取消混合与武器多视角接触。对缺乏数字的路线记录估测范围和视频时间点；优先玩家反馈的见切、气刃、袈裟、居合与登龙。

## 源语义复核的更正

旧 FreeHK 的 transition2 “QUAD” 标签不能证明应改为 t²。新检查的 [MHW-EFX-Editor v0.7.7 原作者求值代码](https://github.com/Dimcirui/MHW-EFX-Editor/blob/v0.7.7/efx_format/sim/resolve.py) 将0/1视为阶跃、2视为线性、3为Hermite、4为smoothstep；当前项目速度线性插值因此保留。该参考不是原作进程执行证明，也明确不适用于 BIG_FLAGS；输入 transition5/961个key仍未完整解码。不能把它扩展为所有输入位语义已知。

原生30个 LinkMotion 节点的32次引用仍未完整调度。已得到的两个阶段编号不说明何时切主段、从哪帧接入；不直接串接完整connector和完整main。当前取消窗口/0.3秒缓存、登龙物理和挂接仍是项目适配参数；完整原作还原继续列为未完成。

## B03后续状态

此前“基础BlendSpace仍使用旧库”属于CHG-002历史。现五段基础循环、DA六字段及两张BlendSpace六样本已迁移至合格平行库，见[CHG-009](../Changes/CHG-20261024-009-mhwi-locomotion-animation.md)。锁根、既有倍率/速度保留；未将旧攀爬034/035重新接入走跑。
