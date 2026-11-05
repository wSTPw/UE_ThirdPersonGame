# PLAN-20261026-002：B14 已取证太刀机制实施

- 状态：implemented-scope（B14源码、A06补排及正式DA迁移已完成；静态校验/构建通过，PIE待用户运行）
- 日期：2026-10-26
- 用户需求：查看 MHWI 与开发台账，只开发原游戏证据已经明确的部分；本机不运行原游戏，未取证且实现方式不清楚的部分不擅自修改，并报告来源、依据与跳过项。
- 关联模块 / 接口 / 问题：`mhwi-longsword`；MHWI-003/005/007/008/010；台账 R10/R11/R13/R16/R19/R21/R29/R31；R-COMBAT-017/018。
- 前置证据：[B13 原生消费者](../Reference/MHWI-Outstanding-Evidence-20261026.md)、[总台账](MHWI-Restoration-Progress.md)。
- 实施记录：[CHG-20261026-005](../Changes/CHG-20261026-005-mhwi-evidenced-mechanics.md)。B14其余机制源码来自`4b5361c`；本批修复登龙一次接触七段补排并保存正式DA。编译修复历史见[CHG-20261026-007](../Changes/CHG-20261026-007-mhwi-build-fix.md)。

## 现状与目标

B13 已把若干参数字段追到原生消费者，但正式玩法尚未迁移：Q 没有自然衰减；回旋仍在命中帧立即升色且不清余槽；10 秒字段被错误留给 Q；登龙 0.4 秒被误用作表现冻结；登龙七段和居合追加伤害仍按落地/普通窗口结算；普通回避仍使用项目自定的 Montage 区间。

本批只迁移已有消费者证据的局部行为，不把“字段已读”扩大为“整个条目已还原”。当前保留的 W03P/COL 可重新读取；B13 的反汇编与 PLP 以 `Tools/MHW/native-outstanding-evidence.json` 的固定指纹快照为证据，本批不声称重新运行原游戏或重新提取缺失的分析缓存。

## 范围与验收标准

| 子项 | 本批实施 | 完成边界 |
| --- | --- | --- |
| R10 Q 自然衰减 | 以 120 为时间标尺、0.05 为倒计时及扣减量；项目 0–100 槽每步扣 5，修改 Q 重置倒计时，回槽分支跳过自然衰减；长帧最多扣一步 | 原 `owner+0x8938 bit0` 的完整上游、技能与 hitstop 顺序仍不补造，R10 不宣称整体关闭 |
| R11 颜色暂停 | 合格回旋提交时颜色余量刷新、10 秒暂停赋值；暂停倒计时结束后颜色才衰减 | 技能倍率和其他上游资格继续开放 |
| R13 回旋清槽 | 真实命中只锁存；动作退出提交升色、Q 清零、颜色计时刷新和 10 秒暂停；空挥不清槽，命中后退出只提交一次 | 未映射的 timeline bit30 精确帧不虚构；死亡/销毁边界单独保留 |
| R16 居合追加命中 | 有色居合首击确认后捕获弱目标与目标相对接触点，0.5 秒后按白/黄/红 55/72/86 结算一次；无色不排队；退出动作取消 | 1.3 只保留为未闭合的部位侧参数，不乘进 HP；原部位/碰撞下游不冒充完成 |
| R19 登龙延迟命中 | 下劈 126 首击确认后从接触起排队，首段 0.4 秒、后续 0.05 秒、最多七段；按接触颜色取 10/15/25；使用目标当前变换还原相对点 | 普通派生不自动清除已提交队列；目标失效安全略过。完整原取消/多部位/空间命中仍开放 |
| R21 普通回避保护 | 动作入口建立浮点帧倒计时，基础 13 帧；保留 13/15/17/19/22/25 技能表和 30 帧衣装值；以显式训练配置选择，倒计时按 Actor 秒×60 | 不把旧 0.06–0.4 Montage 秒当原值；不声称已接真实装备/技能系统或所有伤害类别 |
| R29 特殊纳刀等待 | 核对并保留现有 3.5 秒 Actor 秒等待 | 不修改 73 帧冻结、80/129 事件或全局播放/循环，R29 保持部分完成 |
| R31 时钟纠错 | `SpiritHelmBreaker` 的表现冻结恢复 0；0.4 只供延迟队列，移除落地七窗 | 不新增未经取证的 hitstop、音效、刀光或相机参数 |

