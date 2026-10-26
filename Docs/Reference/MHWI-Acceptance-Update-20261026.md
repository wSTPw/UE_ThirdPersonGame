# MHWI 更新验收：B13/B14/B15（2026-10-26）

审查时结论：**更新已有实际进展，整体验收不通过。** B13初始证据重建、B15键盘静态检查通过，既有日志支持当前源码编译成功；B14正式DA仍未迁移，登龙单次接触也没有排满七段。后续B16修复结果见文末；本页仍不宣称运行验收通过。

审查基线为提交`c09f24872b745294f46b09e721cfc56197f37083`，开始时工作区干净；检查`4b5361c`的B14/B15实现及后续编译修复。历史[首次验收](MHWI-Acceptance-20261026.md)保留当时结论，本页更新其当前状态和运行预期。对应[本轮记录](../Changes/CHG-20261026-008-mhwi-update-acceptance.md)。

## 交付裁决

| 更新 | 可接收范围 | 尚不能接收 |
| --- | --- | --- |
| B13取证 | 默认重建重新通过：18函数、113动作、18资源；续查19函数快照已在仓库 | 续查未纳入统一重建器；十项完整消费者仍有缺口，不能宣称取证完成 |
| B14机制 | 当前源码已有Q步进衰减、回旋命中锁存/退出提交、颜色暂停、居合延迟队列、回避帧倒计时 | 正式DA迁移缺失、登龙补排缺失；精确取消/资格/空间等原有边界仍开放 |
| B15键盘 | 键鼠与手柄Action/状态分离，PC组合使用新成员边沿；本轮49项静态/模型检查PASS | Enhanced Input实际投递、组合手感和动作回归未运行；手柄A02仍开放 |
| 编译修复 | `GetInputRequestSerial`改`int32`，`RemoveAt`使用`EAllowShrinking::No`；保留日志显示Succeeded、20.08秒 | 编译不证明DA已迁移或行为正确；本轮没有再次编译 |

35项状态继续为：**6项历史已验证、1项开发完成待运行、17项部分完成、10项取证中、1项待开发。** 十项为R07/R09/R10/R13/R18/R19/R20/R21/R29/R30；相关R16完整追加语义、R31真实hitstop仍缺证据。B14落地的是部分子链，不增加整项完成数。

## 阻止通过的问题

### A05 / P1：正式DA仍是B12字节，旧伤害窗与新队列并存

当前`Content/MHWI/Data/DA_MHWI_LongSword.uasset`的SHA256为`e09764d08042ca44d19d593373bb3f6c92bc7bc7811e8afd6834dc1fde34450c`，与B12 `authored.json`的保存后指纹完全一致。本轮未加载UE读取资产属性；以下字段依据相同字节对应的历史快照：

- `SpiritHelmBreaker`仍有COL#28、126 MV首击，`HitLagSeconds=0.4000000059604645`。
- `HelmLand`仍有七条直接伤害窗。
- `Saved/MHWIImport/EvidencedMechanics-20261026/authored.json`不存在，B14校验实际返回1，报告缺少保存快照。

`MHWICharacter.cpp:1272`已在下劈命中后排延迟伤害，`:1276`仍读取DA的HitLagSeconds；旧落地窗也仍由`AdvanceAction/SweepWindow`消费。因此旧0.4秒表现冻结未解除，合格命中后可能同时产生延迟伤害与落地七窗伤害。源码和迁移脚本已提交，不能据此宣布正式数据完成迁移。

修复后验收：先处理A06，再用`author_b14_evidenced_mechanics.run(save=False/True)`完成预览、备份、保存及读回；正式下劈hit lag为0，HelmLand无直接七窗，保存报告的磁盘指纹与当前DA一致。随后执行B14离线校验。迁移与运行由后续实施阶段安排，本轮只记录缺口。

### A06 / P1：登龙单目标一次接触只生成一段延迟伤害

`MHWICharacter.cpp:1247`按窗口去重目标，`:1272`对该目标调用一次`ScheduleHelmShell`。该函数`:1886–1894`只添加一个队列元素；`TickDelayedShells:1916–1922`只递减、弹出和结算，没有按前一目标继续补排。`HelmShellHitLimit=7`仅限制最多记录数，不生成七次命中。

对单窗口、单目标、一次合格接触，当前延迟队列最多发出一段；若仅迁移DA清掉旧落地七窗，缺段问题会直接暴露。B13局部消费者证据包含一次接触后继续填队列的行为，B14尚未实现这一环。多目标当前会竞争同一计数，完整原目标/部位选择仍需取证，不在本轮猜补。

修复后验收：一次合格接触在同一目标仍有效的条件下，按0.4秒首段、0.05秒间隔发出约定七段；空挥零段，低帧不丢已到期段，落地不重复结算，目标失效安全退出。目标销毁、死亡及普通派生边界分别记录，不把项目安全策略当原版取消证据。

### 既有问题及记录缺口

| 项目 | 当前复核结论 |
| --- | --- |
| A01 / P1 受击恢复锁 | `RequestNativeSourceInput`仍被`IsGestureLocked`拒绝；R06继续部分完成 |
| A02 / P2 旧组合重发 | 手柄`ResolveFrameInputEdges`仍以Held判组合；B15只修键盘子项 |
| A03 / P2 设备混用 | 键盘有独立Action、Held、Edges与解析器；静态修复可接收，运行待验 |
| A04 / P1 菜单缓存 | `SetInputBlocked:541–550`仍未清NativeSourceInput；内部来源提交及移动/视角阻断仍开放 |
| B14记录 | CHG-20261026-005仍缺失，方案与索引未完整同步；本轮不伪造当时迁移/运行结果 |
| R32版本化 | 当前Tools/MHW 26、Scripts/MHWI 114、Docs 116、Content/MHWI 409个跟踪文件；首次验收的四目录0文件已过时。确定性重建/资产语义和行为覆盖仍未完成 |

