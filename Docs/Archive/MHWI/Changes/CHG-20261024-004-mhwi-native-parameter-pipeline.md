# CHG-20261024-004：原始参数批量提取与白名单导入

- 状态：completed（仅指此次批处理链路和21处支持属性；完整原作还原仍有明确未解项）。
- 日期：2026-10-24。
- 用户需求：原游戏解包参数批量实现，逐动画比较太慢；继续推进。
- 关联：[PLAN-20261024-003](../Plans/PLAN-20261024-003-mhwi-native-parameter-pipeline.md)、MHWI-008、R-COMBAT-009、R-TEST-003。
- Git：工作区变更，未提交；保留前序[防御/窗口/交接](CHG-20261024-003-mhwi-defense-routes-transfer.md)，不覆盖用户其他修改。

## 结果与修改

从用户原安装的chunk索引只读提取48项/约0.23MiB到独立 `ArtSource/ThirdParty/MHWLongSword/NativeParameters/`，含w03p、IK、动作树、碰撞/shell和相机参数。按最新chunk覆盖索引取原文件，不依赖用户启用的动作MOD，也不启动原作采样。

| 文件/入口 | 已实施 |
| --- | --- |
| [extract_native_longsword_params.py](../../Scripts/MHWI/extract_native_longsword_params.py) | 依据固定上游模板读取原始W03P，425字段/100具名，记录每项偏移/类型/值。读取公开资源格式并加解码往返，源文件不写。尾12零字节明确保留未解释，不虚构字段 |
| [native-parameter-sources.json](../../Tools/MHW/native-parameter-sources.json) | Synthlight/MHW-Editor commit b6ff379b13079a4abb99490590fb05dfe6851bbc，5个原作者文件URL/大小/SHA256；缓存缺失可显式fetch，拒绝覆盖不同缓存 |
| [extract_native_equipment_params.py](../../Scripts/MHWI/extract_native_equipment_params.py) | 四条IK的XFS成员按源名称读取，矩阵19/向量35宽度经完整嵌套边界和5982字节/件消费核对；其他资源保留目录/指纹。CMS确认为相机，不猜为挂点 |
| [build_native_action_database.py](../../Scripts/MHWI/build_native_action_database.py) | 一次合并425字段、164动作、90节点/307边/307条件树、299输入轨/961key、4条IK链。保留原树/运算码/mask/value/control/order，不依赖逐动画人工比较 |
| [author_native_parameters.py](../../Scripts/MHWI/author_native_parameters.py) | 原文件重新解码验证后，预览/备份并写正式 `/Game/MHWI/Data/DA_MHWI_LongSword`（UMHWIMovesetData）；11招17属性和4个全局属性，共21处。蒙太奇、武器事件、每条Route均保护读回 |
| `pie_behavior_corrections.py`、`pie_combat_fidelity.py` | 自动化回调加防重入封装，避免PIE启动/加载泵Slate时重复提交相同阶段；子类复用统一wrapper。该修改只在测试工具，不改游戏玩法 |

导入含气刃消耗、见切阈值/反击倍率与霸体、居合霸体/保持/回槽、登龙回槽、颜色持续/暂停衰减及回槽速率。原始分数槽→项目0–100槽显式转换，保留float32的7位有效十进制精度，避免15被转换成15.000001而误判阈值。既有校准值在此21处与原表一致，本次主要建立原文件作为可重建来源，不伪称21项全是新玩法变化。

## 实际验证

证据根：`Saved/MHWIImport/NativeParameterResearch-20261024/`。

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| `python Scripts/MHWI/build_native_action_database.py` | 通过，一次生成统一库；原文件/上游5文件指纹匹配 | native-action-database.json、native-action-database-summary.json |
| 原生参数加解码/字段重编码 | 源1584字节不变，加密往返一致；425字段连续1572字节重编码逐字节一致，12个尾零保留；7个公开数值交叉检查通过 | parameter-validation.json、longsword-native-parameters.json |
| 原始IK结构 | 四条全部嵌套record边界/完整文件消费通过，关节链6/7/8、10/11/12、14/15/16、18/19/20 | equipment-native-parameters.json |
| UE预览→保存→读回 | 21处支持属性保存，源sha一致；引用/事件/路由guard通过，差异均在float噪声内 | native-parameters-authored.json |
| `pie_combat_fidelity.run('resources')` | 12:25:17–12:25:51，615条断言通过（含重复采样），使用正式数据；消耗/低槽弱斩、见切命中与空挥、居合回槽/保色、到期截断、升色暂停 | Saved/MHWIImport/PIE-combat-fidelity-resources.json |
| 排查崩溃后恢复正常音频启动，同一资源套件复测 | 12:33:23–12:33:55再次615条通过；用于排除仅-nosound可运行的限制，不作为新增615个场景 | 同上最新报告；首次通过另存resources-nosound-pass.json |
| 恢复普通启动并从磁盘读回 | 正常带音频启动PID20328，MCP确认IntroCpp/5.8；原生导入目标值与已保存值匹配，PIE结束，脏包0 | native-parameters-disk-readback.json、最终MCP状态 |

首次资源回归在boot_start的PIE启动阶段引擎访问异常，没有生成完成报告，不能视为通过。原日志和CrashContext保留；栈出现重复Slate/Python启动路径，且前有音频设备超时。检查发现测试callback存在可重入入口，已统一加guard；临时-nosound重启后通过，恢复普通带音频启动后同一615检查再次通过。唯一原生崩溃根因仍未完全确认，登记R-TEST-003；未修改正式参数去迎合测试。

本轮不重编引擎/项目：没有在前序58.37秒成功构建后再改游戏C++，新增为读取/导入工具、测试防重入和文档。前序防御911检查是CHG-003的真实历史，不冒充本轮重跑。

## 未实现与回退

299条输入轨的value均位于对应control_l掩码内，但transition5的接受/执行/触发/缓存语义仍未知；307条件树保留原运算码，不凭数值猜AND/OR。23招148个取消窗仍是项目调校。匿名ActionParam块到具体动作的消费者/单位映射、居合0.4速度消费、原生shell延迟消费和IK求解器尚未迁移；这些原值已集中导出，不按浮点巧合硬套。

DA备份在同证据根的 `Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset`；仅恢复该文件可撤回本轮数值写入。其余新增工具/派生结果可独立保留，游戏安装、原LMT/blend/FBX未改。前序C++和三色Montage回退见CHG-003，不恢复整个工作区。

现状/操作入口见 [批处理说明](../Reference/MHWI-Native-Parameter-Pipeline.md)、[系统](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)。
