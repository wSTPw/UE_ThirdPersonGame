# CHG-20261019-004：动作重构方案加入Motion Matching

- 状态：completed，仅方案扩展；玩法未实施
- 日期：2026-10-19
- 需求摘要：解释Motion Matching，并纳入本项目动作管理重构方案。
- 关联方案：[PLAN-20261019-003](../Plans/PLAN-20261019-003-character-action-refactor.md)
- Git：工作区文档变更，未提交；保留此前源码、配置和资产修改。

## 原因与结果

在现有动作生命周期方案中加入Motion Matching移动表现层：说明姿势/轨迹查询原理、与动作组件/CharacterMovement/Montage的分工、动画数据门槛、分层规则、试点与性能验收。新增P5正式接入阶段，P0提前审计数据，P1快照接口稳定后允许独立原型。

## 修改清单

| 路径 | 修改内容 |
| --- | --- |
| `Docs/Plans/PLAN-20261019-003-character-action-refactor.md` | 新增MM设计、当前条件、候选资产、验收和技术参考；方案保持draft |
| `Docs/Plans/README.md` | 更新方案主题与本次扩展链接 |
| `Docs/Changes/README.md` | 新增本记录 |

## 接口、事件与资源影响

无实际运行接口/资源变化。`FLocomotionAnimContext`、Pose Search Schema/Database、测试ABP与P5均为方案。未启用插件、未改Build.cs、未改动画Root Motion开关，未创建或保存UE资产。旧CHG保留当时含义。

## 实际验证

| 检查 | 实际结果 |
| --- | --- |
| 源码/配置/文件只读检查 | uproject未显式列出PoseSearch；引擎安装含PoseSearch插件；项目已有ABP_Move及起停/转向候选序列文件 |
| UE-MCP `animation.read_sequence`批量抽查 | SwordAnim下Idle、Walk_Loop_F_0、Run_Loop_F_0、Run_Start_F_0、Run_Stop_F_0、Turn_180_R对应6条Seq_YBot均读取成功，60FPS、rootMotionEnabled=false；完整路径列于方案 |
| Epic UE5.8官方文档 | 核对Pose Search、Schema/Database、轨迹与姿势查询、移动示例Root Motion要求和调试工具 |
| `python Scripts/Docs/check_docs.py` | PASS：31个Markdown、162个本地链接、10个模块及editor snapshot JSON |
| `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` | 退出码0，仅既有LF→CRLF提示 |

未编译/PIE：仅方案文档调整。未分析Root Bone实际位移、全量骨架/重定向或运行时插件加载状态，不以6条抽查结果推断全库可用性。

## 风险、遗留与回退

MM质量和成本取决于数据覆盖与调参，不承诺开插件即改善或自动消除滑步。实施需先验证根轨迹与位移权威，防止CMC和Montage/MM重复应用位移。回退本次修改只涉及新增方案段落、P5、索引和本记录。

## 已同步文档

- [动作重构方案](../Plans/PLAN-20261019-003-character-action-refactor.md)
- [方案索引](../Plans/README.md)
- [变更索引](README.md)
