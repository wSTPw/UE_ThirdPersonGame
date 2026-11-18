# MHWI 历史归档

2026-10-22 至 2026-11-05 的完整开发过程。**这些文档互相覆盖、部分结论已被推翻**，只用于追溯"为什么是现在这样"。

## 目录

| 子目录 | 数量 | 内容 |
| --- | ---: | --- |
| [Plans/](Plans/) | 57 | 每批的开发方案（`PLAN-*`、`DSH-*`、三份交接文档、两个进度 CSV） |
| [Changes/](Changes/) | 81 | 每次实质变更的记录（`CHG-*`） |
| [Reference/](Reference/) | 34 | 取证报告、验收报告、评审简报、动画库页 |

## 按主题找

| 想追溯 | 看这些 |
| --- | --- |
| 太刀数值/挂接/碰撞的推导过程 | `Reference/MHWI-Native-Parameter-Pipeline.md`、`MHWI-Native-Mount-20261028.md`、`MHWI-Weapon-Collision-Evidence-20261026.md`、`MHWI-Weapon-Mount-Evidence-20261028.md`（旧结论，已被前者推翻） |
| 太刀行为与动画 | `Reference/MHWI-LongSword-Behavior-Research.md`、`MHWI-Source-Fidelity-Audit.md`、`MHWI-Native-LinkMotion-Implementation.md` |
| R01–R35 台账逐项处置 | `Plans/MHWI-Restoration-Progress.md`、`Reference/MHWI-Ledger-Disposition-20261026.md` |
| 三份互相覆盖的验收 | `Reference/MHWI-Acceptance-20261026.md` → `MHWI-Acceptance-Update-20261026.md` → `MHWI-R06-R28-R30-Acceptance-20261027.md`（按此顺序读，后一份修正前一份） |
| 雌火龙下位数据 | `Reference/MHWI-Rathian-LR-Data-20261030.md`、`MHWI-Rathian-Format-Evidence-20261030.md` |
| THK 语义取证全过程 | `Plans/MHWI-Rathian-VM-Semantics-Handoff.md`、`Reference/MHWI-Rathian-FirstChain-Audit-20261105.md` |
| 四板块完整性核对（BEH/NUM/ANIM/AV 编号出处） | `Reference/MHWI-Rathian-Completeness-Check-20261102.md` |
| 对外评审简报 | `Reference/MHWI-Rathian-Review-Brief-20261103.md` |
| 解包流程与格式方法 | `Reference/MHWI-Unpacking-Workflow.md` |
| 给下一个 AI 的交接（自包含） | `Plans/MHWI-Rathian-AI-Handoff-20261104.md` |
| AI交接文档的变更记录 | [CHG-20261104-001](Changes/CHG-20261104-001-rathian-ai-handoff.md) |
| Approx编译修复的变更记录 | [CHG-20261104-002](Changes/CHG-20261104-002-rathian-approx-compile-fix.md) |
| DevFlow接手和THK审计准备 | [CHG-20261104-003](Changes/CHG-20261104-003-devflow-thk-audit-preparation.md) |
| 首链只读审查记录 | [CHG-20261105-003](Changes/CHG-20261105-003-rathian-first-chain-audit.md) |
| 文档现状层简化记录 | [CHG-20261105-004](Changes/CHG-20261105-004-docs-mhwi-simplification.md) |
| BITE 动作 83 的只读取证与 DevFlow | [CHG-20261106-001](Changes/CHG-20261106-001-rathian-bite-dispatch-devflow.md) |
| 动画库 848 条明细 | `Reference/MHWI-Rathian-Animations.md` |
| 音画映射 | `Reference/MHWI-Rathian-AudioVFX-Map-20261102.md` |

## 已知的失效口径（读的时候要当心）

| 说法 | 状态 |
| --- | --- |
| "344 条 name↔id↔vtable 完整动作注册表" | **已撤回**。旧提取器起点错位 +8，跨表按名称去重。新布局 285 条，见 [总账](../../Reference/MHWI-Rathian-Evidence.md) 第五节 |
| "B21 证明没有挂点数据、拟合方法成立" | **已推翻**。B21 只查武器侧事件，漏了猎人骨轨的 usage2 缩放通道 |
| "10 秒是 Q 的抑制时间" | **已推翻**。`0x51d=10` 实际暂停颜色衰减 |
| "0.4 秒是登龙 hit lag" | **已推翻**。0.4 是 shell 首段延迟 |
| "R06/R28/R30 三项完整交付" | 专项验收**不通过**。R06 源码可确认但运行证据在当期检出缺失；R28 未接过渡状态机；R30 无 Profile 资产与四链节点 |
| "五项 B1 修复已完成" | 当时**从未编译成功**。11-04 才修掉 4 类错误，PIE 仍未跑 |
| 雌火龙基础玩法源码（转入归档） | [CHG-20261107-001](Changes/CHG-20261107-001-rathian-basic-combat.md) |
| 玩家受击四方向片段（转入归档） | [CHG-20261116-001](Changes/CHG-20261116-001-hunter-damage-reaction.md) |
