# MHWI 雌火龙音画事件映射表骨架（2026-11-02）

- 日期：2026-11-02。
- 性质：**只读清点 + 字符串扫描骨架**。对应 [PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md) P2（A5x 音画配置细案补全）的映射表部分；原始清点数据见 [rathian-audio-vfx-inventory-20261102.json](../../Tools/MHW/rathian-audio-vfx-inventory-20261102.json)，批次证据见 [rathian-plan-evidence-20261031.json](../../Tools/MHW/rathian-plan-evidence-20261031.json)。
- 数据来源：`Saved/MHWI-Rathian-20261031-PlanEvidence/` 下 73 个 raw 文件（73/73 尺寸+SHA256 与清单一致）。扫描方式为只读字节扫描（ASCII 与 UTF-16LE，长度≥4），**未做任何格式解码，未创建任何 UE 资产**。

## 0. 阅读前提（必须先读）

- **候选名 ≠ 语义闭合**：下表所有名称均为 raw 字节中的可读字符串候选，不构成确认的事件 ID，也不构成语义对应（哪个名字对应吼叫/吐息等行为，尚无证据）。
- **Wwise / EFX 未解码**：`.nbnk`（em001_se/em001_vo）仅文件级登记，bank 内事件/音轨/WEM 结构未读；`.wwev` 事件表、`.efx` 时间线（内含 `timl` 魔数）均未解码，故"引用动作(bank+slot)"与"源时刻"两列只能填 unknown。
- **UE 侧零资产**：截至本页时点，工程内不存在任何由本批次派生的 SoundAsset/Niagara/衰减/附着配置（`/Game/MHWI/Rathian/Presentation` 未建），"UE落点"列全部为 unknown。
- **验收分两级**：后续验收按"**事件忠实**"（源事件→动作/时刻绑定有原作证据）与"**资源近似**"（仅资源形态相似，绑定无证据）分别标注；本骨架所有行均为 raw，两级均未达成。
- 扫描统计：66 个可扫描文件中 59 个含候选，唯一候选 395 个（VFX 353、声音 8、任务/区域 34），UTF-16LE 命中 0；镜头类候选 0 条（镜头震动/hit stop 证据缺口维持，AV-06）。

## 1. 声音候选（源：wwbk/wwev）

| EventKey(源ID/候选名) | SourceFile+SHA256 | 引用动作(bank+slot) | 源时刻 | 类型(声音\|VFX\|镜头) | 附着骨 | UE落点 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `em001_se` | `sound/em/em001.wwbk`<br>sha256:d99157b41618… | `em001_se`（bank 名候选） | unknown | 声音 | unknown | unknown | raw |
| `em001_village` | `sound/em/em001_v.wwbk`<br>sha256:27a87e89117b… | `em001_village`（bank 名候选） | unknown | 声音 | unknown | unknown | raw |
| `em001_vo` | `sound/em/em001.wwbk`<br>sha256:d99157b41618… | `em001_vo`（bank 名候选） | unknown | 声音 | unknown | unknown | raw |
| `em_cmn` | `sound/em/em001.wwbk`<br>sha256:d99157b41618… | `em_cmn`（bank 名候选） | unknown | 声音 | unknown | unknown | raw |
| `sound\em\em001` | `sound/em/em001.wwev`<br>sha256:e5d233ead0bc… | unknown（wwev 事件表未解码） | unknown | 声音 | unknown | unknown | raw |
| `sound\em\em001_v` | `sound/em/em001_v.wwev`<br>sha256:8b57401f8bc6… | unknown（wwev 事件表未解码） | unknown | 声音 | unknown | unknown | raw |
| `sound\em\wwcol\em001_00` | x2（首: `sound/em/em001.wwev`<br>sha256:e5d233ead0bc…） | unknown（wwev 事件表未解码） | unknown | 声音 | unknown | unknown | raw |
| `sound\em\wwspl\em001` | x2（首: `sound/em/em001.wwev`<br>sha256:e5d233ead0bc…） | unknown（wwev 事件表未解码） | unknown | 声音 | unknown | unknown | raw |

