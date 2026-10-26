# CHG-20261026-009：MHWI台账离线取证收尾

- 状态：completed（PLAN-001离线静态取证范围）；台账十项保留“取证中”
- 日期：2026-10-26
- 需求摘要：复核MHWI逐项开发台账并完成其中全部离线取证工作；游戏路径由用户指定。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261026-001](../Plans/PLAN-20261026-001-mhwi-outstanding-evidence.md)、R07/R09/R10/R13/R18/R19/R20/R21/R29/R30、R16/R31边界
- Git：工作区变更，未提交

## 原因与结果

B13报告将十项原生证据保留为接续任务。本批针对指定安装重验EXE和归档资源，从原始chunk重取48项参数/资源并核对SHA，复解析太刀与部位表，复追19个续查函数快照；完成十项逐条证据矩阵，并单独识别 `nativePC` 覆盖。结论仅为离线静态取证收尾，不代表十项行为已完整还原或运行通过。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Docs/Reference/MHWI-Forensic-Completion-20261026.md` | B17来源、复验、R07/R09/R10/R13/R18/R19/R20/R21/R29/R30及R16/R31边界 | 新增完成报告；注明归档原件、本地覆盖、静态事实、推论与未闭合项 |
| `Docs/Plans/MHWI-Restoration-Progress.md` | 当前接续点及十条台账行 | 接上B17结果；保留未闭合项和原状态 |
| `Docs/Plans/PLAN-20261026-001-mhwi-outstanding-evidence.md` | 本批结果/状态 | 标记离线静态工作完成，运行及语义边界仍开放 |
| `Docs/Plans/README.md`、`Docs/Systems/MHWI-LongSword.md`、`Docs/README.md` | 方案索引、太刀现状、技术入口 | 链接B17报告并说明当前安装覆盖 |
| `Docs/Changes/README.md` | CHG索引 | 登记本条变更记录 |
| `Scripts/MHWI/verify_outstanding_followup.py` | 固定版本19个续查函数快照复验 | 新增只读、可重跑的静态比对器，写入本机Saved证据；不执行游戏代码 |
| `Saved/MHWIRestoration/B17-20261026/` | 本机忽略的分析产物 | 保存48资源指纹、19函数复验及24资源提取清单；未写入游戏目录，不纳入版本控制 |

## 接口、事件与资源影响

无玩法接口、事件、配置或正式资源修改。新增的`Scripts/MHWI/verify_outstanding_followup.py`只读取固定分析源和快照，并把比较结果写入本机Saved目录；未改游戏代码、蓝图/DataAsset或安装文件。已存在的工作区修改在本批前后保留；现状文档只改本记录列出的段落。游戏 `nativePC` 有5项清单内覆盖，报告将其与归档原件分开记录。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 原安装EXE及资源复核 | 用户指定MHWI安装，只读 | EXE SHA与固定分析源匹配；48/48资源归档SHA匹配，找到5项当前覆盖 | 本机 `Saved/MHWIRestoration/B17-20261026/native-parameter-fingerprint-verification.json` |
| `python Scripts/MHWI/build_outstanding_evidence.py` | 固定版本本机分析区 | PASS：18函数、113动作、18资源 | `Tools/MHW/native-outstanding-evidence.json` |
| `python Scripts/MHWI/verify_outstanding_followup.py` | 固定版本本机分析区 | PASS：19/19函数入口、范围、可达指令、缺口及分支摘要匹配 | 本机 `followup-function-revalidation.json` |
| `python Scripts/MHWI/extract_native_parts.py` | 仓库固定解析器 | 320武器行、7映射、12肉质、1断尾；1351字节解析、9字节零尾保留 | `Tools/MHW/native-parts-layout.json`、B13本机输出 |
| `python Scripts/MHWI/extract_native_longsword_params.py --output Saved/MHWIRestoration/B17-20261026/native-parameters` | 仓库固定布局/本机Node | 425字段、100标签、1572字节解析、12零尾；解密往返与源未改检查通过 | 本机 `native-parameters/` |
| `python Scripts/Docs/check_docs.py` | 仓库文档 | PASS：120个Markdown文件、1027个本地链接、12个模块和编辑器快照JSON | 全仓文档 |
| `git diff --check` | 仓库工作区 | 默认调用被本机Git LFS过滤进程的Windows命名对象权限错误打断；以`git -c filter.lfs.process= -c filter.lfs.required=false diff --check`重跑，PASS、无空白错误；未改Git配置 | 全仓工作区 |

未执行构建、自动化、UE、原游戏或PIE，因为本批只做只读静态取证；运行行为由用户操作。历史测试不当成本次结果。

## 风险、遗留与回退

R07逐FSM输入位绑定、R09逐动作角度行绑定、R10/R13资格和时序边界、R18坐标变换/肉质消费者、R19取消/目标失效/shell下游、R20完整资格与倍率、R21伤害类型判定、R29播放保持链、R30求解坐标和装配矩阵未闭合；相应运行记录由用户补充。SHLP覆盖格式差异未解码。台账状态保持不变。仅文档变更，无玩法回退；如需撤销，删除本CHG及新增报告，并只移除关联文档中的B17新增段落，保留其他已有工作区修改。

## 已同步文档

[开发台账](../Plans/MHWI-Restoration-Progress.md)、[方案](../Plans/PLAN-20261026-001-mhwi-outstanding-evidence.md)、[方案索引](../Plans/README.md)、[太刀现状](../Systems/MHWI-LongSword.md)、[技术入口](../README.md)、[变更索引](README.md)、[B17取证报告](../Reference/MHWI-Forensic-Completion-20261026.md)。
