# MHWI 雌火龙还原方案完整性核对（2026-11-02）

- 日期：2026-11-02。
- 性质：**静态核对**。只读 Docs 方案/现状页、既有证据 JSON、源码与工作区状态；本轮未重新解包、未启动原作、未运行 PIE、未编译（构建另见 [PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md) 实际结果）。
- 范围：用户指定四板块——行为逻辑（攻击招式、AI 状态机）、数值设定（生命值、伤害、抗性）、动画与模型资源引用、音效与特效配置。
- 证据等级沿用 [总方案](../Plans/PLAN-20261031-002-rathian-restoration-master.md) 的五级定义；本页把"方案文档缺失"与"原作数据语义未闭合"分开，前者是文档问题，后者是取证进度。

## 一、总判定

| 板块 | 方案覆盖 | 数据/资产落地 | 结论 |
| --- | --- | --- | --- |
| 行为逻辑 | 完整（AI-00~12、取消/优先级/终态契约） | 部分落地：THK 解析资格通过，首链咬击/冲撞已提取；VM 语义未闭合 | 结构完整；语义取证进行中 |
| 数值设定 | 完整（C0~C6 分段管线） | 基础值齐全（HP/肉质/硬直/异常）；任务倍率与公式未闭合 | 结构完整；公式与倍率待取证 |
| 动画与模型 | 完整（A0~A5） | 848 动画+模型+材质已导入验证；语义映射/播放层未建 | 结构完整；映射与播放层待实施 |
| 音效与特效 | 有步骤但最薄（A5 五步+E08） | 仅 73 个 raw 文件，零 UE 资产、零事件映射 | **本轮补全细案**（见 PLAN-20261102-001） |

方案文档结构本身已完整：每个未闭合项都能落到编号工作包（E01~E09、AI-00~12、A0~A5、C0~C6）与通过门。以下缺失项清单中，标"文档缺失"的项由本轮补全；标"证据缺口"的项保持原工作包归属，不因补文档而变成已闭合。

## 二、行为逻辑（攻击招式、AI 状态机）

已有证据：

