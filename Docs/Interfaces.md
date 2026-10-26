# 核心接口与事件契约

初始基线：2026-10-17；动作相关契约更新至 2026-10-19 的当前源码。这里记录跨系统调用的语义，而非复制全部头文件。`ITEM-*` 等 ID 用于技术方案、变更记录和模块索引的交叉引用；新增契约时先搜索已有 ID，再分配新号。源码契约已实现不代表关联资产和 PIE 已全部验证。

除特别说明，接口按游戏线程使用；`void` 表示没有结构化成功结果，不表示必然完成。BlueprintCallable 表示可从蓝图调用；动态委托是否能直接在蓝图中 Assign 还取决于 UPROPERTY/BlueprintAssignable。

## ITEM：数据注册和效果

源文件：[ItemDataSubsystem.h](../Source/IntroCpp/ItemDataSubsystem.h)、[ItemDataBase.h](../Source/IntroCpp/ItemDataBase.h)、[ItemAction.h](../Source/IntroCpp/ItemAction.h)。

| ID | 签名/入口 | 前置条件、返回值与副作用 |
| --- | --- | --- |
| ITEM-001 | `UItemDataSubsystem::GetItemData(FName ItemID) -> UItemDataBase*` | 当前 GameInstance 中的注册 ID；可能同步加载并缓存；缺失返回 nullptr；不把返回对象当作角色私有可变实例 |
| ITEM-002 | `GetConsumableData(FName)` / `GetWeaponData(FName)` | 基于同一注册表查询与 Cast，类型不符返回 nullptr |
| ITEM-003 | `RegisterItemData(UItemDataBase*) -> void` | 拒绝 null/空 ID；同 ID 覆盖映射；现有 LoadedCache 不同步失效；不代表保存资产 |
| ITEM-004 | `UItemAction::Execute(UInventoryComponent*, int32 SlotIndex, AActor* Instigator) -> bool` | BlueprintNativeEvent；true 表示请求消耗，false 表示不请求消耗；具体效果由实现决定，不是通用“操作成功”结果 |
| ITEM-005 | `InitializeFromItemData(const UItemDataBase*) -> void` | C++ virtual；执行 Action 前注入 DataAsset 配置；Heal/RestoreMana 分别读取正的 HealthRestore/ManaRestore，否则保留 Action 默认值 |

SlotIndex 的意义由调用路径决定：InventoryComponent::UseItem 传背包索引，快捷栏独立使用路径可能传快捷栏索引。新的 Action 不应未经区分直接按该索引读背包；修改这个约定属于接口迁移。

## INV：背包、快捷栏和装备

源文件：[InventoryComponent.h](../Source/IntroCpp/InventoryComponent.h)、[实现](../Source/IntroCpp/InventoryComponent.cpp)。这些主操作为 BlueprintCallable。

