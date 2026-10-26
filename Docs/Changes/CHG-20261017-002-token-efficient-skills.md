# CHG-20261017-002：项目省 Token 技能与 UE 精简路由

- 状态：completed
- 日期：2026-10-17
- 需求：为 IntroCpp 选择并落地省 Token 的 AI 技能；明确不安装 RTK。
- Git：工作区技能、工具与文档变更，未提交；既有 UE 升级、玩法资产及用户修改不受影响。

## 原因与结果

项目主要上下文成本来自跨系统重复探索和大型 Unreal 构建日志。新增项目专用上下文路由与日志诊断技能，优先选择相关模块、保存完整日志并只返回有界错误片段。

安装 6 个与当前系统直接相关的 UE 5.8 技能后，检查发现其活动正文各约 28–32 KB。为避免触发时一次加载大量通用参考，活动 `SKILL.md` 改成约 0.8–0.9 KB 的项目路由层；原始上游正文保留为同目录 `UPSTREAM_SKILL.md`，仅在具体引擎 API 不确定时读取。RTK、Caveman 与 TOMC 均未安装。

## 修改清单

| 范围 | 内容 |
| --- | --- |
| Tools/AgentSkills/introcpp-context-router | 根据 `Docs/Reference/modules.json` 返回最多 3 个相关模块、文档、源码、接口和资产根 |
| Tools/AgentSkills/ue-build-log-triage | 对 UBT/UHT/MSVC/链接/启动/PIE 日志提取有界错误组，报告哈希与完整日志路径 |
| Tools/AgentSkills/LeanUpstream | 6 个 UE 5.8 技能的短活动路由源 |
| .agents/skills | 上述 8 个活动技能及第三方完整按需参考 |
| Docs/Development.md | 增加技能维护入口 |

未修改 C++、配置、蓝图、DataAsset、关卡或插件运行行为。

## 实际验证

| 检查 | 实际结果 / 证据 |
| --- | --- |
| 上下文路由脚本 | 中文快捷栏/ItemID 请求正确返回 event-bus、inventory、item-data；StateTree/MyLevel 请求返回 enemy-ai、entry 等相关模块 |
| 日志诊断脚本失败样例 | 正确识别首个 `error C2065`、后续 UBT 汇总错误、warning 数量、原日志 SHA-256 与路径 |
| 日志诊断脚本成功样例 | 对既有 401 行 MCP 编译日志报告 0 个错误匹配、4 个 warning，并保留 `Result: Succeeded` |
| 活动 UE 技能体积 | 6 个精简活动正文各 16 行、约 0.8–0.9 KB；完整上游正文仍可恢复读取 |
| Skill 结构校验 | skill-creator quick validator 对 8 个活动技能全部通过 |
| 文档检查 | `python Scripts/Docs/check_docs.py` 通过 |
| `git diff --check` | 通过；仅报告既有 LF/CRLF 转换提示 |
| C++ 编译 / PIE | 未执行；本次没有修改运行时代码或资产 |

## 使用与回退

新会话会发现项目 `.agents/skills/` 下的技能。上下文路由和日志诊断源文件维护在 `Tools/AgentSkills/`，修改后再同步活动副本。UE 技能通常先读项目现状文档；只有精确 API 存疑时才读取 `UPSTREAM_SKILL.md`。

回退时移除本次新增的 8 个活动技能与 `Tools/AgentSkills/`，并撤销本文、索引和 Development 入口。不要删除原有 `skill-creator`，也不要恢复或覆盖其他未提交修改。

## 已同步文档

[开发与验证](../Development.md)、[技能源说明](../../Tools/AgentSkills/README.md)、[修改记录索引](README.md)。
