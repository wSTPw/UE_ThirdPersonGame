# MHWI 解包数据与工具链

数据源：本机 `F:\PCprogram\Steam\steamapps\common\Monster Hunter World`（Iceborne Steam 版），只读。
统计为 2026-10-30 对本地既有产物的只读复核，不是重新解包。

**核心口径：索引全量，提取选择性。** 下面的条目数描述"归档里有什么"，不是"我们拿到了什么"。

## 一、数据性质

| 项 | 事实 |
| --- | --- |
| 读取对象 | `chunk/chunkG*.bin`，13 个归档包，物理合计 51.13 GiB |
| 读取方式 | `0x40000` 字节分块 → Oodle 解压 → 按密钥异或 → 按条目偏移取窗口；密钥与格式参考 MHWNoChunk（MIT） |
| 索引范围 | 扫描全部 13 包，收集 `kind == 0` 条目并按同路径合并；不代表所有条目类型已解析 |
| 提取范围 | 按正则挑选，**从未全量解包** |
| 写入范围 | 只写项目内 `ArtSource/`、`Tools/MHW/` 缓存、`Saved/` 批次；不写游戏安装、不写 `Content/` |
| 权利 | 素材权利归 Capcom 等原权利人；工具 MIT 不构成素材再分发许可 |

## 二、目录与职责

| 路径 | 内容 | 入库 |
| --- | --- | --- |
| `Tools/MHW/` | 提取/检查/转换脚本、`tool-sources.json`（来源 SHA256）、许可、证据 JSON | 脚本与证据入库；`Downloads/`、`Source/`、`BlenderAddons/`、`Runtime/`、`*.log` 忽略 |
| `ArtSource/ThirdParty/MHWLongSword/nativePC/` | 首轮原始提取，保持游戏内相对路径 | 忽略 |
| `.../MHWLongSword/Converted/` | Blender/FBX 转换产物（1.3 GB / 282 文件） | 忽略 |
| `.../MHWLongSword/NativeFidelity/` | 独立源采样 FBX + 225 骨绑定（131 MB / 50 文件） | 入库 |
| `.../MHWLongSword/NativeParameters/` | 48 项原始参数二进制 + manifest（19 MB / 50 文件） | 入库 |
| `.../MHWLongSword/R06*` | R06 批次 FBX 与 journal | 入库 |
| `ArtSource/ThirdParty/MHWRathalos/nativePC/` | 雌火龙 em001，300 文件 / 76.97 MiB | 忽略 |
| `Saved/` | 探针与取证批次输出 | 整目录忽略 |
| `Scripts/MHWI/` | 提取、采样、校验、UE 授权脚本 | 入库 |

## 三、归档索引统计

主文件 `ArtSource/ThirdParty/MHWLongSword/archive-index.json`（19 MB，本机生成，已忽略）。结构三块：`source`（安装路径）、`archives`（包名 → `[物理字节, mtime_ns]`）、`files`（路径 → `{archive, offset, size}`）。

**`offset` 是解压后数据流地址，不是物理文件偏移**——不能直接 `seek` 原文件。条目尺寸之和（69.57 GiB）大于物理归档（51.13 GiB）是正常的。

| 指标 | 数值 |
| --- | ---: |
| 条目路径数 | 171,615 |
| 唯一存储区间数 | 143,531 |
| 共享区间路径数 | 28,084（同数据多入口） |
| 唯一区间合计 | 69.57 GiB（解压口径） |
| 扩展名种类 | 419 |

主要包：`chunkG0.bin` 113,792 路径 / 40.10 GiB；`chunkG7.bin` 21,349 / 2.97 GiB；`chunkG1.bin` 11,507 / 1.80 GiB。`chunkG10.bin` 索引为 0（条目类型未追查，不等于缺资源）。

体积分布：`.tex` 55,777 条 / 37.98 GiB 双第一；`.npck`（音频）条目少但体积第二；模型/动画（`.mod3` 10,553 + `.lmt` 5,776）合计不到 11 GiB。

顶层目录：`Assets` 39,518、`pl` 23,523、`em` 20,676、`common` 12,258、`vfx` 12,025、`wp` 11,827、`sound` 10,325、`quest` 10,066。

### 太刀取材面