| ID | 签名/入口 | 当前真实契约 |
| --- | --- | --- |
| INV-001 | `AddItem(FName ItemID, int32 Quantity=1) -> bool` | 数量需正、数据需存在；先查总重量，再叠加/填空槽。true 表示整次填完；false **可能已经部分修改数组且未刷新统计/事件**，不是事务回滚 |
| INV-002 | `RemoveItem(FName, int32 Quantity=1) -> bool` | 扣到的数量大于零就返回 true，不保证满足全部请求；按 ID 路径与装备/快捷栏同步不完整 |
| INV-003 | `RemoveItemAt(int32 SlotIndex, int32 Quantity=1) -> bool` | 无效/空/非正数量返回 false；最多移除当前整堆；最后一件可能触发卸装。清空后构造移除事件会丢原 ItemID，见已知问题 |
| INV-004 | `UseItem(int32 SlotIndex) -> bool` | 玩家 Owner 转发 `Actions.RequestUseItem(false, SlotIndex).IsAccepted()`；true 仅表示请求被接受，动画播放、效果及消费结果需另查。无动作组件的 Owner 使用原来源预约后即时提交；提交事件保存原 ItemID，最后一件不再清空后读取 ID |
| INV-005 | `DropItem(int32) -> void` | 检查可丢弃后尝试 Spawn，最后移除整堆；当前缺少 Spawn 成功才提交扣除的保证 |
| INV-006 | `SetItemAt(int32, const FItemInstance&) -> void` | 原样覆盖有效槽并广播全量刷新；不重新验证重量/堆叠，也不重算统计或维护装备索引 |
| INV-007 | `SwapItems(int32,int32)` / `SortItems()` | 交换或按 ItemID 排序后广播刷新；不会重映射 EquippedSlotIndex；Sort 不合并堆叠 |
| INV-008 | `GetItemAt(int32) -> FItemInstance` / `GetAllItems() -> TArray<FItemInstance>` | 返回拷贝；无效索引返回空实例；修改拷贝不修改组件 |
| INV-009 | `HasItem(FName)` / `GetItemCount(FName)` / `FindItemSlot(FName)` | 调用者传非空 ID；按 ItemID 匹配，Find 返回第一格或 -1；不能用它表示唯一物品实例 |
| INV-010 | `SelectQuickSlot(int32) -> bool` | 有效范围 0..4；选中同一格返回 true 且不再广播；本函数本身不使用物品 |
| INV-011 | `SetQuickSlot(int32,const FItemInstance&) -> bool` / `ClearQuickSlot(int32)` | 写入/清空另一数组并广播 OnQuickSlotChanged；不会自动扣除或转移背包物品，不校验来源所有权 |
| INV-012 | `UseSelectedQuickSlot() -> bool` | 玩家消耗品转发 `RequestUseItem(true, SelectedQuickSlotIndex)`，bool 表示接受；武器通过 CanChangeEquipment 后调用角色 EquipWeapon，不再为此回填背包。无动作组件时按快捷栏来源即时提交；快捷栏仍是独立容器，不扣背包同 ID 物品 |
| INV-013 | `EquipItem(int32) -> bool` / `UnequipItem()` | 装备位置是背包索引；要求非空武器；广播动态装备委托。角色 EquipWeapon 的职责不同 |
| INV-014 | `GetEquippedWeaponData()` / `GetEquippedItemID()` | 根据当前背包装备索引查配置/ID；无装备通常返回 nullptr/NAME_None；排序交换后需警惕索引语义已变 |

`HasSpace()` 依赖 CurrentItemCount，`CanCarryWeight(float)` 依赖 CurrentWeight。现有计数/重量在部分写入路径上不一致；它们不能提供完整 AddItem 容量预检或事务保证。

动作组件存在时，前台动作、派发、清理和 OwnerEnded 阶段会拒绝**全背包和快捷栏公共写操作**，包括添加、移除、丢弃、排序、交换、覆盖、装备、选槽和快捷栏写入；bool 接口返回 false，void 接口直接返回。当前不是仅锁预约槽位。内部 `ReserveActionItem` 保存容器/索引/ID/数量/全局版本，`CommitActionItem` 重新校验并仅扣原来源；它们是受控 C++ 提交接口，不是可绕过动作的玩家启动 API。

`FActionItemCommitResult` 分开 `bApplied`、`ConsumedQuantity`、`bPartial`，`IsCommitted()` 仅判断消耗数量大于零。旧 ItemAction 的 bool 作为报告值适配：至少一个成功报告时消费一次，部分报告失败或后续效果被终止可标记 Partial；false 不证明任意自定义副作用都未发生。无 Action 的消耗品仍保留消费规则，满 HP/MP 的现有 Heal/RestoreMana 仍可能报告成功并消费。

## ATTR：属性

源文件：[AttributeComponent.h](../Source/IntroCpp/AttributeComponent.h)、[实现](../Source/IntroCpp/AttributeComponent.cpp)。

