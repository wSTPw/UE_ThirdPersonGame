# MHWI 解包数据管理与统计

- 状态：现状页（living）。统计数字为 2026-10-30 对本地既有产物的**只读复核**，不是重新解包。
- 数据源：本机 `F:\PCprogram\Steam\steamapps\common\Monster Hunter World`（Iceborne，Steam 版），只读。
- 本页范围：解包数据**在哪、有多少、怎么来、怎么校验、哪些已入库、能得出什么结论**。
- 本页不覆盖：Blender/FBX 转换算法、UE 导入与玩法实现（见 [MHWI 太刀训练模组](MHWI-LongSword.md)）、原作机制语义（见 [源保真调查](../Reference/MHWI-Source-Fidelity-Audit.md)）。
- 工具与逐条命令的完整来源：[MHW 素材采集工具说明](../../Tools/MHW/README.md)；首次采集事实：[CHG-20261022-001](../Changes/CHG-20261022-001-mhw-longsword-source-assets.md)。

操作顺序、命令、太刀/怪物解析入口与失败判定：见 [现有解包方式与复现流程](../Reference/MHWI-Unpacking-Workflow.md)。

## 2026-10-31：雌火龙方案取证补充

本轮复核既有em001的300文件（80,708,036 B），尺寸/SHA256全部一致；另外定向补取73个外部音画及任务/区域候选文件，16,446,967 B（15.69 MiB）：音频8、VFX52、任务/区域13。73/73复读一致；提取后300原文件与13归档尺寸/mtime再次核对一致，未计算整归档SHA。

新批次为 `Saved/MHWI-Rathian-20261031-PlanEvidence/`，原始资源和复制的索引留本机Saved；可携带的逐文件归档/offset/hash及工具指纹见[精简证据](../../Tools/MHW/rathian-plan-evidence-20261031.json)。这些资料仍是raw，尚未证明LR资格、任务倍率、完整音画依赖或原作机制。没有改Content、既有清单或游戏安装。下文2026-10-30统计保留当时口径，不把新批次悄然并入旧统计。[分工方案](../Plans/PLAN-20261031-002-rathian-restoration-master.md)和[本轮CHG](../Changes/CHG-20261031-002-rathian-restoration-plan.md)记录后续步骤及实际结果。

## 一、这份数据的性质

| 项目 | 事实 |
| --- | --- |
| 读取对象 | 安装目录下 `chunk/chunkG*.bin`，共 13 个归档包 |
| 读取方式 | 分块（0x40000 字节）Oodle 解压后按密钥异或，再按条目偏移取数据；密钥与格式参考 MHWNoChunk（MIT） |
| 索引范围 | 扫描全部 13 个包，收集 `kind == 0` 文件条目并按同路径合并；不代表所有条目类型均已解析 |
| 提取范围 | **选择性**：只按正则挑选需要的文件，从未全量解包 |
| 写入范围 | 只写项目内 `ArtSource/`、`Tools/MHW/` 缓存与 `Saved/` 批次目录；不写游戏安装、不写 `Content/` |
| 权利归属 | 游戏素材权利归 Capcom 等原权利人；工具 MIT 许可不构成素材再分发或商用许可 |

"索引全量、提取选择性"是本页所有统计的前提：下面的条目数描述的是**归档里有什么**，不是**我们拿到了什么**。已提取量见第四节。

## 二、目录与职责

