# MHWI 当前开发计划

这是**唯一活跃**的 MHWI 计划页。已完成的方案与批次记录全部在 [Archive/MHWI/](../Archive/MHWI/README.md)，不在本页追溯。

现状见 [太刀训练模组](../Systems/MHWI-LongSword.md) 与 [雌火龙](../Systems/MHWI-Rathian.md)。
取证结论见 [太刀总账](../Reference/MHWI-LongSword-Evidence.md) 与 [雌火龙总账](../Reference/MHWI-Rathian-Evidence.md)。

## 一、目标与阶段

在 UE 5.8 的 IntroCpp 里用 em001 原作数据还原下位单人雌火龙战斗。两条线并行：

- **忠实线**：原作数据 + 原作 THK 决策，可宣称"还原"。当前卡在 THK 条件语义——社区命名覆盖 81.5% 条件段使用，**运行验证为 0**。
- **近似线 B1**：真动画 + 真数值 + 自制决策层，永远只能叫"近似 profile"。代码已编译通过，**PIE 验收一次没跑过**。

已确认的架构约束见 [ADR-0002](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md)：决策与执行分离、禁止两套执行逻辑、动作覆盖口径改为"已验证 ÷ 实际可达"。

## 二、里程碑（按执行顺序）

### M1 条件语义三栏表（本机可做，无需授权）

1. 以 `Scripts/MHWI/map_thk_function_semantics.py` 的输出（`Tools/MHW/rathian-thk-fexty-coverage-20261103.json`）为底
2. 对 27 类已命名项逐类校验参数取值范围是否与命名自洽：距离类应呈连续 cm 值、角度类应是 0~360 的对、布尔类参数必须全 0、rank 类必须 0~3
3. 产出"已证 / 冲突 / 未知"三栏表，落 `Docs/Reference/`
4. 31 类未命名项按使用次数排序，`0x5a`(186 次) 优先做参数聚类——`[4,30,10,32]` 这类整数很像枚举 ID，可与动作/区域/状态枚举对照

### M2 下位可达动作清单（本机可做，无需授权）

1. 遍历 105 THK 节点树，找出被 `0xB8`（`is_rank`）门控的分支
2. 提取各分支内 emit 的 actionID
3. 与 em001 的 285 条动作表交叉（**旧"344 条"口径已撤回**，新布局见[总账第五节](../Reference/MHWI-Rathian-Evidence.md)）
4. 产出"LR 可达动作集"作为新分母

### M3 BITE 的 ActionSpec + 差异报告（需授权开原作）

按 `PLAN-20261103-001` 的字段清单落表；原作侧未观测字段一律写 `unobserved`。

### M4 B1 PIE 验收（用户操作）

```
打开 L_MHWI_Training → PIE → 控制台：
summon /Script/IntroCpp.MHWIRathianApproxPawn
```

关注日志前缀 `[RathianApprox][Decision]` / `[RathianApprox] hit` / `Rage ON` / `DEAD`。
回归项：太刀五项（普攻/气刃/见切/居合/登龙）+ 训练靶不受影响。

## 三、待用户拍板

| # | 事项 | 说明 |
| --- | --- | --- |
| 1 | 原作运行授权 | 任何启动原作的验证（运行时 dump / 受控观测）需先获明确同意。约定：离线、隔离、关闭 `nativePC` 覆盖、记录原始目录快照 |
| 2 | 工作区未提交项 | 首链、B1、Approx 代码与 10-30 以来的改动。分拣"用户已有工作 / 项目新增"属用户决定范围 |
| 3 | 技术路线选择 | Ghidra 类型恢复（3–6 GB / 1–2 会话 / 70–85% 成功率）vs LuaEngine 运行时观测 vs 停在候选级 |

## 四、风险

| 级别 | 风险 | 处置 |
| --- | --- | --- |
| 🔴 | 关键证据在 `Saved/`（被 gitignore）：`action-registry-dump`、`thk-all-raw.json`(16.8 MB)、`analysis-text.bin`(48.3 MB)、`default.fexty` | 可归档的证据 JSON 复制到 `Tools/MHW/`（该目录已跟踪）；大二进制登记为"可再生/本地必需"并留 hash |
| 🟠 | B1 腐化 | B1 是脚手架。每闭合一条 THK 语义就替换一层手写规则；若三个月后 B1 还在自己长功能，说明主线偏了 |
| 🟠 | 社区数据污染 | fexty 是社区命名可能错；`mhw-lmt-engine` 是新工具。用前标注来源与验证状态 |
| 🟡 | 第三方注入器安全 | LuaEngine 等来自社区，只在离线环境、明确授权下使用 |

## 五、术语

| 词 | 含义 |
| --- | --- |
| **THK** | MHWI 怪物 AI 的"思考表"，存的是决策程序（节点+条件+指令），不是数值。em001 有 105 个 + 2 thklst |
| **THK VM 语义** | 原作 exe 里解释执行 THK 指令的虚拟机及各指令真实业务含义。缺口 BEH-01 |
| **fexty** | Leviathon 的 THK 函数签名/命名定义，社区维护，给出 condition 候选名 |
| **ACTP2** | 动作参数表，342 记录 / 142 启用 / 4,295 属性项 |
| **LR 资格** | 有证据地判定哪些记录/动画/攻击真被下位配置消费。文件里有 ≠ 下位用，数组下标 ≠ 动作 ID。缺口 BEH-03 |
| **B1 / 近似 profile** | 真动画+真数值+自制决策层，永远不能宣称"还原" |
| **首链** | 第一条端到端链路：THK → 动作 → 位移 → 碰撞（咬击 83 / 冲撞 86-87） |
| **ActionSpec** | 单个动作的完整定义（资格/转向/动画/位移/碰撞窗/伤害/可打断/结束），决策层与执行层的共享契约 |
| **cross-verified** | 两个独立来源一致（如本机解析 + 公开数据库），可升入忠实 profile |

## 六、给接手者的一句话

数据已经到手，代码已经能跑，缺的是"看懂原作的决策"和"把候选变成已证"。别再从零逆向，先复用 fexty；别追全量覆盖，先定下位可达集；**别相信任何没跑过的验收**。
