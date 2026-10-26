# UI、输入与蓝图资产契约

UI 的可视布局、Class Defaults 与动画配置保存在二进制资产中。以下 C++ 符号、控件名称和 `/Game/` 路径是开发接口；修改时同时检查实际资产。

## 已核实资产入口

| 用途 | 当前路径 |
| --- | --- |
| 当前开始标题 UI 类 | `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy`，父类 `UUW_MainHUD` |
| 保留的像素菜单 UI 类 | `/Game/MyStuff/MyUI/UW_MainHUD`，父类 `UUW_MainHUD` |
| 暗黑标题页纹理 | `/Game/MyStuff/MyUI/DarkFantasyTitle/Textures` |
| 开始菜单像素纹理 | `/Game/MyStuff/MyUI/MainMenu/Textures` |
| 自定义玩家蓝图 | `/Game/MyStuff/BP/BP_MyPlayer`，父类 MyPlayerCharacter |
| 玩家输入映射 | `/Game/MyStuff/MyInput/IMC_MyPlayer` |
| 背包 UI 类 | `/Game/MyStuff/MyUI/UW_InventoryUI` |
| 状态栏 UI 类 | `/Game/MyStuff/MyUI/WB_StatusBar` |
| 快捷槽 UI 资产 | `/Game/MyStuff/MyUI/WBP_QuickSlot` |
| 背包槽 UI 资产 | `/Game/MyStuff/MyUI/UW_InventorySlot_BP` |
| 动画蓝图资源 | `/Game/MyStuff/Model/Robot/ABP_Move`；2026-10-20制作前读取父类为MyAnimInstance、骨架Y_Bot_Skeleton_RootOn；图保留原三个移动分支及Slot分层 |
| 长剑连击数据 | `/Game/Data/ComboData/DA_LongSwordComboData` |

玩家蓝图 CDO 已核实 InventoryUIClass、StatusBarUIClass 与 InputMapping 连接到上表。快捷槽/背包槽类、ABP、Montage 的所有实际绑定未逐一检查；不能仅因资产文件存在就标记验证通过。旧 `/Game/MyStuff/BP_MyPlayer` 为 redirector，不进行无关的自动重定向清理。

## UMG BindWidget 名称

| C++ Widget | 必需 BindWidget | BindWidgetOptional |
| --- | --- | --- |
| [UUW_MainHUD](../../Source/IntroCpp/UW_MainHUD.h) | Button_StartGame、Button_1、Button_2 | 无 |
| [UUW_InventoryUI](../../Source/IntroCpp/UW_InventoryUI.h) | Grid_Inventory、Text_CurrentWeight、Text_MaxWeight、Text_ItemCount、Button_Sort、Button_Close | Image_SelectedItemIcon、Text_SelectedItemName、Text_SelectedItemDescription、Button_UseItem、Button_DropItem |
| UW_InventorySlot，同上头文件 | 无 | Border_SlotBackground、Image_ItemIcon、Text_ItemQuantity |
| [UUW_StatusBar](../../Source/IntroCpp/UW_StatusBar.h) | ProgressBar_HP、ProgressBar_MP | Text_HP、Text_MP、QuickSlotContainer |
| [UUW_QuickSlot](../../Source/IntroCpp/UW_QuickSlot.h) | 无 | Image_ItemIcon、Text_Count、Border_Highlight |

必需控件要同名、类型兼容，并在蓝图中是可绑定变量。Optional 缺失虽可避免绑定失败，但对应表现可能缺失；这不代表功能完整。变更控件名时同步处理 C++、Widget Blueprint、父类、旧资产与接口记录。

## 开始菜单视觉契约

`/Game/MyStuff/Lvl_Start` 当前创建 `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy`。新标题页采用黑金居中构图：`Image_Background` 和 `Image_Sigil` 组成背景，`Text_Title`、`Text_Subtitle`、`Text_Version` 组成标题区，`Button_StartGame` 显示“点击进入世界”。`Button_1`、`Button_2` 保留为同名 Button 以满足父类合同，但在该 Widget 中为 Collapsed。

| 纹理资产 | 用途 | 关键设置 |
| --- | --- | --- |
| `/Game/MyStuff/MyUI/DarkFantasyTitle/Textures/T_DarkTitle_Background` | 16:9 近黑烟尘背景 | UI LOD、UserInterface2D、NoMipmaps、Nearest、sRGB、NeverStream |
| `/Game/MyStuff/MyUI/DarkFantasyTitle/Textures/T_DarkTitle_Sigil` | 透明原创暗金符文 | 同上 |

