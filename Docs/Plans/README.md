# 技术方案索引

这里保存开发前的目标方案。`draft` 表示目标设计，`implemented` 表示已按对应变更记录落地；方案交付不代表已获授权实施全部玩法改动。

新增时复制 [功能方案模板](../Templates/Feature-Plan.md)，使用 `PLAN-YYYYMMDD-NNN-主题.md`，并在下表追加一行。实现完成后更新状态与 CHG 链接，同时更新现状文档。

| ID | 主题 | 状态 | 变更记录 |
| --- | --- | --- | --- |
| [PLAN-20261026-003](PLAN-20261026-003-mhwi-keyboard-adaptation.md) | B15 MHWI原游戏PC键盘适配 | implemented-scope，代码与49项静态检查完成；未编译/PIE，手柄A02保留 | [B15记录](../Changes/CHG-20261026-006-mhwi-keyboard-adaptation.md) |
| [PLAN-20261026-001](PLAN-20261026-001-mhwi-outstanding-evidence.md) | B13剩余原生消费者取证 | partial，子链归档；十项完整缺口未关闭，未运行 | [B13记录](../Changes/CHG-20261026-004-mhwi-outstanding-evidence.md) |
| [PLAN-20261025-005](PLAN-20261025-005-mhwi-r06-remaining.md) | B10完成R06剩余三项及资源/台账交付 | implemented，开发完成；未编译/测试 | [B10记录](../Changes/CHG-20261025-005-mhwi-r06-remaining.md) |
| [PLAN-20261025-004](PLAN-20261025-004-mhwi-r06-completion.md) | B09真实来源、主段保护与统一入帧 | partial，完整R06未完成；未编译/测试 | [B09记录](../Changes/CHG-20261025-004-mhwi-r06-source-clock.md) |
| [PLAN-20261025-003](PLAN-20261025-003-mhwi-r06-character-playback.md) | B08角色连接播放和原生112绑定 | implemented-scope，完整R06仍开放；未编译/测试 | [B08记录](../Changes/CHG-20261025-003-mhwi-r06-character-playback.md) |
| [PLAN-20261025-002](PLAN-20261025-002-mhwi-r06-native-consumer.md) | B07原生连接控制核心和独立片段库 | partial，角色播放适配尚未接入；未测试 | [B07记录](../Changes/CHG-20261025-002-mhwi-link-motion-core.md) |
| [PLAN-20261025-001](PLAN-20261025-001-mhwi-native-transition-gate.md) | B06链式函数、通用门控与本机Phase字段 | partial，工具待验证；武器规则取证中 | [B06记录](../Changes/CHG-20261025-001-mhwi-native-transition-gate.md) |
| [PLAN-20261024-009](PLAN-20261024-009-mhwi-native-connector-logic.md) | B05原生连接取证与左右来源 | partial，来源修复待测试；原生退出/选择未定 | [B05记录](../Changes/CHG-20261024-011-mhwi-native-connector-logic.md) |
| [PLAN-20261024-008](PLAN-20261024-008-mhwi-connector-evidence.md) | B04连接动画逐条原始取证 | partial，入帧表已读、退出待取证 | [B04记录](../Changes/CHG-20261024-010-mhwi-connector-evidence.md) |
| [PLAN-20261024-007](PLAN-20261024-007-mhwi-locomotion-animation.md) | B03基础循环动画源采样迁移 | implemented，限定范围 | [B03记录](../Changes/CHG-20261024-009-mhwi-locomotion-animation.md) |
| [PLAN-20261024-006](PLAN-20261024-006-mhwi-source-branches.md) | B02原生气刃弱/强及接续分支 | implemented，本批限定范围；复杂验证后置 | [B02记录](../Changes/CHG-20261024-008-mhwi-spirit-branches.md) |
| [PLAN-20261024-005](PLAN-20261024-005-mhwi-original-restoration.md) | Content/MHWI以原版为目标的完整还原 | in-progress，已授权开发；[逐项状态](MHWI-Restoration-Progress.md) | [审查交付](../Changes/CHG-20261024-006-mhwi-restoration-review.md) |
| [PLAN-20261024-004](PLAN-20261024-004-mhwi-weapon-placement.md) | 太刀武器位置与交接收尾 | implemented，编译通过；运行验收由用户执行 | [位置收尾](../Changes/CHG-20261024-005-mhwi-weapon-placement.md) |
| [PLAN-20261024-003](PLAN-20261024-003-mhwi-native-parameter-pipeline.md) | 原游戏参数批处理与白名单导入 | implemented，此批处理范围；完整原生消费者/控制逻辑未完成 | [批处理结果](../Changes/CHG-20261024-004-mhwi-native-parameter-pipeline.md) |
| [PLAN-20261024-002](PLAN-20261024-002-mhwi-defense-transitions-transfer.md) | 独立防御、逐路由窗口与连续交接 | partial，已构建/写入，防御911断言通过；后续优先参数路线 | [实施记录](../Changes/CHG-20261024-003-mhwi-defense-routes-transfer.md) |
| [PLAN-20261024-001](PLAN-20261024-001-mhwi-native-fidelity-implementation.md) | MHWI源采样与武器事件实施 | partial，平行动画/内部武器轨道已实施；公开资料校准继续 | [本轮结果](../Changes/CHG-20261024-002-mhwi-native-fidelity-implementation.md) |
| [PLAN-20261023-001](PLAN-20261023-001-mhwi-source-fidelity.md) | MHWI原始武器轨道与完整时序调查 | implemented-investigation，调查和后续阶段方案完成；原版精确还原未完成 | [调查记录](../Changes/CHG-20261024-001-mhwi-source-fidelity-audit.md) |
| [PLAN-20261022-002](PLAN-20261022-002-mhwi-longsword-behavior.md) | MHWI太刀动作行为与袈裟方向修正 | implemented，七项核心行为与限定验证完成；精确原版参数/全部地形仍有标定边界 | [实施与验收](../Changes/CHG-20261023-001-mhwi-behavior-implementation.md)、[实施会话](DSH-20261022-mhwi-behavior-task.md) |
| [PLAN-20261022-001](PLAN-20261022-001-mhwi-longsword-module.md) | MHWI素材导入与太刀动作模组 | in-progress | 制作中 |
| [PLAN-20261020-002](PLAN-20261020-002-ninja-root-motion.md) | Ninja Root Motion与移动意图适配 | implemented，制作保存完成；按用户要求未做完工后验证 | [CHG-20261020-002](../Changes/CHG-20261020-002-ninja-root-motion.md) |
| [PLAN-20261020-001](PLAN-20261020-001-ninja-animation-replacement.md) | Ninja动画重定向与替换 | implemented，制作保存完成；按用户要求未做完工后验证 | [CHG-20261020-001](../Changes/CHG-20261020-001-ninja-animation-replacement.md) |
| [PLAN-20261019-003](PLAN-20261019-003-character-action-refactor.md) | 角色动作管理重构，含Motion Matching移动表现 | partial，动作核心已落地；MM按用户要求待资源后继续 | [初版](../Changes/CHG-20261019-003-action-refactor-proposal.md)、[MM扩展](../Changes/CHG-20261019-004-motion-matching-plan.md)、[实施](../Changes/CHG-20261019-005-character-actions-implementation.md) |
| [PLAN-20261019-002](PLAN-20261019-002-dark-fantasy-title-screen.md) | 暗黑幻想标题页 | implemented | [CHG-20261019-002](../Changes/CHG-20261019-002-dark-fantasy-title-screen.md) |
| [PLAN-20261019-001](PLAN-20261019-001-main-menu-pixel-ui.md) | 像素风格主菜单 | implemented | [CHG-20261019-001](../Changes/CHG-20261019-001-main-menu-pixel-ui.md) |

待办线索见 [已知问题](../Known-Issues.md)。它们不是已完成或已批准的技术方案。

动作重构补充：[MM数据实查](MM-P5-Audit-20261019.md)、[用户待处理的Root Motion资源清单](MM-RootMotion-Resource-Checklist.md)。
