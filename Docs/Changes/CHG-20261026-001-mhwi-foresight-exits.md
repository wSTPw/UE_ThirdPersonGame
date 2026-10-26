# CHG-20261026-001：B11 见切缺失出口（B→突刺、R+A→登龙突刺）

- 状态：completed（开发完成，未测试）。批次目录沿用 `Saved/MHWIRestoration/B11-20261025`（10-25 完成的取证与脚本准备）；正式资产保存与读回于 2026-10-26 00:44（本地时间）完成。
- 日期：2026-10-26（批次始于 2026-10-25）。
- 执行与身份：**WorkBuddy 代理会话**（2026-10-25 21:30 接手台账；此前 B01–B10 由其他会话完成）。本台账多会话共用，特此注明执行者、原因与思路，便于交接追溯。
- 需求摘要：按[台账](../Plans/MHWI-Restoration-Progress.md)当前接续点顺序接手开发；本批完成第 4 点的 R04 见切缺失出口。
- 关联：[总台账](../Plans/MHWI-Restoration-Progress.md)、R04、[33项审查 R04](../Reference/MHWI-Restoration-Review.md)、[B01 原生证据](../../Saved/MHWIRestoration/B01-20261024/native-reference-plan.json)、[B02 同条件窗口复用先例](CHG-20261024-008-mhwi-spirit-branches.md)。
- Git：工作区变更，未提交；保留协作者 B10 及用户的全部既有修改。

## 原因与结果

审查 R04 记录：正式见切 `ForesightSlash` 只有 `Light→StepSlash`（B01 已修），缺原版 B（○）与 R+A（R+△）两条出口。本批直接重读固定指纹原 `wp03_action.fsm`，确认 node28 完整边表并实现：

| 原 FSM 边（node28） | 条件 | 目标节点/身份 | 正式路由结果 |
| --- | --- | --- | --- |
| order 6 | `['○']`（operator 17） | node4 = Thrust（ActionNo 79） | `THRUST` → `Thrust` |
| order 3 | `['R+△']`（operator 16） | node45 = SpiritThrust（ActionNo 87） | `HELM_BREAKER` → `SpiritThrust` |

条件 ID 交叉一致：○→4 为 90、R+△→45 为 108，与 `transition_calibration.json` 独立记录的 `source_outgoing_links`（4:90、45:108）相同；节点身份与 `moveset_mapping.json`（Thrust node4、SpiritThrust node45、StepSlash node11）一致。

正式 `DA_MHWI_LongSword.ForesightSlash.Routes` 由 6 条增至 8 条（全 DA 149→151 条），只改该招路由；伤害窗口、消耗、回槽、防御窗、动画与连接数据一律未动。

**思路**：遵循台账既有规则"新增同条件路线只复用现有适配窗口"。两条原边均无命中/反击/槽位等附加条件，与已存在的 `Light→StepSlash` 同属无前置条件类，因此复制该路由派生出新路由，窗口沿用其项目适配窗 1.5–2.6667 秒（校准文件 LIGHT 规则帧 90..160）。**不新造任何时间值**，精确输入位/取消帧仍属 R07、未声称原版时序。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/native_foresight_exits.py`（新增） | node28 边取证与指纹守卫 | 每轮重读固定指纹 FSM，断言 ○→4、R+△→45、△→11 三条边及 operator；输出 `Saved/MHWIRestoration/B11-20261025/native-foresight-plan.json` |
| `Scripts/MHWI/author_foresight_exits.py`（新增） | `apply_to_copies`/`run` | 路由派生、全字段结构保护、幂等（已应用状态可识别）、备份、保存、读回 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | `ForesightSlash.Routes` | 6→8；新增 `THRUST→Thrust`、`HELM_BREAKER→SpiritThrust`，`require_*` 全 false，`cancel_start=1.5`、`cancel_end=2.6666667` |
| `Saved/MHWIRestoration/B11-20261025/*` | 批次证据与驱动脚本 | 预览/保存响应、结构快照、读回与备份；`b11_author_driver.py` 以 `importlib.reload` 驱动，避免编辑器缓存旧模块 |

## 接口、事件与资源影响

无 C++、反射、枚举或接口签名改变，无需编译。仅一个 Content 资产（正式 DA）磁盘字节变化；Montage、Sequence、BlendSpace、地图、蓝图、HUD 与 `transition_calibration.json` 均未改。蓝图中经 `Moveset` 读取该 DA 的路径自动获得新路由，无需重编译蓝图。

## 实际验证

按本阶段约定（用户要求"开发优先、不运行测试"）只执行写入路径自带的守卫与读回，不运行编译、PIE、自动化、语法/文档/diff 检查。

| 检查 | 环境 | 实际结果 | 证据 |
| --- | --- | --- | --- |
| 源指纹与边取证 | 本机 Python（只读原始文件） | 固定指纹匹配；node28 共 7 条边；○→4、R+△→45、△→11 断言通过；条件 ID 与校准文件一致 | `native-foresight-plan.json` |
| 复制预览 | UE-MCP 编辑器 Python | `saved=false`、`idempotent=true`、`protected_fields_unchanged=true`、新增 2 条路由；未写盘 | `preview-response.json` |
| 正式保存与读回 | 同上 | `saved=true`；结构快照 before/after 仅 `ForesightSlash.routes` 不同，32 招其余字段（含全部伤害窗口）逐字段相同 | `authored.json` |
| 磁盘与脏包 | 本机 + 桥接 | DA 118851→119387 字节；SHA256 `2979914e…`→`490ab87f…`；保存后脏包列表为空 | `authored.json`、`list_dirty_packages` |
| 运行时读回 | 编辑器 Python | 8 条路由顺序为 SPIRIT、LIGHT、THRUST→Thrust、HELM_BREAKER→SpiritThrust、FORESIGHT、SPECIAL_SHEATHE、EVADE、FADE_SLASH | `live-state.json` |
| 未执行 | — | 编译/UHT、PIE、自动化、`check_docs.py`、`git diff --check` 均未运行；不声称通过 | 无 |

**开发中发现并修正的两处脚本问题**（供后续批次参考）：① 原幂等复检把"已应用"状态当异常，已改为可识别并校验派生一致性；② 编辑器 Python 会缓存已导入模块，修改脚本后必须 `importlib.reload`，否则执行旧代码。

## 风险、遗留与回退

- R04 的**存在性**已闭合（三条原边全部实现），但**精确性**未闭合：`1.5–2.6667` 是项目适配窗，原版接收/执行/取消帧仍属 [R07](../Plans/MHWI-Restoration-Progress.md)，不得把本批当作原版时序完成。
- R06 连接数据、R08 输入缓存、R09 转向、R24 受击均未改动；本批不涉及命中空间、伤害管线或耐力。
- 回退：恢复 `Saved/MHWIRestoration/B11-20261025/Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset`（保存前 118851 字节；SHA256 前 16 位 `2979914ea2a6eb70`），或删除两条新增路由后重存。脚本与证据可逐项撤除。不要重置整个工作区，不覆盖协作者 B10 与用户既有资产。

## 已同步文档

[总台账](../Plans/MHWI-Restoration-Progress.md)（当前批次、接续点 4、R04 行、B11 小节）、[系统现状](../Systems/MHWI-LongSword.md)（见切操作行）、[已知问题](../Known-Issues.md)（R-COMBAT-010）、[记录索引](README.md)。
