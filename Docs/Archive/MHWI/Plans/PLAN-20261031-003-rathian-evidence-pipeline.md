# PLAN-20261031-003：雌火龙原作证据与定向解包流水线

- 状态：draft；实施步骤方案。已有原始资料只读复核完成；新提取状态见末节与本轮 CHG。
- 日期：2026-10-31。
- 用户需求：总体还原方案分工中的数据考据、缺失资料定向解包及证据闭合步骤。
- 关联模块 / 接口 / 问题：mhwi-unpack-data、mhwi-rathian-animation；原作行为接口均为候选，未改变运行接口。
- 实施记录：本轮仅文档与隔离原始证据；未实施玩法。[总体方案](PLAN-20261031-002-rathian-restoration-master.md)。

## 现状与目标

**项目现状证据**：本轮逐文件读取 `ArtSource/ThirdParty/MHWRathalos/extraction-manifest.json`，300/300 文件尺寸与 SHA256 一致，合计 80,708,036 B。`MHWRathalos` 是历史目录名，文件身份属于 em001 雌火龙，不能改取 em002。既有全量索引 171,615 路径、13 归档；本轮归档尺寸与 mtime_ns 同索引一致，未计算整包内容 SHA。原始目录 `em/em001/00/` 含 105 THK、2 THKLST、19 LMT、10 MBD、1 AT、1 ACTP2、42 COL、37 SHLP、2 TIML；此外3份掉落表。

**既有静态结果，非本次重新解析**：342 ACTP2（142启用）、70 Atk2原记录（主35/shell35）、PBC三层对象结构已有[格式证据](../Reference/MHWI-Rathian-Format-Evidence-20261030.md)。319个ACTP2名称只有历史DTI反CRC候选，数组位置不等于动作ID。848有效动画是源库条目/导入资产覆盖数字，不是848招。

**本次发现**：基础300文件之外还有 `sound/em/` 事件、`sound/wwise/Windows/em001_{se,vo}.nbnk`、`vfx/{dds,efx}/em/em001/`，以及直接带em001名的外部任务FSM/区域配置。这里的名称匹配只建立候选关联，未证明LR资格、完整依赖或原作实际触发。

**目标**：建立可追溯的“归档身份→资源→结构→消费者→动作时序→运行观测”链条；每条结论独立标记 `raw / parsed / bound / runtime-verified / unknown`。Epic支持UE承载能力，不能证明MHWI机制。

## 官方与维护者来源、版本及结论边界

