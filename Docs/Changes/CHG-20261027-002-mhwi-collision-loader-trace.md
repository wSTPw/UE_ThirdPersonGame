# CHG-20261027-002：MHWI 碰撞加载工厂追踪与可用性裁决

- 状态：completed
- 日期：2026-10-27
- 需求摘要：沿固定版原生静态加载链追踪太刀 `.col` 的类型工厂，直到能判断原作几何是否足以直接指导项目实现。
- 关联 PLAN / ADR / 问题 / 接口 ID：R18 刀刃/部位空间
- Git：工作区变更，未提交

## 原因与结果

此前已把 39 条太刀碰撞时间轨连接到 `wp03.col` 的攻击记录与几何组，但 `CLND` 类型编号和创建对象未知。本次把类型 1 追到节点工厂类 `cCollNodePl`，并沿它的读取槽定位到节点数据解析函数。该结果没有把 13 组 `CLGM` 参数映射到 `cGeometryJoint`，字段语义和骨骼空间仍未解码。

可用性裁决：**现有原作数据不足以直接实现忠实刀刃碰撞；要推进项目命中判定，应采用项目自己的武器/骨骼扫掠方案。** 本次只做离线取证与文档，没有开始修改玩法实现。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/trace_weapon_collision_loader.py` | 固定版 `CLND` 工厂与读取槽 | 新增可复跑的只读静态追踪，核对 type 1、初始化对象、`cCollNodePl`、creator 和读取函数 |
| `Docs/Reference/MHWI-Weapon-Collision-Evidence-20261026.md` | B19 续查 | 写明加载链证据、结论边界和“暂不可直接复用”的决策 |
| `Docs/Changes/README.md`、`Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Reference/MHWI-Ledger-Disposition-20261026.md`、`Docs/Systems/MHWI-LongSword.md`、`Docs/Known-Issues.md`、`Docs/README.md` | R18 现状同步 | 统一记录节点类型已解、几何字段和骨骼消费者仍未闭合 |

## 接口、事件与资源影响

无 C++/蓝图接口、玩法代码、正式资产或游戏安装文件改动。新增脚本只读取固定 EXE 指纹对应的分析 `.text` 副本及只读 PE 数据，结果写入忽略目录 `Saved/MHWIRestoration/B19-20261026/`。既有工作区修改均保留。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `python Scripts/MHWI/trace_weapon_collision_loader.py` | 固定 EXE 与 `.text` 指纹；离线静态读取 | 通过；type 1 表项指向静态初始化为 `cCollNodePl` 的节点工厂，读取链到 `0x1419c2fe0`；没有证明 geometry/bone 映射 | `Saved/MHWIRestoration/B19-20261026/weapon-collision-loader-chain.json` |
| `python Scripts/MHWI/trace_outstanding_evidence.py --function 0x140009890 --function 0x14191a5c0 --function 0x1419c30b0 --function 0x1419c2fe0 --function 0x1419c13d0 --function 0x1419c14a0 --call 0x142466d70` | 固定版 `.text` 静态反汇编 | 通过；复核初始化、索引分发、CLND 读取、CLGM 定长记录读写及独立 `cGeometryJoint` 构造器引用 | `Saved/MHWIRestoration/B13-20261026/fn-*`、`call-0x142466d70.json` |
| `python Scripts/Docs/check_docs.py` | 仓库文档链接/结构检查 | 通过；127 Markdown、1089 本地链接、12 modules 与 editor snapshot JSON 检查通过 | 命令输出 |
| `git diff --check` | Git 工作区 | 通过，退出码 0；仅提示 Ledger 文件行尾转换，不影响检查 | 命令输出 |

未启动游戏、调试器、UE 或 PIE；没有运行时碰撞对象观测。

## 风险、遗留与回退

- R18 仍未完成：几何形状字段、`CLGM` 到 `cGeometryJoint` 的映射、骨骼索引/变换、受击部位与肉质选择仍未知。
- 静态证据只能支持节点工厂和读取链存在，不能把节点对象类型当成攻击体形状。
- 文档和脚本可单独回退；本次没有玩法代码或资源需要回退。

## 已同步文档

[B19 武器碰撞取证](../Reference/MHWI-Weapon-Collision-Evidence-20261026.md)、[MHWI 还原进度台账](../Plans/MHWI-Restoration-Progress.md)、[R18 处置矩阵](../Reference/MHWI-Ledger-Disposition-20261026.md)、[太刀系统现状](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[文档入口](../README.md)及[变更索引](README.md)。
