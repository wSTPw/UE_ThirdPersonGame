# CHG-20261022-002：MHWI 太刀素材导入与独立训练模组

- 状态：partial，功能与运行回归已通过，视觉收尾中。
- 日期：2026-10-22。
- 需求：在 Content/MHWI 导入原版猎人、太刀及动画，制作可操作的地面太刀动作模组。
- 关联：[PLAN-20261022-001](../Plans/PLAN-20261022-001-mhwi-longsword-module.md)、R-ANIM-003、DAMAGE-001、MHWI-001..005。
- Git：工作区变更，未提交。

## 原因与结果

此前只有 Blender/FBX 源包，现新增独立 `/Game/MHWI` 角色、动作数据、ABP、HUD 和训练图，包含普通连段、气刃升色、见切、居合与命中后登龙。用户取消“完工后禁止验证”的旧限制，本轮完成完整 Editor Target 构建、真实 PIE 和重启后资产持久化检查。原 Ninja/菜单/默认图保留，不把旧角色的测试算到新模组。

## 修改清单

| 文件/资产完整路径 | 关键实现与效果 |
| --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | 独立前台动作、Enhanced Input、根运动、蒙太奇位置窗口、槽/颜色、反击、特殊纳刀定格、登龙标记与延迟七段、清理 |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h`、`MHWIAnimInstance.h/.cpp` | 数据驱动派生/窗口/变体、源速度曲线适配、真实速度/姿态到动画图 |
| `Source/IntroCpp/MHWI/MHWITrainingTarget.h/.cpp` | 三个可扣血练习目标，一个定时预警攻击 |
| `Source/IntroCpp/MHWIUI/MHWIHUD.h/.cpp` | HP、气刃槽/颜色/期限、当前动作及控制提示 |
| `Source/IntroCpp/IncomingDamageResponse.h`、`AttributeComponent.cpp` | 属性扣血前的可选预伤害接口；未实现接口的旧 Owner 沿原路径 |
| `/Game/MHWI/Character`、`Weapons`、`Animations`、`Textures`、`Materials` | 猎人、剑/刀鞘、164 太刀+5 通用动画、71 贴图、18 基础材质实例；225 骨统一猎人骨架 |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter`、`BP_MHWI_Hunter`、`BP_MHWI_TrainingGameMode` | 原生父类、速度 BlendSpace/纳拔刀混合/DefaultSlot、默认 Pawn/HUD |
| `/Game/MHWI/Data/DA_MHWI_LongSword`、`/Game/MHWI/Montages/M_*` | 29 招式定义及对应根运动 Montage、居合颜色变体 |
| `/Game/MHWI/Maps/L_MHWI_Training` | 独立训练场入口，地面/光照/出生点/练习目标 |
| `Scripts/MHWI` | 源映射、武器证据、通用 FBX 导出、分批导入/制作与本轮实际运行检查 |

## 接口、事件与资产影响

新接口详见 [契约](../Interfaces.md)。RequestInput 活跃时返回 true 仅表示缓冲；StartMove 是空闲启动入口。单一动作拥有执行序号和 Montage 实例身份；命中窗口按跨帧区间处理。槽收益和升色基于真实属性扣血。弱目标标记只沿合法登龙链转移，中断/死亡/退出清除。纳刀和拔刀翻滚分开选动画。

新角色不接旧背包、物品或 Ninja 动作组件。此轮修改 AttributeComponent 的预伤害入口叠加在既有动作重构修改上，没有回退用户已有更改。`Plugins/UE_MCP_Bridge`、`Tools/ue-mcp` 为现有第三方工具，本轮业务代码放在项目 Source；未为此功能修改第三方工具实现。

## 实际验证与修复

| 检查/命令 | 环境与实际结果 | 证据 |
| --- | --- | --- |
| `Build.bat IntroCppEditor Win64 Development -Project=... -WaitMutex -NoHotReloadFromIDE` | 关闭编辑器后完整构建；首轮成功 70.16 秒，登龙修复后成功 75.22 秒 | `Saved/MHWIImport/Build.log`、`Build-helm-fix.log` |
| 完整重启后 `verify_assets.py` | 10 项通过；19 槽材质、参考根锁定、纳拔刀姿态与三种蓝图生成类持久化 | `asset-persistence.json` |
| `pie_smoke.py` | 13 项通过；真实受控角色移动约 197.8 cm、动画速度、拔刀斩伤害 26、回槽与根运动约 133.93 cm | `PIE-smoke.json` |
| `pie_moveset.py` | 实际 Enhanced Input、翻滚免伤/窗外扣血、三次见切升白黄红、完整气刃 I→II→III→大回旋六命中共 158.4、居合双命中/反击保级/失败降级、登龙全阶段/七段 154 伤害/单次降级/恢复移动、死亡清理均通过 | `PIE-moveset.json` |

构建最初被沙盒阻止写入 Engine/Source，使用授权的完整构建后成功；不将该错误误归因于项目路径。自动化脚本初版遇到 Python 内部/受保护 API、InputActionValue 不透明结构体、IsAlive 属性绑定等问题，改用可用的对象枚举、向量输入注入和属性读取。

实际玩法检查发现并修复：登龙落在靶子顶部时，按角色高度扫掠导致七段漏伤，改为对突刺命中目标结算延迟伤害；画面检查发现第一帧锁根去掉导入参考根旋转，全部 169 条改为 REF_POSE；SkeletalMaterial 就地修改未标脏，强制保存网格并完整重启读回。测试连续根运动曾走出训练场边界，脚本在各组空闲间归位，保留动作过程真实位移。

## 边界、遗留与回退

源 TIML 碰撞启停有证据；招式语义部分由姿态推断。取消、反击、无敌帧、伤害和资源是项目适配参数；源 MotionSpeed 用线性插值，未宣称原版逐帧一致。普通命中为前向球扫扇区，未制作刀刃逐骨轨迹。完整原版 shader/特效/音效、骑乘/斜坡/空战/飞翔爪/怪物专属交互、联网没有还原。

回退前先确认 MHWI 目录没有用户追加编辑；移除本轮新资产/源码，撤回 AttributeComponent 中接口调用和 include，保留旧动作/背包修改。原素材转换工具和素材采集记录可单独保留。不能整文件回退 AttributeComponent 或批量还原全部工作区。

## 已同步文档

[当前系统](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[开发验证](../Development.md)、[问题](../Known-Issues.md)、[素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md)、[工具说明](../../Tools/MHW/README.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。

后续：用户优先要求处理武器与刀鞘错位，独立完成结果见 [CHG-20261022-003](CHG-20261022-003-mhwi-weapon-attachment.md)。视觉检查期间曾出现一次 D3D12/SlateRHIRenderer 访问异常，完整日志保存在 `Saved/MHWIImport/Editor-visual-crash.log`；没有证据确定为玩法代码问题，也没有宣称根因已解决。恢复编辑器后再次移动/攻击冒烟通过，位置修正另完成新 PIE 挂接验证。
