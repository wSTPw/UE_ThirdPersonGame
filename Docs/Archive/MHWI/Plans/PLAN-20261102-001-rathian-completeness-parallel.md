# PLAN-20261102-001：雌火龙方案完整性核对、音画细案补全与四模块并行实施

- 状态：implemented-scope；2026-11-02 核对页、音画细案、P1–P4 与构建验证均已交付（见 [CHG-20261102-001](../Changes/CHG-20261102-001-rathian-completeness-parallel.md)）；原作语义 unknown 按证据保留，非本轮闭合。
- 日期：2026-11-02。
- 用户需求：核对 MHWI 雌火龙还原方案文档完整性（行为逻辑/数值/动画模型/音效特效），缺失项先列清单再补全；确认后按模块拆分任务分派子代理并行实施，完成后汇总各模块进度与遗留问题。
- 关联模块 / 接口 / 问题：mhwi-unpack-data、mhwi-rathian-animation、enemy-ai、mhwi-longsword；核对结论见 [完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)。
- 上级方案：[总体方案](PLAN-20261031-002-rathian-restoration-master.md)、[首条链路](PLAN-20261031-007-rathian-first-chain.md)；不改已获授权选型（1C/2B/3B/4B/5A/6B/7B），不重新请求同一选型。
- 实施记录：[CHG-20261102-001](../Changes/CHG-20261102-001-rathian-completeness-parallel.md)。

## 现状与目标

核对结论（详见完整性核对页）：方案文档结构已完整（所有缺口有编号工作包与通过门）；四大板块中音效与特效最薄——只有 A5 五步+E08 工作包，无清点、无事件映射表、UE 侧零资产。另有文档记录缺口：首链实施无 CHG、索引缺行、modules.json 未登记。本轮目标：

1. 音画配置细案补全（下文 A5x 节）。
2. 文档记录补全（CHG-20261031-003 补录、索引、modules.json）。
3. 四个可并行、互不冲突的离线实施工作包（P1–P4）+ 主代理构建验证。

边界：全部为**离线静态/脚本工作**，不启动原作、不运行 PIE、不改旧 848 动画与既有太刀资产；语义未闭合项保持 unknown，不以工程产物冒充原作已证。

## 音画配置细案补全（A5x，补入本轮方案；实施随 M5）

A5/E08 原文保留；以下为落地方案细化，机制来源为 Epic UE5.8 官方文档（Niagara 不证明原作行为）：