## 2. VFX 候选（源：efx，47 个文件）

以下为 47 个 `.efx` 内提取的粒子/节点/纹理路径候选。`vfx\...` 形态条目为该 efx 引用的共享依赖路径（多数**不在**本批次 73 文件内，依赖闭包未建）；其余为 efx 内部节点名候选。

| EventKey(源ID/候选名) | SourceFile+SHA256 | 引用动作(bank+slot) | 源时刻 | 类型(声音\|VFX\|镜头) | 附着骨 | UE落点 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ACT_LAND` | x4（首: `vfx/efx/em/em001/em001_003.efx`<br>sha256:d3709870cb32…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `ACT_PT` | x9（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `ACT_PT0` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `ACT_PT1` | `vfx/efx/em/em001/em001_202.efx`<br>sha256:0e9ec2956b92… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Action` | x4（首: `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Action0` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Assets\stage\_tex\water\SmallWaves_NM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `B_fire` | `vfx/efx/em/em001/em001_203.efx`<br>sha256:0ead812a0419… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL` | x6（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL0` | x3（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL1` | x4（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL10` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL11` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL12` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL13` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL2` | x4（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL3` | x3（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL4` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL8` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `DECAL9` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter` | x8（首: `vfx/efx/em/em001/em001_100.efx`<br>sha256:55339ce065c8…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter0` | x5（首: `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter1` | x2（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter10` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter11` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter12` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter13` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter14` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter15` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter2` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter3` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter6` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Emitter9` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern` | x6（首: `vfx/efx/em/em001/em001_010.efx`<br>sha256:55973331b3c7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern0` | x4（首: `vfx/efx/em/em001/em001_010.efx`<br>sha256:55973331b3c7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern1` | x2（首: `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern10` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern11` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern12` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern13` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern14` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern15` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern16` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern19` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern2` | x2（首: `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern20` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern3` | x2（首: `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern4` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern5` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern6` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern7` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Extern8` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `FILTER` | x9（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_L_new_ci` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_L_new_g` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_L_new_rt` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_L_old_ci` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_hahen` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_skin` | x6（首: `vfx/efx/em/em001/em001_701.efx`<br>sha256:f67f3f34e9c9…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_skin0` | `vfx/efx/em/em001/em001_702.efx`<br>sha256:bd671d78ab2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_smoke` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_tubu` | x7（首: `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_tubu0` | `vfx/efx/em/em001/em001_702.efx`<br>sha256:bd671d78ab2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_tume` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G0_uroko` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_L_old_g` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_L_old_rt` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_hahen` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_skin` | x6（首: `vfx/efx/em/em001/em001_701.efx`<br>sha256:f67f3f34e9c9…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_skin0` | `vfx/efx/em/em001/em001_701.efx`<br>sha256:f67f3f34e9c9… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_smoke` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_tubu` | x7（首: `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_tubu0` | `vfx/efx/em/em001/em001_701.efx`<br>sha256:f67f3f34e9c9… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_tume` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G1_uroko` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G2_skin` | x2（首: `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G2_skin0` | `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G2_tubu` | x2（首: `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G2_tubu0` | `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G3_skin` | x2（首: `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G3_skin0` | `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G3_tubu` | x2（首: `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `G3_tubu0` | `vfx/efx/em/em001/em001_703.efx`<br>sha256:11105c2197e2… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPU0` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPU1` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPUP` | x11（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPUP0` | x9（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPUP1` | x2（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPUP_yoin` | x4（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPU_plume` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPU_plume0` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `GPU_plume1` | `vfx/efx/em/em001/em001_202.efx`<br>sha256:0e9ec2956b92… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `IMP_fire` | x5（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `IMP_fire0` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `IMP_fire1` | x2（首: `vfx/efx/em/em001/em001_012.efx`<br>sha256:7ef09f57ce5e…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `IMP_fire2` | x2（首: `vfx/efx/em/em001/em001_012.efx`<br>sha256:7ef09f57ce5e…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `IMP_fire4` | `vfx/efx/em/em001/em001_012.efx`<br>sha256:7ef09f57ce5e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `I_mod` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `LIGHT` | x16（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `LIGHT0` | x13（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `LIGHT1` | x4（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `MhPointLightBehavior` | x21（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_GPUP` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_GPUP0` | x2（首: `vfx/efx/em/em001/em001_011.efx`<br>sha256:24724583b423…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_GPUP1` | x3（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_GPUP2` | x2（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_LAND` | `vfx/efx/em/em001/em001_013.efx`<br>sha256:af559f5a372f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_Light2` | `vfx/efx/em/em001/em001_207.efx`<br>sha256:ddbd85ed23b6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_Light3` | `vfx/efx/em/em001/em001_207.efx`<br>sha256:ddbd85ed23b6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `PT_Light4` | `vfx/efx/em/em001/em001_207.efx`<br>sha256:ddbd85ed23b6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `P_fire` | x13（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `P_fire0` | x7（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `P_fire1` | x2（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `P_plume` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Pspark` | x3（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Pspark0` | `vfx/efx/em/em001/em001_014.efx`<br>sha256:7bc08205a554… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Pspark1` | `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `Root` | x19（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `T0_C` | x4（首: `vfx/efx/em/em001/em001_009.efx`<br>sha256:addb98df1ca4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `add_light1` | `vfx/efx/em/em001/em001_213.efx`<br>sha256:b470cacb5c1d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `black` | x2（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `black0` | `vfx/efx/em/em001/em001_014.efx`<br>sha256:7bc08205a554… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `black1` | `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `black_smk` | x3（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `black_smk0` | `vfx/efx/em/em001/em001_014.efx`<br>sha256:7bc08205a554… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `black_smk1` | `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `blur` | x6（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `blur0` | x3（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bom0` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bom7` | `vfx/efx/em/em001/em001_202.efx`<br>sha256:0e9ec2956b92… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bom_0` | `vfx/efx/em/em001/em001_212.efx`<br>sha256:c29680a9220d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bom_black` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bom_black0` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bom_black1` | `vfx/efx/em/em001/em001_202.efx`<br>sha256:0e9ec2956b92… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb` | x5（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb0` | x4（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb1` | x4（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb2` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_power` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_power3` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_round` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_round0` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_round1` | `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_up` | `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_up0` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_up2` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `bomb_yoin` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `claw_NEW` | `vfx/efx/em/em001/em001_700.efx`<br>sha256:b2a0a04d1f2e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `claw_NEW_ci` | `vfx/efx/em/em001/em001_700.efx`<br>sha256:b2a0a04d1f2e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `claw_NEW_ci0` | `vfx/efx/em/em001/em001_700.efx`<br>sha256:b2a0a04d1f2e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `claw_OLD` | `vfx/efx/em/em001/em001_700.efx`<br>sha256:b2a0a04d1f2e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `common\em\trace\cm_uroko\mod\cm_uroko` | x7（首: `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `d_P_dirt` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `d_P_wat` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `d_dirt` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `d_dirt1` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `d_dirt2` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `d_wat` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `dirt` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `dist` | x11（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `dist0` | x4（首: `vfx/efx/em/em001/em001_014.efx`<br>sha256:7bc08205a554…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `dist1` | `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `distort1` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk1` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk2` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk3` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk4` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk5` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `f_smk6` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire` | x11（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire0` | x10（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire1` | x7（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire2` | x7（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire3` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire4` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire9` | `vfx/efx/em/em001/em001_202.efx`<br>sha256:0e9ec2956b92… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_dark` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_imp` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_imp0` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_spread` | `vfx/efx/em/em001/em001_212.efx`<br>sha256:c29680a9220d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_up0` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_up1` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin` | x4（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin0` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin1` | `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin2` | `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin3` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin4` | `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fire_yoin5` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fireloop` | x2（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fireloop1` | x2（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fireloop4` | `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `fireloop5` | `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_MOD` | x5（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_MOD0` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_dirt` | x7（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_dirt1` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_mod` | x2（首: `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_smk1` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `g_smk2` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `glow` | x3（首: `vfx/efx/em/em001/em001_012.efx`<br>sha256:7ef09f57ce5e…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `hit_plume1` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `hit_smk` | x3（首: `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_GPU` | x4（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_GPU0` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_P_plume` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_P_wat` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_mod` | x2（首: `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_mod0` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_smk` | x5（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_smk0` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_smk2` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_wat` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_wat1` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `i_wat2` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `impbom` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `impbom1` | x2（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `impbom2` | x2（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_P_wat` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_smk` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_smk1` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_smk2` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_wat` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_wat1` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_wat2` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `l_wat3` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `light` | x2（首: `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `light0` | x2（首: `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `m_P_wat` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `m_decal` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `m_dirt` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `m_tower` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `m_wat` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `m_yoin` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_P_wat` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_mod` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_wat` | x2（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_wat0` | x2（首: `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_wat1` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_wat2` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_wat3` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `mw_yoin` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plame_main` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plame_up` | x2（首: `vfx/efx/em/em001/em001_205.efx`<br>sha256:f7acf46bf9b1…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plame_up1` | `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plame_up2` | `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plame_up_bomb` | x2（首: `vfx/efx/em/em001/em001_211.efx`<br>sha256:7c36008ef175…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plume` | x10（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plume0` | x3（首: `vfx/efx/em/em001/em001_003.efx`<br>sha256:d3709870cb32…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `plume1` | `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `r_mod` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `r_mod0` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `r_smk1` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `r_smk2` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `s_P_dirt` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `s_dirt` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `shovel` | x2（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `shovel0` | `vfx/efx/em/em001/em001_011.efx`<br>sha256:24724583b423… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `smk_yoin` | x4（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `smk_yoin0` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `smk_yoin1` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `smk_yoin2` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `smk_yoin3` | `vfx/efx/em/em001/em001_015.efx`<br>sha256:16b822d50ab5… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `snP_plume` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_GPU` | x6（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_GPU0` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_P_dirt` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_SHOVEL` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_dirt` | x5（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_mod` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_plume` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk1` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk2` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk_yoin` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk_yoin0` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk_yoin1` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk_yoin2` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `sn_smk_yoin3` | `vfx/efx/em/em001/em001_015.efx`<br>sha256:16b822d50ab5… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `spark` | x3（首: `vfx/efx/em/em001/em001_005.efx`<br>sha256:ec5927c2e1d4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `spark0` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `spark1` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `spark2` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `spark3` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `spark4` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `t_MOD` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `t_mod` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `t_mod0` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_cubemap\cm_cube_001_CM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_000_F_NM` | x6（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_001_F_NM` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_002_F_NM` | x4（首: `vfx/efx/em/em001/em001_004.efx`<br>sha256:6c8073241405…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_003_F_NM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_004_F_NM` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_005_F_NM` | `vfx/efx/em/em001/em001_219.efx`<br>sha256:23aca6a48b87… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_008_F_NM` | x18（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\cm\cm_flowmap\cm_flow_009_F_NM` | x18（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\em\em001\em001_700_BM` | `vfx/efx/em/em001/em001_700.efx`<br>sha256:b2a0a04d1f2e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\em\em001\em001_700_NM` | `vfx/efx/em/em001/em001_700.efx`<br>sha256:b2a0a04d1f2e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\em\em001\em001_800_BM` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\dds\em\em001\em001_800_NM` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\efx\cm\cm_em\ground\cm_em_land_001` | x2（首: `vfx/efx/em/em001/em001_702.efx`<br>sha256:bd671d78ab2d…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\efx\cm\cm_em\ground\cm_em_land_100` | x2（首: `vfx/efx/em/em001/em001_003.efx`<br>sha256:d3709870cb32…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_hahen\md_cm_dirt000\md_cm_dirt000` | x8（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_hahen\md_cm_ice000\md_cm_ice000_002` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_hahen\md_cm_leaf000\md_cm_leaf000` | x3（首: `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_hahen\md_cm_part000\md_cm_part000` | `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_hahen\md_cm_stone000\md_cm_stone000` | x2（首: `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_hahen\md_cm_wood000\md_cm_wood000` | x8（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_cm_wave002` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_wave001_BM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_wave002_F_NM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_wave002_MM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_wave002_normal_VM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_wave002_pos_VM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\mod\cm\md_liquid\md_cm_wave000\md_wave002_tangent_VM` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_fire_900` | x15（首: `vfx/efx/em/em001/em001_001.efx`<br>sha256:702fbaa30ce4…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_fire_901` | x26（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_hahen_000` | x2（首: `vfx/efx/em/em001/em001_050.efx`<br>sha256:dde603a90381…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_hahen_900` | x8（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_hahen_901` | x6（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_light_000` | x21（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_liquid_000` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_liquid_900` | x9（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_smoke_000` | `vfx/efx/em/em001/em001_200.efx`<br>sha256:db861b2747a7… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm\cm_smoke_900` | x24（首: `vfx/efx/em/em001/em001_000.efx`<br>sha256:054abfc16b8f…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm_decal\cm_decal_000` | x8（首: `vfx/efx/em/em001/em001_006.efx`<br>sha256:e53483a330ec…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `vfx\uvs\cm_decal\cm_decal_100` | x2（首: `vfx/efx/em/em001/em001_800.efx`<br>sha256:c9262ceeafd3…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_GPUP_rain` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_GPUP_rain0` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_Normal` | `vfx/efx/em/em001/em001_210.efx`<br>sha256:06aafa9d4d2d… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_P_wat` | x2（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_hamonNormal` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_hamonNormal0` | `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_mod` | x6（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_smk` | x3（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_smk1` | `vfx/efx/em/em001/em001_216.efx`<br>sha256:64735487f23f… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_smk2` | `vfx/efx/em/em001/em001_217.efx`<br>sha256:57ca5256fa3e… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat` | x4（首: `vfx/efx/em/em001/em001_002.efx`<br>sha256:641651845123…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat0` | x2（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat1` | x5（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat10` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat2` | x3（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat3` | x4（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat4` | x3（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat5` | x2（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat6` | x2（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat7` | x2（首: `vfx/efx/em/em001/em001_201.efx`<br>sha256:ae6b26a4c65a…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat8` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_wat9` | `vfx/efx/em/em001/em001_208.efx`<br>sha256:f60284dba6c6… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_ww` | x4（首: `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78…） | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |
| `w_yoin` | `vfx/efx/em/em001/em001_008.efx`<br>sha256:a7c8b5606e78… | unknown（efx 未解码） | unknown（timl 未解码） | VFX | unknown | unknown | raw |

## 3. 任务/区域候选（参考，不属音画三类型）

来自 q00301 FSM 与 boss 区域 SOBJ 的流程节点/组件类名候选，仅作动作→事件绑定的旁证线索：

| EventKey(源ID/候选名) | SourceFile+SHA256 | 引用动作(bank+slot) | 源时刻 | 类型(声音\|VFX\|镜头) | 附着骨 | UE落点 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ActionEnd` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `ActionSet_em` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `ContinueQuest` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `Draw_OFF_t0000` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `EmAIState` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `EventBegin_em` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `EventEnd_em` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `EventStart` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `FcEmDesireSetter` | x7（首: `quest/enemy/boss/em001_00_st101_00.sobj`<br>sha256:3e6eaf63ba50…） | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `FcEmRepopSetter` | x7（首: `quest/enemy/boss/em001_00_st101_00.sobj`<br>sha256:3e6eaf63ba50…） | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `FcEmSetter` | x7（首: `quest/enemy/boss/em001_00_st101_00.sobj`<br>sha256:3e6eaf63ba50…） | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `Init` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `Init_t0000` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `MoveAndDrawOff` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QP_check200` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QP_check210` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QP_check213` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QP_set210` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QP_set220` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QuestProgress` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `QuestProgress_qt` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `Timer0` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `TimerCheck_qt` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `Warp` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `WarpEm_qn` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `Zone` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `ZoneCheck_qp` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `cAIFSMProcessContainer` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `cFSMQuest` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `cFSMQuestEnemy` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `cFSMQuestPlayer` | `quest/q00301/fsm/em/em001_00.fsm`<br>sha256:a5268fa8be9d… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `em001_00_000` | `quest/enemy/boss/em001_00_st102_03.sobj`<br>sha256:c27f7891f41a… | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `quest\enemy\boss\trace\em001_00_st101_00` | x3（首: `quest/enemy/boss/em001_00_st101_00.sobj`<br>sha256:3e6eaf63ba50…） | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |
| `quest\enemy\boss\trace\em001_00_st102_00` | x2（首: `quest/enemy/boss/em001_00_st102_00.sobj`<br>sha256:d5baa6faa3a4…） | unknown | unknown | 任务/区域（参考） | unknown | unknown | raw |