| ID | 签名/入口 | 语义 |
| --- | --- | --- |
| ATTR-001 | `ApplyDamage(float DamageAmount, AActor* Instigator=nullptr) -> void` | 存活且正伤害先经DAMAGE-001；未消费再经可选DAMAGE-002调整，随后更新并clamp HP、重置恢复计时。生命周期复查后才继续，死亡/不可致死规则见实现；调用方不依赖void判断命中 |
| ATTR-002 | `ApplyHeal(float)` / `RestoreMana(float)` / `UseMana(float)` | 存活时修改对应值并 clamp；数值改变时广播；UseMana 不提供余额校验返回值 |
| ATTR-003 | `SetHealth(float)` / `SetMana(float)` | 直接设置并 clamp，变化时广播；SetHealth 降至零可触发死亡；设正 HP 不等于有完整复活流程 |
| ATTR-004 | `SetMaxHealth(float)` / `SetMaxMana(float)` | 最大值至少为零，必要时截断当前值并广播；不会自动补满 |
| ATTR-005 | `GetHealthPercent()` / `GetManaPercent()` / `IsAlive()` | 比例最大值为零时返回 0；不要用 getter 改状态 |
| ATTR-006 | `TrySpendMana(float ManaAmount) -> bool`；`BeginNotificationBatch()` / `EndNotificationBatch()` | TrySpendMana 在游戏线程验证存活、有限非负成本和余额；false 不改 MP，true 扣除并可能同步通知。批处理为 C++ 提交边界，配对调用、支持嵌套；仅在最外层 End 发布待发送 HP/MP 通知，不提供通用副作用回滚 |

当前 `bCanDie=false` 时，ApplyDamage 会直接忽略足以使 HP 降至零的整次伤害，并非保留 1 HP；调用者若需要不同的无敌/濒死规则，应另行定义并验证。

## ACTION：玩家动作调度

源文件：[CharacterActionComponent.h](../Source/IntroCpp/Actions/CharacterActionComponent.h)、[CharacterActionTypes.h](../Source/IntroCpp/Actions/CharacterActionTypes.h)、[CharacterActionExecution.h](../Source/IntroCpp/Actions/CharacterActionExecution.h)、[CharacterActionEffects.cpp](../Source/IntroCpp/Actions/CharacterActionEffects.cpp)。当前为本地单前台动作，不提供多人复制、预测或 GAS 能力保证。

| ID | 签名/入口 | 当前真实契约 |
| --- | --- | --- |
| ACTION-001 | `RequestAttack() -> FCharacterActionRequestResult` / `RequestUseItem(bool bQuickSlot, int32 SlotIndex) -> FCharacterActionRequestResult` | 统一检查死亡、UI、派发/清理与占用；返回 Started/Buffered/Rejected、Failure、RunId。Started 不等于效果提交成功，IsAccepted 也不表示已扣物/蓝；无 Montage 物品可同步完成或失败。近战攻击可刷新唯一一条限时缓冲，使用物品不排队；失败不会自动改走旧后端 |
| ACTION-002 | `GetSnapshot() -> FCharacterActionSnapshot`；`HandleNotify(Mesh, Animation, EventReference, Event) -> bool` | 快照按值返回RunId、Kind、Phase、0基ComboIndex、SegmentGeneration、本段bCommitted、MoveScale和bAllowJump；UI/死亡/结束锁定移动输入、新走跑意图及跳跃。Root Motion动作自身位移不由MoveScale缩放，死亡/结束需统一终止Montage。通知要求当前Mesh/Montage、engine MontageInstanceID、段内预期事件地址，先记账再执行；重复/旧事件false。链共享RunId，每段新Montage实例并增代次；转段及自然结束必须收齐必需事件 |
| ACTION-003 | `TryCancelAction(int64 RunId) -> bool` / `Interrupt(ECharacterActionEndReason Reason) -> void`；`IsBusy()` / `CanChangeEquipment()` | TryCancelAction 只接受当前 RunId 和显式 Cancel 时间范围，派发/清理/BlendOut 或无窗口 false；Interrupt 为强制结束，不受自愿取消窗口限制。终止先失效身份再停动画，派发内延后清理，旧回调不能解锁新动作；死亡/EndPlay 走此生命周期，提交后不退款。换装要求空闲且存活；动作占用时全背包写接口也拒绝 |
| ACTION-004 | `UCharacterActionDefinition`；`UAnimNotifyState_ActionWindow`；`UMyAnimInstance::LocomotionContext` | Definition配置Montage、速率、移动/跳跃、缓冲与看门狗；WeaponData/ConsumableData可选引用，未赋值仍适配旧配置。窗口标记Chain/Cancel动画时间范围，组件自行采样，不依赖NotifyEnd；无Chain沿用HitWindow，无Cancel不可自愿取消。LocomotionContext仍为游戏线程只读快照；ABP_Move现用DesiredVelocity方向及其长度×经MoveScale去重的输入力度驱动Root Motion选片，Velocity保留实际速度。RootMotionFromEverything让CharacterMovement消费根位移，不表示MM已接通 |

