// Fill out your copyright notice in the Description page of Project Settings.

#include "InventoryComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"
#include "PickupItem.h"           // DropItem 生成 APickupItem 需要
#include "ItemAction.h"           // UseItem 执行 ItemAction 需要
#include "ItemDataSubsystem.h"    // GetSubsystem<UItemDataSubsystem>() 获取数据

// ============================================================================
//  构造函数
// ============================================================================

/**
 * 初始化背包组件默认值：
 * - 背包数组预分配 MaxSlots(20) 个空 FItemInstance
 * - 快捷栏预分配 QUICK_SLOT_COUNT(5) 个空 FItemInstance
 * - 统计归零
 */
UInventoryComponent::UInventoryComponent()
{
    PrimaryComponentTick.bCanEverTick = true;

    // 初始化背包数组：20个空槽位（FItemInstance 默认构造=空）
    Inventory.Init(FItemInstance(), MaxSlots);
    CurrentWeight = 0.0f;
    CurrentItemCount = 0;

    // 初始化快捷栏：5个空槽位
    QuickSlots.Init(FItemInstance(), QUICK_SLOT_COUNT);
    SelectedQuickSlotIndex = 0;
}

// ============================================================================
//  BeginPlay — 生命周期初始化
// ============================================================================

/**
 * 确保背包数组大小与 MaxSlots 一致（防止编辑器中途改了值导致不匹配），
 * 并广播初始状态让 UI 在打开时能正确渲染。
 */
void UInventoryComponent::BeginPlay()
{
    Super::BeginPlay();

    // 防御性检查：如果编辑器改了 MaxSlots 但数组大小未同步
    if (Inventory.Num() != MaxSlots)
    {
        Inventory.SetNum(MaxSlots);
        for (int32 i = 0; i < MaxSlots; i++)
        {
            Inventory[i] = FItemInstance();  // 重置所有格为空
        }
    }

    // 广播初始状态（UI 打开时需要知道当前背包内容）
    BroadcastInventoryUpdate();
}

void UInventoryComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    // 当前 Tick 为空，预留扩展位置：
    // - 持续 Buff 效果倒计时
    // - 物品自动回收/腐烂机制
    // - 重量超重减速效果
}

// ============================================================================
//  AddItem — 添加物品到背包
// ============================================================================

/**
 * 核心添加逻辑（支持堆叠）：
 *
 * @param ItemID   要添加的物品 ID（必须对应已注册的 DataAsset）
 * @param Quantity 数量
 * @return         是否成功
 *
 * 流程图：
 *   Quantity <= 0? → false (防非法参数)
 *   Subsystem 找不到 ItemData? → false (日志警告)
 *   超重? → false (日志警告)
 *   可堆叠? → 遍历已有同ID槽位逐格叠加 (每格不超过 MaxStackSize)
 *   还有剩余? → FindEmptySlot 开新格 (每格最多 MaxStackSize)
 *   无空格? → false (背包满，部分可能已添加成功)
 *   → UpdateWeight + OnItemAdded + OnInventoryUpdated → true
 */