| 路径 | 内容 | 入库 |
| --- | --- | --- |
| `Tools/MHW/` | 提取/检查/转换脚本、工具来源与 SHA256（`tool-sources.json`）、上游许可、证据 JSON | 脚本与证据入库；`Downloads/`、`Source/`、`BlenderAddons/`、`Runtime/`、`*.log` 忽略 |
| `ArtSource/ThirdParty/MHWLongSword/nativePC/` | 首轮原始提取，**保持游戏内相对路径** | 忽略（含 `.tex.png` 派生） |
| `ArtSource/ThirdParty/MHWLongSword/Converted/` | Blender/FBX 转换产物（1.3 GB / 282 个文件） | 忽略 |
| `ArtSource/ThirdParty/MHWLongSword/NativeFidelity/` | 独立源采样 FBX 与 225 骨绑定（131 MB / 50 个文件） | **已入库** |
| `ArtSource/ThirdParty/MHWLongSword/NativeParameters/` | 48 项原始参数二进制 + 独立 manifest 与索引（19 MB / 50 个文件） | **已入库** |
| `ArtSource/ThirdParty/MHWLongSword/R06*` | R06 批次 FBX 与 journal（`R06Staging`、`R06Main`、`R06MainShared`、`R06Remaining`） | **已入库** |
| `ArtSource/ThirdParty/MHWLongSword/*.json` | `extraction-manifest`、`source-inventory`、`conversion-report`、`player-candidates`、`archive-index` | 前者三个入库；后两者忽略 |
| `Saved/MHWProbe-*`、`Saved/MHWIRestoration/` | 探针与取证批次输出 | 忽略（整目录） |
| `Scripts/MHWI/` | 提取、采样、校验、UE 授权脚本 | 入库 |

入库现状与 `.gitignore` 字面规则之间的差异见第五节，属于**未决事项**，不在本页处理。

## 三、归档索引层（统计口径）

主文件：`ArtSource/ThirdParty/MHWLongSword/archive-index.json`（19 MB，本机生成，已忽略）。

结构只有三块：`source`（安装路径字符串）、`archives`（包名 → `[物理字节数, mtime_ns]`）、`files`（路径 → `{archive, offset, size}`）。

**关键口径**：`offset` 是**解压后数据流里的地址**，不是物理文件偏移——`extract_resources.py` 按 `0x40000` 块解压再按 `offset` 取窗口。因此条目尺寸之和（69.57 GiB）大于物理归档（51.13 GiB）是正常的，不能反推压缩率，也不能用 `offset` 直接 `seek` 原文件。

| 指标 | 数值 | 口径 |
| --- | --- | --- |
| 条目路径数 | 171,615 | 每条路径一条记录；跨包同路径取最新包覆盖 |
| 唯一存储区间数 | 143,531 | 按 `(包, 偏移, 尺寸)` 去重 |
| 共享区间的路径数 | 28,084 | 多条路径指向同一存储区间（同数据多入口） |
| 唯一区间合计 | 69.57 GiB | 解压口径 |
| 13 个归档物理合计 | 51.13 GiB | 磁盘实际字节 |
| 与物理体积之比 | 1.36 | 仅作数量级参考，非严格压缩比 |
| 扩展名种类 | 419 | 路径口径 |

### 按归档包

| 包 | 路径数 | 唯一区间 | 物理大小 | 唯一区间合计 |
| --- | ---: | ---: | ---: | ---: |
| chunkG0.bin | 113,792 | 93,911 | 40.10 GiB | 55.07 GiB |
| chunkG1.bin | 11,507 | 9,582 | 1.80 GiB | 2.23 GiB |
| chunkG2.bin | 5,058 | 4,423 | 2.17 GiB | 2.70 GiB |
| chunkG3.bin | 5,772 | 4,567 | 1.37 GiB | 1.90 GiB |
| chunkG4.bin | 5,612 | 3,556 | 0.35 GiB | 0.51 GiB |
| chunkG5.bin | 2,907 | 2,635 | 1.32 GiB | 1.82 GiB |
| chunkG6.bin | 25 | 25 | 0.36 MB | <0.01 GiB |
| chunkG7.bin | 21,349 | 19,356 | 2.97 GiB | 4.05 GiB |
| chunkG8.bin | 1,299 | 1,249 | 0.99 GiB | 1.18 GiB |
| chunkG9.bin | 1,605 | 1,538 | 0.04 GiB | 0.10 GiB |
| chunkG10.bin | **0** | 0 | 0.34 MB | 0 |
| chunkG11.bin | 101 | 101 | 0.82 MB | <0.01 GiB |
| chunkG60.bin | 2,588 | 2,588 | 1.16 MB | 0.01 GiB |
| **合计** | **171,615** | **143,531** | **51.13 GiB** | **69.57 GiB** |

