# 雌火龙（em001）下位数据解包与解码状态


> **编号确认（2026-10-30）：本页数据属于 `em001` = 雌火龙（Rathian）；按用户决定，本项目以雌火龙为目标继续。**
>
> 证据一：`em001.dtt_epg` 头部 `Monster_Id` = 9，`em002.dtt_epg` = 1；对照名称表 ID 9 = 雌火龙、ID 1 = 火龙。
> 证据二：`tr_em001_02` 痕迹文本为"金色的鳞片"（金火龙＝雌火龙稀少种），`tr_em002_02` 为"银色的鳞片"（银火龙＝火龙稀少种）。
>
> 因此本页所有数值（Health 3000、7 组硬直阈值、12 组肉质、发怒/疲劳/状态值等）均为**雌火龙**数值。火龙（Rathalos）对应 `em002`，其数据（257 文件）已另行提取于 `ArtSource/ThirdParty/MHWRathalos-em002/` 备用。
> 当时把 `em001` 认作火龙是未经验证的假设所致，属本项目的判断失误，已记录于 [CHG-020](../Changes/CHG-20261030-020-mhwi-monster-id-correction.md)。

- 日期：2026-10-30。
- 阶段：**数据收集**。未接入 UE、未改 `Content/`、未改 `Scripts/MHWI/` 既有玩法代码、未改游戏安装。
- 来源：本机 `F:\PCprogram\Steam\steamapps\common\Monster Hunter World`，只读。
- 机器可读清单：[em001-datamine-manifest.json](../../Tools/MHW/em001-datamine-manifest.json)（300 条，逐文件路径/字节/SHA256/类别/解码状态）。
- 边界：本页的"已解码"只表示**该项目内字节级解析通过**，不表示己方已还原原作机制。

## 一、"下位"取哪一套

**结论**：取 `em/em001/00/` 目录，且下位数值在各文件的 **`_LR_` 段内**，不在目录维度。

证据（均来自本次解出的字段，非推断）：

| 证据 | 内容 |
| --- | --- |
| `em001.dtt_sta` | 单个文件内并列 `Fatigue_LR_` / `Fatigue_HR_` / `Fatigue_MR_` 三段，等级维度在文件内部 |
| `Parts1/2/3` 字段 | 同时含 `Part_Id_LR_HR1_*` 与 `Part_Id_MR1_*`，LR 与 HR 共用一套、MR 单列 |
| 目录差异 | `01/`、`02/` 与 `00/` 的 `actp2` 分别为 205,037 / 223,957 / 262,569 字节；`02/` 独有 shell ID 100–151 等 30 余个 |
| 掉落表 | `common/item/` 下并列 `em001.itlot`、`em001_01.itlot`、`em001_02.itlot` 三份 |

**推断（未用官方资料确认）**：`00/01/02` 对应本体/亚种/稀少种三个变体（即 火龙 / 苍火龙 / 银火龙），依据是三份 itlot 与 `02/` 多出的招式 ID。若后续要主张变体身份，需另有来源核实，本页不据此下结论。

因此本页所有"下位"数值取自 `00/` 目录中标注 `LR` 的字段/段。

## 二、已提取数据

| 项目 | 值 |
| --- | --- |
| 文件数 | 300（`em/em001/00/` 全部 297 + `common/item/em001*,em001_01,em001_02.itlot` 3） |
| 体积 | 76.97 MiB |
| 输出 | `ArtSource/ThirdParty/MHWRathalos/nativePC/`（保持游戏内相对路径） |
| 清单 | `ArtSource/ThirdParty/MHWRathalos/extraction-manifest.json`，逐文件 包名/偏移/尺寸/SHA256 |
| 覆盖内容 | 模型 (`mod3`/`mrl3`/`tex`)、动作 (`lmt`/`mbd`/`timl`/`at`)、数值 (`dtt_*`)、AI (`thk`×105/`thklst`)、招式判定 (`shlp`×37/`shll`/`col`×42)、IK、特效、掉落表 |
| 未提取 | `01/`、`02/` 变体与 `data/event/q301` 之外的外部引用资源（如需另开批次） |

