# CHG-20261030-018：恢复火龙材质显示（槽位丢失 + 光照）

- 状态：completed（材质显示链路）；关卡未保存
- 日期：2026-10-30
- 需求摘要：用户反馈材质"全消失"，要求还原。
- 关联：[CHG-017](CHG-20261030-017-mhwi-rathalos-material-finalize.md)

## 现象与原因

材质资产（4 个 `.uasset`）仍在磁盘上，材质图也未被破坏。真正丢的是**引用**与**亮度**：

1. **引用丢失**：上一轮 `import_skeletal_mesh(replaceExisting=true)` 重建了网格资产，网格自身的材质槽被重置，导致 Actor 渲染回退到默认材质。`asset.set_mesh_material` 只支持静态网格，对 SkeletalMesh 直接报 "Failed to load static mesh"，无法用它修。
2. **亮度塌陷**：`NoImage_EM` 白图自发光被断开后（CHG-015 的正确修复），模型只靠场景光照明；而 `L_MHWI_Training` 的定向光是 Stationary/烘焙，改强度不实时生效。两者叠加，模型看起来发黑。

## 处理

| 步骤 | 内容 |
| --- | --- |
| 材质归位 | 用 `level.set_actor_material` 给 `MHWI_Rathalos_Body` 四个槽位显式指定 `FakeEye_Mt__4`、`Ch_EM001_Mt__2`、`Ch_FakeSphere__3`、`Ch_EM001_Mt__damage`；`MHWI_Rathalos_Tail` 两槽指定 `Ch_EM001_Mt__2`、`Ch_EM001_Mt__damage` |
| 清理孤立节点 | `Ch_EM001_Mt__2` 删除残留的 `NoImage_EM` 采样后 `valid=true`（expr 3 / reachable 3）；另两个材质仍有 1 个孤立采样（节点名为空，接口无法按名删除），不影响编译与渲染 |
| 补光 | 新增可移动点光 `MHWI_Rathalos_KeyLight`（(-300,-300,600)，8000，半径 2500），绕开烘焙光 |
| 保存 | 4 个材质 `asset save` 全部成功 |

## 验证

| 项 | 结果 |
| --- | --- |
| 材质资产 | 4 个文件均在 `Content/MHWI/Rathalos/Materials/` |
| 材质有效性 | `Ch_EM001_Mt__2`/`FakeEye_Mt__4` valid=true；另两个仅 orphan 警告 |
| 基色连接 | 4 个材质的 BaseColor 均指向真实贴图（`FakeSphere` 用 `NoImage_BM` 属预期） |
| Actor 覆盖 | Body 四槽、Tail 两槽覆盖已确认写入 |

**未能目视确认**：`editor.capture_scene_png` 在多次调用后彻底冻结——不同分辨率、不同相机、不同光照、加补光后均返回同一字节数（112,860 B），只有一次在 `redraw_viewport(invalidateHitProxies)` 后拿到过新帧（该帧显示模型偏黑，即上述亮度问题的证据）。该接口不能用于验证观感，必须由人在视口确认。

## 风险与遗留

- 材质目前挂在 **Actor 覆盖** 上，只有保存关卡才会持久化；网格资产自身的材质槽仍为空。若要不依赖关卡，需要重新导入并保留材质，或在编辑器里手工给网格赋材质后保存网格资产。
- 两个材质各留一个孤立采样节点（`NoImage_EM_tex_ncl1_*`），节点名为空，`delete_expression` 按名找不到；不影响渲染。
- 场景新增一盏点光，属临时补光，可按需删除。

## 回退

- 删除两个 Actor 或撤销关卡修改即可移除覆盖材质与补光；材质资产本身不动。
