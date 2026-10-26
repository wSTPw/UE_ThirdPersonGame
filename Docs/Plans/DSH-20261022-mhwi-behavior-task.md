# DeepSeek 实施任务：MHWI 七项动作行为

- 用户：2026-10-22 明确授权记录袈裟斩规则后直接实施，并尝试多子代理。
- cwd：`E:/Unreal Projects/IntorCpp`。
- 方案：[PLAN-20261022-002](PLAN-20261022-002-mhwi-longsword-behavior.md)；证据：[资料核对](../Reference/MHWI-LongSword-Behavior-Research.md)。
- 启动日期：2026-10-23，Asia/Shanghai；任务包与研究起于2026-10-22。
- 父会话：`session-e3dd6ab0-ccf0-45c3-bc57-21cdb1f6a567`，headless，cwd同上。
- 原生子代理 A：`118c7511-fd8f-4b65-8cf8-652153f6926f`；B：`d483334a-0b77-4354-9ed1-593ec3deb10c`；C：`fdefcd4f-89f0-4f75-9f4e-cf97659386cb`。
- 状态：实施中；2026-10-23三次原生subagent调用同批成功，实际结果保存在 `Saved/MHWIImport/DSH-20261022/parent-events.jsonl` 与 dispatch.json；不是实施通过报告。

## Codex 运行环境补充（2026-10-23）

DSH shell 的 Windows 沙箱初始化遇到 `SetNamedSecurityInfoW ... grantWrite` 失败，DSH自带提权也没有审批通道。**禁止尝试修复/更改Windows文件夹权限、关闭沙箱或提升自身权限**；不是本任务授权内容。直接read/write/edit文件工具仍可用于限定文件实现。所有git、语法检查、Blender、UE构建及验证命令可列出交给Codex按宿主正常权限执行。Codex已完成启动前git status和定向备份，不要因shell失败重复探测/修复权限；报告未运行检查即可。若直接文件工具也失败，报告准确错误，禁止绕过。

## 给 DeepSeek 父代理的执行指令

你是实施协调代理。Codex 已制定下面的合同；请实际完成实现，不要只给建议。首先读取项目 AGENTS.md、Docs/README.md、上述方案和研究页、Docs/Systems/MHWI-LongSword.md、Docs/Development.md，以及 `.agents/skills/introcpp-context-router/SKILL.md` 和 `.agents/skills/ue-input-system/SKILL.md`。实际源码在Source，不是C++ Source。

**先尝试原生 subagent 工具同时启动下述 A/B/C 三个子代理**。每个子代理得到完整合同与自己的文件所有权，初始cwd均为本项目。若子代理工具不存在/深度或容量拒绝，不修改本机DSH配置：将实际错误写报告，停止派生；若只能两个则A+B先并行，C随后。你不得调用Codex/Claude或其他外部模型代理；只使用本机当前DeepSeek路线，子代理沿用配置。父代理只协调、只读审查、收集结果，不写A/B/C所有权文件。

启动后立即将真实父/子会话ID、标签、工作目录、文件所有权写入 `Saved/MHWIImport/DSH-20261022/dispatch.json`。按实际工具返回读取ID；父ID若运行上下文未提供可留null并由Codex从session事件补齐。记录工具拒绝或成功，不把包已安装当作并行成功。

## 共同边界

- 工作区已有大量未提交修改。启动前git status，保留所有无关内容；禁止git reset/clean/checkout回滚、commit、push、依赖安装、改插件/全局配置/凭据。
- 不读取个人凭据文件或输出API Key。不得改本机DSH/UE安装；不得绕过任何宿主权限拒绝。只按本任务允许路径读写。
- 子代理可以并行写各自所有权文件，不得跨界；发现合同问题通过父子消息报告，不能静默改另一个代理文件。
- **不操作UE编辑器、不启动/停止PIE、不保存uasset、不编译本项目**。Codex负责串行编辑器操作、完整构建、独立验收。可以只读查询本机UE头文件、对自己脚本做语法检查。
- 所有代码保持单前台动作、实例身份/ExecutionSerial、死亡/中断/EndPlay清理。不能以跳过真实输入/资源/伤害来制造测试成功。
- 保留气刃II=106/上挑=107、根锁REF_POSE、RootMotionFromMontagesOnly常态、纳刀203/090走跑、武器/鞘口拟合、默认训练木桩被动、不修改Ninja。
- 所有新增角度、速率、空中参数初值标记项目调校，不能冒充原版精确常数。公开格式解码的登龙参数组仍未经调用映射证明。

## A：C++ 动作运行时（只写这些文件）

`Source/IntroCpp/MHWI/MHWICharacter.h`、`MHWICharacter.cpp`、`MHWIMovesetData.h`。必要的独立原生测试可新增 `Source/IntroCpp/Tests/MHWIBehaviorTests.cpp`，但不能为方便测试扩大公开作弊API。

