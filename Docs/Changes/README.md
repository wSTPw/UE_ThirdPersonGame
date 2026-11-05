# 修改记录索引

本目录记录实际发生的实质修改。按 [维护工作流](../Maintenance.md) 使用 [变更模板](../Templates/Change-Record.md)。记录有日期、原因、文件/接口、实际验证、未完成项及回退。

| ID | 日期 | 主题 | 状态 |
| --- | --- | --- | --- |
| CHG-20261105-003 | 2026-11-05 | [雌火龙首链只读取证与源码审查](CHG-20261105-003-rathian-first-chain-audit.md) | completed（审查/文档）；动作表旧口径撤回、根轨/三UID复核；整链仍partial |
| CHG-20261105-002 | 2026-11-05 | [核对官方源并继续修复Sandbox](CHG-20261105-002-windows-official-source-repair.md) | partial；WU修复曾Healthy、SFC无违规；Sandbox仍因OC压缩元数据失败，完整源待核 |
| CHG-20261105-001 | 2026-11-05 | [监督组件库修复与Sandbox恢复](CHG-20261105-001-windows-component-store-repair.md) | partial；修复退出1/0x800f0915缺源；Repairable/Disabled，无重启/关机 |
| CHG-20261104-004 | 2026-11-04 | [选择Windows Sandbox及启用失败诊断](CHG-20261104-004-windows-sandbox-enablement.md) | partial；组件存储Repairable，功能仍Disabled；未修复/重启 |
| CHG-20261104-003 | 2026-11-04 | [DevFlow接手与THK审计任务准备](CHG-20261104-003-devflow-thk-audit-preparation.md) | partial；doctor/prepare通过，隔离环境待就绪，执行模型调用0 |
| CHG-20261104-002 | 2026-11-04 | [Approx 层编译修复（五项修复批次从未编译成功）](CHG-20261104-002-rathian-approx-compile-fix.md) | completed；4类UE5.8错误修完，`Result: Succeeded`；PIE未执行 |
| CHG-20261104-001 | 2026-11-04 | [雌火龙项目 AI 交接文档](CHG-20261104-001-rathian-ai-handoff.md) | completed（文档）；新增自包含交接页；发现 Saved/ 被忽略致关键证据未纳管的风险并记录 |
| CHG-20261103-002 | 2026-11-03 | [外部评审采纳：fexty条件映射复用与路线修订](CHG-20261103-002-rathian-review-adoption.md) | completed-scope；27/58条件类型、81.5%使用覆盖实证；路线/时间表修订 |
| CHG-20261103-001 | 2026-11-03 | [NUM-03双源闭合、运行时路线更新与评审简报](CHG-20261103-001-rathian-review-brief.md) | completed（文档）；部位映射cross-verified；R2定为LuaEngine；评审简报可外发 |
| CHG-20261102-004 | 2026-11-02 | [B1近似profile实施批次一（AP-0~4代码）](CHG-20261102-004-rathian-approx-implementation.md) | partial；代码落地+UE5.8构建通过；PIE交战验收与太刀回归待用户 |
| CHG-20261102-003 | 2026-11-02 | [原生动作注册表转储与B1方案交付](CHG-20261102-003-rathian-approximate-profile-plan.md) | completed-scope；344条注册表+命名空间修正；B1方案交付 |
| CHG-20261102-002 | 2026-11-02 | [THK VM 条件语义静态取证（负结果固化）](CHG-20261102-002-rathian-vm-semantics-recon.md) | completed-scope；载体/结构/偏移/统计闭合+跳转表排除；逐函数语义阻塞于RE工具链，交接文档已出 |
| CHG-20261102-001 | 2026-11-02 | [雌火龙方案完整性核对、音画细案补全与四模块并行实施](CHG-20261102-001-rathian-completeness-parallel.md) | completed-scope；核对页+4工作包交付+首链UE5.8构建通过；unknown按证据保留 |
| CHG-20261031-003 | 2026-10-31（11-02补录） | [雌火龙首条THK→动作→移动→碰撞链路实施](CHG-20261031-003-rathian-first-chain.md) | partial；THK解析资格通过+首链代码落地（未提交）；构建/PIE/VM语义未闭合 |
| CHG-20261031-002 | 2026-10-31 | [雌火龙总体/分工细案与73文件外部证据补取](CHG-20261031-002-rathian-restoration-plan.md) | completed-scope；仅方案及raw，玩法未实施，方向待选择 |
| CHG-20261031-001 | 2026-10-31 | [雌火龙旧24条时长修复](CHG-20261031-001-rathian-legacy-duration.md) | completed；24/24按源帧数重导，原路径/对象/骨架/引用列表核对通过 |
| CHG-20261030-023 | 2026-10-30 | [雌火龙遗漏动画补齐](CHG-20261030-023-mhwi-rathian-animation-completion.md) | completed-scope；新增824，共848；旧24保留；集合/骨架/时长/12库骨轨读回通过 |
| CHG-20261030-022 | 2026-10-30 | [雌火龙动画导出并导入引擎](CHG-20261030-022-mhwi-rathian-animations.md) | completed（首批）；em001_00.lmt共111动作，首批24个已导入挂骨架，语义映射未解 |
| CHG-20261030-021 | 2026-10-30 | [按用户决定以雌火龙为目标，文档口径与文件名更正](CHG-20261030-021-mhwi-rathian-rename.md) | completed（文档）；4份在用文档重命名，20文件引用替换，历史CHG保持原义 |
| CHG-20261030-020 | 2026-10-30 | [编号更正：em001=雌火龙，火龙是em002；修RMT采样类型](CHG-20261030-020-mhwi-monster-id-correction.md) | corrective；此前全部"火龙"数值实为雌火龙；em002已提取257文件/84.21MiB，待重跑解析与转换 |
| CHG-20261030-019 | 2026-10-30 | [按视口反馈调光并隐藏损坏部位网格](CHG-20261030-019-mhwi-rathalos-lighting-damage-mesh.md) | completed（场景调整）；撤点光+天光降至1.5，damage槽换M_HiddenSlot；关卡未保存 |
| CHG-20261030-018 | 2026-10-30 | [恢复火龙材质显示（槽位丢失+光照）](CHG-20261030-018-mhwi-rathalos-material-restore.md) | completed（显示链路）；Actor四槽覆盖已写入，新增可移动补光；截图接口冻结未能目视确认 |
| CHG-20261030-017 | 2026-10-30 | [材质收尾：CMML/FM评估、眼睛补齐、场景恢复](CHG-20261030-017-mhwi-rathalos-material-finalize.md) | completed（材质）；CMML/FM经测量判定不接，4材质已保存，尾巴Actor重导后已恢复 |
| CHG-20261030-016 | 2026-10-30 | [接入RMT粗糙度/金属度，材质链路补齐](CHG-20261030-016-mhwi-rathalos-rmt-material.md) | completed（材质）；R→Roughness、G→Metallic，3材质已保存；CMM/FM未接 |
| CHG-20261030-015 | 2026-10-30 | [修复火龙白模（自发光误接）与关卡光源竞争](CHG-20261030-015-mhwi-rathalos-white-material-fix.md) | completed（材质/光照）；Emissive断开后正常上色，关卡未保存 |
| CHG-20261030-014 | 2026-10-30 | [火龙模型与贴图导入引擎](CHG-20261030-014-mhwi-rathalos-ue-import.md) | completed（导入）；2网格/2骨架/12贴图/4材质落盘，骨骼142 vs Blender141待核对 |
| CHG-20261030-013 | 2026-10-30 | [火龙模型转FBX（本体+尾巴）](CHG-20261030-013-mhwi-rathalos-model-fbx.md) | completed（转换）；141骨/25网格/67,445面回读一致；贴图未进FBX |
| CHG-20261030-012 | 2026-10-30 | [格式解析与取证流程归纳](CHG-20261030-012-mhwi-workflow-format-methods.md) | completed（文档）；方法选择/执行顺序/成功标准与适用边界 |
| CHG-20261030-011 | 2026-10-30 | [火龙ACTP2/COL攻击字段与PBC嵌套读取](CHG-20261030-011-mhwi-rathalos-format-evidence.md) | completed（本批离线读取）；342动作/70攻击原字段，PBC三层确认；耐久、LR资格与实战仍partial |
| CHG-20261030-010 | 2026-10-30 | [新增火龙未解项交接文档](CHG-20261030-010-mhwi-rathalos-handoff.md) | completed（文档）；自包含交接，含三个未解项、已否决路线与验收口径 |
| CHG-20261030-009 | 2026-10-30 | [em_pbc记录步长确认与actp2结构探查](CHG-20261030-009-mhwi-pbc-actp2-probe.md) | completed（结构探查）；步长48经4文件比对确认，字段语义未定；actp2周期过弱未解析 |
| CHG-20261030-008 | 2026-10-30 | [火龙状态值/口水硬/陷阱解码与em_pbc结构探查](CHG-20261030-008-mhwi-rathalos-status-values.md) | completed（解码）；dtt_eda零尾通过并发布状态值，em_pbc仅结构可见未出阈值 |
| CHG-20261030-007 | 2026-10-30 | [解析器布局hash校验与流程页shlp口径修正](CHG-20261030-007-mhwi-parser-pin-check.md) | completed（工具/文档）；9份布局校验通过，解析结果不变，R-DATA-002降为partial |
| CHG-20261030-006 | 2026-10-30 | [整理现有解包方式与复现流程](CHG-20261030-006-mhwi-unpacking-workflow.md) | completed（文档）；三批488条尺寸/hash复核，未重抽或运行解析/游戏；记录清单与解析边界 |
| CHG-20261030-005 | 2026-10-30 | [火龙(em001)下位数据解包与首批解码](CHG-20261030-005-mhwi-rathalos-datamine.md) | partial，300文件/76.97MiB提取；发怒、疲劳、部位肉质已解码；招式/AI/部位破坏未解码，无伤害数值 |
| CHG-20261030-004 | 2026-10-30 | [新增MHWI解包数据管理与统计文档](CHG-20261030-004-mhwi-unpack-data-doc.md) | completed（文档）；13包/171,615条索引的只读复核，未重抽；入库边界差异仅记录未处置 |
| CHG-20261030-003 | 2026-10-30 | [气刃连段突刺、见切续查与攻击判定说明](CHG-20261030-003-mhwi-spirit-thrust-routes.md) | partial，三条路线已保存；游戏测试由用户，见切精确许可续查 |
| CHG-20261030-002 | 2026-10-30 | [太刀五项操作修正](CHG-20261030-002-mhwi-five-controls.md) | partial，四项已实施；方向21例通过，突刺/出刀待用户手测，见切精确窗口开放 |
| CHG-20261030-001 | 2026-10-30 | [删除旧UEBridgeMCP插件遗留归档](CHG-20261030-001-mhwi-retire-legacy-bridge.md) | completed（清理）；唯一副本永久删除，当前UE_MCP_Bridge未受影响 |
| CHG-20261028-001 | 2026-10-28 | [MHWI太刀/刀鞘原版父骨选择、背部配置与导入坐标修复](CHG-20261028-001-mhwi-native-equipment-mount.md) | partial，源码和编译完成，用户验收待进行；未执行自动PIE握持验收，原生旋转补偿/扩展状态保留 |
| CHG-20261027-007 | 2026-10-27 | [MHWI太刀攻击姿态右手握点约束](CHG-20261027-007-mhwi-hand-grip-ik.md) | completed（项目适配）；Editor构建通过；38项动画消费者PIE及30 FPS武器交接PIE 3750项检查通过 |
| CHG-20261027-006 | 2026-10-27 | [MHWI忠实还原重构审查提案与官方方案先行约定](CHG-20261027-006-mhwi-fidelity-refactor-proposal.md) | completed（文档/规则）；提出有来源候选及决策门，未选架构、未改玩法代码/资产 |
| CHG-20261027-005 | 2026-10-27 | [武器碰撞/加载链证据JSON归档到已跟踪目录](CHG-20261027-005-mhwi-evidence-json-archive.md) | completed（归档）；副本入库、脚本输出改到Tools/MHW，取证结论未复现 |
| CHG-20261027-004 | 2026-10-27 | [翻滚阻断、六段过渡与四链IK实装及调试](CHG-20261027-004-mhwi-roll-locomotion-ik.md) | partial，项目消费者实装；6轮PIE通过、完整原生边界保留 |
| CHG-20261027-003 | 2026-10-27 | [R06/R28/R30专项验收](CHG-20261027-003-mhwi-r06-r28-r30-acceptance.md) | completed（审查）；三项完整交付不通过，87行/75动画文件存在性核对，历史运行报告缺失，未启动UE/PIE |
| CHG-20261027-002 | 2026-10-27 | [MHWI碰撞加载工厂追踪与可用性裁决](CHG-20261027-002-mhwi-collision-loader-trace.md) | completed（静态追到 `cCollNodePl`）；几何/Bone映射未闭合，原作数据暂不可直接作为实现依据 |
| CHG-20261027-001 | 2026-10-27 | [R06/R28/R30动画全集覆盖处理与交接](CHG-20261027-001-mhwi-animation-coverage.md) | partial，R06修复及14项PIE通过；R28/R30数据层与逐项处置，全部运行覆盖未完成 |
| CHG-20261026-011 | 2026-10-26 | [MHWI太刀武器碰撞静态取证](CHG-20261026-011-mhwi-weapon-collision-evidence.md) | completed（离线关联完成）；形状/骨骼空间/运行时消费者未闭合，R18保持取证中 |
| CHG-20261026-010 | 2026-10-26 | [MHWI R28/R30补充取证与实施方案](CHG-20261026-010-mhwi-r28-r30-forensics-and-plans.md) | completed（取证/方案）；玩法未实施，原生solver语义保留 |
| CHG-20261026-009 | 2026-10-26 | [MHWI台账离线取证收尾](CHG-20261026-009-mhwi-forensic-completion.md) | completed（离线静态范围）；48项资源和19个函数快照复核通过，十项玩法语义/运行边界保留 |
| CHG-20261026-008 | 2026-10-26 | [MHWI B13/B14/B15更新验收](CHG-20261026-008-mhwi-update-acceptance.md) | completed，审查完成；整体验收不通过，A05正式DA未迁移/A06登龙缺补排；49项静态及B13初始重建PASS，未运行 |
| CHG-20261026-007 | 2026-10-26 | [B14/B15提交的编译错误修复](CHG-20261026-007-mhwi-build-fix.md) | completed，`uint32`蓝图类型与`RemoveAt`签名两处修复；编译通过，未PIE |
| CHG-20261026-006 | 2026-10-26 | [B15 MHWI原游戏PC键盘适配](CHG-20261026-006-mhwi-keyboard-adaptation.md) | partial，键盘代码与49项静态检查完成；未编译/PIE，手柄A02保留 |
| CHG-20261026-005 | 2026-10-26 | [B14机制实施、登龙七段补排与正式DA迁移](CHG-20261026-005-mhwi-evidenced-mechanics.md) | partial，A05/A06静态修复、构建和22项离线校验通过；未运行PIE，取消/空间等边界保留 |
| CHG-20261026-004 | 2026-10-26 | [B13剩余原生消费者与两项旧依据更正](CHG-20261026-004-mhwi-outstanding-evidence.md) | partial，静态子链补证；十项未全关闭，玩法未修复，未运行 |
| CHG-20261026-003 | 2026-10-26 | [MHWI台账静态验收与运行交接](CHG-20261026-003-mhwi-static-acceptance.md) | completed，审查完成；4项静态问题未修，R06降为部分完成；51项离线PASS，运行由用户操作 |
| CHG-20261026-002 | 2026-10-26 | [B12全台账35项逐项处置与可证据落地](CHG-20261026-002-mhwi-ledger-sweep.md) | partial，10项实施/16项部分完成/10项取证/1项待开发；增量编译通过，正式DA两处保存/读回通过；未运行PIE |
| CHG-20261026-001 | 2026-10-26 | [B11见切缺失出口B→突刺、R+A→登龙突刺](CHG-20261026-001-mhwi-foresight-exits.md) | completed，开发完成；正式DA保存/读回通过；未测试（精确窗口仍属R07） |
| CHG-20261025-005 | 2026-10-25 | [B10真实来源、专用入口与原生混合/独立时钟完整开发](CHG-20261025-005-mhwi-r06-remaining.md) | completed，开发完成；未编译/测试 |
| CHG-20261025-004 | 2026-10-25 | [B09真实来源交接、主段保护与统一入帧](CHG-20261025-004-mhwi-r06-source-clock.md) | partial，前置玩法/专用入口/混合门控仍开放；未编译/测试 |
| CHG-20261025-003 | 2026-10-25 | [B08角色连接接入、112主段和正式时钟迁移](CHG-20261025-003-mhwi-r06-character-playback.md) | partial，角色已接入源码；前置玩法/混合尚有缺口；未编译/测试 |
| CHG-20261025-002 | 2026-10-25 | [B07原生连接控制核心、124身份记录及26段平行库](CHG-20261025-002-mhwi-link-motion-core.md) | partial，正式角色未消费；未编译/测试 |
| CHG-20261025-001 | 2026-10-25 | [B06链式函数、门控解除及本机Phase字段](CHG-20261025-001-mhwi-native-transition-gate.md) | partial，工具待验证；具体退出/选择未定，不测试 |
| CHG-20261024-011 | 2026-10-24 | [B05左右FSM来源修正与连接逻辑取证](CHG-20261024-011-mhwi-native-connector-logic.md) | partial，已修来源/待测试；原生规则仍取证，新增连接0条 |
| CHG-20261024-010 | 2026-10-24 | [B04连接入帧原表及逐条取证](CHG-20261024-010-mhwi-connector-evidence.md) | partial，30节点32引用；既有129原值接入，新增连接0条 |
| CHG-20261024-009 | 2026-10-24 | [B03基础循环动画迁移](CHG-20261024-009-mhwi-locomotion-animation.md) | completed，8资产及7.766秒短冒烟通过；完整移动还原仍开放 |
| CHG-20261024-008 | 2026-10-24 | [B02气刃弱强与有序派生修复](CHG-20261024-008-mhwi-spirit-branches.md) | completed，本批限定范围；原值/构建/18秒短冒烟通过，复杂验证后置 |
| CHG-20261024-007 | 2026-10-24 | [还原开发台账与B01原生基础修复](CHG-20261024-007-mhwi-native-basics.md) | partial，完整编译/专项/边界/地面回归通过；确定修复已落地，完整还原和长测继续开放 |
| CHG-20261024-006 | 2026-10-24 | [Content/MHWI原版还原批判性审查与修改方案](CHG-20261024-006-mhwi-restoration-review.md) | completed，33项问题及阶段方案；349资产文件只读核对未变，未实施玩法修改 |
| CHG-20261024-005 | 2026-10-24 | [太刀武器位置与交接收尾](CHG-20261024-005-mhwi-weapon-placement.md) | completed，此轮实现及编译通过；最终UE运行调试由用户验收 |
| CHG-20261024-004 | 2026-10-24 | [原始参数批处理与21处属性导入](CHG-20261024-004-mhwi-native-parameter-pipeline.md) | completed，此批处理范围；425字段/164动作/4条IK，资源回归和磁盘读回通过，未知控制逻辑仍单列 |
| CHG-20261024-003 | 2026-10-24 | [独立防御、逐路由窗口与连续交接](CHG-20261024-003-mhwi-defense-routes-transfer.md) | partial，构建与防御911断言通过；三色共享骨轨已适配，完整视觉/路由验收待续 |
| CHG-20261024-002 | 2026-10-24 | [MHWI源采样修复、独立武器轨道与公开资料替代路线](CHG-20261024-002-mhwi-native-fidelity-implementation.md) | partial，36段合格/27处迁移，内部武器事件和限定回归通过；完整交接与取消待校准 |
| CHG-20261024-001 | 2026-10-24 | [MHWI武器轨道、原生时序与还原差距调查](CHG-20261024-001-mhwi-source-fidelity-audit.md) | completed，完整源审计/正式资产只读核对与后续方案；正式还原未实施 |
| CHG-20261023-001 | 2026-10-23 | [MHWI动作行为与袈裟方向实施](CHG-20261023-001-mhwi-behavior-implementation.md) | completed，七项核心行为保存；最终构建、四套PIE及10 FPS方向通过，精确标定仍有边界 |
| CHG-20261022-006 | 2026-10-22 | [MHWI太刀六项行为资料与实施方案](CHG-20261022-006-mhwi-behavior-research.md) | completed，仅调查/方案；玩法未改，精确转向与空中参数对应待标定 |
| CHG-20261022-005 | 2026-10-22 | [训练场默认关闭木桩自动攻击](CHG-20261022-005-mhwi-training-damage.md) | completed，7项来源诊断与33项训练安全PIE检查通过 |
| CHG-20261022-004 | 2026-10-22 | [MHWI 动画映射与普通攻击派生修正](CHG-20261022-004-mhwi-animation-corrections.md) | completed，39项PIE与12项磁盘重载检查通过 |
| CHG-20261022-003 | 2026-10-22 | [MHWI 武器与刀鞘挂接修正](CHG-20261022-003-mhwi-weapon-attachment.md) | completed，保存并完成45项挂接PIE检查 |
| CHG-20261022-002 | 2026-10-22 | [MHWI 太刀训练模组](CHG-20261022-002-mhwi-longsword-module.md) | partial，战斗回归已通过；视觉收尾中 |
| CHG-20261022-001 | 2026-10-22 | [MHW太刀与配套猎人素材采集](CHG-20261022-001-mhw-longsword-source-assets.md) | completed，素材获取/转换；UE接入与效果待处理 |
| CHG-20261020-003 | 2026-10-20 | [移动根运动缓存与衔接修复](CHG-20261020-003-locomotion-root-cache-fix.md) | completed，配置已保存；运行效果待确认 |
| CHG-20261020-002 | 2026-10-20 | [Ninja Root Motion适配](CHG-20261020-002-ninja-root-motion.md) | completed，制作保存完成；未做完工后验证 |
| CHG-20261020-001 | 2026-10-20 | [Ninja动画重定向与替换](CHG-20261020-001-ninja-animation-replacement.md) | completed，制作保存完成；按用户要求未做完工后验证 |
| CHG-20261019-005 | 2026-10-19 | [角色动作调度与事务提交实施](CHG-20261019-005-character-actions-implementation.md) | partial，动作核心已验证；MM待用户资源 |
| CHG-20261019-004 | 2026-10-19 | [动作重构方案加入Motion Matching](CHG-20261019-004-motion-matching-plan.md) | completed，仅方案 |
| CHG-20261019-003 | 2026-10-19 | [动作管理审查与重构方案交付](CHG-20261019-003-action-refactor-proposal.md) | completed，仅方案 |
| CHG-20261019-002 | 2026-10-19 | [暗黑幻想标题页](CHG-20261019-002-dark-fantasy-title-screen.md) | completed |
| CHG-20261019-001 | 2026-10-19 | [像素风格主菜单](CHG-20261019-001-main-menu-pixel-ui.md) | completed |
| CHG-20261017-002 | 2026-10-17 | [项目省 Token 技能与 UE 精简路由](CHG-20261017-002-token-efficient-skills.md) | completed |
| CHG-20261017-001 | 2026-10-17 | [技术文档与 AI 维护基线](CHG-20261017-001-documentation-baseline.md) | completed |

此前已完成但未使用本编号体系的工作：[UE 5.8 升级、旧插件卸载、新 UE-MCP 安装与验证](../UE58-Upgrade.md)。此链接保留原始记录，不伪造新提交或新的验证时间。
