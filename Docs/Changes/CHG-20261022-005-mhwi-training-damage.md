# CHG-20261022-005：训练场默认关闭木桩自动攻击

- 状态：completed，已保存地图并完成运行来源与训练安全验证
- 日期：2026-10-22
- 需求摘要：用户报告练习太刀时会被“自己打死”。
- 关联问题 / 接口：R-COMBAT-006；MHWI-005、DAMAGE-001
- Git：工作区变更，未提交

## 原因与结果

普通近战的碰撞查询和候选过滤均已排除自身。真正来源为训练场默认开启主动攻击的 `MHWI_CounterTarget`：每 4 秒对 220 cm 范围内玩家造成 12 点伤害。修正前真实 PIE 订阅玩家 `OnDamaged`，约第 4.016 秒记录来源 `MHWITrainingTarget_0`、伤害 12、玩家招式为 None，生命由100降到88，证明空闲也会被目标攻击。

现有训练地图三个木桩及地图新建脚本统一设置 `enable_attacks=false`，普通动画/连招练习默认被动。需要反击练习时选中场景目标，在 Details 的 MHWI 分类显式勾选 Enable Attacks。没有用玩家无敌或删除所有外部伤害来掩盖问题。

## 修改清单

| 文件/完整资产路径 | 关键修改 |
| --- | --- |
| `/Game/MHWI/Maps/L_MHWI_Training` | 原生 `AMHWITrainingTarget` 实例 `MHWI_CounterTarget` 从 true 改为 false；另两个实例本就 false。保存地图，位置、攻击间隔/伤害、目标血量和场景其余内容保留 |
| `Scripts/MHWI/author_assets.py::training_map` | 新建地图的三个目标均显式关闭攻击 |
| 同脚本 `passive_training_targets()` | 已打开训练地图的定向更新与保存；禁止 PIE 中保存默认配置，不重建已有地图 |
| `Scripts/MHWI/inspect_training_damage.py` | 读取实际目标完整路径、启用值、伤害/距离/间隔，并支持输出前后快照 |
| `Scripts/MHWI/pie_training_damage.py::run(mode)` | 伤害委托记录真实来源；诊断旧默认、验证新默认/自身攻击安全/目标真实伤害及见切 |

## 接口、事件与资源影响

限定 MHWI 独立训练场目标配置，不改 `Source/`、反射、角色正常受击/反击/死亡或原 Ninja 系统。保存前确认没有脏内容或地图，定向备份原训练地图，保留工作区此前已有修改。

原生 `AMHWITrainingTarget` 类的 `bEnableAttacks` 缺省仍 true，本次只修改已放置实例与生成脚本；手工新增原生目标应明确选择被动或主动。测试的目标移动、临时开启攻击、1秒攻击周期仅在一次性 PIE 世界中，不保存到正式关卡。默认被动目标的现有标签仍使用原训练提示文本，主动反击需手动启用。

## 实际验证

| 检查/命令 | 环境与实际结果 | 证据路径 |
| --- | --- | --- |
| MCP `editor.run_python_file` → `inspect_training_damage.audit()` | 修改前只有 `MHWI_CounterTarget` 启用，伤害12/间隔4秒/范围220cm | `Saved/MHWIImport/training-targets-before.json` |
| `pie_training_damage.run('diagnose')` | UE5.8 真实 PIE，**7项通过**；空闲角色受到外部目标12伤害，来源不是角色自身 | `Saved/MHWIImport/PIE-training-damage-diagnose.json` |
| `author_assets.passive_training_targets()` | 在编辑器世界将三个实例设为被动并保存关卡，返回原值 true/false/false → false/false/false | `Saved/MHWIImport/training-passive-authoring.json` |
| `pie_training_damage.run('verify')` | 从保存地图新开 PIE，**33项通过**，测试没有先强制关闭目标；原地处于范围内超过5秒不掉血，正常/气刃10个动作目标共扣268，玩家满血；大回旋升白刃 | `Saved/MHWIImport/PIE-training-damage-verify.json` |
| 同次 PIE 显式启用目标 | 外部目标攻击使玩家100→88；随后真实目标攻击在见切窗口被拦截，生命保持88且气刃槽补满，只有一次实际 OnDamaged 事件 | 同上 `damage_events` |
| 结束测试后 `inspect_training_damage.audit(output_name='training-targets-after.json')` | 编辑器关卡三个目标仍为 false，伤害12/范围220/间隔4秒均保留；PIE 临时开启与1秒周期没有写回地图，最终无脏包 | `Saved/MHWIImport/training-targets-after.json`、MCP 返回 |
| `python Scripts/Docs/check_docs.py`；三个受影响 Python 的 AST 检查；`git diff --check -- Docs Scripts/MHWI` | PASS：47个 Markdown、344个本地链接、12个模块；Python语法通过，文本diff退出0 | 本轮控制台输出 |

本轮没有改 C++/反射，因此未重新编译项目；没有重跑历史全部动作、挂接和登龙测试。此检查覆盖来源与训练场安全，不表示全项目所有自定义投射物、蓝图和其他地图都已排除自伤。

## 风险、遗留与回退

不再默认自动提供见切/居合练习攻击；使用者需显式勾选目标的 Enable Attacks。该行为变更已写入模组说明。

原地图定向备份位于 `Saved/MHWIImport/Backup-CHG005/L_MHWI_Training.umap`。回退可仅把 `MHWI_CounterTarget.enable_attacks` 设回 true 并保存，或在停止使用地图时定向恢复备份；同步恢复生成脚本的首目标主动配置。不要全仓库重置覆盖用户其他工作。

## 已同步文档

[模组现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[记录索引](README.md)。
