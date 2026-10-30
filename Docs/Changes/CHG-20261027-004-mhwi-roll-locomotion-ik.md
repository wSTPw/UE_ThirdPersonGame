# CHG-20261027-004：翻滚阻断修复、六段移动过渡与四链IK实装

- 状态：partial（本批项目消费者已实施并运行，完整原生还原边界保留）
- 日期：2026-10-27
- 需求摘要：继续定位并修复翻滚入口阻断，完成R06/R28/R30可明确实施的剩余开发与实际调试；来源未明确不猜配。
- 关联：[PLAN-20261027-001](../Plans/PLAN-20261027-001-mhwi-remaining-animation-development.md)、R06/R28/R30、MHWI-015、R-ANIM-007/008、R-COMBAT-012/014/016。
- Git：工作区变更，未提交。开始时已存在的CHG-003专项验收及相关现状页修改已保留。

## 原因与结果

真实翻滚动态Montage在`DuplicateObject`到角色后时长归零，导致播放拒绝。改为引擎动态Montage工厂重建受支持模板，不手填时长。另修复014/015过渡接管后旧翻滚缓存优先的问题，新增只读来源诊断验证实际Action65/66。

六段005/006/007/008/014/015完成原生消费者取证、合格导出、NativeFidelity导入与实际ABP过渡。014/015是翻滚到移动/转向，纠正旧落地候选描述。四链Profile及四个TwoBoneIK已保存，采用end/mid骨骼相对偏移避免反馈漂移，实际肘骨及脚部地形响应通过。详见[B20实施与边界报告](../Reference/MHWI-B20-Animation-Development-20261027.md)。

## 修改清单

| 文件/资产完整路径 | 符号或属性 | 效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacterLinkMotion.cpp` | CopyNativePlaybackMontage、PrepareNativeLink、BeginNativeLink、CommitNativeMain | 动态载体工厂、真实过渡来源优先及诊断 |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | 自然翻滚完成序号、只读失败/入口诊断 | 自然结束才授权014/015事实，保留生命周期门控 |
| `Source/IntroCpp/MHWI/MHWIAnimInstance.h/.cpp` | UpdateLocomotionTransition、UpdateEquipmentIK | 真实移动/翻滚消费者与游戏线程骨骼偏移目标 |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter` | SequenceEvaluator/布尔混合、Slot后四链 | 13个动画节点及实际30条图连接，既有基础循环保留 |
| `/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile` | 四条连续骨链、项目探测/Alpha配置 | 新建保存并绑定CDO |
| `/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_005`、`006/007/008/014/015`（同目录与前缀） | 合格来源、骨架、REF_POSE/force root lock | 新增6个实际Sequence，基础层不叠加额外物理位移 |
| `ArtSource/ThirdParty/MHWLongSword/NativeFidelity/Animations/w03_00_005.fbx`等6文件及export-manifest.json | 源采样与FBX回读资格 | 六段独立合格导出，不提升缺镜像上下文片段 |
| `Scripts/MHWI/extract_locomotion_consumers.py`、`Tools/MHW/native-locomotion-evidence.json` | 19函数/6绑定、W03P70° | 可重建来源证据；trace_outstanding_evidence可选bank参数保持旧默认输出 |
| `Scripts/MHWI/author_remaining_animation.py`、`author_equipment_ik.py` | 定向制作、finalize/verify_assets/verify_weapon_selections | 保存/读回及实际32招选择枚举，不全量重建正式DA |
| `Scripts/MHWI/pie_remaining_animation.py`、`pie_r06_impact_matrix.py`、`pie_r06_repairs.py` | 真实生产PIE、瞬态夹具、独立输出目录 | 来源/骨骼/门控回归与可携带报告 |
| `Scripts/MHWI/audit_animation_coverage.py`、`Tools/MHW/animation-coverage-decisions.json` | 独立输出、合格资产路径及处置 | 87行逐项维护；181/182排除为非必需失败请求 |
| `Scripts/MHWI/collect_animation_verification.py`、`Tools/MHW/b20-animation-runtime-evidence.json`、`b20-animation-graph.json` | 报告指纹、保留断言、实际资产/连接清单 | 证据不再只依赖忽略的Saved；图清单不冒称独立重建器 |

## 接口、事件与资源影响

MHWI-015新增六段映射/运行快照及三个只读角色getter。Effector/JointTarget由旧component-space绝对目标改为end/mid骨骼相对偏移，ABP节点同时迁移到BCS_BoneSpace，不能只回退其中一侧。Profile中的项目极向偏移仍以component space配置，在游戏线程转换后供图消费；未在动画worker解引用Actor。

