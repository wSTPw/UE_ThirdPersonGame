# IntroCpp 技术文档

这套文档同时服务于开发者阅读和 AI 持续接手。2026-10-17 首次基线来自当前 C++、配置及连接中编辑器的只读核对。它描述项目现状，并为后续技术方案和改动留出固定记录位置。

## 快速阅读

| 想做什么 | 先读 |
| --- | --- |
| 继续雌火龙首链只读取证与源码审查 | [2026-11-05首链审查](Reference/MHWI-Rathian-FirstChain-Audit-20261105.md)：纠正动作表起点、285项交叉一致、29根键/三UID及源码风险；首链仍未闭合，Sandbox修复暂缓 |
| 查看雌火龙总体还原方案、子代理细案与实施顺序 | [总方案](Plans/PLAN-20261031-002-rathian-restoration-master.md)：证据、AI、动画、战斗四细案及M0–M6；[本轮记录](Changes/CHG-20261031-002-rathian-restoration-plan.md)含73文件raw补取，技术候选待选择，玩法未实施 |
| 查看雌火龙方案四大板块完整性与缺失清单 | [完整性核对](Reference/MHWI-Rathian-Completeness-Check-20261102.md)：行为/数值/动画/音画逐项证据与缺口编号；[并行实施](Plans/PLAN-20261102-001-rathian-completeness-parallel.md)与[本轮记录](Changes/CHG-20261102-001-rathian-completeness-parallel.md)、[首链补录](Changes/CHG-20261031-003-rathian-first-chain.md) |
| 对外评审/交接（自包含简报） | [评审简报](Reference/MHWI-Rathian-Review-Brief-20261103.md)：项目现状/已闭合事实/未闭合清单/工具路线/时间预估/评审问题清单，单文件可直接外发 |
| **新 AI/新同事接手本项目** | [AI 交接文档](Plans/MHWI-Rathian-AI-Handoff-20261104.md)：环境与构建坑/项目规矩/代码地图/四板块取证总账/技术发现/阻塞/里程碑/高风险，自包含无需历史对话 |
| 接手项目、判断修改位置 | [项目架构](Architecture.md)、[模块索引 JSON](Reference/modules.json) |
| 修改物品、背包、快捷栏 | [背包系统](Systems/Inventory.md)、[接口契约](Interfaces.md) |
| 修改攻击、动画通知、敌人 | [战斗与 AI](Systems/Combat-AI.md) |
| 查询Ninja新动画替换、重定向、片段映射与窗口 | [Ninja动画配置](Systems/Ninja-Animation-Configuration.md)，2026-10-20制作，按用户要求未做完工后验证 |
| 查询MHW太刀、配套猎人模型及源素材转换 | [MHWI太刀训练模组](Systems/MHWI-LongSword.md)、[源素材](../ArtSource/ThirdParty/MHWLongSword/README.md)，独立地图与动作数据；验证见变更记录 |
| 查询现有解包方式、复现命令及解析失败处理 | [现有解包流程](Reference/MHWI-Unpacking-Workflow.md)：chunk 定向提取、素材转换、太刀/怪物参数读取、版本与覆盖边界 |
| 查询解包数据在哪、有多少、如何重抽与校验 | [解包数据管理](Systems/MHWI-Unpack-Data.md)、[采集工具说明](../Tools/MHW/README.md)：13个归档/51.13 GiB、171,615条路径、三级提取清单与入库边界；统计为2026-10-30只读复核，不是重新解包 |
| 查询雌火龙(em001)下位数据、肉质/发怒/疲劳数值与解码缺口 | [雌火龙下位数据](Reference/MHWI-Rathian-LR-Data-20261030.md)：300文件清单、状态/肉质参数；[格式续查](Reference/MHWI-Rathian-Format-Evidence-20261030.md)已读342条ACTP2与70条COL攻击原记录，LR资格/实战伤害/PBC耐久仍开放 |
| 查询雌火龙动画补齐、源库及引擎路径 | [雌火龙动画库](Systems/MHWI-Rathian-Animations.md)：19容器、848有效动作；新增824，旧24保留；逐条读回及12库骨轨抽检完成 |
| 接手雌火龙未解项（招式伤害、部位破坏） | [交接文档](Plans/MHWI-Rathian-Datamine-Handoff.md)：已更新ACTP2/COL读取结果与PBC三层结构；保留耐久、LR资格及完整时长缺口，可脱离历史对话接手 |
| 查询MHWI武器独立动画、完整TIML/FSM和逐帧还原缺口 | [源保真调查](Reference/MHWI-Source-Fidelity-Audit.md)、[阶段方案](Plans/PLAN-20261023-001-mhwi-source-fidelity.md)；2026-10-24只读调查，未修改正式玩法 |
| 查看Content/MHWI原版还原进度与交接 | [逐项开发台账](Plans/MHWI-Restoration-Progress.md)、[B10三项开发交付](Reference/MHWI-R06-Remaining-Development.md)；[B13/B14/B15验收及B16复验](Reference/MHWI-Acceptance-Update-20261026.md)：A05/A06已静态修复，B14构建/正式DA保存读回/22项离线检查通过，未PIE；35项总状态不变，运行由用户操作 |
| 验收R06/R28/R30当前交付 | [B20开发与调试](Reference/MHWI-B20-Animation-Development-20261027.md)：翻滚阻断修复，六段合格过渡与四链IK已实际接入；来源/低帧/姿态结果及原生未闭合边界分别记录；[开发前验收](Reference/MHWI-R06-R28-R30-Acceptance-20261027.md)保留历史 |
| 查询刀/刀鞘原版父骨及拔纳刀/居合挂点切换 | [原版挂接修复](Reference/MHWI-Native-Mount-20261028.md)：Main/Sub消费者与LMT功能骨30/47选择器闭合，原版背部功能骨2/比例0.8，导入坐标84组对照通过；标准挂接源码已替代腕骨/掌心拟合并通过UE 5.8构建。最终PIE握持画面验收由用户进行；原生切换旋转补偿、扩展层/状态继续开放。[B21旧报告](Reference/MHWI-Weapon-Mount-Evidence-20261028.md)保留历史，遗漏骨轨的旧结论已更正 |
| 查询R28基础移动与R30装配/IK补充取证及方案 | [B18取证报告](Reference/MHWI-R28-R30-Evidence-20261026.md)、[R28移动过渡方案](Plans/PLAN-20261026-004-mhwi-locomotion-transitions.md)、[R30四链IK方案](Plans/PLAN-20261026-005-mhwi-equipment-ik.md)；候选动作与骨链已有源依据，原生语义/solver 未完全闭合 |
| 查询原作太刀攻击碰撞证据及项目实现差异 | [B19武器碰撞取证](Reference/MHWI-Weapon-Collision-Evidence-20261026.md)：39/39动作碰撞轨UID匹配太刀COL；CLND类型1已追到节点工厂`cCollNodePl`，但CLGM几何/骨骼映射未闭合，原作数据暂不可直接用于忠实实现 |
| 查询MHWI全部离线静态取证结论 | [B17取证收尾](Reference/MHWI-Forensic-Completion-20261026.md)：EXE指纹匹配、48/48资源和19/19函数快照复验；发现5项`nativePC`覆盖，分别记录原版归档与当前覆盖；十项台账边界仍待语义闭合/运行观测 |
| 查看MHWI忠实还原重构审查与架构选项 | [忠实还原重构提案](Plans/PLAN-20261027-002-mhwi-fidelity-refactor.md)：目标已确认为原版忠实度；对照Epic UE 5.8官方方案，架构暂未选定，未改玩法代码/资产 |
| 查询剩余原生消费者及B12证据更正 | [B13取证](Reference/MHWI-Outstanding-Evidence-20261026.md)：Q/回旋/shell/回避/等待子链；10秒属颜色暂停、0.4秒属shell延迟；[B14实施记录](Changes/CHG-20261026-005-mhwi-evidenced-mechanics.md)；取消/转向/耐力/空间/IK及完整运行验收仍开放 |
| 查询源采样修复、独立武器轨道及公开帧表校准 | [实施现状](Reference/MHWI-Native-Fidelity-Implementation.md)、[实施方案](Plans/PLAN-20261024-001-mhwi-native-fidelity-implementation.md)；36段平行库、27处Montage迁移，完整装配和取消仍有缺口 |
| 批量读取原游戏太刀参数/输入条件/IK，避免逐动画抄数值 | [原始参数批处理](Reference/MHWI-Native-Parameter-Pipeline.md)、[批处理方案](Plans/PLAN-20261024-003-mhwi-native-parameter-pipeline.md)；425字段/164动作/4条IK链，21处属性白名单导入 |
| 查询MHWI太刀原版动作、派生、转向和登龙依据 | [行为资料核对](Reference/MHWI-LongSword-Behavior-Research.md)、[实施方案](Plans/PLAN-20261022-002-mhwi-longsword-behavior.md)、[本轮实施记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)；七项核心行为及四套/低帧回归完成，精确标定边界单列 |
| 修改 Widget、输入、蓝图配置 | [UI 与资产配置](Systems/UI-Assets.md) |
| 编译、验证、使用 MCP | [开发流程](Development.md)、[UE-MCP 说明](../Tools/ue-mcp/README.md) |
| 实现新功能或修改接口 | [维护工作流](Maintenance.md)、[功能方案模板](Templates/Feature-Plan.md) |
| 查询历史修改和风险 | [变更记录](Changes/README.md)、[已知问题](Known-Issues.md)、[架构决策](Decisions/README.md) |
| 追溯引擎升级 | [UE 5.8 升级记录](UE58-Upgrade.md) |

