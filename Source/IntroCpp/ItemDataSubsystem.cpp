// Fill out your copyright notice in the Description page of Project Settings.

#include "ItemDataSubsystem.h"
#include "ConsumableData.h"    // GetConsumableData() 的 Cast 目标类型
#include "WeaponData.h"        // GetWeaponData()   的 Cast 目标类型
#include "Engine/AssetManager.h"           // AssetManager 主/备扫描方案
#include "AssetRegistry/AssetRegistryModule.h"  // AssetRegistry 兜底扫描

// ============================================================================
//  内部辅助 — 物品数据自动扫描注册
// ============================================================================

/**
 * 确保物品 DataAsset 已全部注册到 ItemDataMap
 *
 * 【设计说明】
 * 此方法是整个 Subsystem 数据加载的核心入口，采用双策略兜底机制：
 *
 * 策略1（首选）：通过 UE AssetManager 扫描 Primary Asset
 * - 前提：DefaultEngine.ini 或 ProjectSettings 中配置了 Type="Item" 的 PrimaryAsset
 * - 优点：引擎原生支持，性能最优
 *
 * 策略2（兜底）：通过 AssetRegistry 手动扫描指定目录
 * - 触发条件：策略1返回 0 个结果时激活
 * - 扫描路径：/Game/Data/Items（递归子目录）
 * - 适用场景：未配置 PrimaryAssetRules、开发调试阶段
 *
 * 【幂等保证】
 * bHasCompletedScan 标志位确保无论被调用多少次，
 * 实际文件系统扫描只执行一次。后续调用直接 return。
 */
void UItemDataSubsystem::EnsureItemsRegistered()
{
	// 幂等保护：已扫描过则跳过（避免重复加载和重复日志）
	if (bHasCompletedScan)
	{
		return;
	}
	bHasCompletedScan = true;

	// ===== 方案1：通过 AssetManager PrimaryAsset 扫描 =====
	TArray<FPrimaryAssetId> AssetIds;
	UAssetManager::Get().GetPrimaryAssetIdList(TEXT("Item"), AssetIds);

	for (const FPrimaryAssetId& Id : AssetIds)
	{
		FSoftObjectPath ObjectPath = UAssetManager::Get().GetPrimaryAssetPath(Id);
		if (!ObjectPath.IsNull())
		{
			// 同步加载 DataAsset 对象并注册
			UItemDataBase* Loaded = Cast<UItemDataBase>(
				UAssetManager::Get().GetStreamableManager().LoadSynchronous(ObjectPath));
			if (Loaded)
			{
				RegisterItemData(Loaded);
			}
		}
	}

	// ===== 方案2（兜底）：AssetManager 无结果时用 AssetRegistry 手动扫描目录 =====
	if (ItemDataMap.Num() == 0)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("[UItemDataSubsystem] AssetManager scanned 0 items, falling back to AssetRegistry scan..."));

		// 加载 AssetRegistry 模块并获取注册表引用
		FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
		IAssetRegistry& Registry = AssetRegistryModule.Get();

		// 扫描 /Game/Data/Items 目录及其所有子目录中的资产
		TArray<FAssetData> FoundAssets;
		Registry.GetAssetsByPath(FName("/Game/Data/Items"), FoundAssets, true); // true = 递归子目录

		for (const FAssetData& AssetData : FoundAssets)
		{
			// 只处理 UItemDataBase 及其子类（过滤掉 Texture/Material 等无关资产）
			if (AssetData.IsInstanceOf<UItemDataBase>())
			{
				FSoftObjectPath ObjectPath(AssetData.ToSoftObjectPath());
				if (!ObjectPath.IsNull())
				{
					UItemDataBase* Loaded = Cast<UItemDataBase>(
						UAssetManager::Get().GetStreamableManager().LoadSynchronous(ObjectPath));
					if (Loaded)
					{
						RegisterItemData(Loaded);
					}
				}
			}
		}

		UE_LOG(LogTemp, Log,
			TEXT("[UItemDataSubsystem] AssetRegistry fallback: found %d assets, registered %d"),
			FoundAssets.Num(), ItemDataMap.Num());
	}

	// 最终汇总日志：报告总共注册了多少种物品
	UE_LOG(LogTemp, Log,
		TEXT("[UItemDataSubsystem] Scan complete. Total registered items: %d"),
		ItemDataMap.Num());
}

// ============================================================================
//  生命周期
// ============================================================================

/**
 * 初始化回调 — GameInstance 启动时由引擎自动调用
 *
 * 尽早执行预扫描，将所有已知物品 DataAsset 注册到 ItemDataMap。
 * 此时资产可能还未完全就绪（取决于平台/项目配置），
 * 但 EnsureItemsRegistered() 的懒加载兜底保证了首次查询时的安全性。
 */
void UItemDataSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// 预扫描：尽早注册物品数据
	EnsureItemsRegistered();
}

/**
 * 清理回调 — GameInstance 关闭时由引擎自动调用
 *
 * 清空软引用映射和硬指针缓存，释放所有引用。
 * UPrimaryDataAsset 本身由引擎 Garbage Collector 管理生命周期，
 * 此处仅断开 Subsystem 持有的指针引用。
 */
void UItemDataSubsystem::Deinitialize()
{
	Super::Deinitialize();

	ItemDataMap.Empty();     // 清空软引用映射（~0 内存开销释放）
	LoadedCache.Empty();      // 清空硬指针缓存（断开对 DataAsset 对象的引用）

	UE_LOG(LogTemp, Log, TEXT("[UItemDataSubsystem] Deinitialized."));
}

// ============================================================================
//  数据查询接口实现
// ============================================================================

/**
 * 按 ItemID 获取物品数据（通用接口）— 两级缓存查找
 */
UItemDataBase* UItemDataSubsystem::GetItemData(FName ItemID)
{
	// ★ 确保物品数据已注册（懒加载兜底）
	// 即使 Initialize() 时 AssetRegistry 未就绪导致扫描为空，
	// 第一次查询时会在此处触发补扫，保证时序安全
	EnsureItemsRegistered();

	// --- 第一级：硬指针缓存（O(1) TMap 查找）---
	if (UItemDataBase** Cached = LoadedCache.Find(ItemID))
	{
		return *Cached;  // 缓存命中，直接返回原始指针（最快路径）
	}

	// --- 第二级：软引用映射 → 同步懒加载 ---
	if (TSoftObjectPtr<UItemDataBase>* SoftPtr = ItemDataMap.Find(ItemID))
	{
		if (!SoftPtr->IsNull())
		{
			// 执行同步加载（会阻塞当前帧直到资源就绪）
			// 对于 DataAsset 这种小型数据对象，同步加载通常 < 1ms，可接受
			UItemDataBase* Loaded = SoftPtr->LoadSynchronous();
			if (Loaded)
			{
				// ★ 加载成功后写入缓存，下次同 ID 直接走第一级
				LoadedCache.Add(ItemID, Loaded);
				return Loaded;
			}
		}
	}

	// 未找到或加载失败 → 打印 Warning 日志帮助排查配置错误
	UE_LOG(LogTemp, Warning,
		TEXT("[UItemDataSubsystem] ItemData not found: %s"),
		*ItemID.ToString());
	return nullptr;
}

/**
 * 获取消耗品数据（便捷方法）
 * 内部调用 GetItemData() + Cast<UConsumableData>()
 */
UConsumableData* UItemDataSubsystem::GetConsumableData(FName ConsumableID)
{
	// 先通过通用接口获取基类指针
	UItemDataBase* Base = GetItemData(ConsumableID);
	if (!Base)
	{
		return nullptr;  // 物品不存在
	}

	// 尝试向下转型为消耗品子类
	// 若该物品实际是武器/材料等非消耗品类型，Cast 返回 nullptr（安全失败）
	return Cast<UConsumableData>(Base);
}

/**
 * 获取武器数据（便捷方法）
 * 内部调用 GetItemData() + Cast<UWeaponData>()
 */
UWeaponData* UItemDataSubsystem::GetWeaponData(FName WeaponID)
{
	// 先通过通用接口获取基类指针
	UItemDataBase* Base = GetItemData(WeaponID);
	if (!Base)
	{
		return nullptr;  // 物品不存在
	}

	// 尝试向下转型为武器子类
	return Cast<UWeaponData>(Base);
}

// ============================================================================
//  注册
// ============================================================================

/**
 * 注册一个物品 DataAsset 到子系统
 *
 * 将资产写入 ItemDataMap（软引用），不触发实际内存加载。
 * 实际的 LoadSynchronous 延迟到第一次 GetItemData() 时执行。
 */
void UItemDataSubsystem::RegisterItemData(UItemDataBase* ItemData)
{
	// 参数校验：空指针或未设置 ItemID 的资产拒绝注册
	if (!ItemData || ItemData->ItemID.IsNone())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("[UItemDataSubsystem] RegisterItemData: Invalid item data or empty ItemID"));
		return;
	}

	// 写入软引用映射表（以 ItemID 为键，不触发实际加载）
	// 如果重复注册相同 ItemID，TMap::Add 会覆盖旧值（预期行为）
	ItemDataMap.Add(ItemData->ItemID, ItemData);

	UE_LOG(LogTemp, Log,
		TEXT("[UItemDataSubsystem] Registered: %s"),
		*ItemData->ItemID.ToString());
}