分组：AI 思考表 105、碰撞 42、招式判定 37、贴图 20、动作库 19、动作混合 10、IK 4、其余各 1–3。

## 三、已解码数值

以下全部来自本轮实际解析，且**字节完全消费**（或注明差异）。

### 3.1 基础与部位（`em001.dtt_epg`，Blowfish 加密）

来源：`dtt_epg`，密钥 `DTT_EPG_KEY`。该文件本项目在 B13 已用独立布局解析并通过；本轮提取的 SHA256 与当时一致（`2ffdcb81…`），故沿用其解析结果。

| 字段 | 值 |
| --- | ---: |
| Monster_Id | 9 |
| Health（基础值） | 3000 |
| 部位组数（Flinches） | 7 |
| 命中部位（Hitzones） | 12 |
| 切断部位（Severs） | 1，`Sever` = 300 |

**肉质表（12 个部位组，单位 %）**：

| # | 斩 | 打 | 弹 | 火 | 水 | 冰 | 雷 | 龙 | 气绝 | 夺取 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 70 | 75 | 65 | 0 | 15 | 15 | 20 | 30 | 100 | 100 |
| 1 | 40 | 45 | 35 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 2 | 35 | 30 | 25 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |
| 3 | 35 | 30 | 25 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |
| 4 | 55 | 50 | 45 | 0 | 10 | 10 | 15 | 25 | 0 | 100 |
| 5 | 40 | 40 | 35 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 6 | 45 | 40 | 35 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |
| 7 | 60 | 65 | 45 | 0 | 15 | 15 | 20 | 30 | 100 | 100 |
| 8 | 37 | 45 | 30 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 9 | 21 | 21 | 45 | 0 | 10 | 10 | 15 | 25 | 0 | 100 |
| 10 | 37 | 37 | 25 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 11 | 45 | 37 | 30 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |

部位组 0/7 的气绝值 100，对应头部（可气绝部位）；`#9` 弹肉质 45 高于斩打 21，符合翼膜类特征。**组号→部位名的映射本条未解**，不得把上表行号直接写成"头/背/翼"。

**硬直阈值（`Flinch_Value`，7 组）**：240 / 300 / 180 / 180 / 210 / 210 / 200。
每组另带 `Special_Part_1..3`（除最后一组为 0 外均为 −1）、`Kinsect_Color`（0–3）与 `Parts_Type`（1 或 2）区分软硬部位映射。阈值语义（累计伤害触发哪类硬直/倒地）**未解**，不命名。

### 3.2 发怒（`em001.dtt_agr`，明文，字节 144/144 通过）

文件内含 2 组 `Rage_Stats`（偏移 16、80），两组数值完全相同：

| 字段 | 值 |
| --- | ---: |
| Build_to_Trigger | 600 |
| Duration | 80.0 秒 |
| Speed_Modifier | ×1.05 |
| Damage_Modifier | ×1.15 |
| Player_Damage_Modifier | ×1.10 |
| Out_of_Combat_Decay_Multiplier | ×0.10 |

**发怒累积倍率随血量变化**（HP 100 / 88–99 / 77–88 / 66–77 / 55–66 / 44–55 / 33–44 / 22–33 / 11–22 / 0–11）：

`0.5 / 0.5 / 1.0 / 1.0 / 0.5 / 0.5 / 0.5 / 2.0 / 2.0 / 2.0`

即低血量段（<33%）受击积攒发怒值的倍率是常规段的 4 倍。

### 3.3 体力与疲劳（`em001.dtt_sta`，明文，字节 92/92 通过）

| 等级 | 疲劳时长 | 耐力区间 | 基础值 |
| --- | ---: | ---: | ---: |
| 下位 LR | 70.0 秒 | 500–600 | 500 |
| 上位 HR | 60.0 秒 | 650–750 | 650 |
| 大师 MR | 50.0 秒 | 800–900 | 800 |

另有 `Stamina_Count` = 1（每级一条）与 `Fatigue_Speed` = 0.9（末尾固定段）。上表直接对应本页要用的下位行：**70 秒 / 500–600**。

