# PLAN-20261104-001：以Dual-Agent DevFlow执行THK条件参数审计

- 状态：prepared-awaiting-isolation；DevFlow已到PREPARED，执行模型/候选验收/独立模型审查均未启动。
- 日期：2026-11-04。
- 用户需求：阅读交接文档后，用刚安装的Dual-Agent DevFlow继续工作。
- 关联：BEH-01、R-DATA-005；后续播放问题R-ANIM-012独立处理。
- 变更记录：[CHG-20261104-003](../Changes/CHG-20261104-003-devflow-thk-audit-preparation.md)。

## 现状与目标

已读[11-04交接](MHWI-Rathian-AI-Handoff-20261104.md)、VM交接及11-04编译记录。当前首个小任务采用交接§8里程碑1：完整读取已解出的THK段，为社区候选语义做参数形态、映射冲突及未知优先级审计。此任务不依赖UE或原作运行；下位候选可达集和B1动画播放另开后续任务。

本次只读核查发现：旧统计的参数对先放set，恒定排序后截6项，映射工具又截4项，因此旧top_params不是全量频次证据；fexty的0x3重复定义十六进制选择器50（即0x50）。形态一致仍不证明原生语义。

B1源码当前使用AnimationBlueprint+普通UAnimInstance，却调用需要SingleNode实例的Body.SetAnimation(Montage)；本机UE5.8源码确认该模式下只发警告。此为静态发现，未做PIE，记录R-ANIM-012，不混入本次数据审计范围。

## 官方方案及版本

