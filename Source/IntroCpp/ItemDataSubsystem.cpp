// Fill out your copyright notice in the Description page of Project Settings.

#include "ItemDataSubsystem.h"
#include "ConsumableData.h"
#include "WeaponData.h"          // UWeaponData（GetWeaponData Cast 需要）
#include "Engine/AssetManager.h"
#include "AssetRegistry/AssetRegistryModule.h"

// ============================================================================
// 内部辅助
// ============================================================================

void UItemDataSubsystem::EnsureItemsRegistered()
{
	// 已注册过则跳过（幂等保护）
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
			TEXT("[UItemDataSubsystem] AssetManager scanned 0, falling back to AssetRegistry scan..."));

		FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
		IAssetRegistry& Registry = AssetRegistryModule.Get();

		TArray<FAssetData> FoundAssets;
		Registry.GetAssetsByPath(FName("/Game/Data/Items"), FoundAssets, true); // true = 递归子目录

		for (const FAssetData& AssetData : FoundAssets)
		{
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

	UE_LOG(LogTemp, Log,
		TEXT("[UItemDataSubsystem] Scan complete. Total registered items: %d"),
		ItemDataMap.Num());
}

// ============================================================================
// 生命周期
// ============================================================================

void UItemDataSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// 预扫描：尽早注册物品数据
	// （如果此时 AssetRegistry 未就绪，会在首次 GetItemData 时由 EnsureItemsRegistered 补扫）
	EnsureItemsRegistered();
}

void UItemDataSubsystem::Deinitialize()
{
	Super::Deinitialize();

	// 清空软引用映射和硬指针缓存，释放所有引用
	// （UPrimaryDataAsset 本身由引擎 GC 管理生命周期，此处仅断开引用）
	ItemDataMap.Empty();
	LoadedCache.Empty();

	UE_LOG(LogTemp, Log, TEXT("[UItemDataSubsystem] Deinitialized."));
}

// ============================================================================
// 数据查询
// ============================================================================

UItemDataBase* UItemDataSubsystem::GetItemData(FName ItemID)
{
	// ★ 确保物品数据已注册（懒加载兜底）
	// 即使 Initialize 时 AssetRegistry 未就绪导致扫描为空，
	// 第一次查询时会在此处触发补扫，保证时序安全
	EnsureItemsRegistered();

	// --- 第一级：硬指针缓存（O(1) 查找） ---
	if (UItemDataBase** Cached = LoadedCache.Find(ItemID))
	{
		return *Cached;
	}

	// --- 第二级：软引用映射 → 同步懒加载 ---
	if (TSoftObjectPtr<UItemDataBase>* SoftPtr = ItemDataMap.Find(ItemID))
	{
		if (!SoftPtr->IsNull())
		{
			UItemDataBase* Loaded = SoftPtr->LoadSynchronous();
			if (Loaded)
			{
				LoadedCache.Add(ItemID, Loaded);
				return Loaded;
			}
		}
	}

	// 未找到或加载失败
	UE_LOG(LogTemp, Warning,
		TEXT("[UItemDataSubsystem] ItemData not found: %s"),
		*ItemID.ToString());
	return nullptr;
}

UConsumableData* UItemDataSubsystem::GetConsumableData(FName ConsumableID)
{
	// 先通过通用接口获取基类指针
	UItemDataBase* Base = GetItemData(ConsumableID);
	if (!Base)
	{
		return nullptr;
	}

	// 尝试向下转型为消耗品子类
	// 若该物品实际是武器/材料等非消耗品类型，Cast 返回 nullptr
	return Cast<UConsumableData>(Base);
}

UWeaponData* UItemDataSubsystem::GetWeaponData(FName WeaponID)
{
	// 先通过通用接口获取基类指针
	UItemDataBase* Base = GetItemData(WeaponID);
	if (!Base)
	{
		return nullptr;
	}

	// 尝试向下转型为武器子类
	return Cast<UWeaponData>(Base);
}

// ============================================================================
// 注册
// ============================================================================

void UItemDataSubsystem::RegisterItemData(UItemDataBase* ItemData)
{
	// 参数校验：空指针或未设置 ItemID 的资产拒绝注册
	if (!ItemData || ItemData->ItemID.IsNone())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("[UItemDataSubsystem] RegisterItemData: Invalid item data or empty ItemID"));
		return;
	}

	// 将资产写入软引用映射表（不触发实际加载）
	// 实际加载延迟到第一次 GetItemData() 调用时执行
	ItemDataMap.Add(ItemData->ItemID, ItemData);

	UE_LOG(LogTemp, Log,
		TEXT("[UItemDataSubsystem] Registered: %s"),
		*ItemData->ItemID.ToString());
}