### 3.4 状态值累积与抗性（`em001.dtt_eda`，Blowfish 加密）

解析 **888/896 字节 + 8 字节全零尾**，判为通过（零尾规则与 B13 部位解析器的 `expected_zero_tail` 一致；非零残留仍判失败）。26 段全部读到，字段名来自上游结构定义。

**累积型状态**（`Base` = 初始累积值，`Buildup` = 每次命中增加，`Max_Cap` = 上限）：

| 状态 | Base | 每次累积 | 上限 | 持续 | 每次使用递减 | 最小持续 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 毒 | 250 | 150 | 700 | 15 s | 0 | 0 |
| 睡眠 | 150 | 100 | 550 | 40 s | 0 | 0 |
| 麻痹 | 180 | 130 | 570 | 10 s | 0 | 0 |
| `Stun`（上游命名） | 120 | 100 | 620 | 7 s | 0 | 0 |
| 疲劳累积 | 225 | 75 | 900 | — | 0 | 0 |
| 乘骑 | 40 | 70 | 460 | — | 0 | 0 |
| 爆破 | 120 | 60 | 720 | — | 0 | 0 |
| 捕获 | 150 | 200 | 300 | — | 0 | 0 |

毒衰减 10 s / 5 点；毒伤 5 点、每 2 s 一跳。

**气绝/眩晕（文件内并列三套，语义未定，勿合并）**：

| 段 | 数值 |
| --- | --- |
| `Dizziness_LR_HR` | 持续 20 s，每次使用 −4 s，最小 5 s |
| `Dizziness_MR` | 累积 60 / 上限 90 / 再充能 150 s / 首次 20 s、重复 10 s |
| `Concussion` | Base 100 / 上限 100（其余为 0） |

**其它机制数值**：

| 项 | 值 |
| --- | --- |
| **口水硬（`Clagger`）** | Base 300 / 上限 300 |
| 乘骑击倒伤害 | 100 |
| 爆破伤害 | 100 |
| 疲劳伤害 | 150 |
| 捕获阈值 | 下位·上位 30%，大师 25% |
| 麻痹陷阱 | 8 s，每次 −2 s，最小 2 s |
| 落穴 | 10 s，每次 −2 s，最小 2 s |
| 藤蔓陷阱 | 8 s，无递减 |
| 粪 | 持续 30 s |
| 发怒累积（钩爪相关） | 上墙投射 30 / 无墙投射 30 / 爪攻击 35 / 上墙 30 / 边缘 30 |

命名警示：`Stun`、`Dizziness`、`Concussion` 三个上游字段名并存，本页不判断哪一个对应游戏内"气绝"。`Clagger` 按社区术语对应口水硬，属**名称推断**，未用实机观测验证。

## 四、招式、AI 与判定：当前解码边界

2026-10-30续查已解决此前ACTP2结构阻塞，且找到COL类型2的攻击原字段。完整原字段表、来源/版本、PBC对象布局与复现见[格式续查结果](MHWI-Rathian-Format-Evidence-20261030.md)，历史探查见CHG-009/010。

| 数据 | 文件/数量 | 当前状态 |
| --- | --- | --- |
| ACTP2 | `data/em001.actp2`，205,037 B | 完整消费/重编码一致；342动作记录/142启用/4,295属性项。存在公开维护者模板，111种具名属性中未见直接数值型伤害/击退字段 |
| COL | 42份，主35+shell35攻击记录 | Names/CLND/CLGM边界与70条Atk2攻击字段已读取；6份无攻击。原名/UID/索引/偏移可追，几何语义及OAP/CRC尾部仍opaque |
| SHLP | 37份 | 先前布局未全闭合；上游定义未见直接攻击力/击退字段。它引用COL/时间轴，不能推出数值只能在ACTP2 |
| PBC | `data/em001.em_pbc`，256 B | 类CRC已命名，加载/保存链确认Info→State→Detail数组；48 B仅当前计数展开长度。耐久/部位身份未解 |
| EM_DMG | `data/em001.em_dmg`，7,620 B | 受击动作选择；本批未完整解码，不能当攻击伤害表 |
| THK/THKLST | 105+1 | 本批未解析；不以限定搜索断言不存在公开格式 |
| 动作库 | 19 LMT（其中 7 个为 16 B 空壳，实有内容 12 个） | 已提取；**未拆逐帧/未导出**，见第 5 节 |
| 模型 | 2 MOD3（本体 + 尾巴）+ 2 MRL3 + 20 TEX | **已转 FBX**：本体 141 骨 / 25 网格 / 67,445 面（6.46 MB），尾巴 2 骨（0.36 MB）；贴图转出 19 张 PNG，但 FBX 内无贴图链接，见第 5 节 |