`Failure` 包括 Busy、Dead、UIBlocked、Cooldown、InvalidSource、MissingAnimation、MissingEvent、InsufficientMana、SpawnFailed、NoEffect、NotReady。`GetLastFailure()` 是组件最近一次拒绝/结束记录，可被后续请求覆盖；需按 RunId 观察结束委托，不能把它当作永久历史。

窗口前 InputBufferSeconds 默认0.15世界秒，窗口内立即登记唯一衔接意图，不再受早按TTL影响；Chain/Cancel 是相对段落的动画秒。正常BlendOut关闭命中和衔接，Ended检查完整提交；看门狗超时只失败清理。2026-10-19的10项自动化和41项真实PIE断言覆盖当日四段6命中/施法/物品/取消/死亡，证据见 [实施记录](Changes/CHG-20261019-005-character-actions-implementation.md)。2026-10-20仅做 [Ninja资源迁移](Systems/Ninja-Animation-Configuration.md)：四段5命中及逐段窗口、火球提交约0.183333秒、火杖LeftHand发射，C++签名不变；用户禁止完工后验证，故旧证据不覆盖新资产。MM未启用。

## COMBAT / AI / UI：协作入口

| ID | 所有者与入口 | 契约/扩展条件 |
| --- | --- | --- |
| COMBAT-001 | `AMyPlayerCharacter::EquipWeapon(UWeaponData*)` / `UnequipWeapon()` | 经 ACTION-003 的 CanChangeEquipment 许可后更新角色表现及配置，不负责将物品写入 Inventory；动作/死亡/结束期间拒绝换装 |
| COMBAT-002 | `Attack()` / `FireFromHand()` | Attack 仅转发 ACTION-001；旧 FireFromHand 无身份调用记录警告且不产生效果。火球通知改走 ACTION-002，标准投射物伤害覆盖在 deferred spawn 激活前写入 |
| COMBAT-003 | `OnMeleeHitNotify()` / `MeleeHitCheck()` | 旧无身份入口仅警告，不结算；MeleeHit Notify 携带上下文走 ACTION-002，再执行当前单目标球扫。每段不同事件可分别伤害，SubHits 不循环，不默认每目标每段只伤害一次 |
| COMBAT-004 | `UseHeldItem()` / `OnUseItemAnimFinished()` | UseHeldItem 转发当前快捷栏来源到 ACTION-001；旧完成回调、ExecuteItemUseEffect/ExecuteItemActions 不再直接生效。来源及提交由执行上下文和 Inventory 管理，不保留角色 pending 作为权威 |
| COMBAT-005 | `BP_OnMeleeAttackHit(HitResult, ComboHitIndex, SubHitIndex, FinalDamage)` | 蓝图表现扩展；ComboHitIndex 为 0 基；伤害已由 C++ 处理，不重复扣血 |
| COMBAT-006 | `BP_OnComboAdvanced(int32)` / `BP_OnComboReset(bool)` | 实际进入下一段后报告 0 基段号；近战结束时 Reset 参数为终止理由是否非 Completed，OwnerEnded 不广播。角色攻击/使用 bool 和 AnimInstance 字段是动作快照的兼容镜像，不可据此启动第二套结算 |
| AI-001 | `AEnemyBase::SetTargetActor(AActor*)` / `ClearTargetActor()` | 设置当前目标，不证明已有控制器、导航或感知能力 |
| AI-002 | `PerformAttack()` / `OnAttackAnimNotify()` | 启动动作与伤害生效分离；需 EnemyData、目标、冷却与通知配置 |
| AI-003 | `OnReceiveDamage(float,AActor*)` / `Die()` | 非致死受击反馈与死亡清理；控制器死亡状态另经 Tick 或 OnOwnerDied 更新 |
| UI-001 | `UUW_InventoryUI::SetInventoryComponent(...)` / `RefreshUI()` | 注入模型并订阅、刷新；当前重复注入可能重复订阅，构造/重挂生命周期需验证 |
| UI-002 | `UUW_StatusBar::InitWithAttributes(...)` / `InitWithInventory(...)` | 注入模型并显示 HP/MP/快捷栏；重绑与 NativeDestruct 解绑是维护边界 |
| UI-003 | `AMyPlayerCharacter::ToggleInventory()` / `OnInventoryUIClosed()` | 管理 UI、鼠标、输入模式和 Actions.UIBlocked；动作/死亡期间拒绝打开。背包使用按钮先保存来源并关闭 UI，再核对同槽 ID/数量后发起 UseItem，避免 UI gate 拒绝自身请求；仅隐藏 Widget 不会完成这些清理 |
| UI-004 | `UDragItemOperation::CreateFromInventory(...)` / `CreateFromQuickSlot(...)` | 载荷含来源、索引、ItemInstance 快照、图标；真正写数据发生在目标 OnDrop；不是事务凭证 |
| PICKUP-001 | `APickupItem::InitializePickup(FName,int32)` / `OnPickup(AActor*)` | 初始化掉落物；OnPickup 为 BlueprintNativeEvent，默认 Destroy；覆写时明确是否保留父实现 |