`chunkG10.bin` 有物理内容但索引中 **0 条** `kind == 0` 条目。静态发现，**不代表包损坏或为空**；本次未追查其条目类型，不据此推断缺失资源。

### 按扩展名（路径口径，未去重，前 10）

| 扩展名 | 路径数 | 条目尺寸合计 |
| --- | ---: | ---: |
| `.tex` | 55,777 | 37.98 GiB |
| `.gmd` | 18,079 | 0.15 GiB |
| `.mrl3` | 11,053 | 57 MB |
| `.mod3` | 10,553 | 7.24 GiB |
| `.efx` | 10,136 | 0.14 GiB |
| `.lmt` | 5,776 | 3.30 GiB |
| `.sobj` | 5,310 | 10 MB |
| `.thk` | 4,866 | 46 MB |
| `.nbnk` | 4,550 | 1.67 GiB |
| `.npck` | 1,569 | **20.53 GiB** |

贴图（`.tex`）占条目数与体积双第一；`.npck`（音频包）条目少但体积排第二。模型/动画（`.mod3`/`.lmt`）合计不到 11 GiB。

### 按顶层目录（路径口径，前 12）

| 目录 | 路径数 | 目录 | 路径数 |
| --- | ---: | --- | ---: |
| `Assets` | 39,518 | `sound` | 10,325 |
| `pl` | 23,523 | `quest` | 10,066 |
| `em` | 20,676 | `event` | 7,655 |
| `common` | 12,258 | `stage` | 7,064 |
| `vfx` | 12,025 | `npc` | 6,057 |
| `wp` | 11,827 | `ui` | 3,336 |

### 太刀相关定位（本项目的实际取材面）

| 前缀 | 路径数 | 条目尺寸合计 | 用途 |
| --- | ---: | ---: | --- |
| `hm/wp/wp03/` | 30 | 3.6 MiB | 太刀动作库、参数、动作树、碰撞、shell |
| `wp/swo/` | 851 | 183.4 MiB | 太刀（swo001）与刀鞘模型、武器侧动画 |
| `pl/m_equip/pl001_0000/` | 37 | 14.5 MiB | 男性猎人五件护甲 |
| `pl/m_face/face001/` | 7 | 10.5 MiB | 脸部 |
| `pl/common_tex/` | 179 | 51.6 MiB | 共享贴图 |
| `Assets/default_tex/` | 156 | 7.3 MiB | 引擎默认/占位贴图 |
| `hm/common/mot/co00_00/` | 2 | 5.7 MiB | 318 条通用猎人动作库 |
| `hm/common/ik/` | 8 | <0.1 MiB | IK 控制参数 |
| `common/equip/` | 82 | 1.0 MiB | 武器数值/制作表（无挂点变换） |

## 四、已提取数据

太刀三类提取，各自独立 manifest，**互不覆盖**（指这些批次目录隔离；同目录重跑会重写清单，见第六节）：

| 批次 | 数量 | 体积 | 输出位置 | 清单 |
| --- | ---: | ---: | --- | --- |
| 首轮素材（动画/模型/贴图） | 140 个文件 | 52,004,942 B（49.60 MiB） | `ArtSource/.../nativePC/` | `extraction-manifest.json`（逐文件 包/偏移/尺寸/SHA256） |
| 原始参数 | 48 个文件 | 242,071 B（0.23 MiB） | `ArtSource/.../NativeParameters/nativePC/` | 该目录下独立 `extraction-manifest.json` |
| 全量重抽探针 | 41 个文件 | 6.55 MiB | `Saved/MHWProbe-20261028/`（不入库） | 该目录下独立 `extraction-manifest.json` |