R11颜色暂停在当前C++已恢复，R-COMBAT-017改为部分修复待验证；不能再将B13“玩法未改”的批次描述当作当前源码状态。R-COMBAT-018在本页首次验收时受A05阻塞，B16静态修复见文末。Q衰减已存在，但原owner资格、技能和双回槽时钟等完整边界仍开放。

## 本轮实际验证

证据目录为`Saved/MHWIRestoration/Acceptance-Update-20261026`，源/DA指纹及跟踪数量见[离线记录](../../Saved/MHWIRestoration/Acceptance-Update-20261026/offline-evidence.json)。

| 检查 | 结果与边界 |
| --- | --- |
| `python -B Scripts/MHWI/build_outstanding_evidence.py` | PASS：18函数/113动作/18资源；只验证初始B13字节及提取一致性 |
| `verify_keyboard_adaptation.main()` | PASS：49项；仅将报告路径重定向到本轮目录，未改断言/期望；不证明UE事件投递 |
| `python -B Scripts/MHWI/verify_evidenced_mechanics.py --da Saved/MHWIImport/EvidencedMechanics-20261026/authored.json` | FAIL：已检查12项来源值，缺B14保存报告；不以B12快照冒充B14通过 |
| 历史UBT日志 | 本轮只读并复制；北京时间2026-10-26 19:21:39开始，Succeeded，20.08秒；未再编译 |

文档/diff检查结果记录在本轮CHG。未执行游戏、UE、PIE、运行自动化、资产加载/保存、蓝图父类与实例检查。原B13/首次验收与B15的历史结果均保留范围，不改写成此次运行。

## 用户运行验收的更新

A05/A06的静态修复已在B16完成，执行相关玩法验收前仍需用户运行。原报告U06的“0.4秒表现冻结”和U07的“不额外+10秒”预期被B13证据更正；本页覆盖这两条旧预期。

| 范围 | 当前应检查 |
| --- | --- |
| 登龙 | 126首击之后，从接触起0.4+0.05n秒结算七段；下劈不再使用0.4表现冻结；落地不重复结算；测试空挥/目标失效/中断/低帧 |
| 回旋/Q/颜色 | 空挥不清Q，合格命中锁存后退出仅提交一次；升色并刷新余量、颜色暂停赋值10秒；Q自然衰减与回槽独立检查。精确bit30提交帧仍未接入 |
| 居合/回避 | 有色居合接触后0.5秒追加一次、退出取消；普通回避13帧基础计时及训练技能/衣装选表；完整伤害资格仍单列 |
| PC输入 | LMB/RMB/Ctrl及四种组合，按住组合后按无关键，预设开关与设备隔离，E/Shift姿态过滤；使用B15真实输入脚本，记录请求次数与最终动作 |
| 受击/菜单 | 仍按A01/A04复验；键盘使用当前Ctrl组合，不再沿用旧R/F/G/Q/C直达快捷键 |

运行结果需带用例、输入顺序、配置/颜色/资源、时间点和通过/失败/未测。本轮未获得新的运行结果。

## B16实施复验（2026-10-26，后续）

以下只更新A05/A06的源码、资产和离线状态。上文A05/A06描述的是本页审查时的工作区事实，保留其历史意义。

| 项目 | B16结果 |
| --- | --- |
| A06 登龙补排 | `ScheduleHelmShell`现对一次合格接触按首延迟和间隔预排至`HelmShellHitLimit`；每条记录保存同一目标弱引用、目标相对接触点、颜色MV和倍率。低帧到期由原`TickDelayedShells`循环逐项处理。UE 5.8 Editor构建成功；未运行PIE，因此七段实际伤害/时序尚待用户验证。 |
| A05 正式DA | UE-MCP通过B14脚本预览、备份、保存和读回。`SpiritHelmBreaker`仍为COL#28/MV126，`HitLagSeconds=0`；`HelmLand.DamageWindows`从7条变为0。预览幂等、全字段保护通过；保存报告磁盘SHA256与当前`Content/MHWI/Data/DA_MHWI_LongSword.uasset`一致：`97a78f601a3f0aac7f83a82666779f4041d324f1812342ff3226bdc05ffc926a`。改前SHA为`e09764d08042ca44d19d593373bb3f6c92bc7bc7811e8afd6834dc1fde34450c`。 |
| 离线源/DA校验 | `python -B Scripts/MHWI/verify_evidenced_mechanics.py --da Saved/MHWIImport/EvidencedMechanics-20261026/authored.json`：PASS，22项；证据`Saved/MHWIRestoration/B14-20261026/offline-verification.json`。 |
| 完整构建 | UE 5.8 `IntroCppEditor Win64 Development`：Succeeded，`-NoUBA`，编辑器关闭后链接成功；日志`Saved/MHWIRestoration/B14-20261026/build-no-uba-closed.log`。编辑器已重新启动并保持打开。 |
| 未执行 | 未运行PIE、游戏、原作、运行自动化或蓝图行为矩阵。A01、手柄A02、A04及R19空间/取消/多目标等范围仍开放；35项总状态不变。 |

对应[CHG-20261026-005](../Changes/CHG-20261026-005-mhwi-evidenced-mechanics.md)。本次静态处理关闭A05资产缺口并实施A06补排，但不把它们扩写为原版时序/空间已运行验证。
