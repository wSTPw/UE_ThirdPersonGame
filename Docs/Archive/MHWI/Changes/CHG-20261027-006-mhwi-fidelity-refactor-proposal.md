# CHG-20261027-006：MHWI 忠实还原重构审查提案与官方方案先行约定

- 状态：completed
- 日期：2026-10-27
- 需求摘要：用户认为 MHWI 实现方向和复杂度不可接受，要求提出重构方案，并要求今后技术调查/决策/方案以对应技术社区官方已有方案为先，不得擅自定技术方向。用户确认重构首要目标为忠实还原原版 MHWI。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261027-002](../Plans/PLAN-20261027-002-mhwi-fidelity-refactor.md)；R06/R28/R30、R-COMBAT-010、R-ANIM-003/007/008
- Git：工作区变更，未提交

## 原因与结果

只读检查发现 `AMHWICharacter` 的输入、动作推进、武器姿态、命中、资源、空中连段、受击与延迟伤害职责集中；`FMHWIMoveDefinition` 数据字段也覆盖多个行为领域。现有文档同时保留原生连接、移动 FSM、IK 语义等尚未闭合项目。以上支持结构性审查，但不构成任一架构方案正确的证据。

调查 Epic UE 5.8 官方组件、Gameplay Modules、Game Features、GAS、AnimBP Linking 与 Data Asset 资料，写入有出处的候选及适用条件。没有把模块拆分、GAS 或 Game Feature 选为最终方案。建立 draft 计划和用户长期技术规则，等待用户选择。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `AGENTS.md` | “官方方案先行” | 记录先搜官方资料、区分官方结论/项目事实/推断、多解时等用户选型的长期规则 |
| `Docs/Plans/PLAN-20261027-002-mhwi-fidelity-refactor.md` | 忠实还原重构审查 | 汇总只读事实、官方方案链接、候选和决策门；未选架构 |
| `Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md` | 文档/方案/变更索引 | 提供可发现入口 |

## 接口、事件与资源影响

无 C++、反射、蓝图、接口、正式资产和运行配置变化。计划中的架构候选尚未被选择，也未触发数据迁移。

本轮开始时工作区已有 54 条修改路径。未对这些既有源码/资产做修改或回退。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `git status --short` | 项目根目录 | 检查到 54 条既有路径；保护不动 | 本次会话只读状态 |
| `python Scripts/Docs/check_docs.py` | 项目 Python 环境 | PASS：137 Markdown 文件、1174 个本地链接、12 个模块及编辑器快照 JSON | — |
| `git diff --check` | 项目 Git 工作区 | 默认命令被本机 Git LFS 子进程启动错误中断；以 `git -c filter.lfs.process= -c filter.lfs.smudge= -c filter.lfs.clean= -c filter.lfs.required=false diff --check` 重跑，exit 0。仅有 `AGENTS.md` 与既有修改脚本的 LF/CRLF 提示 | — |

未编译、未运行 UE/PIE：本记录只涉及文档和约定更新，没有玩法或资产变更。

## 风险、遗留与回退

- 尚未选择架构、试点路径或工具清理范围；方案状态保持 `draft`。
- 若需撤回本次文字变化，回退 `AGENTS.md` 中新增规则、PLAN-002、CHG-006 及相应索引行即可；不会触碰已有 MHWI 代码或资产。

## 已同步文档

- [项目文档入口](../README.md)
- [方案索引](../Plans/README.md)
- [变更索引](README.md)
- [长期项目约定](../../AGENTS.md)