## 事件契约

| 事件 ID | 发布者、参数 | 订阅者/触发边界 |
| --- | --- | --- |
| EVT-INV-01 | OnInventoryUpdated，无参数 | 原生多播，UI 全量刷新；多条路径会重复广播 |
| EVT-INV-02 | OnItemAdded / OnItemRemoved / OnItemUsed，`const FItemInstance&` | 原生多播，AddUObject/委托句柄；参数仅在回调期按引用使用，持久记录需复制。动作消费先保存原 ID 并提交数量再发布；普通 RemoveItemAt 的旧 ID 风险仍见 INV-003 |
| EVT-INV-03 | OnEquipmentChanged，`FName ItemID, bool bEquipped` | 动态多播，角色与 StatusBar 用 AddDynamic；当前成员没有 BlueprintAssignable UPROPERTY |
| EVT-INV-04 | OnQuickSlotSelected / OnQuickSlotChanged，`int32 SlotIndex` | 动态多播；角色外观、快捷栏 UI；当前成员没有 BlueprintAssignable UPROPERTY |
| EVT-ATTR-01 | OnHealthChanged / OnManaChanged，`float CurrentValue, float MaxValue` | BlueprintAssignable 动态多播，UI 消费；最大值变化也可广播 |
| EVT-ATTR-02 | OnCharacterDeath，无参数；OnDamaged，`float DamageAmount, AActor* Instigator` | BlueprintAssignable；ApplyDamage 致死分支只发死亡，不发 OnDamaged |
| EVT-ACTION-01 | OnActionChanged，`FCharacterActionSnapshot Snapshot` | BlueprintAssignable 动态多播；启动、阶段/提交及结束镜像更新后发布副本，OwnerEnded 抑制；不是单独 OnActionStarted，不能假定只广播一次 |
| EVT-ACTION-02 | OnActionEnded，`int64 RunId, ECharacterActionEndReason Reason, ECharacterActionFailure Failure` | BlueprintAssignable 动态多播；身份失效、停止动画和镜像更新后，每次实际执行至多一次；回调处仍在清理保护内，新请求 Busy。OwnerEnded 不广播，已提交效果不因中断退款 |
| EVT-UI-01 | OnInventoryClosed，无参数 | BlueprintAssignable；关闭按钮通知角色恢复输入 |
| EVT-BUS-01 | GlobalEvents::Item_Pickup，FString ItemID | Pickup 成功后 Publish_StringParam；不含数量、接收者、事务 ID |
| EVT-BUS-02 | GlobalEvents::Player_Jump，无参数 | JumpStart 发布；不表示落地事件 |

[UMyEventBusGameInstance](../Source/IntroCpp/MyEventBusGameInstance.h) 提供 NoParam/String/Int/Float/Actor/Damage 六套独立 Subscribe/Publish/Unsubscribe。相同 FName 在不同参数映射中不是同一订阅。Damage 载荷是 `int32, AActor*`，与 AttributeComponent 的 float 伤害事件不同；当前没有证明它已接入实际伤害链。只有 NoParam 另有 Lambda 订阅重载；Lambda 捕获对象需要自行保证生命周期。

## 模板接口

