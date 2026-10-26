# CHG-20261026-005：B14机制实施、登龙七段补排与正式DA迁移

- 状态：partial（A05/A06静态交付完成；未运行PIE）
- 日期：2026-10-26
- 需求摘要：按MHWI台账接续点修复A06登龙单次接触缺少后续shell段，并完成A05正式DA迁移、保存和读回。
- 关联：PLAN-20261026-002；R19/R31；R-COMBAT-018/019；MHWI-005。
- Git：工作区变更，未提交。B14其余机制代码已在基线`4b5361c`；本记录补齐缺失的B14记录并记录本批A05/A06收尾。

## 原因与结果

B14已有延迟shell队列，但一次合格下劈接触只加入一个元素，`HelmShellHitLimit=7`未产生剩余六段。同时正式`DA_MHWI_LongSword`仍保留B12的下劈0.4秒表现冻结和`HelmLand`七条直接伤害窗，与延迟队列并存。B16让一次接触预排至多七段，随后通过B14白名单迁移保存正式DA。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | `AMHWICharacter::ScheduleHelmShell` | 一次合格接触按首延迟、间隔和上限预排整组段；各段固定弱目标、目标相对接触点、颜色MV、伤害倍率和段序号。已有`TickDelayedShells`在低帧下排空全部到期段。 |
| `Scripts/MHWI/author_b14_evidenced_mechanics.py` | UE-MCP Python导入 | 将脚本自身目录加入`sys.path`，使`run_python_file`入口能解析同目录制作/校验模块；不改变迁移白名单。 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` (`Content/MHWI/Data/DA_MHWI_LongSword.uasset`) | `SpiritHelmBreaker.damage_windows[0].hit_lag_seconds`；`HelmLand.damage_windows` | 保留COL#28/MV126首击，将HitLagSeconds设0；移除旧七条落地伤害窗，避免与shell队列双重结算。改前SHA256 `e09764d08042ca44d19d593373bb3f6c92bc7bc7811e8afd6834dc1fde34450c`；改后 `97a78f601a3f0aac7f83a82666779f4041d324f1812342ff3226bdc05ffc926a`。 |
| `Docs/Systems/MHWI-LongSword.md`、`Docs/Interfaces.md`、`Docs/Known-Issues.md`、`Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Reference/MHWI-Acceptance-Update-20261026.md`、`Docs/README.md`、`Docs/Reference/modules.json`及索引 | 当前B14/A05/A06状态 | 记录实际资产、接口返回和验证状态；保留B13/B14/B15验收原结论作为历史。 |

## 接口、事件与资源影响

没有新增反射签名。一次合格登龙接触后，`GetPendingHelmShellCount()`立即显示预排的待发段数；各条按`HelmShellFirstDelay + index * HelmShellInterval`到期。目标仍为弱引用，接触点仍按目标相对变换复原；目标销毁/死亡安全略过，角色死亡/EndPlay清理队列，普通派生不撤销已提交队列。正式DA已迁移并保存。本工作区开始时的验收文档修改和CHG-008保持独立；未覆盖或回退它们。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| UE-MCP `author_b14_evidenced_mechanics.run(save=False)` | UE 5.8 Editor | PASS；`old_land_window_count=7`，幂等、全字段保护通过；预览未改变资产SHA。 | `Saved/MHWIImport/EvidencedMechanics-20261026/preview.json` |
| UE-MCP `author_b14_evidenced_mechanics.run(save=True)` | UE 5.8 Editor | PASS；成功备份、保存和对象读回；COL#28/MV126保留、HitLagSeconds=0、HelmLand窗口数=0。 | `Saved/MHWIImport/EvidencedMechanics-20261026/authored.json`、`Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset` |
| `& 'E:/UE/UE_5.8/Engine/Build/BatchFiles/Build.bat' IntroCppEditor Win64 Development '-Project=E:/Unreal Projects/IntorCpp/IntroCpp.uproject' -WaitMutex -NoHotReloadFromIDE -NoUBA` | UE 5.8 / VS2022，编辑器关闭 | Succeeded；C++对象和链接完成。初次UBA调用在“All processes queued”停滞，编辑器开启时链接被DLL占用；关闭编辑器后本命令成功。随后编辑器已重启用于DA保存。 | `Saved/MHWIRestoration/B14-20261026/build-no-uba-closed.log`；UE日志分诊SHA `48449537bc1ea1e9c28db44c7d423abd9914d56540a4e661f6e957f46e87330e` |
| `python -B Scripts/MHWI/verify_evidenced_mechanics.py --da Saved/MHWIImport/EvidencedMechanics-20261026/authored.json` | 本地Python及保存快照 | PASS，22项；当前磁盘SHA与保存报告的`disk_sha256_after`一致。 | `Saved/MHWIRestoration/B14-20261026/offline-verification.json` |
| `python -B Scripts/Docs/check_docs.py` | 本地Python | PASS：118份Markdown、1007条本地链接、12模块及Editor快照JSON。 | 输出在本轮工具记录 |
| `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` | 本地Git | PASS。常规调用曾被Git LFS子进程的Windows权限错误打断；禁用filter后对工作区diff完成同一空白检查。新增CHG独立尾随空白扫描也通过。 | 本轮工具记录 |
| PIE、自动化、真实输入/伤害时序 | — | 未运行；按当前MHWI台账由用户执行。构建/离线字段检查不证明七段实际扣血、低帧表现或完整原版行为。 | — |

## 风险、遗留与回退

R19仍为取证中：本批没有确定多目标/多部位选择、精确取消或刀刃空间规则。R31仍为部分完成：真实hitstop、音效、刀光、相机未实现/验证。A01、手柄A02、A04与其他开放台账项不在本批处理；35项汇总状态数量不变。

代码与脚本回退仅恢复本批对应源码差异；资产恢复使用`Saved/MHWIImport/EvidencedMechanics-20261026/Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset`，预期回到改前SHA。文档修改与先前未提交内容交织时只回退本记录新增段落，不整体重置工作区。反射签名未改；若后续回退含代码，需重新构建。

## 已同步文档

[MHWI系统现状](../Systems/MHWI-LongSword.md)、[接口契约](../Interfaces.md)、[开发台账](../Plans/MHWI-Restoration-Progress.md)、[已知问题](../Known-Issues.md)、[B13/B14/B15更新验收与B16复验](../Reference/MHWI-Acceptance-Update-20261026.md)、[MHWI入口](../README.md)、[模块索引](../Reference/modules.json)、[方案](../Plans/PLAN-20261026-002-mhwi-evidenced-mechanics.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
