# CHG-20261030-016：接入 RMT 粗糙度/金属度，材质链路补齐

- 状态：completed（材质）；未做 CMM/FM，关卡仍未保存
- 日期：2026-10-30
- 需求摘要：继续处理材质，把此前"未接线"的 RMT 接进去。
- 关联：[CHG-015](CHG-20261030-015-mhwi-rathalos-white-material-fix.md)（自发光修复）、[CHG-014](CHG-20261030-014-mhwi-rathalos-ue-import.md)（首次导入）

## 通道映射的确定方式

不套用记忆里的 MHW 约定，而是先量贴图本身的数值分布（`em001_00_RMT`，256² 采样）：

| 通道 | 均值 | 中位数 | p10–p90 | 近 0 占比 | 判断 |
| --- | ---: | ---: | --- | ---: | --- |
| R | 0.776 | 0.820 | 0.549–0.945 | 0.00 | **粗糙度**（有连续分布） |
| G | 0.000 | 0.000 | 0.000–0.000 | 1.00 | **金属度**（火龙无金属，恒 0 合理） |
| B | 0.073 | 0.000 | 0.000–0.322 | 0.85 | 遮罩类，未接线 |
| A | 0.297 | 0.000 | 0.000–0.996 | 0.64 | 遮罩类，未接线 |

结论：`R → Roughness`、`G → Metallic`。仍属**基于数值分布的推断**，未用原作者数据核对。

## 实施

1. 先前 RMT 贴图并未导入 UE（Blender 侧就没接，属 `unwired`）。本轮先导入 3 张：`em001_00_RMT`、`em001_00_damage_RMT`、`em001_00_eye_RMT`，均按线性数据导入（`sRGB=false`）。
2. 对 `Ch_EM001_Mt__2`、`Ch_EM001_Mt__damage`、`FakeEye_Mt__4` 各新增 `RMT` 纹理采样节点，用 `material.connect_to_property` 接 R→Roughness、G→Metallic，并保存。
3. `Scripts/MHWI/import_rathalos_mesh.py` 新增 `wire_rmt()`，重导后会自动接线，避免手工补救。

## 修改清单

| 文件/资产 | 修改内容 |
| --- | --- |
| `/Game/MHWI/Rathalos/Textures/em001_00*_RMT_tex` | 新增 3 张 RMT 贴图（sRGB 关） |
| `Content/MHWI/Rathalos/Materials/*.uasset` | 3 个材质各增 RMT 采样节点与两条连接，已保存 |
| `Scripts/MHWI/import_rathalos_mesh.py` | 新增 `wire_rmt()`（Roughness/Metallic）并接入主流程 |

## 验证

`material.read_graph`（`Ch_EM001_Mt__2`）：

```
BaseColor  -> Texture Sample (em001_00_BML_tex)
Normal     -> Texture Sample (em001_00_NM_tex)
Roughness  -> Texture Sample (em001_00_RMT_tex)
Metallic   -> Texture Sample (em001_00_RMT_tex)
Emissive   -> None
```

4 个材质 asset save 均返回 `saved`。

**未验证**：目视效果。`editor.capture_scene_png` 对同一取景返回相同字节（本轮 512×288 与上次 480×270 同为 225,665 B），无法用它判断粗糙度变化的观感差异，需在编辑器视口确认。粗糙度从常量 0.65 换成贴图后视觉变化本就细微。

## 仍未做

- `CMML`（染色/色相遮罩）、`FM`（毛发/流动遮罩）未接；当前只有基色/法线/粗糙度/金属度。
- 眼睛材质的自发光仍在（`em001_00_eye_EM`），未验证强度是否合适。
- 关卡 `L_MHWI_Training` 仍未保存。

## 回退

- 材质：删除各材质的 `RMT` 节点即可回到常量粗糙度/金属度；或将 `Roughness`/`Metallic` 断开后分别设常量。
- 贴图：删除 3 张 RMT 资产。