**原始攻击字段已有，不等于实战伤害已验证**：主表`空中必殺キック`的Motion_Value=75、击退Type17/Lvl0，`地上かみつき`为30、Type16/Lvl0，均是文件原字段。整个00碰撞资源还含G級原名标签，不是下位专用表；最终扣血、反应名称、等级触发资格未闭合。

ACTP2时间参数与动作名候选已提取：DAMAGE_DOWN候选mLoopTime=8、DAMAGE_STUN/RIDE_DOWN候选=10；未知325/326为5.5/6.5，不能当作口水硬时长。CRC候选与运行时钟分别标注，详见续查页。

PBC三常量是`rEmPartsBreakCtrl::PartsInfo/PartsStateInfo/PartsDetailInfo`的反CRC32（31位）。当前样本+24不是五条都2006：第一条-1、后四条2006（雌火龙2007）。所有业务字段仍unknown，不发布部位破坏耐久。

## 五、方法与可复现

归档提取与通用参数解析见[解包流程](MHWI-Unpacking-Workflow.md)。既有dtt_agr/dtt_sta完整消费、dtt_eda按888+8全零尾判据通过，后者不等于888字节解释了全部896字节；原结果见前节，本轮未重跑。

新增离线入口：

```powershell
python Scripts/MHWI/read_action_params.py --self-check
python Scripts/MHWI/read_monster_collision.py
python Scripts/MHWI/inspect_parts_break.py --self-check
python Scripts/MHWI/inspect_parts_break_native.py
```

完整ACTP2/COL报告在忽略的`Saved/MHWRathalos-20261030-Format/`，紧凑证据及来源hash在Tools/MHW。原始采集清单不变，分类清单`decode`状态随本轮更新。字段来自维护者模板与固定代码，未启动原作或UE，不宣称机制忠实度。

### 5.1 模型转 FBX（2026-10-30 追加）

入口：[convert_monster_model.py](../../Tools/MHW/convert_monster_model.py)，无头 Blender 4.5 + Feuleur suite，单文件转换，只读源文件、只写 `--out`。

```powershell
& 'Tools/MHW/Runtime/blender-4.5.0-windows-x64/blender.exe' --background --factory-startup `
  --python-exit-code 1 --python Tools/MHW/convert_monster_model.py -- `
  --mod3  'ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/mod/em001_00.mod3' `
  --mrl3  'ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/mod/em001_00.mrl3' `
  --tex-root 'ArtSource/ThirdParty/MHWRathalos/nativePC' `
  --out 'Saved/MHWProbe-20261030/model-test/em001_00_body.fbx'
