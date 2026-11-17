# CHG-20261107-001：雌火龙基础玩法源码与离线验证

- 状态：completed（离线代码阶段；完整玩法仍partial，资产/PIE续接CHG-20261107-002）
- 日期：2026-11-07
- 需求摘要：暂停原作取证，先实现巡逻、发现/按招式移动、小咬/龙车/单火球/尾翻起飞落地、盒形判定、HP、受击击飞与死亡。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261107-001](../Plans/PLAN-20261107-001-rathian-basic-combat.md)、ADR-0002、R-ANIM-012。
- Git：工作区变更，未提交；DevFlow输入/验证副本有私有基线提交，不是用户仓库提交。

## 原因与结果

旧Approx执行体缺少完整基础循环。已建立独立输入/候选/验证副本，由原生gpt-6-luna实现；父审查要求保留原有可替换策略接口，统一由Decision/Policy决定动作，Pawn只执行。最终13文件快照已通过冻结UE5.8 UHT/C++/链接、全新Luna独立审查和主代理L3审核，DevFlow状态ACCEPTED；已按原文件hash核验合入主Source并备份9份旧文件。已补齐巡逻/策略选招/阶段动作/盒扫/火球/HP/死亡源码；数据和运行部分仍未完成，不能称为可玩版本。

用户最新要求先不启动UE，因此本批只做源码、UBT/UHT离线构建和静态审查；必须启动Editor进行动画挑选、资产配置、蓝图读回及PIE时停止。该限制前有一次编辑器启动尝试，但桥接未就绪；限制后核对本任务PID已不运行，未再次启动Editor/Cmd/PIE。未启动原作、未继续解包、未修Sandbox、未重启或关机。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Docs/Plans/PLAN-20261107-001-rathian-basic-combat.md`、`Docs/Plans/MHWI-Current.md` | 基础玩法范围、验收、UE停止边界 | 方案先行，区分工程玩法与原作忠实度 |
| `Source/IntroCpp/IntroCpp.Build.cs` | AnimGraphRuntime依赖 | 为原生动画节点声明直接依赖；保留已有用户修改 |
| `Tools/DevFlow/Rathian-Basic-20261107/` | 冻结task/config/checks、输入hash及迁移凭据 | 将候选限制在Approx源码；检查只启动UBT/UHT，不启动Editor |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxPawn.h/.cpp`、`MHWIRathianApproxData.h/.cpp` | 执行状态、配置/接口及阶段数据 | 巡逻/发现、移动/转向、实例身份/跨窗/盒扫、持续Landing、HP与终态死亡；默认参数为工程近似 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianDecisionComponent.h/.cpp`、`MHWIRathianDecisionPolicy.h`、`MHWIRathianScriptedPolicy.h/.cpp` | 统一决策接口/快照、资格、冷却、角度与请求 | Pawn只消费决策，不另建选招器；使用atan2有符号角度及按度/秒限制的转向 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxAnimInstance.h/.cpp`、`MHWIRathianApproxFireball.h/.cpp` | 新增4个文件 | 原生动画图/死亡从0非循环；延迟生成socket火球、一次伤害、自身causer与反击霸体门 |
| `Saved/RathianBasic-20261107/next-ue-checkpoint.md` | 下一资产/运行节点 | 待执行清单，不是运行报告 |
| `Docs/Changes/README.md`、`Docs/Archive/MHWI/README.md`、`Docs/Known-Issues.md` | 最近5条记录轮换与链接 | 历史003原文移入Archive；不改历史结论 |

## 接口、事件与资源影响

已新增MHWI-016：SetCombatTarget、RequestBasicAttack及状态/招式/运行编号/HP读取；数据资产增加阶段动画、骨骼盒及移动参数，原生AnimInstance作为唯一动画图。反射签名随UHT和模块编译通过，实际蓝图尚未编译/保存或读回。Configure一次性幂等，替换数据需新实例。新增参数是工程近似，UE官方机制不能证明MHWI原作行为。

