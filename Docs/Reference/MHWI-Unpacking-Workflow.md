# MHWI 现有解包方式与复现流程

- 更新：2026-10-30；状态：现有脚本与产物的静态核对，非新增解包工具或技术选型。
- 适用：本机 Steam《Monster Hunter World: Iceborne》的 `chunk/chunkG*.bin`；工具宿主使用 Python、Blender 4.5.0、UE 5.8 本地 Oodle 库。未证明适用于更新后的游戏归档、主机版或 Iceborne 更新前格式。
- 本轮验证：太刀素材 140/140、太刀参数 48/48、火龙 300/300 条清单记录对应的本地文件尺寸/SHA256 一致；这些是按批次计的 488 条记录，不能当作互不重复的路径数。未重抽、重跑解析/转换、启动游戏或 UE。
- 分工：[解包数据管理](../Systems/MHWI-Unpack-Data.md)维护目录、统计与入库边界；本文说明现有方法、执行顺序和失败判定；[工具说明](../../Tools/MHW/README.md)保留素材制作的详细命令。

## 来源、版本与证据边界

这里的“上游”指工具维护者，不是 Capcom 发布的原作机制规范。先查询维护者资料，再核对项目脚本；官方 UE 文档不能证明 MHWI 原作行为。

| 直接来源与适用版本 | 维护者资料结论 | 项目现状证据 |
| --- | --- | --- |
| [JodoZT/MHWNoChunk 源码 Chunk.cs](https://github.com/JodoZT/MHWNoChunk/blob/master/MHWNoChunk/Chunk.cs)，项目缓存为 2026-10-22 master snapshot | 提供 Iceborne chunk 分块读取、解压及密钥处理实现 | [extract_resources.py](../../Tools/MHW/extract_resources.py)读取未修改的 `Chunk.cs` 与 `Resources/chunk.key`，自行实现命令行定向提取；不是调用 MHWNoChunk GUI |
| [Feuleur MHW tool suite 1.3.9](https://github.com/Feuleur/blender-mhworld-tools-suite/releases/tag/1.3.9)、[维护者说明](https://github.com/Feuleur/blender-mhworld-tools-suite) | 提供 MHW 素材导入器 | 项目 `inspect_source_assets.py`、`build_asset_bundle.py`、`finish_materials.py` 使用本地发布包；归档版本/SHA256 见 [tool-sources.json](../../Tools/MHW/tool-sources.json) |
| [wowo-dot/mhw-anim-tools](https://github.com/wowo-dot/mhw-anim-tools)，项目记录缓存 v1.1.0；上游目标为 Blender 4.5 LTS | 提供 LMT/TIML 工具及 CPU 姿态求值能力 | [native_animation_source.py](../../Scripts/MHWI/native_animation_source.py)只加载 reader/pose 模块；项目实际逐文件指纹见 `NativeFidelity/export-manifest.json`，不能用上游当前分支替换后沿用旧资格结果 |
| [Synthlight/MHW-Editor](https://github.com/Synthlight/MHW-Editor)，固定 commit `b6ff379b13079a4abb99490590fb05dfe6851bbc`；[W03P 定义](https://github.com/Synthlight/MHW-Editor/blob/b6ff379b13079a4abb99490590fb05dfe6851bbc/MHW-Generator/Weapons/Wp03Param.cs) | 提供数据文件布局、字段名称及资源加解码实现 | [太刀布局指纹](../../Tools/MHW/native-parameter-sources.json)、[怪物布局指纹](../../Tools/MHW/mhw-editor-sources.json)固定来源；项目读取模板/生成 C#，不运行编辑器程序 |

本轮维护者仓库/发布说明已查询；固定 W03P 网页抓取未成功，其版本依据来自项目固定来源清单及本地解析器。上游能力、项目执行结果、语义推断分别记录：字段有名字不证明消费者已闭合；`00/01/02` 的变体身份、未知位域的取消含义仍按对应取证页标注，不能写成已核实原作行为。

## 现有方法怎么分工

```text
只读游戏 chunkG*.bin
  → 分块 Oodle 解压 + 异或 → PKG 索引 → 合并同路径 → 正则定向提取
  → 批次 nativePC/ + extraction-manifest.json
      ├─ 模型/材质/动画 → Blender 检查依赖 → FBX/PNG/blend
      ├─ 太刀参数/TIML/FSM/IK → 固定布局解析 → 原始数据库与校验报告
      └─ 怪物参数 → C# LoadData 读取序列解释 → 逐文件 ok/consumed 报告
消费者仍未知的字段 → 对应固定版本 EXE 静态取证/原作运行证据（独立阶段）
UE 导入和玩法适配 → Scripts/MHWI 的 author/import 入口（独立阶段）
```

| 方法 | 现有入口 | 产物及边界 |
| --- | --- | --- |
| 归档提取 | `Tools/MHW/extract_resources.py` | 原始字节与来源清单；不解读字段、不导入 UE |
| 素材检查与通用转换 | `inspect_source_assets.py` → `build_asset_bundle.py` → `finish_materials.py` | `source-inventory.json`、`Converted/`；贴图可能需要按依赖追加提取，模型/材质不等于原版 shader 完整复现 |
| 动画源采样旁路 | `native_animation_source.py`、`export_native_animation.py`、`verify_native_animation.py`；武器侧 `native_weapon_export.py` / `native_weapon_verify.py` | `NativeFidelity/` 的独立采样/FBX 重读证据；保留源 LMT 和 Converted，不假定所有 NeedsParent 动作可独立求值 |
| 太刀参数批处理 | `extract_native_longsword_params.py`、`build_native_action_database.py`、`extract_native_equipment_params.py`、`read_source_fsm.py` | 固定布局 W03P、TIML/FSM 原始条件与 IK 结构；不是原生执行器，详见[参数批处理](MHWI-Native-Parameter-Pipeline.md) |
| 怪物参数读取 | [parse_em_params.py](../../Scripts/MHWI/parse_em_params.py) | 解释 C# `LoadData(BinaryReader, ulong)` 读取序列；当前仅映射 `dtt_epg/dtt_agr/dtt_sta/dtt_eda/shlp`，并非任意 C# 或所有怪物格式解析器。`shlp` 虽可解析，但其结构不含伤害类字段 |
| 消费者取证 | `extract_exe_recon.py`、`trace_native_connections.py` 等既有专项脚本 | 固定 EXE/分析代码区/函数范围/源哈希；不能把压缩 chunk 字节当 CPU 指令。证据和运行缺口见 [B17 收尾](MHWI-Forensic-Completion-20261026.md) |

上述脚本分别位于 [Tools/MHW](../../Tools/MHW) 和 [Scripts/MHWI](../../Scripts/MHWI)。当前归档入口没有接入 WorldChunkTool CLI、通用 UE Pak/IoStore 提取或 GUI 自动化；本文不新增替代方案。

2026-10-30续查新增独立入口：`read_action_params.py`完整读ACTP2；`read_monster_collision.py`按维护者Atk2读取70条火龙攻击原记录；`inspect_parts_break.py`/`inspect_parts_break_native.py`核对PBC类CRC和嵌套读写。实际版本、适配、输出与语义边界见[格式续查](MHWI-Rathian-Format-Evidence-20261030.md)。SHLP未见伤害字段不代表数值只能在ACTP2。

## 新增的格式解析与取证流程（2026-10-30）

归档层仍使用原有chunk索引/Oodle/正则提取。新增能力位于提取后的格式层；本节归纳CHG-011已执行结果，本次文档整理未重跑解析。前文488条文件校验是原文档批次记录，不代表没有执行过后续解析。

### 按格式选择读取路线

| 目标 | 已验证的方法 | 成功标准与边界 |
| --- | --- | --- |
| ACTP2动作参数 | 固定维护者actp2.bt与UnitProperty.bt，按Property类型标签、值、元数据和变长字符串读取 | 完整消费并独立重编码逐字节一致；本机342记录/4295属性。拒绝未知tag/版本、截断、计数越界和尾部；数组索引不是已证动作ID |
| 怪物COL攻击字段 | 根据Names和CLND/CLGM计数顺序定位ATK，按类型2的47字段/171B读取 | 42份COL共70攻击原记录，保留原文名称/攻击索引/UID/字段偏移；几何与OAP尾部仍opaque，不能据字节收集宣称全语义解码 |
| PBC类型与样本结构 | 对真实类名重算反CRC32，和历史DTI及文件常量交叉核对 | 三常量匹配Info/State/Detail；只对4份固定样本做形状检查，未知载荷保留raw |
| PBC序列化归属 | 复用固定EXE/text指纹的NativeTrace，核对加载/保存调用链和owned unwind范围 | 6函数/24关键指令/7字段对象偏移可追；三层数组计数决定展开长度，48B不是通用步长，不命名未知业务字段为耐久 |

维护者直接来源：[Fexty固定模板](https://github.com/Fexty12573/MHW-010-Templates/tree/cea17f2c0c7d5c4f2ed421a7d0e04586bfb275f7)、[Synthlight固定COL模板](https://github.com/Synthlight/MHW-Editor/blob/b6ff379b13079a4abb99490590fb05dfe6851bbc/010%20Templates/col.bt)、[历史DTI](https://github.com/Andoryuuta/MHW-DTI-Dumps/blob/4a124e4073519eaf19e3a446cb62d375d8da3209/dti_prop_dump.h)。ACTP2采用同源Property包装的项目适配，非原样执行模板；来源hash与完整证据见[格式续查](MHWI-Rathian-Format-Evidence-20261030.md)。这些资料支持读取机制，不证明原作业务语义。

### 实际执行顺序

1. 保持原始提取批次与清单，先校验资源和维护者缓存的尺寸/hash；换版本必须重新资格核对。
2. 按格式运行下列入口。ACTP2、COL可独立执行；PBC先核对样本/类CRC，再核对固定代码读写归属。不为未知字段先做词表猜测或自相关切片。
3. 分别保存原始字段报告、完整消费/往返结果、未解释区域和候选映射；报告成功状态只对其声明的读取范围成立。
4. 更新分类清单decode及现状文档。只有消费者/等级资格/运行证据闭合后，才能把原字段提升为原作机制结论。

```powershell
python Scripts/MHWI/read_action_params.py --self-check
python Scripts/MHWI/read_monster_collision.py
python Scripts/MHWI/inspect_parts_break.py --self-check
python Scripts/MHWI/inspect_parts_break_native.py
```

完整ACTP2/COL报告在`Saved/MHWRathalos-20261030-Format/`，不随仓库交接；紧凑证据和`rathalos-*-sources.json`在`Tools/MHW/`。ACTP2/PBC默认重写各自报告，COL拒绝替换不同内容报告；保留历史时用各自CLI输出参数指定新文件。当前工具限定已固定的火龙资源/类型与代码版本，不能直接宣称适配所有怪物。

### 可复用的调查经验

- 有类型标签与字符串的格式，优先查询维护者完整模板及其依赖，再验证变长读取和独立重编码；弱自相关峰值不能替代结构依据。
- 一种资源没有目标字段，只能得出该资源的限定负结果。SHLP无直接伤害字段，不能推出伤害只能在ACTP2；本次实际载体是COL Atk2。
- 重复常量先与有出处的真实类型名/CRC核对。DTI用于身份参考，旧虚表地址不能自动套当前构建。
- 固定长度重复可能是嵌套计数相同的结果，须用加载/保存链核实；未知业务含义继续保留unknown。
- 原表Motion_Value不是实战扣血；00碰撞库混含G級标签，不能整批标下位。动作名CRC候选及mLoopTime也不能直接证明完整倒地/口水硬时长。

本节是已验证方法的归纳，不选择新的业务推断方案。仍需决策的消费者追踪/运行候选与代价见格式续查末节；文档变更见[CHG-012](../Changes/CHG-20261030-012-mhwi-workflow-format-methods.md)。

## 归档读取的实际规则

源码证据：`extract_resources.py::Archive.__init__/block/read/entries` 与 `main`。

1. 扫描 `--game/chunk/chunkG*.bin`，按 `G` 后数字升序读取；`catalog.update` 使较后包覆盖同一路径，得到合并视图。它不保留该路径每个旧包版本，也不读取游戏根目录的 MOD `nativePC/`。
2. 校验 CMP 头；每个逻辑块为 `0x40000` 字节。压缩块调用 `OodleLZ_Decompress`，未压缩块直接读取；然后按上游密钥顺序异或。`Archive.read` 按逻辑偏移拼接窗口，LRU 最多缓存 32 块。
3. 校验解压流的 `PKG ` 标识，只收集 `kind == 0` 文件条目。`archive-index.json` 的 `offset` 是解压流地址，不能直接用于物理 bin 的 `seek`。索引为文件条目的合并视图，不代表所有条目类型都已解析。
4. 无 `--pattern` 时只建立/复用索引并写出 `player-candidates.json`；它的候选筛选仅针对 `pl/` 中部分模型/动画，不是全素材候选表。即使仅索引，仍需 Oodle 和上游源码/密钥缓存。
5. 有 `--pattern` 时用 `re.search(..., re.I)` 匹配游戏内路径，路径分隔符为 `/`；先汇总条目尺寸，超过 `--max-mb × 1024²` 或零匹配则拒绝。提取到 `<output>/nativePC/<原路径>`，记录包/偏移/尺寸/SHA256。
6. 已有索引必须匹配游戏绝对路径、当前所有包名及各包 `size/mtime_ns`，否则要求新输出目录；这不是全归档 SHA256 校验。原始目标同名且 hash 不同则拒绝覆盖；相同内容仍会重写。

脚本的“只读”指游戏输入，不代表无输出：索引、候选、原始资源和清单都会写入 `--output`。本机 Oodle 路径来自 UE 5.8，不是上游要求的 DLL 文件名；跨机器能否兼容须重新验证，不能只重命名 DLL 视为通过。

## 可复现操作顺序

以下为待执行的参考命令，本轮没有执行。PowerShell 从项目根目录运行；先恢复 [工具说明](../../Tools/MHW/README.md)中的本地缓存，并按 [tool-sources.json](../../Tools/MHW/tool-sources.json)核对下载归档 SHA256。Python 需支持 `Path.is_relative_to`（3.9+）；使用与本机 Oodle 匹配的 Windows Python，参数解密另需 Node.js。

### 先建索引，再决定提取范围

使用独立批次目录，避免覆盖历史清单；示例位于忽略的 `Saved/`。不手工把整个安装目录复制进项目。

```powershell
$gamePath = 'F:\PCprogram\Steam\steamapps\common\Monster Hunter World'
$oodlePath = 'E:\UE\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\runtimes\win-x64\native\oo2core.dll'
$batchPath = 'Saved/MHWUnpack-20261030-Workflow'
python Tools/MHW/extract_resources.py `
  --game $gamePath --oodle $oodlePath --output $batchPath
```

检查 `<batch>/archive-index.json` 的 `source/archives/files`，先确定完整资源前缀和后缀。不要把 171,615 条已合并索引当作已提取文件数，历史统计见[管理页](../Systems/MHWI-Unpack-Data.md)。

下表是既有取材规则，可替换命令的正则；太刀动作参数与模型分别位于 `hm/wp/wp03/` 和 `wp/swo/`，不能只搜索一个目录。

| 目标 | 现有正则/依据 |
| --- | --- |
| 太刀动作、参数及公共猎人动作 | `^(hm/wp/wp03/|hm/common/mot/co00_00/)`；完整首轮模型/猎人选择见工具说明 |
| 精确重建太刀参数批次 | 使用 `NativeParameters/extraction-manifest.json` 中的 `pattern` 和文件表，避免另猜 48 项资源集合 |
| 雌火龙当前批次（em001） | `^(?:em/em001/00/|common/item/em001(?:_0[12])?\.itlot$)`；297 条目录资源 + 3 份掉落表 |

例如重抽既有雌火龙范围到这个新批次：

```powershell
python Tools/MHW/extract_resources.py `
  --game $gamePath --oodle $oodlePath --output $batchPath `
  --pattern '^(?:em/em001/00/|common/item/em001(?:_0[12])?\.itlot$)' `
  --max-mb 256
```

本机已有火龙清单为 300 条、80,708,036 B；这里只复用取材范围，命令不会修改现有 `MHWRathalos/` 目录。下位字段在资源内部的 LR 段；目录 `00` 不应直接等同下位专用目录，见[火龙数据现状](MHWI-Rathian-LR-Data-20261030.md)。

### 提取后先验原始文件，再解析或转换

检查 `extraction-manifest.json` 的 `source/pattern/total_bytes/files`；逐记录核对 `<batch>/nativePC/<path>` 的 `size` 与 SHA256。例如单文件可用 `Get-FileHash -Algorithm SHA256 -LiteralPath '<完整文件路径>'`。清单本身不是外部可信签名，同时手工改文件与清单不能证明与归档一致；需要更强证明时按记录从原包重抽到另一个目录后比较。

- 图片/模型/通用动画：按[工具命令](../../Tools/MHW/README.md)执行依赖检查，再补共享/default 贴图，最后转换。第二轮若复用同一输出目录，正则须保留首轮集合，或改用独立批次留存各轮清单。
- 太刀原始参数：在原 `NativeParameters/` 已恢复且布局缓存完整时，运行下列既有入口。它们输出到脚本固定的 `Saved/MHWIImport/NativeParameterResearch-20261024/`，会重写同名报告；日期是历史路径标识，不是本次执行日期。

```powershell
python Scripts/MHWI/extract_native_longsword_params.py --fetch-layout
python Scripts/MHWI/build_native_action_database.py
```

`--fetch-layout` 只恢复太刀来源清单中缺失的固定文件，先校验 SHA256；不同内容的已有缓存拒绝覆盖。资源解密是独立于 chunk 的第二层：按固定实现进行字序转换 → Node.js `--openssl-legacy-provider` 下的 Blowfish ECB → 字序还原；不会向游戏目录回写解密内容。不要把这一步和 Oodle 分块解压混为一谈。

怪物参数先核对 [mhw-editor-sources.json](../../Tools/MHW/mhw-editor-sources.json)中 9 份布局的固定版本/hash，并恢复太刀来源清单中的 `EncryptionKeys.cs` 等解码依赖；`parse_em_params.py` 不自动下载；当前可用 `--pins` 在解析前校验这些布局 hash。以下命令读取现有火龙数据：

```powershell
python Scripts/MHWI/parse_em_params.py `
  --layouts 'Tools/MHW/Source/MHW-Editor-b6ff379' `
  --input 'ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/data' `
  --keys 'Saved/MHWIImport/NativeParameterResearch-20261024/MHW-Editor/MHW-Template/EncryptionKeys.cs' `
  --pins 'Tools/MHW/mhw-editor-sources.json' `
  --out 'Saved/MHWUnpack-20261030-Workflow/em001-params.json'
```

该入口只遍历 `--input` 的直接子文件，不递归；shell 参数位于另一目录时需另开输入/报告。退出码 0 仅表示本次实际处理的文件无失败，不证明预期资源全部处理：未映射扩展名、缺布局的文件会跳过，必须同时核对 `files` 与预期集合。报告逐文件要求 `ok == true`，且 `consumed == size`，或明确记录当前政策接受的≤64 B全零尾（`zero_tail`）；后者仅为未解释零尾判据；`MISMATCH` 仍可能带有部分 `data`，不得据此发布数值。

当前历史结果仅 `dtt_agr/dtt_sta` 在通用入口完整消费；`dtt_epg` 在通用入口不完整，现有表值来自独立的 [extract_native_parts.py](../../Scripts/MHWI/extract_native_parts.py)及源 hash 互证；`dtt_eda` 后续已按888+8全零尾判据接受（CHG-008），本轮未重跑。`shlp` 另有结论：`rShellParam` 各类字段只含 EPV 索引、关节号、碰撞/时间轴路径、子判定、音效与投射体，**没有伤害/击退/气绝字段**，故即使在长度上对齐也拿不到招式数值——该路线的负结果见[火龙现状](MHWI-Rathian-LR-Data-20261030.md)第 4 节。本文没有重新验证这些解析结果，详见[火龙现状](MHWI-Rathian-LR-Data-20261030.md)及 [CHG-005](../Changes/CHG-20261030-005-mhwi-rathalos-datamine.md)。

本轮补充：`parse_em_params.py` 新增 `--pins` 参数，解析前逐份校验 [mhw-editor-sources.json](../../Tools/MHW/mhw-editor-sources.json) 的 SHA256，不一致直接退出（`R-DATA-002` 的布局校验缺口已闭合）。该参数不自动下载；启用`--pins`时清单缓存缺失/hash不同会在读取前停止，不按成功跳过。

## 失败、覆盖与恢复边界

| 情况 | 当前实际行为/处置 |
| --- | --- |
| 索引源或包时间戳/尺寸不同 | 拒绝复用；另开输出目录重建，不手改 stamp 强行继续 |
| Oodle 加载/解压失败，或 CMP/PKG 头错误 | 检查本机 DLL、架构、归档与源码/密钥缓存；不把补零/改后缀视为修复 |
| 正则无匹配/超预算 | 在资源写出前终止；已有索引仍可能已经写出。缩小范围或在确认范围后调整预算 |
| 路径含逃逸或目标内容冲突 | 拒绝当前文件；此前文件可能已经落盘。改用独立批次，保留冲突证据 |
| 同一输出目录多次提取 | 原文件保留但 `extraction-manifest.json` 只记录最近成功调用的选择集合，**不会自动合并**。新清单不能覆盖证明所有残留文件 |
| 提取中途异常 | 没有事务回滚；旧清单可能仍在或新清单尚未生成。目录存在不等于本次完成；按日志和逐文件清单复核，优先用新批次重建 |
| C# 布局读取长度不符/扩展名无解析器 | 分别记录 FAIL、MISMATCH 或跳过；保留原字节与 hash，不猜 padding、不把跳过算成功，不据部分字段宣称机制闭合 |
| 转换脚本重跑 | `Converted/` 等同名输出会被重写，先保留手工调整；转换脚本没有通用 `--output` 批次参数，不能直接套归档脚本参数 |

原版归档与已装 MOD 的运行行为必须分开：B17 在当时 48 项复核中发现 5 项游戏 `nativePC` 覆盖，当前提取入口只读 chunk，不把这些覆盖混入原始文件。运行结论仍须记录实际加载版本/覆盖，详见 [B17](MHWI-Forensic-Completion-20261026.md)。

## 文档交接与后续接入

每批保留：游戏源路径及归档 stamp、选择正则、逐文件来源包/逻辑偏移/尺寸/hash、工具和布局版本/hash、完整命令、实际运行日期、成功/失败/跳过与未验证项。批次清单与转换报告分别留存，`Saved/` 本机结果不会自动随仓库交接。

更新目录职责与入库现状用[管理页](../Systems/MHWI-Unpack-Data.md)，参数含义用[参数批处理](MHWI-Native-Parameter-Pipeline.md)/[火龙数据页](MHWI-Rathian-LR-Data-20261030.md)，玩法接入用[太刀系统](../Systems/MHWI-LongSword.md)。只有进入 UE 的 author/import 阶段才涉及 `/Game/...` 资产及其实际父类/属性核对，提取或字节解析成功不能替代这一步。

新格式没有可直接采用的维护者布局、或有多个实质技术候选时，记录缺口与有来源的选项后等待用户选择；本文仅归档当前路径，没有选定新的解析、反汇编或还原方案。已知工具边界见 [R-DATA-001/002](../Known-Issues.md)，本轮变更与验证见 [CHG-006](../Changes/CHG-20261030-006-mhwi-unpacking-workflow.md)。