bool UInventoryComponent::AddItem(FName ItemID, int32 Quantity)
{
    if (Quantity <= 0) return false;

    // 通过全局 Subsystem 获取物品静态配置数据（返回指针，nullptr 表示未注册此物品）
    UItemDataBase* ItemData = GetItemData(ItemID);
    if (!ItemData)
    {
        UE_LOG(LogTemp, Warning, TEXT("无法添加物品: 未找到物品数据 %s"), *ItemID.ToString());
        return false;
    }

    // ★ 重量限制前置检查：预估新增重量是否会超标
    if (!CanCarryWeight(ItemData->Weight * Quantity))
    {
        UE_LOG(LogTemp, Warning, TEXT("无法添加物品: 超重 %s x %d"), *ItemID.ToString(), Quantity);
        return false;
    }

    int32 RemainingQuantity = Quantity;

    // === 阶段1：尝试堆叠到已有同ID物品的槽位 ===
    if (ItemData->MaxStackSize > 1)  // 只有可堆叠物品才走此分支
    {
        for (int32 i = 0; i < Inventory.Num() && RemainingQuantity > 0; i++)
        {
            // 找到同 ID 且未满的槽位
            if (Inventory[i].ItemID == ItemID && Inventory[i].Quantity < ItemData->MaxStackSize)
            {
                // 计算本格还能塞多少（取剩余需添加量 和 本格剩余空间 的较小值）
                int32 CanAdd = FMath::Min(RemainingQuantity, ItemData->MaxStackSize - Inventory[i].Quantity);
                Inventory[i].Quantity += CanAdd;
                RemainingQuantity -= CanAdd;

                UE_LOG(LogTemp, Log, TEXT("物品堆叠: %s 槽位 %d, 数量 %d"), *ItemID.ToString(), i, CanAdd);
            }
        }
    }

    // === 阶段2：将剩余数量放入新空槽位 ===
    while (RemainingQuantity > 0)
    {
        int32 EmptySlot = FindEmptySlot();
        if (EmptySlot == -1)
        {
            // 背包已满，无法放入更多（之前堆叠的部分已经成功了！）
            UE_LOG(LogTemp, Warning, TEXT("无法添加物品: 背包已满 %s"), *ItemID.ToString());
            return false;  // 注意：此处返回 false 但前面可能已经加了部分
        }

        // 新槽位的数量 = 剩余量 与 单格上限 的较小值（应对单格放不完的情况）
        int32 CanAdd = ItemData->MaxStackSize > 0 ? FMath::Min(RemainingQuantity, ItemData->MaxStackSize) : 1;
        Inventory[EmptySlot] = FItemInstance(ItemID, CanAdd);
        RemainingQuantity -= CanAdd;

        UE_LOG(LogTemp, Log, TEXT("物品添加到新槽位: %s 槽位 %d, 数量 %d"), *ItemID.ToString(), EmptySlot, CanAdd);
    }

    // === 更新统计并广播事件 ===
    UpdateWeight();                    // 重新计算总重量
    CurrentItemCount++;                // 非空槽位数+1（新开了至少一个格子）

    // 广播事件通知 UI 刷新
    FItemInstance AddedItem(ItemID, Quantity);
    OnItemAdded.Broadcast(AddedItem);       // 传递型委托：告诉监听者具体添了什么
    BroadcastInventoryUpdate();             // 通用委托：触发 UI 全量/增量刷新

    return true;
}

// ============================================================================
//  RemoveItem — 按 ID 移除物品（跨槽位扣除）
// ============================================================================

/**
 * 从所有匹配 ItemID 的槽位中逐格扣除指定数量。
 * 先从第一个有该物品的槽开始扣，扣完该格再找下一个。
 * 扣完后如果某格数量归零 → Empty() 清空该格。
 *
 * @param ItemID   要移除的物品ID
 * @param Quantity 要移除的数量
 * @return         实际移除了 >0 个则返回 true
 */
bool UInventoryComponent::RemoveItem(FName ItemID, int32 Quantity)
{
    if (Quantity <= 0) return false;

    int32 TotalRemoved = 0;

    // 遍历所有槽位，逐一扣除直到满足 Quantity 或遍历完
    for (int32 i = 0; i < Inventory.Num() && TotalRemoved < Quantity; i++)
    {
        if (Inventory[i].ItemID == ItemID)
        {
            // 本格最多能扣除多少 = (需求剩余量, 本格存量) 取小值
            int32 CanRemove = FMath::Min(Quantity - TotalRemoved, Inventory[i].Quantity);
            Inventory[i].Quantity -= CanRemove;
            TotalRemoved += CanRemove;

            // 本格扣完了 → 清空槽位（释放给其他物品使用）
            if (Inventory[i].Quantity <= 0)
            {
                Inventory[i].Empty();
            }
        }
    }

    if (TotalRemoved > 0)
    {
        UpdateWeight();
        CurrentItemCount--;

        FItemInstance RemovedItem(ItemID, TotalRemoved);
        OnItemRemoved.Broadcast(RemovedItem);     // 通知 UI：某物品被移除了
        BroadcastInventoryUpdate();

        return true;
    }

    return false;  // 背包里没有这个物品
}

// ============================================================================
//  RemoveItemAt — 按槽位索引移除（精确操作）
// ============================================================================

/**
 * 从指定索引槽位精确移除物品。
 * 特殊处理：如果移除的是当前装备武器的槽位 → 自动解除装备状态
 *
 * @param SlotIndex 目标槽位 [0, MaxSlots)
 * @param Quantity  要移除的数量
 * @return          成功返回 true
 */
