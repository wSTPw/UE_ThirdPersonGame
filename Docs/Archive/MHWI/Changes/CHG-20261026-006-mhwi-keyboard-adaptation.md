# CHG-20261026-006：MHWI 原游戏 PC 键盘适配

- 状态：partial，键盘代码和静态检查完成；编译与PIE受本机引擎缺失阻塞
- 日期：2026-10-26
- 需求摘要：只做键盘适配，不改手柄组合逻辑和过渡动画。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261026-003](../Plans/PLAN-20261026-003-mhwi-keyboard-adaptation.md)；R01/R08；R-COMBAT-015的A03及键盘A02；MHWI-001/MHWI-013/MHWI-014
- Git：工作区变更，未提交

## 原因与结果

原实现把太刀命令绑为LMB/RMB/R/F/G/Q/Space/E/C/V，且键鼠和手柄共享Action与手势状态。开启`bOriginalInputPreset`会重解释键鼠，Held驱动的组合也允许无关键重发旧组合。

本批将PC核心操作改为LMB普攻、RMB突刺、Ctrl气刃、Ctrl+LMB登龙、Ctrl+RMB见切、LMB+RMB袈裟、Ctrl+Space特殊纳刀。R/F/G/Q/C不再作为这些动作的键盘直达键。E只在拔刀时请求纳刀，纳刀RMB不提交突刺；Shift在纳刀时冲刺、拔刀时经既有许可请求纳刀。V投射器连射保留。

键盘与手柄现在使用不同Action、Held和边沿。键盘组合要求本帧至少一个新成员边沿，一次手势只提交一个组合命令；无关键不会重发旧组合。重叠三键优先级SpecialSheathe > HelmBreaker > Foresight > FadeSlash仅作为项目适配，未声称原游戏全局仲裁。`bOriginalInputPreset`默认值、手柄映射和手柄A02均未改。

