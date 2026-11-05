# 火龙未解格式续查：ACTP2、COL 攻击字段与 PBC 嵌套结构

- 日期：2026-10-30；状态：**离线结构读取已实现，完整原作机制仍 partial**。
- 需求：核对并推进[火龙交接](../Plans/MHWI-Rathian-Datamine-Handoff.md)中的未解项。
- 范围：本地 300 文件批次及既有 4 份 PBC 样本；未重新解包、启动原作/UE、注入或修改游戏安装与 Content。
- [方案](../Plans/PLAN-20261030-004-mhwi-rathian-format-evidence.md)、[变更记录](../Changes/CHG-20261030-011-mhwi-rathalos-format-evidence.md)。历史 CHG-009/010 保留当时结论，当前状态以本文和现状页为准。

## 结论与证据等级

| 交接问题 | 此次实际结果 | 仍不能宣称 |
| --- | --- | --- |
| ACTP2 没有公开结构、未能定步长 | 找到维护者模板；205,037/205,037 B 完整消费且独立重编码与原文逐字节一致。342 条 ActionData，142 条启用，4,295 个 Property（3,540 具名、111 种名） | 数组索引=原生动作ID；所有属性消费者已还原 |
| 伤害/击退只能从 ACTP2 取 | 此前推论错误。COL 类型2直接有具名攻击/击退字段：42 文件中36含ATK，共70条，主35+shell35；其余6份无攻击记录 | 原字段=实战扣血；所有记录仅下位可触发；类型数字=已确认反应名称 |
| PBC 三常量未命名 | 精确命中 PartsInfo/PartsStateInfo/PartsDetailInfo 类名CRC；固定版本加载/保存链确认三层数组 | 2006/2007=耐久；48 B 是所有 PBC 的通用步长 |
| 倒地/口水硬动作时长 | ACTP2 时间参数已可读；部分动作名获得CRC候选 | mLoopTime=整个实机动作持续时间；未命名5.5/6.5就是口水硬 |

## 维护者来源与项目适配

