# CHG-20261107-002：雌火龙Basic动画、碰撞盒与PIE完成

- 状态：completed（基础工程profile；原作忠实链不在本批验收范围）
- 日期：2026-11-07
- 需求摘要：更新交接后启动UE，完成基础动画、判定、玩家三档受击与死亡；纠正默认残血步态。
- 关联：[PLAN-002](../Plans/PLAN-20261107-002-rathian-basic-assets-pie.md)、[PLAN-001](../Plans/PLAN-20261107-001-rathian-basic-combat.md)、MHWI-016、R-AI-004、R-ANIM-012、R-ANIM-014。
- Git：工作区变更，未提交。

## 原因与结果

基础源码编译通过后仍无完整运行资源。此次建立独立Basic地图、两份DA、Pawn/GameMode及20动画副本，配置4招并完成24项真实PIE、101断言。用户明确采用玩家既有小/中/大三档，按招式区分轨迹；火球保留工程演出，原作片段后续再换。

实际预览及用户反馈指出00_065是残血步态，已换健康步行00_007；旧Walk副本保留但不引用。旧08_103落地末姿悬空，改用08_005下降/站稳两个片段。咬击和龙车恢复去除子根端点漂移，火球候选00_081去除XY退步；飞行高度由Actor独占。没有改写原片。

真实PIE还发现根球半径140cm切地扫掠不能水平移动，落地短射线够不到地面。独立冻结Luna任务补巡逻/接近速度与实际速度混合，再补完整2cm地面间隙和落地确认；均通过代码门、全新Luna审查、主审、核hash合入、原项目离线构建和重启后的PIE。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 原因与效果 |
| --- | --- | --- |
| Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxData.h | PatrolSpeedCmPerSecond / ApproachSpeedCmPerSecond | 0保持legacy回退；Basic对应健康Walk/Run实际根速度 |
| Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxPawn.cpp | 地面移动、速度混合、SnapToGround/KeepOnGround/落地确认 | 速度分段Idle/Walk/Run；统一2cm间隙，实际根高度达到完整目标后才离开Landing；死亡仍保持Dead |
| Scripts/MHWI/author_rathian_basic.py | 新副本创建、配置、场景和只读验证入口 | 全部142骨RAW采样，闭区间N+1键；检测副数据，拒绝覆盖既有动画目标 |
| Scripts/MHWI/pie_rathian_basic.py | 独立PIE、真实Hunter输入/受击、瞬态障碍夹具 | 异步结果报告；finally清理，真实game tick低帧证明；配置盒与有效窗口分开表述 |
| /Game/MHWI/Rathian/Basic/Animations/ | 20个新AnimSequence，14个活动、6个未引用候选 | 完整每片路径/源帧/模式/指纹见[配置清单](../../Tools/MHW/rathian-basic-profile-20261107.json) |
| /Game/MHWI/Rathian/Basic/Data/DA_RathianBasic_Stats | HP3000、巡逻333.21945、接近1248.35cm/s | 基础工程配置 |
| /Game/MHWI/Rathian/Basic/Data/DA_RathianBasic_Moveset | BITE / DASH_BITE2 / FIRE_BREATH / ROLLING_TAIL_ATTACK2_L | 按实际头/颌/身/尾骨及skin范围配盒、窗口、四招阶段与击飞 |
| /Game/MHWI/Rathian/Basic/Blueprints/BP_RathianBasic | 父类 /Script/IntroCpp.MHWIRathianApproxPawn | 正式绑定Stats/Moveset、网格/骨架、Body Yaw=-90和Z=-142 |
| /Game/MHWI/Rathian/Basic/Blueprints/BP_RathianBasicGameMode | 父类 /Script/Engine.GameModeBase | 默认 /Game/MHWI/Blueprints/BP_MHWI_Hunter 及现有MHWIHUD |
| /Game/MHWI/Rathian/Basic/Maps/L_RathianBasic | 专用平地、生产Pawn、PlayerStart | 不覆盖用户已有训练关卡；PIE后保留编辑器打开 |
| Tools/MHW/rathian-basic-profile-20261107.json | 配置、源码/资产/报告hash、24用例和保护摘要 | 将可复核的小结从被忽略Saved目录落入工具目录 |

前置基础13文件和Build.cs变更由[CHG-001](../Archive/MHWI/Changes/CHG-20261107-001-rathian-basic-combat.md)记录；本记录只对后续速度/落地修正及资产运行收尾负责。未改第三方插件。

## 官方机制、项目证据与推断

