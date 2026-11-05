# CHG-20261030-011：火龙ACTP2/COL攻击字段读取与PBC嵌套证据

- 状态：completed（本批离线读取）；完整原作机制 partial。
- 日期：2026-10-30。
- 需求摘要：核查火龙未解项交接，能解决的范围实际推进并记录。
- 关联：[PLAN-004](../Plans/PLAN-20261030-004-mhwi-rathian-format-evidence.md)、模块mhwi-unpack-data、R-DATA-003；前序CHG-009/010保持历史。
- Git：工作区变更，未提交。

## 原因与结果

原交接以“ACTP2无公开结构”“SHLP无伤害→只能从ACTP2取数值”为阻塞，把4份PBC的48字节周期当作通用步长。维护者模板、项目已缓存DTI与固定原生代码给出了更直接的证据。

按[格式续查](../Reference/MHWI-Rathian-Format-Evidence-20261030.md)的直接来源/固定版本实现独立离线入口：ACTP2完整解析205037B且独立重编码一致；42份COL读取70条Atk2原字段/日文名称；PBC类CRC精确匹配，并由加载/保存链确认三层嵌套与载荷对象归属。更正“首条+24为2006”与“全00即下位表”等不成立前提。

官方/维护者资料支持：Fexty模板cea17f2…、Synthlight col.bt b6ff379…、Andoryuuta历史DTI 4a124e4…；它们不是Capcom运行机制规范。项目证据为本机原字节/hash、独立往返与固定代码指令；动作名变换、未解释字段业务含义和完整运行表现分别标候选/未知。部位破坏耐久未解，尚未定新业务推断路线。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/read_action_params.py` | 带类型Property读取/独立编码/指纹与边界检查 | 解除ACTP2结构阻塞；同源Property包装适配单独记录，上游不改 |
| `Scripts/MHWI/read_monster_collision.py` | Names→CLND/CLGM→Atk2 | 70条具名攻击原字段可读，几何/OAP保留opaque |
| `Scripts/MHWI/inspect_parts_break.py`、`inspect_parts_break_native.py` | 4样本类CRC/raw、固定加载/保存链 | 证明对象类型/嵌套与字段归属，未知耐久不命名 |
| `Tools/MHW/rathalos-{actp2,collision,pbc}-sources.json` | 来源commit/尺寸/hash及样本范围 | 可追溯、来源变化拒绝；缓存保持原文 |
| `Tools/MHW/em001-{actp2,collision,pbc}-evidence.json`、`em001-pbc-native-layout-evidence.json`、`em001-pbc-rea-identity.json` | 读取结果/校验/原生指令及REA实际身份记录 | 紧凑证据随仓库；完整ACTP2/COL报告在Saved可重建 |
| `Tools/MHW/em001-datamine-manifest.json` | decode及format_evidence | 只更新当前状态，不改300条路径/尺寸/hash |
| `Tools/MHW/Licenses/Fexty-MHW-010-MIT.txt` | 原作者MIT声明 | 保留新适配使用的模板许可 |
| `Docs/Reference/MHWI-Rathian-Format-Evidence-20261030.md` | 新增当前结果/35条主攻击原表/来源/候选 | 本批主体证据与后续缺口 |
| `Docs/Plans/MHWI-Rathian-Datamine-Handoff.md`、`PLAN-20261030-003-mhwi-rathian-datamine.md`、`PLAN-20261030-004-mhwi-rathian-format-evidence.md` | 当前交接/原方案/本批方案 | 清除已否决前提，按真实状态交接 |
| `Docs/Reference/MHWI-Rathian-LR-Data-20261030.md`、`MHWI-Unpacking-Workflow.md`、`Docs/Systems/MHWI-Unpack-Data.md` | 当前读取范围与入口 | 与新工具一致；补既有pins/零尾判据的现状说明，未改通用解析器 |
| `Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md`、`Docs/Reference/modules.json`、`Docs/Known-Issues.md`、`Tools/MHW/README.md` | 索引/模块sources/R-DATA-003 | 对齐项目文档结构 |

## 接口、事件与资源影响

无C++/反射/蓝图/Content变更，不启动游戏/UE，不重新解包、不改原始资源。独立CLI只写其报告，既有parse_em_params.py/read_collision未改。用户原有MHWI代码、资产、布局校验和采集批次保持；分类清单仅改状态、当前文档仅更新相关段落。旧CHG-005~010正文未改。

ACTP2/PBC会重写各自输出报告，COL拒绝不同内容报告；需要历史时指定新输出路径。完整输出在Saved忽略，工具缓存亦忽略；换机需依来源指纹恢复。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `python Scripts/MHWI/read_action_params.py --self-check` | 本机Python，离线 | 205037B完整消费/独立往返；342动作、142启用、4295属性；7项自检通过 | Tools/MHW/em001-actp2-evidence.json及Saved完整报告 |
| `python Scripts/MHWI/read_monster_collision.py` | 同上，固定模板/42源文件 | 42源hash/尺寸及读取后保护一致，36有ATK/6无ATK、70攻击；8项边界检查通过，OAP语义保留未解 | Tools/MHW/em001-collision-evidence.json |
| `python Scripts/MHWI/inspect_parts_break.py --self-check` | 同上，4样本/历史DTI | 4文件20条、3类CRC一致，每样本6项拒绝通过 | Tools/MHW/em001-pbc-evidence.json |
| `python Scripts/MHWI/inspect_parts_break_native.py` | 固定EXE/text，复用NativeTrace | 6函数owned范围完整解码、24条关键指令与7字段映射通过；字段业务语义未闭合 | Tools/MHW/em001-pbc-native-layout-evidence.json |
| REA inspect_byte_entropy（PBC） | REA实际工具 | 256B及SHA与清单一致；仅文件身份，不用熵证明格式或加密 | Tools/MHW/em001-pbc-rea-identity.json |
| `python Scripts/Docs/check_docs.py` | 项目根目录 | PASS：165篇Markdown、1440个本地链接、13模块及快照JSON | 本轮工具输出 |
| `git diff --check` / 新文件空白检查 | 项目根目录 | Git检查exit0；仅既有.gitignore/memory有LF→CRLF提示。沙箱Git无法识别工作树，沙箱外只读执行通过；16个新文件逐行空白/末尾换行及JSON检查PASS | 本轮工具输出 |
| 分类与工具证据一致性 | 只读Python | 300条分类路径/尺寸/hash与原采集清单一致；ACTP2/PBC工具证据脚本hash与当前源码一致 | 本轮工具输出 |

未执行：原作运行、UE/PIE/编译、当前MOD覆盖验证、最终伤害/等级资格/完整时长验证；未重跑既有DTT参数解析。REA Ghidra未配置，不安装/改配置，原生指令证据来自项目已有固定读取器，不冒充REA深度引擎Evidence。

## 风险、遗留与回退

R-DATA-003仍partial：PBC载荷不是已确认耐久，00混含G級原名，动作CRC候选不等于注册/时钟语义。后续有来源候选与代价见结果页，用户选择前不定新的实质方向。

回退删除本轮新增脚本/来源/证据/文档，定点撤销相关现状段落/索引和分类decode字段；不整体git restore覆盖用户已有工作，不删除原始资源/其他Saved批次。玩法与资产未改，无资源迁移。

## 已同步文档

[结果](../Reference/MHWI-Rathian-Format-Evidence-20261030.md)、[交接](../Plans/MHWI-Rathian-Datamine-Handoff.md)、[火龙现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)、[原方案](../Plans/PLAN-20261030-003-mhwi-rathian-datamine.md)、[本批方案](../Plans/PLAN-20261030-004-mhwi-rathian-format-evidence.md)、[流程](../Reference/MHWI-Unpacking-Workflow.md)、[管理](../Systems/MHWI-Unpack-Data.md)、[工具](../../Tools/MHW/README.md)、[模块索引](../Reference/modules.json)、[问题](../Known-Issues.md)、[总入口](../README.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)。
