# AI 持续维护工作流

目标是让下一次接手能够回答“系统现在怎么工作、这次为何这么改、哪些接口受影响、是否验证过”，而无需重新翻遍聊天历史。

## 一次任务的记录流程

1. **读取现状**：从 [入口](README.md) 和 [模块索引](Reference/modules.json) 找到系统页、源文件与接口 ID；检查用户已有工作区修改。
2. **建立范围**：简单修复直接写变更记录；涉及多个系统、存储语义、公共接口、资产迁移的功能先复制功能方案到 Plans。
3. **写清目标行为**：给出可观察的输入/结果、边界和验收标准。区分当前实现与目标方案。多个选择确有取舍时再建 ADR。
4. **实现并读回**：代码与资产改动互相核对；MCP 超时先查询实际状态，避免重复修改。接口变化要说明旧调用方和蓝图如何迁移。
5. **同步当前事实**：改接口就更新 Interfaces；改职责/调用链就更新系统页；改入口就更新 Architecture、modules.json；修复问题就更新 Known-Issues。
6. **留存实际结果**：新增 Changes 记录和索引，关联 Plan/ADR/问题 ID，填写验证与限制。只在验收达成时标为已完成。

## 稳定编号与状态

| 内容 | 文件名/编号 | 状态 |
| --- | --- | --- |
| 功能方案 | `PLAN-YYYYMMDD-NNN-主题.md` | draft / ready / implementing / implemented / superseded |
| 变更记录 | `CHG-YYYYMMDD-NNN-主题.md` | completed / partial / blocked；状态不能替代具体结果 |
| 架构决策 | `ADR-NNNN-主题.md` | proposed / accepted / superseded / rejected |
| 接口契约 | 当前使用 ITEM、INV、ATTR、COMBAT、AI、UI、PICKUP、EVT 前缀 | 在 Interfaces 中维护，修改沿用 ID，拆分/新增再分配新 ID |
| 问题 | `R-领域-NNN` | open / fixed / needs-verification |

创建记录前查看同类最大编号，不复用、不为了补历史虚构提交日期/commit。历史记录没有 commit 时写“工作区变更/未提交”。方案编号不代表自动获得实施授权，用户任务决定实际工作范围。

## 文档同步矩阵

| 改了什么 | 应更新 |
| --- | --- |
| 新增系统或责任迁移 | Architecture、系统页、modules.json、Changes；长期取舍另建 ADR |
| 函数签名/返回含义/事件参数 | Interfaces、受影响系统页、Changes、调用方与蓝图迁移说明 |
| 新 DataAsset 字段/ItemID | 系统页、资产说明、Changes；若写入已有资产，记录旧值/新值及默认值 |
| 输入映射/控件/Notify/类路径 | UI-Assets 或 Combat-AI、Changes、受影响资源验证 |
| 修复已有问题 | Known-Issues 状态、接口/现状页、Changes 与验证证据 |
| 仅实现细节优化 | Changes，按实际影响决定是否更新系统页；不要为无变化的接口改号 |
| 工具/构建配置 | Development、工具说明、Changes；工程级事实改变才更新 Architecture |

编辑器快照只在确实重新核对时更新 observed_on 与内容。读取了几个资产就记录几个，缺字段、未加载、redirector 和未验证信息要保留；不要用文件存在代替配置核对。

## 可直接给下一位 AI 的任务描述

> 阅读 AGENTS.md、Docs/README.md 和相关模块文档，完成以下需求：……。先核对源码与蓝图现状；为复杂改动建立功能方案；实现后同步接口、已知问题和变更记录，并报告实际验证结果。

不要求每次重新生成整套文档。让当前事实页保持准确，用追加的变更记录保留原因和历史，避免单一巨型日志或复制完整源码。

## 接口变更的最低信息

所有者、签名、输入范围/单位、返回值、失败时是否部分生效、状态归属、线程、事件顺序/次数、生命周期、蓝图/资产依赖、兼容与迁移、验证场景。字段不适用时说明原因；不能用“调用成功”掩盖“流程通过但无消耗”等既有语义。
