# CHG-20261030-015：修复火龙白模（自发光误接）与关卡光源竞争

- 状态：completed（材质与光照）；未保存关卡
- 日期：2026-10-30
- 需求摘要：处理模型材质发白问题，并处理编辑器提示"多个定向光源竞争前向着色"。
- 关联：[数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md) 5.2 节、[CHG-014](CHG-20261030-014-mhwi-rathalos-ue-import.md)

## 一、白模：根因是自发光接了一张白色占位贴图

CHG-014 的材质重建按"有 EM 图就接自发光"处理，而 `NoImage_EM`（4×4 白色占位图）也被当成 EM 接了进 Emission Color，强度 1.0。结果整个网格自发光发白，压过 Base Color，且几乎不受光照影响。

排查顺序与排除项（都可复现）：

| 假设 | 检查方式 | 结果 |
| --- | --- | --- |
| 材质没连贴图 | `material.read_graph` | 已排除：BaseColor←`em001_00_BML_tex`、Normal←`em001_00_NM_tex` |
| 贴图文件损坏/空白 | Blender 采样平均色 | 已排除：(0.405, 0.351, 0.275)，有内容 |
| UE 内贴图导错 | `asset.export_texture` 回导 | 已排除：4096×4096，21,859,246 B，与源图一致 |
| UV 丢失 | Blender 读 `uv_layers` | 已排除：25 个网格各有 1 层 UV |
| 材质槽映射错 | Blender 读 `material_slots` | 已排除：主体网格均为 `Ch_EM001_Mt__2` |
| 过曝 | 调整两盏定向光强度 | 已排除：5→3.5、3→0.8 后仍纯白 |
| **自发光误接** | 断开 Emissive 后重截 | **成立**：断开后露出褐棕贴图 |

修复分两步：

1. `Tools/MHW/rebuild_monster_materials.py` 的 `pick()` 增加 `NoImage_*` 过滤，占位图不再进自发光（真 EM 如 `em001_00_eye_EM` 仍保留）。
2. 已导入的材质不会因覆盖导入而重建，故在活动编辑器里对 `Ch_EM001_Mt__2`、`Ch_EM001_Mt__damage`、`Ch_FakeSphere__3` 执行 `material.disconnect_property(property='EmissiveColor')` 并保存。

验证：`read_graph` 显示三者的 `EmissiveColor -> None`，`FakeEye_Mt__4` 保留眼睛自发光；重新截图后翼膜与躯干显示真实褐棕贴图。

## 二、光源竞争提示

编辑器提示"多个定向光源正在竞争……请调整 ForwardShadingPriority"。关卡 `L_MHWI_Training` 内有两盏定向光，`ForwardShadingPriority` 均为 0。

处理：`MHWI_Sun` 设为 1，填充光保持 0；同时把强度从 5/3 调为 3.5/0.8。读回确认为 1。

## 三、截图接口的坑

`editor.capture_scene_png` 对**同一取景会返回完全相同的字节**（多次 420×236 截图为 157,982 B，换成红色材质也不变），因此不能用来做 A/B 判断；只有换分辨率或改变光照后字节数才变化。判断渲染问题时不要依赖它做单变量对照。

## 修改清单

| 文件/资产 | 修改内容 |
| --- | --- |
| `Tools/MHW/rebuild_monster_materials.py` | `pick()` 跳过 `NoImage_*` 占位图 |
| `Content/MHWI/Rathalos/Materials/*.uasset` | 断开 3 个材质的 EmissiveColor，已保存 |
| `L_MHWI_Training`（**未保存**） | `MHWI_Sun` 优先级 0→1、强度 5→3.5；`MHWI_FillLight` 强度 3→0.8；两个预览 Actor 仍在场景中 |
| `Saved/MHWProbe-20261030/model-ue/*.fbx` | 重新导出（无占位自发光） |

## 验证与未验证

已验证：材质图连接、贴图导出比对、UV/槽位、自发光断开后的渲染差异、光源优先级读回。
未验证：**关卡未保存**（`L_MHWI_Training` 有用户未提交修改，不代为落盘）；未做 RMT/CMM/FM 打包接线，粗糙度/金属度仍是常量；未在 PIE 中查看。

## 回退

- 材质：重新导入 FBX 并勾选材质覆盖，或在编辑器里把 `NoImage_EM_tex` 接回 EmissiveColor。
- 关卡：不保存即还原；或在编辑器内撤销 `MHWI_Sun` 的属性修改、删除两个 `MHWI_Rathalos_*` Actor。
