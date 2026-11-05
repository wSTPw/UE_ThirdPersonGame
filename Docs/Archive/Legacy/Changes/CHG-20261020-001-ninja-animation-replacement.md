# CHG-20261020-001：Ninja 动画替换

- 状态：completed（资源制作与保存完成；按用户要求未做完工后验证）
- 日期：2026-10-20
- 需求摘要：检查 UE MCP，将新 `/Game/ARPG_Ninja/Animations` 接入项目替换原动画，完工后禁止验证。
- 关联 PLAN / 问题 / 接口：[PLAN-20261020-001](../Plans/PLAN-20261020-001-ninja-animation-replacement.md)；R-ANIM-001、R-MM-001；ACTION-002/004、COMBAT-003/005。
- Git：工作区变更，未提交。

## 原因与结果

新动画绑定独立UE4 Mannequin骨架，正式角色使用YBot RootOn，无法直接赋给旧BlendSpace/Montage。因此新建独立IK资产、20条身体手指链与Ninja_APose，重定向26条Sequence到YBot；替换三个移动BlendSpace、四段剑攻击与火球手势。制作命令均返回保存成功；本轮没有完工后资产读回或运行检查。

新包没有同语义喝药资源，M_Drink继续使用原动画。未接入当前图的攀爬、闪避、跳跃等不新增玩法。角色模型、ABP原图及动作C++调度继续使用原入口；正式MM尚未接入。

## 修改清单

| 文件/资产完整路径 | 类/关键属性 | 原因与效果 |
| --- | --- | --- |
| `/Game/MyStuff/Animation/Ninja/Rig/IK_Ninja_Source` | IKRigDefinition，Pelvis、Root、20链 | 适配Ninja真实骨名 |
| `/Game/MyStuff/Animation/Ninja/Rig/IK_Ninja_YBot` | IKRigDefinition，Hips、Root、20链 | 独立目标Rig，保留旧IK_YBot |
| `/Game/MyStuff/Animation/Ninja/Rig/RT_NinjaToYBot` | IKRetargeter，Ninja_APose、Root Motion操作 | 同名链映射、姿态对齐、真实Root复制 |
| `/Game/MyStuff/Animation/Ninja/Sequences/*_YBot` | 26条AnimSequence | 3待机、18移动（8方向Walk/Run及无武器正向各2）、4攻击、1投掷；不覆盖源包 |
| `/Game/MyStuff/Model/Robot/BS_Move` | 27样本、0/175/525速度层 | 无武器Idle与正向，侧后方借用持武器方向资源 |
| `/Game/MyStuff/Model/Robot/BS_LongSwordMove` | 27样本、Idle1及八方向IPC | 新持剑移动 |
| `/Game/MyStuff/Model/Robot/BS_StaffMove` | 27样本、Idle2及八方向IPC | 原法杖分支使用新移动 |
| `/Game/MyStuff/Model/Robot/M_LongSwordAttack` | 4片段、Combo01..04、5命中、8窗口 | Attack Slot不变，约4.2秒；BlendIn=.08、BlendOut=.1 |
| `/Game/Data/ComboData/DA_LongSwordComboData` | Hits、SubHits、倍率、HitWindow | 命中1/1/2/2→2/1/1/1，保留各段累计配置伤害15/20/30/50 |
| `/Game/MyStuff/Model/Robot/M_Attack_Fireball` | Throw_A_YBot、UpperBodyOnly、唯一Fireball通知 | 左手投掷作为施法手势；提交11/60秒，BlendIn/Out=.1 |
| `/Game/Data/Items/Weapons/DA_WP_FireStaff` | WeaponFireSocketName | RightHand→LeftHand，对应左手投掷 |
| [NinjaReplacement-20261020.json](../../ArtSource/Animation/NinjaReplacement-20261020.json) | 完整制作映射 | 源/目标路径、链、81个移动样本、5命中、8窗口与数值 |