- [CodeBuddy CLI参数](https://www.codebuddy.ai/docs/cli/cli-reference)：本机doctor实测2.179.3，所需参数齐全；模型使用已安装配置中的deepseek-v4.1-flash，不改全局默认、不添加fallback。精确服务端1017检查点不能由CLI回显独立证明。
- [微软Sandbox配置](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file)：可将workspace读写、input只读映射；配置文件本身不代表隔离环境已经存在。
- [微软Sandbox版本与入口](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-versions)：核查同时覆盖旧入口与新版应用/wsb入口，避免只凭WindowsSandbox.exe缺失误判。
- 已调用本机devflow-orchestrator/planner/quality-gate/reviewer等技能套件1.0.1；其workflow明确禁止省略VM/Sandbox边界后启用自主执行。此为本次执行环境前置，非项目技术路线重新审批。

## 范围与验收标准

冻结任务ID为RATHIAN-THK-AUDIT-20261104，风险L2。只允许新增：

1. Scripts/MHWI/audit_rathian_thk_candidates.py
2. Tools/MHW/rathian-thk-condition-audit-20261104.json
3. Docs/Reference/MHWI-Rathian-Condition-Audit-20261104.md

以上三项尚未实现。不能把此准备记录当作条件审计报告。原作、UE、运行源码、资产、原有工具与可信checks均不在执行者修改范围。

| 验收组 | 必须证明 |
| --- | --- |
| actual_complete_coverage | 105表/1795节点/13015段全计数；排除0x0/0x2后2191次、58类；保留全部250种参数组合及来源定位 |
| rare_pair_not_truncated | 低频、出现在旧截断界限之后的参数冲突也被审计 |
| candidate_shape_boundaries | 距离/布尔/角度/rank候选规则与越界，跨零角度有效；未审查规则保持unknown |
| hex_duplicate_selectors | Use Hex正确，超过8个case后的重复且冲突定义不被覆盖 |
| unknown_never_promoted | 未映射保持未知；形态一致仍community-candidate；原生语义已证数为0 |
| deterministic_cli_provenance | 输入SHA来自真实字节；换输入根/输出目录仍可重复，逻辑路径不带机器绝对目录 |
| malformed_inputs_refused | 三个int32字段缺失/错误类型/越界、损坏JSON、重复定位和计数不符须拒绝 |
| real_reports_generated | 全量实际输入生成两份报告，Markdown与JSON一致，本地self-check完成 |

58类是本审计的“非结构functionType候选集合”；不推导全部为纯布尔条件，也不据此建立已验证LR动作分母。

## 技术方案与接口

任务契约：[task.json](../../Tools/DevFlow/Rathian-Condition-Audit-20261104/task.json)。
可信验收：[check_candidate_audit.py](../../Tools/DevFlow/Rathian-Condition-Audit-20261104/checks/check_candidate_audit.py)。

拟新增脚本提供audit(raw, fexty_text)、render_markdown(report)、main(argv)；CLI显式指定raw/fexty及JSON/Markdown输出。完整schema与候选形态假设已冻结在输入包Context/task-brief.md，普通字符串表达式不得eval。

GPT负责任务与固定验收；CodeBuddy负责限定范围实现；控制端独立capture/check；新CodeBuddy会话无工具review；decide有缺口不能放行。只有ACCEPTED才导出补丁。保持八轮、最多两轮修复、六次模型调用上限及完整审查包预算，不用截断证据包换取通过。

## 基准与数据迁移

未对原工程暂存或提交。为满足DevFlow完整干净提交要求，建立单独的七文件输入包仓库，包含全量raw、固定fexty、旧参考报告与上下文；这是任务输入包，不是整个UE工程快照。

- 原工程HEAD：f29b9e62851cfe8f9984dd6839fe5e37449c4125。
- 独立输入包最终基准：8904746b662dffc6527d93acc7dcfe99f49258c4。
- 逐文件源路径/尺寸/SHA见[source-manifest.json](../../Tools/DevFlow/Rathian-Condition-Audit-20261104/source-manifest.json)。
- 本机运行回执：[readiness.json](../../Tools/DevFlow/Rathian-Condition-Audit-20261104/readiness.json)，phase=PREPARED、model_calls=0。
- workspace/input/baseline及原始16.8MB输入留Saved/DevFlow/Rathian-Condition-Audit-20261104，控制契约/可信checks/回执另外归档到Tools/DevFlow，避免关键准备记录只留忽略目录。

## 实施步骤与依赖

1. 已完成：交接核查、官方资料与CLI doctor、任务规划、独立输入基准、可信check独立只读审查及修订、正式prepare、双映射Sandbox配置生成。
2. 执行前置：提供真实隔离执行环境和可信测试环境。本机尚未找到Sandbox旧/新入口、应用包或开发VM；WSL报告未安装。读取Windows可选功能状态需要管理员提升，因此未将其写成确定的Disabled。
3. 在隔离环境中复用公开任务及固定输入。若运行路径/平台变化，使用归档task.json重新prepare；不能改写既有冻结run的task/config/state。超过两小时调用预算时新建run，保留旧PREPARED记录。
4. 执行者在来宾独立登录，保留default工具权限提示；不映射主机账户凭据，不使用绕过参数。
5. 执行停止后登记真实会话/模型/退出码，capture→check→新会话review→decide。缺身份或证据保持失败/待验证，不伪造放行。
6. ACCEPTED后export，按源清单复核原工程相关文件SHA及目标文件是否已出现，git apply --check后定点集成，再跑项目文档检查。原工程其他未提交内容保留。

## 验证计划与实际边界

本次doctor通过、任务prepare成功、check脚本只做语法编译及独立静态审查，未运行任何候选。Sandbox XML只映射workspace和只读input，未启动来宾。最终文档检查见CHG。

候选尚不存在，不能写check通过、review通过、audit已完成或原作语义已证。数据工作不重编译引擎，不把11-04历史构建当本轮执行。

## 风险与回退

首要前置是执行隔离；技能要求的边界不能用普通Git副本或IsolatedGuest参数代替。环境需要启用系统功能或新VM时应由用户确认具体操作。本次没有更改系统功能、登录、默认模型、游戏或UE资产。

未集成时可保留或单独丢弃本次候选/输入包；只撤回本批文档和Tools/DevFlow准备产物，不reset/clean原工程。已完成历史CHG不改写。

## 文档同步清单

同步Plans/Changes索引、交接最新补充、Known-Issues的R-DATA-005/R-ANIM-012，以及现有解包模块的任务契约入口；未新增虚构的已实现审计运行模块。

## 2026-11-04环境选择与实际阻塞

用户交由助手选择后，采用Windows Sandbox。管理员启用实际失败0x80073712；随后CheckHealth确认Repairable、Sandbox仍Disabled，未执行RestoreHealth或重启。详见[CHG-004](../Changes/CHG-20261104-004-windows-sandbox-enablement.md)。环境启用权限不扩大为系统修复权限，拟议修复命令为Repair-WindowsImage -Online -RestoreHealth -NoRestart，等待用户明确同意。冻结run保持PREPARED，模型调用0。

## 2026-11-05系统修复授权与监督

用户已明确授权执行RestoreHealth+NoRestart，已完成监督：退出1/0x800f0915缺源，复查仍Repairable/Disabled，无重启/关机；最终状态见[本次记录](../Changes/CHG-20261105-001-windows-component-store-repair.md)。11-04“等待修复授权”仅保留为当时事实，不再作为当前授权状态。冻结DevFlow run未修改，模型调用0。

## 2026-11-05官方源续修与当前阻塞

详见[续修记录](../Changes/CHG-20261105-002-windows-official-source-repair.md)。WU源修复曾Healthy，SFC无违规，但实际Sandbox启用仍受OC压缩元数据异常阻塞；外部用户上下文重启后当前复查Repairable/Disabled。官方包仅作工作区来源核验，未安装旧更新/升级系统。DevFlow保持PREPARED、模型调用0。