目标：

1. 镜头相对移动意图统一函数：`Yaw(ControlRotation).RotateVector(FVector(MoveInput.Y,MoveInput.X,0))`。无输入保留朝向。普通动作在合法早期窗口以最短弧、偏角上限和角速度转向；Roll可保留原先自由起手方向。镜头观察本身不无条件转身。
2. 袈裟斩在中立与活动派生两处统一选择：世界意图投影到**选择前角色右轴**，小于-0.2选FadeSlashLeft，大于0.2选Right，其余/无输入选后退FadeSlash。选中后三片段禁止额外程序入口转身（数据TurnMaxAngle=0），不能双重旋转。实际源127左、128右，103后退，已从根轨迹交叉核对。
3. 路由增加RequireDrawn条件。Roll恢复Light路由只在持刀成立，纳刀翻滚仍走DrawSlash。过期/中断/死亡/纳刀清除恢复身份，支持合法恢复边界，不让旧Roll长期影响中立。
4. 插入动作身份使用`SpiritComboThrust`、`SpiritComboRisingSlash`，其路由由B设置；正常RMB循环靠路由而非永久全局气刃段数。保留原0.3秒输入缓冲/窗口跨帧/真实成本校验。
5. 登龙阶段明确分为Rise/Air/Strike/Land（可内部枚举，动作ID固定），起手实际命中且白刃以上才进入Rise；Rise 171保留垂直根运动，完成后切Air。Air/Strike用物理速度、重力、碰撞，零根轨迹172/173必须在本AnimInstance忽略位移而非覆盖水平初速。跨阶段不能StopMovementImmediately丢失运动；存/恢复RootMotionMode、GravityScale、MovementMode等快照由整个链管理一次。
6. Air阶段LMB/RMB/R/G映射为下劈请求；在Rise尾部可用原缓冲排队。Air没有攻击输入则自然落地收尾，不发七段、不降色。Strike只在指定动画起落点提交快速下落；不要从0秒立刻砸地导致尚未举刀就落地。`Landed`只登记事实，游戏线程安全点按代次切Land，不能重入重复提交。Air→Land（无下劈）也是合法阶段，但无伤害授权。
7. Air/Strike动画到尾部可保持/循环姿态，不能因此直接瞬移落地、长期Flying或单靠长度自动下一步；实际落地驱动。低顶/斜面/目标顶部、死亡、UnPossessed/EndPlay、播放失败都恢复。HelmLand七段与降色只由本次有效下劈授权，标记目标沿合法链传递，退出/打断清空。保留已有每窗口去重与反击语义。
8. 见切退避和回斩可分别采样方向/限制偏角，回斩窗口通过下面的数据字段配置。不得把近战所有招式变成持续360度追随镜头。

### 固定共享反射合同（A实现，B/C只使用）

在FMHWIRoute新增 `bool RequireDrawn=false`（Python `require_drawn`）。

在FMHWIMoveDefinition新增以下EditAnywhere/BlueprintReadWrite浮点字段，均是**项目调校**：

| C++ | Python | 默认值 / 单位 |
| --- | --- | --- |
| TurnStartTime | turn_start_time | 0，Montage秒 |
| TurnEndTime | turn_end_time | 0.12，Montage秒 |
| TurnMaxAngle | turn_max_angle | 25，度；0禁用 |
| TurnSpeed | turn_speed | 360，度/秒 |
| ReturnTurnStartTime | return_turn_start_time | -1，禁用第二窗口 |
| ReturnTurnEndTime | return_turn_end_time | -1，Montage秒 |
| ReturnTurnMaxAngle | return_turn_max_angle | 45，度 |

在UMHWIMovesetData新增以下EditAnywhere/BlueprintReadWrite浮点字段：

| C++ | Python | 默认值 / 单位 |
| --- | --- | --- |
| HelmAirVerticalSpeed | helm_air_vertical_speed | 700，cm/s |
| HelmAirForwardSpeed | helm_air_forward_speed | 200，cm/s |
| HelmAirGravity | helm_air_gravity | 1250，cm/s² |
| HelmStrikeSpeed | helm_strike_speed | 3000，cm/s，向下取正参数 |
| HelmStrikeStartTime | helm_strike_start_time | 25/60，Montage秒 |

数据层不新增空中枚举，由动作身份/内部阶段决定。仅Rise继续使用旧bUseFullRootMotion；B将Air/Strike自动出口清空。C可从GetCurrentMove、角色速度/MovementMode/朝向、正式数据字段验证，不需要A新增作弊setter。

## B：动作数据与制作脚本（只写这些文件）

`Scripts/MHWI/author_assets.py`、`Scripts/MHWI/moveset_mapping.json`；可新增 `Scripts/MHWI/author_behavior_corrections.py` 和只读连接端点分析脚本 `Scripts/MHWI/audit_behavior_links.py`。不改C++或测试脚本，不执行UE写入。

