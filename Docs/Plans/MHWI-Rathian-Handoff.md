# 雌火龙基础玩法交接

- 更新日期：2026-11-07（Asia/Shanghai）。
- 当前结果：Basic 基础版已完成源码、资产配置、碰撞盒校准及本轮24项PIE验收。它是使用em001素材的工程近似玩法，未接原作THK，不能升级为忠实还原。
- 用户已选定：玩家使用既有小/中/大三档受击，按招式区分力度与轨迹；基础版保留工程火球演出，后续再换原作片段。原作取证、Sandbox修复仍暂停。
- UE保持打开，当前地图 /Game/MHWI/Rathian/Basic/Maps/L_RathianBasic；PIE已结束，世界及内容包均无未保存修改。临时后台节流设置已恢复原值true，无系统重启或关机。

## 玩家受击最新修正

低帧下短受击曾被提前终止且首帧保留旧姿，出现状态/编号/速度有记录、画面却站姿的缺陷。已修MHWIAnimInstance.h/.cpp、MHWICharacterNativeSources.cpp：仅Impact消费首次owner delta、按实际源帧/真实Montage结束；其他默认保持。没有改三档源片、伤害/力度或Basic资产。

冻结run HUNTER-HITREACTION-20261107-20f5bf83e6，snapshot e5d5da74d4bbb18a10c16d43d87ca5095c48e22cf9e370db3c420a77932b2094；169.209s编译、全新Luna独立审查和主审接受，核hash合入，主项目97.74s构建通过后重启UE。

固定3FPS旧二进制最终骨姿FAIL、新二进制PASS（平均相对骨旋转误差约0.0044°；命中后实际水平105cm/上升72cm）。12受击场景、2次加强命中后位移断言重测及死亡/实际居合霸体2场景，共16次成功运行121断言；900资产hash未变，171源码仅3预期变化。连续输入未证明立即取消大受击，故未改输入门槛。

新脚本 Scripts/MHWI/pie_hunter_hit_reaction.py，先专用Basic PIE、需要时用prepare_drawn/drawn_ready完成真实拔刀，再run(move,stance,mode,fps,tag)，等status.done和报告passed；每例自行结束PIE。原始报告 Saved/RathianHitReaction-20261107/，稳定[修复清单](../../Tools/MHW/hunter-hit-reaction-repair-20261107.json)和[CHG-003](../Changes/CHG-20261107-003-hunter-hit-reaction.md)含失败夹具/测试版本/限界。截图为真实命中后暂停，临时隐藏怪物仅为检查玩家姿态，不代替连续验证。旧下文24项不补记成当时已核最终玩家骨姿。

## 运行入口

打开 /Game/MHWI/Rathian/Basic/Maps/L_RathianBasic 后点击Play。地图自带RathianBasic、PlayerStart及Hunter GameMode；玩家出生在雌火龙约50m外，可观察巡逻，再靠近触发发现/接近/选招。不要用旧训练地图直接summon未配置的原生ApproxPawn代替Basic蓝图。

| 资源 | 完整路径与实际父类/配置 |
| --- | --- |
| Pawn蓝图 | /Game/MHWI/Rathian/Basic/Blueprints/BP_RathianBasic；父类 /Script/IntroCpp.MHWIRathianApproxPawn |
| GameMode蓝图 | /Game/MHWI/Rathian/Basic/Blueprints/BP_RathianBasicGameMode；父类 /Script/Engine.GameModeBase，默认玩家为 /Game/MHWI/Blueprints/BP_MHWI_Hunter |
| Stats | /Game/MHWI/Rathian/Basic/Data/DA_RathianBasic_Stats；HP3000，巡逻333.21945cm/s，接近1248.35cm/s，发现4000cm，丢失5500cm |
| Moveset | /Game/MHWI/Rathian/Basic/Data/DA_RathianBasic_Moveset；4招均启用工程阶段配置 |
| 本体/骨架 | /Game/MHWI/Rathalos/Mesh/SK_EM001_Body 与同目录 SK_EM001_Body_Skeleton，142骨 |
| 坐标/地面 | 网格前向+Y，Body相对Yaw=-90、Z=-142；根球半径140cm，地面间隙2cm，平地运行根中心Z142 |

## 源码与执行边界

