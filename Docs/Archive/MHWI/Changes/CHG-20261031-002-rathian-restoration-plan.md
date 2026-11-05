# CHG-20261031-002：雌火龙总体/子代理细案与外部资源补取

- 状态：completed-scope；方案与隔离原始资料交付，玩法未实施，技术候选待选择。
- 日期：2026-10-31。
- 需求摘要：提出总体还原方案，派子代理写细化步骤，汇总流程；缺资料时可指挥子代理解包。
- 关联 PLAN / 问题：PLAN-20261031-002至006；R-DATA-001/002/003/004、R-AI-001/002。
- Git：工作区变更，未提交。

## 原因与结果

现有雌火龙具备模型、19库848动作及部分参数/格式证据，但原作AI、动作窗口、部位/耐久与任务倍率尚未闭合。此次三个子代理分别承担数据/解包、AI/世界、动画/战斗，交付四份细案；主代理汇总总方案、依赖、共同契约及验收流程，并统一ActionRunId等身份命名、子时钟边界、已发射投射物独立生命周期和表现失败不得回滚已提交伤害等跨包约束。

目标取项目既有MHWI普通em001/00，首个验收配置为下位单人；更高难度及MHWI交互能力单列依赖。AI编排/移动/时钟/碰撞/数据候选均未选定，本轮没有创建运行类、蓝图或DataAsset。

原始300文件本轮300/300尺寸/SHA256复核一致。复用已有归档索引，在新Saved批次定向补取73文件、16,446,967 B（15.69 MiB）：音频8/14,779,047 B、VFX52/1,628,162 B、任务/区域13/39,758 B。73/73复读通过；提取后原300文件和13归档尺寸/mtime再次核对一致，未计算整归档内容SHA。

新资料仍为raw；同名路径只建立候选关联，不证明LR资格、任务倍率、完整音画依赖或可直接用于UE。原资源、复制的索引及manifest留本机Saved，精简证据JSON可纳入版本管理。

## 官方资料、版本与证据边界

