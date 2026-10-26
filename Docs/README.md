# IntroCpp 技术文档

这套文档同时服务于开发者阅读和 AI 持续接手。2026-10-17 首次基线来自当前 C++、配置及连接中编辑器的只读核对。它描述项目现状，并为后续技术方案和改动留出固定记录位置。

## 快速阅读

| 想做什么 | 先读 |
| --- | --- |
| 接手项目、判断修改位置 | [项目架构](Architecture.md)、[模块索引 JSON](Reference/modules.json) |
| 修改物品、背包、快捷栏 | [背包系统](Systems/Inventory.md)、[接口契约](Interfaces.md) |
| 修改攻击、动画通知、敌人 | [战斗与 AI](Systems/Combat-AI.md) |
| 查询Ninja新动画替换、重定向、片段映射与窗口 | [Ninja动画配置](Systems/Ninja-Animation-Configuration.md)，2026-10-20制作，按用户要求未做完工后验证 |
| 查询MHW太刀、配套猎人模型及源素材转换 | [MHWI太刀训练模组](Systems/MHWI-LongSword.md)、[源素材](../ArtSource/ThirdParty/MHWLongSword/README.md)，独立地图与动作数据；验证见变更记录 |
| 查询MHWI武器独立动画、完整TIML/FSM和逐帧还原缺口 | [源保真调查](Reference/MHWI-Source-Fidelity-Audit.md)、[阶段方案](Plans/PLAN-20261023-001-mhwi-source-fidelity.md)；2026-10-24只读调查，未修改正式玩法 |
| 查看Content/MHWI原版还原进度与交接 | [逐项开发台账](Plans/MHWI-Restoration-Progress.md)、[B10三项开发交付](Reference/MHWI-R06-Remaining-Development.md)；[2026-10-26验收](Reference/MHWI-Acceptance-20261026.md)：6项历史已验证/1项开发完成/17项部分完成/10项取证/1项待开发；R06受击恢复回归待修；[32引用台账](Plans/MHWI-Connector-Progress.md)，B12历史编译成功，运行由用户操作 |
| 查询源采样修复、独立武器轨道及公开帧表校准 | [实施现状](Reference/MHWI-Native-Fidelity-Implementation.md)、[实施方案](Plans/PLAN-20261024-001-mhwi-native-fidelity-implementation.md)；36段平行库、27处Montage迁移，完整装配和取消仍有缺口 |
| 批量读取原游戏太刀参数/输入条件/IK，避免逐动画抄数值 | [原始参数批处理](Reference/MHWI-Native-Parameter-Pipeline.md)、[批处理方案](Plans/PLAN-20261024-003-mhwi-native-parameter-pipeline.md)；425字段/164动作/4条IK链，21处属性白名单导入 |
| 查询MHWI太刀原版动作、派生、转向和登龙依据 | [行为资料核对](Reference/MHWI-LongSword-Behavior-Research.md)、[实施方案](Plans/PLAN-20261022-002-mhwi-longsword-behavior.md)、[本轮实施记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)；七项核心行为及四套/低帧回归完成，精确标定边界单列 |
| 修改 Widget、输入、蓝图配置 | [UI 与资产配置](Systems/UI-Assets.md) |
| 编译、验证、使用 MCP | [开发流程](Development.md)、[UE-MCP 说明](../Tools/ue-mcp/README.md) |
| 实现新功能或修改接口 | [维护工作流](Maintenance.md)、[功能方案模板](Templates/Feature-Plan.md) |
| 查询历史修改和风险 | [变更记录](Changes/README.md)、[已知问题](Known-Issues.md)、[架构决策](Decisions/README.md) |
| 追溯引擎升级 | [UE 5.8 升级记录](UE58-Upgrade.md) |

推荐 AI 首次阅读顺序：根目录 [AGENTS.md](../AGENTS.md) → 本页 → Architecture → 相关系统 → Interfaces → Known-Issues。后续只读取任务涉及的部分。

## 文档职责

| 目录/文件 | 内容与更新时机 |
| --- | --- |
| `Architecture.md`、`Systems/`、`Interfaces.md` | 当前实现；代码、配置或接口行为改变时更新 |
| `Reference/modules.json` | AI 可解析的模块、源码入口、关联接口、验证入口 |
| [编辑器观测快照](Reference/editor-observations.json) | 有日期的资产核对证据；仅作当时事实，不代替后续实查 |
| [Plans/](Plans/README.md) | 开发前的方案；明确状态，禁止用计划替代现状 |
| [Changes/](Changes/README.md) | 每次实质变更的事实记录和验证证据 |
| [Decisions/](Decisions/README.md) | 跨系统、影响长期维护的取舍及原因 |
| [Templates/](Templates/README.md) | 可复制的方案、接口、变更、ADR 模板 |

## 事实与历史边界

- 实现与头文件注释不一致时，以 `.cpp` 和运行证据为准，并记录差异。
- 编辑器快照的 `missingProperties`、`suspect` 是查询工具元数据；对子类不适用的字段或重定向资源可能触发它们，不应直接等同于资产损坏。
- 旧文档 [背包设计](../Source/IntroCpp/InventorySystem_DesignDoc.md)、[背包使用说明](../Source/IntroCpp/InventorySystem_README.md)、[武器设计](../Source/IntroCpp/WeaponSystem_DesignDoc.md)、[连击设计](../Source/IntroCpp/MeleeComboSystem_DesignDoc.md)、[敌人设计](../Source/IntroCpp/EnemySystem_DesignDoc.md) 保留为历史参考；其中的待实现代码、联网和扩展设想不自动成为现有能力。
- 此次文档工作没有修改玩法代码或保存蓝图资产，也没有重跑此前升级阶段的编译和 PIE。历史验证在升级记录中，本次验证在文档基线变更记录中。