[IShooterWeaponHolder](../Source/IntroCpp/Variant_Shooter/Weapons/ShooterWeaponHolder.h) 是模板射击玩法的 C++ 纯虚接口：AttachWeaponMeshes、PlayFiringMontage、AddWeaponRecoil、UpdateWeaponHUD、GetWeaponTargetLocation、AddWeaponClass、OnWeaponActivated、OnWeaponDeactivated、OnSemiWeaponRefire。它不是自定义武器 DataAsset 系统的接口，不应直接混用。

新增或破坏性修改使用 [接口模板](Templates/Interface.md)，更新本页条目、调用方、资产影响与迁移步骤。

## MHWI：独立太刀与预伤害

实现：[MHWICharacter.h](../Source/IntroCpp/MHWI/MHWICharacter.h)、[MHWIMovesetData.h](../Source/IntroCpp/MHWI/MHWIMovesetData.h)、[IncomingDamageResponse.h](../Source/IntroCpp/IncomingDamageResponse.h)。玩法入口见 [MHWI 太刀](Systems/MHWI-LongSword.md)。

| ID | 签名/入口 | 当前真实契约 |
| --- | --- | --- |
| DAMAGE-001 | `IIncomingDamageResponse::InterceptIncomingDamage(float,AActor*) -> bool` | BlueprintNativeEvent；由属性组件在正伤害扣血前同步调用 Owner。true 消耗本次伤害，不扣血、不广播受伤/死亡；false 继续既有扣血路径。回调后重新检查组件/Owner/存活状态。未实现接口的 Owner 不受影响 |
| DAMAGE-002 | `IIncomingDamageResponse::AdjustIncomingDamage(float,AActor*,float& AdjustedDamage) -> bool` | DAMAGE-001未消费后调用；true且out为有限数时使用其非负值，0不扣血也不广播；false或非有限out保持原请求。调整后再次检查组件/Owner生命周期和存活。未实现的默认false保持兼容；受击广播使用实际调整后伤害。MHWI用于有时限霸体的50%减伤，不免除真实扣血/死亡 |
| MHWI-001 | `AMHWICharacter::RequestInput(EMHWIInput) -> bool` | 空闲/特殊纳刀保持时尝试启动；活跃时 true 表示写入最后一次输入缓冲及实际Montage接收位置，仍需满足取消窗口、资源和派生条件。低帧/结束回调仅补算输入收到后的真实区间，窗口关闭后输入不能追溯派生。死亡/结束/派发清理时 false。只在游戏线程使用 |
| MHWI-002 | `StartMove(FName) -> bool` / `InterruptMove() -> void` | StartMove 仅空闲可启动且检查 Montage/资源；不绕过活跃派生窗口，也不能从中立直接启动登龙中间阶段。InterruptMove 清理前台执行、缓冲、翻滚恢复上下文、命中去重、登龙标记/七段授权，并恢复空中移动/根运动快照；命中派发重入时延后清理 |
| MHWI-003 | `GetSpiritGauge/Level/TimeRemaining`、`GetCurrentMove/GetMoveStatus`、`IsSheathed/IsSpecialSheathHolding` | 只读快照；槽 0–100，等级 0–3，时间为世界秒。数据窗口为 Montage 秒，不是墙钟或乘速后的秒 |
| MHWI-004 | `OnStateChanged()` / `OnMoveChanged(FName,FText)` | BlueprintAssignable 动态委托；状态/资源变化与动作开始/结束广播。结束 MoveId 为 NAME_None；回调不得假定旧执行仍有效。尚未提供网络复制承诺 |
| MHWI-005 | `FMHWIHitWindow` / `FMHWIMoveDefinition` / `FMHWIRoute` | 每个命中窗口对目标至多一次伤害、每窗口至多一次槽收益。只有真实扣血才确认命中。登龙突刺弱目标仅沿合法阶段传递；173 到达提交时刻才授权落地七段/降色；无输入或提前落地不授权。`RequireDrawn` 限制翻滚出口。`TurnStartTime/EndTime/MaxAngle/Speed` 与返回段窗口为 Montage 秒/角度/度每秒；按区间交集处理，预算每段独立 |
| MHWI-006 | `FMHWIWeaponMotionEvent`、`FMHWIMoveDefinition::WeaponMotionEvents`、`UMHWIMovesetData::WeaponMotions`；`GetWeaponMotionNo()` / `GetWeaponMotionPosition()` | 事件按源 Montage 秒升序，编号负值保持当前内部动作；map 为独立武器骨架的 Sequence，必须与 WeaponMesh 的 Skeleton 相同。动作开始消费 time=0 一次，其后按实际进度跨窗消费；特殊纳刀不越过保持边界。内部动作时钟使用 Actor 秒并停在片段尾，支持猎人冻结后继续收柄。真实结束/打断/死亡清游标并恢复纳刀0/持刀1；直接派生推迟中间重置，后继事件/默认姿态选择完才刷新挂接。无源事件的纳刀攻击先用内部拔出2。无独立 Timer。getter 为实际内部动作编号和片段秒，非整件武器挂点或原版装配编号。空配置兼容旧资产 |
| MHWI-007 | `FMHWIMoveDefinition::bIndependentDefenseWindows`、无敌/反击字段及资源字段；`HasCounterConfirmed()`、`GetCounterArmorRemaining()`、`GetGaugeRegenTimeRemaining()`、`GetSpiritDecayPauseRemaining()`、`GetSpiritGaugeAtMoveStart()` | 独立模式中防御窗为半开源Montage秒 `[start,end)`，成功反击与单纯无敌分开；阈值检查扣费前捕获槽。霸体/回槽/衰减暂停使用Actor秒，回槽只积未到期部分；正常派生保留计时，显式中断清霸体，死亡/EndPlay清三个计时。见切确认后必须真实回斩扣血才满槽；getter为只读状态，不是调试写入口 |
| MHWI-008 | `build_native_action_database.run()` / `author_native_parameters.run(save=False)` | 原始数据批处理与白名单导入。先验证源/模板SHA256，解码425字段并保留未知区；B01补气刃踏步cost后为18个招式属性与4个全局属性，原21处为历史规模。save=False仅预览复制结构，save=True备份后写正式DA并核对全部Montage/武器事件/Route及数值读回。匿名物理块、IK消费者、输入mask和shell调度不猜；十秒字段当前消费者仍待取证，不能将数值导入成功当消费者证明 |
| MHWI-009 | `FMHWIWeaponAttachmentRuntime::Update/IsBackMounted/Reset`、`FMHWIWeaponAttachmentContext` | 游戏线程同步装配，无UObject所有权。上下文含动作入口装备状态、当前源Montage秒和显式收刀锚点；`IsBackMounted()`为上次几何过渡达到95%的视觉状态，不能作攻击许可。握点在最终混合之后锁右掌，居合鞘口锁左掌；材质握点按0..8源帧转移，普通回握使用0.16 Actor秒。不同动作但左手所有权相同不会重置鞘过渡。现有UPROPERTY/资产不迁移；当前窗口为项目拟合，非已解码原版挂点 |
| MHWI-010 | `FMHWIHitWindow::SpiritLevelDamage`；`native_reference_basics.run()` / `author_reference_basics.run(save=False)` | 可选map按当前动作启动捕获的颜色0..3选命中基值，缺对应键回退Damage，再应用既有倍率；不新增伤害窗、shell或原作完整HP公式。原生基础入口直接读取固定指纹COL/W03P/FSM，保留原索引/偏移，复制结构预览/幂等/全字段保护，save=True备份后只写正式DA。新字段要求完整构建，旧资产空map兼容；命令行环境不查询不存在的LevelEditor UI，正常编辑器禁止PIE中写入 |
| MHWI-011 | `FMHWIRoute::RequireFullSpiritCost`；`native_spirit_branches/author_spirit_branches.run` | 默认false，旧路由行为不变。启用时仅比较当前槽与目标定义的有限非负SpiritCost，不足继续扫描原序后备；不绕过显式输入许可。B02用于插入上挑R优先III、后备I；气刃踏步复用弱斩消费者，原值18/28/20/10直接读取，回退I的14/26及弱消费也从原表重建。新增同条件B/后备R复制现有适配窗口，未证明原版精确帧；复制预览/幂等/白名单保护，save仅写正式DA |
| MHWI-012 | `AMHWICharacter::BindNativeActionSource(Montage, InstanceId, Identity) -> uint32` / `ReleaseNativeActionSource(Token)`；`ResolveActionEntry`、`MotionPosition`、`GetNativeMainMotion` | 游戏线程来源交接；实际匹配实例和已知原生身份返回非零令牌，0失败，陈旧令牌不撤销新拥有者；已接实际Step/Creep/Shot调用。消费真实源帧/Phase，规范绑定还校验bank/motion及射击变体。专用入口保留前请求→通用Phase→后覆盖及中间MBD来源；直入/连接后事件从实际入帧初始化，不补播过去事件，13终点绑定保护保留。来源证明不授予任意输入/取消许可；B12历史编译成功，当前A01发现受击锁阻断真实来源恢复，未运行验证，见[验收报告](Reference/MHWI-Acceptance-20261026.md) |
| MHWI-013 | `IMHWIContactResponse`、`EMHWIImpactSize`；`EMHWIInput::SlingerBurst`；`UMHWIAnimInstance::BeginNativeBlend/CancelNativeBlend` | 接触接口明确提供Small/Medium/Large及是否弹刀，游戏线程同步调用，不根据伤害值猜测。来源拥有者独占运动/输入直到合法续段、实际结束或中断；投射器原生mTrigger第36源帧只发射/扣弹一次。输入枚举仅尾追加V/D-pad Left；源取消窗口、方向/弹药/伤害为项目适配。动画代理捕获显示姿态、首个求值前elapsed保持0，Actor动画秒×60独立于动作倍率，按合格线性插值输出；新Montage在根运动提取前全权重，无request200不启用尾淡出。撤销/死亡清理拥有者、缓存及混合；B12历史编译成功，但A01恢复许可回归待修，R06当前部分完成；未运行验证 |