实际构建入口为 Source/。Approx目录共15个h/cpp，本轮基础实现修改其中13个；原有StateComponent两文件保留。新增AnimInstance和Fireball各h/cpp，Build.cs直接依赖AnimGraphRuntime，未改第三方插件。

Decision/Policy统一选择攻击、转向或移动；Pawn执行巡逻、发现/丢失目标、阶段Montage、骨骼有向盒及HP/死亡。Native图idle/walk/run混合后进入DefaultSlot；回调核run、phase epoch和Montage实例，自然结束推进，中断不误推进。骨盒跨帧裁窗、子步扫掠、阶段去重，并检查来源→盒→目标遮挡。火球一次生成/命中，来源死亡清理。

空中丢失目标、中断或受阻进入持续Landing，确认接地后恢复AI；空中死亡保持Dead并落地，死亡终止攻击且Configure不回血/复活。移动扫掠已修复切地停滞和落地射线长度问题；2cm是本关卡实测工程间隙。

MHWI-016提供ConfigureApprox、SetCombatTarget、RequestBasicAttack及状态/攻击/run/HP只读接口。Configure为一次性幂等初始化，更换DA后需新实例；null目标仍允许自动发现玩家0；Request返回true只证明启动，命中需另验。

## 动画配置与玩家受击

20份新动画副本中14份实际使用，6份早期候选保留但不引用。完整源路径、闭区间源帧、处理模式、活动标记见[基础配置与验收清单](../../Tools/MHW/rathian-basic-profile-20261107.json)。源动画不改，RateScale均为1。

| 用途 | 最终来源/处理 |
| --- | --- |
| Idle/普通步行/跑步/死亡 | 00_003 / 健康步行00_007 / 00_067 / 03_031 |
| 小咬 | 02_001全片，BiteSmooth消除XY端点漂移 |
| 龙车 | 00_003前摇、00_067冲刺、02_001后段恢复；ChargeRecoverySmooth消除漂移 |
| 单火球 | 00_081分为SpitWindup/SpitRelease，消除XY退步；来源仍是张口/退步候选，按用户选择保留工程演出，非已证原作站地单火球 |
| 尾翻起飞/空中动作 | 08_002分段，Actor负责高度，副本去除子根XYZ位移，保留其他骨轨 |
| 落地/站稳恢复 | 08_005分为LandingDescend/Recovery；替换末姿悬空的旧08_103候选 |

旧Walk来自残血步态00_065，已从Moveset撤下，当前只用WalkHealthy（00_007），不能重新绑回旧Walk。顶层Armature含90°旋转且bone_root是子骨，顶层Root Motion为0不足以证明原位；地面副本保留Z，飞行高度明确由Actor负责。

| 招式 | 伤害 | 玩家受击 | 配置击飞速度：前向/上抛 cm/s |
| --- | --- | --- | --- |
| 小咬 | 20 | Small | 300 / 0 |
| 单火球 | 30 | Medium | 550 / 260 |
| 龙车 | 35 | Large | 850 / 380 |
| 尾翻 | 40 | Large | 600 / 620 |

两种持刀状态均实测：纳刀Small/Medium/Large使用motion70/71/72，拔刀使用61/62/63。龙车和尾翻共用Large起手，尾翻上抛更高；真实水平速度受现有玩家运动系统影响，不等于配置向量原值。以上伤害、盒体、窗口、力度和高度均为工程值。

## 编译、审查与真实PIE

| 冻结Luna任务 | 代码门及主项目构建 | 接受快照 |
| --- | --- | --- |
| RATHIAN-BASIC-20261107-e9f989d679 | quality-3 UHT/C++/链接113.88s PASS；独立新Luna approve、主审approve、ACCEPTED；主项目201.82s PASS | e7a2ee3a5df6716f40140a332bc9aa392d3c9de004c937f84dae8a825b6d0676 |
| RATHIAN-LOCOMOTION-20261107-5df46aac5e | quality-1 191.599s PASS；独立新Luna/主审接受；主项目65.21s PASS | f131774b61dac92e74a89c847033b82c74de6a988db4bcd9422dabff6c1ff5f2 |
| RATHIAN-GROUND-FINAL-20261107-81c425c0ed | quality-1 107.81s PASS；独立新Luna/主审接受；主项目16.93s PASS，UTC02:16:35结束后重启编辑器再测 | dfb766fd5bb638003ba60d0b79b1d933dc108f08920f9a67fa4017b81bcc41bf |