bool UInventoryComponent::RemoveItemAt(int32 SlotIndex, int32 Quantity)
{
    // 边界和有效性检查
    if (!Inventory.IsValidIndex(SlotIndex)) return false;
    if (Quantity <= 0) return false;

    FItemInstance& Item = Inventory[SlotIndex];
    if (Item.IsEmpty()) return false;  // 已经是空格了

    // 计算实际可扣除量
    int32 CanRemove = FMath::Min(Quantity, Item.Quantity);
    Item.Quantity -= CanRemove;

    // 如果本格扣完（数量<=0），执行清理
    if (Item.Quantity <= 0)
    {
        // ★ 如果卸掉的是当前装备的武器 → 自动解除装备
        if (SlotIndex == EquippedSlotIndex)
        {
            FName OldItemID = Item.ItemID;  // 保存 ID 用于广播（因为下面要 Empty 掉）
            EquippedSlotIndex = -1;          // 重置装备状态
            OnEquipmentChanged.Broadcast(OldItemID, false);  // 通知角色卸下武器模型
        }

        Item.Empty();          // 清空槽位数据
        CurrentItemCount--;    // 非空格数减1
    }

    UpdateWeight();  // 重新计算总重量

    // 广播移除事件
    FItemInstance RemovedItem(Item.ItemID, CanRemove);
    OnItemRemoved.Broadcast(RemovedItem);
    BroadcastInventoryUpdate();

    return true;
}

// ============================================================================
//  UseItem — 使用物品（核心消费流程）
// ============================================================================

/**
 * 使用指定槽位的物品——这是整个物品系统的核心执行入口。
 *
 * 【完整流程】
 * 1. 校验槽位有效且非空
 * 2. 通过 Subsystem 读取 ItemData，检查 bCanUse 标志
 * 3. 权限校验：必须在服务器端执行（HasAuthority）
 * 4. 加载 ItemActionClasses 中注册的所有 Action 类：
 *    a. LoadSynchronous() 同步加载 Action UClass
 *    b. NewObject<Action>(this, Class) 创建实例
 *    c. InitializeFromItemData(ItemData) 从 DataAsset 读取参数初始化 Action
 *    d. Execute(Inventory, SlotIndex, Instigator) 执行效果
 *    e. 任一 Action 返回 true → bConsumed = true
 * 5. 如果 bConsumed == true:
 *    → RemoveItemAt(SlotIndex, 1) 扣减一个数量
 *    → OnItemUsed 广播使用事件
 *    → BroadcastInventoryUpdate 刷新UI
 *
 * 【无 ActionClasses 的回退行为】
 * 如果 ItemActionClasses 为空列表但 ItemType==Consumable → 也标记为已消费
 * （兼容简单消耗品不需要自定义 Action 的情况）
 *
 * @param SlotIndex 要使用的物品所在槽位索引
 * @return          流程是否完整执行（true不代表一定消费了，false表示校验失败）
 */
bool UInventoryComponent::UseItem(int32 SlotIndex)
{
    // 基础校验
    if (!Inventory.IsValidIndex(SlotIndex)) return false;

    FItemInstance& Item = Inventory[SlotIndex];
    if (Item.IsEmpty()) return false;

    // 获取物品静态配置数据
    UItemDataBase* ItemData = GetItemData(Item.ItemID);
    if (!ItemData || !ItemData->bCanUse)
    {
        UE_LOG(LogTemp, Warning, TEXT("无法使用物品: %s（不可用或数据缺失）"), *Item.ItemID.ToString());
        return false;
    }

    // ★ 强制在服务器执行（多人游戏时客户端不能直接修改服务端背包数据）
    if (!GetOwner() || !GetOwner()->HasAuthority())
    {
        UE_LOG(LogTemp, Warning, TEXT("UseItem 必须在服务器上执行"));
        return false;
    }

    // === 执行 ItemAction 列表（策略模式的核心循环）===
    bool bConsumed = false;
    if (ItemData->ItemActionClasses.Num() > 0)
    {
        AActor* Instigator = GetOwner();  // 触发者通常是拥有此组件的角色

        for (const TSoftClassPtr<UItemAction>& SoftActionClass : ItemData->ItemActionClasses)
        {
            if (SoftActionClass.IsNull()) continue;  // 跳过空的引用

            // 同步加载 Action 的 UClass（Action 类通常很小，同步加载开销可接受）
            UClass* ActionClass = SoftActionClass.LoadSynchronous();
            if (!ActionClass) continue;

            // 创建 Action 实例（Outer=this 让 GC 随组件一起管理生命周期）
            UItemAction* Action = NewObject<UItemAction>(this, ActionClass);
            if (!Action) continue;

            // 用物品数据初始化 Action 参数（子类会 Cast 到具体类型读取字段）
            Action->InitializeFromItemData(ItemData);

            // ★ 执行 Action —— 返回 true 表示该物品已被消费
            bool bThisConsumed = Action->Execute(this, SlotIndex, Instigator);
            bConsumed = bConsumed || bThisConsumed;  // 任一 Action 消费即标记为已消费
        }
    }
    else
    {
        // 无自定义 Action 但是消耗品类型 → 直接标记为已消费（最简单的回退行为）
        bConsumed = (ItemData->ItemType == EItemType::Consumable);
    }

    // === 如果被消费了，执行扣减和广播 ===
    if (bConsumed)
    {
        RemoveItemAt(SlotIndex, 1);              // 数量 -1
        OnItemUsed.Broadcast(FItemInstance(Item.ItemID, 1));  // 通知外部"使用了XX"
        BroadcastInventoryUpdate();              // 刷新 UI 显示
    }

    return true;
}