| 前缀 | 路径数 | 尺寸 | 用途 |
| --- | ---: | ---: | --- |
| `hm/wp/wp03/` | 30 | 3.6 MiB | 动作库、参数、动作树、碰撞、shell |
| `wp/swo/` | 851 | 183.4 MiB | 太刀与刀鞘模型、武器侧动画 |
| `pl/m_equip/pl001_0000/` | 37 | 14.5 MiB | 男性猎人五件护甲 |
| `pl/common_tex/` | 179 | 51.6 MiB | 共享贴图 |
| `Assets/default_tex/` | 156 | 7.3 MiB | 引擎默认/占位贴图 |
| `hm/common/mot/co00_00/` | 2 | 5.7 MiB | 318 条通用猎人动作库 |
| `hm/common/ik/` | 8 | <0.1 MiB | IK 控制参数 |
| `common/equip/` | 82 | 1.0 MiB | 武器数值/制作表（**无挂点变换**） |

雌火龙取材正则：`^(?:em/em001/00/|common/item/em001(?:_0[12])?\.itlot$)`，命中 297 + 3 = 300 条、80,708,036 B。

## 四、已提取量

| 批次 | 数量 | 体积 | 位置 |
| --- | ---: | ---: | --- |
| 太刀首轮素材 | 140 | 49.60 MiB | `ArtSource/.../MHWLongSword/nativePC/` |
| 太刀原始参数 | 48 | 0.23 MiB | `.../NativeParameters/nativePC/` |
| 雌火龙 em001 | 300 | 76.97 MiB | `ArtSource/.../MHWRathalos/nativePC/` |
| 雌火龙音画补充 | 73 | 15.69 MiB | `Saved/`（不入库） |

`nativePC/` 实测 209 文件 = 140 原始提取 + 69 个 `.tex.png` 派生（贴图转换产物，非重复提取）。

**三类合计不足全包路径数的 0.14%**，且取材范围在 `hm/wp/wp03/` 与 `wp/swo/` 上交叠，**不能相加当"已解包比例"**。`Converted/`、`NativeFidelity/`、`R06*` 都是项目自制产物，不是游戏原始数据。

## 五、版本控制实际边界

`.gitignore` 排除 `nativePC/`、`Converted/`、`archive-index.json`、`player-candidates.json`、`Tools/MHW` 的缓存目录，以及整个 `Saved/`。

`git ls-files` 实际跟踪 `ArtSource/ThirdParty/MHWLongSword/` **167 文件 / 295.9 MiB**，主要是 `NativeFidelity/`（50 / 130.9 MiB）、`R06Remaining-20261025/`（33 / 90.9 MiB）、`R06Staging-20261025/`（27 / 51.6 MiB）、`NativeParameters/`（50 / 18.6 MiB）。

**已知差异（未处置）**：[源素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md) 写的是"二进制素材默认留本机"，但 `NativeParameters/` 的 48 个原版二进制与 R06 批次 63 个文件实际已入库。这是既有事实，删除/迁移/补 `.gitignore` 需要单独决策。

## 六、复现

```powershell
python Tools/MHW/extract_resources.py `
  --game 'F:\PCprogram\Steam\steamapps\common\Monster Hunter World' `
  --oodle 'E:\UE\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\runtimes\win-x64\native\oo2core.dll' `
  --output '<独立批次目录>' `
  --pattern '<正则>' --max-mb 256
```

无 `--pattern` 时只建索引并输出 `player-candidates.json`（`pl/` 下 `.lmt` 与含 `000` 的 `.mod3`），不写素材。

提取后解析：

```powershell
# 太刀参数（需 Node.js 的 OpenSSL legacy Blowfish）
python Scripts/MHWI/extract_native_longsword_params.py --fetch-layout
python Scripts/MHWI/build_native_action_database.py

# 怪物参数（先校验 9 份布局 hash）
python Scripts/MHWI/parse_em_params.py --layouts 'Tools/MHW/Source/MHW-Editor-b6ff379' `
  --input 'ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/data' `
  --keys '<EncryptionKeys.cs>' --pins 'Tools/MHW/mhw-editor-sources.json' --out '<报告>'

# 雌火龙格式
python Scripts/MHWI/read_action_params.py --self-check
python Scripts/MHWI/read_monster_collision.py
python Scripts/MHWI/inspect_parts_break.py --self-check
python Scripts/MHWI/inspect_parts_break_native.py
```

