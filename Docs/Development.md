# 开发、验证与提交前检查

## 构建入口

[IntroCpp.Target.cs](../Source/IntroCpp.Target.cs) 为 Game，[IntroCppEditor.Target.cs](../Source/IntroCppEditor.Target.cs) 为 Editor；均为 UE5.8 include order 与 V7 build settings。本机引擎为 `E:/UE/UE_5.8`，路径不是仓库对所有开发者的通用要求。

编辑器 C++ 构建：

```powershell
& 'E:/UE/UE_5.8/Engine/Build/BatchFiles/Build.bat' `
  IntroCppEditor Win64 Development `
  '-Project=E:/Unreal Projects/IntorCpp/IntroCpp.uproject' `
  -WaitMutex -NoHotReloadFromIDE
```

改 UCLASS/USTRUCT/UPROPERTY/UFUNCTION、Target、Build.cs 或插件时，优先关闭使用本项目的编辑器后完整构建，避免仅靠 Live Coding 判定兼容。若编辑器中有待保存资源，先辨明用户工作再安排关闭。新增依赖在项目 Build.cs 声明，不依赖编辑器插件偶然带来的链接符号。

## 按变更选择验证

| 变更 | 最小合理验证 |
| --- | --- |
| 仅 Markdown / JSON / 文档工具 | 文档检查、脚本语法、diff 检查；不重新编译项目 |
| 普通 C++ 逻辑 | 相关 Target 编译及对应功能运行检查 |
| 反射签名、父类、控件名 | 完整编译、受影响蓝图编译、引用及数据迁移核对 |
| 物品/拖拽/数量/装备 | 满包、超重、部分堆叠、仅快捷栏、最后一件、交换/整理、丢弃失败等针对性检查 |
| 动画/连击/敌人 | 实际动作、通知次数、受击、打断、切武器、死亡、场景退出；仅启动冒烟不覆盖这些边界 |
| UE/插件/工具连接 | 完整编译、真实编辑器启动、MCP 握手与项目身份、读回实际状态 |

记录每条验证的命令、实际结果、环境和日志路径；未执行写“未执行”及原因，超时写“结果未确认”。不要把计划中的验证、旧日志或编译通过当作全部玩法通过。

## 现有验证工具

- [ue58_smoke.py](../Scripts/Tests/ue58_smoke.py)：真实编辑器启动后分别让 Lvl_Start 与 MyLevel PIE 运行约 10 秒，结果在 Saved/Upgrade-UE58/EditorSmoke.json。它不自动穷举战斗、背包或 AI。
- [test-ue-mcp.mjs](../Scripts/Tests/test-ue-mcp.mjs)：编辑器已打开时执行 `node Scripts/Tests/test-ue-mcp.mjs`，验证 MCP 初始化、工具列表、项目/PID、插件新旧、场景 Actor 列表。结果在 Saved/Upgrade-UE58/McpSmoke.json。
- [check_docs.py](../Scripts/Docs/check_docs.py)：运行 `python Scripts/Docs/check_docs.py` 检查本文档集的本地文件链接、模块索引及接口 ID。它不验证蓝图内容或 C++ ABI，也不检查 Markdown 标题锚点。
- `IntroCpp.Actions` 原生自动化：通过 MCP `editor.run_automation_tests` 使用 `filter:"IntroCpp.Actions"`；当前10项覆盖许可、通知身份、旧执行/段、缺提交、死亡重入、333ms帧输入窗口和库存提交。临时原生世界测试不等同于真实Montage播放。
- [action_refactor_pie.py](../Scripts/Tests/action_refactor_pie.py)：2026-10-19资产基线的MyLevel真实PIE脚本，覆盖当日四段6命中、施法、喝药、中断、取消和死亡；结果为 `Saved/ActionRefactor-20261019/PIE.json`。2026-10-20 [Ninja替换](Systems/Ninja-Animation-Configuration.md) 已改变命中数量、窗口及提交时刻，该脚本的旧固定时序需先适配后才能用于新资产，不能将历史结果视为当前通过。Ninja 替换当时用户禁止完工后验证，未执行此旧脚本；2026-10-22 用户取消了限制，MHWI 使用独立脚本。正常编辑器内通过MCP执行后保持打开；命令行 `-ExecutePythonScript` 可能在结束后自动退出。
- [AgentSkills](../Tools/AgentSkills/README.md)：保存项目专用上下文路由、UE 日志切片及 6 个 UE 5.8 技能的精简路由源文件。活动副本位于 `.agents/skills/`；完整第三方参考仅在具体 API 不确定时读取。

PIE 的已验证启动命令见 [升级记录](UE58-Upgrade.md)。MCP 安装、依赖恢复、项目级 Codex 设置见 [工具说明](../Tools/ue-mcp/README.md)；连接端口/PID 是运行时数据，以 port.json 和 get_status 为准，不能把历史 PID 写成配置。

- [MHWI 冒烟](../Scripts/MHWI/pie_smoke.py)与[连段回归](../Scripts/MHWI/pie_moveset.py)：仅针对 `/Game/MHWI/Maps/L_MHWI_Training` 的独立新角色；使用 `editor.run_python_file` 启动后等待 Slate 回调完成，以 `Saved/MHWIImport/PIE-*.json` 的 passed 判定结果，工具启动成功不代表测试通过。
- [MHWI当前行为回归](../Scripts/MHWI/pie_behavior_corrections.py)：`run(suite='all')` 顺序执行ground/direction/air/lifecycle，或单独指定其中一个。正式DA/成本不改为预览值；覆盖气刃插入、普通B/A交替（B01已去除项目自定B无限循环）、翻滚出口、17种袈裟输入（含同帧按下/松开）、转向、登龙七段/自然落地/过早落地/高落差、中断/死亡和缓冲边界。以 `PIE-behavior-<suite>.json` 的passed和时间戳判定。编辑器最小化会被UE强制降到约3 FPS，即使关闭普通后台节流也一样；构造提交前落地的夹具可能因此无法采样，须区分夹具失败与业务失败。旧pie_moveset.py的自动登龙整段串联假设已过时，不能原样作为本轮回归依据。
- [MHWI原始基础数据校验](../Scripts/MHWI/verify_reference_basics.py)：直接重读固定指纹COL/W03P/FSM，75条攻击记录逐字段重编码并核对已确认映射；不启动原作。[原版基础专项PIE](../Scripts/MHWI/pie_reference_basics.py)的`run()`验证真实命中/回槽、派生正反例、四色居合首击和三色登龙；`run(scope='step')`用生产动作构造0→23→8→20槽边界。期望来自原文件及独立固定基准，不从正式DA反生成；不验证尚未还原的几何、shell起算、精确取消帧和完整伤害公式。
- [B02短冒烟](../Scripts/MHWI/pie_spirit_branches.py)：`run()`仅验证弱18/强28及费用、A/B插入、原序III/I和自定B负例，本轮约18秒。不默认重跑全套。B01原报告中的低槽拒绝属于历史适配；当前边界夹具已改为低槽弱斩允许，不能复用旧拒绝预期。

## 文档/源码约定

新增文档 UTF-8；已有源码/历史文档存在混合编码，编辑前读取确认，不因查看乱码就批量重编码整个目录。C++ 编辑保留 Unreal 反射、generated.h 顺序和命名约定。

角色/Widget/动态委托的回调维持 UFUNCTION 与参数签名一致；原生委托 AddUObject 和动态委托 AddDynamic 不是同一种蓝图暴露方式。需要持续持有 UObject 时检查 UPROPERTY/TObjectPtr/弱引用边界；这里是新增代码约定，不表示现有裸指针已全部整改。

不要为文档检查顺手保存、迁移或修复全部资产。原有用户修改与本次变更在记录中区分；资源实际被修改时写清完整路径与原因。

## 完成时交付

运行必要验证 → 更新现状文档/接口/已知问题/索引 → 新增变更记录 → `python Scripts/Docs/check_docs.py` → `git diff --check` → 汇报改了什么、验证了什么、仍有哪些未确认项。用户未要求时不自动提交或发布。

- [B03动画定向迁移](../Scripts/MHWI/author_locomotion_fidelity.py)：`run(save=False)`只预检，`run(save=True)`备份并迁移已合格循环；源清单变化须重新资格核对。配套[短PIE](../Scripts/MHWI/pie_locomotion_fidelity.py)只测真实移动/站姿、速度和有限姿态，不涵盖原作逐帧对照。

- [B04连接原值校验](../Scripts/MHWI/verify_connector_source.py)：`python Scripts/MHWI/verify_connector_source.py`，固定MBD/FSM/LMT、全字节往返、损坏/歧义拒绝、32引用和349资产哈希保护。`before-assets.json`为本批基线，后续资产修改后不能直接把此旧保护报告当当前通过；逐条进度见[连接台账](Plans/MHWI-Connector-Progress.md)。本批未新增连接，未执行PIE。

## 历史验收安排（2026-10-26；B20已获调试授权）

该历史批次用户要求验收开发台账，运行调试由用户操作。本轮只做静态审查、离线源/快照基准与文档/diff检查；不启动编辑器、不编译或运行PIE/自动化。结果与用户操作清单见[验收报告](Reference/MHWI-Acceptance-20261026.md)。下文的“不测试”是B06当时批次安排，不能覆盖当前要求。

## B06之后的历史验证安排

当时用户明确要求不测试；该历史阶段不运行编译、PIE、语法、文档或diff检查。每项交付状态与[通过准则](Plans/MHWI-Connector-Acceptance.md)，测试留下一阶段。B04校验脚本固定2冲突/旧输出预期已过时；先迁移再运行，禁止使用旧报告代替新结果。[原生逻辑汇总入口](../Scripts/MHWI/native_connector_logic.py)是只读原文件取证，不代表执行原生消费者或测试通过。

B06[链式函数读取器](../Scripts/MHWI/trace_native_connections.py)只提取固定来源静态字节，通用门控及参数元数据不等同武器规则；工具也待验证。具体地址、候选排除和下一步见[控制现状](Reference/MHWI-Native-Connector-Control.md)。

## B12台账处置工具（2026-10-26）

- [audit_ledger_sources.py](../Scripts/MHWI/audit_ledger_sources.py)：只读导出固定指纹的59条近战、16条shell、90个FSM节点及307条件树，保留记录/字段偏移；不启动UE，不代表玩法通过。
- [author_b12_ledger_sweep.py](../Scripts/MHWI/author_b12_ledger_sweep.py)：正式DA的登龙空中126首击与居合适配位写入；`run(save=False)`预览、`save=True`备份/保存/读回，带幂等和全字段保护。编辑器驱动为`Saved/MHWIRestoration/B12-20261026/b12_author_driver.py`。
- [verify_native_baseline.py](../Scripts/MHWI/verify_native_baseline.py)：51项静态基准，重读COL/shell/W03P/FSM并核对DA快照；`python Scripts/MHWI/verify_native_baseline.py --da Saved/MHWIRestoration/B12-20261026/authored.json`。非PIE，不覆盖行为矩阵。

## B20定向动画开发与调试（2026-10-27）

用户已授权实际调试。`Scripts/MHWI/author_remaining_animation.py`提供合格六段导入/CDO绑定及`verify_assets/finalize`实际读回；四链图配置见`Tools/MHW/b20-animation-graph.json`。`pie_remaining_animation.py`验证生产移动、翻滚出口、IK实际骨骼和门控；`pie_r06_impact_matrix.py`验证两种姿态S/M/L到Light/Spirit。它们异步运行，以Saved/MHWIRestoration/B20-20261027报告passed和时间戳判定；不能并行占用同一个PIE世界。多视角截图冻结不算动作时序测试，瞬态Profile/地形夹具不保存正式资产。详见[B20报告](Reference/MHWI-B20-Animation-Development-20261027.md)。
