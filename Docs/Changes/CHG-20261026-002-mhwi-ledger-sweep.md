# CHG-20261026-002：B12 台账全量处置（35 项逐项裁决 + 可证据落地）

- 状态：partial（本轮覆盖的条目已实施/取证；多项因源数据或资产缺口保留开放）。
- 日期：2026-10-26。
- 执行与身份：**WorkBuddy 代理会话**（DeepSeek-V4.1-Flash），B12 批次。B01–B11 由其他会话完成；本批使用独立目录 `Saved/MHWIRestoration/B12-20261026/`，未改写他批证据。
- 需求摘要：按用户要求“处理开发台账中的全部条目，逐项完成并保持处理方式一致；可协调多个代理分工协助，确保每项都得到处理且结果完整汇总”。
- 关联：[总台账](../Plans/MHWI-Restoration-Progress.md)、[全量处置矩阵](../Reference/MHWI-Ledger-Disposition-20261026.md)、[33项审查](../Reference/MHWI-Restoration-Review.md)、[B11 记录](CHG-20261026-001-mhwi-foresight-exits.md)。
- Git：工作区变更，未提交；保留其他协作者与用户的既有修改。

## 原因与结果

台账 35 项分布在 S0–S7，状态混杂：6 项已验证、2 项开发完成未测试、7 项部分完成、12 项取证中、8 项待开发。若逐项“凭感觉补齐”，会重犯本项目已反复警告的错误（把外部说法当源值、把项目调适当原版、把未运行写通过）。因此本批采用统一协议：

1. 先用固定指纹复核原始 COL/W03P/FSM/LMT，并把条件树、记录偏移、shell 分组一次性导出；
2. 每个条目给出证据等级（确定/高置信/不足）、当前代码/资产落点、可否实施；
3. 只实施**一手证据充分且落点明确**的改动；证据不足的条目不写猜测值，改为明确缺口与下一步；
4. 资产改动走“预览→幂等→全字段保护→保存→读回→脏包清零”；代码改动后做一次增量编译，确认可构建；
5. 所有结论汇总到[全量处置矩阵](../Reference/MHWI-Ledger-Disposition-20261026.md)，不只写“做了什么”，也写“为什么没做”。

结果概览：6 项保持已验证；2 项开发完成（R04/R06，其中 R06 本轮编译通过但未运行）；16 项部分完成；10 项仍取证中；1 项待开发（R23，契约已设计未改接口）。

## 修改清单

