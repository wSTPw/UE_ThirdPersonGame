# CHG-20261103-001：NUM-03 双源闭合、运行时路线更新与对外评审简报

- 状态：completed（文档批次）
- 日期：2026-11-03
- 需求摘要：用户要求将近期对话成果落文档并生成可外发 GPT 评审的材料。
- 关联 PLAN / ADR / 问题 / 接口 ID：[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md) NUM-03、[VM 语义交接](../Plans/MHWI-Rathian-VM-Semantics-Handoff.md) R2、[评审简报](../Reference/MHWI-Rathian-Review-Brief-20261103.md)。
- Git：工作区变更，未提交。

## 原因与结果

原行为：网上数据库交叉验证结论（NUM-03 部位映射闭合、NUM-01 期望源）、LuaEngine 工具路线、时间预估均只在对话中，未落文档；无对外评审材料。

当前行为：

1. **NUM-03 闭合**：本机 12 行肉质表与 monsterhunterwiki.org MHWI 雌火龙逐行一致（行0=Head … 行11=MR Tail；MR Wings 21/21/45 精确匹配），证据等级升为 cross-verified，核对页已更新；7 组硬直部位映射同步确认。
2. **R2 路线更新**：交接文档 R2 由"x64dbg 自写 hook"更新为 **LuaEngine（Gitee 系 Mt Framework 注入器）** 运行时观测路线，附四层工具路线对照（文件/数值/运行时/格式解析）。
3. **评审简报**：新增自包含单文件 `MHWI-Rathian-Review-Brief-20261103.md`（现状/已闭合事实/未闭合清单/决策/时间预估/风险/6 条评审问题），可直接外发。
4. Docs 首页增加评审简报入口。

## 修改清单

| 文件 | 修改 | 效果 |
| --- | --- | --- |
| `Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md` | NUM-03 行更新 | 证据缺口→双源闭合 |
| `Docs/Plans/MHWI-Rathian-VM-Semantics-Handoff.md` | R2 行重写+工具对照节 | 运行时路线定为 LuaEngine |
| `Docs/Reference/MHWI-Rathian-Review-Brief-20261103.md` | 新增 | 对外评审自包含简报 |
| `Docs/README.md` | 快捷入口新增 | 可发现性 |

## 接口、事件与资源影响

无代码/资产变更。

## 实际验证

| 检查/命令 | 结果 |
| --- | --- |
| `python Scripts/Docs/check_docs.py` | PASS（见本轮末尾汇总） |
| `git diff --check` | PASS |

## 风险、遗留与回退

- 评审简报中的时间为估算（基于本会话实测速率），非承诺排期。
- 回退：删除简报与索引行，还原两处文档段落即可。

## 已同步文档

[核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[VM 交接](../Plans/MHWI-Rathian-VM-Semantics-Handoff.md)、[评审简报](../Reference/MHWI-Rathian-Review-Brief-20261103.md)、[Docs 首页](../README.md)、[Changes 索引](README.md)。