- `nativePC/` 目录实测 **209** 个文件 = 140 个原始提取 + 69 个 `.tex.png` 派生（贴图转换产物，与清单口径不同，不是重复提取）。
- 三类合计仍不足全包路径数的 **0.14%**，且三者取材范围在 `hm/wp/wp03/` 与 `wp/swo/` 上有交叠，**不能相加当作"已解包比例"**。
- 派生转换产物体积：`Converted/` 1.3 GB（282 文件）、`NativeFidelity/` 131 MB（50）、`R06Remaining-20261025/` 91 MB（33）、`R06Staging-20261025/` 52 MB（27）。这些都是**项目自制产物**，不是游戏原始数据。

同日另有独立雌火龙批次（em001；编号核对见数据页文首）：`ArtSource/ThirdParty/MHWRathalos/` 下 300 个文件、80,708,036 B，未计入上述太刀三批及其比例。逐文件清单、解码状态和本机/入库边界见 [雌火龙数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)与 [CHG-005](../Changes/CHG-20261030-005-mhwi-rathalos-datamine.md)；本轮仅复核其本地尺寸/hash，未重新提取。

## 五、版本控制边界

`.gitignore` 实际排除：

```
/ArtSource/ThirdParty/MHWLongSword/nativePC/
/ArtSource/ThirdParty/MHWLongSword/Converted/
/ArtSource/ThirdParty/MHWLongSword/archive-index.json
/ArtSource/ThirdParty/MHWLongSword/player-candidates.json
/Tools/MHW/Downloads/  /Tools/MHW/Source/  /Tools/MHW/BlenderAddons/  /Tools/MHW/Runtime/  /Tools/MHW/*.log
Saved/（整目录）
```

`git ls-files` 实际跟踪：`ArtSource/ThirdParty/MHWLongSword/` **167 个文件 / 295.9 MiB**，`Tools/MHW/` 34 个文件。

| 分组 | 文件数 | 体积 | 性质 |
| --- | ---: | ---: | --- |
| `NativeFidelity/` | 50 | 130.9 MiB | 采样 FBX + 绑定 JSON（自制） |
| `R06Remaining-20261025/` | 33 | 90.9 MiB | R06 片段 FBX（自制） |
| `R06Staging-20261025/` | 27 | 51.6 MiB | R06 中间产物 |
| `NativeParameters/` | 50 | 18.6 MiB | **48 个原版参数二进制** + 2 个清单 |
| `R06Main*` | 3 | 3.3 MiB | R06 主批次 |
| 根目录 JSON/README | 4 | 0.6 MiB | 清单与说明 |

**已知差异（静态发现，未处理）**：[源素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md) 的表述是"二进制素材默认留本机"，但 `NativeParameters/` 的 48 个原版二进制与 R06 批次 63 个文件（59 个 FBX + 4 个 journal JSON）实际已入库。这是既有事实，不是本页的处置结论；删除、迁移或补 `.gitignore` 需要单独决策，本文档不代为执行。

体积参考：`Tools/MHW/Runtime/` 906 MB（便携 Blender）、`Downloads/` 396 MB 均为忽略的本机缓存，换机需重新获取。

## 六、复现与校验

最小复现（索引 → 定向提取 → 检查），路径为**本机配置**，换机需改 `--game` 与 `--oodle`：

```powershell
python Tools/MHW/extract_resources.py `
  --game 'F:\PCprogram\Steam\steamapps\common\Monster Hunter World' `
  --oodle 'E:\UE\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\runtimes\win-x64\native\oo2core.dll' `
  --output 'ArtSource/ThirdParty/MHWLongSword' `
  --pattern '<正则>' --max-mb 256
```

脚本内置的保护，改脚本前须知：

| 机制 | 行为 |
| --- | --- |
| 索引缓存一致性 | 复用 `archive-index.json` 时比对 13 个包的 `size` 与 `mtime_ns`；不一致直接抛错，要求换新输出目录 |
| 输出隔离 | 输出目录与游戏安装目录互为祖先时拒绝运行 |
| 路径逃逸 | 拒绝绝对路径、`..`、含 `:` 的条目名；写入前再校验目标仍在 `nativePC/` 下 |
| 覆盖保护 | 同名目标若 SHA256 与本次不同则拒绝写入 |
| 体积预算 | 选中条目合计超过 `--max-mb` 直接终止，不部分写出 |
| 完整性 | 每次提取记录 SHA256；不做全量归档 SHA 证明 |

