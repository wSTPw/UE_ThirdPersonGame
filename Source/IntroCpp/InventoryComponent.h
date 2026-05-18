// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ItemDataBase.h"    // FItemInstance 结构体 + UItemDataBase 基类
#include "WeaponData.h"      // UWeaponData（装备查询 GetWeaponData 需要）
#include "EWeaponTypes.h"    // EItemType 枚举（EquipItem 判断武器类型需要）
#include "InventoryComponent.generated.h"

// ============================================================
//  委托声明 — 背包事件通知系统
// ============================================================

/** 背包内容变更委托（无参数，任何变化都触发）— 用于 UI 全量刷新 */
DECLARE_MULTICAST_DELEGATE(FOnInventoryUpdated);

/** 物品添加委托 — 新物品进入背包时触发 */
DECLARE_MULTICAST_DELEGATE_OneParam(FOnItemAdded, const FItemInstance&);

/** 物品移除委托 — 物品从背包移除时触发 */
DECLARE_MULTICAST_DELEGATE_OneParam(FOnItemRemoved, const FItemInstance&);

/** 物品使用委托 — UseItem 成功消费后触发 */
DECLARE_MULTICAST_DELEGATE_OneParam(FOnItemUsed, const FItemInstance&);

/**
 * 装备变更动态多播委托（支持蓝图绑定 + UFUNCTION AddDynamic）
 * @param ItemID    被装备/卸下的物品 ID
 * @param bEquipped true=刚装备, false=刚卸下
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnEquipmentChanged, FName, ItemID, bool, bEquipped);

/** 快捷栏选中槽位变更委托 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuickSlotSelected, int32, SlotIndex);

/** 快捷栏内容变更委托（设置/使用/清除/拖拽交换时广播）*/
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuickSlotChanged, int32, SlotIndex);

// ============================================================
//  UInventoryComponent — 背包组件（系统核心）
// ============================================================

/**
 * 背包与快捷栏管理组件。
 *
 * 【挂载位置】挂载在 ACharacter（如 MyPlayerCharacter）上，作为其子组件。
 * 在角色 Blueprint 的 Components 面板中 Add → 搜索 InventoryComponent。
 *
 * 【核心职责】
 *  1. 背包 CRUD：添加、移除、使用、丢弃、交换、整理物品
 *  2. 重量管理：实时计算总重量，检查超重限制
 *  3. 装备管理：装备/卸下武器，维护 EquippedSlotIndex 状态
 *  4. 快捷栏：5 格 Hotbar 管理（选中切换 + 使用执行）
 *  5. 数据桥接：通过 ItemDataSubsystem 获取物品静态配置数据
 *
 * 【数据存储】
 *   - Inventory[]:    TArray\<FItemInstance\> 背包主存储（默认20格）
 *   - QuickSlots[5]:  TArray\<FItemInstance\> 快捷栏存储
 *   - EquippedSlotIndex: 当前装备所在背包槽位索引（-1=未装备）
 *
 * 【事件驱动 UI】
 *   所有修改操作完成后通过委托广播事件，
 *   UW_InventoryUI 监听这些委托自动刷新显示。
 *   无需手动调用 UI->RefreshUI()——组件自己负责通知！
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class INTROCPP_API UInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UInventoryComponent();

protected:
    /** BeginPlay 时初始化背包数组大小并广播初始状态 */
    virtual void BeginPlay() override;