新增29个UE资产，覆盖7个既有UE资产。四攻击与投掷的输出副本配置enableRootMotion=false、forceRootLock=true、AnimFirstFrame；Root轨迹仍保留，适配当前胶囊移动逻辑。移动Direction轴由±175改为±180、8格并Wrap，速度轴0..525、3格。

## 接口、事件与资源影响

没有C++/反射签名变化。动作定义、武器和ABP仍引用原Montage/BlendSpace路径，但内容与时序已改变；五个MeleeHit、一个CastCommit和Chain/Cancel继续经原身份校验流程提交。首段两次子命中各0.5倍率；第二段20×1，第三段15×2，第四段25×2，按段保留旧累计配置伤害。原球扫、偏移、击退、MP成本和冷却不改；配置算术不代表实际目标扣血已验证。

完整时序与边界见 [Ninja现状](../Systems/Ninja-Animation-Configuration.md)。修改前已有源码、UI、插件、配置及动画变更：两个Walk资源的用户修改未覆盖；M_LongSwordAttack、FireStaff等按当前工作区版本备份，没有用Git旧版本替代。未修改第三方桥接代码或更新ue-mcp版本。

## MCP检查与制作证据

| 操作 | 时机与实际结果 | 证据 |
| --- | --- | --- |
| `project.get_status` | 修改前live、editorConnected=true、IntroCpp.uproject、engineAssociation=5.8；pluginStale=false、pluginBuildStale=false，协议plugin/client均2 | 本轮工具返回；客户端报告installed=1.4.7、可用1.4.8，本轮只检查未升级 |
| 读取骨架、ABP、网格、BS、Montage、ComboData与源姿态采样 | 制作前依赖定位；确认骨名、MyAnimInstance父类、原时序及新资源对应关系 | 本轮只读调用，写入日志中含旧值及rollback信息 |
| IK创建与配置 | 原生制作参数检查；首次Root操作骨名为空产生警告，显式填SourceRoot/TargetRoot/TargetPelvis后配置返回errors=[]、warnings=[] | `Saved/NinjaAnimationReplacement-20261020/authoring-log.json` |
| `animation.batch_retarget_animations` | 制作返回requested=26、createdCount=26，目标/映射链20/20、unmapped=[]，输出保存成功 | 同上，属于制作命令，不是完工后的动画验证 |
| BS/Montage/Notify/属性写入 | 保存返回成功；FireStaff与ComboData属性写入persisted=true | 同上及映射JSON |
| 构建、蓝图编译检查、PIE、自动化、资产读回、文档检查、diff检查 | **未执行：用户明确禁止完工后验证** | 无本轮验证日志 |

2026-10-19的编译、10项自动化和41项PIE断言只作为旧动作核心/旧动画基线的历史证据，不是本次新动画通过的依据。`action_refactor_pie.py`含旧6命中/固定时刻，本轮未执行，后续用于新资源前需适配。

## 风险、遗留与回退

- R-ANIM-001：新重定向姿态、握持、脚步速度、通知时机、连段、取消和左手火球出口均未做完工验证；通知帧来自源姿态采样与制作选择，需后续运行调校。
- R-MM-001：新包已提供；此次只接IPC与现有动作，Rootmotion版本的MM适用性、Schema/Database和正式图接入未完成。
- 7个覆盖资源备份在 `Saved/NinjaAnimationReplacement-20261020/Before/Content/...`；初始状态及首批6资产哈希在同目录git-status-before.txt、assets-before.json，FireStaff随后追加独立完整备份。Saved是本机临时目录，清理前保留所需备份。
- 回退：关闭编辑器，按相对路径恢复7个备份资产；通过编辑器按映射JSON准确列表移除本轮26条Sequence与3个IK资产，恢复本轮文档或新增更正记录；不执行整个工作区reset。

## 已同步文档

[Ninja配置](../Systems/Ninja-Animation-Configuration.md)、[战斗](../Systems/Combat-AI.md)、[UI与资产](../Systems/UI-Assets.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[开发流程](../Development.md)、[文档入口](../README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。按指令未运行检查器。