适用UE5.8：[Animation Sequence Editor](https://dev.epicgames.com/documentation/unreal-engine/animation-sequence-editor-in-unreal-engine?lang=en-US)、[Root Motion](https://dev.epicgames.com/documentation/unreal-engine/root-motion-in-unreal-engine?lang=en-US)、[AnimationBlueprintLibrary](https://dev.epicgames.com/documentation/unreal-engine/API/Editor/AnimationBlueprintLibrary/UAnimationBlueprintLibrary)、[SetActorLocation](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/GameFramework/AActor/SetActorLocation)、[UMovementComponent](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UMovementComponent)支持动画采样/副本处理、根位移与根组件扫掠；具体调用核本机5.8源码及反射。

项目实测：Armature带90°旋转，bone_root为子骨；仅看顶层Root Motion不能断言原位。142骨和848原片均已只读采样；Z140切地扫掠不动、Z142/145可动。完整2cm间隙是该工程场景修正，原位/飞行处理、攻击盒/窗/伤害/受击和火球选片属于工程适配，官方机制不证明MHWI原作语义。

## 接口、事件与资源影响

MHWI-016签名不变，Stats增加两个反射速度字段，默认0维持旧配置回退；本批关闭编辑器完整构建后再重启，不用Live Coding迁移。Configure仍一次性、不回血/复活；修改DA后新建实例。Basic蓝图实际父类和默认玩家通过注册表/场景读回核对。

本轮新增25资产文件，仅位于Basic。848原片及用户原先已改的 /Game/MHWI/Maps/L_MHWI_Training、/Game/MHWI/Data/DA_MHWI_LongSword 均未改写。暂时关闭后台节流仅内存值，结束已恢复true，未保存编辑器配置。

玩家受击配置及两种持刀状态实际motion：
- 小咬20：Small，纳刀70/拔刀61，前向300、上抛0。
- 火球30：Medium，71/62，550/260。
- 龙车35：Large，72/63，850/380。
- 尾翻40：Large，72/63，600/620。

力度单位cm/s，按面向转换后交现有CharacterMovement；实际水平速度受玩家既有动作影响。未改玩家三档动画库，也未新增第四档。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 冻结速度修复 | 原生Luna执行、独立新Luna只读审查、主审 | ACCEPTED；quality-1 191.599s；主项目构建65.21s，exit0 | Saved/DevFlow/Runs-20261107/RATHIAN-LOCOMOTION-20261107-5df46aac5e；Saved/RathianBasic-Assets-20261107/locomotion-main-build.json/.log |
| 冻结最终落地修复 | 同上，最终严格完整间隙合同 | ACCEPTED；quality-1 107.81s；主项目16.93s，exit0，UTC02:16:35结束 | RATHIAN-GROUND-FINAL-20261107-81c425c0ed；ground-final-main-build.json/.log |
| 骨架/原片采样及副数据预检 | 实际UE5.8编辑器，RAW无retarget | 142骨、848片每片9时刻；11源片曲线/通知/同步标记/骨属性均0 | Saved/RathianBasic-Assets-20261107/survey_*.json、source-auxiliary.json |
| 全部副本根轨与有限骨骼相对位置 | 实际UE读回 | 20片1915根键PASS；根最大误差0.000120cm，相对位置最大0.000801cm | authored-clips-verification.json |
| 资产及蓝图/场景读回 | Basic完整 /Game 路径 | 2DA、2BP、地图及引用/父类一致 | basic-data-readback.json、basic-scene-readback.json、basic-blueprint-registry.json |
| 正常循环、四招、躲空、墙体、低帧、起落/中断/死亡、玩家受击 | 最终主项目二进制上真实Basic PIE | 24用例、101断言全部PASS；低帧真实最大dt0.2000002s；8项玩家受击覆盖两种持刀姿态 | PIE-<case>.json；稳定清单列全部报告及hash |
| 保护与集成源码复核 | 本轮全部PIE后重新计算SHA256 | 875保护文件changed0/missing0；13份源码匹配顺序接受指纹 | protected-assets-final.json、3份integration.json |
| 文档/差异和脚本语法 | 本轮收尾 | 见本文末最终检查；不引用旧检查冒充 | python -B Scripts/Docs/check_docs.py；git diff --check |

历史失败如实保留：初次火球测试未冻结后续AI而超时；墙体夹具最初Static Mobility导致换网格失败；空中死亡夹具过早走通用结束分支。均修正测试脚本并在最终二进制上重跑对应用例通过，两个失败JSON单独保留。第一份Ground候选未接受/导出/合入，最终严格合同另开run；审查分歧和身份/输入传递例外留在原始证据，不把工作副本称OS隔离。

未执行：原作运行/解包、精确THK/COL复刻、多人/复杂地形、全部闪避/反击/霸体回归、长时间游玩及原作逐帧视觉对照。本轮有限观察不证明所有中断的每一帧观感。

## 风险、遗留与回退

R-ANIM-014：用户接受基础火球张口/退步候选和可见球体，后续定向查原作片段后替换；不继续取证作为本批前置。忠实线其他缺口保留，Basic修复不关闭首链R-ANIM-013等问题。

回退按ground-final→locomotion→basic逆序查integration.json及pre-integration备份，先核当前hash，恢复本批文件；移除本批新Basic包和两脚本/清单时先核引用。Build.cs只撤本批AnimGraphRuntime，不丢用户其他修改。不reset/clean全树，不覆盖既有脏资产；没有系统修复、重启或关机。

## 已同步文档

[当前交接](../Plans/MHWI-Rathian-Handoff.md)、[当前入口](../Plans/MHWI-Current.md)、[系统](../Systems/MHWI-Rathian.md)、[接口](../Interfaces.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[记录索引](README.md)及两份PLAN。

## 最终检查

- 两个新增Python脚本AST语法检查PASS（不导入unreal、不创建缓存）。
- python -B Scripts/Docs/check_docs.py：PASS，38 Markdown、367本地链接、16模块及editor snapshot JSON；只检查引用，不代替玩法验收。
- git diff --check：PASS，exit0；最终文档写入后再次运行。
- UE最终读回：L_RathianBasic、PIE=false、dirtyPackages=[]；后台节流恢复true。凭据 Saved/RathianBasic-Assets-20261107/editor-final-state.json。保持编辑器打开。

Luna补充只读一致性复核：原资产盘点会话重启审查，24报告及hash、101断言与最终构建时间一致；根模式、墙夹具清理和真实低帧采样缺口已补，无阻断发现。按其建议将cm指标改称骨骼相对位置误差，未比较角误差。凭据 final-independent-consistency-review.json；这不是新的冻结DevFlow门，也不冒称全新审查会话。