主动跳过：R07 精确取消、R08 跨帧缓存与全局仲裁、R09 完整转向、R18 刀刃/部位空间、R20 完整耐力、R23 防御事件类型、R30 IK/装配，以及 R16/R19/R21 尚未闭合的下游。验收 A01–A04 涉及未闭合的原生恢复许可、组合输入仲裁和菜单上下文，本批不顺手改写。

## 依据与外部交叉来源

1. 项目固定证据：`Tools/MHW/native-outstanding-evidence.json` 中 `gauge_change`、`roundslash_commit`、`weapon_tick`、`helm_schedule`、`helm_emit`、`iai_emit`、`dodge_protection_table`、`protection_countdown`、`protection_flags`；参数偏移与资源 SHA-256 以该快照为准。
2. 保留原始资源：`ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp/wp03/wp03_param.w03p`、同目录 `collision/wp03.col` 与 `shell/collision/object.col`；本批重新读取并核对指纹/数值。
3. Kiranico 太刀指南（https://mhworld.kiranico.com/en/guide/long-sword）：回旋需成功命中才升色并刷新等级时长，登龙命中触发回槽；只作行为交叉佐证，不替代消费者指令。
4. MHW World Wiki Evade Window（https://monsterhunterworld.wiki.fextralife.com/index.php?diff=cur&oldid=16586）：13/15/17/19/22/25 帧表与保留 PLP 快照一致。
5. Nexus Mods 的 Iai Spirit Slash Fix（https://www.nexusmods.com/monsterhunterworld/mods/5262）：其修改说明显示原版二击延迟 0.5、白/黄/红 19+55/31+72/39+86，并将 1.3 明确描述为部位伤害而非 HP；只作二手交叉佐证，不采用其修改值。

## 技术方案

- `UMHWIMovesetData` 增加源值字段：Q 时间标尺/比例、登龙延迟参数与三色基值、居合延迟与三色基值、回避帧表/衣装帧。既有 `SpiritDecayPauseOnRaiseSeconds` 保留名称以兼容资产，注释更正为颜色暂停。
- `AMHWICharacter` 集中 Q 修改以重置衰减时钟；颜色暂停与 Q 使用独立计时。回旋使用单次命中锁存，并在 `FinishMove` 的动作退出边界提交。
- 延迟命中使用弱目标引用、目标相对接触点、剩余秒数、MV 与伤害快照。登龙队列独立于落地动画；居合待发生命周期受 Action102 对应动作约束。每次结算先出队再调用属性伤害，目标失效不保留裸指针。
- 普通回避在动作入口设置帧倒计时，伤害拦截只查询该计时，不再回退到旧 Montage 窗。训练用技能等级/衣装开关明确是输入适配，不代表真实装备系统已经接入。
- `FMHWIResolvedHit` 增加延迟标记、段序号和接触位置；旧 `OnHitResolved` 签名不变，延迟段没有伪造近战 COL 索引。
- 新 `author_b14_evidenced_mechanics.py` 只改正式 DA 的声明字段与两处旧窗口：下劈 hit-stop 归零、HelmLand 旧七窗清空。预览/幂等/全字段保护/备份/保存/读回通过后交付；现有生成入口同步避免重建回退。

## 接口与数据迁移

| 接口 / 路径 | 当前行为/值 | 目标行为/值 | 调用方/蓝图影响 | 迁移顺序 |
| --- | --- | --- | --- | --- |
| MHWI-003 资源 getter | 无 Q 衰减倒计时、回避帧和延迟队列读数 | 增加只读快照，不提供私有写入口 | HUD 可继续用旧 getter；新 getter 供验证 | 新字段默认兼容 → 完整构建 → PIE |
| MHWI-005 命中与落地 | 落地七窗直接扣血，突刺目标继承落地七段 | 下劈接触建立延迟队列，落地不再直接结算七窗 | 旧 DA 必须定向迁移，否则双重伤害 | 先备份 → 改 C++ → 改 DA → 读回 |
| MHWI-007 防御/计时 | 回避按 Montage 区间；颜色暂停未在回旋提交启用 | 回避按浮点帧；回旋提交暂停颜色 10 秒 | 非回避反击/无敌窗不变 | 仅 Roll 特化，其他定义不迁移 |
| MHWI-010 `FMHWIResolvedHit` | 无延迟身份和接触点 | 增加 `DelayedShell`、`ShellHitIndex`、`ContactLocation` | 旧字段和事件签名不变 | 默认字段兼容，完整构建 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | 下劈 hit lag 0.4；HelmLand 七窗 | 下劈 hit lag 0；HelmLand 零直接伤害窗；写入源参数 | 仅该资产保存，地图/蓝图不主动保存 | B14 预览 → 备份 → 保存 → 幂等/读回 |

