// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ItemDataBase.h"    // FItemInstance + UPrimaryDataAsset 基类
#include "WeaponData.h"      // UWeaponData（装备查询需要）
#include "EWeaponTypes.h"    // EItemType（判断武器类型需要）
#include "InventoryComponent.generated.h"

// 背包改变委托（用于UI更新）
DECLARE_MULTICAST_DELEGATE(FOnInventoryUpdated);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnItemAdded, const FItemInstance&);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnItemRemoved, const FItemInstance&);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnItemUsed, const FItemInstance&);

// 装备变更委托（动态，支持蓝图绑定 + UFUNCTION AddDynamic）
// 参数：物品ID, 是否装备中
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnEquipmentChanged, FName, ItemID, bool, bEquipped);

/** 快捷栏选中变更委托 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuickSlotSelected, int32, SlotIndex);

/** 快捷栏内容变更委托（设置/使用/清除时广播） */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuickSlotChanged, int32, SlotIndex);

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class INTROCPP_API UInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UInventoryComponent();

protected:
    virtual void BeginPlay() override;

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // ==========================================
    // 背包属性
    // ==========================================
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
    int32 MaxSlots = 20;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
    float MaxWeight = 100.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    float CurrentWeight = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    int32 CurrentItemCount = 0;

    // ==========================================
    // 背包操作
    // ==========================================
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool AddItem(FName ItemID, int32 Quantity = 1);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool RemoveItem(FName ItemID, int32 Quantity = 1);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool RemoveItemAt(int32 SlotIndex, int32 Quantity = 1);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool UseItem(int32 SlotIndex);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void DropItem(int32 SlotIndex);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void SwapItems(int32 SlotIndex1, int32 SlotIndex2);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void SortItems();

    // ==========================================
    // 查询功能
    // ==========================================
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool HasItem(FName ItemID) const;

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    int32 GetItemCount(FName ItemID) const;

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool HasSpace() const { return CurrentItemCount < MaxSlots; }

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool CanCarryWeight(float Weight) const { return CurrentWeight + Weight <= MaxWeight; }

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    FItemInstance GetItemAt(int32 SlotIndex) const;

    /** 设置指定背包槽位内容（覆盖写入，用于拖拽交换等场景） */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void SetItemAt(int32 SlotIndex, const FItemInstance& Item);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    TArray<FItemInstance> GetAllItems() const { return Inventory; }

    /// 通过 UItemDataSubsystem 获取物品数据（替代原 DataTable 直接读取）
    /// @return 找到返回硬指针；未找到返回 nullptr
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    UItemDataBase* GetItemData(FName ItemID) const;

    /// 获取武器数据（便捷方法：内部 GetItemData + Cast）
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    UWeaponData* GetWeaponData(FName WeaponID) const;

    // ==========================================
    // 装备管理
    // ==========================================

    /** 当前装备所在槽位 (-1 = 未装备) */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Equipment")
    int32 EquippedSlotIndex = -1;

    /** 装备变更委托 */
    FOnEquipmentChanged OnEquipmentChanged;

    // ==========================================
    // 背包事件委托实例
    // ==========================================
    FOnInventoryUpdated OnInventoryUpdated;
    FOnItemAdded OnItemAdded;
    FOnItemRemoved OnItemRemoved;
    FOnItemUsed OnItemUsed;

    /**
     * 装备指定槽位的物品（必须是 Weapon 类型）
     * 如果已有装备，先自动卸下旧武器，再装备新武器
     *
     * @param SlotIndex  背包槽位索引
     * @return           成功返回 true；无效槽位/非武器类型返回 false
     */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    bool EquipItem(int32 SlotIndex);

    /** 卸下当前装备（重置 EquippedSlotIndex 为 -1） */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    void UnequipItem();

    /** 获取当前装备的武器数据指针（通过 Subsystem 懒加载 + Cast） */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    UWeaponData* GetEquippedWeaponData() const;

    /** 是否已装备武器 */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    bool IsWeaponEquipped() const { return EquippedSlotIndex >= 0; }

    /** 获取当前装备的 ItemID（未装备返回 NAME_None） */
    FName GetEquippedItemID() const;

    // ==========================================
    // 快捷栏系统（Quick Slot / Hotbar）
    // ==========================================

    static const int32 QUICK_SLOT_COUNT = 5;

    /** 5 个快捷槽位（存储物品实例，不限定类型） */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "QuickSlot")
    TArray<FItemInstance> QuickSlots;

    /** 当前选中的快捷槽索引 (0~4, -1=无选中) */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "QuickSlot")
    int32 SelectedQuickSlotIndex = 0;

    /** 快捷栏选中变更委托 */
    FOnQuickSlotSelected OnQuickSlotSelected;

    /** 快捷栏内容变更委托 */
    FOnQuickSlotChanged OnQuickSlotChanged;

    /**
     * 选中指定快捷槽位
     * 如果再次按同一槽位 → 触发使用
     * @return 是否成功
     */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    bool SelectQuickSlot(int32 SlotIndex);

    /**
     * 使用当前选中槽位的物品
     * 武器类型 → 调用 EquipItem
     * 消耗品类型 → 调用 UseItem (需找到背包中的对应槽位)
     * @return 是否成功执行了操作
     */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    bool UseSelectedQuickSlot();

    /** 设置快捷槽位内容（覆盖写入） */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    bool SetQuickSlot(int32 SlotIndex, const FItemInstance& Item);

    /** 获取快捷槽位内容 */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    FItemInstance GetQuickSlot(int32 SlotIndex) const;

    /** 清空快捷槽位 */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    void ClearQuickSlot(int32 SlotIndex);

    // 查找物品在背包中的位置（返回-1表示不存在）
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    int32 FindItemSlot(FName ItemID) const;

protected:

    // 查找第一个空槽位（返回-1表示背包已满）
    int32 FindEmptySlot() const;

    // 更新重量统计
    void UpdateWeight();

    // 触发更新事件
    void BroadcastInventoryUpdate();

private:
    // 背包数据（存储物品实例）
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory", meta = (AllowPrivateAccess = true))
    TArray<FItemInstance> Inventory;
};