先前RATHIAN-GROUND未接受、未导出、未合入；审查间隙冲突和失败记录保留，不改旧控制。原生代理prompt和工作副本不构成OS/ACL隔离，usage/cost不可见。三次接受仅是各自代码门；下列为最终主项目二进制上的实际PIE。

| 实际检查 | 结果 |
| --- | --- |
| 巡逻→自动发现→接近→策略选招 | PASS，实测均速333.21945cm/s、接近最高1248.35003cm/s，平地根Z142 |
| 四招命中、近战去重及小咬躲空 | PASS，伤害20/35/30/40，单火球一次生成 |
| 小咬/火球墙后不伤害，龙车受墙阻挡 | PASS，真实BlockAll立方体夹具 |
| 低帧跨窗 | PASS，实际最大game tick 0.2000002s，小咬一次20伤害 |
| 尾翻正常落地、丢失目标、中断、顶棚受阻、空中死亡 | PASS，正常峰值Z977.6，顶棚阻挡峰值Z308.16，均回Z142；死亡保持Dead |
| 地面死亡/重复配置/死亡拒绝出招 | PASS，非循环死亡末姿hip Z11.1622稳定保持 |
| 施术者死亡清理已发出的火球 | PASS，spawned1/live0，后续不伤害 |
| 4招×纳刀/拔刀的玩家三档受击及轨迹 | 8项PASS，动作身份及上抛速度均实际采样 |

合计24用例、101断言通过。20副本1915个根键与对应原片处理公式核对通过，最大根误差0.000120cm；有限头/髋/足/尾相对位置最大误差0.000801cm。11个唯一源片的曲线/通知/同步标记/骨属性均为0，裁片脚本对此预检，不能把未来未知副数据默认为空。

证据目录 Saved/RathianBasic-Assets-20261107/：
- PIE-<case>.json：实际状态、骨姿、HP、玩家动作/速度、碰撞夹具及断言；异步脚本启动成功不代替报告passed。
- authored-clips*.json、source-auxiliary.json、basic-data-readback.json、basic-scene-readback.json、basic-blueprint-registry.json：配置及读回。
- locomotion/ground-final-integration.json、各main-build.json/.log：核hash合入和实际构建；基础批证据在 Saved/RathianBasic-20261107/。
- protected-assets-final.json：875文件changed0/missing0，含848原动画、模型材质及用户已改的训练地图/太刀DA；当前13份集成源码与顺序接受指纹一致。
- 稳定汇总已落 Tools/MHW/rathian-basic-profile-20261107.json；Saved原始报告受gitignore影响，交接时需一起保留。

## 复现、遗留与回退

资产脚本 Scripts/MHWI/author_rathian_basic.py：verify_data、verify_authored_clips、source_auxiliary_report、blueprint_registry_report可读回。author_clips只允许新目标，已存在会拒绝；不要为验证重跑整套创建或覆盖现有Basic包。

运行脚本 Scripts/MHWI/pie_rathian_basic.py：先启动专用Basic PIE，再run_behavior或run_case，每例独立世界并等case_status完成；拔刀样例先prepare_drawn，经真实输入等drawn_ready后再请求攻击。测试finally恢复CVar、移除回调并结束PIE；configured_boxes表示配置盒，不能当作每帧有效攻击窗。

本轮已满足基础版范围。后续可替换工程火球动画/球体表现；精确THK、LR动作资格、原作COL、完整伤害/怒态/部位/VFX仍按[取证总账](../Reference/MHWI-Rathian-Evidence.md)等待恢复取证。未做多人、复杂地形NavMesh路线规划、全部闪避/反击/霸体回归、长期游玩或原作逐帧视觉对照，不将有限PIE推为全覆盖。

回退仅针对本批：先按Saved/RathianHitReaction-20261107/integration.json核hash恢复3份玩家源码；旧Basic按ground-final→locomotion→basic的integration.json逆序核当前hash并恢复各pre-integration备份；新Basic资源可单独撤下；Build.cs只移除本批AnimGraphRuntime依赖且保留用户其他修改。不得reset/clean用户工作树或保存覆盖原训练地图/太刀DA。详见[本轮记录](../Changes/CHG-20261107-002-rathian-basic-assets-pie.md)。