所有状态仍在游戏线程持有和推进；延迟队列不拥有目标，不跨死亡/EndPlay 留存。普通派生与登龙队列的关系仅按已证局部链保留，不把工程安全清理描述为原版取消规则。

## 实施步骤与依赖

1. 固定证据与外部来源，保存本方案；不触碰未闭合系统。
2. 修改数据声明和角色资源/延迟/回避逻辑，更新当前生成入口与静态基准。
3. 完整编译 `IntroCppEditor Win64 Development`，先修编译/反射问题。
4. 用 B14 定向迁移正式 DA，检查预览、幂等、全字段保护和读回。
5. 运行源/DA 静态校验、针对性 PIE 与更新后的登龙空气链回归；再执行文档与 diff 检查。
6. 更新台账、系统现状、接口、已知问题、模块索引和 CHG；把未执行/失败/跳过项分别记录。

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 原始参数与 DA | `python Scripts/MHWI/verify_evidenced_mechanics.py --da <B14 authored.json>` | W03P/COL/shell/快照一致；无旧七窗和 0.4 hit-stop | 不执行原游戏，不证明完整消费者覆盖 |
| Q 与回旋 | `pie_evidenced_mechanics` | 约 6 Actor 秒扣 5、长帧不补扣多步；空挥不清槽，命中退出清槽/升色/刷新/暂停 | 不含未知技能与 owner 位上游 |
| 居合追加 | 同上 | 白/黄/红只追加一次对应 MV，0.5 秒前不到账；移动目标按当前变换定位；退出/无色不追加 | 不验证部位 HP 公式和原碰撞下游 |
| 登龙追加 | 同上及 `pie_behavior_corrections.run('air')` | 126 首击后 0.4+0.05n 秒最多七段，落地不重复七窗，提前落地不错误授权 | 多目标/部位/完整取消仍开放 |
| 回避与等待 | `pie_evidenced_mechanics` | 13 帧内拦截、帧外失效；技能/衣装训练输入选表；3.5 秒等待不触发 80 帧事件改造 | 不接真实装备，不声称全部伤害类型 |
| 构建与文档 | UBT、`check_docs.py`、`git diff --check` | 编译和检查通过；失败逐项保留 | 编译不等于行为通过 |

## 风险与回退

- 旧 DA 与代码必须同批迁移；只改一边会双重结算或没有追加伤害。保存前保留 DA 字节和 SHA-256，回退仅恢复该文件及本批源码/脚本。
- 延迟队列必须防止重复结算、目标销毁、死亡重入和跨地图残留；采用先出队、弱引用和死亡/EndPlay 清理。
- Q 修改入口分散，需核对所有直接写入，避免新增衰减计时被旧路径绕过。
- 旧生成入口会重写七窗或旧参数，必须同步修正；历史 B12 文档和快照不改写，旧断言只保留历史含义。
- 完整原版伤害、部位和碰撞尚未完成，本批 MV 与既有训练伤害公式分开记录，不能把伤害数值一致扩大为完整管线一致。

## 文档同步清单

完成后更新 `Docs/Systems/MHWI-LongSword.md`、`Docs/Interfaces.md`、`Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Known-Issues.md`、`Docs/Reference/modules.json`、方案/变更索引及工作日志；新增 B14 实际变更记录和验证报告。方案状态按实际结果改为 implemented 或 partial，不把未运行项写成已验证。

## B16实施复验（2026-10-26）

接续更新验收的A05/A06：`ScheduleHelmShell`在一次合格接触后按`firstDelay + index * interval`预排至`HelmShellHitLimit`，固定目标弱引用、目标相对接触点、颜色MV及动作倍率；已有到期循环低帧时逐条排空。正式`DA_MHWI_LongSword`现已清空`HelmLand`旧七窗并把`SpiritHelmBreaker`首击`HitLagSeconds`置0，B14迁移脚本保存并读回。脚本补上自身目录到`sys.path`，可由UE-MCP Python入口驱动。

UE 5.8 Editor完整构建与22项离线DA/源参数检查通过；保存报告磁盘SHA与当前资产SHA相同。未运行PIE/自动化，运行验收仍由用户执行。原取消、多目标目标选择、刀刃/部位空间和真实表现hitstop继续开放，不提升R19/R31整体状态。
