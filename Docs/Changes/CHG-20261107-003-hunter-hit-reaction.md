# CHG-20261107-003：修复低帧下玩家短受击姿态缺失

- 状态：completed（现有三档动画的UE时序适配）
- 日期：2026-11-07
- 需求摘要：玩家被雌火龙命中只扣血，没有明显位移和受击动作。
- 关联：[PLAN-003](../Plans/PLAN-20261107-003-hunter-hit-reaction.md)、MHWI-013、R-ANIM-015。
- Git：工作区变更，未提交。

## 原因与结果

原24项检查核对了状态、动作编号和速度，没有验证最终显示骨姿。新增固定检查在旧二进制3FPS下稳定失败：35HP伤害、Large状态、source72和真实胶囊位移均出现，但没有可见且与受击源相符的最终骨姿样本。命中后0.333s已经Free/无Montage，短于源片0.533s，截图显示悬空站姿。

TickNativeSource以已经更新的当前帧再加Advance，消费预测结束位，长帧提前终止；NativeBlend首个目的pose保持旧显示姿态，两者叠加能吞掉短受击。修复仅Impact的这两处时序，保留三档源片和原力度配置。最终主项目同条件3FPS由失败变通过：相对根骨的5个躯干/头骨平均旋转误差约0.0044°，可见受击姿态与源片对应，命中后真实水平105cm/上升72cm。两种持刀状态、四招及连续输入/出招中受击均通过。

连续输入对照未证明大受击被立即取消，原ImpactCancelStart及输入规则保留。工程火球演出继续按用户选择保留，未恢复原作取证。

## 修改清单

| 文件/符号 | 修改原因与效果 |
| --- | --- |
| Source/IntroCpp/MHWI/MHWIAnimInstance.h/.cpp：BeginNativeBlend、proxy Begin | 非反射方法增加默认true的首目的pose保持选项；false仍捕获已显示姿态，但首次更新就消费owner delta |
| Source/IntroCpp/MHWI/MHWICharacterNativeSources.cpp：StartNativeSource、TickNativeSource | 仅Impact使用false，结束只按已经到达的当前源帧或真实Montage末尾；其他来源默认和预测行为保留 |
| Scripts/MHWI/pie_hunter_hit_reaction.py | 最终组件骨姿变化、相对根骨旋转与源片对应、实际命中后位移、档位/身份/伤害和真实长帧检查；以实际命中时持刀状态识别源片 |
| Tools/DevFlow/Hunter-HitReaction-20261107/ | 冻结合同/配置/完整Source副本校验及真实UE构建检查器 |
| Tools/MHW/hunter-hit-reaction-repair-20261107.json | 配置/代码门、构建、16次运行的121断言、位置复核及保护/清理摘要 |
| Docs/Plans/PLAN-20261107-003-hunter-hit-reaction.md | 本轮方案、实际证据和验收边界 |

未新增反射或动画系统，未写入动画/蓝图/关卡/DA，未改第三方工具。900资产逐文件hash不变，171源码文件中仅3份预期源码改变且匹配接受快照；用户原有MHWICharacter.cpp等修改保留。

## 官方依据、项目证据与限定