源 PNG 保存在 `ArtSource/UI/DarkFantasyTitle`。参考图仅用于黑场留白、居中标题和底部提示的构图，不复制参考作品的标题、商标、文字或符号。进入提示明确为点击操作；当前没有实现任意键开始。

保留的 `/Game/MyStuff/MyUI/UW_MainHUD` 采用左侧像素奇幻菜单布局。`Image_Background` 全屏显示月夜遗迹背景；`Image_TitleCrest`、`Text_Title` 和 `Text_Subtitle` 组成标题区；`Image_MenuPanel` 承载 `VerticalBox_115` 内的三个必需按钮；`Text_Footer`、`Text_Hint` 提供构建版本和操作提示。

| 纹理资产 | 用途 | 关键设置 |
| --- | --- | --- |
| `/Game/MyStuff/MyUI/MainMenu/Textures/T_MainMenu_Background` | 16:9 全屏背景 | UI LOD、UserInterface2D、NoMipmaps、Nearest、sRGB、NeverStream |
| `/Game/MyStuff/MyUI/MainMenu/Textures/T_MainMenu_Crest` | 透明标题徽记 | 同上 |
| `/Game/MyStuff/MyUI/MainMenu/Textures/T_MainMenu_Panel` | 透明菜单面板 | 同上 |
| `/Game/MyStuff/MyUI/MainMenu/Textures/T_MainMenu_ButtonStates` | Normal、Hover、Pressed 纵向图集 | 同上；按钮 FSlateBrush 使用 UVRegion 选择状态 |

像素菜单源 PNG 保存在 `ArtSource/UI/MainMenuPixel`。图片不包含标题或按钮文字；文字由 UMG TextBlock 渲染。两个菜单的 `Button_StartGame` 都继续打开 `MyLevel`，`Button_1` 和 `Button_2` 的实现仍只输出测试日志。

背包 InitializeSlots 当前写死 20 格、每行 5 格；只改 InventoryComponent.MaxSlots 不会自动改变 UI 格数。图标通过软引用及异步加载显示，回调完成前可能换槽或销毁 Widget，改造时考虑弱引用与请求标识。

## 输入契约

MyPlayerCharacter 的 BeginPlay 为已持有的本地玩家添加 InputMapping；SetupPlayerInputComponent 将 UInputAction 接到处理函数。物理按键以 IMC 资产为准，不能把 C++ 注释中的 Tab、鼠标或数字键当作完整键位绑定证据。

| 属性 | 绑定事件 | 处理入口 |
| --- | --- | --- |
| IA_Move / IA_Look | Triggered | Move / Look |
| IA_Jump | Started、Completed | JumpStart / JumpEnd |
| IA_Inventory | Started | ToggleInventory |
| IA_Attack | Started | AttackStarted → Attack |
| IA_UseItem | Started、Completed | UseItemStarted / UseItemCompleted；实际使用逻辑见战斗/背包文档 |
| IA_QuickSlot1..5 | Started，指针存在时绑定 | OnQuickSlotPressed(0..4) → SelectQuickSlot |

当前玩家 CDO 的 IA_Move、IA_Jump 来自 `/Game/Input/Actions`，IA_UseItem 指向 `/Game/MyStuff/MyInput/IA_Use`。不要按 C++ 属性名创建重复资产。

打开背包设置 GameAndUI 输入模式、鼠标可见并停止移动；关闭操作和 OnInventoryClosed 恢复 GameOnly。重复开关需要检查组件事件是否重复绑定、关闭后能否移动/攻击、拖拽图标能否恢复；“Widget 可见”不足以代表这些验证已通过。

2026-10-19：角色开关背包同时更新 Actions 的 UIBlocked；动作占用或死亡时拒绝打开背包。背包“使用”按钮先保存原组件/槽位/物品快照，再关闭 UI；关闭委托若改变来源则拒绝误用新来源，通过后统一发起 RequestUseItem。移动/跳跃读取动作快照；输入与直接调用都必须遵守后端许可，不能用兼容攻击布尔代替许可判断。

## 当前动作资产配置（更新至2026-10-20，Ninja替换未做完工验证）