### 代码

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h` | `FMHWIHitWindow.ColRecordIndex/HitLagSeconds`；`FMHWIRoute.ProjectAdaptation`；`EMHWIDamageStageStatus`；`FMHWIResolvedHit` | 为命中提供源记录身份、表现停顿和结构化结果；`Unavailable` 显式表示缺数据 |
| `Source/IntroCpp/MHWI/MHWICharacter.h` | `bOriginalInputPreset`、`SetInputBlocked`、`GetControlState`、`GetLastResolvedHit`、`OnHitResolved`、`EMHWIControlState`、`CommandReleased/ResolveFrameInputEdges` | 原版手柄组合、UI 输入门控、受击控制状态、命中事件与结果读取 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | 输入映射/手势解析、R05 适配路线跳过、R11 颜色 T 修正、R22 命中结构、R24 控制状态、R26 Falling 门控、R27 输入阻断、R31 hit lag/广播 | 见下表逐项；“FinalDamage”公式保持原值，除 R11 外不改资源经济 |
| `Source/IntroCpp/MHWI/MHWICharacterNativeSources.cpp` | `StartNativeImpact`、`RequestNativeSourceInput` | 受击 S/M/L 挂载时锁定输入并清缓存；受击结束由 `FinishMove` 回 Free |

### 资产

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | `SpiritHelmBreaker.damage_windows` | 新增 1 窗：0.4166667–1.8666667 s、MV 126、回槽 0、半径 35/前伸 200/侧向 65、`ColRecordIndex=28`、`HitLagSeconds=0.4`。来源为 COL #28「必殺(空中)」与 TIML 碰撞帧 25–112；七段 `HelmLand` 窗口不变 |
| 同上 | `IaiSpiritSlash.routes` | `SPIRIT→SpiritIII`、`SPECIAL_SHEATHE→SpecialSheathe` 标记 `ProjectAdaptation=true`；`HELM_BREAKER→SpiritThrust` 保持非适配（源 node65 唯一显式出口） |

### 脚本与证据

| 文件 | 作用 |
| --- | --- |
| `Scripts/MHWI/audit_ledger_sources.py`（新增） | 统一导出 59 近战/16 shell/90 FSM 节点、307 条件树、记录偏移；修正早期 dump 的 `mpLinkList` 键名与字段裁剪缺陷 |
| `Scripts/MHWI/author_b12_ledger_sweep.py`（新增） | 资产改动的预览/幂等/全字段保护/备份/保存/读回 |
| `Saved/MHWIRestoration/B12-20261026/b12_author_driver.py`（新增） | 编辑器内驱动，`importlib.reload` 避免模块缓存 |
| `Scripts/MHWI/verify_native_baseline.py`（新增） | 51 项独立静态基准：源 COL/shell/W03P/FSM + DA 期望；不启动 UE |
| `Saved/MHWIRestoration/B12-20261026/evidence/` | 6 份只读取证报告 + `ledger-source-dump.json` + `w03p-fields.json` |

## 接口、事件与资源影响

- **新增反射**：`EMHWIDamageStageStatus`、`FMHWIResolvedHit`、`EMHWIControlState`、`FMHWIHitResolved` 委托、`OnHitResolved`、`GetLastResolvedHit`、`GetControlState`、`SetInputBlocked`、`IsInputBlocked`、`bOriginalInputPreset`。已做完整编译/UHT，未运行。
- **USTRUCT 扩展**：`FMHWIHitWindow` 新增两个字段、`FMHWIRoute` 新增一个 bool。DA 保存后旧资产自动获得默认值（`INDEX_NONE`/0/false）；蓝图读取路径不变。
- **行为变化（未验证）**：
  - R11：回旋升色不再把颜色 T 延长 10 s；白/黄/红恢复严格 195/135/60。
  - R15：登龙空中阶段新增 126 MV 首击；与 `HelmLand` 七段独立。
  - R24/R26/R27：受击/空中/UI 阻断会拒绝或清空输入。
  - R31：仅 `SpiritHelmBreaker` 命中触发 0.4 s 表现冻结；槽/颜色计时不受影响。
  - R01/R05：仅 `bOriginalInputPreset=true` 时生效；默认 `false`，键鼠快捷与现有手柄行为不变。
- **未改**：Montage、Sequence、BlendSpace、地图、蓝图、HUD、连接数据、`transition_calibration.json`、伤害公式的最终数值。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 增量编译 `IntroCppEditor Win64 Development` | 本机 UBT，编辑器关闭 | **Succeeded**，约 29.6 s；新增 UPROPERTY/USTRUCT/委托通过 UHT 与链接 | UBT 日志 `Saved/Logs/` / 控制台输出 |
| 资产预览 | UE-MCP 编辑器 Python | `saved=false`、`idempotent=true`、`protected_fields_unchanged=true`、新增 1 窗、标记 2 路由 | `B12/preview-response.json` |
| 正式保存与读回 | 同上 | `saved=true`；before/after 仅 `SpiritHelmBreaker` 与 `IaiSpiritSlash` 不同；路由总数 151 不变 | `B12/authored.json` |
| 新进程磁盘重载 | 关闭编辑器后重新启动，只读加载 | 32 招/151 路由；`SpiritHelmBreaker` 1 窗（126 MV/25–112 帧/COL #28/0.4）；`SPIRIT` 与 `SPECIAL_SHEATHE` 的 `project_adaptation=true`，`HELM_BREAKER=false` | `B12/disk-readback.json` |
| 磁盘与脏包 | 本机 + 桥接 | DA 119387→125300 字节；SHA `490ab87f…`→`e09764d0…`；`list_dirty_packages` content/maps 均为空 | `authored.json` |
| 独立静态基准 | 本机 Python，无 UE | 51 项 PASS：COL #6/#15/#17/#19/#18/#23/#24/#25/#28/#43/#44/#46–49、shell 三色/居合二击、W03P 关键字、FSM node65 单边、DA 126 窗口/居合适配位 | `verify_native_baseline.py` 输出 |
| 文档检查 | 本机 Python | `check_docs.py` PASS：106 个 Markdown、885 个本地链接、12 个模块 | 控制台输出 |
| 文本 diff 检查 | 本机 Git | `git diff --check -- Docs Scripts Source` 退出 0；全量 `git diff --check` 因本机未安装 `git-lfs` 无法读取 `.uasset`，不是空白错误 | 控制台输出 |
| 未执行 | — | PIE、自动化、真实输入/命中/受击/派生矩阵、动画姿态/根运动、音频/特效/相机、低帧/地形/多部位 | 无 |

**说明**：台账此前记录“本阶段不测试，编译也后置”。本批改动了 C++ 反射，若不做编译会留下不可构建风险，因此执行了一次增量编译；这**不是**行为验证，也不把任何条目写成“运行通过”。PIE 与行为矩阵仍按用户既有安排后置。

**编译过程如实记录**：首次链接因 UBA 报 `Access is denied` 后残留 0 字节的 `UnrealEditor-IntroCpp.lib`，触发 LNK1136/LNK1201；删除 0 字节 `.lib/.pdb` 后以 `-NoUBA` 重建成功。该失败是构建缓存/文件锁问题，不是源码错误；源码编译阶段在首次尝试中已通过。

## 风险、遗留与回退

- **最大风险**：新增 126 MV 首击会显著改变登龙总伤害（白/黄/红由 70/105/175 变为 196/231/301 的基值合计），且未做 PIE；若与当前平衡目标冲突，应先回退该窗口。来源证据是 COL #28 + TIML 25–112，不是猜测，但仍需运行确认命中时机/次数。
- **R11**：停止延长颜色 T 是确定映射纠正；但 Q 的自然衰减仍未实现，10 s 字段成为“保留未消费”。HUD 若显示 `GetSpiritDecayPauseRemaining`，会变为 0，UI 批次需同步。
- **R01/R08**：原版预设默认关闭；同帧手势解析已做，但全局仲裁、RT+A、跨帧窗口没有源证据。开启前必须 PIE 验证“单手势不双发”。
- **R24**：受击锁定只覆盖 S/M/L 站立受击；击飞/倒地/起身/死亡动画无资产，死亡仍停移动/禁碰撞。
- **R22/R31**：结构化结果与 hit lag 是契约/表现层最小增量；斩味/会心/部位/音频/特效/相机仍为 `Unavailable` 或缺资产。
- **R32 的仓库风险**：`Tools/MHW`、`Scripts/MHWI`、`Docs`、`Content/MHWI` 在 git 中 0 个跟踪文件；当前证据链只存在于工作区。建议尽快纳入版本控制，否则一次清理会丢失全部源材料与记录。
- **回退**：
  - 资产：恢复 `Saved/MHWIRestoration/B12-20261026/Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset`（保存前 119387 字节，SHA 前 16 位 `490ab87fcd7bb024`），或删除 `SpiritHelmBreaker` 新窗/清除两条 `ProjectAdaptation` 后重存。
  - 代码：回退本记录“修改清单”中的四个 Source 文件；新增字段均有默认值，回退资产后不会残留行为。
  - 不要重置整个工作区，不覆盖 B01–B11 与用户既有资产。

## 已同步文档

[全量处置矩阵](../Reference/MHWI-Ledger-Disposition-20261026.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)（当前批次、逐项状态、接续点、B12 小节）、[系统现状](../Systems/MHWI-LongSword.md)（登龙/气刃槽/输入/受击/hit lag）、[已知问题](../Known-Issues.md)（R-COMBAT-010）、[记录索引](README.md)、[开发流程](../Development.md)（新增脚本入口）。
