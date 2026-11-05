# CHG-20261030-004：新增 MHWI 解包数据管理与统计文档

- 状态：completed（文档）；仅新增/链接文档，未改代码、资产、游戏安装或提取产物。
- 日期：2026-10-30。
- 需求摘要：用户要求写一份专门针对解包数据管理的文档，并适配现有文档结构。
- 关联：前序素材事实见 [CHG-20261022-001](CHG-20261022-001-mhw-longsword-source-assets.md)；无接口变化。

## 原因与结果

现有"解包流程"只散落在 [Tools/MHW/README.md](../../Tools/MHW/README.md)（命令与工具来源）与 CHG-20261022-001（执行结果），`Docs/` 内没有一处集中说明**索引全量、提取选择性、统计口径、入库边界、重抽判定**。此前"13 个包 / 171,615 条路径 / 140 个文件"等数字分散在 6 篇文档里，容易被误读为"已全量解包"或把条目尺寸当成磁盘占用。

新增 [MHWI 解包数据管理与统计](../Systems/MHWI-Unpack-Data.md)，把这些事实收在一处，并补充按归档包、扩展名、顶层目录、太刀取材前缀的统计表。

统计口径首次写清：`archive-index.json` 的 `offset` 位于**解压后数据流地址空间**（`extract_resources.py` 按 `0x40000` 块 Oodle 解压 + 密钥异或后按偏移取窗口），因此"唯一区间合计 69.57 GiB"与"物理 51.13 GiB"并存，两者都不是解包后磁盘占用。

## 统计结果（2026-10-30 只读复核）

| 指标 | 数值 |
| --- | --- |
| 归档包 | 13 个 `chunkG*.bin`，物理合计 51.13 GiB |
| 索引条目路径 | 171,615 |
| 唯一存储区间 | 143,531（28,084 条路径共享其它路径的区间） |
| 唯一区间合计 | 69.57 GiB（解压口径） |
| 扩展名种类 | 419 |
| 首轮提取 | 140 个文件 / 52,004,942 B（49.60 MiB） |
| 参数提取 | 48 个文件 / 242,071 B（0.23 MiB） |
| 探针重抽 | 41 个文件 / 6.55 MiB（`Saved/`，不入库） |
| 已跟踪素材 | 167 个文件 / 295.9 MiB |

静态发现两项，均只记录未处置：

1. `chunkG10.bin` 有物理内容但索引中 0 条 `kind == 0` 条目，未追查条目类型。
2. `.gitignore` 只排除首轮 `nativePC/`、`Converted/` 与工具缓存，而 `NativeParameters/` 的 48 个原版参数二进制与 R06 批次 63 个文件（59 个 FBX + 4 个 journal JSON）实际已入库，与"二进制素材默认留本机"的表述存在差异。

## 修改清单

| 文件完整路径 | 内容 | 原因 |
| --- | --- | --- |
| `Docs/Systems/MHWI-Unpack-Data.md` | 新增现状页：数据性质、目录职责、索引口径与四张统计表、三级提取、入库边界、复现与保护机制、重抽判定、禁止推论 | 本次主体 |
| `Docs/README.md` | 快速阅读表新增"解包数据在哪、有多少"一行 | 入口可发现 |
| `Docs/Reference/modules.json` | 新增模块 `mhwi-unpack-data`（`asset_roots` 为空，非 UE 模块） | AI 可解析入口 |
| `Docs/Systems/MHWI-LongSword.md` | 页首加一句指向解包数据页，划清"素材取得"与"进入 `/Game/MHWI` 后实现" | 避免两页职责重叠 |
| `Tools/MHW/README.md`、`ArtSource/ThirdParty/MHWLongSword/README.md` | 各加一行指向新页 | 双向可追溯 |
| `Docs/Changes/README.md` | 新增本条索引 | 记录索引维护 |

## 接口、事件与资源影响

无 C++/反射/蓝图/接口变化。未新增 `asset_roots`（本模块不产出 `/Game/` 资产），未改 `Content/`、`Scripts/`、`Saved/`、游戏安装。用户工作区中既有未提交修改（`Content/MHWI/*`、`Source/IntroCpp/MHWI/MHWICharacter.cpp`、`Scripts/MHWI/*`、4 篇今日新增文档）未被覆盖；`modules.json` 是追加新条目，未改动 `mhwi-longsword` 既有内容。

## 实际执行与验证

| 操作 | 环境 | 实际结果 |
| --- | --- | --- |
| 只读统计脚本（archive-index / extraction-manifest / git ls-files 汇总） | 本机 Python 3 | 取得上表全部数字；未写任何文件、未重抽、未启动游戏或 UE |
| `git status --short` | 项目根目录 | 30 项既有修改/未跟踪，已在修改前列出并避开 |
| `python Scripts/Docs/check_docs.py` | 项目根目录 | PASS：152 篇 Markdown、1,288 个本地链接、13 个模块、编辑器快照 JSON |
| `git diff --check -- Docs Tools/MHW/README.md ArtSource/.../README.md` | 本次修改范围 | 通过（exit 0），无空白错误 |

未验证项：新页所有数字来自既有 JSON 与磁盘状态，**未重新解包验证**；`chunkG10.bin` 条目类型、69.57 GiB 与 51.13 GiB 差值的完整构成（块压缩 + 跨包覆盖残留各占多少）均未拆分。

## 风险、遗留与回退

- 统计数字随游戏更新失效；重抽或换机后需按第七节判定重建，不能沿用本文数值。
- 入库边界差异属未决事项，本文档只记录，不代为删除或补 `.gitignore`。
- 回退：删除 `Docs/Systems/MHWI-Unpack-Data.md`，撤销 `Docs/README.md`、`Docs/Reference/modules.json`、`Docs/Systems/MHWI-LongSword.md`、`Tools/MHW/README.md`、`ArtSource/ThirdParty/MHWLongSword/README.md` 中对应行，删除本条与索引行。无代码或资产需要恢复。

## 已同步文档

- [MHWI 解包数据管理与统计](../Systems/MHWI-Unpack-Data.md)
- [技术入口](../README.md)
- [MHWI 太刀训练模组](../Systems/MHWI-LongSword.md)
- [采集工具说明](../../Tools/MHW/README.md)
- [源素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md)
- [记录索引](README.md)
