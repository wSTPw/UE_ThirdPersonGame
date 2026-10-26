# 修改记录索引

本目录记录实际发生的实质修改。按 [维护工作流](../Maintenance.md) 使用 [变更模板](../Templates/Change-Record.md)。记录有日期、原因、文件/接口、实际验证、未完成项及回退。

| ID | 日期 | 主题 | 状态 |
| --- | --- | --- | --- |
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