// ============================================================================
//  DropItem — 丢弃物品到场景
// ============================================================================

/**
 * 将指定槽位的物品丢弃到世界中生成 APickupItem Actor。
 *
 * 流程：
 * 1. 读取 ItemData 检查 bCanDrop
 * 2. 计算掉落位置（拥有者正前方 100cm）
 * 3. LoadSynchronous 加载 ItemClass（掉落物蓝图类）
 * 4. SpawnActor 生成掉落物（碰撞处理设为 AdjustIfPossibleButAlwaysSpawn）
 * 5. 如果是 APickupItem → InitializePickup 设置 ItemID/Quantity
 * 6. RemoveItemAt 整格移出背包
 *
 * @param SlotIndex 要丢弃的物品槽位索引
 */
void UInventoryComponent::DropItem(int32 SlotIndex)
{
    if (!Inventory.IsValidIndex(SlotIndex)) return;

    FItemInstance Item = Inventory[SlotIndex];
    if (Item.IsEmpty()) return;  // 空格不能丢

    // 获取物品配置数据，校验是否允许丢弃
    UItemDataBase* ItemData = GetItemData(Item.ItemID);
    if (!ItemData || !ItemData->bCanDrop)
    {
        UE_LOG(LogTemp, Warning, TEXT("无法丢弃物品（数据缺失或不可丢弃）: %s"), *Item.ItemID.ToString());
        return;
    }

    // 需要有有效的拥有者 Actor 来确定掉落位置
    if (AActor* Owner = GetOwner())
    {
        UWorld* World = Owner->GetWorld();
        if (World)
        {
            // 掉落位置 = 拥有者当前位置 + 正前方 100cm
            FVector DropLocation = Owner->GetActorLocation() + Owner->GetActorForwardVector() * 100.0f;
            FRotator DropRotation = Owner->GetActorRotation();

            // 软类加载确保可用（软引用可能尚未加载到内存）
            UClass* SpawnClass = nullptr;
            if (!ItemData->ItemClass.IsNull())
            {
                SpawnClass = ItemData->ItemClass.LoadSynchronous();
            }

            if (SpawnClass)
            {
                // 配置 Spawn 参数
                FActorSpawnParameters Params;
                Params.Owner = Owner;                          // 拥有者 = 丢东西的人
                Params.Instigator = Owner->GetInstigator();   // 造成者（用于伤害系统归属）
                Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
                // 即使位置有重叠也强制生成（避免满地都是东西时无法再丢）

                AActor* Spawned = World->SpawnActor<AActor>(SpawnClass, DropLocation, DropRotation, Params);
                if (Spawned)
                {
                    UE_LOG(LogTemp, Log, TEXT("已在世界中生成物品演员: %s 类型: %s"),
                        *Item.ItemID.ToString(), *SpawnClass->GetName());

                    // 兼容性处理：如果生成的 Actor 是 APickupItem（常见情况），初始化其数据
                    if (APickupItem* Pickup = Cast<APickupItem>(Spawned))
                    {
                        Pickup->InitializePickup(Item.ItemID, Item.Quantity);
                    }
                }
                else
                {
                    UE_LOG(LogTemp, Warning, TEXT("生成物品演员失败: %s"), *Item.ItemID.ToString());
                }
            }
            else
            {
                UE_LOG(LogTemp, Warning, TEXT("未指定 ItemClass，无法在世界中生成物品: %s"), *Item.ItemID.ToString());
            }
        }
    }

    // ★ 最后从背包中整格移除该物品（注意是在 Spawn 之后才移除，保证数据一致性）
    RemoveItemAt(SlotIndex, Item.Quantity);
}

