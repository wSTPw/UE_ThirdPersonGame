// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ItemAction.h"          // UItemAction（TSoftClassPtr 需要完整类型定义）
#include "Engine/Texture2D.h"    // UTexture2D（ItemIcon 字段使用 TSoftObjectPtr 需要）
#include "Animation/AnimMontage.h" // UAnimMontage（UseMontage 使用动画蒙太奇）
#include "ItemDataBase.generated.h"

// ============================================================
//  枚举定义
// ============================================================

/** 物品类型枚举 — 决定物品的大类行为逻辑 */
UENUM(BlueprintType)
enum class EItemType : uint8
{
	Weapon		UMETA(DisplayName = "武器"),       // 可装备，影响攻击方式
	Consumable	UMETA(DisplayName = "消耗品"),     // 使用后消耗(减数量)，产生效果
	Material	UMETA(DisplayName = "材料"),       // 合成/任务用，不可直接使用
	Quest		UMETA(DisplayName = "任务物品"),    // 任务收集物
	Equipment	UMETA(DisplayName = "装备"),       // 防具/饰品等被动装备（预留）
	Miscellaneous UMETA(DisplayName = "杂物")     // 其他杂项物品
};

/** 物品稀有度枚举 — 影响UI显示颜色、掉落概率权重等 */
UENUM(BlueprintType)
enum class EItemRarity : uint8
{
	Common		UMETA(DisplayName = "普通"),     // 灰色/白色 — 最常见
	Uncommon	UMETA(DisplayName = "罕见"),     // 蓝色
	Rare		UMETA(DisplayName = "稀有"),      // 紫色
	Epic		UMETA(DisplayName = "史诗"),      // 橙色
	Legendary	UMETA(DisplayName = "传说")      // 金色 — 最稀少
};

// ============================================================
//  FItemInstance — 运行时背包中的单个物品实例
// ============================================================
/**
 * 每个背包槽位持有的数据结构。
 *
 * 注意：这是**运行时实例数据**（动态变化的），不是静态配置。
 * 静态配置存储在 UItemDataBase / UConsumableData / UWeaponData 中。
 *
 * 典型生命周期：
 *   AddItem() 时创建 → 存入 Inventory[] 数组中
 *   UseItem() 成功后 Quantity-- 或 RemoveItemAt() 后可能被 Empty() 清空
 *   DropItem() 时从 Inventory 移除，转为 APickupItem 场景 Actor
 */
USTRUCT(BlueprintType)
struct FItemInstance
{
	GENERATED_BODY()

	/** 物品ID — 关联到哪个 DataAsset（如 "HP_Potion"、"DA_WP_FireStaff"）*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FName ItemID;

	/** 物品堆叠数量 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	int32 Quantity;

	/** 默认构造函数：空槽位状态 */
	FItemInstance()
		: ItemID(NAME_None), Quantity(0) {}

	/** 带参构造函数：快速创建一个有数据的实例 */
	FItemInstance(FName InItemID, int32 InQuantity)
		: ItemID(InItemID), Quantity(InQuantity) {}

	/**
	 * 判断此槽位是否为空
	 * @return true 当 ItemID 为 None 或 Quantity <= 0 时
	 */
	bool IsEmpty() const { return ItemID == NAME_None || Quantity <= 0; }

	/**
	 * 重置为空槽位（清零 ID 和数量）
	 * 用于 RemoveItemAt 扣完数量后清理槽位
	 */
	void Empty()
	{
		ItemID = NAME_None;
		Quantity = 0;
	}

	/**
	 * 判断是否与另一个实例属于同一种物品（仅比较 ItemID）
	 * 用于堆叠逻辑判断——同一 ID 的物品可以合并到同一槽位
	 */
	bool IsSameType(const FItemInstance& Other) const
	{
		return ItemID == Other.ItemID;
	}
};

// ============================================================
//  UItemDataBase — 物品数据基类（PrimaryDataAsset）
// ============================================================

/**
 * 所有物品的静态配置基类。
 *
 * 【继承体系】
 *   UPrimaryDataAsset (引擎)
 *     └── UItemDataBase              ← 本类（公共属性）
 *          ├── UConsumableData       ← 消耗品子类（HP/MP回复/Buff）
 *          └── UWeaponData           ← 武器子类（投射物/动画/伤害参数）
 *
 * 【设计模式】
 *   - Data Asset 模式：每种具体物品是一个 .uasset 实例（如 DA_HP_Potion）
 *   - 通过 UItemDataSubsystem 全局注册和查询，避免模块间散落引用
 *   - 子类扩展特有属性，基类持有所有物品共有的字段
 *
 * 【在编辑器中使用】
 *   Content Browser → 右键 → Miscellaneous → Data Asset → 选择 UItemDataBase 或其子类
 *
 * 【运行时获取方式】
 *   auto* Subsystem = GetWorld()->GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
 *   UItemDataBase* Data = Subsystem->GetItemData("HP_Potion");
 */
