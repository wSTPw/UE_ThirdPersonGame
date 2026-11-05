# CHG-20261030-013：火龙模型转 FBX（本体 + 尾巴）

- 状态：completed（转换）；材质贴图未进 FBX
- 日期：2026-10-30
- 需求摘要：用户确认把已提取的模型转成可用资产，先用单文件验证插件是否支持怪物模型。
- 关联：[数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md) 第 5.1 节、[CHG-005](CHG-20261030-005-mhwi-rathalos-datamine.md)（素材提取）

## 原因与结果

模型此前只提取了原始 `mod3/mrl3/tex`。本轮用项目内便携 Blender 4.5 + Feuleur suite 做无头转换，先在单文件上验证可行，再转尾巴。

结果：

- **本体** `em001_00.mod3`：26 对象、1 骨架 **141 骨**、25 网格、**67,445 面**，FBX 6,460,428 B。
- **尾巴** `em001_00_tail.mod3`：**2 骨**，FBX 359,788 B。尾巴是独立文件而非本体子网格，接回去需要额外的骨骼挂接处理。
- **回读校验通过**：导出的 FBX 重新导入 Blender 后仍为 1 骨架 141 骨 / 25 网格 / 67,445 面。
- 贴图经 `load_mrl3` 转出 **19 张 `*.tex.png`**（写在 `nativePC/` 内，已被 `.gitignore` 忽略）。

**关键限制**：FBX **不含贴图链接**，只有材质名。带 `--mrl3` 与不带时 FBX 字节数完全相同（均 6,460,428），说明材质节点未进入导出。原因是 suite 使用自定义 shader 节点组，FBX 导出器只识别 `Principled BSDF` 一类标准输入。贴图要进引擎需另做 Principled 重建或直接在 UE 里手工接图。

另有缺件：材质引用了 `Assets/default_tex/` 下的共享默认贴图（sand_CMM、noise_BM/LIN、kizu_CMM、paint_CMM、snow_Col_CMM、null_black、null_fur_CMM 等），本轮未提取这批共享贴图，加载时告警但不中断。

## 修改清单

| 文件完整路径 | 修改内容 |
| --- | --- |
| `Tools/MHW/convert_monster_model.py` | 新增无头转换入口：加载 suite 包、导入 mod3（LOD0）、可选 mrl3、导出 FBX、写 JSON 报告 |
| `Saved/MHWProbe-20261030/model-test/`（忽略） | `em001_00_body.fbx`(6.46 MB)、`em001_00_body_mat.fbx`、`em001_00_tail.fbx`(0.36 MB) 与对应 JSON 报告 |
| `ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/mod/*.tex.png`（忽略） | 19 张贴图转换产物 |
| `Docs/Reference/MHWI-Rathian-LR-Data-20261030.md` | 第 4 节模型/动作库两行改为实际状态；新增 5.1 节记录命令、结果与限制 |

## 实际验证

| 操作 | 结果 |
| --- | --- |
| 单文件无材质转换 → 回读 | 141 骨 / 25 网格 / 67,445 面，转换与回读一致 |
| 带 `--mrl3` 转换 | 材质节点加载成功；FBX 字节数与无材质版完全相同 → 贴图未进 FBX |
| 尾巴转换 | 2 骨，359,788 B |
| `python Scripts/Docs/check_docs.py` | 见下 |

未验证项：未在 UE 中导入、未验证比例/朝向/骨骼命名是否适合 UE 骨架、未做 LOD1/2、未处理材质重建、未处理尾巴与本体骨架的挂接。

## 风险与回退

- `mod3` 的 LOD0 之外还有 LOD1/2，本轮只导 LOD0；若做远景需要另导。
- 转换会写 `nativePC/` 下的 `*.tex.png` 缓存；该目录已忽略，不影响仓库。
- 回退：删除 `Tools/MHW/convert_monster_model.py`、`Saved/MHWProbe-20261030/model-test/`、`nativePC` 下的 `*.tex.png`，还原数据页两行与 5.1 节。

## 已同步文档

- [火龙数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)
- [记录索引](README.md)