适用UE5.8：[UAnimInstance](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UAnimInstance)、[Slot](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/AnimGraphRuntime/FAnimNode_Slot)、[Montage](https://dev.epicgames.com/documentation/unreal-engine/animation-montage-in-unreal-engine)支持真实位置/结束委托、图输出及混合；具体代理扩展核本机5.8源码。它们不能证明MHWI原作语义。

项目证据是实际Basic PIE、已加载的225骨源片和DefaultSlot、最终mesh组件骨姿、源片RAW相对旋转和真实Actor位置。Impact首帧时钟/完成帧是UE post-update工程适配，不升级原作VM或整套受击状态机资格。截图在真实命中后暂停同一姿态，并临时隐藏雌火龙以看清玩家；它不代替连续运行断言。

## 接口影响

BeginNativeBlend(Frames) → BeginNativeBlend(Frames, bHoldFirstDestination=true)，纯C++方法，无反射字段/蓝图引脚迁移。其他调用保持默认true；Impact明确false，仍沿用原插值时长和序列速率。CancelNativeBlend保持原语义。ForwardEndFlags、IsMotionEnded、生成表、伤害/击飞值、输入恢复时机和来源/生命周期守卫不变。

## 实际验证

| 检查 | 实际结果 | 凭据 |
| --- | --- | --- |
| 旧二进制固定画面回归 | FAIL，仅最终骨姿断言失败，0合格样本；HP/档位/编号/真实位移均通过；max tick0.333336s | regression/PIE-before-charge-sheathed-3fps.json |
| 冻结候选编译 | quality-1 PASS，169.209s（UBT165.05s），快照未变 | HUNTER-HITREACTION-20261107-20f5bf83e6/evidence/quality-1 |
| 新Luna独立审查及主审 | approve，A1 met/findings空，L3 approve；ACCEPTED | independent-review.json、run内review/decision |
| 接受快照 | e5d5da74d4bbb18a10c16d43d87ca5095c48e22cf9e370db3c420a77932b2094 | integration.json |
| 主项目离线构建 | exit0，UBT97.74s，UTC07:33:04结束；随后重启真实编辑器 | main-build.json/.log |
| 最终骨姿/实际位移PIE | 12场景PASS：四招×纳刀/拔刀8种、两姿态3FPS、出刀中/连续输入2种，共96断言 | regression/PIE-after-*.json，具体白名单见稳定清单 |
| 位移断言加强 | v1原始数据仅以命中后样本重算，12/12 PASS；v2只加强此范围及基点，出刀/连按重测2次16断言PASS | post-impact-position-audit.json、regression-script-revisions.json、PIE-after-v2-*.json |
| 生命周期消费者 | 死亡清理/终态/拒绝输入4断言PASS；公开StartMove构造居合反击，实获霸体、后续10伤害减至5且不启受击5断言PASS | lifecycle/PIE-death.json、PIE-counter.json |
| 源码/资产保护及清理 | 900资产changed0/missing0；171源码仅3预期变化；PIE=false、dirty=[]、FPS0/Debug0、后台节流true、3个自有case无活跃回调 | protected-final.json、editor-final-state.json |

合计14种场景、16次成功运行、121运行断言；另有12份原始位置数据的独立重算。fps=0表示不强设帧率，实际game tick仍逐条记录；不把它当固定60FPS。所有修复后报告时间晚于主项目最终构建。

代码门目录为 Saved/DevFlow/Runs-20261107/HUNTER-HITREACTION-20261107-20f5bf83e6/；其他上表相对证据均在 Saved/RathianHitReaction-20261107/。稳定[小结](../../Tools/MHW/hunter-hit-reaction-repair-20261107.json)列原始报告hash，Saved证据交接需保留。

执行者与全新审查者分离；审查只读完整packet和未变基线上下文、无工具；工作副本不是OS/ACL隔离，usage/cost不可见。补充Luna审查确认最终骨姿/源片关联成立，并提出位移应排除受击前运动，已加强而未放宽姿态阈值。

历史夹具问题保留：第一次生命周期夹具调用未反射的气槽setter失败；改用无需气槽的真实居合反击，失败JSON留在lifecycle。画面冻结探针继承旧速度峰值采样断言，不作为低帧验收；正式regression使用真实位置，保留原失败含义。原24报告不补写骨姿断言为历史通过。

## 风险、回退和未覆盖

本轮修复短片段被吞；沿用现有三档受击片段，不新增原作完整空中循环/倒地/起身状态机。非Impact默认行为由源码与编译复核，本轮不重跑全量投射器/弹刀/太刀派生或原作逐帧对照。没有原作启动/解包、Sandbox修复或系统重启/关机。

回退只处理本轮3份源码：先核integration.json当前after hash，再从pre-integration恢复原字节并完整构建；不回退其他用户源码/既有Basic资产。测试脚本与稳定清单可单独撤下。旧CHG-002保留当时基础版和有限验收的历史含义。

## 已同步文档

[交接](../Plans/MHWI-Rathian-Handoff.md)、[当前入口](../Plans/MHWI-Current.md)、[方案](../Plans/PLAN-20261107-003-hunter-hit-reaction.md)、[太刀现状](../Systems/MHWI-LongSword.md)、[雌火龙](../Systems/MHWI-Rathian.md)、[接口](../Interfaces.md)、[模块](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[记录索引](README.md)。

## 最终文档检查

- 新回归脚本及冻结构建检查器AST：PASS。
- python -B Scripts/Docs/check_docs.py：PASS，39 Markdown、388本地链接、16模块与editor snapshot JSON；不代替运行验收。
- git -c core.safecrlf=false diff --check：PASS，exit0；仅本次命令关闭行尾转换提示，未改仓库配置。
- 文档写入后再次运行上述文档/差异检查。UE保持Basic、PIE结束、无脏包，调试/帧率/后台节流和回调均清理。