## 4. 必需事件占位（unknown 行）

已知必需事件类别各留一行占位；本批次内**无任何已确认对应**，不得把第 1~3 节候选名擅自填入：

| EventKey(源ID/候选名) | SourceFile+SHA256 | 引用动作(bank+slot) | 源时刻 | 类型(声音\|VFX\|镜头) | 附着骨 | UE落点 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| unknown（吼叫） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（脚步） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（振翅） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（吐息火球） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（尾击） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（受击） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（死亡） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |
| unknown（断尾） | unknown | unknown | unknown | 声音+VFX | unknown | unknown | unknown |

## 5. 遗留缺口

- em001_se.nbnk / em001_vo.nbnk 未解码：事件 ID→音轨→WEM 映射未知，无法声称任何 bank+slot 引用动作
- wwev 的事件表为二进制结构，本次仅提取到自身路径与 wwcol/wwspl 引用字符串，事件名/ID 表未解出
- efx 含 'timl' 魔数（TIML 时刻表引用）但未解码，特效源时刻不可得
- wwcol/wwspl/brem 无 ASCII/UTF-16LE 可读候选，语义未知
- 5 个 .tex 为纹理未做字符串扫描
- efx 引用大量共享依赖（vfx\uvs\cm\*、vfx\mod\cm\*、vfx\dds\cm\*、vfx\efx\cm\cm_em\ground\cm_em_land_001/100、Assets\stage\_tex\water\SmallWaves_NM 等）不在本批次 73 文件内，依赖闭包未建
- 吼叫/脚步/振翅/吐息火球/尾击/受击/死亡/断尾等必需事件在本批次内无任何已确认对应（映射表以 unknown 行占位）
- 镜头震动/hit stop 源证据未取证（对应 AV-06）

## 6. Epic UE5.8 官方参考

以下官方机制页供 UE 侧落点实施参考，**不证明原作行为**：

- [Niagara 概述](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/overview-of-niagara-effects-for-unreal-engine)
- [创建视觉效果（Niagara）](https://dev.epicgames.com/documentation/unreal-engine/creating-visual-effects-in-niagara-for-unreal-engine)
- [Niagara 音效模块](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/how-to-create-audio-effects-in-niagara-for-unreal-engine?application_version=5.3)

## 7. 边界声明

- 本页为骨架：所有行状态=raw 或 unknown；任何一行升格需先有对应格式解码证据（E08 工作包）与动作绑定证据（E02/A5）。
- 本轮零写入 raw、零解码音频数据、零 UE 资产创建；批次文件未做任何修改。
