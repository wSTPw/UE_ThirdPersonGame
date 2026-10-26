# CHG-20261026-004：B13剩余原生消费者取证

- 状态：partial，已归档静态子链；十项取证缺口未全部关闭
- 日期：2026-10-26
- 需求摘要：继续未完成取证，原游戏路径由用户指定；运行调试由用户操作。
- 关联：PLAN-20261026-001；R07/R09/R10/R13/R18/R19/R20/R21/R29/R30，相关R11/R16/R31；新增R-COMBAT-017/018。
- Git：工作区变更，未提交。

## 原因与结果

既有W03P/COL数值及公开布局标签不能证明起算点、时钟或消费者。本批只读固定EXE和既有合格分析区，追踪原生注册、加载及消费者，选择性提取18份资源。已推进Q衰减、回旋接触提交、登龙/居合延迟队列、普通回避计时和特殊纳刀等待子链；十项总体继续取证中，不提升开发完成/运行验证统计。

消费者推翻B12两项依据：10秒字段刷新颜色衰减暂停，不能解释为Q抑制；登龙0.4秒用于接触后shell生成延迟，不能支持HelmStrike的0.4秒hit lag。当前文档已更正，正式玩法未修复。历史CHG未改写。

## 修改清单

| 文件/资产完整路径 | 符号或关键内容 | 原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/trace_outstanding_evidence.py` | `Evidence.function/actions` | 固定指纹、直接可达CFG、CHAININFO归属、显式未闭合间接分支；解析固定版本回避六分支，动作113项绑定 |
| `Scripts/MHWI/extract_outstanding_tables.py` | `decode` | 本地公开C#布局仅作文本；固定SHA、PLP版本/长度、界限及完整消费；未解释区域保留 |
| `Scripts/MHWI/build_outstanding_evidence.py` | `build/main` | 重读原生/资源并核对受版本控制的机器证据；默认比较，显式`--write`才覆盖 |
| `Tools/MHW/native-outstanding-evidence.json` | 18函数、所选动作回调、18资源指纹、PLP/W03P值、306头 | 防止证据只留在被忽略的Saved；保存字节定位、CFG摘要与缺口，不包含完整游戏文件 |
| `Docs/Reference/MHWI-Outstanding-Evidence-20261026.md` | 十项矩阵、字段映射/公式、重建条件、运行交接 | 分开静态确认、未闭合与实现状态，列明两项旧解释更正 |
| `Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Systems/MHWI-LongSword.md` | 当前接续点与相关条目 | 更新实际消费者及仍开放缺口，保留B12历史含义 |
| `Docs/Known-Issues.md` | R-COMBAT-017/018 | 记录颜色暂停与hit lag依据差异；A01–A04仍未修复 |
| `Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md`、`Docs/Reference/modules.json` | 检索入口 | 新报告、方案、CHG和工具可被接手者找到 |

## 接口、事件与资源影响

正式C++、反射、接口、输入、蓝图、DA、Montage和地图均未改，无迁移。原安装只读，未启动原生代码；离线输出为`Saved/MHWIRestoration/B13-20261026`。原已有`.workbuddy/memory/2026-10-26.md`修改未触碰。没有保存编辑器资产。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 原EXE/分析区固定SHA、注册与消费者提取 | 本机Windows，Python 3.13 | 源指纹相符；动作113项解析；只收直接可达路径，未知间接跳转保留gap | `Saved/MHWIRestoration/B13-20261026/source-pins.json`、`actions.json`、`fn-*.json` |
| `python Scripts/MHWI/extract_native_longsword_params.py --output Saved/MHWIRestoration/B13-20261026/native-parameters` | 同上 | passed，425字段、100公开标签，1572字节消费、12零尾；往返及源未变检查通过 | `Saved/MHWIRestoration/B13-20261026/native-parameters/longsword-native-parameters.json` |
| `extract_outstanding_tables.py --source <本批pl_param.plp> --schema <固定SHA本地PlPlayerParam.cs> --output <本批player-parameters.json>` | 同上；完整布局路径见提取输出 | 20688字节完整消费，539字段记录含3个未解释区段 | `Saved/MHWIRestoration/B13-20261026/player-parameters.json`、`.bin` |
| `python Scripts/MHWI/build_outstanding_evidence.py --write`后默认模式重读比较 | 同上 | passed：18函数、113动作、18资源；安装/分析区指纹固定、资源逐文件核对、数据和指令提取一致 | `Tools/MHW/native-outstanding-evidence.json` |
| 脚本语法、PLP重复提取、文档检查、diff检查 | 同上 | passed：3脚本语法；PLP重复输出SHA一致；文档111页/938链接/12模块；diff及新增文件空白检查通过；非运行验证 | `Saved/MHWIRestoration/B13-20261026/verification.json` |

未编译、未启动游戏/UE、未执行PIE、运行自动化或姿态/命中行为验证；用户负责运行调试。B12的51项静态PASS及历史编译不当作本批已执行。

## 风险、遗留与回退

R07/R09/R18/R20/R30核心消费者仍缺；R19取消、R21伤害侧、R29全局播放及相关技能/时钟边界未全部闭合。R11/R31正式实现差异已记录但未修。默认验证核对字节/提取一致性，不证明文字解释、完整函数调用图或实机行为。

重建依赖本地既有分析区、原安装、提取资源和固定SHA公开布局；不是仅靠仓库即可移机重建。资源归档索引新鲜度只核对13个chunk的大小/mtime，不宣称全归档SHA证明。

回退：删除本批新增脚本/机器证据/报告/方案/CHG，恢复本批所改现状文档和索引。改前文档备份及SHA位于`Saved/MHWIRestoration/B13-20261026/Backup/handoff`；此前初始备份也保留。不要恢复或删除用户已有修改。原安装与正式玩法未变，无资产回退。

## 已同步文档

[证据现状](../Reference/MHWI-Outstanding-Evidence-20261026.md)、[台账](../Plans/MHWI-Restoration-Progress.md)、[系统页](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)、[入口](../README.md)、[方案](../Plans/PLAN-20261026-001-mhwi-outstanding-evidence.md)、[方案索引](../Plans/README.md)、[模块索引](../Reference/modules.json)、[变更索引](README.md)。

## 用户要求额度前保存的续查

续查新增`Tools/MHW/native-outstanding-followup.json`（19个函数指令快照及发现）、`Tools/MHW/native-parts-layout.json`（固定公开C#来源SHA和字段声明）、`Scripts/MHWI/extract_native_parts.py`（太刀/部位肉质解析）。更新报告、台账、系统页和模块索引。原公开布局只读；新肉质资源来自原安装，只读提取至`resources-parts`，未覆盖初始18文件清单。

新增静态子链：R07缓存/执行双许可、R09的20行转向参数与消费者、R20一次性/持续消费及余额写入、R18的320武器记录/7部位/12肉质/1断尾、R30管理器加载入口。**先前输入对象e490/62090识别已更正为e480/62080**，按角色构造绑定核对，e490走声音参数。尚未完成全部取证；按用户“额度快没了，先把已完成部分保存”指令保存，不表示完整目标达成。

续查核验保存于`Saved/MHWIRestoration/B13-20261026/verification-followup.json`；初始18函数重建检查不覆盖新增19函数快照。没有运行游戏/UE/PIE或修改正式玩法，未提交Git。