正式`/Game/MHWI/Data/DA_MHWI_LongSword`与B20开始指纹一致，32招、内部动画选择0–3已重新枚举，4/5保留未制造入口。无Build.cs、第三方插件或原游戏安装写入。运行期间训练地图出现额外保存，日志显示01:20:07 UTC保存；其归属未确认，不推断为玩法修改或擅自回退共享编辑器中的资产，另保留只读指纹供核对。

## 实际验证

| 检查/命令 | 环境与结果 | 证据 |
| --- | --- | --- |
| Build.bat IntroCppEditor Win64 Development -WaitMutex -NoHotReloadFromIDE -NoUBA | UE5.8，最后反射/来源修复完整构建Succeeded，101.03秒；此前工厂/IK构建亦成功 | B20/build-final-entry.log、build-roll-carrier.log、build-ik-offsets.log |
| author_remaining_animation.finalize / verify_assets / verify_weapon_selections | 真实编辑器编译保存；实际CDO、6段骨架/时长/根锁、4节点/骨名/空间/目标、Evaluator非循环teleport、32招选择读回通过 | assets-final-readback.json、weapon-motion-coverage.json、equipment-ik-profile.json、graph-connections-final.json |
| pie_r06_repairs.py（B20输出） | 最终二进制14/14通过：拔刀/SpiritI播放、合法受击恢复、非法拒绝、菜单清理 | PIE-r06-repairs.json |
| pie_r06_impact_matrix.py | 12例、95项通过：两姿态S/M/L到Light/Spirit；实际来源身份/源motion均核对 | PIE-r06-impact-matrix.json |
| pie_remaining_animation.py | 60 FPS上限34项、15 FPS上限34项、多视角37项均通过；实际移动、真实翻滚、014/015来源、双臂/双脚、阻断/空中/死亡 | PIE-animation-consumers.json、PIE-animation-15fps.json、PIE-animation-capture.json |
| pie_weapon_transfer.run(max_fps=30) | 178类断言、3750次逐帧检查通过；真实Enhanced Input、内部骨骼姿态、握点、特殊纳刀/居合、中断/死亡后旧事件；默认非strict源hold | PIE-weapon-transfer-30fps.json |
| extract_locomotion_consumers.py | 19函数/6绑定比对PASS | Tools/MHW/native-locomotion-evidence.json |
| build_outstanding_evidence.py / verify_outstanding_followup.py | 18函数/113动作/18资源与19续查函数全部比对PASS | 固定版本源及本机B17续查报告 |
| audit_animation_coverage.py --output Saved/MHWIRestoration/B20-20261027 | 87行完整处置、缺资产为空；不把静态状态当自动运行证明 | B20/animation-coverage.json/md |

六份PIE报告共3964次检查（含重复逐帧断言），受版本控制的精简证据保留所有不同断言及重复数，并记录原报告SHA。[运行证据](../../Tools/MHW/b20-animation-runtime-evidence.json)校验正式DA未变、最终源码及构建指纹。

失败记录保留：动态翻滚原始拒绝；Python反射/API及地形夹具失败；连续根运动离开平台导致地面恢复拒绝；旧截图文件误用及视角失败。截图最终使用独立瞬态相机和唯一文件名，三张逐一查看均保持同一特殊纳刀姿态；冻结截图不代表时序通过。不将早期37项功能断言通过但图像失败的旧run作为视觉证据。

## 风险、遗留与回退

R06完整mode0 MotionTree、N53/N60全部来源/Phase及32引用认证，332/333/334真实Action78前置；R28完整原生FSM/速度/物理和独立落地入口；R30原生solver/限位/坐标/manager/CTM仍缺明确闭合，未猜常量。特殊纳刀hold73是既有项目适配，本轮非strict武器回归不证明原生event80/保持时钟完整实现。N86无入边负例保留。co00_00_181/182纠正为B10附带失败且非必需，不用其他bank别名补齐。

回退只处理本CHG所列C++/脚本/新资产与ABP差异，备份见B20/Backup及before.json。目标快照和图空间配置必须一起回退；保持正式DA、共享地图和已存在专项验收修改。没有自动提交、发布或安装原游戏覆盖。

## 已同步文档

[系统页](../Systems/MHWI-LongSword.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[连接台账](../Plans/MHWI-Connector-Progress.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[开发流程](../Development.md)、[文档入口](../README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)及[B20报告](../Reference/MHWI-B20-Animation-Development-20261027.md)。文档/diff最终结果见B20/checks-final.json。
