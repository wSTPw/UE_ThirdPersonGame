# CHG-20261030-005：火龙（em001）下位数据解包与首批解码

- 状态：partial（提取完成、三类参数已解码；招式/AI/部位破坏未解码）
- 日期：2026-10-30
- 需求摘要：解包火龙完整数据，以下位数值为准，覆盖模型/动画/数值/AI/机制/招式伤害击退/部位破坏/硬直/倒地/口水硬/发怒/虚弱；本阶段只做数据收集。
- 关联：[方案](../Plans/PLAN-20261030-003-mhwi-rathian-datamine.md)、[数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)

## 原因与结果

此前项目只有太刀（`wp03`）与猎人侧数据，怪物侧仅 B13 解过 `em001.dtt_epg` 一份。本轮把 `em/em001/00/` 整套提出来并建立分类清单，同时把参数类文件接入一个通用解析器（直接解释 MHW-Editor 生成的 C# 读取序列），使后续怪物参数可以按同一套路复用。

实际达成：

- 提取 300 个文件 / 76.97 MiB，逐文件 SHA256 入清单。
- `dtt_agr`（发怒）、`dtt_sta`（体力/疲劳）字节完全消费，数值已落入数据文档。
- `dtt_epg`（部位肉质/部位 HP）本轮提取文件 SHA256 与 B13 解析时一致，沿用其校验过的结果。
- `dtt_eda` 888/896、`shlp` 925/928，**未通过自检，未输出数值**。

## 修改清单

| 文件完整路径 | 内容 | 原因 |
| --- | --- | --- |
| `ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/**`、`common/item/em001*.itlot` | 300 个原始文件 | 数据本体；二进制已加入 `.gitignore` |
| `ArtSource/ThirdParty/MHWRathalos/extraction-manifest.json` | 来源包/偏移/尺寸/SHA256 | 可追溯 |
| `Tools/MHW/em001-datamine-manifest.json` | 300 条：路径/字节/SHA256/类别/解码状态 | 机器可读清单 |
| `Tools/MHW/mhw-editor-sources.json` | 9 份结构定义的 commit 与 SHA256 | 布局来源固定 |
| `Tools/MHW/Source/MHW-Editor-b6ff379/**` | 结构定义本地缓存（已忽略） | 离线可重跑 |
| `Scripts/MHWI/parse_em_params.py` | C# 读取序列解释器 + 解密接入 + 字节自检 | 本批主要工具 |
| `Docs/Reference/MHWI-Rathian-LR-Data-20261030.md` | 数据现状与已解码数值 | 交付物 |
| `Docs/Plans/PLAN-20261030-003-mhwi-rathian-datamine.md` | 阶段规划 | 方案 |
| `.gitignore` | 忽略 `MHWRathalos/nativePC/` 与 `archive-index.json` | 与 LS 目录同策略 |

## 接口、事件与资源影响

无 C++/反射/蓝图/接口变化。未新增或修改 `/Game/` 资产。未改 `Scripts/MHWI/` 既有脚本（新脚本独立）；未覆盖 `ArtSource/ThirdParty/MHWLongSword/` 任何产物，也未覆盖用户工作区既有未提交修改。

## 实际执行与验证

| 操作 | 环境 | 实际结果 |
| --- | --- | --- |
| `extract_resources.py` 定向提取 | 本机 chunk + UE5.8 oo2core | 300 文件 / 76.97 MiB；`Extracted 300 files` |
| `parse_em_params.py` 解析 `data/` | Python 3 + Node(legacy provider) | `dtt_agr` 144/144、`dtt_sta` 92/92 通过；`dtt_eda` 888/896、`dtt_epg` 442/1360（该文件另有既有解析器，见下） |
| SHA256 交叉核对 | 本机 | 本轮 `em001.dtt_epg` = `2ffdcb81…`，与 B13 解析源一致，故沿用其结果（Health 3000、7 段硬直、12 部位、1 段切断 300） |
| `parse_em_params.py` 解析单个 `shlp` | 同上 | 解析至 925/928 字节后越界，判 FAIL，未输出数值 |
| `shlp` 结构逐类核查（追加） | 同上 | `Shlp`/`Shlp_1_`/`Child_Shell_Params`/`Assets` 等类合计只含 EPV 索引、关节号、碰撞与时间轴路径、子判定、音效、投射体、修饰符，**无伤害/击退/气绝字段**；据此否决"修 shlp 得伤害表"的路线 |
| MHW-Editor 结构下载校验 | GitHub API | 9 个文件大小与 SHA256 全部与仓库一致 |

未验证项：所有数值**未做运行验证**（未启动游戏或 UE）；`dtt_epg` 的部位组号→部位名映射未解；`00/01/02` 变体身份为推断；`shlp`/`actp2`/`thk`/`em_pbc`/`em_dmg` 未解码，故本批**没有**任何招式伤害、击退、部位破坏阈值、口水硬/倒地时长数字。

## 风险、遗留与回退

- 结构定义来自社区生成代码（MIT），字段语义非官方；中文名称为推断，不得直接作为还原依据。
- 游戏更新后 `archive-index.json` 失效，需换新输出目录重建索引。
- 二进制素材仅留本机；仓库只保存清单与脚本。
- 回退：删除 `ArtSource/ThirdParty/MHWRathalos/`、`Tools/MHW/em001-datamine-manifest.json`、`Tools/MHW/mhw-editor-sources.json`、`Tools/MHW/Source/MHW-Editor-b6ff379/`、`Scripts/MHWI/parse_em_params.py`、两篇文档与 `.gitignore` 两行。无代码/资产需恢复。

## 已同步文档

- [数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)
- [方案](../Plans/PLAN-20261030-003-mhwi-rathian-datamine.md)
- [解包数据管理与统计](../Systems/MHWI-Unpack-Data.md)
- [采集工具说明](../../Tools/MHW/README.md)
- [记录索引](README.md)
