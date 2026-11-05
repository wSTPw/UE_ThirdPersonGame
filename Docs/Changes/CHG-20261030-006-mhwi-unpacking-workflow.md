# CHG-20261030-006：整理现有解包方式与复现流程

- 状态：completed（文档）。
- 日期：2026-10-30。
- 需求摘要：总结现有解包方式，并适配现有文档结构。
- 关联：沿用模块 `mhwi-unpack-data`；工具边界 `R-DATA-001/002`；此前数据管理 [CHG-004](CHG-20261030-004-mhwi-unpack-data-doc.md)、火龙数据 [CHG-005](CHG-20261030-005-mhwi-rathalos-datamine.md)。
- Git：工作区变更，未提交。

## 原因与结果

已有系统页集中统计，工具 README 保存素材命令，参数及消费者证据分散在专项页。新增 Reference 流程说明，将归档定向提取、素材转换、动画采样、太刀/怪物参数读取及消费者取证的输入/产物/完成条件串联起来；保留数据管理页职责和历史记录，不新增解包工具或实质技术方向。

先查询工具维护者资料：JodoZT/MHWNoChunk 的 Chunk.cs（项目缓存 2026-10-22 master snapshot）、Feuleur 1.3.9 发布页、wowo-dot v1.1.0 能力说明、Synthlight/MHW-Editor（项目固定 b6ff379b13079a4abb99490590fb05dfe6851bbc）。直接链接及适用范围见[流程来源表](../Reference/MHWI-Unpacking-Workflow.md)。固定 W03P 页面本轮抓取失败，未把抓取失败写成核实成功；项目版本依据来自既有指纹清单和解析器。工具维护者定义不充当 Capcom 原作机制证明。

项目证据来自现有脚本、清单及本地原始文件；未新增游戏行为推断。特别澄清：只索引 kind=0 文件、数字排序同路径覆盖、Oodle 与资源级 Blowfish 分层、清单重写/中途失败不回滚、怪物解析跳过/部分 data 不能证明成功。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Docs/Reference/MHWI-Unpacking-Workflow.md` | 新增方法总览、版本来源、复现命令及失败处理 | 当前方法集中可读；明确参考命令本轮未执行 |
| `Docs/Systems/MHWI-Unpack-Data.md` | 索引范围、太刀三批口径、清单失败边界及流程链接 | 对齐脚本；另列火龙批次，避免将太刀比例当全项目比例 |
| `Docs/README.md`、`Tools/MHW/README.md` | 新增流程入口 | 适配快速阅读与工具说明 |
| `Docs/Reference/modules.json` | mhwi-unpack-data.sources | 增补流程、解析入口与版本指纹，保留现有 module/document |
| `Docs/Known-Issues.md` | R-DATA-001/002 | 记录清单/非事务写入和解析成功判定边界，未实现修复 |
| `Docs/Changes/README.md`、`Docs/Changes/CHG-20261030-006-mhwi-unpacking-workflow.md` | 本条记录/索引 | 新增记录；修复 004/003 粘在同一表格行 |

## 接口、事件与资源影响

无 C++/反射/蓝图、UE 资产、脚本行为或配置变化。只修改上表文档/文档索引；不改游戏、提取产物、工具缓存、`.gitignore` 或玩法。原工作区已有 MHWI 代码、资产、004/005 文档及火龙采集变更，本轮在既有文档上仅补流程链接/说明，保留其他修改。未改历史 CHG-004/005 正文。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 只读 Python：按三个 extraction-manifest 逐项比对文件尺寸和 hashlib.sha256 | 项目根目录，本机 Python | 太刀素材 140/140（52,004,942 B）、太刀参数 48/48（242,071 B）、火龙 300/300（80,708,036 B）一致，无缺失/不匹配；为批次记录计数，不是去重总量 | 三批 `ArtSource/ThirdParty/*/extraction-manifest.json`；本轮工具输出 |
| `python Scripts/Docs/check_docs.py` | 项目根目录 | PASS：157 篇 Markdown、1,357 个本地链接、13 个模块及编辑器快照 JSON | 本轮工具输出 |
| `git diff --check` | 项目根目录 | 通过（exit 0）；既有 .gitignore / memory 仅有 LF→CRLF 提示。沙箱内 Git 访问工作树失败，改为沙箱外只读执行通过 | 本轮工具输出 |
| `git diff --no-index --check -- NUL <新增文档>`（流程页、CHG-006 各一次） | 项目根目录 | 两次输出仅 LF→CRLF 提示，无空白错误条目（no-index 返回 1）；另用只读 Python 对两篇逐行检查尾随空白及文件末尾换行，均 PASS | 本轮工具输出 |

未执行：重新提取/从 chunk 比对原始内容、参数解密/解析、Blender 转换、EXE 分析、C++ 编译、UE/游戏/PIE。此轮仅文档归纳与本地文件完整性复核；既有 B17、参数及火龙解析结果仅引用历史记录。完整性复核不证明清单未经同步篡改或原作消费者语义正确。

## 风险、遗留与回退

工具缓存与部分结果位于忽略目录，换机不能只靠源码重建；固定路径、游戏更新、上游版本变化需要重新核对。R-DATA-001/002 仍为静态发现，本文补现有操作边界，不修改脚本、不采用新解析方案。

回退仅移除新增流程页、本条与索引行，并撤回本轮对入口、系统页、模块 sources 和 R-DATA-001/002 的增补；保留用户原有修改及 004/005 历史。玩法代码/资源及原始数据未改，无需恢复资产；不要整文件 git restore 覆盖其他工作。

## 已同步文档

- [解包方式与复现流程](../Reference/MHWI-Unpacking-Workflow.md)
- [解包数据管理](../Systems/MHWI-Unpack-Data.md)
- [技术文档入口](../README.md)
- [采集工具说明](../../Tools/MHW/README.md)
- [模块索引](../Reference/modules.json)
- [已知问题](../Known-Issues.md)
- [记录索引](README.md)