脚本内置保护（改脚本前须知）：

| 机制 | 行为 |
| --- | --- |
| 索引一致性 | 复用 `archive-index.json` 时比对 13 包 `size`/`mtime_ns`，不一致抛错并拒绝 |
| 输出隔离 | 输出目录与游戏安装互为祖先时拒绝运行 |
| 路径逃逸 | 拒绝绝对路径、`..`、含 `:` 的条目名；写入前再校验在 `nativePC/` 下 |
| 覆盖保护 | 同名目标 SHA256 不同则拒绝写入 |
| 体积预算 | 超 `--max-mb` 在写出前终止 |
| 完整性 | 逐文件 SHA256；**不做全归档 SHA 证明** |

**无事务回滚**：`extraction-manifest.json` 只在成功结束时重写为本次选择集合，不合并目录内旧文件；中途失败不回滚已落盘文件。目录存在不等于本次完成——按日志和逐文件清单复核，优先用新批次重建。

## 七、数据变更判定

| 触发 | 处置 | 影响 |
| --- | --- | --- |
| 游戏更新致 13 包 `size`/`mtime_ns` 变化 | 换新目录重建索引再按需重抽 | 旧 `offset` 全部失效 |
| 需要新资源类型 | 小批量试抽到新批次目录 | 不覆盖既有 manifest |
| `source-inventory.json` 出现新 `texture_dependencies` | 追加第二/三轮，保留首轮集合 | 清单分裂为多份，需标注轮次 |
| 有手工调整的转换产物 | 先另存再重跑 | `Converted/` 同名产物会被重写 |
| 换机器 | 恢复 `Downloads`/`Source`/`BlenderAddons`/`Runtime` 缓存 | 仅靠仓库不可重建 |

## 八、这些数据推不出的结论

- 索引全量 ≠ 解包完成（171,615 条只是路径清单，已提取不足 0.14%）
- 提取完成 ≠ 原作机制还原（参数存在不等于起算点/时钟/消费者语义闭合）
- 条目尺寸之和 ≠ 磁盘占用（`offset` 在解压流地址空间）
- `.npck`/`.nbnk` 占比大 ≠ 玩法资源丰富（音频包）
- `chunkG10.bin` 索引为空 ≠ 缺资源（条目类型未追查）
- 无全归档加密指纹：只校验了 13 包尺寸/mtime 与已提取文件的 SHA256
- 玩家已装 `nativePC` 覆盖未混入原版素材

## 九、格式读取的已知边界

| 格式 | 能做什么 | 不能做什么 |
| --- | --- | --- |
| ACTP2 | 按 Property 类型标签完整消费并重编码一致（太刀 342 记录 / 4,295 属性） | 数组索引不是已证动作 ID；111 种具名属性无直接伤害字段 |
| 怪物 COL | Names/CLND/CLGM 边界与 70 条 Atk2 字段可读 | 几何语义、OAP/CRC 尾部 opaque |
| PBC | 类 CRC 命名为 `PartsInfo/PartsStateInfo/PartsDetailInfo`，加载链 Info→State→Detail | 业务字段全 unknown；48 B 只是当前计数展开长度，不是通用步长 |
| SHLP | 结构可读（EPV 索引、关节号、碰撞路径、子判定、音效、投射体） | **无伤害/击退/气绝字段** |
| EM_DMG | 受击动作选择 | 不是攻击伤害表 |
| MOD3 → FBX | 本体 141 骨/25 网格/67,445 面回读一致 | FBX **不含贴图链接**（自定义 shader 节点组），只能验几何/骨骼/比例 |

## 相关文档

- 太刀结论：[太刀取证总账](../Reference/MHWI-LongSword-Evidence.md)
- 雌火龙结论：[雌火龙取证总账](../Reference/MHWI-Rathian-Evidence.md)
- 工具来源与完整命令：[MHW 素材采集工具说明](../../Tools/MHW/README.md)
- 素材产物清单：[源素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md)
- 已知问题：[R-DATA-001/002](../Known-Issues.md)
- 历史批次：[Archive/MHWI/](../Archive/MHWI/README.md)
