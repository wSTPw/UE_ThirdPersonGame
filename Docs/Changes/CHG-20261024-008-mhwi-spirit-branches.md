# CHG-20261024-008：B02原生气刃弱强分支与接续修复

- 状态：completed，本批限定范围；完整原版还原仍进行中。
- 日期：2026-10-24。
- 关联：[PLAN-20261024-006](../Plans/PLAN-20261024-006-mhwi-source-branches.md)、[开发台账](../Plans/MHWI-Restoration-Progress.md)、R02/R12/R15/R34/R35、MHWI-011。
- Git：工作区变更，未提交；未重置或清理用户既有修改。

## 原因与结果

原COL与FSM补证后，纠正B01把气刃踏步强化成本当作所有版本启动门槛的适配。B01的成本20/回槽10读数仍正确，但低槽拒绝不再是当前规则；历史报告保持原义，不改写旧测试结果。

| 修改项 | 本批实际行为 | 来源与边界 |
| --- | --- | --- |
| 气刃踏步弱/强 | 不足20允许18弱斩且费用0；够20使用28并扣20；回槽10 | COL记录6/7的基础/条件替换/无槽身份，W03P强化cost；既有弱斩消费者复用 |
| 气刃踏步A/B | 都接`SpiritComboRisingSlash`，保留气刃续段身份 | 原node6→38，同一个A/B条件；新增B复制现有A适配窗口，不声称是原版精确帧 |
| 插入上挑R | 原序优先有完整槽资格的III，不够则接I；I保留已有弱斩规则 | 原node38条件R→LinkMotion→III在先，R→I在后；检查读取目标定义成本，没有另写阈值 |
| 插入突刺B | 删除项目自定B→上挑；A→上挑及R→II保留 | 原node23有A→3及有槽R→II，未保留项目复制出的B循环 |
| 重建兼容 | 两处基础制作尾处理接入B02；B01/窗口/参数入口预览兼容，重复导入不重复路由 | 未重做全部资产；复杂重建/边界矩阵留下一步 |

后备I原有14/26弱强数值也从COL记录15/16重建，防止基础制作重置弱斩而令低槽后备再次失效。正式DA原有I已正确，因此此补强在当前DA上没有新增差异；复制结构模拟过时基础字段后可恢复，未保存探针资产。

## 证据与数值来源

`native_spirit_branches.py`每次直接读取固定指纹原COL/W03P/FSM，输出源记录、字段偏移、完整条件树及原边顺序到`Saved/MHWIRestoration/B02-20261024/native-spirit-plan.json`。所有生产数值18/28/20/10取自原文件；弱倍率按原始18/28计算，不使用手工调值。

弱/强消费语义另由此前保留的MoonBunnie/Deathcream[原作攻击表](https://docs.google.com/spreadsheets/d/e/2PACX-1vTEYb4wGpijtIpFVopiYl1V83m48d7g1AHmTwOBKJ5RXdlz1sfxCyEmnhbgHLWQsGiXnodyBsUlPzc3/pubhtml/sheet?headers=false&gid=362236353)快照佐证：该动作尝试消耗20%练气以提高基础攻击值，与原无槽记录一致。本轮在线复查不可达，未伪称重新取得网页；原缓存JSON/HTML哈希和短注记固定在`Tools/MHW/native-spirit-branch-evidence.json`。该JSON只保留语义证据，生产数值不从其中读取。

## 修改落点与接口

| 文件/资产 | 符号或属性 | 变化 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h` | `FMHWIRoute.RequireFullSpiritCost` | 新增可选布尔，默认false兼容所有旧路由 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | `ResolveInput` | 启用条件时比较目标SpiritCost；不满足继续扫描后续同输入路由；显式输入仍不能被通用取消绕过 |
| `Scripts/MHWI/native_spirit_branches.py` | `build_plan/run` | 原值及有序条件取证，拒绝源/语义指纹变化 |
| `Scripts/MHWI/author_spirit_branches.py` | `apply_to_copies/run` | 复制结构预览、幂等、全字段保护、正式DA保存/读回 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | 三招弱强/Routes | 已保存；仍32定义，现149路由，Montage及时间轴未改 |
| `Scripts/MHWI/author_assets.py` | 两处基础制作尾处理 | 接B02，防修正被基础生成覆盖 |
| `Scripts/MHWI/author_native_parameters.py`、`author_transition_calibration.py` | 路由保护/反射检查 | 保留新资源条件；窗口配置新增同条件B、删除自定插入B，现147规则 |
| `Scripts/MHWI/pie_reference_basics.py` | 历史边界夹具后续预期 | 改为低槽弱斩允许；历史B01报告未改，本轮未重跑该长套件 |
| `Scripts/MHWI/pie_spirit_branches.py` | 短冒烟 | 只检查本批生产Actor资源/动作身份，不扩复杂套件 |

新反射字段已完整构建后才写DA。没有修改动画、刀鞘/装备、地图、蓝图磁盘文件、输入缓存或时序数值；只复制新增同条件路线所需的已有适配窗口。复杂原版窗口/连接/消费者仍有独立开放项。

## 本轮实际验证

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| 完整UHT/C++构建 | Succeeded，35.29秒；新路由字段与ResolveInput成功编译 | `Saved/MHWIRestoration/B02-20261024/build.log` |
| 原文件取证/语法 | 原四文件/语义证据指纹匹配，条件与有序边断言通过；相关Python语法通过 | `native-spirit-plan.json`、收尾报告 |
| 复制预览→保存→重复应用 | 幂等、全部非白名单字段保护与读回通过；仅正式DA磁盘变化 | `preview.json`、`authored.json`、`apply-result.json` |
| 其他制作入口兼容预览 | B01基础导入、147窗口规则、原参数18+4预览通过，未额外保存 | `apply-result.json` |
| 真实短PIE | passed，18.063秒，10个短观察案例；弱18/强28和费用、A/B接上挑、R的I/III分支、自定B出口删除通过 | `PIE-short-smoke.json` |
| 复制结构重建保护 | 已正确的正式DA无新差异；仅在副本模拟弱I被重置后从源恢复成功，未保存副本 | `rebuild-copy-check.json` |
| 文档/diff/最终资产范围 | 由最终收尾报告记录实际结果 | `final-verification.json` |

除第一行构建日志外，表中相对证据均在`Saved/MHWIRestoration/B02-20261024/`。没有重跑全套方向/空中/生命周期，没有复杂地形/多部位/技能矩阵、低帧扫描、长录像或原作进程采集；按用户要求留下一步。

## 遗留与回退

R34/R35关闭的是当前适配器的目标身份、条件及原序分支；精确窗口R07和连接R06仍开放。见切缺失出口、十秒保护、Q衰减、shell及完整主角操作没有在本批完成，不猜参数。

本批改动前字节和哈希保存在`Saved/MHWIRestoration/B02-20261024/Backup/`及`before.json`。回退只恢复指定文件并重编译，保留用户后续修改，不整体checkout或重置项目。原安装及原始源数据未改。

## 已同步

[台账](../Plans/MHWI-Restoration-Progress.md)与CSV、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[已知问题](../Known-Issues.md)、[本批方案](../Plans/PLAN-20261024-006-mhwi-source-branches.md)、模块索引及记录/方案索引。
