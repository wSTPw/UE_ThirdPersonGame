# CHG-20261117-004：THK 语义审计（M1/M2）与斗技场场景提取

- 状态：completed（M1/M2 证据产出 + Arena 原始数据落库）；CFG 剪枝与场景转换未做
- 日期：2026-11-17
- 需求摘要：完成"不跑原作"部分的 M1/M2；斗技场找现成模型无果后解包提取。
- 关联：[PLAN-20261117-001](../Plans/PLAN-20261117-001-mhwi-thk-semantics-and-arena.md)、[MHWI-Current.md](../Plans/MHWI-Current.md) M1/M2、[CHG-20261117-001..003](README.md)

## 结果一：M2 动作发射清单（v1）

来源：冻结副本 `Saved/DevFlow/Rathian-Condition-Audit-20261104/source-baseline/EvidenceInput/thk-all-raw.json`（105 thk / 1795 节点 / 13015 段，roundtrip_exact）。脚本 [map_rathian_action_emissions.py](../../Scripts/MHWI/map_rathian_action_emissions.py)。

- **985 段带 `actionID`**，去重 **147 个动作 ID**；对照 Leviathon ActionDumps `em001.txt`（285 条，已入库 `Tools/MHW/ActionDumps/em001-actiondump.txt`）：**111 个有语义名（76%）**，36 个未命名（ID 286..321+，超出 dump 范围——本身是新发现：THK 在用 dump 未覆盖的编号）。
- **7 处 0xB8 rank 门全部是 HR(1)/MR(2) 分支，无 LR(0) 专属门** → 下位动作集是"全集减去 HR/MR 增量"，不是独立子集。语义声明来自社区 Fexty：`switch(current_quest().is_rank)`，0=LR/1=HR/2=MR/3=AT。
- 发射集中于 9 个行为上下文（`em001_55` 主战斗脑、`em001_01/91` 移动等）。样例：`4=IDLE_TIRED`、`8=TAKE_OFF`、`11=LANDING`、`12=WALK`。

**边界**：本清单是全集；"LR 可达"的 CFG 剪枝需要 Leviathon 反编译器的段流语义（flowControl/branchingControl），列入下轮。

## 结果二：M1 条件语义三栏表

脚本 [audit_thk_condition_semantics.py](../../Scripts/MHWI/audit_thk_condition_semantics.py)。判定规则：距离类=连续正值、角度=0..360、无参类=全零、rank=0..3、布尔=0/1。

- **26 类在用、全部"已证"、0 冲突**（1 类声明了但 THK 未使用，记"未出现"）。
- 未命名 34 类：`0x2`（7947 用，p1 全 0，疑似顺序流转）、`0x0`（2877 用，p1=0/5/10/15/20，疑似计时/步进）、`0x5a`（186 用，p1=0..4 枚举，与交接预判一致）。
- 产出：[三栏表](../Reference/MHWI-Rathian-THK-Condition-Semantics-20261117.md) + [证据 JSON](../../Tools/MHW/rathian-thk-condition-semantics-20261117.json)。

**边界**：参数自洽 ≠ 原作运行等价；运行验证仍属 M3（待授权）。

## 结果三：斗技场场景原始数据

- 现成模型检索无果：Sketchfab API 三轮 0 个可下载结果；Models-Resource 反爬无法列出条目。
- stage 编号候选锁定 st201/st202（st203 无 mod3，是导航数据）。提取 **146 文件 / 137.30 MiB** 至 `ArtSource/ThirdParty/MHWRathalos` 同级 `ArtSource/ThirdParty/MHWRathalos-em002` 旁的 `ArtSource/ThirdParty/MHWI-Stages/`（已加入 .gitignore）：**12 个场景 mod3、20 张 tex、13 份 mrl3、35 份 sdl**，含水体/瀑布变体。
- **哪个是斗技场/特殊斗技场未最终确认**（wiki 无文件级对照）；两批都提取，确认后择一转换。

**未做**：sobj/mod3 场景转 FBX（套件 `sobj` 导入器未验证）、UE 导入、贴图转 PNG。

## 修改清单

| 文件 | 内容 |
| --- | --- |
| `Scripts/MHWI/map_rathian_action_emissions.py`、`Scripts/MHWI/audit_thk_condition_semantics.py` | 新增两个证据生成脚本 |
| `Tools/MHW/rathian-action-emission-inventory-20261117.json`、`rathian-thk-condition-semantics-20261117.json`、`ActionDumps/em001-actiondump.txt` | 入库证据 |
| `Docs/Reference/MHWI-Rathian-THK-Condition-Semantics-20261117.md` | 三栏表 |
| `ArtSource/ThirdParty/MHWI-Stages/`（gitignore） | 146 文件场景原始数据 |
| `.gitignore` | 新增 MHWI-Stages 忽略项 |
| `Docs/Plans/MHWI-Current.md` | M1/M2 状态行更新 |

## 实际验证

| 操作 | 结果 |
| --- | --- |
| `python Scripts/MHWI/map_rathian_action_emissions.py` | emitted=985 distinct=147 named=111 rank_gates=7 |
| `python Scripts/MHWI/audit_thk_condition_semantics.py` | rows=26 proved=26 conflict=0 unnamed=34 |
| `python Tools/MHW/extract_resources.py --pattern '^stage/st20[12]/'` | 146 文件 / 137.30 MiB |
| `python Scripts/Docs/check_docs.py` | PASS |

## 回退

删除上表新增文件与 .gitignore 两行即可；未触碰引擎资产与其他会话工作。
