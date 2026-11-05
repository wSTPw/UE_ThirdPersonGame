# IntroCpp 技术文档

服务于开发者阅读和 AI 接手。描述**项目现状**，并为后续改动留固定记录位置。

## 任务路由

| 想做什么 | 先读 |
| --- | --- |
| 接手项目、判断修改位置 | [项目架构](Architecture.md)、[模块索引 JSON](Reference/modules.json) |
| **看 MHWI 现在做到哪一步** | [当前开发计划](Plans/MHWI-Current.md) → 对应系统页 |
| 改太刀（攻击/派生/数值/挂接） | [太刀训练模组](Systems/MHWI-LongSword.md)、[太刀取证总账](Reference/MHWI-LongSword-Evidence.md) |
| 做雌火龙（AI/动画/战斗） | [MHWI 雌火龙](Systems/MHWI-Rathian.md)、[雌火龙取证总账](Reference/MHWI-Rathian-Evidence.md) |
| 解包数据、跑解析、查素材 | [解包数据与工具链](Systems/MHWI-Unpack-Data.md)、[MHW 工具说明](../Tools/MHW/README.md) |
| 修改物品、背包、快捷栏 | [背包系统](Systems/Inventory.md)、[接口契约](Interfaces.md) |
| 修改攻击、动画通知、敌人 | [战斗与 AI](Systems/Combat-AI.md) |
| 查 Ninja 动画替换与重定向 | [Ninja 动画配置](Systems/Ninja-Animation-Configuration.md) |
| 查 MHWI 接口签名与语义 | [Interfaces](Interfaces.md) MHWI-001..015 |
| 修改 Widget、输入、蓝图配置 | [UI 与资产配置](Systems/UI-Assets.md) |
| 编译、验证、使用 MCP | [开发流程](Development.md)、[UE-MCP 说明](../Tools/ue-mcp/README.md) |
| 实现新功能或改接口 | [维护工作流](Maintenance.md)、[功能方案模板](Templates/Feature-Plan.md) |
| 查已知问题与风险 | [已知问题](Known-Issues.md) |
| 查最近改动 | [变更记录索引](Changes/README.md) |
| 查架构决策 | [决策记录](Decisions/README.md) |
| 追溯引擎升级 | [UE 5.8 升级记录](UE58-Upgrade.md) |
| 查已归档的历史批次 | [Archive/MHWI](Archive/MHWI/README.md)（**只读，不作现状依据**） |

AI 首次阅读顺序：根目录 [AGENTS.md](../AGENTS.md) → 本页 → Architecture → 相关系统页 → Interfaces → Known-Issues。之后只读任务涉及的部分。

## 文档职责

| 目录/文件 | 内容与更新时机 |
| --- | --- |
| `Architecture.md`、`Systems/`、`Interfaces.md` | **当前实现**。代码、配置或接口行为改变时更新 |
| `Reference/` | 取证结论与模块清单。**只写结论和未解项**，不写推导过程 |
| `Reference/modules.json` | AI 可解析的模块、源码入口、接口、验证入口 |
| `Reference/editor-observations.json` | 有日期的资产核对证据，仅作当时事实 |
| `Plans/` | 活跃方案。MHWI 只保留 [MHWI-Current](Plans/MHWI-Current.md) |
| `Changes/` | 每次实质变更的事实记录与验证证据 |
| `Decisions/` | 跨系统、影响长期维护的取舍 |
| `Templates/` | 可复制的方案、接口、变更、ADR 模板 |
| `Archive/` | **冻结的历史**。不再维护内部链接，不作为现状依据 |

## 事实与历史边界

- 实现与头文件注释不一致时，以 `.cpp` 和运行证据为准，并记录差异。
- 编辑器快照的 `missingProperties`/`suspect` 是查询工具元数据；对子类不适用的字段或重定向资源可能触发，不等于资产损坏。
- 旧设计稿（[背包](../Source/IntroCpp/InventorySystem_DesignDoc.md)、[武器](../Source/IntroCpp/WeaponSystem_DesignDoc.md)、[连击](../Source/IntroCpp/MeleeComboSystem_DesignDoc.md)、[敌人](../Source/IntroCpp/EnemySystem_DesignDoc.md)）保留为历史参考；其中的待实现代码、联网和扩展设想不自动成为现有能力。
- 归档区的文档保留其写作时点的事实。**引用归档内容时必须核对当前源码**。

## 文档维护规则

- 现状页只写"现在是什么"，不写"某批次做了什么"。批次过程写进 `Changes/`。
- 取证页只写"已证什么、还没证什么、证据在哪"，不复制推导过程。
- 报告被后续结论推翻时，**直接修正主文档并留一条 `Changes/`**，不要把新旧结论并列堆在同一页。
- 改完文档运行 `python Scripts/Docs/check_docs.py` 和 `git diff --check`。