public:
    /** Tick 目前为空实现（预留扩展：持续效果/Buff 倒计时等）*/
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // ==========================================
    // 背包属性配置（编辑器可调）
    // ==========================================

    /** 背包最大格数（默认20）。影响 Inventory[] 数组初始大小 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
    int32 MaxSlots = 20;

    /** 最大承重限制。AddItem 时检查 CurrentWeight + 新增重量 <= 此值 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
    float MaxWeight = 100.0f;

    // ==========================================
    // 背包运行时状态（只读查看）
    // ==========================================

    /** 当前背包内所有物品的总重量（每次 Add/Remove 后由 UpdateWeight 重新计算）*/
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    float CurrentWeight = 0.0f;

    /** 当前背包中非空槽位的数量（物品种类数，非总件数）*/
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    int32 CurrentItemCount = 0;

    // ==========================================
    // 背包操作接口（CRUD）
    // ==========================================

    /**
     * 添加物品到背包（支持堆叠）
     * 逻辑：
     *   1. 通过 Subsystem 获取 ItemData（读取 MaxStackSize / Weight）
     *   2. 检查重量限制 (CanCarryWeight)
     *   3. 若可堆叠(MaxStackSize>1)→遍历已有同ID槽位尝试叠加
     *   4. 剩余数量 → 找空槽位新建（每格最多放 MaxStackSize 个）
     *   5. 更新统计 + 广播 OnItemAdded + OnInventoryUpdated
     *
     * @param ItemID   物品标识符（需在 Subsystem 中已注册的 DataAsset ID）
     * @param Quantity 要添加的数量（默认1）
     * @return         true=添加成功; false=找不到数据/超重/背包满
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool AddItem(FName ItemID, int32 Quantity = 1);

    /**
     * 按物品ID移除物品（从所有匹配槽位扣除）
     * 遍历整个 Inventory 数组，逐槽扣除直到满足 Quantity 或扣完
     *
     * @param ItemID   要移除的物品ID
     * @param Quantity 要移除的数量（默认1）
     * @return         true=成功移除了>0个; false=没有该物品或Quantity无效
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool RemoveItem(FName ItemID, int32 Quantity = 1);

    /**
     * 从指定索引槽位移除物品（精确到格）
     * 特殊处理：如果移除的是当前装备的武器槽位，自动 Unequip
     *
     * @param SlotIndex 目标槽位索引 [0, MaxSlots)
     * @param Quantity  要移除的数量
     * @return          true=移除成功; false=索引无效/槽位空/数量<=0
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool RemoveItemAt(int32 SlotIndex, int32 Quantity = 1);

    /**
     * 使用指定槽位的物品
     * 完整流程：
     *   1. 校验槽位有效且非空
     *   2. 通过 Subsystem 获取 ItemData，检查 bCanUse
     *   3. 权限校验：必须在服务器端执行 (HasAuthority)
     *   4. 加载并执行 ItemActionClasses 中注册的所有 Action
     *   5. 任一 Action 返回 bConsumed=true → RemoveItemAt(SlotIndex, 1)
     *   6. 广播 OnItemUsed + OnInventoryUpdated
     *
     * @param SlotIndex 要使用的物品槽位索引
     * @return          true=使用流程执行完成; false=校验失败
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool UseItem(int32 SlotIndex);

    /**
     * 丢弃物品到场景（生成 APickupItem Actor）
     * 流程：
     *   1. 读取 ItemData->bCanDrop 和 ItemClass
     *   2. 在拥有者前方 100cm 处 Spawn 掉落物 Actor
     *   3. 如果是 APickupItem → InitializePickup(ItemID, Qty)
     *   4. RemoveItemAt 整格移除
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void DropItem(int32 SlotIndex);

    /** 交换两个槽位的物品（原地交换，用于拖拽排序）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void SwapItems(int32 SlotIndex1, int32 SlotIndex2);

    /** 整理背包（提取非空物品按 ItemID 字典序排列，空格后置）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void SortItems();

    // ==========================================
    // 查询功能接口
    // ==========================================

    /** 检查背包中是否拥有某物品（任意数量 >0 即返回 true）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool HasItem(FName ItemID) const;

    /** 统计背包中某物品的总数量（跨槽位累加）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    int32 GetItemCount(FName ItemID) const;

    /** 是否还有空余格子 */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool HasSpace() const { return CurrentItemCount < MaxSlots; }

    /** 检查增加指定重量是否会超重 */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool CanCarryWeight(float Weight) const { return CurrentWeight + Weight <= MaxWeight; }

    /** 获取指定槽位的物品实例拷贝 */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    FItemInstance GetItemAt(int32 SlotIndex) const;

    /**
     * 设置指定背包槽位内容（覆盖写入）
     * 用于拖拽交换、快捷栏放入等场景
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void SetItemAt(int32 SlotIndex, const FItemInstance& Item);

    /** 获取背包全部内容（用于 UI 遍历渲染）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    TArray<FItemInstance> GetAllItems() const { return Inventory; }

    /**
     * 通过 UItemDataSubsystem 获取物品静态配置数据
     * （替代原 DataTable.FindRow 方式，统一走 Subsystem 缓存层）
     * @return 找到返回硬指针；未找到返回 nullptr
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    UItemDataBase* GetItemData(FName ItemID) const;

    /** 获取武器数据的便捷方法（内部 GetItemData + Cast<UWeaponData>）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    UWeaponData* GetWeaponData(FName WeaponID) const;

    // ==========================================
    // 装备管理（单武器装备槽）
    // ==========================================

    /**
     * 当前装备所在的背包槽位索引
     * -1 = 未装备任何武器
     * >=0 = 该索引位置的物品被视为当前装备
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Equipment")
    int32 EquippedSlotIndex = -1;

    /** 装备变更事件 — 角色和UI监听此委托来换装模型/更新状态 */
    FOnEquipmentChanged OnEquipmentChanged;

    // ==========================================
    // 背包事件委托实例（外部可 Bind 绑定监听）
    // ==========================================
    FOnInventoryUpdated OnInventoryUpdated;
    FOnItemAdded OnItemAdded;
    FOnItemRemoved OnItemRemoved;
    FOnItemUsed OnItemUsed;

    /**
     * 装备指定槽位的物品（必须是 Weapon 类型）
     * 如果已有装备其他武器 → 先自动卸下旧武器，再装备新武器
     *
     * @param SlotIndex  背包槽位索引（必须有效且持有武器类型物品）
     * @return           成功返回 true；无效槽位/空槽位/非武器类型返回 false
     */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    bool EquipItem(int32 SlotIndex);

    /** 卸下当前装备（重置 EquippedSlotIndex 为 -1 并广播事件）*/
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    void UnequipItem();

    /**
     * 获取当前装备的武器数据指针
     * 内部通过 Subsystem 懒加载 + Cast<UWeaponData>
     * @return 未装备或 Cast 失败返回 nullptr
     */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    UWeaponData* GetEquippedWeaponData() const;

    /** 是否已装备了武器 */
    UFUNCTION(BlueprintCallable, Category = "Equipment")
    bool IsWeaponEquipped() const { return EquippedSlotIndex >= 0; }

    /** 获取当前装备的 ItemID（未装备返回 NAME_None）*/
    FName GetEquippedItemID() const;

    // ==========================================
    // 快捷栏系统（Quick Slot / Hotbar）
    // ==========================================

    /** 快捷栏固定 5 格（Minecraft 风格底栏）*/
    static const int32 QUICK_SLOT_COUNT = 5;

    /** 5 个快捷槽位存储（不限定物品类型，武器消耗品都可放）*/
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "QuickSlot")
    TArray<FItemInstance> QuickSlots;

    /** 当前选中的快捷槽索引 (0~4)，-1 表示无选中 */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "QuickSlot")
    int32 SelectedQuickSlotIndex = 0;

    /** 快捷栏选中变更事件（数字键切换高亮时广播）*/
    FOnQuickSlotSelected OnQuickSlotSelected;

    /** 快捷栏内容变更事件（设置/使用/清除/交换时广播）*/
    FOnQuickSlotChanged OnQuickSlotChanged;

    /**
     * 选中指定快捷槽位（Minecraft 模式的数字键 1-5 或滚轮）
     * 再次按同一槽位不做额外操作（避免重复触发的边界问题）
     * ★ 注意：此方法仅做选中/高亮切换，不触发使用！使用由 UseSelectedQuickSlot() 驱动
     *
     * @param SlotIndex 目标槽位 [0, QUICK_SLOT_COUNT)
     * @return          是否成功选中
     */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    bool SelectQuickSlot(int32 SlotIndex);

    /**
     * 使用当前选中快捷槽位的物品
     * 根据 ItemType 分支：
     *   Weapon   → 在背包 FindItemSlot 然后 EquipItem
     *   Consumable → 在背包 FindItemSlot 然后 UseItem（同步快捷栏数量）
     *
     * @return 是否成功执行了操作
     */
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    bool UseSelectedQuickSlot();

    /** 设置快捷槽位内容（覆盖写入，旧内容丢失）*/
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    bool SetQuickSlot(int32 SlotIndex, const FItemInstance& Item);

    /** 获取快捷槽位内容（返回拷贝）*/
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    FItemInstance GetQuickSlot(int32 SlotIndex) const;

    /** 清空快捷槽位（重置为空 FItemInstance）*/
    UFUNCTION(BlueprintCallable, Category = "QuickSlot")
    void ClearQuickSlot(int32 SlotIndex);

    /** 查找物品在背包中的第一个位置索引（不存在返回 -1）*/
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    int32 FindItemSlot(FName ItemID) const;

protected:

    // ==========================================
    // 内部辅助方法（非 UFUNCTION，仅供本类使用）
    // ==========================================

    /** 查找第一个空槽位（线性扫描），满则返回 -1 */
    int32 FindEmptySlot() const;

    /** 遍历所有非空槽位，重新计算 CurrentWeight 总重量 */
    void UpdateWeight();

    /** 触发 OnInventoryUpdated 广播（统一入口，确保每次修改都通知UI）*/
    void BroadcastInventoryUpdate();

private:

    /**
     * 背包主存储数组。
     * 每个元素是一个 FItemInstance（ItemID + Quantity）。
     * 索引范围 [0, MaxSlots)，BeginPlay 时初始化大小。
     *
     * 注意：meta=(AllowPrivateAccess=true) 让蓝图中仍能读取（UPROPERTY 规范要求）
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory", meta = (AllowPrivateAccess = true))
    TArray<FItemInstance> Inventory;
};
