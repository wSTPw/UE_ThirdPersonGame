# CHG-20261030-019：按视口反馈调光并隐藏损坏部位网格

- 状态：completed（场景调整）；关卡未保存
- 日期：2026-10-30
- 需求摘要：用户提供编辑器截图，需要据此处理材质与观感。
- 关联：[CHG-018](CHG-20261030-018-mhwi-rathalos-material-restore.md)

## 截图确认到的事实

用户截图（`L_MHWI_Training`，选中 `MHWI_Rathalos_Body`）显示：右侧"细节"面板列出 **4 个材质槽**（`FakeEye_Mt__4`、`Ch_EM001_Mt__2`、`Ch_FakeSphere__3`、`Ch_EM001_Mt__damage`），与 CHG-018 的 Actor 覆盖一致 —— **材质已正确挂上，不再是丢失状态**。

同时暴露两个观感问题：整体偏白、轮廓多出"毛发状"尖刺。

## 问题一：偏白是打光过曝

场景同时存在四层光：天光 2.5、主光 5、填充光 3、以及我在 CHG-018 加的临时点光 8000。翼膜在原始贴图里本就偏灰白，叠加过曝后整体读作白色。

处理：删除临时点光 `MHWI_Rathalos_KeyLight`；天光 2.5 → 1.5；主光/填充光维持原值 5/3。

## 问题二：损坏部位网格被同时显示

轮廓上的尖刺状几何是 `Ch_EM001_Mt__damage` 那 5 片网格（Blender 侧为 `LOD0_G200_I84`–`G204_I88`，合计约 4.5k 面）。它们在原作里是**部位破坏后**才替换显示的破损状态，现在与完好网格叠加渲染，所以看起来像长了毛。

处理：新建 `M_HiddenSlot`（BlendMode = Masked，`Constant 0 → OpacityMask`，已保存），赋给 `MHWI_Rathalos_Body` 的槽 3 与 `MHWI_Rathalos_Tail` 的槽 1。这样保留材质槽位结构，只是渲染时不可见；后续要做部位破坏表现时，把该槽换回 `Ch_EM001_Mt__damage` 即可。

## 修改清单

| 项 | 内容 |
| --- | --- |
| 删除 | `MHWI_Rathalos_KeyLight`（临时点光） |
| `MHWI_SkyLight` | Intensity 2.5 → 1.5 |
| 新增资产 | `/Game/MHWI/Rathalos/Materials/M_HiddenSlot`（Masked，opacity 0） |
| Actor 覆盖 | Body 槽3、Tail 槽1 → `M_HiddenSlot` |

## 验证与限制

已验证：材质槽列表（截图）、`M_HiddenSlot` 保存成功、两处 Actor 覆盖写入成功、天光读回 1.5。
**未验证**：`capture_scene_png` 仍冻结在 112,860 B（换尺寸/相机/重绘均无效），无法目视确认调光与隐藏效果，需用户在视口确认。

## 遗留

- 若隐藏损坏部位后主体仍偏灰，则问题在反照率而非光照，下一步应做无光照对照（临时把 BaseColor 接自发光并切 Unlit）来隔离。
- 关卡未保存；不保存则上述调整只存在于当前会话。
- 材质仍挂在 Actor 覆盖上，网格资产自身槽位依旧为空。

## 回退

把 Body 槽3 / Tail 槽1 换回 `Ch_EM001_Mt__damage` 即恢复显示损坏部位；天光与点光的改动不保存即还原。