// ============================================================================
//  SwapItems — 交换两个槽位
// ============================================================================

/** 简单的原地交换，TArray::Swap 是 O(1) 操作 */
void UInventoryComponent::SwapItems(int32 SlotIndex1, int32 SlotIndex2)
{
    if (!Inventory.IsValidIndex(SlotIndex1) || !Inventory.IsValidIndex(SlotIndex2)) return;
    if (SlotIndex1 == SlotIndex2) return;  // 自己和自己换没有意义

    Inventory.Swap(SlotIndex1, SlotIndex2);
    BroadcastInventoryUpdate();  // 通知 UI 刷新两个位置的显示
}

// ============================================================================
//  SortItems — 整理背包
// ============================================================================

/**
 * 整理算法：
 * 1. 提取所有非空 FItemInstance 到临时数组
 * 2. 按 ItemID 字典序排序（LexicalLess = ASCII 字符序）
 * 3. 回填到 Inventory 数组（排在前面的在前面的格子）
 * 4. 后续空格用 FItemInstance() 填充
 *
 * 结果视觉上：所有物品按名称字母顺序排列，空格集中在末尾
 */
void UInventoryComponent::SortItems()
{
    // 分离非空物品
    TArray<FItemInstance> NonEmptyItems;
    for (const FItemInstance& Item : Inventory)
    {
        if (!Item.IsEmpty())
        {
            NonEmptyItems.Add(Item);
        }
    }

    // 按 ItemID 字典序排列
    NonEmptyItems.Sort([](const FItemInstance& A, const FItemInstance& B) {
        return A.ItemID.LexicalLess(B.ItemID);
    });

    // 回填：前 N 格放物品，后面全清空
    for (int32 i = 0; i < Inventory.Num(); i++)
    {
        if (i < NonEmptyItems.Num())
        {
            Inventory[i] = NonEmptyItems[i];
        }
        else
        {
            Inventory[i].Empty();
        }
    }

    BroadcastInventoryUpdate();
}

// ============================================================================
//  查询功能实现
// ============================================================================

bool UInventoryComponent::HasItem(FName ItemID) const
{
    // 线性扫描查找任意数量>0的同ID物品
    for (const FItemInstance& Item : Inventory)
    {
        if (Item.ItemID == ItemID)
        {
            return true;
        }
    }
    return false;
}

int32 UInventoryComponent::GetItemCount(FName ItemID) const
{
    // 累加所有同ID槽位的数量
    int32 TotalCount = 0;
    for (const FItemInstance& Item : Inventory)
    {
        if (Item.ItemID == ItemID)
        {
            TotalCount += Item.Quantity;
        }
    }
    return TotalCount;
}

FItemInstance UInventoryComponent::GetItemAt(int32 SlotIndex) const
{
    if (Inventory.IsValidIndex(SlotIndex))
    {
        return Inventory[SlotIndex];  // 返回拷贝（值类型安全）
    }
    return FItemInstance();  // 无效索引返回空实例
}

void UInventoryComponent::SetItemAt(int32 SlotIndex, const FItemInstance& Item)
{
    if (!Inventory.IsValidIndex(SlotIndex)) return;

    Inventory[SlotIndex] = Item;
    BroadcastInventoryUpdate();  // 任何写入操作都通知 UI
}

int32 UInventoryComponent::FindItemSlot(FName ItemID) const
{
    // 返回第一个匹配的槽位索引（线性扫描）
    for (int32 i = 0; i < Inventory.Num(); i++)
    {
        if (Inventory[i].ItemID == ItemID)
        {
            return i;
        }
    }
    return -1;  // 未找到
}

int32 UInventoryComponent::FindEmptySlot() const
{
    for (int32 i = 0; i < Inventory.Num(); i++)
    {
        if (Inventory[i].IsEmpty())
        {
            return i;
        }
    }
    return -1;  // 背包满了
}

// ============================================================================
//  内部辅助方法
// ============================================================================

/**
 * 重新计算背包总重量
 * 遍历每个非空槽位 → GetItemData 读取 Weight → Quantity * Weight 累加
 *
 * 性能注意：每次 Add/Remove 都调用，O(N) 复杂度。
 * 对于 20 格背包完全可接受；若未来扩展到数百格可考虑增量更新优化。
 */
