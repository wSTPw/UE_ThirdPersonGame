# CHG-20261102-003：原生动作注册表转储与 B1 近似 profile 方案交付

- 状态：completed-scope（注册表数据源闭合；方案交付；AP-1~AP-5 未实施）
- 日期：2026-11-02
- 需求摘要：用户选择 B1 路线（真动画+真数值+自制决策层）；本轮先解锁 B1 关键数据源并交付方案。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261102-002](../Plans/PLAN-20261102-002-rathian-approximate-profile.md)、[完整性核对页 BEH-02](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)。
- Git：工作区变更，未提交。

## 原因与结果

原行为：动作→动画映射仅有动作 83 一例（bank2/slot1）；"当前原生动作注册表"被列为 BEH-02 证据缺口；B1 无方案。

当前行为（全部只读静态发现）：

1. **原生动作注册表完整转储**：344 条 `{名字, 运行时ID, vtable}`（ID 10~212），条目布局 32B 从 BITE 样本实证；存在于多张分系统表（地面战/飞行/气球/骑乘各自独立 ID 序列，同一 ID 可对应多表不同名）。
2. **编号命名空间修正（重要）**：ActionDumps 历史编号 ≠ 运行时注册表命名空间，且无统一偏移（BITE 83→84、DASH_BITE2 86→87、ROLLING_TAIL_ATTACK2_L 75→101）。THK emit id ↔ 注册表 id 映射须逐动作核验；**首链 action_correlations 的资格注记（维护者 dump+CRC 候选）维持"候选"定级不变**，注册表为后续核验权威源。
3. **解码算法消费端实证**：`slot=packed&0x1FF; bank=(packed>>12)&0xF`（0x141c0158a/0x141c0159c/0x141c015a7 指令级证据），与 P1 的 INDEX_MASK/BANK_SHIFT 一致。
4. **构造器模式确认**：133 个 `mov qword [reg+0x1E0], packed` 站点（含浮点噪声，过滤规则已记录）；构造器 desc 为方法指针数组，不含注册表 vtable；.data vtable 运行时填充——注册表 id↔motion 桥接归入 R1/R2 收益。
5. **B1 方案交付**：[PLAN-20261102-002](../Plans/PLAN-20261102-002-rathian-approximate-profile.md)——决策层接口化（ScriptedPolicy→未来 ThkPolicy 替换）、双 DataAsset（数值 evidenced/权重 approximated）、AP-0~AP-5 步骤与验收门。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/scan_thk_action_ctors.py` | 新增 | 构造器 motion 编码扫描（B1 数据源工具） |
| `Scripts/MHWI/dump_action_registry.py` | 新增 | 注册表全量转储（B1 招式名单权威源） |
| `Saved/MHWI-Rathian-FirstChain/action-ctor-motion-scan-20261102.json` | 新增 | 133 站点扫描结果 |
| `Saved/MHWI-Rathian-FirstChain/action-registry-dump-20261102.json` | 新增 | 344 条注册表（BEH-02 核心缺口闭合） |
| `Docs/Plans/PLAN-20261102-002-rathian-approximate-profile.md` | 新增 | B1 方案 |
| `Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md` | BEH-02 行更新 | 注册表已转储、命名空间修正 |

## 接口、事件与资源影响

无既有接口/蓝图/资产变更；不修改游戏安装与既有证据 JSON。用户既有未提交修改保持原样。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 注册表转储 | Python（hash 校验内建） | 344 条；BITE/DASH_BITE2/ROLLING_TAIL_ATTACK2_L 抽验与 ActionDumps 交叉 | `action-registry-dump-20261102.json` |
| 解码实证 | capstone 反汇编 | 消费端位域指令与 P1 常量一致 | `scan_thk_action_ctors.py` 头注+JSON |
| 文档检查 | `python Scripts/Docs/check_docs.py`；`git diff --check` | 通过 | 本记录 |
| PIE/编辑器/原作运行 | — | 未执行（静态边界） | — |

## 风险、遗留与回退

- 遗留：注册表 id↔motion packed 桥（R1/R2）；THK emit id↔注册表 id 逐动作核验；AP-1~AP-5 未实施。
- 回退：删除上表 4 个新文件与文档行即完全回退。

## 已同步文档

[B1 方案](../Plans/PLAN-20261102-002-rathian-approximate-profile.md)、[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[Plans 索引](../Plans/README.md)、[Changes 索引](README.md)。
