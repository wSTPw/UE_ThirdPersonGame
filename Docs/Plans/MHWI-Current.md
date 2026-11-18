# MHWI 当前开发计划

这是 MHWI 当前工作的统一入口。复杂批次的实施细节由本页链接；已完成方案与批次记录在 [Archive/MHWI/](../Archive/MHWI/README.md)。

现状见 [太刀训练模组](../Systems/MHWI-LongSword.md) 与 [雌火龙](../Systems/MHWI-Rathian.md)。
取证结论见 [太刀总账](../Reference/MHWI-LongSword-Evidence.md) 与 [雌火龙总账](../Reference/MHWI-Rathian-Evidence.md)。

## 当前结果：Basic基础版及玩家受击修正完成（2026-11-07）

最新修复：[玩家短受击](../Changes/CHG-20261107-003-hunter-hit-reaction.md)解决低帧下提前结束/首帧旧姿导致受击不可见。固定3FPS在旧版本FAIL、新版本PASS，验证最终骨姿及命中后真实位移；14场景16次运行121断言通过，含两持刀状态、连续输入、死亡和实际居合霸体消费者。未更换三档源片或原有伤害/力度。稳定证据见[清单](../../Tools/MHW/hunter-hit-reaction-repair-20261107.json)；旧24项的状态/编号检查不当作历史最终骨姿证明。

按用户指令暂停原作取证，先实现基础可玩版。巡逻、发现/移动选招、小咬、龙车、单火球、尾翻起飞接落地、骨骼盒判定、玩家三档受击、HP和死亡均已配置；24项真实PIE、101断言通过。源码三轮冻结Luna任务均ACCEPTED，主项目三次离线构建通过，最终编译后重启再执行全部本轮PIE。

- 运行入口：/Game/MHWI/Rathian/Basic/Maps/L_RathianBasic → Play。UE保持打开，PIE结束，包已保存；不要用旧原生summon入口替代已配置Basic蓝图。
- [当前交接](MHWI-Rathian-Handoff.md)列完整资产、源码/构建/审查、动画/盒/PIE结果和回退；[本轮记录](../Changes/CHG-20261107-002-rathian-basic-assets-pie.md)、[稳定配置/验收清单](../../Tools/MHW/rathian-basic-profile-20261107.json)可复核。
- 健康步行使用00_007，已撤下残血步态00_065；玩家纳刀/拔刀均验证Small/Medium/Large，龙车与尾翻共用Large起手、力度与轨迹不同。按用户选择保留00_081工程火球演出，原作站地单火球片段后续替换。
- 25个新增资产仅在Basic；875个原片/模型材质/用户原有脏训练地图与太刀DA文件hash不变。本轮完成不代表忠实THK/COL链通过；原作取证、Sandbox修复继续暂停，无待用户选择的基础版技术路线。
- 以下M0..M3为忠实线后续待办，保留历史静态证据边界；本轮没有恢复原作调查或运行验证。
## 一、目标与阶段

在 UE 5.8 的 IntroCpp 里用 em001 原作数据还原下位单人雌火龙战斗。两条线并行：

- **忠实线**：原作数据 + 原作 THK 决策，可宣称"还原"。当前卡在 THK 条件语义——社区命名覆盖 81.5% 条件段使用，**运行验证为 0**。
- **近似线 B1 / Basic**：em001动画素材 + 已知数值代理 + 工程参数/决策。基础版源码、资产及24项PIE已通过；精确原作规则未证，只能叫近似profile。

已确认的架构约束见 [ADR-0002](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md)：决策与执行分离、禁止两套执行逻辑、动作覆盖口径改为"已验证 ÷ 实际可达"。

## 二、里程碑（按执行顺序）

### M0 BITE动作83的查找与启动（2026-11-06，取证暂停）

按用户本轮指令先追 `THK raw83 → 动作键 → 对象查找 → BITE启动`，再推进下面的全量条件/下位清单。仅静态取证和现有源码审查；Sandbox修复保持暂缓，不启动/附加/注入原作或启动UE，确缺文件才另做定向解包。