- AI 状态组织、地空迁移、取消/优先级/终态契约：[AI 细案](../Plans/PLAN-20261031-004-rathian-ai-world.md)（AI-00~AI-12）。
- THK 解析资格**通过**：105 THK/2 thklst、1795 节点/13015 段，Leviathon commit `1e647f08` 字节重编码一致；负例自检（signature/version/node_pointer/segment_count/truncated_core）全部正确拒绝（`Tools/MHW/rathian-thk-chain-evidence.json`）。
- 首链已提取：咬击 `ACTION::BITE`(id 83, ACTP2 #15)、冲撞分支 `DASH_BITE2`(86)/`DASH_BITE_TIRED`(87)、转尾 `ROLLING_TAIL_ATTACK2_L/R`(75/76)，共 5 动作完成 ACTP2 记录关联；调用方节点与源偏移可追。
- 首链运行代码已存在：`Source/IntroCpp/MHWI/Monsters/`（ThkExecutor/SourceMovement/SourceCollision/FirstChainPawn，1546 行，见 [CHG-20261031-003](../Changes/CHG-20261031-003-rathian-first-chain.md) 补录）。

| 编号 | 缺失项 | 类型 | 归属 |
| --- | --- | --- | --- |
| BEH-01 | THK 条件函数/opcode 业务语义未闭合，不能宣称原作决策等价。**2026-11-03 重大进展**：Leviathon `default.fexty`（社区映射，本地已有）覆盖 **27/58 条件类型、81.5% 条件段使用**；参数形态全部自洽（0x6/0x8=距离 cm、0x16=角度对、0x1E=发怒、0x1F=疲劳、0x70=飞行、0xB8=等级、0x76=部位破坏）；首链冲撞分支 0x1F 语义=疲劳（86 常态/87 疲劳变体自洽）。剩余：27 类逐项参数校验、33 类低频缺口、定向运行观测；路线见 [PLAN-20261103-001](../Plans/PLAN-20261103-001-rathian-review-adoption.md) | 证据缺口（社区映射已覆盖主干，待校验） | P1/定向观测 |
| BEH-02 | **2026-11-05更正**：旧344条name↔id↔vtable导出起点错位、跨表按名称去重，完整注册表闭合口径撤回。新32B布局使BITE=83；em001表285/285与固定dump一致，新增表指针getter及原生注册循环字段/stride读点；THK动作查找/启动和caller怪物归属未证，见[首链审查](MHWI-Rathian-FirstChain-Audit-20261105.md) | 证据缺口（布局原生静态支持，完整动作绑定开放） | E02 |
| BEH-03 | LR 招式资格表未建立（`00/` 混有 G 级标签，342 ACTP2≠LR 招式表）。**2026-11-03 进展**：`0xB8 = current_quest().is_rank(LR/HR/MR/AT)` 已定位——可从 THK 节点按等级门控反推下位可达动作清单（分母不再用 344 全量）；流程见 [PLAN-20261103-001](../Plans/PLAN-20261103-001-rathian-review-adoption.md) P1 | 证据缺口（有可行路线） | P1 |
| BEH-04 | 同帧多事件状态优先级表无原作证据（工程幂等契约已有） | 证据缺口 | AI-08/C5 |
| BEH-05 | 咬击/冲撞之外的 105 THK 其余链路未逐条提取 | 证据缺口 | E01/AI-07 |
| BEH-06 | 首链实施无变更记录、Plans 索引缺 PLAN-007、modules.json 未登记 Monsters 入口 | **文档缺失→本轮补全** | CHG-20261031-003、索引 |

## 三、数值设定（生命值、伤害、抗性）

已有证据（[LR 数据页](../Reference/MHWI-Rathian-LR-Data-20261030.md)，全部来自固定归档实际解析）：

- 基础 HP 3000；12 组肉质完整表（斩/打/弹/火水冰雷龙/气绝/夺取）；7 组硬直阈值 240/300/180/180/210/210/200；切断 Sever=300。
- 发怒：累积 600、持续 80s、速度×1.05、伤害×1.15、玩家伤害×1.10、脱战衰减×0.10、10 段血量累积倍率表。
- 疲劳：LR 70s、耐力 500–600；异常抗性全套 Base/Buildup/Max/持续（毒/眠/麻/Stun/疲劳/乘骑/爆破/捕获）；陷阱时长与递减；捕获阈值 30%；口水硬 Clagger 300。
- COL 70 条攻击原记录（主 35+shell35）；342 ACTP2 记录/142 启用/4295 属性项。

| 编号 | 缺失项 | 类型 | 归属 |
| --- | --- | --- | --- |
| NUM-01 | 任务倍率（任务 HP/攻击/部位耐久/体型）未闭合；HP3000 不是任务实战 HP | 证据缺口 | E05/C0 |
| NUM-02 | 最终伤害公式（乘法顺序/上限/逐段取整）未闭合；COL Motion_Value≠实战扣血 | 证据缺口 | E05/C3 |
| NUM-03 | 肉质组号→部位名映射。**2026-11-03 进展：cross-verified 闭合**——本机 12 行 dtt_epg 肉质表与 monsterhunterwiki.org 的 MHWI 雌火龙逐行对照完全一致：行0=Head(70/75/65,气绝100)、行1=Neck、行2=Body、行3=Back、行4=Wings、行5=Legs、行6=Tail、行7~11=(MR)各部位变体（MR Wings 21/21/45 精确匹配）；7 组硬直=Head/Body/L翼/R翼/L脚/R脚/Tail。两独立来源互证，可升入忠实 profile（任务倍率仍是唯一缺口） | 已闭合（双源交叉验证） | E03 关闭 |
| NUM-04 | PBC 破坏耐久未解（2006/2007 语义未知；Sever 300 不是任务最终阈值） | 证据缺口 | E04/C4 |
| NUM-05 | Stun/Dizziness/Concussion 三套气绝语义未定，不得合并 | 证据缺口 | C5 |
| NUM-06 | 断尾后毒判定资格、闪光/陷阱免疫递增未取证 | 证据缺口 | C4/C5 |
| NUM-07 | 数值"分段可重放结算"只有方案（C3.1），无可执行原型 | **方案有、实现缺→本轮建原型** | PLAN-20261102-001 P3 |

## 四、动画与模型资源引用

已有证据（[动画库现状](../Systems/MHWI-Rathian-Animations.md)、LR 数据页 §5.2）：

- 848 条 AnimSequence（19 LMT/8 bank+_fs），逐条类/Skeleton/时长读回通过；旧 24 条时长已按源帧数修复（R-ANIM-011 fixed-readback）。
- 本体 `/Game/MHWI/Rathalos/Mesh/SK_EM001_Body`（142 骨/4 材质槽）+ 独立尾巴 `SK_EM001_Tail`（3 骨）；材质 4 个（BML+NM+EM、damage），12 贴图（4 张法线）；RMT 通道实测接入；眼睛外 Emissive 断开修复。
- 历史路径约定明确：保留 `/Game/MHWI/Rathalos/...`，新运行资源走 `/Game/MHWI/Rathian/...` 候选根。

| 编号 | 缺失项 | 类型 | 归属 |
| --- | --- | --- | --- |
| ANIM-01 | bank/slot→UE 资产语义映射表（source-motion-map）未生成；资格列全 unknown | **实现缺→本轮生成首版** | A0/PLAN-20261102-001 P4 |
| ANIM-02 | Rathian 专用 ABP/Montage/播放组件未建（当前零播放层资产） | 证据/实现缺口 | A3/M2 |
| ANIM-03 | 部位破坏/断尾网格映射（PBC→mesh section）未闭合 | 证据缺口 | E04/A2 |
| ANIM-04 | `_fs` 叠加层/常量轨/NeedsParent 语义未解；不单独当完整动作 | 证据缺口 | A1 |
| ANIM-05 | CMML 染色通道、FM 毛发 shader、LOD1/2 未做 | 证据/实现缺口 | A2 |
| ANIM-06 | 原作逐帧姿态对照未执行（视口验收由用户操作） | 待运行验证 | M6 |

## 五、音效与特效配置

已有证据：73 个外部 raw 文件（声音 8：WW 事件+`em001_{se,vo}.nbnk`；VFX 52：47 EFX+5 TEX；任务/区域 13），SHA256 复读一致（[精简证据](../../Tools/MHW/rathian-plan-evidence-20261031.json)）；方案步骤见 [A5](../Plans/PLAN-20261031-005-rathian-animation-assets.md)、工作包 [E08](../Plans/PLAN-20261031-003-rathian-evidence-pipeline.md)、总方案 M5.4。

| 编号 | 缺失项 | 类型 | 归属 |
| --- | --- | --- | --- |
| AV-01 | 73 个 raw 文件无只读清点：事件名候选、文件结构、共享依赖未知 | **实现缺→本轮清点** | PLAN-20261102-001 P2 |
| AV-02 | 源音画事件→动作/时刻→UE 资产映射表不存在（吼叫/脚步/吐息/尾击/受击等无一行映射） | **映射表骨架缺→本轮建** | A5/PLAN-20261102-001 P2 |
| AV-03 | Wwise NBNK 未解码；无固定解码工具候选（需用户选择后才能转 UE 音频） | 证据缺口 | E08 |
| AV-04 | EFX 格式语义未解码；47 EFX 未证明全为本体 LR 特效 | 证据缺口 | E08 |
| AV-05 | UE 侧零资产：无 SoundAsset/Niagara/衰减/附着配置（`/Game/MHWI/Rathian/Presentation` 未建） | 证据/实现缺口 | A5/M5 |
| AV-06 | 镜头震动/hit stop 的原作证据来源未取证 | 证据缺口 | A5.4/M5 |

Epic UE5.8 官方机制来源（音画适配可用，不证明原作行为）：[Niagara 概述](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/overview-of-niagara-effects-for-unreal-engine)、[创建视觉效果](https://dev.epicgames.com/documentation/unreal-engine/creating-visual-effects-in-niagara-for-unreal-engine)、[Niagara 音效模块](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/how-to-create-audio-effects-in-niagara-for-unreal-engine?application_version=5.3)、动画通知（见 PLAN-005 引用）。

## 六、文档记录完整性（本轮修复）

| 项 | 问题 | 处置 |
| --- | --- | --- |
| DOC-01 | 首链实施（1546 行 C+++3 脚本+链证据 JSON）无 CHG | 补 [CHG-20261031-003](../Changes/CHG-20261031-003-rathian-first-chain.md)（补录，静态核对） |
| DOC-02 | Plans 索引缺 PLAN-20261031-007 行 | 已补 |
| DOC-03 | modules.json 未登记 `Source/IntroCpp/MHWI/Monsters/` 入口 | 已补（登记为已存在源码入口，验证状态如实标注） |
| DOC-04 | `MHWI-Rathian-Datamine-Handoff.md` 标题"雌雌火龙"笔误 | 已修 |
| DOC-05 | 本核对页与音画细案、并行实施方案无归属 | 新增 [PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md) 并更新索引 |

## 七、边界声明

- 本页所有"已有"结论均引用既有证据文件，本轮未重跑解析/导入/PIE；"缺失"指截至 2026-11-02 静态核对时点。
- 音画映射表、数值原型、动画映射首版为**工程产物**，不提升任何原作语义状态；unknown 保持 unknown。
- 构建结果、子代理产出与本轮实际执行见 [PLAN-20261102-001](../Plans/PLAN-20261102-001-rathian-completeness-parallel.md) 与 [CHG-20261102-001](../Changes/CHG-20261102-001-rathian-completeness-parallel.md)。
