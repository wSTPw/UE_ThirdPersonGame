# 变更记录索引

记录实际发生的实质修改。一条记录 = 一次可回退的改动，含原因、源文件/符号、接口影响、验证结果、未验证项、回退方法。

**这里只列最近 5 条。** 更早的全部在 [Archive/MHWI/Changes](../Archive/MHWI/Changes/) 与 [Archive/Legacy/Changes](../Archive/Legacy/Changes/)。

| ID | 日期 | 主题 | 状态 |
| --- | --- | --- | --- |
| CHG-20261105-004 | 2026-11-05 | [MHWI 文档简化：归档 189 份历史、重写现状层](CHG-20261105-004-docs-mhwi-simplification.md) | completed（文档）；归档 + 4 份现状重写 + 2 份取证总账；未改代码/资产 |
| CHG-20261105-003 | 2026-11-05 | [雌火龙首链只读取证与源码审查](CHG-20261105-003-rathian-first-chain-audit.md) | completed（审查/文档）；动作表旧口径撤回、根轨/三UID复核；整链仍 partial |
| CHG-20261104-003 | 2026-11-04 | [DevFlow 接手与 THK 审计任务准备](CHG-20261104-003-devflow-thk-audit-preparation.md) | partial；doctor/prepare 通过，隔离环境待就绪，模型调用 0 |
| CHG-20261104-002 | 2026-11-04 | [Approx 层编译修复](CHG-20261104-002-rathian-approx-compile-fix.md) | completed；4 类 UE5.8 错误修完，`Result: Succeeded`；PIE 未执行 |
| CHG-20261104-001 | 2026-11-04 | [雌火龙项目 AI 交接文档](CHG-20261104-001-rathian-ai-handoff.md) | completed（文档）；发现 `Saved/` 被忽略致关键证据未纳管 |

## 写新记录

1. 复制 [变更模板](../Templates/Change-Record.md)，命名 `CHG-YYYYMMDD-NNN-主题.md`（同日编号先查已有文件）
2. 在本表顶部加一行
3. 若超过 5 条，把最旧的移入对应 `Archive/*/Changes/` 并在归档 README 索引里补一行

编号不重复使用。已完成的记录保留历史含义；后续行为改变应新建记录，不改旧记录。