1. 更新源映射SpiritThrust=170、FSM node45/Action87；ForesightSlash=140、node28/Action86。同步所有TIML碰撞、长度、输入字段、MotionSpeed等依赖，不能只改clip字符串；数据来自现有extract_moveset_mapping.lmt_events。保留106/107及其他已修标签。
2. 制作默认moveset及定向修复入口都采用新路由：SpiritI Light/Thrust→SpiritComboThrust；SpiritII Light/Thrust→SpiritComboRisingSlash；两个插入身份R→SpiritII/III，普通Light回到原普通链；普通Thrust右键→RisingSlash，RisingSlash右键→Thrust。
3. 新插入身份可复用已核对105/107主Montage，但明确标记连接帧尚属项目混合，不能臆造新原版动作映射。原始118/121/124连接作为端点分析对象，不能增加伤害段。
4. Roll的Light→`RollStepSlash`，RequireDrawn=true。制作专用Montage尝试129连接到101的合适入口（保留攻击55..66源帧，避免完整129+完整101双重前冲）。用原Converted .blend只读采样/端点误差找切入点；如果当前UEPython不能写AnimSegments，提供Codex需要通过MCP执行的**明确段配置JSON**，不能私自改现有Montage成别的序列或仅写假报告。新动作的伤害/取消时间必须随组合偏移重新计算，后续LMB→OverheadSlash。
5. SpiritThrust命中后AutoFollowUpOnHit→HelmRise，时间与170碰撞末端一致；只有Rise保留自动→HelmAir。Air/Strike清空自动出口，取消窗口普通通用取消禁用；Air/Strike由A按输入/真实着地管理。不要改源Sequence整体Root Motion设置；运行时处理。
6. Foresight140反击窗口可先保留8..42源帧作为项目调校；碰撞70..80，回斩转向窗口46..68源帧、偏角45。普通转向按共享默认；Roll及三条Fade额外转向窗口禁用（Roll已有专用起手）。HelmAir和Strike前25源帧可允许大角度瞄准，所有值明确项目适配。
7. 定向入口形如 `run()`，仅复制并更新正式DA中的目标struct（UnrealMap必须先转dict、struct.copy，禁止预览零消耗残留），保存受影响资产；禁止SaveAll/重建训练图/覆盖人工材质/重新导入所有资源。脚本模块import必须无副作用，入口可多次执行；新增/修改资产清单、需要MCP先做的步骤、实际Python语法结果写报告。
8. 制作入口应检查不是PIE且新反射字段存在，不满足时报错，不吞异常假成功。新共享字段以A合同为准，不随意改名。

## C：验证脚本（只写这些文件）

新增 `Scripts/MHWI/pie_behavior_corrections.py`，必要时新建只读 `Scripts/MHWI/inspect_behavior_corrections.py`。不要改已有历史PIE脚本或任何业务实现，不运行UE。

制作可由Codex调用的 `run(suite='all')`，模块import无副作用；使用Slate tick有限状态机，报告输出 `Saved/MHWIImport/PIE-behavior-<suite>.json`。可分ground/direction/air/lifecycle子套件控制时长。读取已有pie_moveset、pie_edges、pie_animation_corrections等了解真实Enhanced Input注入，不复制旧的自动登龙假设。

覆盖：实际140/170段/姿态；真实气刃链积槽再插入续接、至少六次RMB交替；持刀/纳刀Roll接左键；镜头0/90/180/270、前后左右/无输入的袈裟方向与真实位移（禁止只断言MoveID）；普通派生转向及无输入只动相机不转身；登龙命中/空挥、Air攻击输入与无输入着地、七段授权/降色、物理阶段时长/Z/速度、打断后恢复。A尚未完成时只写脚本，稍后读实际实现确认API，不预设不存在的getter。

测试正常路径用正式成本和正式DA；不得将成本设0制造成功。独立边界夹具若确需复制数据，要显式transient、标明未覆盖自然输入路径，不改正式资产。默认木桩被动性先断言，不要强制全关后再宣称默认正确。恢复EditorPerformanceSettings、临时世界/回调；错误也落盘并释放。每套有wall-clock超时和清晰phase诊断；不要断言未经标定的原版准确角度/秒数。

## 汇报与完成

每个子代理把修改文件、实际运行过的检查、未运行的UE步骤、关键设计/不确定性写入自己独占的 `Saved/MHWIImport/DSH-20261022/report-A.md`、B、C。父代理只读审查交界，发现问题消息要求原作者修复；都完成后输出汇总 `report-parent.md`，并明确真实多子代理成功/失败及ID。

不要以“等待其他子代理”作为最终交付；headless宿主支持等待子代理完成通知。若确有阻塞，写准确错误与已完成文件，不隐瞒。你的任务结束不代表项目验收通过，Codex会独立检查并编译/运行。