- **官方结论，UE5.8**：[StateTree](https://dev.epicgames.com/documentation/unreal-engine/overview-of-state-tree-in-unreal-engine?lang=en-US)、[Data Assets](https://dev.epicgames.com/documentation/unreal-engine/data-assets-in-unreal-engine?application_version=5.8)、[Traces](https://dev.epicgames.com/documentation/unreal-engine/traces-with-raycasts-in-unreal-engine)、[Automation](https://dev.epicgames.com/documentation/en-us/unreal-engine/automation-test-framework-in-unreal-engine)支持编排、承载、查询与验证；不证明MHWI行为，也不要求选择特定架构。
- **维护者直接来源**：[MHWNoChunk Chunk.cs](https://github.com/JodoZT/MHWNoChunk/blob/master/MHWNoChunk/Chunk.cs)支持项目既有定向提取实现；本地固定快照/tool/Oodle指纹见JSON。未修改第三方工具与插件。
- **项目事实**：读取真实Source入口、Build.cs及玩家SweepWindow/延迟shell直扣血流程；资产依据磁盘/脚本/历史报告。本轮MCP为editorConnected=false，未重新读回实时CDO/资产。
- **项目推断/方案**：拟议类型、动作/状态所有权、未来资产根和D1–D5候选尚未冻结。THK语义、原生消费者、部位映射、PBC耐久、完整伤害公式和时长仍unknown。

## 修改清单

以下以项目根为路径前缀；原始输出目录包含本轮manifest列出的73资源及本轮索引缓存。

| 文件/资产完整定位 | 符号或内容 | 原因与效果 |
| --- | --- | --- |
| `Docs/Plans/PLAN-20261031-002-rathian-restoration-master.md` | M0–M6、G0–G5、L0–L4、D1–D5 | 总体、分工、选择门和集成验收 |
| `Docs/Plans/PLAN-20261031-003-rathian-evidence-pipeline.md` | E01–E09、实际命令 | 来源、解包及语义闭合细案 |
| `Docs/Plans/PLAN-20261031-004-rathian-ai-world.md` | AI-00–AI-12 | AI/地空/状态/狩猎细案 |
| `Docs/Plans/PLAN-20261031-005-rathian-animation-assets.md` | A0–A5 | 骨骼/时间/位移/动画/破损/音画细案 |
| `Docs/Plans/PLAN-20261031-006-rathian-combat-integration.md` | C0–C6 | 双向命中/肉质/异常/部位/太刀桥接细案 |
| `Tools/MHW/rathian-plan-evidence-20261031.json` | 来源/offset/hash/tool/command | 可携带精简证据，不含游戏素材 |
| `Saved/MHWI-Rathian-20261031-PlanEvidence/` | 73原资源、manifest、复制的archive-index | 本机隔离批次，Saved忽略 |
| `Docs/Systems/MHWI-Unpack-Data.md` | 2026-10-31补充 | 区分旧统计与新批次 |
| `Docs/Known-Issues.md` | R-DATA-004 | 登记AI/动作/部位关联及外部依赖缺口 |
| `Docs/Reference/modules.json` | mhwi-unpack-data.sources | 增加实际精简证据入口 |
| `Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md` | 导航入口 | 总方案、四细案及本轮记录 |

## 接口、事件与资源影响

无运行接口、反射字段、事件、蓝图或正式配置变化；未写Source、Content或游戏安装。未来接口/蓝图路径仅作拟议，NBNK/EFX未转换为UE资源。

开始时工作区已有大量修改，包括MHWICharacter.cpp、DA_MHWI_LongSword.uasset、L_MHWI_Training.umap及文档索引/证据。本次只对表中现状/索引作增量编辑，保留原有内容；不将完整git diff归为本次产生。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| git status --short | 本机PowerShell，项目根 | 已读初始/交付中状态；沙箱git受限后用require_escalated只读查询成功 | 工具输出 |
| 300文件尺寸/SHA、13包stamps | 子代理，本机离线 | 提取前后300/300一致，13包尺寸/mtime一致；非整包SHA | [精简证据](../../Tools/MHW/rathian-plan-evidence-20261031.json) |
| extract_resources.py --pattern … --max-mb 32 | 既有适配器、本机Oodle | 73文件/16,446,967 B，完整命令在003和JSON | 新Saved批次及JSON |
| 73文件/manifest独立复读 | 主代理只读Python，另有子代理复核 | 73唯一path、尺寸/SHA全部一致，manifest尺寸/hash一致，正则匹配73条 | 主代理输出/JSON |
| MCP/REA状态 | 子代理只读 | MCP未连编辑器；REA无打开目标、Ghidra未配置，未执行消费者反编译 | 子代理输出/JSON |
| python Scripts/Docs/check_docs.py | 全部文件落地后 | PASS：187 Markdown、1566本地链接、14模块及快照JSON；仅文件引用/清单验证 | 本次工具输出 |
| git diff --check / 新增行尾检查 | 全部文件落地后 | git diff退出0，仅LF/CRLF提示；新增5 PLAN+CHG+JSON另查行尾/JSON。初检发现003/004缺末尾换行，已补齐并复查 | 本次工具输出 |

未执行C++构建、PIE、动画重导入、音频/VFX语义解码、THK反编译、原作启动或运行对照：本轮为方案及隔离raw交付，未改玩法。历史测试只作参考；Ghidra缺配置不代表语义永不可解。

## 风险、遗留与回退

THK/thklst、动作/窗口、骨骼/肉质、PBC耐久及任务倍率/公式仍开放；R-DATA-004已登记，R-DATA-003不因补取raw而关闭。架构选择在具体候选与代价可审阅后由用户决定，当前未实施。

回退本次新增5份PLAN、CHG、JSON及索引/现状/模块sources中本次加入内容。Saved批次可保留；若移除须先验证绝对目标仅为该隔离目录，再单独处理，不清理旧素材/游戏。用户既有未提交文件不能整体回退。

## 已同步文档

[总体及子方案入口](../Plans/PLAN-20261031-002-rathian-restoration-master.md)、[首页](../README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)、[解包现状](../Systems/MHWI-Unpack-Data.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)。
