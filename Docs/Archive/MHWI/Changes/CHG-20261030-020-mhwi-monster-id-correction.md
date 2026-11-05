# CHG-20261030-020：编号更正——em001 是雌火龙，火龙是 em002；并修 RMT 采样类型错误

- 状态：corrective（更正 + 部分修复）
- 日期：2026-10-30
- 需求摘要：用户反馈材质编辑器报错（截图），需处理；处理过程中发现怪物编号错误。
- 关联：[数据页](../Reference/MHWI-Rathian-LR-Data-20261030.md)、[CHG-005](CHG-20261030-005-mhwi-rathalos-datamine.md) 起的全部"火龙"批次

## 一、编号错误（本项目的判断失误）

从 CHG-005 起，本项目把 `em/em001/` 当作火龙（Rathalos）处理，依据是**未经验证的记忆假设**，当时没有做任何校验。实测后结论相反：

| 文件 | `dtt_epg` 头 `Monster_Id` | 名称表对应 |
| --- | ---: | --- |
| `em001` | **9** | 雌火龙（Rathian） |
| `em002` | **1** | 火龙（Rathalos） |

独立佐证：`common/text/trace/tr_em001_02_chS.gmd` 文本为"金色的鳞片"（金火龙＝雌火龙稀少种），`tr_em002_02_chS.gmd` 为"银色的鳞片"（银火龙＝火龙稀少种）。两条证据互相印证。

**影响范围**：`em001` 批次的 300 个文件、全部已发布数值（Health 3000、7 组硬直阈值 240/300/180/180/210/210/200、12 组肉质、发怒、疲劳 LR/HR/MR、状态累积、口水硬 300）、以及导入引擎的模型与材质，**都是雌火龙的**，不能当火龙使用。

**已做**：
- 数据页顶部加入醒目更正块，逐一说明证据与影响。
- 重新提取正确的火龙数据：`ArtSource/ThirdParty/MHWRathalos-em002/`，`em/em002/00/` + 3 份 `em002*.itlot`，共 **257 文件 / 84.21 MiB**，含 `em002_00.mod3`（3,685,384 B）与 `em002_00_tail.mod3`（646,400 B）。

**未做**：em002 的参数解析、模型转换、材质重建、引擎导入均未开始；上表所有数值需按 em002 重跑后才能发布。

## 二、RMT 采样类型报错（用户截图）

材质编辑器报：

```
SM6: (Node TextureSample) Sampler type is Color, should be Linear Color
     for /Game/MHWI/Rathalos/Textures/em001_00_RMT_tex
```

以及眼睛材质的同类报错。原因：RMT 是数据贴图，必须线性采样；之前 `import_texture` 传了 `sRGB:false`，但资产仍为 Color 采样类型，导致节点编译失败（材质图中该节点显示 ERROR），模型因此显示不出正常颜色。

处理：以 `sRGB:false` + `compressionSettings:"Masks"` 重新导入三张 RMT（`em001_00_RMT`、`em001_00_damage_RMT`、`em001_00_eye_RMT`）。

**未验证**：无法确认报错是否消失——`capture_scene_png` 已冻结，材质编译状态也没有可读接口，需用户在材质编辑器里查看。

## 三、教训

- 怪物编号不能凭记忆。第一条命令就该用 `dtt_epg` 头的 `Monster_Id` 或痕迹文本核对，成本不到一分钟。
- 本项目《工作规范》要求"官方/维护者资料先行、区分已实现与待验证"，本次在**起点**上违反了这条：把假设当事实写进了标题、文档、文件名和资产路径。

## 四、回退与后续

- `em001` 批次产物保留但已在数据页标注为雌火龙数据，不再作为火龙依据。
- 后续应将 `ArtSource/ThirdParty/MHWRathalos*` 与 `/Game/MHWI/Rathalos/*` 的命名改为按 em 编号（如 `MHWRathian-em001`、`MHW-Rathalos-em002`），避免再次混淆；本轮未做重命名。
