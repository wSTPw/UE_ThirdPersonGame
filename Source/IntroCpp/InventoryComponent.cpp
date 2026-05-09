// Fill out your copyright notice in the Description page of Project Settings.

#include "InventoryComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"
#include "PickupItem.h"
#include "ItemAction.h"
#include "ItemDataSubsystem.h"    // GetSubsystem<UItemDataSubsystem>() 需要

// 设置组件默认值
UInventoryComponent::UInventoryComponent()
{
    PrimaryComponentTick.bCanEverTick = true;

    // 初始化背包大小
    Inventory.Init(FItemInstance(), MaxSlots);
    CurrentWeight = 0.0f;
    CurrentItemCount = 0;

    // 初始化快捷栏（5个空槽位）
    QuickSlots.Init(FItemInstance(), QUICK_SLOT_COUNT);
    SelectedQuickSlotIndex = 0;
}

void UInventoryComponent::BeginPlay()
{
    Super::BeginPlay();
    
    // 确保背包大小正确
    if (Inventory.Num() != MaxSlots)
    {
        Inventory.SetNum(MaxSlots);
        for (int32 i = 0; i < MaxSlots; i++)
        {
            Inventory[i] = FItemInstance();
        }
    }
    
    // 广播初始状态
    BroadcastInventoryUpdate();
}

void UInventoryComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

// 添加物品到背包
bool UInventoryComponent::AddItem(FName ItemID, int32 Quantity)
{
    if (Quantity <= 0) return false;
    
    // 通过 Subsystem 获取物品数据（返回指针，nullptr 表示未找到）
    UItemDataBase* ItemData = GetItemData(ItemID);
    if (!ItemData)
    {
        UE_LOG(LogTemp, Warning, TEXT("无法添加物品: 未找到物品数据 %s"), *ItemID.ToString());
        return false;
    }
    
    // 检查重量限制
    if (!CanCarryWeight(ItemData->Weight * Quantity))
    {
        UE_LOG(LogTemp, Warning, TEXT("无法添加物品: 超重 %s x %d"), *ItemID.ToString(), Quantity);
        return false;
    }
    
    int32 RemainingQuantity = Quantity;
    
    // 尝试堆叠到现有物品
    if (ItemData->MaxStackSize > 1)
    {
        for (int32 i = 0; i < Inventory.Num() && RemainingQuantity > 0; i++)
        {
            if (Inventory[i].ItemID == ItemID && Inventory[i].Quantity < ItemData->MaxStackSize)
            {
                int32 CanAdd = FMath::Min(RemainingQuantity, ItemData->MaxStackSize - Inventory[i].Quantity);
                Inventory[i].Quantity += CanAdd;
                RemainingQuantity -= CanAdd;
                
                UE_LOG(LogTemp, Log, TEXT("物品堆叠: %s 槽位 %d, 数量 %d"), *ItemID.ToString(), i, CanAdd);
            }
        }
    }
    
    // 添加剩余物品到新槽位
    while (RemainingQuantity > 0)
    {
        int32 EmptySlot = FindEmptySlot();
        if (EmptySlot == -1)
        {
            UE_LOG(LogTemp, Warning, TEXT("无法添加物品: 背包已满 %s"), *ItemID.ToString());
            return false; // 背包已满
        }
        
        int32 CanAdd = ItemData->MaxStackSize > 0 ? FMath::Min(RemainingQuantity, ItemData->MaxStackSize) : 1;
        Inventory[EmptySlot] = FItemInstance(ItemID, CanAdd);
        RemainingQuantity -= CanAdd;
        
        UE_LOG(LogTemp, Log, TEXT("物品添加到新槽位: %s 槽位 %d, 数量 %d"), *ItemID.ToString(), EmptySlot, CanAdd);
    }
    
    // 更新统计
    UpdateWeight();
    CurrentItemCount++;
    
    // 广播事件
    FItemInstance AddedItem(ItemID, Quantity);
    OnItemAdded.Broadcast(AddedItem);
    BroadcastInventoryUpdate();
    
    return true;
}