void UInventoryComponent::UpdateWeight()
{
    CurrentWeight = 0.0f;

    for (const FItemInstance& Item : Inventory)
    {
        if (!Item.IsEmpty())
        {
            UItemDataBase* ItemData = GetItemData(Item.ItemID);
            if (ItemData)
            {
                CurrentWeight += ItemData->Weight * Item.Quantity;
            }
        }
    }
}

/** 触发通用背包更新广播 */
void UInventoryComponent::BroadcastInventoryUpdate()
{
    OnInventoryUpdated.Broadcast();
}

// ============================================================================
//  Subsystem 数据桥接 — 获取物品配置数据
// ============================================================================

/**
 * 通过 UItemDataSubsystem 获取物品静态数据
 * 这是 InventoryComponent 访问 DA_xxx.uasset 配置的唯一入口
 */
UItemDataBase* UInventoryComponent::GetItemData(FName ItemID) const
{
	UWorld* World = GetWorld();
	if (!World) return nullptr;

	// 从 GameInstance 获取 Subsystem 单例，委托其懒加载 + 缓存机制
	if (UItemDataSubsystem* Subsystem = World->GetGameInstance()->GetSubsystem<UItemDataSubsystem>())
	{
		return Subsystem->GetItemData(ItemID);
	}

	return nullptr;
}

UWeaponData* UInventoryComponent::GetWeaponData(FName WeaponID) const
{
	UWorld* World = GetWorld();
	if (!World) return nullptr;

	if (UItemDataSubsystem* Subsystem = World->GetGameInstance()->GetSubsystem<UItemDataSubsystem>())
	{
		return Subsystem->GetWeaponData(WeaponID);
	}

	return nullptr;
}

// ============================================================================
//  装备管理实现
// ============================================================================

/**
 * 装备指定槽位的物品为当前武器
 *
 * 校验链：
 * 1. SlotIndex 有效?
 * 2. 该槽位非空?
 * 3. GetItemData 成功?
 * 4. ItemType == Weapon? (只有武器才能装备)
 * 5. 已有其他武器装备? → 先 Unequip 卸下旧的
 * 6. 设定 EquippedSlotIndex + 广播 OnEquipmentChanged(true)
 */
bool UInventoryComponent::EquipItem(int32 SlotIndex)
{
	// 参数校验
	if (!Inventory.IsValidIndex(SlotIndex))
	{
		UE_LOG(LogTemp, Warning, TEXT("[Equip] 无效槽位: %d"), SlotIndex);
		return false;
	}

	FItemInstance& TargetSlot = Inventory[SlotIndex];
	if (TargetSlot.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("[Equip] 槽位 %d 为空，无法装备"), SlotIndex);
		return false;
	}

	// 获取物品数据并验证类型
	UItemDataBase* ItemData = GetItemData(TargetSlot.ItemID);
	if (!ItemData || ItemData->ItemType != EItemType::Weapon)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Equip] 物品 %s 不是武器类型"), *TargetSlot.ItemID.ToString());
		return false;
	}

	// ★ 如果已有装备且不是同一把武器 → 先卸下旧武器
	if (EquippedSlotIndex >= 0 && EquippedSlotIndex != SlotIndex)
	{
		FName OldItemID = Inventory[EquippedSlotIndex].ItemID;
		EquippedSlotIndex = -1;
		OnEquipmentChanged.Broadcast(OldItemID, false);  // 通知旧武器卸下
	}

	// 设置新装备
	EquippedSlotIndex = SlotIndex;

	UE_LOG(LogTemp, Log, TEXT("[Equip] 已装备武器: %s (槽位 %d)"),
		*TargetSlot.ItemID.ToString(), SlotIndex);

	OnEquipmentChanged.Broadcast(TargetSlot.ItemID, true);  // 通知新武器装备
	BroadcastInventoryUpdate();

	return true;
}

/**
 * 卸下当前装备
 * 仅重置 EquippedSlotIndex 状态，不从背包移除物品
 * （武器仍然在背包原来的槽位里）
 */
void UInventoryComponent::UnequipItem()
{
	if (EquippedSlotIndex < 0)
	{
		return;  // 未装备，无需操作
	}

	FName OldItemID = Inventory[EquippedSlotIndex].ItemID;
	EquippedSlotIndex = -1;

	UE_LOG(LogTemp, Log, TEXT("[Unequip] 已卸下武器: %s"), *OldItemID.ToString());

	OnEquipmentChanged.Broadcast(OldItemID, false);
	BroadcastInventoryUpdate();
}

