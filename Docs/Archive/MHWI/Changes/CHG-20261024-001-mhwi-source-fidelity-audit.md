# CHG-20261024-001：MHWI 武器轨道、原生时序与还原差距调查

- 状态：completed（调查与方案阶段；完整原作还原未实施）
- 日期：2026-10-23 开始，2026-10-24 继续完成
- 需求摘要：用户报告部分动作武器位置仍异常，希望从原作解包查武器动画及逐招取消/输入/衔接时机，以完整还原原作为目标。
- 关联：[PLAN-20261023-001](../Plans/PLAN-20261023-001-mhwi-source-fidelity.md)；mhwi-longsword；R-ANIM-007..009、R-COMBAT-009。
- Git：工作区变更，未提交。沿用已有MHWI及大量其他未提交变更，未覆盖无关资产。

## 原因与结果

本轮先调查底层数据，新增完整读取/独立核对/逐动作对照工具。已确认：原武器独立动画未接入，现有固定挂接未消费原武器事件；大部分原生连接片段缺失；原生输入标志的确切含义尚未解码；变速与骨压缩采样存在差异。完整证据、原始事件及后续实施步骤见[源保真调查](../Reference/MHWI-Source-Fidelity-Audit.md)。

本轮未修正正式武器位置，未重导出动画，未修改 C++/Content/第三方导入器。不能将调查通过写成原作动作已经还原。

## 修改清单