| 来源 / 适用版本 | 来源支持的结论 | 项目处理与缺口 |
| --- | --- | --- |
| [Epic Data Assets](https://dev.epicgames.com/documentation/unreal-engine/data-assets-in-unreal-engine?application_version=5.8)，UE5.8 | UDataAsset存储系统数据；UPrimaryDataAsset提供PrimaryAssetId与bundle加载支持 | 可作为导入后数据承载候选；不是原作数据语义规范，也未定本项目最终类型 |
| [JodoZT/MHWNoChunk Chunk.cs](https://github.com/JodoZT/MHWNoChunk/blob/master/MHWNoChunk/Chunk.cs)，项目固定2026-10-22 master snapshot | Iceborne chunk索引、分块读取与解码实现 | 项目 `extract_resources.py` 适配；来源哈希见 `tool-sources.json`。使用本机UE5.8 Oodle，不下载或复制运行库 |
| [Leviathon维护者仓库](https://github.com/AsteriskAmpersand/Leviathon)，本次只核对仓库说明，尚未固定commit | MHW THK参考反编译/编译工具与语言 | 可供THK结构资格验证的候选；尚未安装、未对em001完成解析，更不能证明随机/优先级语义 |
| [Fexty ACTP2模板](https://github.com/Fexty12573/MHW-010-Templates/blob/cea17f2c0c7d5c4f2ed421a7d0e04586bfb275f7/actp2.bt)，固定cea17f2 | ACTP2/UnitProperty结构 | 沿用项目已有Property包装适配及字节往返证据；不是AI执行器 |
| [Synthlight COL模板](https://github.com/Synthlight/MHW-Editor/blob/b6ff379b13079a4abb99490590fb05dfe6851bbc/010%20Templates/col.bt)、[Collisions说明](https://github.com/Synthlight/MHW-Editor/wiki/Collisions)，固定b6ff379 | Names/UID/攻击索引、Atk2字段 | 几何载荷/骨骼映射/实际伤害公式仍unknown |
| [wowo-dot/mhw-anim-tools](https://github.com/wowo-dot/mhw-anim-tools)，项目缓存v1.1.0；[Feuleur工具1.3.9](https://github.com/Feuleur/blender-mhworld-tools-suite/releases/tag/1.3.9) | LMT/TIML读取、素材转换能力 | 保持既有逐文件哈希；不以新上游版本覆盖后沿用旧资格结果 |

社区工具维护者是其格式实现的直接来源，不是Capcom官方玩法规范。本次网页仅核对可用的维护者页面与Epic5.8页；固定模板网页缓存未取得时依本地已固定来源清单，不伪称重新下载核验。

## 范围与验收标准

1. 普通 em001/00 + LR 字段为首验收基线候选；具体任务、区域、尺寸与玩家装备仍需在实现前固定。`00/`同时含高等级记录，不能整库标LR。
2. 在新 `Saved/MHWI-Rathian-20261031-PlanEvidence/` 批次补取原始候选资料；不覆盖旧manifest，不写游戏或Content，不启动原作或UE。
3. 新提取每文件保留来源归档、解压流偏移、尺寸、SHA256；复读结果一致。简明证据入 `Tools/MHW/rathian-plan-evidence-20261031.json`，原资源及大索引留Saved。
4. 原作身份、等级资格、动作绑定、碰撞时序、消费者与运行证据分开验收；未知项须保留阻断等级，禁止猜值填充正式数据。

## 技术方案

### 证据模型（拟新增，不是现有接口）

每项记录至少包含 `EvidenceId / SourceFileSHA256 / Archive / StreamOffset / ByteRange / ParserPin / RawValue / Unit / SemanticStatus / ConsumerEvidence / RuntimeCapture / RankEligibility / Unknowns`。源时刻保留原始单位和时基；换算秒需单列依据，不以UE播放帧号替换。

建立四张只读中间表：资源清单、动作身份映射、时间轴事件映射、参数消费者映射。键使用源路径+SHA+原始ID，不用翻译名、UE资产序号或ACTP2数组索引代替原生ID。只有 `bound` 以上数据才允许进入相应忠实行为路径；临时演示数值必须有单独状态，不能回写原证据。

### 缺口与任务包

| 优先级 / ID | 具体缺口 | 已有入口 | 可执行步骤与通过门 |
| --- | --- | --- | --- |
| P0 E01 | THK/THKLST执行图、等级条件、随机/优先级/动作请求 | `data/em001.thklst`、105 THK；event/q301另表 | 固定Leviathon commit与依赖，先一张THK结构→源偏移→反编译/重编码资格；未知opcode保留raw并阻止忠实导出；不得把节点可读当已还原决策 |
| P0 E02 | Action/ACTP2→LMT bank/slot→TIML/AT UID→COL/SHELL | ACTP2、19LMT、10MBD、em001_tree.at、COL Names/UID、SHLL/SHLP | 建跨表连接，记录一对多/缺失/冲突；逐招输出入场、有效窗、取消、位移、退出及等级资格。数组索引不能凭相等连接 |
| P0 E03 | 碰撞几何/骨骼→141骨，受击部位→12肉质/7硬直组 | COL原始geometry、MOD3骨表、DTT_EPG | 固定几何布局/消费者证据，验证局部/世界坐标、缩放及部位映射；输出debug几何对照；未知ID不默认到头部 |
| P0 E04 | PBC破坏耐久、断尾条件及反应事件 | PBC Info/State/Detail、EPG、既有加载保存链 | 追真实读消费者或独立机制证据；2006/2007只是未定语义字段，不能当耐久；切断值300不能当任务最终阈值 |
| P0 E05 | LR资格与任务血量/攻击/部位倍率及伤害公式 | DTT各rank字段、任务索引、主35+shell35 Atk2 | 先固定具体任务，再追任务入口引用及倍率消费者。HP3000/Atk2 Motion_Value只保留基础/原字段，不直接输出最终HP/扣血 |
| P1 E06 | 完整受击/倒地/口水硬总时长及中断 | ACTP2 mLoopTime、EM_DMG、LMT入场/循环/起身 | 对当前动作注册及时间消费者取证；5.5/6.5禁止经验命名。逐帧运行作为另一路候选，需明确采集条件后执行 |
| P1 E07 | 火球发射socket/时刻、运动/寿命、爆炸/残留火焰 | SHLL/SHLP、TIML、COL、EPV3及新增VFX | 分离投射物伤害与视觉事件；逐项闭合速度单位、寿命、复击和owner生命周期，不让视觉销毁决定伤害结束 |
| P1 E08 | 音效/VFX事件依赖与可用素材 | EPV3/EPVSP/WWCT及新增WW*、NBNK、EFX/TEX | 本轮先提取60候选文件；后续解析引用链，找共享资源并再小批取。未证明47 EFX都是本体LR特效，也未解码Wwise音频 |
| P2 E09 | 外部任务、区域迁移、巢穴、生态事件 | 新13候选任务/区域文件、THK与stage | 先建立任务引用关系；q00301命名仅候选，不自动定为首验收任务。场景配置可读不等于复刻了原作地图 |

捕获30%、怒疲倍率现有结果来自维护者布局字段解读；无当前业务消费者或原作运行闭合。状态优先级、断尾后毒攻击资格、闪光/陷阱免疫与递增等必须单独取证，不按其他代怪猎经验补全。

### 多候选取证路线与选择门

- 静态路线：固定THK工具及原生读取消费者，优点是可定位字段与分支，代价是opcode/间接调用语义成本高；需要深度provider环境。
- 运行路线：受控离线原作场景逐帧/事件采集，优点是直接观测动作和最终结果，代价是随机样本覆盖、装备/任务控制与观测工具建设。
- 两条路线可交叉佐证，但维护者没有完整雌火龙业务规范；本方案只列步骤，进一步实质取证路线由主方案选择门决定。本轮已授权的定向提取不依赖新架构选择。

本次实际检查 REA 6.8.0：没有打开目标；Ghidra候选因 `GHIDRA_INSTALL_DIR` 未配置不可启动。本次未做消费者反编译，没有声称这些缺口永不可解。技能只提供操作流程，不带每调用审批要求。

## 接口与数据迁移

| 接口 ID / 路径 | 当前行为/值 | 目标行为/值 | 调用方/蓝图影响 | 迁移顺序 |
| --- | --- | --- | --- | --- |
| 原始manifest | 本地300文件原证据 | 保持；新批另存73候选 | 无 | 先验证身份再提取 |
| `Tools/MHW/rathian-plan-evidence-20261031.json` | 本批前不存在；本轮已交付 | 仅清单、指纹与未解边界 | 无；不由游戏运行时加载 | 提取完成后生成 |
| 候选中间表 | 尚无完整动作语义表 | 带源偏移/单位/资格/未知项的数据 | 后续数据导入器，未定具体UDataAsset类 | 结构→绑定→运行核验 |
| 已有UE资产 | 历史Rathalos路径中是em001 | 不搬移、不重导入 | 无 | 实施阶段按资产核验后安排 |

不修改现有公开签名、反射字段、蓝图或DataAsset。未来导入需在游戏线程修改UObject，异步只处理不可变原始数据；弱引用和generation校验后才能应用结果。

## 实施步骤与依赖

1. **身份冻结**：核对em001、EXE/text（如后续用消费者）、归档尺寸/mtime、已有300源hash、工具固定清单。任一不符停止复用旧证据。
2. **选择预算**：规范化索引路径前导`/`，只选择下述两个正则的并集；预计算73文件、16,446,967B，小于32MiB。复制已经过尺寸/mtime校验的索引至新批次，避免重新扫描13包；仍由提取器再检查缓存资格。
3. **离线定向提取**：新批次首次不存在才创建；按下面命令运行。失败保留部分产物状态，不以目录存在当完成；不得合并覆盖旧manifest。
4. **复读核验**：逐文件读取并比较manifest的尺寸/hash；生成紧凑JSON，附源工具、Oodle及清单hash、归档stamps、实际命令与来源边界。
5. **语义工作包分发**：E01交AI；E02/E06及层叠动画交动画；E03/E04/E05/E07交战斗；E08/E09由资源/地图侧承接。每包先输出一个可闭合示例，再扩到全部目标集合。
6. **导入门**：结构和引用闭合后才生成UE候选数据；运行对照未完成仍标待验证，不因离线parser通过提升为忠实已验。

本次提取命令（首次先在新目录复制经验证的旧索引；不是提取器自动复制）：

```powershell
python Tools/MHW/extract_resources.py `
  --game 'F:\PCprogram\Steam\steamapps\common\Monster Hunter World' `
  --oodle 'E:\UE\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\runtimes\win-x64\native\oo2core.dll' `
  --output 'Saved/MHWI-Rathian-20261031-PlanEvidence' `
  --pattern '^(?:sound/em/(?:em001(?:_v)?\.(?:wwbk|wwev)|wwcol/em001_00\.wwcol|wwspl/em001\.wwspl)|sound/wwise/Windows/em001_(?:se|vo)\.nbnk|vfx/(?:dds|efx)/em/em001/|quest/(?:q00301/fsm/em/em001_00\.fsm|enemy/boss/em001_00_st10[12]_0[0-3]\.sobj|bui/br00_em001_00_\d+\.brem)$)' `
  --max-mb 32
```

后续重验ACTP2/COL应指定新输出参数，防止默认重写历史报告；以下为计划命令，未执行：

```powershell
python Scripts/MHWI/read_action_params.py --self-check --output Saved/MHWI-Rathian-Recheck/actp2.json --summary Saved/MHWI-Rathian-Recheck/actp2-summary.json
python Scripts/MHWI/read_monster_collision.py --output Saved/MHWI-Rathian-Recheck/collision.json --evidence Saved/MHWI-Rathian-Recheck/collision-summary.json
```

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 来源冻结 | 300文件尺寸/SHA、13包stamps对照 | 零不一致 | 非整归档加密指纹 |
| 新批提取 | 提取CLI、复读manifest | 73文件/16,446,967B，SHA一致 | 原始候选，不是语义解码 |
| THK资格 | 固定工具单文件/损坏样本/往返 | 原始偏移可重建；未知op显式报告 | 不自动涵盖105表业务 |
| 动作连接 | 逐键完整性、重复/空引用检查 | 一条完整招式链有来源 | 未来执行，当前未完成 |
| 任务及最终伤害 | 固定任务+装备、消费者和受控样本 | 最终数值与条件可解释 | 未来执行，不据基础值替代 |
| 文档 | `python Scripts/Docs/check_docs.py`、`git diff --check` | 通过 | 父代理统一执行、记录实际结果 |

## 风险与回退

- 新批目录使用Saved忽略；原始NBNK/EFX等不加入版本库。提取记录偏移在解压流地址空间，不能直接seek物理bin。
- 同名资源与正则覆盖只建立候选集合；共享音效、纹理、任务倍率、场景引用仍可能在别处。
- 提取不是事务：命令中止会留下部分文件；按manifest及SHA识别成功，使用新批次重试。已存在且内容不同必须停止。
- 本轮回退只移除新增方案/紧凑证据和该隔离批次；不恢复或删除用户已有修改。若执行删除须先验证解析后的绝对路径属于本批次；本文不执行删除。

## 文档同步清单

父代理统一维护本轮CHG、Plans/Changes索引及必要现状入口。此工作包不修改现有系统文档或模块接口，不创建已实现怪物模块的假象。后续实际接入时更新Combat-AI、Interfaces、modules.json及Known-Issues。

## 本次实际执行与未验证项

- 已执行：官方/维护者页面搜索；300源文件尺寸/hash复核；13归档stamps对照；外部路径候选与体积预算；REA服务能力检查。
- 已执行：新批次73/73文件定向提取并复读尺寸/SHA256一致，共16,446,967B（15.69MiB）；其中音频候选8文件14,779,047B、VFX候选52文件1,628,162B、任务/区域候选13文件39,758B。提取后再次核对既有300文件与13归档stamps一致。详见[本轮紧凑证据](../../Tools/MHW/rathian-plan-evidence-20261031.json)。
- 未执行：THK反编译、消费者逆向、Wwise解码、VFX语义解码、任务倍率闭合、原作启动、UE构建/PIE、正式资产导入。