UCLASS()
class INTROCPP_API UItemDataBase : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UItemDataBase();

	// ==========================================
	// 基础标识信息
	// ==========================================

	/**
	 * 唯一标识符（如 "HP_Potion"、"Gold_Coin"、"FireStaff"）。
	 * 用作 TMap 的查找键，必须全局唯一。
	 * 推荐命名规则：类型_名称（如 WP_FireStaff、POT_HP、MAT_IronOre）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FName ItemID;

	/** 显示名称（支持本地化 FText）— UI 中展示的物品名 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FText ItemName;

	/**
	 * 描述文本（支持本地化）。
	 * 在背包 UI 的详情面板中显示。
	 * meta=(MultiLine=true) 让编辑器中可输入多行文本
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item", meta = (MultiLine = true))
	FText ItemDescription;

	// ==========================================
	// 分类与品质
	// ==========================================

	/** 决定物品的行为分类（武器→装备逻辑，消耗品→使用扣减逻辑）*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	EItemType ItemType;

	/** 影响UI颜色、掉落概率等 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	EItemRarity ItemRarity;

	// ==========================================
	// 外观资源（全部使用软引用 TSoftObjectPtr，支持异步加载）
	// ==========================================

	/**
	 * 物品图标纹理（2D图片）。
	 * 软引用：不会随关卡加载而立即加载内存，首次访问时按需加载。
	 * UW_InventoryUI::LoadItemIconAsync() 通过 StreamableManager 异步加载此资源
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TSoftObjectPtr<UTexture2D> ItemIcon;

	/**
	 * 手持模型 StaticMesh。
	 * 选中快捷栏时显示在手部的3D模型（如药水瓶、武器模型）。
	 * 留空则不显示手持模型。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TSoftObjectPtr<UStaticMesh> ItemStaticMesh;

	/**
	 * 使用动画 Montage。
	 * 右键长按使用物品时播放的角色动画（如"喝药水"、"吃食物"动作）。
	 * 动画播完后通过 AnimNotify_UseItemComplete 通知角色执行实际效果。
	 * 留空 = 不播放动画，立即执行效果（适合瞬发物品）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
	UAnimMontage* UseMontage = nullptr;

	/**
	 * 掉落物 Actor 类（软引用）。
	 * 从背包丢弃(DropItem)或怪物死亡掉落时 Spawn 的 Actor 类型。
	 * 通常填 BP_Pickup_xxx（APickupItem 的蓝图子类）。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TSoftClassPtr<AActor> ItemClass;

	/**
	 * 关联的 ItemAction 类列表（策略模式的 Action 注册表）。
	 * 使用该物品时，InventoryComponent 会遍历此列表：
	 *   1. LoadSynchronous 加载每个类
	 *   2. NewObject 创建实例
	 *   3. InitializeFromItemData(Data) 初始化参数
	 *   4. Execute() 执行效果，任一返回 true 则标记为已消费
	 *
	 * 示例：[BP_Action_Heal] 或 [BP_Action_Heal, BP_Action_BuffSpeed]
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TArray<TSoftClassPtr<UItemAction>> ItemActionClasses;

	// ==========================================
	// 背包相关属性（影响 InventoryComponent 行为）
	// ==========================================

	/**
	 * 最大堆叠数量。
	 * 1 = 不可堆叠（每个槽位只能放1个，如武器、装备）
	 * >1 = 可堆叠（如药水最大10个叠在一格）
	 * InventoryComponent::AddItem() 会据此决定是叠加已有槽位还是开新格
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
	int32 MaxStackSize;

	/** 单个物品重量。InventoryComponent 用它计算总重量并检查超重限制 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
	float Weight;

	/** 单个物品价值（金币数）。商店系统预留字段 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
	int32 Value;

	// ==========================================
	// 行为标志（控制哪些操作允许执行）
	// ==========================================

	/** 是否可在商店出售 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bCanSell;

	/** 是否可通过右键/快捷栏使用（消耗品=true，普通材料=false）*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bCanUse;

	/** 是否可从背包丢弃到场景生成 PickupItem */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bCanDrop;
};
