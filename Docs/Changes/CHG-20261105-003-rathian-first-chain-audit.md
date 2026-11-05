# CHG-20261105-003：雌火龙首链只读取证与源码审查

- 状态：completed（本轮只读审查与文档）；首链忠实实现仍partial。
- 日期：2026-11-05。
- 需求摘要：暂缓Sandbox修复，继续三个子代理按“THK→动作→移动→命中”补最小证据缺口。
- 关联：PLAN-20261031-007、ADR-0002、BEH-01/02、E01–E04；R-DATA-006/007、R-ANIM-013、R-COMBAT-013、R-AI-003。
- Git：工作区文档变更，未提交；已有代码/资产修改保留。

## 原因与结果

旧动作表导出从name指针起读，导致BITE名称连接到下一项84和类型描述符。新32B候选布局下BITE为83；em001表285项与固定维护方dump逐项一致，新增有界追证找到表指针getter及原生注册循环，stride32/字段读点获得静态消费者支持；THK动作查找/启动及caller怪物对象归属未证。撤回现状页“344条完整name↔id↔vtable注册表已闭合”口径，不改历史CHG或旧JSON。

本轮还复核THK55/n200的两条件九步受控路径，独立解码29根键/131点，补齐UID32/21/24三通道。静态审查确认共享时钟、TOI覆盖、骨轨近似、原位资产资格、strict条件provider及动作完成回VM等边界。详见[完整证据与顺序](../Reference/MHWI-Rathian-FirstChain-Audit-20261105.md)。原作条件语义、完整命中/伤害链仍未验证。

## 修改清单

| 文件/资产完整路径 | 符号或内容 | 原因与效果 |
| --- | --- | --- |
| Docs/Reference/MHWI-Rathian-FirstChain-Audit-20261105.md | 新取证台账 | 三代理成果、原始偏移/hash、资格与缺口、源码审查及下一步 |
| Docs/Plans/MHWI-Rathian-AI-Handoff-20261104.md | 顶部增补与BEH-02 | 当前推荐顺序与撤回旧注册表闭合口径 |
| Docs/Plans/MHWI-Rathian-VM-Semantics-Handoff.md | 顶部增补 | 将首链最小切片/身份新证据连接到历史交接 |
| Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md | BEH-02 | 恢复为候选布局交叉一致、原生消费者开放 |
| Docs/Known-Issues.md | 五个静态问题与环境暂缓 | 明确源码风险未修复、系统修复按用户要求暂缓 |
| Docs/README.md、Docs/Changes/README.md | 入口/索引 | 可直接接续本轮证据 |
| Docs/Changes/CHG-20261105-003-rathian-first-chain-audit.md | 本记录 | 验证与回退 |

以上项目相对路径均相对 `E:/Unreal Projects/IntorCpp`。

## 接口、事件与资源影响

无代码、接口、事件、配置、蓝图、关卡或资产变更；未修改Scripts/Tools源文件、旧原始数据/证据JSON、冻结DevFlow任务及验收。未重解包、安装、启动原作或UE。Sandbox修复按用户要求暂缓，本轮未执行修复/重启/关机指令。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据 |
| --- | --- | --- | --- |
| 三代理只读struct/JSON/有界原生字节核查 | 固定EXE、分析.text、em001原始THK/LMT/COL/MOD3 | 新布局285/285、59/59、131/131交叉一致；29根键与131样本一致；三UID已读；消费者缺口保留 | 取证台账的完整路径/offset/SHA256 |
| 主代理独立struct/pefile读取与关键源码审查 | 同上 | THK200044=83；候选表/指针匹配；主代理再次独立逐项核3表285/59/131全匹配、em001有155条非零字段；表指针getter/注册循环字节与stride32/ID32/+8类型/+24名称读点匹配；源码边界成立；未运行构造反例 | 取证台账 |
| UE-MCP project.get_status | 现有桥接 | disconnected/editorConnected=false；未启动UE，实际001根轨/锁根资产属性未读回 | 子代理本轮工具回执及取证台账 |
| 归并前后29文件SHA256比对 | Source/Monsters、对应测试/工具/原始输入及既有证据 | 29/29一致，变更列表为空 | 本轮工具回执 |
| `python Scripts/Docs/check_docs.py` | 本工作区 | PASS：213 Markdown、1774本地链接、16模块与快照JSON；只验文件/索引 | 本轮工具回执 |
| `git diff --check` | 本工作区 | exit0；仅既有工作区的LF→CRLF提示，无空白错误 | 本轮工具回执 |

未执行构建、项目单元测试、PIE、原作对照；只读任务无需用这些替代缺失的原生语义证据。历史编译/导入读回仅作历史引用。官方UE 5.8机制与社区资料的适用范围在取证台账分别标明。

## 风险、遗留与回退

完整首链未闭合；不要将83/84修正升级为原生动作绑定通过，不要把130/60导入时长当原作60Hz，不据MV0推断通道无作用。源码发现尚未修改，后续实现须冻结独立任务及验收。原始/缓存证据多位于忽略目录，报告给出完整hash但不意味着已归档托管。

回退仅撤销本轮文档增补、新报告及本CHG/索引行；保留所有原有工作区变更。历史已完成CHG不重写。无新系统或源码入口变化，模块索引不改。

## 已同步文档

[入口](../README.md)、[交接](../Plans/MHWI-Rathian-AI-Handoff-20261104.md)、[VM交接](../Plans/MHWI-Rathian-VM-Semantics-Handoff.md)、[完整性](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[已知问题](../Known-Issues.md)、[记录索引](README.md)。
