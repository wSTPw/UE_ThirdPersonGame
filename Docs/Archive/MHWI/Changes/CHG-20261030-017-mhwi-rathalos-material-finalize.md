# CHG-20261030-017：材质收尾（CMML/FM 评估、眼睛补齐、场景恢复）

- 状态：completed（材质）；关卡仍未保存
- 日期：2026-10-30
- 需求摘要：把材质相关工作一次做完，不再中途停。
- 关联：[CHG-016](CHG-20261030-016-mhwi-rathalos-rmt-material.md)（RMT 接线）

## 一、CMML 与 FM：测了，但不接

延续 CHG-016 的做法，先量通道分布再决定，不凭名称猜。

| 贴图 | 尺寸 | 通道分布 | 判断 |
| --- | --- | --- | --- |
| `em001_00_CMML` | 2048² | R 均值 0.939（p10 0.871）、G 0.952、B 1.000、A 1.000 | 近似全白，作为色调相乘几乎没有可分辨的影响 |
| `em001_00_FM` | 2048² | R 恒 0.514、G 恒 0.505、B ≈0、A 1.000 | 常量场，没有方向/细节信息 |

结论：**两者都不接**。CMML 即便接上也等于乘 0.94 的白，收益为零且多一层易错节点；FM 是常量场，接进任何通道都只是给整块模型加一个常数偏移。贴图已导入 UE（CMML 有导入，供后续裁剪/染色研究），但材质图保持只有 BaseColor / Normal / Roughness / Metallic。

> 注：`CMML` 在原作里大概率是染色区域遮罩而非直接可乘的颜色；要正确使用需要先知道染料系统的通道分配，属未解范畴，本轮不以猜测代替。

## 二、眼睛材质补齐

`FakeEye_Mt__4` 五路齐全，均为真实贴图：

```
BaseColor -> em001_00_eye_BML_tex
Normal    -> em001_00_eye_NM_tex
Roughness -> em001_00_eye_RMT_tex
Metallic  -> em001_00_eye_RMT_tex
Emissive  -> em001_00_eye_EM_tex
```

## 三、场景恢复

重新导入（`replaceExisting`）会使引用旧资产的 Actor 失效：`MHWI_Rathalos_Tail` 在前一轮重导后从大纲消失。已重新放置并挂回网格（2 个材质槽）。**这是重导流程的固有副作用，以后覆盖导入后要复查场景中的 Actor。**

## 四、四个材质的最终状态

`Ch_EM001_Mt__2`、`Ch_EM001_Mt__damage`、`Ch_FakeSphere__3`、`FakeEye_Mt__4` 全部 `asset save` 成功（4/4 saved）。共同特征：Emissive 已断开（眼睛除外）、RMT 接入粗糙度与金属度。

## 修改清单

| 资产/文件 | 修改内容 |
| --- | --- |
| `/Game/MHWI/Rathalos/Textures/em001_00_CMML_tex` | 新增（sRGB 开），仅供后续研究，未接材质 |
| `/Game/MHWI/Rathalos/Materials/*.uasset` | 4 个材质保存（RMT 接线 + Emissive 断开） |
| `L_MHWI_Training`（未保存） | 重新放置 `MHWI_Rathalos_Tail`，与 Body 并列 |

## 验证

- `material.read_graph` 复核 4 个材质：连接关系与上表一致，无孤立/自环节点。
- 期间有一次误操作：用 `connect_expressions` 把 `BaseMul` 连到自身形成自环，已删除该节点与 `CMML` 节点并复核恢复。教训：材质图编辑后必须回读 `read_graph`，不能只看 `success: true`。

## 未验证 / 未完成

- **目视效果仍未确认**：`capture_scene_png` 对同一取景恒定返回相同字节（400×225、420×236 均为 157,982 B），无法用于观感对照。粗糙度接贴图后的细微差异需在视口确认。
- 关卡 `L_MHWI_Training` 未保存（含用户未提交修改，不代为落盘）。
- CMML 的正確用法（染料/染色通道）未解；FM 的毛发/流动效果需要专用 shader，未做。

## 回退

- 材质：`Ch_*` 删除 RMT 节点即回常量；需要恢复自发光则把 `NoImage_EM_tex` 重新接 Emissive（不推荐）。
- 场景：不保存即还原；或删除两个 `MHWI_Rathalos_*` Actor。