/** 获取当前装备的武器数据（带 Subsystem 查询 + 类型安全 Cast）*/
UWeaponData* UInventoryComponent::GetEquippedWeaponData() const
{
	if (EquippedSlotIndex < 0)
	{
		return nullptr;
	}

	const FItemInstance& Slot = Inventory[EquippedSlotIndex];
	if (Slot.IsEmpty())
	{
		return nullptr;
	}

	return GetWeaponData(Slot.ItemID);
}

FName UInventoryComponent::GetEquippedItemID() const
{
	if (EquippedSlotIndex < 0 || !Inventory.IsValidIndex(EquippedSlotIndex))
	{
		return NAME_None;
	}
	return Inventory[EquippedSlotIndex].ItemID;
}

// ============================================================================
//  快捷栏系统（Quick Slot / Hotbar）实现
// ============================================================================

/**
 * 选中快捷栏槽位（数字键 1-5 或滚轮切换）
 *
 * ★ Minecraft 模式设计要点：
 * 此方法只做选中切换和高亮显示，不触发使用操作！
 * 使用由 UseSelectedQuickSlot() 或右键长按 UseHeldItem() 驱动。
 * 这样可以避免误触数字键就吃掉了药水的问题。
 *
 * 如果按的是已经选中的槽位 → 不做任何事（幂等保护）
 */
bool UInventoryComponent::SelectQuickSlot(int32 SlotIndex)
{
	// 边界检查 [0, QUICK_SLOT_COUNT)
	if (SlotIndex < 0 || SlotIndex >= QUICK_SLOT_COUNT)
	{
		return false;
	}

	// 再次按同一槽位 → 忽略（避免重复触发选中事件的边界问题）
	if (SlotIndex == SelectedQuickSlotIndex)
	{
		return true;
	}

	// 记录旧索引用于日志
	int32 PreviousIndex = SelectedQuickSlotIndex;
	SelectedQuickSlotIndex = SlotIndex;

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] Selected slot %d (previous: %d)"), SlotIndex, PreviousIndex);

	// 广播快捷栏选中变更（UI 监听此事件来切换高亮边框/显示手部模型）
	OnQuickSlotSelected.Broadcast(SlotIndex);
	return true;
}

/**
 * 使用当前选中的快捷栏物品
 *
 * 根据 ItemType 分支处理：
 *
 * 【Weapon 分支】
 *   1. 在主背包 FindItemSlot 找该武器
 *   2. 找到了 → EquipItem(InvSlot) 装备它
 *   3. 没找到（可能全拖到快捷栏了）→ 先 AddItem 回背包，再用新位置 EquipItem
 *
 * 【Consumable 分支】
 *   1. 在主背包 FindItemSlot 找该消耗品
 *   2. 找到了 → UseItem(InvSlot)（内部执行 Action + RemoveItemAt）
 *      → 同步更新快捷栏数量（SlotItem.Quantity--）
 *      → 用完了 ClearQuickSlot，还有余量则 OnQuickSlotChanged 刷新数字
 *   3. 背包中没有（全部在快捷栏）→ 直接扣减快捷栏数量
 *      → 手动执行 ItemAction（因为不走 UseItem 通道了）
 *      → 用完清空 / 有余量刷新
 *
 * @return 操作是否成功
 */
