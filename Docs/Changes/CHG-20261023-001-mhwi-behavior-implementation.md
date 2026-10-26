# CHG-20261023-001：MHWI 动作行为与袈裟方向实施

- 状态：completed，七项核心行为已实现并保存；最终构建、四套PIE与10 FPS方向回归通过。原版精确标定及未覆盖地形边界见文末。
- 日期：2026-10-23；2026-10-22完成研究/方案并收到直接实施授权。
- 需求摘要：气刃突刺/见切映射、登龙阶段、转向、气刃插入续接、RMB循环、持刀翻滚后LMB，以及新增袈裟斩镜头/移动输入方向规则。
- 关联：PLAN-20261022-002；R-ANIM-005/006、R-COMBAT-007/008；MHWI-001/002/003/004。
- Git：工作区变更，未提交；大量用户已有修改独立保留。

## 当前事实

1. 已在原方案记录袈裟方向：镜头水平轴把移动输入转换到世界方向，再对选择前角色右轴投影；无输入或前后死区默认后退；三条片段不额外转身造成重复旋转。
2. 已按明确文件范围定向备份3份C++、author_assets、映射JSON、DA及两条Montage到 `Saved/MHWIImport/Backup-CHG007/`，含baseline-hashes.json；备份不意味着资产已改。
3. DeepSeek headless父会话 `session-e3dd6ab0-ccf0-45c3-bc57-21cdb1f6a567` 已通过原生subagent工具同批成功启动三个子代理，实际ID/所有权见[任务记录](../Plans/DSH-20261022-mhwi-behavior-task.md)。不只是多开三个CLI进程。
4. DSH的pwsh工具在Windows沙箱写入授权初始化失败，自身提权无审批通道；直接文件工具可用。已要求不得修复Windows权限或关闭沙箱，命令/UE操作由Codex按宿主权限执行。此处不是自动审批审查拒绝，也不代表需要用户修改项目权限。
5. 本轮首次MCP状态为disconnected，UE未运行；不得把此前运行中的PIE写成本轮状态。完成源码后按完整构建、启动和定向验证推进。

## 分工与边界

| 代理 | 文件所有权 | 验收责任 |
| --- | --- | --- |
| DeepSeek A | MHWICharacter.h/cpp、MHWIMovesetData.h；可新增MHWIBehaviorTests.cpp | Codex独立源码/编译/运行审查 |
| DeepSeek B | author_assets.py、moveset_mapping.json、新定向制作/端点分析脚本 | Codex串行制作资产、实际属性/姿态/持久化审查 |
| DeepSeek C | 新PIE/只读检查脚本 | Codex运行并审查真实输入、血量、方向、时序证据 |
| Codex | 方案、任务/CHG/现状文档、命令执行、审查/返修、资产操作、独立验收 | 代理退出0或自报成功不代替验收 |

三个子代理不得互写文件、不操作UE、不自行构建或安装依赖。默认的木桩被动、106/107映射、走跑203/090、武器挂接和REF_POSE根锁保留。新增参数有原版未确定的标定边界，明确标记项目调校。

## 已落地修改

