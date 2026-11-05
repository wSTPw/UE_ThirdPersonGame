# CHG-20261022-003：MHWI 武器与刀鞘挂接修正

- 状态：completed，配置已保存并完成新生成角色的 PIE 检查。
- 日期：2026-10-22。
- 需求：优先修复武器与刀鞘位置不对。
- 关联：MHWI-001..005、R-ANIM-003；接续 [模组实施](CHG-20261022-002-mhwi-longsword-module.md)。
- Git：工作区变更，未提交。

## 原因与修改

初版固定变换仅为几何估计。导入后刀身长轴为模型组件 +Y，原右手挂接 Roll=90 使刀刃朝向持柄的身体一侧；刀鞘以骨盆为父级且方向上扬，难以贴背。当前在独立 PIE 中分开校准右手握持、背负纳刀与特殊纳刀；拟合配置见 [attachment_fit.json](../../Scripts/MHWI/attachment_fit.json)，预览工具见 [attachment_workbench.py](../../Scripts/MHWI/attachment_workbench.py)。

源模型没有重写；角色组件采用统一 0.7 适配比例，避免原 325 cm 总长在此角色上过大。拔刀握柄考虑缩放后的柄部偏移。背负刀鞘与刀身共用模型原点，以便入鞘；特殊纳刀另设左手挂点。最终右手父骨 bone_012，背负父骨 bone_002，特殊纳刀父骨 bone_008。最终变换保存在拟合 JSON 中，由 author_assets.attachment_defaults() 写入 `/Game/MHWI/Blueprints/BP_MHWI_Hunter`；character() 再制作也读取此配置，避免恢复错误初值。

## 实际验证

已在真实 PIE 中固定拔刀姿态，从正面、侧面和背面查看；修正后的右手位于柄部、刀刃朝外。保存证据位于 `Saved/MHWIImport/Attachment-*.png`；不能用单张图证明三维接触或所有动画都适配。已完成纳刀背负与特殊纳刀双手接触校准；特殊纳刀使用右柄部参考点、左鞘口参考点反解左腕局部变换，未改变原生动作调度。

## 风险与回退

此修正只针对 `/Game/MHWI/Blueprints/BP_MHWI_Hunter` 及制作脚本，旧角色与武器资产不应受影响。回退应恢复初版挂接字段，不能整目录还原用户已有修改。原生行为若需要随视觉问题调整，应另列具体源码、构建和运行证据。

## 完成证据与边界

| 检查 | 实际结果 |
| --- | --- |
| `author_assets.py` 的 `attachment_defaults` | 强制保存新角色 Blueprint 默认值；保存前的字段备份在 `Saved/MHWIImport/attachment-defaults-before.json` |
| Blueprint 编译 | 0 errors / 0 warnings |
| `pie_attachments.py` | 新建 PIE Pawn 45 项通过，核对五组位置/旋转/比例持久化、父骨、拔刀朝向/掌心参考点、特殊纳刀两组件轴线重合、居合转右手及结束回背、普通纳刀与再次进入特殊纳刀 |
| 参考点误差 | 拔刀柄点、特殊鞘口/柄点均小于 0.001 cm；这是定义的掌心参考点距离，不是完整手指表面穿插保证 |
| 多角度画面 | `Attachment-drawn-*-02.png`、`Attachment-sheathed-*-final.png`、`Attachment-special-front-final.png`、`Attachment-special-side-final.png`；固定同一姿态分别检查 |
| 本轮构建边界 | 只改 Blueprint 默认值/JSON/制作脚本与文档，没有改 C++；未重复完整原生构建，沿用模组构建产物并执行了此次真实 PIE |

未逐帧检查全部 164 条动画、未加入双手 IK，也未复现原版全部武器附件动画。通用普通命中仍为既有扇区扫掠，此修正没有改伤害窗口。测试结束已退出专用暂停 PIE；用户随后自行开始普通 Play，未终止用户的游戏会话。最终额外保存尝试因编辑器处于 Play 被拒绝；核心参数已在此次新 Pawn 检查前保存到磁盘（16:09），不依赖该次额外保存。用户的 Play 随后已结束，最后一次 finish_attachment_fix.py 已实际保存成功，当前编辑器保留训练地图。

精确回退：背负两个父骨恢复 bone_000，右手恢复 `(-7,2,0)/Roll=90/Scale=1`，背负两组恢复 `(12,18,-12)/(Pitch=-35,Roll=130)/Scale=1`，特殊两组恢复 `(-4,2,0)/Roll=90/Scale=1`；或使用上述备份逐字段恢复。不要覆盖其他角色默认属性。

已同步 [当前系统](../Systems/MHWI-LongSword.md)、[模块索引](../Reference/modules.json)、[问题](../Known-Issues.md) 与 [变更索引](README.md)。