`FMHWIRoute.CancelStart/CancelEnd` 分别负值时回退招式对应端点，否则以路由源Montage秒闭区间判断。匹配的显式输入拥有先决条件和窗口，不能失败后绕过通用取消；袈裟目标占位`FadeSlash`仍在选择时解析左右/后退。请求、缓存、跨帧、保持入口及HUD使用相同取窗规则；23招148规则的数值是[源阶段约束下的项目调校](Reference/MHWI-Transition-Calibration.md)，未冒充原始输入位解码。

2026-10-22 动作数据修正：Light 的 DrawSlash/StepSlash 出口接 OverheadSlash；SpiritII/RisingSlash 分别对应 106/107，命中窗口随各自片段重算。接口签名与缓冲返回语义未改变，具体配置与本轮验证见 [MHWI 动画修正](Changes/CHG-20261022-004-mhwi-animation-corrections.md)。

2026-10-22 训练场配置修正：`L_MHWI_Training` 的三个目标实例默认 `bEnableAttacks=false`，主动伤害只在显式开启该目标属性后生效。伤害仍以训练目标为来源传给 `UAttributeComponent::ApplyDamage`；角色正常受击与防御契约保持，未设置全局无敌。原生目标类缺省值未修改，见 [训练场伤害记录](Changes/CHG-20261022-005-mhwi-training-damage.md)。

2026-10-23 行为配置：正式 DA 新增 `SpiritComboThrust`、`SpiritComboRisingSlash` 和 `RollStepSlash`；气刃插入再按 R 保持 II/III 段位，普通 RMB 为突刺/上挑循环。翻滚恢复身份只在相应执行结束后 0.15 秒内有效，中断/死亡/收刀/过期清除。袈裟按镜头相对移动意图与选择前角色右轴决定方向，无输入默认后退。`UMHWIMovesetData::HelmAirVerticalSpeed/ForwardSpeed/Gravity/StrikeSpeed/StrikeStartTime` 为项目物理初值；Rise 根运动，Air/Strike Falling，真实着地驱动 Land。反射字段有默认值，已显式制作正式 DA；未修改旧动作系统或多人复制契约。验证状态见 [本轮记录](Changes/CHG-20261023-001-mhwi-behavior-implementation.md)。

实际硬件/Enhanced Input入口 `CommandStarted` 在选招前读取本帧已求值的 `MoveAction`，不依赖后触发的 `Move(Triggered/Completed)` 回调更新缓存。方向键与袈裟键同帧按下或松开也使用该帧方向；直接蓝图 `RequestInput` 仍使用角色已有移动意图，不暗中读取键盘或绕过映射上下文。