| 文件/资产 | 变化与影响 |
| --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | 镜头相对移动意图、袈裟左右投影、普通/返回段转向窗口；翻滚来源姿态和有界恢复身份；登龙阶段/输入/物理/着地/一次授权与清理 |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h` | `FMHWIRoute::RequireDrawn`，转向起止/预算/速度及返回窗口；登龙速度、重力和下砸提交时刻反射参数 |
| `Source/IntroCpp/MHWIUI/MHWIHUD.cpp` | 仅操作提示文本：RMB循环、镜头相对袈裟、空中二次攻击下劈 |
| `Scripts/MHWI/author_assets.py`、`moveset_mapping.json`、`extract_moveset_mapping.py` | 制作源、140/170标签/源节点/窗口及SourcePlayRates随片段同步；提取器仅修两项定义，未全量重生成覆盖人工映射 |
| `Scripts/MHWI/author_behavior_corrections.py` | 定向制作32个正式动作身份/路由/物理参数，保留既有调校；序列段按显式MCP步骤制作，不在PIE中保存 |
| `Scripts/MHWI/audit_behavior_links.py` | 源动作连接候选姿态扫描、129实际尾帧/101裁剪时间与140/170来源交叉检查；首轮脚本把字典误作帧列表失败，修后重新执行通过 |
| `Scripts/MHWI/pie_behavior_corrections.py` | ground/direction/air/lifecycle异步套件、正式数据/实际输入/伤害/位移/阶段采样；实际运行发现的夹具错误需返修，不能以脚本存在作为通过 |
| `/Game/MHWI/Montages/M_SpiritThrust`、`M_ForesightSlash` | 分别改为170、140，整段长度同步；DA中碰撞84..97/60、70..80/60，见切反击/返回转向采用项目调校 |
| `/Game/MHWI/Montages/M_FadeSlashLeft`、`M_FadeSlashRight` | 运行发现原127/128左右标签与UE实际侧移相反；现分别改128/node9/action83、127/node8/action82，配套来源记录、制作器、DA窗口/取消/速度均已同步保存；方向选择函数/测试预期不反写掩盖 |
| `/Game/MHWI/Montages/M_RollStepSlash` | 新增DefaultSlot两段：129的0..29/60接101的48..150/60；总2.183333秒，混入0.10/混出0.12秒；旧StepSlash不覆盖 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | 新增两条SpiritCombo身份和RollStepSlash，SpiritI/II插入后续II/III；普通RMB循环；Roll持刀/纳刀分支；登龙除Rise外取消自动串段，Air/Strike真实物理驱动 |
| `/Game/MHWI/Montages/M_HelmAir`、`M_SpiritHelmBreaker` | 禁用自动混出，使空中尾帧保持到真实着地；制作源同样维护，段未改 |

接口细节见 [MHWI-001..005](../Interfaces.md)，当前参数/操作见 [系统文档](../Systems/MHWI-LongSword.md)。未修改插件、引擎、Ninja系统或第三方源模型/FBX。新增反射值已通过完整构建，正式DA显式写入；未重命名旧反射类/资产路径，无重定向迁移。

## 验证进度

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 多子代理 | 原生三子代理真实启动成功；父代理list_agents曾同时显示三个running | `Saved/MHWIImport/DSH-20261022/parent-events.jsonl`、dispatch.json |
| DSH shell | 失败，grantWrite；直接read/write仍可用，未修改系统权限 | 同父会话日志；检查命令由Codex补执行 |
| C++编辑器Target构建 | 初次272.03秒、DSH审查后87.03秒、窗口边界修复52.23秒、同帧输入最终修复20.19秒均成功；最新编译/链接完成 | `Saved/MHWIImport/Build-behavior-20261023-first.log`、`Build-behavior-20261023-final.log`、`Build-behavior-20261023-codex-final.log`、`Build-behavior-20261023-sameframe-final.log` |
| 编辑器与 MCP | 最终构建后新进程启动并连上 MCP；本轮 `project.get_status` 确认项目身份/连接 | 首次启动工具曾 120 秒超时但进程仍在启动，后续读回确认；不能把工具超时等同启动失败 |
| 正式资产制作/读回 | 见切140、突刺170、翻滚连接129+101与 DA 定向制作均保存；最终重启后翻滚连接仍为2.183333秒 | `behavior-corrections.json`、MCP `list_montage_segments`；BlendIn/Out另显式保存0.10/0.12秒 |
| 源连接端点/映射 | Blender 只读审计完成：101第48帧四骨平均误差0.5424cm；140/170节点/动作/碰撞映射通过 | `behavior-link-audit.json`、`blender-link-audit-after-round1.log`；不代表UE全帧视觉质量 |
| Python/JSON静态 | 五个制作/审计/验证脚本AST、映射JSON解析通过；Round2测试修复后再次AST通过 | 宿主实际执行，DSH自身shell未执行 |
| 七项行为/生命周期PIE | 最终all通过：410条断言记录（含逐帧重复），ground/direction/air/lifecycle四套完成；32个正式定义、17方向用例、真实成本/扣血/物理/生命周期；10 FPS方向104条通过 | `Saved/MHWIImport/PIE-behavior-all.json`，08:09:32..11:34；`PIE-behavior-direction-10fps-final.json`，08:05:04..32；历史失败和中间通过另存，不当作最终结果 |
| 文档检查/文本检查 | 最终check_docs.py通过：58 Markdown、393本地链接、12模块；限定git diff检查与26份源码/脚本/文档的no-index文本检查通过；5脚本AST与映射JSON解析通过 | 2026-10-23本轮宿主执行；cr-at-eol允许原CRLF，不重编码历史文件 |

### 运行验收续记

- 01:57:09..28，方向套件92项通过（18.656秒）：14个镜头/输入用例的动作身份、真实侧移/后退与yaw均符合预期；普通Thrust与派生RisingSlash各转25°；无方向只动镜头不转身。报告另存 `PIE-behavior-direction-pass-before-final-DA.json`，此时左右Montage已交换，但配套DA窗口/制作源尚未完成Round6同步，不能作为最终全部数据版本通过。
- 01:57:46..58:02，air准备链真实积槽/升白成功，随后G空挥未启动。静态发现准备链末大回旋会纳刀，air_miss_setup未再次确保持刀；当前失败属于夹具姿态前置条件缺失，未证明登龙业务失败。报告 `PIE-behavior-air-fail1-stance.json` 保留。
- Round6已交原B/C（左右映射整套来源同步、普通RMB独立六连与夹具预算），但DSH返回 `QUOTA: Insufficient Balance`，进程退出1。日志只有读/发消息，无本轮文件写入。Codex已向用户报告并询问接手实施或充值；未静默越过分工技能。原始日志 `DSH-20261022/round6-events.jsonl` 不含本项目凭据。
- 01:59:11..12，ground在 `ground_assets` 的 `EditorAssetLibrary.does_asset_exist` 失败；日志明确 `The Editor is currently in a play mode`，不是资源丢失。需把静态资产存在性检查移至PIE前，或在运行态检查正式DA已加载的Montage/Sequence引用。该轮报告已保存，未达到实际连招阶段。
- 已运行文档检查：57 Markdown、389本地链接、12模块通过；后续文档变更仍需最终重跑。
- 后续检查已重新完成为上表58/391/12；编辑器仍打开训练地图，PIE=false，内容/地图dirty均为0。各失败/成功报告均记录回调与测试清理。

### Codex接手后的实际进展

- 用户明确选择Codex接手。两名隔离职责的Codex子代理分别同步制作源和只读审查C++，主代理修测试夹具、集成并验收；未继续消耗DeepSeek余额。
- 左袈裟128的命中27..42/60秒、取消0.733333..1.436667；右127的命中27..43/60秒、取消0.75..1.47，SourcePlayRates随各自源记录清空空轨。伤害、收益、成本及路由保留。`fade_direction_corrections()`与`aerial_montage_corrections()`已实际MCP执行并返回saved=true。
- ground运行通过83项（07:43:10..44:37），含140实际姿态对照、三轮气刃插入升白黄红、独立普通RMB六连、持刀/纳刀翻滚出口和过期对照。该轮编辑器最小化导致约3 FPS，不将其扩大为正常帧率视觉质量通过。
- air首次到early-landing夹具时因3 FPS跨过25/60提交点而无法构造“提交前落地”，未判定为业务失败。恢复本项目编辑器窗口后07:46:54..47:32共84项通过：无输入Air约1.391秒、Rise约221.24cm；主动下劈7次独立伤害共147（白刃），速度最小-3083.33cm/s，白→无色；提交前落地0七段/0降色。
- 独立源码审查发现Montage结束从0重查窗口会放行窗口关闭后的输入。已记录输入实际Montage接收位置，求交起点不早于该位置，并让结束回调只处理真实尾段区间；Finish重置字段。新验证将对照窗口内/后的输入。完整构建 `Build-behavior-20261023-codex-final.log` 成功，52.23秒；后续使用新进程重新运行最终套件。
- 空中自动混出问题由实际属性读回确认后修复，新增5000cm高落差姿态尾帧回归；此条检查在上述84项之后新增，最终结果见后续记录。
- 新进程首轮all通过（07:51:50..53:44，114秒），四套392条断言记录（包含重复逐帧检查）：14方向矩阵、连招/翻滚、登龙、5000cm高落差尾帧保持72次、晚输入/窗口内输入、中断/死亡均通过。原报告另存 `PIE-behavior-all-pass-before-sameframe-input-fix.json`。训练场安全/见切又完成33项，报告mtime为07:54:46，非沿用历史结果。
- t.MaxFPS=10的持有方向矩阵通过92条记录，另存 `PIE-behavior-direction-10fps.json`。最初两个失败分别暴露夹具只按Slate时间等候、同帧Move尚未被游戏帧处理；在已注入后等待实际world tick，固定测试选择基底后通过。无玩法数值或方向期望被改写。
- 进一步增加真实“方向键+C同帧”及“松方向+C同帧”用例，旧二进制在 simultaneous A+C 下错误选择后退（pre/observed yaw均0），明确复现实际问题。UE本地EnhancedPlayerInput.cpp会把Started委托排在Triggered/Completed之前；现CommandStarted读取本帧已求值MoveAction后再选招，消除回调先后依赖。该修正需再次构建与回归；失败报告 `PIE-behavior-direction-fail7-sameframe-actual.json` 保留。
- 同帧修复最终编译20.19秒成功，新进程PID6784运行10 FPS方向回归104条/17用例通过（08:05:04..32），包括同时按下A+C、镜头90度W+C、松方向+C。松开用例曾因测试器先注入旧方向再注入零而失败；UE注入队列会累加，现每Slate tick在phase决定最终held状态后只注入一次，未改变真实方向预期。正式报告 `PIE-behavior-direction-10fps-final.json`。
- 扩展后的单次all耗时超过红刃原60秒，在Strike期间自然降色与登龙消耗叠加，旧测试错误期待只有一级变化。未改游戏衰减规则；夹具在剩余时间不足45秒时通过真实积槽/气刃链刷新刃色，再确认降色次数。组合失败证据 `PIE-behavior-all-fail1-natural-spirit-expiry.json` 保留。
- **最终完整回归**：08:09:32..11:34，最新二进制/正式资产/最终测试器all通过，410条断言记录含逐帧重复（boot22、ground61、direction82、air217、lifecycle28）。17种方向含同帧按下/松开；三轮气刃插入、普通RMB六连、翻滚三种出口均通过。自然Air约1.407秒、Rise约221.26cm；红刃下劈七次共168伤害、红→黄一级，提交前落地零七段/零降色；5000cm高落差保持73次尾帧采样；窗口内/后请求、中断/死亡通过。报告清理记录确认释放Move/Sprint、注销回调、恢复后台设置并结束PIE。
- 最终新二进制再次运行训练场安全/见切：`PIE-training-damage-verify.json`，mtime08:12:43，33项通过；玩家普通/气刃连招保持100HP，显式开启目标攻击后正常扣12HP、见切窗口拦截外部伤害，未设全局无敌。测试只改临时PIE目标实例。
- 补充渲染核对：`Saved/MHWIImport/behavior-final-hunter.png`为最终版本新PIE的SceneCapture，已查看角色/材质/纳刀模型可见性；只证明该静态场景，不是逐动画视觉或HUD截图。临时Capture Actor已销毁；PIE已结束，编辑器保留训练地图。
- 最终机器可读快照 `Saved/MHWIImport/Behavior-final-validation.json` 已检查三份报告passed及mtime晚于最新构建，记录源码SHA256、构建日志、410/104/33条断言、32正式动作和明确未覆盖项。末次MCP读回：PIE=false，内容/地图dirty=0，t.MaxFPS数值恢复0，Slate.bAllowThrottling=1；无项目/全局ini变更。

### 接手后的处理范围

1. 用户已通过选择“由Codex接手完成（推荐）”明确授权剩余实施，Codex继续返修与验收；不再调用余额不足的DeepSeek。按互不重叠文件范围安排制作源修改与只读C++审查子代理，主代理负责测试脚本/UE集成/实际验收。
2. 已完成128/127制作源、DA窗口/SourcePlayRates同步，RollStepSlash混合值维护和正式保存；空中尾帧属性同样已持久化。
3. 已修PIE资产存在性检查、升色后重新确保持刀、真实积槽链预算/进展、独立普通RMB六连。正式成本、伤害窗口和判定期望未用零值或假数据替换。
4. 四套与10 FPS同帧按下/松开回归已在最新二进制完成。全量地形/原版精确视觉标定属于下述明确未验证范围，不把源姿态核对与当前调校的运行通过扩大为逐帧复刻。

## 遗留与回退

精确原版角度、运动参数调用关系/倍率尚无完整一手标定，不把本地初值当作原版常数。空中转向目前只改变攻击朝向，不重算水平漂移；自定义重力体积、低顶、斜坡、目标顶部及独立UnPossessed/EndPlay场景仍需专项验证。

启动时C盘原Zen缓存写入HTTP507（剩余空间低于缓存阈值）。本轮仅为编辑器进程传入 `-LocalDataCachePath="E:/Unreal Projects/IntorCpp/Saved/DerivedDataCache"`，新Zen状态OK；未删除缓存、修改全局设置或项目ini。后续启动如不传该参数，可能再次命中原C盘缓存限制。

回退仅依据baseline-hashes和本次资产清单恢复明确文件；禁止git reset/clean或覆盖无关未提交资产。Backup-CHG007-round6另存左右Montage、DA、映射JSON、定向制作器与提取器的Round6前版本。初始备份不包含后来扩展的HUD提示/提取器两项定义，不能宣称可整目录自动回退；这两处按本轮限定diff恢复，新增RollStepSlash需确认无新用户引用后才移除。资产恢复应在编辑器关闭且确认相关dirty内容已处理后进行。

## 文档入口

[研究](../Reference/MHWI-LongSword-Behavior-Research.md)、[方案](../Plans/PLAN-20261022-002-mhwi-longsword-behavior.md)、[任务会话](../Plans/DSH-20261022-mhwi-behavior-task.md)、[变更索引](README.md)。
