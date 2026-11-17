# 变更记录索引

记录实际发生的实质修改。一条记录 = 一次可回退的改动，含原因、源文件/符号、接口影响、验证结果、未验证项、回退方法。

**这里只列最近 5 条。** 更早的全部在 [Archive/MHWI/Changes](../Archive/MHWI/Changes/) 与 [Archive/Legacy/Changes](../Archive/Legacy/Changes/)。

| ID | 日期 | 主题 | 状态 |
| --- | --- | --- | --- |
| CHG-20261117-001 | 2026-11-17 | [本地积压改动入库与版本控制范围调整](CHG-20261117-001-local-backlog-versioning.md) | completed；10-30~11-16 积压入库，DamageSource 9 个资产补齐（C++ 硬编码引用）；Rathalos 848 个全量动画/1.6GB 与 datamine 二进制排除入库；未改 C++、未重编、未 PIE |
| CHG-20261116-001 | 2026-11-16 | [玩家受击改用原生 DAMAGE_S 四方向片段并补全大/中档](CHG-20261116-001-hunter-damage-reaction.md) | completed；三档方向化选段+落地起身链合入，13 例真实 PIE 全 PASS；Medium 为用户批准试验组，击飞落体段与特殊受击仍 open |
| CHG-20261107-003 | 2026-11-07 | [修复低帧下玩家短受击姿态缺失](CHG-20261107-003-hunter-hit-reaction.md) | completed；三源码经Luna冻结编译/独立审查/主审合入，主项目构建及最终骨姿/真实位移、生命周期16次运行121断言通过 |
| CHG-20261107-002 | 2026-11-07 | [雌火龙Basic动画、碰撞盒与PIE完成](CHG-20261107-002-rathian-basic-assets-pie.md) | completed；25新资产、健康步行/起落修正、24项真实PIE/101断言通过，工程火球按用户选择保留 |
| CHG-20261107-001 | 2026-11-07 | [雌火龙基础玩法源码与离线验证](CHG-20261107-001-rathian-basic-combat.md) | completed（代码阶段）；13文件基础合入，冻结编译/独立审查/主审及原项目编译通过；资产/PIE完成见CHG-002 |

## 写新记录

1. 复制 [变更模板](../Templates/Change-Record.md)，命名 `CHG-YYYYMMDD-NNN-主题.md`（同日编号先查已有文件）
2. 在本表顶部加一行
3. 若超过 5 条，把最旧的移入对应 `Archive/*/Changes/` 并在归档 README 索引里补一行

编号不重复使用。已完成的记录保留历史含义；后续行为改变应新建记录，不改旧记录。
