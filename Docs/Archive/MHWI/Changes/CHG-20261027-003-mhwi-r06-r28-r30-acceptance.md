# CHG-20261027-003：R06/R28/R30专项验收

- 状态：completed，审查完成；三项完整交付均不通过
- 日期：2026-10-27
- 需求摘要：验收R06、R28、R30；运行调试由用户操作。
- 关联：B19、PLAN-20261026-004/005/006；R-ANIM-007/008、R-COMBAT-012/014/016、R-TEST-006。
- Git：基线`02a72404a5301c4b313e651b148775fca54193dc`，本次文档工作区变更未提交。

## 原因与结果

B19已有代表性源码修复，但“87项处置”不能解释为全量实现。当前源码确认R06模式后备/受击恢复/菜单缓存修复；R28六候选未接ABP，R30预定Profile缺失且制作脚本也不创建求解节点。当前检出缺七份B19引用报告，历史14项PIE及两次构建声明无法在此复核，不能作为本次通过。三项维持部分完成/取证中。

## 修改清单

| 文件 | 修改原因与效果 |
| --- | --- |
| `Docs/Reference/MHWI-R06-R28-R30-Acceptance-20261027.md` | 新增逐项裁决、来源/消费者缺口、证据可用性及用户运行准则 |
| `Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Plans/MHWI-Connector-Progress.md` | 当前验收入口与三项状态/历史运行声明范围 |
| `Docs/Systems/MHWI-LongSword.md`、`Docs/Known-Issues.md` | 同步当前证据缺失和R28/R30尚无消费者，登记R-TEST-006 |
| `Docs/README.md`、`Docs/Changes/README.md` | 新增验收入口及本次变更索引 |

## 接口、事件与资源影响

无。开始时工作区干净；没有修改C++、脚本实现、机器证据、Content、蓝图、DA、Montage、地图或原游戏。只读MCP确认编辑器已退出，没有启动/关闭编辑器或进行运行调试。按字节记录资产存在性，不冒充父类/骨架/属性读回。

## 实际验证

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| `audit_animation_coverage.main()`，仅重定向`OUT` | 重建87行（66/11/10），81条资产引用对应75个不同`.uasset`均存在；历史决策标签不是新运行结果 | `Saved/MHWIRestoration/Acceptance-R06-R28-R30-20261027/coverage-rebuild/animation-coverage.json` |
| 当前源码、资产指纹与Git差异只读 | 32引用/124身份；B19无Content差异；预定IK Profile不存在；七份B19引用报告缺失 | 同目录`offline-evidence.json` |
| UE-MCP `project.get_status` | disconnected/editor exited；未启动编辑器 | 本轮工具返回及离线记录 |

`python -B Scripts/Docs/check_docs.py`通过：131份Markdown、1127条本地链接、12模块；`git diff --check`通过，新增两文件另行尾空白检查通过。上述检查不验证玩法或资产属性。未编译、未运行游戏/UE/PIE、未新增截图、未保存/加载资产内部属性。历史14/14与两次构建只按交付声明引用；不认定为失败，也不记成本次通过。

## 风险、遗留与回退

R06原生mode0/全来源与逐条运行仍缺；R28六候选消费者和R30四链求解仍需开发。B19历史报告需补入可携带证据包，重建处置表不能替代它们。IK制作脚本只绑定Profile，不构造姿态节点。

回退仅恢复本次现状文档与索引，删除新增验收/CHG；改前备份在`Saved/MHWIRestoration/Acceptance-R06-R28-R30-20261027/Backup`。不撤销B19或其他用户提交，不涉及资产回退。

## 已同步文档

[验收报告](../Reference/MHWI-R06-R28-R30-Acceptance-20261027.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[连接台账](../Plans/MHWI-Connector-Progress.md)、[系统页](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[技术入口](../README.md)、[变更索引](README.md)。