// 从背包移除物品
bool UInventoryComponent::RemoveItem(FName ItemID, int32 Quantity)
{
    if (Quantity <= 0) return false;
    
    int32 TotalRemoved = 0;
    
    // 遍历所有槽位移除物品
    for (int32 i = 0; i < Inventory.Num() && TotalRemoved < Quantity; i++)
    {
        if (Inventory[i].ItemID == ItemID)
        {
            int32 CanRemove = FMath::Min(Quantity - TotalRemoved, Inventory[i].Quantity);
            Inventory[i].Quantity -= CanRemove;
            TotalRemoved += CanRemove;
            
            // 如果物品数量归零，清空槽位
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
        OnItemRemoved.Broadcast(RemovedItem);
        BroadcastInventoryUpdate();
        
        return true;
    }
    
    return false;
}

// 从指定槽位移除物品
bool UInventoryComponent::RemoveItemAt(int32 SlotIndex, int32 Quantity)
{
    if (!Inventory.IsValidIndex(SlotIndex)) return false;
    if (Quantity <= 0) return false;
    
    FItemInstance& Item = Inventory[SlotIndex];
    if (Item.IsEmpty()) return false;
    
    int32 CanRemove = FMath::Min(Quantity, Item.Quantity);
    Item.Quantity -= CanRemove;
    
    // 如果物品数量归零，清空槽位
    if (Item.Quantity <= 0)
    {
        // ★ 如果卸掉的是当前装备的武器，自动解除装备
        if (SlotIndex == EquippedSlotIndex)
        {
            FName OldItemID = Item.ItemID;
            EquippedSlotIndex = -1;
            OnEquipmentChanged.Broadcast(OldItemID, false);
        }

        Item.Empty();
        CurrentItemCount--;
    }
    
    UpdateWeight();
    
    FItemInstance RemovedItem(Item.ItemID, CanRemove);
    OnItemRemoved.Broadcast(RemovedItem);
    BroadcastInventoryUpdate();
    
    return true;
}

// 使用物品
bool UInventoryComponent::UseItem(int32 SlotIndex)
{
    if (!Inventory.IsValidIndex(SlotIndex)) return false;

    FItemInstance& Item = Inventory[SlotIndex];
    if (Item.IsEmpty()) return false;

    // 通过 Subsystem 读取物品数据
    UItemDataBase* ItemData = GetItemData(Item.ItemID);
    if (!ItemData || !ItemData->bCanUse)
    {
        UE_LOG(LogTemp, Warning, TEXT("无法使用物品: %s"), *Item.ItemID.ToString());
        return false;
    }

    // 强制在服务器执行（必须在服务器端调用该函数或通过 RPC 请求服务器调用）
    if (!GetOwner() || !GetOwner()->HasAuthority())
    {
        UE_LOG(LogTemp, Warning, TEXT("UseItem 必须在服务器上执行"));
        return false;
    }

    // 如果配置了 ItemActionClasses，则逐个加载类并创建实例执行
    bool bConsumed = false;
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

		// 用 UItemDataBase 指针初始化动作参数（子类会 Cast 到具体类型）
		Action->InitializeFromItemData(ItemData);

		// 执行动作
		bool bThisConsumed = Action->Execute(this, SlotIndex, Instigator);
		bConsumed = bConsumed || bThisConsumed;
	}
    }
    else
    {
        bConsumed = (ItemData->ItemType == EItemType::Consumable);
    }

    // 如果 action 返回已消费，移除一单位并广播
    if (bConsumed)
    {
        RemoveItemAt(SlotIndex, 1);
        OnItemUsed.Broadcast(FItemInstance(Item.ItemID, 1));
        BroadcastInventoryUpdate();
    }

    return true;
}