新增只读`GetInputRequestSerial/GetLastRequestedInput`诊断：每个`RequestInput`入口递增并记录命令，包括随后被拒绝的请求；不改变返回语义、出招许可、伤害或动画。HUD同步为实际PC提示。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.h` | 输入Action、设备Held/边沿、键盘方法与只读诊断 | 分离键盘和手柄所有权；声明键盘组合/Shift/移动采样入口 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | `BuildInputMapping`、`SetupPlayerInputComponent`、`KeyboardCommandStarted/Released`、`ResolveKeyboardFrameInputEdges`、`KeyboardSprintStarted`、`RequestInput` | 官方PC键位与组合、纳刀过滤、无关键重发保护、设备隔离；旧`MHWI_Command_*`保留给手柄和既有注入脚本 |
| `Source/IntroCpp/MHWIUI/MHWIHUD.cpp` | `DrawHUD`控制提示 | 移除旧快捷键提示，显示Ctrl组合、E收刀和Shift姿态行为 |
| `Scripts/MHWI/verify_keyboard_adaptation.py` | 静态检查与手势模型 | 校验映射、设备隔离、清理、HUD及按下/按住/松开/同帧释放等场景 |
| `Scripts/MHWI/pie_keyboard_adaptation.py` | 真实Enhanced Input回归 | 覆盖单键、组合、请求次数、无关键、预设隔离、E/RMB/Shift；需编译后的编辑器执行 |
| `Docs/Plans/PLAN-20261026-003-mhwi-keyboard-adaptation.md` | 本批方案 | 固定范围、来源边界、验收和回退 |
| `Docs/Systems/MHWI-LongSword.md`、`Docs/Interfaces.md`、`Docs/Plans/MHWI-Restoration-Progress.md` | 当前输入契约与台账 | 同步PC操作、MHWI-014、实际验证边界 |
| `Docs/Known-Issues.md`、`Docs/Reference/modules.json`、方案/变更索引 | R-COMBAT-015与模块入口 | 键盘子项关闭，手柄A02保留；登记测试与接口 |

没有修改Content、Config、DataAsset、Montage、Sequence、BlendSpace、蓝图或地图。没有处理过渡动画。`MHWICharacter.cpp/h`中此前B14未提交战斗改动保留，本批未回退或接管其验证结论。

## 原游戏PC操作来源

以下来源用于交叉核对原游戏默认PC操作，而不是把项目自定义键位当作原版：

1. 篝火营地《怪物猎人：世界》武器基础操作解说（https://gouhuo.qq.com/u/t/167376i）：太刀LMB/RMB/Ctrl、LMB+RMB、Ctrl+LMB、Ctrl+RMB及气刃连段。
2. SteamXO《魔物猎人世界冰原》太刀用法（https://www.steamxo.com/?p=1334740）：Ctrl+Space特殊纳刀、纳刀后的LMB/Ctrl居合、RMB持刀突刺及组合说明。
3. 3DM《冰原太刀特殊纳刀动作使用方法》（https://m.3dmgame.com/abcd/gl/3799481.html）：特殊纳刀R2+X对应Ctrl+Space。
4. IGN中国PC操作说明（http://cn.ign.com/monster-hunter-world-game/25843/feature/guai-wu-xi-ren-shi-jie-lun-ru-he-rang-jian-shu-cao-zuo-geng）：V按住/C切换投射器瞄准；本批不扩建完整瞄准系统。

这些是公开操作指南的交叉佐证，不冒充已重新运行原游戏或取得原生全局输入仲裁代码。全局优先级、跨帧缓存、精确取消窗继续保留原台账边界。

## 接口、事件与资源影响

- `RequestInput(EMHWIInput) -> bool`签名和返回语义不变；仅增加只读请求序号和最后命令快照。
- 新增MHWI-014输入契约。`MHWI_Command_*`名称与手柄路径保留，降低旧PIE/调试脚本回归；新键盘测试使用`MHWI_KeyboardCommand_*`和`MHWI_KeyboardSprint`。
- 纳刀E/RMB过滤只在键盘回调内生效，直接蓝图`RequestInput`和手柄行为不变。
- 无资源迁移、蓝图重编译、存档或网络复制影响。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `python -m py_compile Scripts/MHWI/verify_keyboard_adaptation.py Scripts/MHWI/pie_keyboard_adaptation.py` | 本机Python | 通过 | 命令输出 |
| `python Scripts/MHWI/verify_keyboard_adaptation.py` | 本机Python，无UE | **49项PASS、0失败**；含源码静态检查与独立手势模型，不是引擎行为验证 | `Saved/MHWIImport/KeyboardAdaptation-static.json` |
| `git diff --check`（本批代码/脚本/文档范围） | 本机Git | 通过 | 命令输出 |
| `python -m json.tool Docs/Reference/modules.json` | 本机Python | 通过，JSON合法 | `Docs/Reference/modules.json` |
| `python Scripts/Docs/check_docs.py` | 本机Python | **失败：12个既有缺失目标**；含上一批B14的`CHG-20261026-005`及11处历史Saved证据，输出无B15路径 | 命令输出；不作为本批通过项 |
| UBT `IntroCppEditor Win64 Development` | UE5.8 | **未执行**：本机只有C:盘，`E:\UE\UE_5.8`不可见，`C:\Program Files\Epic Games\UE_5.8`无引擎内容 | 环境检查记录 |
| `pie_keyboard_adaptation.py` | 编译后的Unreal Editor/PIE | **未执行**：无可用编辑器；脚本已创建，不能记为运行通过 | `Scripts/MHWI/pie_keyboard_adaptation.py` |

静态模型覆盖：六个单命令、四种同帧组合、修饰键按住、反向成员顺序、无关键、新Space优先特殊纳刀、释放、同帧按下即松开及三键项目优先级。它验证设计逻辑和源码结构，不证明Enhanced Input驱动投递、Montage表现或战斗许可。

## 风险、遗留与回退

- 手柄A02旧组合重发、RT+A、跨帧缓存和原生全局仲裁不在本批；R01/R08仍部分完成。
- 真实键盘按键投递、组合手感、动作资源/窗口拒绝后的表现、HUD实机布局及既有动作回归仍需编译后PIE。
- `MHWICharacter.cpp/h`同时含B14未提交改动。回退本批必须按B15差异逐段撤下，**不得整文件checkout**，否则会同时删除B14。脚本、HUD和文档按各自变更回退；无Content数据需要恢复。

## 已同步文档

[方案](../Plans/PLAN-20261026-003-mhwi-keyboard-adaptation.md)、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[总台账](../Plans/MHWI-Restoration-Progress.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[方案索引](../Plans/README.md)、[记录索引](README.md)及项目工作日志。
