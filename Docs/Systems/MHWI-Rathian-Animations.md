# 雌火龙动画库与遗漏补齐

- 更新：2026-10-30；状态：本批补齐完成。新增824条，连同保留的24条共848条AnimSequence。
- 目标：em001雌火龙。沿用历史目录名`/Game/MHWI/Rathalos/Animations`，不迁移资产引用。
- Skeleton：`/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton`（Skeleton；源模型141骨，UE导出含Armature根共142骨轨）。
- 源模型：`ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/mod/em001_00.mod3`。

## 源库与覆盖口径

原归档合并索引和本机提取目录均有19个LMT，非零动作指针合计848条。CHG-022首批已导24条，需补824条。容器指针空槽不代表遗失动画，不为零条目创建伪资产；保留bank名称与原槽号，不推测中文招式名。

| bank | 非空动作 |
| --- | ---: |
| em001_00 / em001_00_fs | 111 / 93 |
| em001_01 / em001_01_fs | 68 / 29 |
| em001_02 / em001_02_fs | 123 / 66 |
| em001_03 / em001_03_fs | 62 / 0 |
| em001_04 / em001_04_fs | 95 / 0 |
| em001_05 / em001_05_fs | 49 / 0 |
| em001_06 / em001_06_fs | 4 / 0 |
| em001_07 / em001_07_fs | 0 / 0 |
| em001_08 / em001_08_fs | 103 / 45 |
| em001_tree | 0 |

## 转换与导入

沿用Feuleur 1.3.9的MOD3/LMT读取，不改第三方插件。[Epic UE5.8官方导入方式](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-animations-using-fbx-in-unreal-engine)要求单独导入动画指定既有Skeleton，项目据此复用原骨架。

1. 通过`Saved/rathian_inventory.py`读取实际编辑器24条基线，保存原uasset hash；原采集manifest逐LMT核对hash。
2. `Tools/MHW/complete_rathian_animations.py`在便携Blender执行，枚举所有bank，跳过既有动画；每条使用源帧数设置scene的0..frame_count-1、60FPS，并清理上一动作姿态。单帧条目以至少一个采样间隔导出并明确记录。
3. `Scripts/MHWI/complete_rathian_import.py::run(limit=12)`由MCP分批调用；拒绝覆盖未登记的既有资产，显式绑定Skeleton，逐条保存并核对时长。
4. `verify_rathian_completion.py::run()`核对源有效条目集合、旧/新增集合、UE实际资产集合、类/骨架/时长、旧资产hash，并抽查不同bank骨轨变化。最后由`record_rathian_completion.py`记录紧凑证据。

完整日志、FBX、导出/导入/验证报告在`Saved/RathianAnimationCompletion-20261030/`，忽略目录不随仓库交接。工具只补动画，不创建Montage或接入AI/动画蓝图。

## 已知边界

- 旧24条保持原样，均4.15秒的历史范围问题见Known-Issues的R-ANIM-011；本次新增动画使用源帧数，不把旧批次检查当作修复。
- `_fs`后缀和源单帧条目原样保留，不擅自赋予招式/动作层语义；导入不等于已还原原作合成、NeedsParent、根运动和所有姿态。
- 源模型141骨，不合并独立尾部模型。未运行原作，不宣称完整玩法忠实度。
- 批量MCP调用超时不能视为取消；先查看逐条journal，确认原批次结束后再继续，防止重复导入。

方案见[PLAN-005](../Plans/PLAN-20261030-005-mhwi-rathian-animation-completion.md)，历史首批见[CHG-022](../Changes/CHG-20261030-022-mhwi-rathian-animations.md)。

## 本批实际验证

824/824新增资产类、Skeleton、时长与磁盘保存读回通过；19容器/848有效条目的集合与UE资产集合一致，原24条hash未变。12个有效bank抽检各一条，10条有骨轨变化，em001_01_fs与em001_02_fs样本无变化，保留常量结果，不宣称全库每条均动态。每样本142轨；完整抽检与逐条映射见[紧凑证据](../../Tools/MHW/rathian-animation-completion.json)，本批记录见[CHG-023](../Changes/CHG-20261030-023-mhwi-rathian-animation-completion.md)。

导入日志出现绑定姿势与少数单帧烘焙数量警告；本轮已检查骨架、采样时长与骨轨，未完成原作逐帧姿态/叠加层或视口播放验收。

## 2026-10-31旧24条时长修复

旧24条已按源帧数同路径重导，原对象身份、Skeleton及引用列表保持，24/24时长与保存读回通过；此前关于旧时长未修的段落仅描述2026-10-30批次。当前R-ANIM-011已fixed-readback，见[本批记录](../Changes/CHG-20261031-001-rathian-legacy-duration.md)。动画总量仍848条。
