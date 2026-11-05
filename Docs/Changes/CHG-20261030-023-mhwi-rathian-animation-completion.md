# CHG-20261030-023：雌火龙遗漏动画补齐（824条）

- 状态：completed-scope（源库覆盖与UE动画资产导入）；原作姿态/合成忠实度未验。
- 日期：2026-10-30；Git：工作区未提交。
- 需求：以雌火龙em001为目标，解包导入遗漏动画。
- 关联：[PLAN-005](../Plans/PLAN-20261030-005-mhwi-rathian-animation-completion.md)、模块mhwi-rathian-animation、R-ANIM-011；历史CHG-022不改。

## 原因与结果

旧批次仅em001_00前24条。核对归档合并索引与提取目录19个LMT完全一致，原始资源已全部提取，无需重复解包。非零动作指针848条；新增转换/导入824条，与原24条形成完整源条目集合。零容器/零槽不生成动画。

旧导出未按动作设置scene帧范围，24条均4.15秒。本轮保留旧资产，新增按源frame_count设置0..count-1、60FPS并清理前动作姿态，避免延续固定时长。逐条动画-only导入复用Skeleton，不覆盖现有资产。方法依据[Epic UE5.8官方FBX动画导入](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-animations-using-fbx-in-unreal-engine)，源读取沿用项目Feuleur 1.3.9，不改第三方。

## 修改清单

| 文件/资产完整路径 | 内容与影响 |
| --- | --- |
| `Tools/MHW/complete_rathian_animations.py` | 全bank枚举、源hash校验、差集转换、源帧数范围与逐条journal |
| `Scripts/MHWI/complete_rathian_import.py` | run(limit=12)，缺失动画分批导入/保存/类骨架时长核对，拒绝覆盖 |
| `Scripts/MHWI/verify_rathian_completion.py`、`record_rathian_completion.py` | 全集合与旧hash核对、12库骨轨抽检、紧凑证据归档 |
| `Content/MHWI/Rathalos/Animations/A_em001_*.uasset` | 824条新AnimSequence；精确清单见证据added/import_readback；旧24条hash未变 |
| `Tools/MHW/rathian-animation-completion.json` | 源bank/帧数/FBX hash/UE路径/逐条时长及验证结果 |
| `Docs/Systems/MHWI-Rathian-Animations.md`、`Docs/Plans/PLAN-20261030-005-mhwi-rathian-animation-completion.md` | 新现状与实施方案 |
| `Docs/Reference/MHWI-Rathian-LR-Data-20261030.md`、`Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md`、`Docs/Reference/modules.json`、`Docs/Known-Issues.md` | 当前入口、模块、记录与旧24条范围问题R-ANIM-011 |

## 接口与资产边界

Skeleton为`/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton`，动画位于`/Game/MHWI/Rathalos/Animations`。源模型141骨，FBX含Armature节点，读回142骨轨。不改C++/原转换脚本、玩法、ABP、Montage或训练图，不改原始提取产物，不迁移历史Rathalos目录；用户其余未提交修改保留。

## 实际验证

| 检查/命令 | 环境与实际结果 |
| --- | --- |
| 归档index与本地LMT列表、原manifest逐文件hash | 19/19容器一致，848非零动作；空容器7个，12个有效库 |
| 便携Blender4.5.0 --background --factory-startup --python-exit-code 1 --python Tools/MHW/complete_rathian_animations.py | 824条FBX，0转换错误，进程exit0；日志Saved/rathian-completion-export.log |
| UE-MCP editor.run_python_file 调complete_rathian_import.run | 824条类/骨架/时长/磁盘保存逐条通过；一次100条大批工具超时但后台执行到105条后结束，先读journal确认，再改小批，不重放已导资产。Slate尝试未持续推进，随后全部用同步小批执行 |
| verify_rathian_completion.run | passed=true，848总量/824新增/24保留，源与实际资产集合一致，旧24文件hash不变 |
| AnimationLibrary骨轨抽样 | 12有效库各一条、每条142轨；10样本有数值变化，01_fs/02_fs样本为常量，原样记录不视作招式 |
| record_rathian_completion.py | 紧凑证据保存；完整FBX/报告在Saved/RathianAnimationCompletion-20261030 |
| 文档/空白检查 | check_docs.py通过：179篇、1500本地链接、14模块；新脚本AST/新增文件空白通过。普通git diff受既有LFS clean写.git权限阻断，关闭LFS过滤的只读diff检查通过 |

导入出现绑定姿势回退零时与部分单帧烘焙数量警告，完整UE日志保留Saved/Logs/IntroCpp.log；本轮实际读回骨架/时长/骨轨，不据此声称原作姿态完整还原。未做PIE、视口逐条播放、原作运行、NeedsParent/叠加层资格或完整根运动比较；无需重编引擎。旧24条时长问题未修。

## 风险与回退

原编号不等于招式名称，静态/辅助条目不等于动态招式。旧24问题见R-ANIM-011。回退在编辑器内只删除证据added列出的824条新动画；保留旧24、骨架和用户其他资产。新增脚本/证据/文档与入口可定点撤销，不整体恢复工作区。Saved中的FBX与报告为本机中间产物。

## 已同步文档

[现状](../Systems/MHWI-Rathian-Animations.md)、[方案](../Plans/PLAN-20261030-005-mhwi-rathian-animation-completion.md)、[源数据](../Reference/MHWI-Rathian-LR-Data-20261030.md)、[总入口](../README.md)、[模块](../Reference/modules.json)、[问题](../Known-Issues.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
