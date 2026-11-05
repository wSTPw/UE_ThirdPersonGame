# PLAN-20261022-001：MHWI太刀素材导入与动作模组

- 状态：in-progress。
- 日期：2026-10-22。
- 用户需求：在Content创建MHWI，导入已获取素材，在UE中还原太刀整体动作模组。
- 关联模块/问题：player-combat、ui-input、R-ANIM-003。
- 实施记录：制作中，实际结果另记CHG。

## 现状与目标

原版素材已在ArtSource/ThirdParty/MHWLongSword：164条太刀独立FBX、225骨猎人、太刀/刀鞘、482 Action Blender、71 PNG。现用Ninja/YBot四段连击不具备太刀独立招式派生、气刃槽/颜色、见切/居合反击或登龙规则。旧运行证据不能证明此次素材有效。

目标是在`/Game/MHWI`形成独立可玩的地面太刀角色和训练场，保留原项目入口与Ninja资产便于对照。不是只导入164段动画或循环播放展示。优先从原版FSM中的招式/动作编号建立映射；不能将未知编号写成已确认动作。

## 范围与验收标准

- 目录：Character、Weapons、Textures、Materials、Animations/LongSword、Animations/Common、Montages、Data、Blueprints、Maps。
- 导入同骨架角色/动画，保留源根轨迹；构建可移动的动画基底和全身Montage Slot，避免图层根运动缓存问题。
- 原生独立角色/动作数据实现：常规攻击与突刺/上挑/袈裟、气刃I–III/大回旋、槽消耗与白黄红等级/期限、见切成功判定及派生、命中后登龙七段、特殊纳刀/居合二连/居合气刃、翻滚/拔刀收刀/奔跑。
- 包含输入缓冲/取消、按动画位置处理跨帧命中窗口、窗口内目标去重、死亡/结束清理、输入和HUD。
- 训练图提供玩家出生、地面、靶子和攻击练习目标，便于用户自行体验；不宣称已复现攀爬/骑乘/斜坡/空战/怪物专属互动、完整原版数值与特效。
- 保留已获得的全部太刀动画；未完成精确语义/时序映射的条目作为源序号资产，不冒充已接入招式。

## 技术方案

新增`Source/IntroCpp/MHWI`中的Character、AnimInstance和Moveset DataAsset，拥有一个前台动作状态；不并行调用现有AMyPlayerCharacter的Actions。以Montage动画秒数驱动派生窗口、反击窗口和命中扫掠，移动基底采用明确速度来源，攻击由Montage Root Motion驱动。Action请求先判状态/资源再播放；失败、打断、死亡与EndPlay统一清理。组件、委托和资产引用按游戏线程及GC可见持有。

现有伤害直接走UAttributeComponent，因此增加通用IncomingDamageResponse接口，在正伤害扣血前询问Owner，支持翻滚与见切/居合的预伤害处理；未实现接口的旧Actor行为不变。原生MHWI HUD单独显示气刃/招式/输入。

导入与资产制作使用UE Python/MCP，脚本分批保存并记录日志，可恢复处理中断。用户2026-10-22随后明确取消此前禁止验证的要求；现按新增反射类型完整构建，完成实际PIE、动作派生/反击/多段命中和移动检查，失败继续修复。资产构造成功不能写成玩法验证通过。

## 接口与数据迁移

| 路径/接口 | 当前行为 | 目标 | 调用方影响/顺序 |
| --- | --- | --- | --- |
| `/Game/MHWI` | 尚不存在 | 独立太刀源资产与训练玩法 | 先导入骨架/模型，再动画、Montage、Data/BP/ABP和地图 |
| `IncomingDamageResponse.InterceptIncomingDamage` | 无预伤害接口 | true表示已处理并取消本次属性扣血 | 旧Actor不实现则保持原路径；新MHWI角色实现 |
| `AMHWICharacter` | 无 | 独立状态、输入、气刃与动作调度 | 训练GameMode默认Pawn；不迁移旧背包/角色蓝图父类 |
| `UMHWIMovesetData` | 无 | 招式配置、窗口、派生、资源成本和通用动作 | Data配置需绑定同一新骨架Montage |

## 实施步骤与依赖

1. 只读确认项目状态、UE连接和已有改动；记录方案。
2. 从原版FSM/MBD/LMT获取映射，制作缺少的通用移动FBX。
3. 导入MHWI资产并保留源序号；按原骨架构造蒙太奇。
4. 并行实现原生运行与HUD；集成伤害拦截；统一构建加载新类。
5. 制作ABP、MovesetData、角色/训练BP和地图，执行实际运行检查并修复问题。
6. 同步现状、接口、模块索引、问题和CHG，报告具体已实现/待完善范围。

## 验证计划与限制

| 场景 | 方法 | 预期/边界 |
| --- | --- | --- |
| 新反射类型可加载 | 最小Editor Target编译 | 仅证明构建可用，不证明招式运行正确 |
| 资源制作 | 导入/编译工具反馈、错误修复 | 记录制作结果，与运行证据分开 |
| 实际移动/派生/反击/登龙 | 新训练地图真实PIE及定向断言 | 本轮执行；只报告实际覆盖范围 |
| 文档 | 文档检查和限定路径diff检查 | 不触及现有二进制改动 |

## 风险与回退

源动画动作编号/原始根轨迹不等于项目派生窗口已正确；当前语义映射和数值须标明来源/推断。材质仅基础PBR，原游戏shader/全部特效未复现。玩法为本地单机，不构成网络复制支持。

回退移除新建MHWI资源与新增源码、通用伤害接口及其调用和相应文档；原有Ninja/菜单/关卡与用户工作区修改保留。先检查新目录有无用户追加修改，再做回退。

## 文档同步清单

Docs/Systems/MHWI-LongSword.md、Interfaces.md、Reference/modules.json、Known-Issues.md、Changes与Plans索引、ArtSource素材说明。
