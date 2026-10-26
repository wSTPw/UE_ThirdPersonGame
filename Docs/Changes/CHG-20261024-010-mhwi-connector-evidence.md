# CHG-20261024-010：B04连接入帧原表及逐条取证

- 状态：partial（数据读取及既有129参数已接入；新增连接播放0条）
- 日期：2026-10-24
- 需求：优先R06，确认连接退出和主段入帧，不猜参数，每条同步状态。
- 关联：[PLAN-008](../Plans/PLAN-20261024-008-mhwi-connector-evidence.md)、R06/R32/R33；工作区变更，未提交。

## 原因与结果

此前调查只检查FSM/TIML，漏查配套MBD，因此“主段入帧无法从数据查到”的表述过宽。本批从原`w03_00.mbd`读出按前片段匹配的startFrame字段：164条目标记录、317个匹配块，覆盖30连接节点的32次片段引用。源MBD与独立chunk提取副本SHA一致；字段布局来自固定指纹FreeHK原作者`struct/mbd.py`，不执行该第三方模块。

已有129→101的48帧由原MBD直接提供，原字节偏移4102。`author_behavior_corrections.ROLL_STEP_ENTRY_FRAME`现从固定源读取；端点拟合仅为诊断，不能再覆盖原值。正式Montage原本就是48，本批没有改变播放行为。

**连接退出帧仍未查清，新增正式连接0条，R06没有完成。** 32次引用的TIML均没有显式ActionPhase/LinkMotionPhase键；FSM空子列表/mOperator0出口不足以给出原生进程完成时刻。原LMT/TIML长度及MBD的插值/重叠字段不直接当成退出。60/76的Phase1选择、时间映射和混合消费者也未解码。原保护EXE的既有只读证据不能作为已取得消费者的证明；未运行原游戏。

## 逐条状态与新增发现

全部32次引用分别记录在[连接台账MD](../Plans/MHWI-Connector-Progress.md)及[CSV](../Plans/MHWI-Connector-Progress.csv)，含入口节点、连接片段、FSM目标、MBD目标、startFrame偏移、退出状态、实施和下一步。

- 30次与项目当前目标映射一致，2次冲突：FSM节点80/81经361/362时，原MBD分别指定127@22/128@24，项目现有左右映射则相反。先保留冲突，不以原表单条记录直接互换用户已识别的左右动作。
- 118除了目标105@14，还有112@14；项目插入突刺复用105不是原生消费者证明。完整候选记录已保存。
- 已有129退出29/60仍是项目适配；本批只确认MBD入口字段48，不将原生完整接续写成已验证。

## 修改清单

| 文件/符号 | 修改与影响 |
| --- | --- |
| [native_connector_source.py](../../Scripts/MHWI/native_connector_source.py) | 标准库MBD21读取/重编码、原字节偏移、歧义拒绝；直接重读原FSM/LMT，保留全部TIML和条件，30节点32引用逐条关联 |
| [native-connector-sources.json](../../Tools/MHW/native-connector-sources.json) | 固定MBD/FSM/LMT、既有映射与FreeHK布局指纹；源变化拒绝消费 |
| [author_behavior_corrections.py](../../Scripts/MHWI/author_behavior_corrections.py) | 129主段48帧制作参数从原文件读取；退出/混合未改 |
| [audit_behavior_links.py](../../Scripts/MHWI/audit_behavior_links.py) | 原MBD决定入口，姿态误差不再选帧；诊断报告明确消费者边界 |
| [verify_connector_source.py](../../Scripts/MHWI/verify_connector_source.py) | 原字节往返、独立偏移锚点、截断/损坏和多匹配拒绝、引用数量和资产哈希保护 |

没有C++/反射签名改变、没有保存蓝图、DA、Montage或Sequence；349个Content/MHWI文件均不变。不添加未知时序或新连接片段。制作脚本依赖本地固定源存在；源丢失/变化时明确报错，不能降级回猜测常量。

## 实际验证

证据目录`Saved/MHWIRestoration/B04-20261024/`。

| 检查/命令 | 实际结果 | 证据 |
| --- | --- | --- |
| `python Scripts/MHWI/verify_connector_source.py` | 16499字节全量重编码一致；164/317计数；3个独立偏移锚点通过；5种损坏/截断拒绝；170←308多候选拒绝；30/32关联和2冲突检查通过 | `verification.json`、`mbd-decoded.json`、`connector-evidence.json` |
| MCP `editor.run_python_file`，本批readback.py | 实际`/Game/MHWI/Montages/M_RollStepSlash`类AnimMontage，129+101，主段start0.800000012秒，与原48帧一致；未保存资产 | `editor-readback.json` |
| `python Scripts/MHWI/audit_behavior_links.py` | 完成；没有bpy，不是本轮新源姿态采样；旧采样只作诊断，48从原MBD读取 | `Saved/MHWIImport/DSH-20261022/behavior-link-audit.json` |
| tree配套检查 | 树MBD四个默认块读取；AT version7仅核对头/大小/指纹，未解码其消费者，不以无字符串推导无时序 | `tree-inspection.json` |
| 原资产哈希与语法 | 349文件均不变；4相关脚本语法通过 | `before-assets.json`、`verification.json` |
| 文档/差异 | 最终结果写本批验证报告；只运行文档及差异检查 | `verification.json` |

开发中的全量映射预检曾拒绝无关65四色变体；收窄到真实目标节点后继续。源目标不一致和118多目标也先被拒绝，随后显式保存候选与冲突，未静默选首条，未改资产。

没有编译和PIE：无C++/运行行为变更，静态与实际资产只读核对足够本批参数出处改动；新连接实际播放、根位移、低帧、取消/伤害时钟及原作观测留待确认退出后。网络公开搜索未取得结果，已终止，不作本批在线佐证。

## 遗留与回退

后续优先31/40/33/36/37/39，入口表已解析；下一硬缺口是LinkMotion进程完成与阶段选择。回退恢复本批`Backup/`中的制作/审计脚本，移除两个新增脚本及来源清单；没有需要恢复的Content资产。文档保留此次证据，后续另建CHG记录消费者结论。

## 文档同步

[逐连接台账](../Plans/MHWI-Connector-Progress.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)及CSV、[系统页](../Systems/MHWI-LongSword.md)、[已知问题](../Known-Issues.md)、[开发流程](../Development.md)、[模块索引](../Reference/modules.json)及文档/计划/变更入口。旧调查页保留历史并追加更正。