- 使用更新后的 DevFlow v2 原生后端：Luna（`gpt-6-luna/high`）执行，另一个全新Luna会话独立审查，主代理核验高风险推断与缺口。
- 合同和可信检查已冻结：[task.json](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/task.json)、[检查器](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/verify_evidence.py)。候选只允许 `evidence.json/report.md`，不导入或执行候选代码。
- 固定输入副本在 `Saved/DevFlow/Rathian-BITE-Dispatch-20261106-input`，基线提交 `f5d5c1fb292f5a27595378d3f88428388c5620c3`；不要求清理或提交用户的原工作区。
- 先检查 `0x140269c30` 的键/返回对象，分别记录注册、查找、请求/enter和THK手递交；布局字段已有原生静态支持不等于启动链闭合。
- 验收为固定源hash、逐字节锚、4条桥接义务、源码行hash和明确未验证边界；9项确定性案例只证明报告可追溯，不证明原作运行等价。
- 工作副本不是操作系统/ACL隔离。未知边保持unknown，不用资格bool冒充真实证据。最多初次加两轮修复；只有ACCEPTED才导出，归档原始报告，现状页只汇总结论。
- 本轮结果：限定静态报告已ACCEPTED，9项冻结数据检查及全新Luna独立审查通过，2轮定向修订的未通过记录保留；[记录](../Archive/MHWI/Changes/CHG-20261106-001-rathian-bite-dispatch-devflow.md)。THK83→键、对象→enter、caller归属仍未闭合，键→对象仅candidate。下一轮先追THK递交及wrapper两个receiver，再追callback记录/enter；当前未缺原始文件，不解包、不动Sandbox。

- 社区检索补充：SPL签名已对应LaunchAction `0x141cc5360`、ForceAction `0x1413973b0`、已有DoAction `0x140269ce0`；下一步从这两个新入口追THK83输入/对象，见[固定来源与匹配](../../Tools/MHW/rathian-community-dispatch-20261106.json)。仅静态对应，无运行资格升级。

### M1 条件语义三栏表（本机可做，无需授权）——**已完成 2026-11-17**：26 类全"已证" 0 冲突，见[三栏表](../Reference/MHWI-Rathian-THK-Condition-Semantics-20261117.md)与[CHG-20261117-004](../Changes/CHG-20261117-004-mhwi-thk-semantics-arena-extract.md)

1. 以 `Scripts/MHWI/map_thk_function_semantics.py` 的输出（`Tools/MHW/rathian-thk-fexty-coverage-20261103.json`）为底
2. 对 27 类已命名项逐类校验参数取值范围是否与命名自洽：距离类应呈连续 cm 值、角度类应是 0~360 的对、布尔类参数必须全 0、rank 类必须 0~3
3. 产出"已证 / 冲突 / 未知"三栏表，落 `Docs/Reference/`
4. 31 类未命名项按使用次数排序，`0x5a`(186 次) 优先做参数聚类——`[4,30,10,32]` 这类整数很像枚举 ID，可与动作/区域/状态枚举对照

### M2 下位可达动作清单（本机可做，无需授权）——**v1 完成 2026-11-17**：985 发射段/147 动作 ID/111 命名，rank 门全为 HR/MR（无 LR 专属门）；CFG 剪枝待反编译器语义，见[清单](../../Tools/MHW/rathian-action-emission-inventory-20261117.json)与[CHG-20261117-004](../Changes/CHG-20261117-004-mhwi-thk-semantics-arena-extract.md)

1. 遍历 105 THK 节点树，找出被 `0xB8`（`is_rank`）门控的分支
2. 提取各分支内 emit 的 actionID
3. 与 em001 的 285 条动作表交叉（**旧"344 条"口径已撤回**，新布局见[总账第五节](../Reference/MHWI-Rathian-Evidence.md)）
4. 产出"LR 可达动作集"作为新分母

