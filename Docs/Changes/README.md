# 变更记录索引

记录实际发生的实质修改。一条记录 = 一次可回退的改动，含原因、源文件/符号、接口影响、验证结果、未验证项、回退方法。

**这里只列最近 5 条。** 更早的全部在 [Archive/MHWI/Changes](../Archive/MHWI/Changes/) 与 [Archive/Legacy/Changes](../Archive/Legacy/Changes/)。

| ID | 日期 | 主题 | 状态 |
| --- | --- | --- | --- |
| CHG-20261117-004 | 2026-11-17 | [THK语义审计（M1/M2）与斗技场场景提取](CHG-20261117-004-mhwi-thk-semantics-arena-extract.md) | completed（证据产出）；147动作ID/111命名，26类条件全已证，st201+st202共146文件落库 |
| CHG-20261117-003 | 2026-11-17 | [刀光第二版（收至刀尖 + 淡红自发光）与版本切换](CHG-20261117-003-weapon-trail-tip.md) | completed；外观抽成 FullBlade/TipOnly 两份 look，切换先清样本；19/19 PIE PASS（两版分别采样/扣血/数字）；真实帧率观感未验收 |
| CHG-20261117-002 | 2026-11-17 | [太刀刀光与命中数字显示](CHG-20261117-002-weapon-trail-damage-numbers.md) | completed；新增刀刃残影组件与 Canvas 命中数字，窗口跟随源命中窗口；11 项 PIE PASS，真实帧率观感未验收 |
| CHG-20261117-001 | 2026-11-17 | [本地积压改动入库与版本控制范围调整](CHG-20261117-001-local-backlog-versioning.md) | completed；10-30~11-16 积压入库，DamageSource 9 个资产补齐（C++ 硬编码引用）；Rathalos 848 个全量动画/1.6GB 与 datamine 二进制排除入库；未改 C++、未重编、未 PIE |
| CHG-20261107-003 | 2026-11-07 | [修复低帧下玩家短受击姿态缺失](CHG-20261107-003-hunter-hit-reaction.md) | completed；三源码经Luna冻结编译/独立审查/主审合入，主项目构建及最终骨姿/真实位移、生命周期16次运行121断言通过 |
| CHG-20261107-002 | 2026-11-07 | [雌火龙Basic动画、碰撞盒与PIE完成](CHG-20261107-002-rathian-basic-assets-pie.md) | completed；25新资产、健康步行/起落修正、24项真实PIE/101断言通过，工程火球按用户选择保留 |

## 写新记录

1. 复制 [变更模板](../Templates/Change-Record.md)，命名 `CHG-YYYYMMDD-NNN-主题.md`（同日编号先查已有文件）
2. 在本表顶部加一行
3. 若超过 5 条，把最旧的移入对应 `Archive/*/Changes/` 并在归档 README 索引里补一行

编号不重复使用。已完成的记录保留历史含义；后续行为改变应新建记录，不改旧记录。
