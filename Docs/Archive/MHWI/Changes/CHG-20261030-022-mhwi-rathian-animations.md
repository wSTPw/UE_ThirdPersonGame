# CHG-20261030-022：雌火龙动画导出并导入引擎（24/24）

- 状态：completed（首批 24 个动作）；其余 87 个动作与其余 LMT 未导
- 日期：2026-10-30
- 需求摘要：动画要处理好并导入引擎、能够使用。
- 关联：[CHG-021](CHG-20261030-021-mhwi-rathian-rename.md)（编号确认：em001=雌火龙）

## 结果

- `em001_00.lmt`（主动作库）解析出 **111 个动作**；首批导出 **24 个**。
- 引擎内 `/Game/MHWI/Rathalos/Animations/` 落盘 **24 个 AnimSequence**（`A_em001_00_001`…），全部挂接 `SK_EM001_Body_Skeleton`，单条时长约 4.15 s（60 fps）。
- 导入 24/24 成功、0 错误，目录已保存。

## 两个新入口

| 文件 | 作用 |
| --- | --- |
| `Tools/MHW/convert_monster_animations.py` | 无头 Blender：load_mod3 + load_lmt，逐 action 烘焙导出 FBX（`--max-actions` 控制数量） |
| `Scripts/MHWI/import_rathalos_animations.py` | 编辑器内：FBX → AnimSequence，挂既有骨架，写报告 |

## 过程中的三处修正（都已验证）

1. Blender 4.5 FBX 导出器**不接受** `bake_anim_use_default_range/range_start/range_end` 参数——首跑 24 个全部 TypeError；且旧汇总把失败计成"exported 24"，已改为只计成功（`exported_ok`）。
2. 编辑器内 `unreal.Paths.project_dir()` 返回相对路径，`resolve()` 后指错目录导致找不到 FBX；改用 `get_project_file_path()`。
3. 5.8 的 AnimSequence 没有 `number_of_frames` 属性，报告改用 `sequence_length`（带 try 回退）。

## 未做 / 边界

- 只导了 `em001_00.lmt` 的前 24 个动作；该库共 111 个，另有 11 个有效 LMT（`_fs` 变体、`em001_01/02/04/05/08` 等）未导。
- 动作名为引擎内编号（`em001_00_001`），**无语义名称**——动作→招式的语义映射需要后续解 LMT 名称表或对照实机。
- 未在视口播放验证动画表现；未接 AnimMontage/蓝图。
- 仍是雌火龙骨架（141 骨）；与尾巴骨架（2 骨）未合并。

## 验证

| 操作 | 结果 |
| --- | --- |
| Blender 导出 | `exported_ok=24/24`，FBX 全部落盘 |
| 编辑器导入 | `imported=24/24 errors=0`，24 个 uasset 落盘，`save_directory` 成功 |
| 时长抽检 | 24 条 `sequence_length` 均有值 |
