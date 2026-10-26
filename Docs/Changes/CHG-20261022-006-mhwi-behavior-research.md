# CHG-20261022-006：MHWI 太刀六项行为资料与实施方案

- 状态：completed（研究文档交付；六项玩法修改尚未实施）。
- 日期：2026-10-22。
- 需求摘要：按用户要求先收集 World/Iceborne 原版资料，再处理动画反置、登龙滞空、转向、气刃插入普攻、右键循环、翻滚后左键。
- 关联 PLAN / 问题 / 接口：PLAN-20261022-002；R-ANIM-005/006、R-COMBAT-007/008；MHWI-001/002/003/004。
- Git：工作区文档变更，未提交；本轮未修改此前已有的源码、配置或游戏资产。

## 原因与结果

不能只依赖此前推断的动画标签或测试通过数量。此次对照本机原版 FSM/LMT/武器参数、公开格式源码、作者操作指南及 UE 正式 Data/Montage，确认结构性差异，列出实施目标和可观察验收条件。

已确认 140 是见切轨迹、170 是登龙突刺轨迹，正式 Montage 引用反置；原始登龙空中状态按输入/着地转换；气刃一式可插突刺续二式、二式插上挑续三式；持刀翻滚有129连接到踏步斩。连续RMB循环是用户要求的项目快捷适配，原版FSM记录突刺到上挑用△。

只读解码原始参数文件，获得重力/时间倍率/初速度与登龙七段延迟字段。**原版精确转向角度、运动参数组到动作的调用对应和逐帧阶段时长尚未闭环**，文档明确保留缺口，未写成已还原。这些研究结论不等于本轮运行验证。

## 修改清单

| 文件/材料 | 变化及用途 |
| --- | --- |
| `Docs/Reference/MHWI-LongSword-Behavior-Research.md` | 六项证据表、原始节点/连接/事件、文件哈希、项目差异、原版与快捷适配边界、待标定项 |
| `Docs/Plans/PLAN-20261022-002-mhwi-longsword-behavior.md` | 单动作身份、插入续接、方向策略、分阶段空中运动、数据迁移、DSH实施分工、独立验收和回退方案 |
| `Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md` | 添加可检索入口 |
| `Docs/Systems/MHWI-LongSword.md`、`Docs/Known-Issues.md` | 标注实际问题仍未修复，保留旧验证的历史范围 |
| `Saved/MHWIImport/Research-20261022/` | 只读资料缓存：UE读回、源节点/条件/事件、解码参数及公开格式源码；不属于玩法实现 |

## 接口、事件与资源影响

本轮无运行接口、反射字段、输入配置、蓝图、关卡、DataAsset、Montage、Sequence 或插件变更。正式动作仍为29个定义。模块索引和接口签名未变，无新系统入口需迁移。

UE-MCP 连接正常，`project.get_status` 返回本工程5.8/live；`pluginStale=false`。读取资产和PIE状态不代表行为测试；发现用户已有PIE处于运行状态，本轮未停止或操控该会话。

当前属于方案/只读工程调查，依个人 DeepSeek CLI 分工技能无需启动实施代理；实际实施仍默认交 DSH，并由 Codex 独立验收。尚无本任务 DSH sessionId。

## 实际验证

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| 原版FSM与LMT只读调查 | 提取22节点、106条件、15片段；保留完整条件树而非仅标签 | `Saved/MHWIImport/Research-20261022/source-evidence.json` |
| 正式资产MCP读回 | 29定义，140/170错位、两条插入路由/循环/翻滚缺失、空中阶段时间与Flying配置均读回 | 同目录 `editor-readback.json` |
| 原版参数只读解码 | 标头W03有效；格式消费1572/1584字节，余12字节未解释；原始值及来源哈希保存 | 同目录 `wp03-params-decoded.json` |
| 本机UE5.8运动源码读取 | Falling只保留重力轴速度；零动画根速度仍会覆盖水平速度，补入方案 | `CharacterMovementComponent.cpp::ConstrainAnimRootMotionVelocity` |
| 文档链接/索引检查 | 通过：50份Markdown、374个本地链接、12个模块及编辑器快照JSON；仅检查引用有效性 | `python Scripts/Docs/check_docs.py` |
| 文本空白检查 | `git diff --check -- Docs`通过；本轮8份文档按原有LF/CRLF格式逐一复核，全部无空白诊断。no-index新增差异退出码1，聚合检查退出0 | `git -c core.autocrlf=false -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --no-index --check -- NUL <文件>` |

早期读取遇到默认GBK解码、单节点/列表形状不一致和大小写标头断言问题，已修正调查命令并重新得到上述缓存；没有修改原始文件。公开格式源码只读下载成功；视频逐帧画面未取得，官方手册403，故没有捏造视频测量或完整官方参数依据。

文本复核第一次关闭autocrlf后将原有CRLF的CR误报为行尾空白；随后显式声明cr-at-eol并重跑8份文档全部通过。未为消除诊断而重写旧文件的行尾格式。

本轮未构建、未新增/运行PIE验证、未保存资产，原因是用户要求先资料调查，且未改变玩法。先前测试仅见各自CHG，不当作本轮证据。

## 风险、遗留与回退

六项实际行为仍待实现。误用原始Y轴/时间倍率、连接片段重复根位移、无下劈授权却结算七段、瞬时无限转向是实施时需防止的具体风险。

只回退本轮新增研究/方案/记录及索引、问题标注即可；源缓存可保留作调查记录。无需回退游戏资产或停止当前PIE，不使用git reset/clean覆盖此前大量未提交内容。

## 已同步文档

[资料](../Reference/MHWI-LongSword-Behavior-Research.md)、[方案](../Plans/PLAN-20261022-002-mhwi-longsword-behavior.md)、[系统](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)、[总入口](../README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