| 资产 | 实际新增引用 / 通知 |
| --- | --- |
| `/Game/Data/Items/Weapons/DA_WP_LongSword` | ActionDefinition → `/Game/Data/Actions/DA_Action_LongSword` |
| `/Game/Data/Items/Weapons/DA_WP_FireStaff` | ActionDefinition → `/Game/Data/Actions/DA_Action_Fireball`；本轮WeaponFireSocketName改为LeftHand |
| `/Game/Data/Items/DA_HP_Potion`、`DA_MP_Potion`（同目录） | ActionDefinition → `/Game/Data/Actions/DA_Action_UseConsumable` |
| `/Game/MyStuff/Model/Robot/M_LongSwordAttack` | Ninja ComboA1..4_YBot、4段5次MeleeHit、8个ActionWindow；新时序见下方配置链接 |
| `/Game/MyStuff/Model/Robot/M_Attack_Fireball` | Ninja Throw_A_YBot、UpperBodyOnly、唯一Fireball通知约0.183333秒 |
| `/Game/MyStuff/Model/Robot/BS_Move`、`BS_LongSwordMove`、`BS_StaffMove` | 各27个Ninja样本，移动已切Rootmotion；Direction轴±180°并Wrap，Speed意图坐标0/175/525，实际位移来自根轨迹 |
| `/Game/MyStuff/Model/Robot/ABP_Move` | RootMotionFromEverything；事件图用DesiredVelocity与最近消费输入力度计算Speed/Direction，保留状态机与Slot分层 |

移动缓存修复：AnimGraph.LayeredBoneBlend.Node.bUpdateBasePoseFirst=true，保留按根骨权重分层；同一PoseCache被上半身和底层复用时须避免上层零根权重先占用缓存。三个BS现为Direction/Speed输入平滑0.10/0.16秒、临界阻尼SpringDamper、样本权重插值8/s并EaseInOut。配置已保存，未做运行验证，详见 [Ninja配置](Ninja-Animation-Configuration.md)。

三个动作定义父类为 `/Script/IntroCpp.CharacterActionDefinition`，分别引用长剑、火球、喝药 Montage；这些路径稳定，但长剑与火球内容已替换。MoveScale=0，bAllowJump=false。通知以动画播放位置读取，取消不依赖NotifyEnd回调；旧HitWindow字段仍服务未迁移资产。完整行为见 [战斗与动画](Combat-AI.md)、[接口契约](../Interfaces.md)。

`ABP_Move` 保留正式状态机和Slot，事件图已改用移动意图，以避免Root Motion静止无法起步的速度反馈。首次新建26条Sequence与三个IK资产，后续再增加18条Rootmotion输出，26条正式Ninja Sequence启用提取根运动。路径、完整映射、窗口、伤害、输入公式和分阶段回退见 [Ninja动画配置](Ninja-Animation-Configuration.md)。M_Drink保留；未新增MM资产。按用户要求不做完工后验证；编辑工具内部生成类更新属于制作步骤，不是额外编译检查或运行成功证明。

## 修改资产时应记录

记录包路径和对象路径、父类、涉及的 UPROPERTY/控件名/通知类、关键旧值与新值、被哪个关卡或类默认值引用、是否实际保存、是否编译成功。对于只读查询明确写“未保存”；对于自动化超时，先读回状态再决定是否重试。

通过 MCP 先用语义搜索找到原生读写工具；当前 micro 模式入口为 `tools(action="call", category=..., method=..., args={...})`。读取资产请打开 includeValues 或相应参数，并区分 Blueprint CDO 与关卡实例属性。配置与复测见 [开发流程](../Development.md)。

## MHWI训练场运行输入（2026-10-25，B10）

`AMHWICharacter::BuildInputMapping`动态创建Enhanced Input映射，优先级50，失去控制/EndPlay移除。新增枚举只尾追加`SlingerBurst`，键盘V与手柄D-pad Left在气刃连段合法窗口进入投射器连射，移动方向决定左右/正面；既有命令值不重排。W＋左键使用WalkOnSlash前进斩，持刀回避按方向选择11/12/13/10源片段。

`AMHWIHUD`为原生Canvas HUD，新增投射器弹药与按键提示；无UMG命名绑定迁移。本轮未保存地图/蓝图或输入资产，未编译/测试。来源取消窗口和物理按键为项目适配；详见[B10交付](../Reference/MHWI-R06-Remaining-Development.md)和接口MHWI-013。