清单与中途失败边界：`extraction-manifest.json` 在成功结束时重写为本次选择集合，不自动合并目录内旧文件；后续文件失败不会回滚此前落盘内容。新批次使用独立目录，恢复时逐文件校验，不据目录存在判断完成。详见 [流程与失败处理](../Reference/MHWI-Unpacking-Workflow.md)、[R-DATA-001](../Known-Issues.md)。

无 `--pattern` 时只建索引并输出 `player-candidates.json`（`pl/` 下 `.lmt` 与含 `000` 的 `.mod3`），不写素材。

## 七、数据变更判定

| 触发条件 | 应做什么 | 影响 |
| --- | --- | --- |
| 游戏更新，13 个包的 `size` 或 `mtime_ns` 变化 | 换新的输出目录重建索引，再按需重抽 | 旧索引不可复用；旧 `offset` 全部失效 |
| 需要新的资源类型 | 先按正则小批量试抽，写入新批次目录 | 不覆盖既有 `extraction-manifest.json` |
| `source-inventory.json` 的 `texture_dependencies` 有新项 | 追加第二/第三轮提取，保留首轮路径集合 | 清单会分裂为多份，需在说明里指明轮次 |
| 目录中有手工调整的转换产物 | 先另存再重跑转换脚本 | `Converted/` 同名产物会被重写 |
| 换机器 | 恢复工具缓存（`Downloads`/`Source`/`BlenderAddons`/`Runtime`）后重跑 | 仅靠仓库不可重建，见 [取证收尾](../Reference/MHWI-Forensic-Completion-20261026.md) |

## 八、这些数据不能推出的结论

- **索引全量 ≠ 解包完成**：171,615 条只是路径清单，上述太刀三批记录数不足索引的 0.14%，并非含火龙等后续批次的全项目覆盖率。
- **提取完成 ≠ 原作机制已还原**：参数值存在，不等于起算点、时钟、消费者语义已闭合。
- **条目尺寸之和不等于磁盘占用**：`offset` 在解压流地址空间，69.57 GiB 不能当解包后体积或压缩率。
- **`.npck`/`.nbnk` 占比大不代表玩法资源丰富**：那是音频包。
- **`chunkG10.bin` 索引为空不等于缺资源**：条目类型未追查。
- **没有全归档加密指纹**：现有校验只覆盖 13 个包的尺寸/mtime 与已提取文件的 SHA256。
- **`nativePC` 覆盖未混入**：全流程未把玩家已装 MOD 当作原版素材，见 [B17 取证](../Reference/MHWI-Forensic-Completion-20261026.md) 中 5 项覆盖记录。

## 九、相关文档

- [雌火龙格式续查](../Reference/MHWI-Rathian-Format-Evidence-20261030.md)：ACTP2/COL原字段及PBC嵌套证据，区分提取/解码/消费者语义

- [MHW 素材采集工具说明](../../Tools/MHW/README.md)：工具来源、完整命令、转换约定
- [源素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md)：产物清单、骨架/材质边界
- [CHG-20261022-001 素材采集](../Changes/CHG-20261022-001-mhw-longsword-source-assets.md)：首轮执行证据与未验证项
- [MHWI 太刀训练模组](MHWI-LongSword.md)：素材如何进入 `/Game/MHWI`
- [原始参数批处理](../Reference/MHWI-Native-Parameter-Pipeline.md)：48 项参数的字段与消费者边界
- [源保真调查](../Reference/MHWI-Source-Fidelity-Audit.md)：解包数据与原作机制之间的缺口
- [已知问题](../Known-Issues.md)：R-ANIM-003 等素材相关遗留
- [变更记录索引](../Changes/README.md)：本次文档新增记录