用户已有太刀DA、训练地图、MHWICharacter.cpp及其他未提交修改保留。本批未创建或保存任何新Basic资产；拟使用`/Game/MHWI/Rathian/Basic/`，848条素材原件不覆盖。非BITE动画、实际骨名、根轨/比例仍须预览确认。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| DevFlow prepare/capture | UE5.8、源文件私有干净输入 | 最终run捕获13文件且scope issues为空 | `Saved/DevFlow/Runs-20261107/RATHIAN-BASIC-20261107-e9f989d679/state.json` |
| 冻结quality-1 compile | 最终run、精简环境 | 失败：UBAExecutor.Init默认CommonApplicationData为空，尚未得到C++通过结果 | 同run `evidence/quality-1/quality.json`；完整UBT日志另存`Saved/RathianBasic-20261107/candidate-attempt1-ubt.log` |
| 项目级UBA缓存显式配置预检 | 独立验证项目、MaxParallelActions=2 | 已越过初始化；系统提交内存接近耗尽，父代理停止本任务预检，未称通过 | `Saved/RathianBasic-20261107/environment-preflight-ubt.log`、`validation-environment-correction.json` |
| `python Scripts/Docs/check_docs.py` | 当前主工作区 | PASS：36 Markdown、344本地链接、16模块；仅文档/索引 | 控制台实际输出，非玩法验证 |
| `git -c core.safecrlf=false diff --check` | 当前主工作区 | 退出0，无差异空白错误 | 本轮独立执行，不含进程查询退出码 |
| 主源码输入保护核对 | 当前主工作区167份Source文件 | 与本批输入全部hash一致（输入已含父代理AnimGraphRuntime依赖）；业务候选尚未合入 | `Saved/RathianBasic-20261107/main-source-protection.json` |
| 冻结quality-2 compile | 原封存检查，验证项目单并发 | UHT通过；C++失败为Pawn两处`FVector::Lerp`（C2039/C3861），未称通过；检查期间快照未变 | 同run `evidence/quality-2/quality.json`；`Saved/RathianBasic-20261107/candidate-attempt2-ubt.log` |
| 冻结quality-3 compile | 最终快照e7a2ee3a…，原封存检查/单并发 | PASS：UHT、C++及链接；exit0，113.88秒；快照检查期间未变 | 同run `evidence/quality-3/quality.json`；`Saved/RathianBasic-20261107/candidate-attempt3-ubt.log` |
| 全新Luna独立审查 | `/root/luna_basic_independent_review`，gpt-6-luna/high，fork none，与执行者不同 | approve、A1 met、findings空；只审离线代码资格，不宣称运行通过 | 同run `evidence/review-1/review.json`及identity.json |
| 主模型L3审核/导出 | 读简报和关键源码，绑定最终快照 | ACCEPTED；补丁SHA256 a112569c3a34b0f9b962fd4342b55a86a47b825adec357bdfa0468d7bafcbd51 | 同run `evidence/decision.json`；`Saved/RathianBasic-20261107/accepted-export` |
| 核hash合入主Source | 主工作区 | 13文件精确候选字节，9份旧文件已备份；合入前主文件与输入基线相符 | `Saved/RathianBasic-20261107/integration.json`、`pre-integration/` |
| 原项目离线构建 | 实际IntroCpp.uproject，单并发、NoUBA、不启动Editor | PASS：exit0，19动作完成，UBT201.82秒；2026-11-07 01:40:21+08结束 | `Saved/RathianBasic-20261107/main-project-build.json`、main-project-build.log |
| 旧基线预检 | 原始baseline | 曾到29/73动作后父停止；仅预检，不是候选验收 | `Saved/DevFlow/Validation-20261107/RATHIAN-BASIC-20261107-0f0faae472/build.log` |