```

| 项 | 结果 |
| --- | --- |
| 本体 `em001_00.mod3` | 26 对象 / 1 骨架 141 骨 / 25 网格 / 67,445 面，FBX 6,460,428 B |
| 尾巴 `em001_00_tail.mod3` | 2 骨，FBX 359,788 B（独立文件，非本体子网格） |
| 回读校验 | FBX 重新导入 Blender：1 骨架 141 骨 / 25 网格 / 67,445 面，与导出前一致 |
| 贴图 | `load_mrl3` 转出 19 张 `*.tex.png`（8 张本体 + eye/damage 系列），写在 `nativePC/` 内（已忽略） |
| **限制** | FBX 只保留材质名，**不含贴图链接**：suite 用自定义 shader 节点组，FBX 导出器不识别，带/不带 `--mrl3` 的 FBX 字节数完全相同（均 6,460,428） |
| 缺件 | 引用了 `Assets/default_tex/` 下的共享默认贴图（sand_CMM、noise_BM/LIN、kizu_CMM、paint_CMM、snow_Col_CMM、null_black、null_fur_CMM 等），本轮未提取，加载时告警但不中断 |

要贴图进 FBX 或进 UE，需另做一步：按 `Principled BSDF` 重建材质并把 PNG 接进 Base Color / Normal / RMT 槽，或直接在 UE 里用导出的 PNG 手工建材质。**当前 FBX 只能用于验证几何、骨骼层级与比例**，不能当成品资产。

### 5.2 引擎内结果（2026-10-30 追加）

`Tools/MHW/rebuild_monster_materials.py` 重建 Principled 材质后，`Scripts/MHWI/import_rathalos_mesh.py` 无头启动编辑器完成导入：

| 资产 | 内容 |
| --- | --- |
| `/Game/MHWI/Rathalos/Mesh/SK_EM001_Body` | 4 材质槽，**142 骨** |
| `/Game/MHWI/Rathalos/Mesh/SK_EM001_Tail` | 2 材质槽，**3 骨** |
| `Textures/` | 12 张，其中 4 张已设 `TC_NORMALMAP` |
| `Materials/` | 4 个，实测纹理采样：本体 = BML + NM + EM，damage = damage_BM + damage_NM |

**骨骼数差异**：Blender 141 → 引擎 142，尾巴 2 → 3，属 FBX 导入新增根骨，**未逐骨核对**；重定向或挂接前必须先确认。

材质最终状态（2026-10-30 收尾）：4 个材质均为 `BaseColor / Normal / Roughness / Metallic` 接入，RMT 按实测通道 `R→Roughness`、`G→Metallic`；`Emissive` 除眼睛外全部断开（此前 `NoImage_EM` 白图误接导致整只模型发白）。`CMML`（2048²，R 0.939 / G 0.952 / B 1.0）与 `FM`（R、G 恒 0.514/0.505）经通道分布测量后判定**不接**：前者近似全白无收益，后者是常量场无细节。见 [CHG-016](../Changes/CHG-20261030-016-mhwi-rathalos-rmt-material.md)、[CHG-017](../Changes/CHG-20261030-017-mhwi-rathalos-material-finalize.md)。

未验证：未在视口目视确认渲染（`capture_scene_png` 同一取景恒定返回相同字节，不能做观感对照）；未做 LOD1/2；CMML 的染色通道分配未解、FM 需专用毛发 shader。

## 六、剩余问题与交接

1. PBC结构已明，耐久需沿Detail/State/Info字段的真实读消费者核实，不能继续以猜哈希替代。
2. LR动作资格、COL索引/UID到LMT/TIML和动作请求的对应关系仍缺；攻击字段不是最终对玩家扣血。
3. 倒地/口水硬总时长需动作绑定及时间消费者；不能用单个mLoopTime直接验收。
4. 肉质组号到部位名、任务倍率、变体身份及AI仍分别开放，Health3000不是任务实际血量。

自包含[交接文档](../Plans/MHWI-Rathian-Datamine-Handoff.md)已更新，[后续候选与代价](MHWI-Rathian-Format-Evidence-20261030.md)尚待用户选择，未擅自定新业务推断方案。关联[原方案](../Plans/PLAN-20261030-003-mhwi-rathian-datamine.md)、[本轮方案](../Plans/PLAN-20261030-004-mhwi-rathian-format-evidence.md)、[CHG-011](../Changes/CHG-20261030-011-mhwi-rathalos-format-evidence.md)。

## 动画补齐现状（2026-10-30）

本地19个LMT已全部核对，848非空动作中旧24条保留、新增824条导入既有雌火龙骨架；不是新增原作机制或招式语义判断。完整覆盖与验证边界见[雌火龙动画库](../Systems/MHWI-Rathian-Animations.md)。前述未拆动作库的表述保留前批次范围，本批已按上述专页更新。