推荐 AI 首次阅读顺序：根目录 [AGENTS.md](../AGENTS.md) → 本页 → Architecture → 相关系统 → Interfaces → Known-Issues。后续只读取任务涉及的部分。

## 文档职责

| 目录/文件 | 内容与更新时机 |
| --- | --- |
| `Architecture.md`、`Systems/`、`Interfaces.md` | 当前实现；代码、配置或接口行为改变时更新 |
| `Reference/modules.json` | AI 可解析的模块、源码入口、关联接口、验证入口 |
| [编辑器观测快照](Reference/editor-observations.json) | 有日期的资产核对证据；仅作当时事实，不代替后续实查 |
| [Plans/](Plans/README.md) | 开发前的方案；明确状态，禁止用计划替代现状 |
| [Changes/](Changes/README.md) | 每次实质变更的事实记录和验证证据 |
| [Decisions/](Decisions/README.md) | 跨系统、影响长期维护的取舍及原因 |
| [Templates/](Templates/README.md) | 可复制的方案、接口、变更、ADR 模板 |

## 事实与历史边界

- 实现与头文件注释不一致时，以 `.cpp` 和运行证据为准，并记录差异。
- 编辑器快照的 `missingProperties`、`suspect` 是查询工具元数据；对子类不适用的字段或重定向资源可能触发它们，不应直接等同于资产损坏。
- 旧文档 [背包设计](../Source/IntroCpp/InventorySystem_DesignDoc.md)、[背包使用说明](../Source/IntroCpp/InventorySystem_README.md)、[武器设计](../Source/IntroCpp/WeaponSystem_DesignDoc.md)、[连击设计](../Source/IntroCpp/MeleeComboSystem_DesignDoc.md)、[敌人设计](../Source/IntroCpp/EnemySystem_DesignDoc.md) 保留为历史参考；其中的待实现代码、联网和扩展设想不自动成为现有能力。
- 此次文档工作没有修改玩法代码或保存蓝图资产，也没有重跑此前升级阶段的编译和 PIE。历史验证在升级记录中，本次验证在文档基线变更记录中。