最终冻结编译、独立审查、原项目编译均已通过；源码合入及现状同步后文档检查PASS：36 Markdown、352链接、16模块，diff退出0。最后额外Consistency JSON写入曾因自动审批额度耗尽未执行，不把它写成通过。后续用户已授权UE，见CHG-002与当前交接。资产/PIE按用户限制未执行，不用历史构建或编译结果替代玩法验收。ComfyUI进程不属于本任务，未关闭；曾因约14GB提交占用询问编译安排，随后实际可用提交内存恢复约7GB，无需关闭用户程序，原授权的离线构建以单并发继续。单并发配置hash见`Saved/RathianBasic-20261107/validation-single-action.json`。

## 官方机制、现状与推断

- 官方UE5.8：[Montage/Slot](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine)、[形状Trace](https://dev.epicgames.com/documentation/en-us/unreal-engine/traces-in-unreal-engine---overview)说明播放与扫掠能力。本机5.8 AnimInstanceProxy.h支持GetCustomRootNode/GetCustomNodes。
- 官方引擎源码：`Engine/Source/Programs/UnrealBuildTool/Executors/UnrealBuildAccelerator/UBAExecutor.cs:257–278`支持显式RootDir；本次仅设置验证项目本地XML缓存目录/2GB容量，不改系统配置、冻结检查或引擎源码。hash见validation-environment-correction.json。
- 官方UE5.8 [活跃Montage实例查找](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UAnimInstance/GetActiveInstanceForMontage?lang=en-US)明确非活跃返回空；[FAnimMontageInstance](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/FAnimMontageInstance)提供实例ID。结合本机AnimInstance.cpp:3417–3441/3696–3710推断旧候选结束阈值不可靠；该推断是UE源码审查，不是原作运行证据。
- 项目静态证据：13文件候选、实际失败日志和内存读数。攻击距离/窗口/盒体/击飞/飞行参数属于工程配置，不能推断为原作机制。

## 风险、遗留与回退

已按冻结检查→全新Luna审查→主审→ACCEPTED导出→核hash合入执行。最初wrapper/receipt预检失败的旧run没有导出，最终run的quality-1环境失败/quality-2插值API失败原始日志保留；初次加两轮修复未超限。控制文件和检查未改写以放行候选。

审查输入传递有一项明确例外：[devflow-reviewer技能](<C:/Users/Butter cookies/.agents/skills/devflow-reviewer/SKILL.md>)名义要求“不要改文件或调用工具”；本宿主提示仅允许先只读加载父代理生成的129445字节冻结packet（含hash/分片输出），完整加载后禁止工具，不执行/导入候选或联网。该输入传递例外已写入identity attestation；不宣称严格零工具审查或OS/ACL隔离。packet SHA256为b7bee46d28c037429cf5c4ba72502468a24e7f42a762e77b4e99dce0ff11cc54；真实usage/cost不可见，保留null。

运行时动画/碰撞/地形/死亡仍未验收，按用户要求先停止，不启动UE；下阶段须在独立Basic资产/关卡验证。

回退按integration.json逐文件核对当前hash：恢复pre-integration中的9份旧源码，移除本批新增4份源码；只在确认没有后续修改时操作。随后按需撤销Build.cs新增AnimGraphRuntime依赖并同步现状文档；保留其余用户修改，禁止reset/clean整个工作树。没有业务资产回退需求。

## 已同步文档

[文档入口](../README.md)、[当前入口](../Plans/MHWI-Current.md)、[实施方案](../Plans/PLAN-20261107-001-rathian-basic-combat.md)、[已知问题](../Known-Issues.md)、[记录索引](README.md)、[归档索引](../Archive/MHWI/README.md)。已同步[系统页](../Systems/MHWI-Rathian.md)、[接口MHWI-016](../Interfaces.md)、[模块索引](../Reference/modules.json)；R-ANIM-012保留运行待验，新增R-AI-004记录资产/PIE边界。
