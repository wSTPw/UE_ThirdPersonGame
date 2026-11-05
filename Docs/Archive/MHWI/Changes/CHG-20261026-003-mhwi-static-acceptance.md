# CHG-20261026-003：MHWI台账静态验收与运行交接

- 状态：completed（静态验收与文档交接完成；玩法问题未修复，整体完成验收不通过）。
- 日期：2026-10-26。
- 需求摘要：验收目前MHWI开发台账进度，运行调试由用户操作。
- 关联：R01/R06/R08/R24/R27/R32/R33；R-COMBAT-014/015/016；MHWI-012/013；[验收报告](../Reference/MHWI-Acceptance-20261026.md)。
- Git：工作区变更，未提交；保留原有源码/配置/资产及未跟踪文件。

## 原因与结果

B12记录了35项处置，但部分状态没有覆盖新代码对旧入口的影响。本次对照当前源码发现：受击全程锁阻断B10真实来源恢复、按住旧组合后无关边沿重发组合、开启手柄预设改变键鼠组合、菜单阻断遗漏原生来源缓存。均为静态发现，未运行复现、未修复。

R06从开发完成降为部分完成；当前统计为6项历史已验证、1项开发完成、17项部分完成、10项取证中、1项待开发。B12历史矩阵和已完成CHG保留原义。仅完成本次审查交付，不宣称原版还原或运行验收通过。

## 修改清单

| 文件/资产完整路径（仓库相对） | 符号或内容 | 影响 |
| --- | --- | --- |
| `Docs/Reference/MHWI-Acceptance-20261026.md` | 35项状态、A01–A04、U01–U09 | 新增验收结论、证据与用户运行步骤 |
| `Docs/Plans/MHWI-Restoration-Progress.md` | R06及R01/R08/R24/R27 | 更新当前裁决，保留批次历史统计 |
| `Docs/Plans/MHWI-Connector-Progress.md`、同名`.csv` | 32引用状态 | 同步B12历史编译；N53-P0/N60-P0/N60-P1重开，node86继续不可达 |
| `Docs/README.md`、`Docs/Systems/MHWI-LongSword.md` | 当前入口/输入与控制边界 | 避免把B10开发完成或键鼠不变当当前事实 |
| `Docs/Interfaces.md`、`Docs/Known-Issues.md` | MHWI-012/013，R-COMBAT-014/015/016 | 记录静态回归与接口未闭合项 |
| `Docs/Development.md`、`Docs/Changes/README.md` | 验证安排/记录索引 | 明确本轮离线审查，用户操作运行调试 |
| `Saved/MHWIRestoration/Acceptance-20261026/` | 文档备份、源哈希、离线结果、历史编译摘要 | 本轮证据独立存放，不覆盖B12证据 |

## 接口、事件与资源影响

无C++、反射签名、事件、配置或资产修改。只修正文档对现有行为的描述。未连接编辑器读取当前蓝图父类/属性；正式DA通过磁盘SHA256与B12历史保存报告关联，资产内部值仍标历史读回。模块入口未变化，不修改modules.json。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 现有`verify_native_baseline.main()`，传B12`authored.json` | 本机Python；W03P输出定向至本轮目录，断言未改 | 51项PASS，425字段重读；非行为测试 | `Saved/MHWIRestoration/Acceptance-20261026/baseline.txt` |
| DA SHA256、连接CSV唯一ID、B10新增包存在性 | 本机文件读取 | DA与B12一致；32引用无重复；32新增包无缺失；不证明骨架/父类属性正确 | 同目录`offline-evidence.json` |
| 读取UBT历史Log.txt首尾 | 只读日志 | 2026-10-26 01:40:09开始，Succeeded/29.62秒；本轮未编译 | 同目录`historical-build.txt` |
| `git ls-files`逐目录统计 | 本机Git | Tools/MHW、Scripts/MHWI、Docs、Content/MHWI均0跟踪文件 | 同目录`offline-evidence.json` |
| `python Scripts/Docs/check_docs.py`、`git diff --check`与本轮文档独立检查 | 本机 | 文档PASS（108篇/911链接/12模块）；原始diff因git-lfs/MSYS启动失败；仅该命令禁用LFS过滤器后diff退出0。Docs未跟踪，另核对本轮11文档新增行、35项统计、32行MD/CSV及源码/DA哈希均PASS | 同目录`validation.txt` |

未执行：编译、PIE、UE自动化、编辑器/MCP资产加载或保存、输入/命中/姿态/低帧运行矩阵。按用户要求由用户操作运行调试，交接用例均标待执行。

## 风险、遗留与回退

四项静态问题仍在当前代码中，须开发修复并运行验证；51项离线PASS不能关闭它们。六项历史已验证没有本次回归证据。关键材料尚未纳入Git，不自动暂存/提交。

回退仅恢复本轮9个既有文档在`Saved/MHWIRestoration/Acceptance-20261026/Backup/Docs/`中的备份（修改前哈希见`before-docs.json`），移除新增验收报告和本记录。不要回退源码或正式资产，不重置整个工作区。

## 已同步文档

[总台账](../Plans/MHWI-Restoration-Progress.md)、[连接台账](../Plans/MHWI-Connector-Progress.md)、[验收报告](../Reference/MHWI-Acceptance-20261026.md)、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[已知问题](../Known-Issues.md)、[开发流程](../Development.md)、[入口](../README.md)、[记录索引](README.md)。
