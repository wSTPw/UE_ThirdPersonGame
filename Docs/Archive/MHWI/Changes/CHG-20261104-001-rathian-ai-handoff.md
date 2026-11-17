# CHG-20261104-001：雌火龙项目 AI 交接文档

- 日期：2026-11-04。
- 起因：用户要求"交接一下工作，给其他 AI 看的"——需要一个自包含、无需读历史对话即可接手的交接文档。
- 关联：[完整性核对页](../Archive/MHWI/Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[路线方案](../Archive/MHWI/Plans/PLAN-20261103-001-rathian-review-adoption.md)、[VM 语义交接](../Archive/MHWI/Plans/MHWI-Rathian-VM-Semantics-Handoff.md)。

## 改动内容

| 文件 | 改动 |
| --- | --- |
| `Docs/Plans/MHWI-Rathian-AI-Handoff-20261104.md` | **新增**。12 节交接文档：一分钟摘要、环境与工程事实（构建命令 + 两个本机构建坑 + UE5.8 API 差异表）、项目规矩、两条产品线、代码地图（首链 9 文件 / Approx 11 文件 / 12 个脚本）、四板块取证总账、五个已实锤技术发现、3 项阻塞 + 2 项待用户拍板、下一步四个里程碑、5 条高风险、术语表、文档地图；§4.4 记录 2026-11-04 编译修复 |
| `Docs/Plans/README.md` | 追加交接文档索引行 |
| `Docs/Changes/README.md` | 追加本条与 CHG-20261104-002 记录 |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxPawn.{h,cpp}` | 编译修复，见 [CHG-20261104-002](CHG-20261104-002-rathian-approx-compile-fix.md) |

## 为什么需要它（写之前核实的现状）

1. 工作区 **147 项未提交**（`git status --short | wc -l`，2026-11-04 实测），包含首链、B1/Approx 三大块代码与 10-30 起全部文档；任何接手者若直接改代码，极易覆盖用户既有修改。
2. `Saved/` 被 `.gitignore:11` 忽略，而 **BEH-02 唯一产出**（`Saved/MHWI-Rathian-FirstChain/action-registry-dump-20261102.json`，344 条）、全量 THK 段数据（16.8 MB）、反汇编唯一可用载体（`analysis-text.bin`，48.3 MB）、社区映射表（`default.fexty`）**全部落在该被忽略目录内**——只有 `Tools/MHW/` 下的 6 个证据 JSON 是可跟踪的。此风险此前无任何文档记载，本轮写入交接文档 §9 第 2 条。
3. 此前进度分散在 6 份 CHG、3 份 PLAN、2 份交接文档中，无统一入口；新接手者需要读 10+ 文件才能建立现状认知。

## 内容边界（如实标注）

- 本文档为**现状汇总**，不含新取证。所有"已证/候选/未解"沿用核对页编号与既有证据文件，未提升任何证据等级。
- B1 的五项用户反馈修复（浮空/移动/朝向/衔接/受击）标注为"**编译通过、PIE 验收未执行**"，未写成已验证。
- §4.2 的缺陷表逐条对应 2026-11-02 用户实测反馈，修复状态按代码实际改动记录，未宣称已解决。

## 验证

- `python Scripts/Docs/check_docs.py`：通过（见执行输出）。
- `git diff --check`：通过。
- 未编译、未 PIE、未启动原作——本轮仅文档。

## 未验证项 / 遗留

- 交接文档中"下一步里程碑 1/2（条件语义三栏表、下位可达动作清单）"尚未执行。
- `Saved/` 证据归档到 `Tools/MHW/` 的建议动作未执行（需用户确认，涉及 48 MB 二进制与目录策略）。

## 回退

删除 `Docs/Plans/MHWI-Rathian-AI-Handoff-20261104.md`，回退 `Docs/Plans/README.md` 与 `Docs/Changes/README.md` 各一行，删除本文件。