### M3 BITE 的 ActionSpec + 差异报告（需授权开原作）

按 `PLAN-20261103-001` 的字段清单落表；原作侧未观测字段一律写 `unobserved`。

### M4 Basic PIE（本轮已完成）

打开 /Game/MHWI/Rathian/Basic/Maps/L_RathianBasic → Play，使用已配置BP_RathianBasic及Hunter GameMode。24用例覆盖基础循环、4招命中/受击、躲空、墙体/低帧、飞行中断/死亡及火球清理，详见当前交接。原生MHWIRathianApproxPawn是未完整配置模板，旧训练图summon不作为Basic复现入口。

本轮未重新执行太刀完整连段/训练靶专项回归，相关已有功能不按本轮验证覆盖。
## 三、待用户拍板

| # | 事项 | 说明 |
| --- | --- | --- |
| 1 | 原作运行授权 | 任何启动原作的验证（运行时 dump / 受控观测）需先获明确同意。约定：离线、隔离、关闭 `nativePC` 覆盖、记录原始目录快照 |
| 2 | 工作区未提交项 | 首链、B1、Approx 代码与 10-30 以来的改动。分拣"用户已有工作 / 项目新增"属用户决定范围 |
| 3 | 技术路线选择 | Ghidra 类型恢复（3–6 GB / 1–2 会话 / 70–85% 成功率）vs LuaEngine 运行时观测 vs 停在候选级 |

## 四、风险

| 级别 | 风险 | 处置 |
| --- | --- | --- |
| 🔴 | 关键证据在 `Saved/`（被 gitignore）：`action-registry-dump`、`thk-all-raw.json`(16.8 MB)、`analysis-text.bin`(48.3 MB)、`default.fexty` | 可归档的证据 JSON 复制到 `Tools/MHW/`（该目录已跟踪）；大二进制登记为"可再生/本地必需"并留 hash |
| 🟠 | B1 腐化 | B1 是脚手架。每闭合一条 THK 语义就替换一层手写规则；若三个月后 B1 还在自己长功能，说明主线偏了 |
| 🟠 | 社区数据污染 | fexty 是社区命名可能错；`mhw-lmt-engine` 是新工具。用前标注来源与验证状态 |
| 🟡 | 第三方注入器安全 | LuaEngine 等来自社区，只在离线环境、明确授权下使用 |

## 五、术语

| 词 | 含义 |
| --- | --- |
| **THK** | MHWI 怪物 AI 的"思考表"，存的是决策程序（节点+条件+指令），不是数值。em001 有 105 个 + 2 thklst |
| **THK VM 语义** | 原作 exe 里解释执行 THK 指令的虚拟机及各指令真实业务含义。缺口 BEH-01 |
| **fexty** | Leviathon 的 THK 函数签名/命名定义，社区维护，给出 condition 候选名 |
| **ACTP2** | 动作参数表，342 记录 / 142 启用 / 4,295 属性项 |
| **LR 资格** | 有证据地判定哪些记录/动画/攻击真被下位配置消费。文件里有 ≠ 下位用，数组下标 ≠ 动作 ID。缺口 BEH-03 |
| **B1 / 近似 profile** | em001素材、已知数值代理及工程决策/执行；Basic参数不冒充原作已证规则 |
| **首链** | 第一条端到端链路：THK → 动作 → 位移 → 碰撞（咬击 83 / 冲撞 86-87） |
| **ActionSpec** | 单个动作的完整定义（资格/转向/动画/位移/碰撞窗/伤害/可打断/结束），决策层与执行层的共享契约 |
| **cross-verified** | 两个独立来源一致（如本机解析 + 公开数据库），可升入忠实 profile |

## 六、给接手者的一句话

数据已经到手，代码已经能跑，缺的是"看懂原作的决策"和"把候选变成已证"。别再从零逆向，先复用 fexty；别追全量覆盖，先定下位可达集；**别相信任何没跑过的验收**。
