# CHG-20261026-011：MHWI 太刀武器碰撞静态取证

- 状态：completed（限定离线静态证据链；R18继续取证中）
- 日期：2026-10-26
- 需求摘要：继续核实原作太刀攻击判定是否由攻击相关武器碰撞参数和动作时间轨驱动，并对照项目现有实现。
- 关联 PLAN / ADR / 问题 / 接口 ID：R18；R-ANIM-003
- Git：工作区变更，未提交

## 原因与结果

原先已知太刀动作有`CollisionTimelineObject`轨道、`wp03.col`有碰撞记录，但尚未将轨道UID、攻击记录和几何索引全部关联。本次只读脚本完成这条关联，并解析CLND/CLGM几何参数块边界；另从固定版分析代码区确认原生类型名`nCollision::cGeometryJoint`及其构造器/vtable。结果强力支持原作有按动作时间启停、由攻击记录引用的武器碰撞参数，原生引擎也包含joint-geometry命名类型；但未建立`.col`几何组到该类或具体骨骼的映射，因此几何实际形状、骨骼空间和运行时消费者仍未知。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/audit_weapon_hit_volume_evidence.py` | `parse_geometry_table`、`build_report` | 新增只读可复跑脚本，关联LMT时间轨与`.col` UID/几何索引，核对游戏覆盖文件，并保留未知字段的原始值 |
| `Docs/Reference/MHWI-Weapon-Collision-Evidence-20261026.md` | B19报告 | 记录来源指纹、39/39关联、StepSlash示例、安装覆盖差异、项目当前SweepWindow实现和证据限制 |
| `Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Reference/MHWI-Ledger-Disposition-20261026.md` | R18 | 增补时间轨/几何组/原生类型证据，但维持“取证中”状态 |
| `Docs/Systems/MHWI-LongSword.md`、`Docs/Known-Issues.md`、`Docs/README.md` | 当前实现、问题和导航 | 明确项目球形扫掠与原生几何参数不是同一实现，并提供取证报告入口 |

## 接口、事件与资源影响

无C++接口、蓝图、正式资产或游戏安装资源改动。脚本只读仓库归档、LMT、B17安装覆盖快照及指定安装下`nativePC/hm/wp/wp03/collision/wp03.col`；默认结果写入git忽略目录`Saved/MHWIRestoration/B19-20261026/`。

来源布局依据包括仓库固定的`native-combat-layout.json`和社区逆向格式模板 [MHW-Editor `col.bt`](https://github.com/Synthlight/MHW-Editor/blob/master/010%20Templates/col.bt)。后者仅用于核对CLND/CLGM字段顺序，未被当作官方格式规范或未知字段语义来源。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `python Scripts/MHWI/audit_weapon_hit_volume_evidence.py` | 仓库Python与指定游戏安装 | 完成；39条动作碰撞轨全部匹配，13组几何参数、55个表头引用/52条攻击记录；安装覆盖SHA与B17快照相同，几何和UID映射相同，仅52条记录`Flinch_Value`不同，208个变化字节均属该字段 | `Saved/MHWIRestoration/B19-20261026/weapon-hit-volume-evidence.json`（本机忽略目录） |
| `python Scripts/MHWI/trace_outstanding_evidence.py --function 0x1424661d0 --function 0x142466d70 --call 0x142466d70` | 固定版EXE指纹和分析`.text`；仅读，不执行游戏代码 | 抽取类初始化器、`cGeometryJoint`构造器及直接调用引用；确认构造器/vtable结构。未闭合该类与太刀`.col`记录的装载映射 | `Saved/MHWIRestoration/B13-20261026/fn-*.json`、`call-0x142466d70.json`（本机忽略目录） |
| `python Scripts/Docs/check_docs.py` | 仓库文档检查 | PASS：125个Markdown、1073条本地链接、12个模块及编辑器快照JSON；检查范围不包含C++ ABI、玩法或资产验证 | 命令输出 |
| `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` | 仓库工作区 | 退出码0；无空白错误。Git提示一个已有文档下次触及时会LF转CRLF | 命令输出 |

未执行编译、游戏、UE、PIE或行为测试；本批仅做静态取证，运行时消费者未观测。

## 风险、遗留与回退

- R18仍未闭合：CLGM具体形状、骨骼索引/变换、运行时碰撞对象消费、怪物部位到肉质及完整伤害管线均不能由本次数据关联单独推出。
- 当前安装`nativePC`覆盖与归档文件必须区别引用；当前覆盖保留相同几何/UID映射，但击退字段有差异。
- 回退本次全部文件即可移除本报告和关联；无游戏文件、资产或用户数据需恢复。

## 已同步文档

- [MHWI武器碰撞取证](../Reference/MHWI-Weapon-Collision-Evidence-20261026.md)
- [MHWI太刀现状](../Systems/MHWI-LongSword.md)
- [MHWI还原台账](../Plans/MHWI-Restoration-Progress.md)
- [已知问题](../Known-Issues.md)
- [开发文档入口](../README.md)
