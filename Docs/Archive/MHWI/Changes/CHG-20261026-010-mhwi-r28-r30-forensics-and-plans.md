# CHG-20261026-010：MHWI R28/R30 补充取证与实施方案

- 状态：completed（取证与方案范围）；未实施玩法
- 日期：2026-10-26
- 需求摘要：先补查 R28 基础移动候选与 R30 原生 IK 链，再编写分项实施方案。
- 关联 PLAN / ADR / 问题 / 接口 ID：R28、R30、R-COMBAT-012、R-ANIM-007、[PLAN-20261026-004](../Plans/PLAN-20261026-004-mhwi-locomotion-transitions.md)、[PLAN-20261026-005](../Plans/PLAN-20261026-005-mhwi-equipment-ik.md)
- Git：工作区变更，未提交

## 原因与结果

B17 已确认基础移动转换片段和原生 IK 求解坐标/语义尚有缺口。本批重新读取六条 R28 候选 LMT 动作头字段，并将四条 R30 IK 链索引对应到项目 rig-bind 骨链；据此形成 R28 状态过渡与 R30 项目 IK 适配两份方案。原生 solver 语义仍未闭合，方案明确不把 UE 近似 solver 称为原版复刻，台账状态不升级。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/audit_r28_r30_evidence.py` | LMT 005/006/007/008/014/015、基础循环 manifest、IK 文件 SHA 和 rig-bind 父链 | 新增只读复核工具，固定输出到本机 Saved；不改游戏/UE 资源 |
| `Docs/Reference/MHWI-R28-R30-Evidence-20261026.md` | R28/R30 新证据和未闭合边界 | 保存取证结论、数据来源及是否足以实施的裁决 |
| `Docs/Plans/PLAN-20261026-004-mhwi-locomotion-transitions.md` | R28 实施设计 | 新增状态机、资产资格、移动物理边界与验收计划 |
| `Docs/Plans/PLAN-20261026-005-mhwi-equipment-ik.md` | R30 实施设计 | 新增四链项目 IK、线程/坐标空间和武器挂接依赖计划 |
| 台账、太刀现状、已知问题与文档索引 | R28/R30 当前状态 | 更新交接点和入口；状态仍为部分完成/取证中 |
| `Saved/MHWIRestoration/B18-20261026/r28-r30-evidence.json` | 本机忽略的证据输出 | 6 条 LMT 候选、5 条已合格循环、8 个 IK 资源与 4 条骨链摘要；不纳入版本控制 |

## 接口、事件与资源影响

没有改 C++、反射接口、蓝图、DataAsset、Montage、Sequence、BlendSpace、地图或游戏安装。新增审计工具只读取固定抽取件与 B17 校验结果，并在 `Saved/` 写 JSON。用户原先未提交的 Content/Source/Docs/Scripts 修改保留；本批只新增上述文件并修改注明的文档段落。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `python Scripts/MHWI/audit_r28_r30_evidence.py` | 仓库固定 LMT/rig 与 B17 归档复验 | 完成：6 条候选解析；8/8 IK 资源匹配归档；4/4 骨链映射到连续 rig 父子链 | `Saved/MHWIRestoration/B18-20261026/r28-r30-evidence.json` |
| `python Scripts/Docs/check_docs.py` | 仓库文档 | PASS：124 Markdown 文件、1065 个本地链接、12 个模块及编辑器快照 JSON | 全仓文档 |
| `git diff --check` | 仓库工作区 | PASS：默认 LFS filter 进程受 Windows 本机对象权限阻止；以 `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` 绕过 LFS filter 后通过 | 全仓工作区 |

没有启动原游戏、UE 或 PIE；源动作角色绑定、原生 IK solver 空间与项目拟合结果仍待后续核验。

## 风险、遗留与回退

R28 候选 Motion 的状态语义未逐条由原生动作路由绑定，原版速度/阈值未知；R30 manager 字段、solver 目标坐标/极向/限位和 CTM 语义未解。R28 维持“部分完成”，R30 维持“取证中”。撤销时删除本条、报告、两份方案与审计脚本，再只移除此记录新增的索引句/表行；不改动任何正式玩法资源或现存用户更改。

## 已同步文档

[R28/R30 报告](../Reference/MHWI-R28-R30-Evidence-20261026.md)、[R28 方案](../Plans/PLAN-20261026-004-mhwi-locomotion-transitions.md)、[R30 方案](../Plans/PLAN-20261026-005-mhwi-equipment-ik.md)、[开发台账](../Plans/MHWI-Restoration-Progress.md)、[太刀现状](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[方案索引](../Plans/README.md)、[技术入口](../README.md)、[变更索引](README.md)。
