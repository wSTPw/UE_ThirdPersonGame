// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ItemAction.h"          // UItemAction（TSoftClassPtr 需要）
#include "Engine/Texture2D.h"    // UTexture2D（TSoftObjectPtr 需要）
#include "Animation/AnimMontage.h" // UAnimMontage（使用动画需要）
#include "ItemDataBase.generated.h"

/** 物品类型枚举 */
UENUM(BlueprintType)
enum class EItemType : uint8
{
	Weapon		UMETA(DisplayName = "武器"),
	Consumable	UMETA(DisplayName = "消耗品"),
	Material	UMETA(DisplayName = "材料"),
	Quest		UMETA(DisplayName = "任务物品"),
	Equipment	UMETA(DisplayName = "装备"),
	Miscellaneous UMETA(DisplayName = "杂物")
};

/** 物品稀有度枚举 */
UENUM(BlueprintType)
enum class EItemRarity : uint8
{
	Common		UMETA(DisplayName = "普通"),
	Uncommon	UMETA(DisplayName = "罕见"),
	Rare		UMETA(DisplayName = "稀有"),
	Epic		UMETA(DisplayName = "史诗"),
	Legendary	UMETA(DisplayName = "传说")
};

// 单个物品实例数据（背包格子中的物品）
USTRUCT(BlueprintType)
struct FItemInstance
{
	GENERATED_BODY()

	// 物品ID（用于关联物品数据）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FName ItemID;

	// 物品数量
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	int32 Quantity;

	// 构造函数
	FItemInstance()
		: ItemID(NAME_None), Quantity(0) {}

	FItemInstance(FName InItemID, int32 InQuantity)
		: ItemID(InItemID), Quantity(InQuantity) {}

	// 判断是否为空
	bool IsEmpty() const { return ItemID == NAME_None || Quantity <= 0; }

	// 重置物品
	void Empty()
	{
		ItemID = NAME_None;
		Quantity = 0;
	}

	// 判断是否是同一类物品
	bool IsSameType(const FItemInstance& Other) const
	{
		return ItemID == Other.ItemID;
	}
};

/**
 * UItemDataBase — 物品数据基类（PrimaryDataAsset）
 *
 * 继承自 UPrimaryDataAsset，可在编辑器中创建独立资产实例（DA_xxx），
 * 每个 DataAsset 对应一种物品的完整静态数据。
 *
 * 【设计要点】
 * - 所有物品共有的基础属性集中在此类
 * - 子类（如 UConsumableData）扩展特有属性
 * - 通过 UItemDataSubsystem 统一注册与查询
 */
UCLASS()
class INTROCPP_API UItemDataBase : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UItemDataBase();

	// ==========================================
	// 基础标识
	// ==========================================

	/** 唯一标识符（如 "HP_Potion"、"Gold_Coin"），用于 TMap 查找键 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FName ItemID;

	/** 显示名称 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FText ItemName;

	/** 描述文本 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item", meta = (MultiLine = true))
	FText ItemDescription;

	// ==========================================
	// 分类与品质
	// ==========================================

	/** 物品类型 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	EItemType ItemType;

	/** 稀有度 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	EItemRarity ItemRarity;

	// ==========================================
	// 外观与关联资源
	// ==========================================

	/** 物品图标（软引用，支持异步加载） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TSoftObjectPtr<UTexture2D> ItemIcon;

	/** 手持模型（StaticMesh，选中快捷栏时显示在手上，留空则不显示） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TSoftObjectPtr<UStaticMesh> ItemStaticMesh;

	/** 使用动画 Montage（右键长按时播放，播放完毕后执行效果；留空则立即生效不播动画） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
	UAnimMontage* UseMontage = nullptr;

	/** 掉落物 Actor 类（软引用）— 丢弃时 Spawn 的类型 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TSoftClassPtr<AActor> ItemClass;

	/** 关联的 ItemAction 类列表 — 使用物品时按顺序执行 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	TArray<TSoftClassPtr<UItemAction>> ItemActionClasses;

	// ==========================================
	// 背包相关属性
	// ==========================================

	/** 最大堆叠数量（1 = 不可堆叠） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
	int32 MaxStackSize;

	/** 单个物品重量 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
	float Weight;

	/** 单个物品价值（金币数） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory")
	int32 Value;

	// ==========================================
	// 行为标志
	// ==========================================

	/** 是否可出售 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bCanSell;

	/** 是否可使用 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bCanUse;

	/** 是否可丢弃到世界 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bCanDrop;
};