// 丢弃物品
void UInventoryComponent::DropItem(int32 SlotIndex)
{
    if (!Inventory.IsValidIndex(SlotIndex)) return;

    FItemInstance Item = Inventory[SlotIndex];
    if (Item.IsEmpty()) return;

    // 通过 Subsystem 获取物品数据
    UItemDataBase* ItemData = GetItemData(Item.ItemID);
    if (!ItemData || !ItemData->bCanDrop)
    {
        UE_LOG(LogTemp, Warning, TEXT("无法丢弃物品（数据缺失或不可丢弃）: %s"), *Item.ItemID.ToString());
        return;
    }

    // 计算出生位置（在拥有者前方）
    if (AActor* Owner = GetOwner())
    {
        UWorld* World = Owner->GetWorld();
        if (World)
        {
            FVector DropLocation = Owner->GetActorLocation() + Owner->GetActorForwardVector() * 100.0f;
            FRotator DropRotation = Owner->GetActorRotation();

            // 软类可能未被加载，使用 LoadSynchronous 以确保类可用
            UClass* SpawnClass = nullptr;
            if (!ItemData->ItemClass.IsNull())
            {
                SpawnClass = ItemData->ItemClass.LoadSynchronous();
            }

            if (SpawnClass)
            {
                FActorSpawnParameters Params;
                Params.Owner = Owner;
                Params.Instigator = Owner->GetInstigator();
                Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

                AActor* Spawned = World->SpawnActor<AActor>(SpawnClass, DropLocation, DropRotation, Params);
                if (Spawned)
                {
                    UE_LOG(LogTemp, Log, TEXT("已在世界中生成物品演员: %s 类型: %s"), *Item.ItemID.ToString(), *SpawnClass->GetName());

                    // 如果生成的是 APickupItem（常见情况），初始化其 ItemID/数量
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

    // 从背包中移除该槽位的物品（整格移除）
    RemoveItemAt(SlotIndex, Item.Quantity);
}

// 交换两个槽位的物品
void UInventoryComponent::SwapItems(int32 SlotIndex1, int32 SlotIndex2)
{
    if (!Inventory.IsValidIndex(SlotIndex1) || !Inventory.IsValidIndex(SlotIndex2)) return;
    if (SlotIndex1 == SlotIndex2) return;
    
    Inventory.Swap(SlotIndex1, SlotIndex2);
    BroadcastInventoryUpdate();
}

// 整理背包（按类型和ID排序）
void UInventoryComponent::SortItems()
{
    // 先分离空槽位和物品
    TArray<FItemInstance> NonEmptyItems;
    for (const FItemInstance& Item : Inventory)
    {
        if (!Item.IsEmpty())
        {
            NonEmptyItems.Add(Item);
        }
    }
    
    // 按物品ID排序
    NonEmptyItems.Sort([](const FItemInstance& A, const FItemInstance& B) {
        return A.ItemID.LexicalLess(B.ItemID);
    });
    
    // 重新填充背包
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

// 检查是否拥有物品
bool UInventoryComponent::HasItem(FName ItemID) const
{
    for (const FItemInstance& Item : Inventory)
    {
        if (Item.ItemID == ItemID)
        {
            return true;
        }
    }
    return false;
}

// 获取物品数量
int32 UInventoryComponent::GetItemCount(FName ItemID) const
{
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

// 获取指定槽位的物品
FItemInstance UInventoryComponent::GetItemAt(int32 SlotIndex) const
{
    if (Inventory.IsValidIndex(SlotIndex))
    {
        return Inventory[SlotIndex];
    }
    return FItemInstance();
}

void UInventoryComponent::SetItemAt(int32 SlotIndex, const FItemInstance& Item)
{
    if (!Inventory.IsValidIndex(SlotIndex)) return;

    Inventory[SlotIndex] = Item;
    BroadcastInventoryUpdate();
}

// 查找物品槽位
int32 UInventoryComponent::FindItemSlot(FName ItemID) const
{
    for (int32 i = 0; i < Inventory.Num(); i++)
    {
        if (Inventory[i].ItemID == ItemID)
        {
            return i;
        }
    }
    return -1;
}

// 查找空槽位
int32 UInventoryComponent::FindEmptySlot() const
{
    for (int32 i = 0; i < Inventory.Num(); i++)
    {
        if (Inventory[i].IsEmpty())
        {
            return i;
        }
    }
    return -1;
}

// 更新重量统计
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

// 广播背包更新事件
void UInventoryComponent::BroadcastInventoryUpdate()
{
    OnInventoryUpdated.Broadcast();
}

// 通过 UItemDataSubsystem 获取物品数据（替代原 DataTable.FindRow）
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

// ============================================================================
// 装备管理
// ============================================================================

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

bool UInventoryComponent::EquipItem(int32 SlotIndex)
{
	// 校验槽位有效性
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

	// 获取物品数据，校验是否为武器类型
	UItemDataBase* ItemData = GetItemData(TargetSlot.ItemID);
	if (!ItemData || ItemData->ItemType != EItemType::Weapon)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Equip] 物品 %s 不是武器类型"), *TargetSlot.ItemID.ToString());
		return false;
	}

	// 如果已有装备 → 先卸下旧武器
	if (EquippedSlotIndex >= 0 && EquippedSlotIndex != SlotIndex)
	{
		FName OldItemID = Inventory[EquippedSlotIndex].ItemID;
		EquippedSlotIndex = -1;
		OnEquipmentChanged.Broadcast(OldItemID, false);
	}

	// 设置新装备
	EquippedSlotIndex = SlotIndex;

	UE_LOG(LogTemp, Log, TEXT("[Equip] 已装备武器: %s (槽位 %d)"),
		*TargetSlot.ItemID.ToString(), SlotIndex);

	OnEquipmentChanged.Broadcast(TargetSlot.ItemID, true);
	BroadcastInventoryUpdate();

	return true;
}

void UInventoryComponent::UnequipItem()
{
	if (EquippedSlotIndex < 0)
	{
		return; // 未装备，无需操作
	}

	FName OldItemID = Inventory[EquippedSlotIndex].ItemID;
	EquippedSlotIndex = -1;

	UE_LOG(LogTemp, Log, TEXT("[Unequip] 已卸下武器: %s"), *OldItemID.ToString());

	OnEquipmentChanged.Broadcast(OldItemID, false);
	BroadcastInventoryUpdate();
}

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
// 快捷栏系统（Quick Slot / Hotbar）
// ============================================================================

bool UInventoryComponent::SelectQuickSlot(int32 SlotIndex)
{
	// 边界检查
	if (SlotIndex < 0 || SlotIndex >= QUICK_SLOT_COUNT)
	{
		return false;
	}

	// ★ Minecraft 模式：切换快捷栏只做选中/显示模型，使用物品由右键长按触发（UseHeldItem）
	// 如果按的是已选中的槽位 → 不做任何事（避免重复触发）
	if (SlotIndex == SelectedQuickSlotIndex)
	{
		return true;
	}

	// 切换选中
	int32 PreviousIndex = SelectedQuickSlotIndex;
	SelectedQuickSlotIndex = SlotIndex;

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] Selected slot %d (previous: %d)"), SlotIndex, PreviousIndex);

	OnQuickSlotSelected.Broadcast(SlotIndex);
	return true;
}

bool UInventoryComponent::UseSelectedQuickSlot()
{
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

	// 获取物品数据
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
		// 武器：优先在背包中找并装备；找不到则先放回背包再装备（处理"全拖到快捷栏"的场景）
		int32 InvSlot = FindItemSlot(SlotItem.ItemID);
		if (InvSlot < 0)
		{
			// 背包中没有 → 先 AddItem 回背包，再用新位置装备
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
		// 消耗品：优先在背包中找到并使用；背包没有则直接扣减快捷栏数量
		int32 InvSlot = FindItemSlot(SlotItem.ItemID);
		if (InvSlot >= 0)
		{
			bSuccess = UseItem(InvSlot);

			if (bSuccess)
			{
				// 更新快捷栏数量（与背包同步）
				SlotItem.Quantity--;

				// 用完了 → 清空快捷槽
				if (SlotItem.Quantity <= 0 || !HasItem(SlotItem.ItemID))
				{
					ClearQuickSlot(SelectedQuickSlotIndex);
				}
				else
				{
					// 还有剩余 → 广播更新让 UI 刷新数量
					OnQuickSlotChanged.Broadcast(SelectedQuickSlotIndex);
				}
			}
		}
		else
		{
			// 背包中没有该消耗品（全在快捷栏）→ 直接扣减快捷栏数量
			SlotItem.Quantity--;
			if (SlotItem.Quantity <= 0)
			{
				ClearQuickSlot(SelectedQuickSlotIndex);
			}
			else
			{
				OnQuickSlotChanged.Broadcast(SelectedQuickSlotIndex);
			}

			// 执行物品效果（通过 ItemAction）
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
				// 简单消耗品无 ActionClasses → 标记为已消费
				bSuccess = true;
			}
		}
		break;
	}

	default:
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
	return FItemInstance();
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