| 路径 | 符号/内容 | 原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/audit_native_timing.py` | parse_lmt/audit/raw_bit_intervals | 完整读取TIML/FSM，保留关键帧类型/控制/插值/hash/原序，标注bit区间仅为前值保持假设 |
| `Scripts/MHWI/verify_native_timing.py` | verify/action_table | 独立LMT偏移校验；原序FSM/条件对照；接入正式32招快照与30节点连接覆盖 |
| `Scripts/MHWI/audit_weapon_fidelity.py` | 两种只读审计模式 | 10份LMT/508动作、模型function映射、旧解码器与参考sampler、CMS未知字段、保护文件哈希 |
| `Scripts/MHWI/read_fidelity_assets.py` | run | UE正式DA32定义、Montage段、武器CDO读回；完整导出避免专用getter截断 |
| `Scripts/MHWI/build_fidelity_report.py` | 离线报告生成 | 输出逐动作JSON索引、可查看全部TIML/FSM/正式配置的独立HTML及24招对照表 |
| `Docs/Reference/MHWI-Source-Fidelity-Audit.md`、PLAN | 源事实、未知项、分阶段方案 | 后续AI不再按碰撞末帧+2猜取消帧；不将武器局部骨误当整件装配 |
| 系统页、入口/索引、Known-Issues、modules.json | 当前范围/审计入口 | 区分历史行为通过与原版保真未完成 |

临时审计脚本及上游源码缓存保存在 `Saved/MHWIImport/SourceFidelity-20261023/`；新稳定入口与本轮报告保存在Scripts和24日目录。原工具未安装/更新；没有修改游戏 nativePC。

## 主要确认事实

- LMT95：464槽中164有效动作，19类、1358组、5014轨、8727关键帧。旧五类筛选实际保留404组、遗漏954组。
- FSM：90节点、307条有序连接和307棵条件树；30个LinkMotion节点共32次MotionNo/Phase1引用，正式Montage段仅出现129，其余31次引用不在正式段中。不是31个不同动作的断言，也不表示它们都该无条件触发。
- 武器：8份LMT中4份有效、26动作；wg03_00主要驱动内部骨2的手柄区域。正式武器/刀鞘AnimClass=None，仍为固定父骨+Transform；源mWeaponMotionNo有拔/纳/居合等中途事件。家族映射、装备装配与交接规则待进一步确认。
- 排除项：猎人247..254存在且抽样20动作有曲线，无缺失目标骨；508动作无重复bone+usage，未发现重复轨道覆盖。不能据此宣称所有采样/IK都准确。
- 解码：参考sampler与旧导入器的数值规则存在差异，129/function48最高约18.7998°、173/function30约175.8053°。它们是特定源轨道key采样差异；尚未证实UE皮肤误差、整刀错位根因或替换后的视觉改善。function不是MOD3数组序号，已排除旧rename解剖标签误导。
- 未解码：全部961个输入key的transition=5，bit区间仅按前值保持生成候选；mAttackAdjustAngleIndex是索引；码2工具标签QUAD不等于本轮已证明原生`t*t`。不得将这些转换为精确取消/角度常数。

## 接口、事件与资源影响

公开玩法接口、蓝图引用、Montage和反射结构无变更。只读审计JSON记录schema/status/hash/单位与未知语义，非运行时数据源。完整逐输入路由窗口、LinkMotion调度、源曲线、装备事件消费均为后续方案。

## 实际验证

| 检查/命令 | 实际结果 | 证据 |
| --- | --- | --- |
| `python Scripts/MHWI/audit_native_timing.py --output Saved/MHWIImport/SourceFidelity-20261024` | 成功保留全部源事件/条件，新增区间假设标签 | `timing-native-full.json`、`timing-summary.json` |
| `python Scripts/MHWI/verify_native_timing.py --audit Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json` | 16481条结构/资产比较，0错误；不是16481个玩法场景 | `timing-verification.json` |
| Blender便携Python运行武器审计 | 10文件508动作；71个保护文件前后SHA256一致 | `weapon-fidelity-summary.json`、`weapon-decoder-*.json` |
| Blender后台只读已保存blend | 20动作曲线/辅助骨/蒙皮核对，blend前后哈希一致 | `weapon-blender-audit.json` |
| MCP专用getter及只读Python逐项读回 | DA32、单段来源/范围/速度端点与映射一致；武器AnimClass=None；首次完整Moves getter被截断，转逐项脚本成功 | `editor-readback.json`，带磁盘资产哈希 |
| 编辑器启动/状态 | 初始未运行；用项目内DDC覆盖启动PID35216，ready后只读核对。未启PIE；没有保存资产；dirty packages为0。核对完成后通过bridge正常退出，恢复初始关闭状态 | `Saved/Logs/IntroCpp.log`、MCP读回 |
| 报告生成/DOM检查 | 164动作、32定义、90节点渲染/搜索通过；33正式片段。Edge后台本地打开截图，已检查报告首页显示 | `fidelity-report-validation.json`、`fidelity-report-preview.png` |
| AST/JSON/新增文件空白 | 5个Python AST、JSON成功；14个本轮脚本/文档/索引逐文件no-index空白检查通过 | `final-validation.json` |
| 文档检查 | 61 Markdown、423本地链接、12模块通过；只查文件/索引，不验证标题锚点/玩法 | `python Scripts/Docs/check_docs.py` |
| Git差异空白 | 初次默认git diff触发git-lfs filter-process的MSYS权限错误；用单次`-c filter.lfs.process= -c filter.lfs.required=false -c filter.lfs.clean= -c filter.lfs.smudge=`禁用过滤后`diff --check`通过，未修改Git配置 | 退出0；仅既有文件LF/CRLF提示 |

上次执行受账户额度/自动审批服务额度影响中断；24日续接后MCP只读导出成功，已不构成本轮阻塞。一次公开GitHub API索引请求返回403 rate limit，格式核对改用本地已缓存上游源码，不影响源文件审计。

编辑器启动日志出现13条`LogAutomationTest: Error: Condition failed`及UnifiedErrorTest输出；编辑器后续ready且资产读回成功。用日志排查技能保留首次16条匹配和上下文，发生在Engine初始化之前、没有MHWI用例名；本轮未进一步证明每条的具体生成原因，不将其记录为MHWI测试失败，也不宣称启动日志零错误。没有运行新的原作控制实验、UE行为PIE、C++构建，也没有将10月23日行为回归算作本轮验证。

## 风险、遗留与回退

完整原作还原仍有源采样、原生窗口/连接规则、装备放置和相机/停帧/技能/特效等缺口。用户指定的单键RMB循环继续明确作为项目适配。源字段/社区命名不能直接作为原生行为证明。

回退仅撤回本轮新增审计脚本、生成报告与文档/索引条目；对旧脚本同名修改按本轮差异恢复。不要删除整个MHWI目录，不要恢复覆盖用户其他资产。Saved中的第三方缓存和源证据按需保留，没有必须回滚的玩法/二进制资产变更。

## 已同步文档

[调查页](../Reference/MHWI-Source-Fidelity-Audit.md)、[方案](../Plans/PLAN-20261023-001-mhwi-source-fidelity.md)、[方案索引](../Plans/README.md)、[系统现状](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[文档入口](../README.md)、[记录索引](README.md)。