bool UInventoryComponent::UseSelectedQuickSlot()
{
	// 基础校验
	if (SelectedQuickSlotIndex < 0 || SelectedQuickSlotIndex >= QUICK_SLOT_COUNT)
	{
		return false;
	}

	FItemInstance& SlotItem = QuickSlots[SelectedQuickSlotIndex];
	if (SlotItem.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("[QuickSlot] Slot %d is empty, nothing to use"), SelectedQuickSlotIndex);
		return false;
	}

	// 获取物品配置数据
	UItemDataBase* ItemData = GetItemData(SlotItem.ItemID);
	if (!ItemData)
	{
		UE_LOG(LogTemp, Warning, TEXT("[QuickSlot] Cannot find item data for %s"), *SlotItem.ItemID.ToString());
		return false;
	}

	bool bSuccess = false;

	switch (ItemData->ItemType)
	{
	case EItemType::Weapon:
	{
		// ===== 武器：需要在背包中有对应物品才能装备 =====
		int32 InvSlot = FindItemSlot(SlotItem.ItemID);
		if (InvSlot < 0)
		{
			// 背包中没有这把武器（可能用户把唯一的那个也拖进快捷栏了）
			// → 先 AddItem 放回背包，再用新位置装备
			if (AddItem(SlotItem.ItemID, SlotItem.Quantity))
			{
				InvSlot = FindItemSlot(SlotItem.ItemID);
			}
		}
		if (InvSlot >= 0)
		{
			bSuccess = EquipItem(InvSlot);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[QuickSlot] 武器 %s 无法放入背包进行装备"), *SlotItem.ItemID.ToString());
		}
		break;
	}

	case EItemType::Consumable:
	{
		// ===== 消耗品：优先走背包标准 UseItem 通道 =====
		int32 InvSlot = FindItemSlot(SlotItem.ItemID);
		if (InvSlot >= 0)
		{
			// 背包里有 → 走标准通道（自动执行 Action + 扣减 + 广播）
			bSuccess = UseItem(InvSlot);

			if (bSuccess)
			{
				// ★ 同步快捷栏显示数量与背包一致
				SlotItem.Quantity--;

				// 快捷栏里的也用完了 → 清空该格
				if (SlotItem.Quantity <= 0 || !HasItem(SlotItem.ItemID))
				{
					ClearQuickSlot(SelectedQuickSlotIndex);
				}
				else
				{
					// 还有剩余 → 广播更新让 UI 刷新数字显示
					OnQuickSlotChanged.Broadcast(SelectedQuickSlotIndex);
				}
			}
		}
		else
		{
			// ★ 背包中没有该消耗品（全部在快捷栏中）→ 手动处理
			SlotItem.Quantity--;
			if (SlotItem.Quantity <= 0)
			{
				ClearQuickSlot(SelectedQuickSlotIndex);
			}
			else
			{
				OnQuickSlotChanged.Broadcast(SelectedQuickSlotIndex);
			}

			// 手动执行 ItemAction 效果（绕过 UseItem 因为背包里没这个东西）
			if (ItemData->ItemActionClasses.Num() > 0)
			{
				AActor* Instigator = GetOwner();
				for (const TSoftClassPtr<UItemAction>& SoftActionClass : ItemData->ItemActionClasses)
				{
					if (SoftActionClass.IsNull()) continue;
					UClass* ActionClass = SoftActionClass.LoadSynchronous();
					if (!ActionClass) continue;

					UItemAction* Action = NewObject<UItemAction>(this, ActionClass);
					if (!Action) continue;

					Action->InitializeFromItemData(ItemData);
					Action->Execute(this, SelectedQuickSlotIndex, Instigator);
				}
				bSuccess = true;
			}
			else if (ItemData->ItemType == EItemType::Consumable)
			{
				// 简单消耗品无 ActionClasses → 标记为已消费（数量已在上面扣了）
				bSuccess = true;
			}
		}
		break;
	}

	default:
		// 其他类型（材料、任务物品等）暂不支持从快捷栏使用
		UE_LOG(LogTemp, Log, TEXT("[QuickSlot] Item %s type (%d) not usable from quickslot"),
			*SlotItem.ItemID.ToString(), (int32)ItemData->ItemType);
		break;
	}

	return bSuccess;
}

bool UInventoryComponent::SetQuickSlot(int32 SlotIndex, const FItemInstance& Item)
{
	if (SlotIndex < 0 || SlotIndex >= QUICK_SLOT_COUNT)
	{
		return false;
	}

	QuickSlots[SlotIndex] = Item;

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] Set slot %d to item %s x%d"),
		SlotIndex, *Item.ItemID.ToString(), Item.Quantity);

	OnQuickSlotChanged.Broadcast(SlotIndex);
	return true;
}

FItemInstance UInventoryComponent::GetQuickSlot(int32 SlotIndex) const
{
	if (SlotIndex >= 0 && SlotIndex < QuickSlots.Num())
	{
		return QuickSlots[SlotIndex];
	}
	return FItemInstance();  // 无效索引返回空
}

void UInventoryComponent::ClearQuickSlot(int32 SlotIndex)
{
	if (SlotIndex < 0 || SlotIndex >= QUICK_SLOT_COUNT)
	{
		return;
	}

	QuickSlots[SlotIndex].Empty();

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] Cleared slot %d"), SlotIndex);

	OnQuickSlotChanged.Broadcast(SlotIndex);
}
