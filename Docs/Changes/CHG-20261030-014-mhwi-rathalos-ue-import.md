# CHG-20261030-014：火龙模型与贴图导入引擎（/Game/MHWI/Rathalos）

- 状态：completed（导入并可渲染）；未做材质精修、未做动画
- 日期：2026-10-30
- 需求摘要：模型与贴图要走到"导入引擎能够使用"，之后再进行下一步。
- 关联：[数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md) 5.1 节、[CHG-013](CHG-20261030-013-mhwi-rathalos-model-fbx.md)

## 原因与结果

CHG-013 只出了 FBX，材质仅剩名称、无贴图链接，引擎里会是白模。本轮把三件事补齐：

1. **Blender 侧重建成标准材质**：suite 的 `WorldShader`/`EM100_pre/post` 节点组 FBX 导不出，改为 Principled BSDF + 贴图节点，基色接 `BML/BM`、法线接 `NM`、自发光接 `EM`。新入口 `Tools/MHW/rebuild_monster_materials.py`。
2. **贴图随 FBX 携带**：`path_mode='COPY'` 把 PNG 复制到 `<name>.fbm/`，UE 导入时可自动建 Texture 资产。
3. **引擎内导入**：`Scripts/MHWI/import_rathalos_mesh.py` 以无头方式启动编辑器，导入 2 个 SkeletalMesh、回读贴图归位到 `Textures/`、材质归位到 `Materials/`、法线贴图设 `TC_NORMALMAP`+sRGB 关，保存并退出。

### 引擎内实际结果

| 资产 | 内容 |
| --- | --- |
| `/Game/MHWI/Rathalos/Mesh/SK_EM001_Body` | 4 个材质槽（`FakeEye_Mt__4`、`Ch_EM001_Mt__2`、`Ch_FakeSphere__3`、`Ch_EM001_Mt__damage`），**142 骨** |
| `/Game/MHWI/Rathalos/Mesh/SK_EM001_Tail` | 2 个材质槽，**3 骨** |
| `Mesh/*_Skeleton` | 两具骨架，各自独立 |
| `Textures/` | 12 张 Texture2D，其中 4 张已设为法线贴图（`em001_00_NM`、`damage_NM`、`eye_NM`、`NoImage_NM`） |
| `Materials/` | 4 个 Material，实测纹理采样：`Ch_EM001_Mt__2` → BML + NM + EM；`_damage` → damage_BM + damage_NM；其余为占位 |

**骨骼数差异**：Blender 侧为 141 骨，引擎内为 142 骨；尾巴 2 → 3。属 FBX 导入时新增根骨的常见行为，**未逐骨核对**，做重定向/挂接前必须先确认这根多出来的骨是哪一个。

## 修改清单

| 文件完整路径 | 修改内容 |
| --- | --- |
| `Tools/MHW/rebuild_monster_materials.py` | 新增：重建 Principled 材质 + 导出带贴图的 FBX |
| `Scripts/MHWI/import_rathalos_mesh.py` | 新增：引擎内无头导入、贴图/材质归位、法线设置、报告与退出 |
| `Content/MHWI/Rathalos/**` | 新增 20 个资产（2 网格 + 2 骨架 + 12 贴图 + 4 材质） |
| `Saved/MHWProbe-20261030/model-ue/`（忽略） | 带贴图的 FBX、`.fbm` 贴图副本、导入报告 |
| `Docs/Reference/MHWI-Rathian-LR-Data-20261030.md` | 5.1 节补引擎导入结果与骨骼数差异 |

## 实际验证

| 操作 | 结果 |
| --- | --- |
| Blender 重建材质并导出 | 4 个材质均有基色/法线贴图；FBX 6,476,316 B；`.fbm` 内 10 张 PNG |
| PNG 有效性 | 基色 4096×4096、法线 4096×2048、damage 1024×1024、eye 256×256，均为 8-bit RGBA |
| 无头启动 UE 导入（3 次迭代） | 退出码 0；首次因报告代码 `SkeletalMaterial.get_path_name` 与 `lod_info` 报错但资产已建成，修正后资产归位 |
| 引擎内回读校验 | 网格材质槽、骨架骨骼数、材质纹理采样均按上表确认 |

未验证项：**未在视口目视确认渲染效果**（无头运行，无截图）；未做材质精修（RMT/CMM/FM 未接线，粗糙度/金属度为常量 0.65/0）；未做 LOD1/2；未验证骨骼命名与朝向是否满足项目重定向需求；`Interchange` 已按要求关闭、走 legacy FBX 工厂。

## 风险与回退

- `Content/MHWI/Rathalos/` 是本轮新增资产，未提交；如需移除直接删除该目录即可，不影响既有 `/Game/MHWI` 内容。
- 导入脚本使用 `replace_existing=True`，重跑会覆盖同名资产；改过材质后重跑会丢失手工调整。
- 回退：删除 `Content/MHWI/Rathalos/`、两个新脚本、`Saved/MHWProbe-20261030/model-ue/`，还原数据页 5.1 节。

## 已同步文档

- [火龙数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)
- [记录索引](README.md)