| 来源 / 适用版本 | 维护者资料支持 | 本项目实际处理 |
| --- | --- | --- |
| [Fexty actp2.bt](https://github.com/Fexty12573/MHW-010-Templates/blob/cea17f2c0c7d5c4f2ed421a7d0e04586bfb275f7/actp2.bt)、[UnitProperty.bt](https://github.com/Fexty12573/MHW-010-Templates/blob/cea17f2c0c7d5c4f2ed421a7d0e04586bfb275f7/UnitProperty.bt)，固定 `cea17f2…` | ActionData 头、启用标志、nameCRC及带类型属性/元数据定义 | `actp2.bt` 的数组直接写 UnitProperty，但原字节具有同仓 Property 的 tag/value 包装；按同源 Property → UnitProperty 读取，不改上游。仅支持实际出现的5种tag，其他拒绝；本机版本2完整往返闭合 |
| [Synthlight col.bt](https://github.com/Synthlight/MHW-Editor/blob/b6ff379b13079a4abb99490590fb05dfe6851bbc/010%20Templates/col.bt)、[维护者 Collisions 说明](https://github.com/Synthlight/MHW-Editor/wiki/Collisions)，固定 `b6ff379…` | Names 的攻击索引/UID、CLND/CLGM边界、Atk2的47字段/171 B | 按计数顺序推进到 ATK，不扫描猜起点；现有太刀 type1 读取器不适合直接套火龙 type2。几何载荷与 OAP/CRC 尾部原样保留 |
| [Andoryuuta DTI dump](https://github.com/Andoryuuta/MHW-DTI-Dumps/blob/4a124e4073519eaf19e3a446cb62d375d8da3209/dti_prop_dump.h)，固定 `4a124e4…`；文件头为2021-03-23 | 类名、类CRC与历史反射信息 | 只用类型身份，不能把旧虚表地址当当前ABI；动作名由类名变换得到，单独标 candidate |
| [现有固定代码来源](../../Tools/MHW/native-connector-code-sources.json)及 [NativeTrace](../../Scripts/MHWI/trace_native_connections.py) | 项目已有 EXE/text SHA 固定的离线函数范围读取机制 | 本轮仅复用固定分析代码，读取PBC加载/保存函数与owned unwind范围；不是运行或反编译观察 |

来源清单含实际文件 SHA256、缓存/下载位置与适配说明：[ACTP2来源](../../Tools/MHW/rathalos-actp2-sources.json)、[COL来源](../../Tools/MHW/rathalos-collision-sources.json)、[PBC来源](../../Tools/MHW/rathalos-pbc-sources.json)。社区维护者资料不是 Capcom 官方机制规范；上述完整消费证明读取边界，不能自动证明业务语义。

## COL：已有原文名称与攻击字段

- 主文件 `em/em001/00/collision/em001.col`：35条Atk2，攻击区 `[29831, 35816)`，每条171 B；主文件共35,865 B。
- 42文件的原始尺寸/hash与采集清单一致，读取后原文件保持不变。主文件剩余49 B、常见shell剩余36 B作为 `opaque_tail` 保存；`fully_semantically_decoded=false`，不把保留原文叫全语义解码。
- 下方名称直接来自 COL Names 表，通过表内 `attack_index` 对应ATK；不把该索引写成原生 ActionNo。完整70条的UID、字段偏移和来源hash见[紧凑证据](../../Tools/MHW/em001-collision-evidence.json)，全部47字段及原始几何/尾部在可重建完整报告。
- 原文存在 `G級_レイア_サマー` 等标签；不能把整个 `00/` 或每条记录自动标为下位火龙实际招式。还需等级资格与时间轴消费者绑定。

### 主表35条原始数值

字段名沿用维护者定义。`Motion_Value` 是原表攻击标量，下面不称“对玩家扣多少血”；击退Type/Lvl、Element_Id均保留数值，不擅自译成反应/属性名称。

| ATK索引（0起） | 文件内原名 | Motion_Value | 击退Type / Lvl | 防御耐力消耗 | 属性Id / Dmg | Stun |
| ---: | --- | ---: | --- | ---: | --- | ---: |
| 0 | 空中組み技チェック | 1 | 14 / 0 | 0 | 0 / 0 | 0 |
| 1 | 空中かみつき_頭 | 35 | 18 / 0 | 30 | 0 / 0 | 45 |
| 2 | 空中ひっかき；攻_空中中距離左；攻_空中中距離右 | 25 | 18 / 0 | 30 | 0 / 0 | 35 |
| 3 | 空中必殺キック | 75 | 17 / 0 | 55 | 0 / 0 | 60 |
| 4 | 空中尻尾攻撃(尻尾先)；空中尻尾攻撃(尻尾本) | 45 | 18 / 0 | 30 | 0 / 0 | 45 |
| 5 | 空中連続キック | 45 | 18 / 0 | 30 | 0 / 0 | 45 |
| 6 | 空中滑空 | 45 | 18 / 0 | 30 | 0 / 0 | 45 |
| 7 | 地上かみつき | 30 | 16 / 0 | 30 | 0 / 0 | 35 |
| 8 | 地上ダッシュかみ_胴；地上ダッシュかみ_頭 | 45 | 18 / 0 | 30 | 0 / 0 | 45 |
| 9 | 地上尻尾攻撃(尻尾先)；地上尻尾攻撃(尻尾本) | 35 | 18 / 0 | 30 | 0 / 0 | 35 |
| 10 | （无关联Name） | 0 | 5 / 0 | 10 | 0 / 0 | 0 |
| 11 | 捕食攻撃_ザコ用 | 1 | 12 / 0 | 0 | 0 / 0 | 0 |
| 12 | 捕食攻撃_PL用 | 25 | 18 / 0 | 30 | 0 / 0 | 0 |
| 13 | （无关联Name） | 10 | 16 / 0 | 10 | 0 / 0 | 0 |
| 14 | しぐさ+FH(全身)；しぐさ+FH(尻尾) | 0 | 7 / 0 | 0 | 0 / 0 | 0 |
| 15 | 小型リアクション用 | 0 | 39 / 0 | 0 | 0 / 0 | 0 |
| 16 | 地形対応アクション(全身)；地形対応アクション(尻尾) | 0 | 18 / 0 | 45 | 0 / 0 | 0 |
| 17 | 茂みごそごそ | 1 | 16 / 0 | 10 | 0 / 0 | 25 |
| 18 | （无关联Name） | 20 | 18 / 0 | 50 | 0 / 0 | 35 |
| 19 | 通_ひるみ地形破壊 | 0 | 39 / 0 | 0 | 0 / 0 | 0 |
| 20 | 拘束攻撃 | 20 | 2 / 0 | 40 | 0 / 0 | 0 |
| 21 | 踏みつけ | 55 | 18 / 0 | 40 | 0 / 0 | 45 |
| 22 | 空中かみつき_胴 | 20 | 16 / 0 | 20 | 0 / 0 | 35 |
| 23 | 着陸分岐キック | 75 | 17 / 0 | 55 | 0 / 0 | 60 |
| 24 | 空中ブレス；地上ブレス | 30 | 16 / 0 | 20 | 0 / 0 | 25 |
| 25 | 乗り暴れ_全身；乗り暴れ_尾先端 | 30 | 18 / 0 | 40 | 0 / 0 | 35 |
| 26 | 乗り衝撃；乗_ひるみ地形破壊 | 0 | 39 / 0 | 0 | 0 / 0 | 0 |
| 27 | レイア_サマー(先端) | 75 | 17 / 0 | 55 | 0 / 0 | 50 |
| 28 | レイア_滑空 | 45 | 18 / 0 | 30 | 0 / 0 | 30 |
| 29 | レイア_サマー(本体) | 75 | 17 / 0 | 55 | 0 / 0 | 50 |
| 30 | 3連突進_1&2_胴；3連突進_1&2_頭 | 45 | 18 / 0 | 15 | 0 / 0 | 45 |
| 31 | 地形移動アクション | 0 | 18 / 0 | 20 | 0 / 0 | 0 |
| 32 | クロー誘導地形破壊用 | 0 | 39 / 0 | 0 | 0 / 0 | 0 |
| 33 | G級_レイア_サマー(先端) | 90 | 17 / 0 | 55 | 0 / 0 | 50 |
| 34 | G級_レイア_サマー(本体) | 90 | 17 / 0 | 55 | 0 / 0 | 50 |

## ACTP2：结构已闭合，时间与动作身份分层

5种实际tag：Bool717、Int32 1,766、Float1,039、Vector4 18、PageEnd755。完整报告保留 ActionData/nameCRC、每个属性的类型/名称/值/元数据与起止偏移；200条未启用记录仍保留。111种具名字段中没有直接数值型攻击力/击退字段；`mbRideSuccessDamage`、`mbDisableFriendHitS` 是 bool，不能当伤害数值。

基于历史DTI的 `nActEm*` 类名生成 `ACTION::UPPER_SNAKE` 候选，再比较完整32位反CRC：319/342条获得候选，23条未命中；本候选集合无不同字符串的同CRC冲突。这是有界候选匹配，不能代替当前注册/动作绑定证据。

| ActionData数组索引 | nameCRC | 候选名称（推断） | 原字段 / 值 | 字段偏移 |
| ---: | --- | --- | --- | ---: |
| 9 | `0x4032910c` | `ACTION::DAMAGE_DOWN` | `mLoopTime=8` | 6534 |
| 181 | `0xafb9d039` | `ACTION::DAMAGE_STUN` | `mLoopTime=10` | 131876 |
| 213 | `0x83b3ab5e` | `ACTION::DAMAGE_RIDE_DOWN` | `mLoopTime=10` | 166686 |
| 325 | `0x3f459390` | 未命名 | `mLoopTime=5.5` | 202089 |
| 326 | `0xe37f9b48` | 未命名 | `mLoopTime=6.5` | 203502 |

不能把单个循环参数等同包含入场/循环/起身、倍率和中断的全程时长；特别不能把5.5/6.5按经验命名为口水硬。[ACTP2紧凑证据](../../Tools/MHW/em001-actp2-evidence.json)保留候选与边界。

## PBC：类CRC已解，48字节是样本展开长度

使用 `(~zlib.crc32(class_name)) & 0x7fffffff`，从类名独立重算并与历史dump/原字节三方一致：

| 样本相对偏移 | 值 | 对应类名 |
| ---: | --- | --- |
| +0 | `0x0befc97f` | `rEmPartsBreakCtrl::PartsInfo` |
| +8 | `0x6900901d` | `rEmPartsBreakCtrl::PartsStateInfo` |
| +16 | `0x5dc14d7c` | `rEmPartsBreakCtrl::PartsDetailInfo` |

固定代码读取链：`0x1419d86e0`校验头 → `0x1419d7c20`读Info数组 → `0x1419d7de0`读State数组 → `0x1419d7a20`读Detail数组。保存链 `0x1419d8780 → 0x1419d7f80` 以对应次序写出。具体owned函数范围、源指纹与关键指令见 [PBC静态代码证据](../../Tools/MHW/em001-pbc-native-layout-evidence.json)。这是项目固定代码的离线指令证据，不是REA原生引擎或原作执行记录。

+4 是State数组计数、+12是Detail数组计数，4个样本均为1，所以才出现 `16+5×48`；其他计数的资源可变长。原交接将48 B称通用记录步长应更正。

| 样本相对偏移 | 对应对象字段 | 火龙00样本值（记录0..4） | 业务语义 |
| ---: | --- | --- | --- |
| +20 | Detail +0x10 | 5 / 1 / 4 / 3 / 2 | 未解 |
| +24 | Detail +0x20 | **-1** / 2006 / 2006 / 2006 / 2006 | 未解；不是五条全2006 |
| +28 | Detail +0x28 | 0 / 4 / 1 / 2 / 8 | 未解 |
| +32 | State +0x10 | 全-1 | 未解 |
| +36 | Info +0x28 | 全0 | 未解 |
| +40 | Info +0x2c | 全-1 | 未解 |
| +44 | Info +0x30 | 全2 | 未解 |

雌火龙样本仅后4条 +24 为2007。仍无真实消费者证明以上字段是耐久、部位名或某种ID。[样本证据](../../Tools/MHW/em001-pbc-evidence.json)逐条保留raw载荷。[REA身份记录](../../Tools/MHW/em001-pbc-rea-identity.json)的Evidence ID为 `ev_7f6f0fefcfc609a953bcccde23ec130ef999ee1835611c539c29e8a3e0d5aac2`，仅证明本轮读取文件身份/尺寸/hash，不能用于字段语义论证。REA原生Ghidra未配置，本轮未安装或启动它。

## 复现与实际验证

从项目根目录运行，依赖本机原始资源与来源清单指定的固定缓存；缺失或指纹不符应停止。CLI不自动重新提取或下载。

```powershell
python Scripts/MHWI/read_action_params.py --self-check
python Scripts/MHWI/read_monster_collision.py
python Scripts/MHWI/inspect_parts_break.py --self-check
python Scripts/MHWI/inspect_parts_break_native.py
```

| 入口 | 本轮结果 | 输出 |
| --- | --- | --- |
| ACTP2 | 完整消费/独立重编码一致；7项往返/损坏拒绝通过 | `Saved/MHWRathalos-20261030-Format/actp2.json` + Tools紧凑证据 |
| COL | 42/42源尺寸/hash及读后保护一致；70条Atk2；8项损坏/未知类型/源指纹拒绝通过 | 同目录`collision.json` + Tools紧凑证据 |
| PBC样本 | 4文件20条、3类CRC一致；每个样本6项损坏拒绝通过；仅该固定样本形状 | Tools样本证据 |
| PBC代码 | 6个固定函数owned范围与关键读写位置核对；未命名业务消费者 | Tools静态代码证据 |

完整ACTP2报告约2.2 MB，Saved忽略；紧凑证据、脚本与来源清单保留在仓库。COL默认拒绝覆盖内容不同的报告，ACTP2/PBC默认会重写各自报告；需保留历史时改用其输出参数的新路径。未做编译/PIE/游戏观测，未验证当前nativePC覆盖或最终伤害公式。

## 剩余问题与后续选择

| 缺口 | 有出处的候选方向 | 代价 / 未选择原因 |
| --- | --- | --- |
| PBC载荷的业务含义与耐久 | 沿[本轮固定加载/保存链](../../Tools/MHW/em001-pbc-native-layout-evidence.json)继续追Detail/State/Info字段的真实读消费者，再与`dtt_epg`对照 | 中到大；类型身份已解决，尚无直接可套的业务定义，本文不选择新的推断算法 |
| LR有效招式与实战伤害 | 按[COL维护者定义](https://github.com/Synthlight/MHW-Editor/wiki/Collisions)继续连接LMT/TIML UID、攻击索引、等级/任务倍率；需要时单独安排受控原作观测 | 大；当前阶段禁止原作运行，不据MV直接下结论 |
| 倒地/口水硬全程时长 | 沿ACTP2 nameCRC核对当前动作注册/`em_dmg`分派及`mLoopTime`消费者，再接LMT入场/起身；运行逐帧记录是另一独立验证候选 | 中到大；当前仅候选名和原参数，运行尚不在范围 |

这些候选都有现有源入口，但没有直接解决业务语义的完整维护者方案；后续实质方向留用户选择。本轮不把“结构解出”写成“完整原作机制已解出”。