| 项 | 细化内容 | 官方/项目来源 |
| --- | --- | --- |
| 事件映射表 schema | 每行：`EventKey(源ID/候选名) / SourceFile+SHA / 引用动作(bank+slot) / 源时刻(unknown 占位) / 类型(声音/VFX/镜头) / 附着骨(unknown) / UE落点 / 状态(raw/parsed/bound/approximated)`；unknown 不填 0 | 证据模型沿 PLAN-003 |
| 声音落点 | 候选 `/Game/MHWI/Rathian/Presentation/Audio/`；NBNK 解码工具候选需固定 commit 并经用户选择，未解码前只有清单行 | E08 选择门 |
| VFX 落点 | 候选 `/Game/MHWI/Rathian/Presentation/VFX/`；EFX→Niagara 重建属"表现近似"级，须显式标注，不得标原作保真 | [Niagara 概述](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/overview-of-niagara-effects-for-unreal-engine)、[创建视觉效果](https://dev.epicgames.com/documentation/unreal-engine/creating-visual-effects-in-niagara-for-unreal-engine) |
| 播放接入 | 事件行经动画事件通道（Notifies）驱动；音效播放沿用 Notify 官方机制，Niagara 内音频按 [Play Audio 模块](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/how-to-create-audio-effects-in-niagara-for-unreal-engine?application_version=5.3) 条件选择 | PLAN-005 引用+本轮检索 |
| 清理规则 | 循环呼吸/振翅绑定 Montage 退出；实例按 ShellInstanceId/ActionRunId 代次清理；卸载/死亡不残留附着实例 | PLAN-005 A4/A5 既有契约 |
| 验收等级 | "事件忠实、资源近似"与"原资源转换"分列；近似不改变总还原状态 | A5.5 既有 |

## 并行实施工作包（P1–P4，本轮执行）

| 包 | 模块 | 输入（只读） | 产出（新文件，不覆盖既有证据） |
| --- | --- | --- | --- |
| P1 行为链路取证 | W1/E02 | `rathian-thk-chain-evidence.json`、`extract_rathian_chain_motion/collision.py`、manifest | 5 个已关联动作（75/76/83/86/87）的动作→ACTP2→LMT bank/slot→AnimSequence 路径→COL 攻击字段完整关联表 `Saved/MHWI-Rathian-FirstChain/action-asset-correlation-20261102.json` |
| P2 音画清点与映射骨架 | W3/E08·A5x | `Saved/MHWI-Rathian-20261031-PlanEvidence/`（73 文件）、`rathian-plan-evidence-20261031.json` | 只读清点 `Tools/MHW/rathian-audio-vfx-inventory-20261102.json`；映射表骨架 `Docs/Reference/MHWI-Rathian-AudioVFX-Map-20261102.md`（unknown 行显式，不解码 NBNK） |
| P3 数值分段结算原型 | W4/C3.1 | LR 数据页已证数值（硬编码引用+来源注释） | `Scripts/MHWI/rathian_damage_pipeline_stages.py`（阶段化纯数据演算，未证阶段显式 unavailable）+ `Saved/MHWI-Rathian-FirstChain/damage-pipeline-sample-20261102.json` 示例输出；标注"工程原型，非原作公式验证" |
| P4 动画源映射首版 | W3/A0 | `rathian-animation-completion.json`、`extraction-manifest.json` | `Tools/MHW/rathian-source-motion-map-20261102.json`：SourceHash/Bank/Slot→UE 资产路径/Skeleton/时长→资格列（unknown）→已关联动作列 |
| 主代理 | W5 | 全部 | IntroCppEditor Win64 Development 构建验证首链 1546 行代码；索引/CHG/汇总 |

### 并行冲突边界

- P1 写 `Saved/MHWI-Rathian-FirstChain/`（新文件）+ 不修改既有脚本（如需扩展先在包内声明）；P2 写 `Tools/MHW/` 清点 JSON + Reference md；P3 写 `Scripts/MHWI/` 新脚本 + Saved 输出；P4 写 `Tools/MHW/` 映射 JSON。四包文件集互不相交。
- 索引（Plans/Changes/README、modules.json、Docs 首页）由主代理在包完成后统一更新，避免并发写。
- 不做：同一地图/DA/骨架写操作、构建产物并行写（构建由主代理独占）、UE 编辑器资产保存。

## 实施步骤与依赖

1. 补全文档（已完成先行）：核对页、音画细案、CHG-20261031-003、索引。
2. 并行 P1–P4；主代理同时启动构建。
3. 主代理核验四包产出（文件存在、JSON 可解析、unknown 未被填值、脚本 self-check 通过）。
4. 统一更新索引与 [CHG-20261102-001](../Changes/CHG-20261102-001-rathian-completeness-parallel.md)；记录构建与各包实际结果、遗留清单。

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 文档 | `python Scripts/Docs/check_docs.py`；`git diff --check` | 新增链接/索引合法、无空白问题 | 不验证玩法 |
| 构建 | UE5.8 Build.bat IntroCppEditor Win64 Development | 首链 Monsters 代码编译通过或失败原因明确 | 编译通过≠玩法正确 |
| P1 关联表 | JSON 可解析、每行含源 offset/SHA、动作 5/5 覆盖或显式缺因 | 无凭相似度的"已关联" | 不证明 VM 语义 |
| P2 清点 | 73 文件计数/尺寸与 plan-evidence 一致；NBNK 未解码标注 | 清点零写坏原文件 | 候选名≠语义闭合 |
| P3 原型 | `--self-check`；同输入两次输出一致；unavailable 阶段显式 | 无猜测数值冒充已证 | 非原作公式验证 |
| P4 映射 | 848 条与 completion 证据集合一致；资格列全 unknown | 与既有证据零冲突 | 不重跑导入 |

## 风险与回退

- 全部产物为新文件，回退=删除本批列出的新文件与文档行；不触碰用户未提交资产（太刀 C++/DA/训练地图等保持原样）。
- 构建若失败：只记录首条错误与定位，不在本轮擅自大改首链代码；修复属后续批次。
- P2 清点只读 raw 文件；解码尝试失败不阻断，如实记 unknown。
- P3 原型禁止把示例演算结果写成原作对照期望。

## 文档同步清单

完成后更新：本页状态、[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)（若产出改变结论）、Plans/Changes 索引、[CHG-20261102-001](../Changes/CHG-20261102-001-rathian-completeness-parallel.md)、modules.json（Monsters 入口）、Known-Issues（若有新发现）。历史 CHG-002/003 保留原义。
