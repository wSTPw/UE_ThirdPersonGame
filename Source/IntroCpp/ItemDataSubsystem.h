// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Subsystems/SubsystemCollection.h"  // FSubsystemCollectionBase（UE5.6 Initialize 参数需要）
#include "ItemDataBase.h"
#include "ItemDataSubsystem.generated.h"

/**
 * UItemDataSubsystem — 物品数据管理子系统（全局唯一）
 *
 * 【设计目标】
 * 集中管理所有物品 DataAsset 的加载与缓存，避免各模块分散持有引用。
 * 任何需要物品数据的类（InventoryComponent、UI、Character 等）统一通过此 Subsystem 获取。
 *
 * 【架构说明】
 * - 继承自 UGameInstanceSubsystem，随 GameInstance 自动创建/销毁
 *   → 游戏运行期间始终存在，游戏结束时自动清理，无需手动管理生命周期
 *
 * - 双层存储结构：
 *   ① ItemDataMap (TMap<FName, TSoftObjectPtr<UItemDataBase>>)
 *      → 注册时存入软引用，不占用内存，仅记录资产路径
 *   ② LoadedCache (TMap<FName, UItemDataBase*>)
 *      → 首次查询时执行 LoadSynchronous 懒加载，之后缓存在此加速重复访问
 *
 * - 数据流向：
 *   编辑器创建 DA_xxx 资产 → RegisterItemData() 注册到 ItemDataMap
 *   → 外部调用 GetItemData("HP_Potion") → 查 LoadedCache / LoadSynchronous → 返回硬指针
 *
 * 【与现有代码的关系】
 * - 替代原 InventoryComponent.ItemDataTable 直接读取 DataTable 的方式
 * - 与 MyEventBusGameInstance 不冲突，作为其子模块共存
 *
 * 【使用示例】
 *   // C++ 中获取物品数据
 *   auto* Subsystem = GetWorld()->GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
 *   UItemDataBase* Item = Subsystem->GetItemData("HP_Potion");
 *   if (auto* Consumable = Subsystem->GetConsumableData("MP_Potion"))
 *   {
 *       int32 Mana = Consumable->ManaRestore;
 *   }
 */
UCLASS()
class INTROCPP_API UItemDataSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:

	// ==========================================
	// 生命周期
	// ==========================================

	/** 初始化：GameInstance 启动时自动调用，输出已注册物品数量日志 */
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** 清理：GameInstance 关闭时自动调用，清空映射表和缓存 */
	virtual void Deinitialize() override;

	// ==========================================
	// 公开查询接口（全部支持蓝图调用）
	// ==========================================

	/**
	 * 按 ItemID 获取物品基础数据
	 *
	 * 查找策略（两级）：
	 *  1. 先查 LoadedCache 硬指针缓存 → 命中则直接返回（O(1)）
	 *  2. 未命中则查 ItemDataMap 软引用 → 执行 LoadSynchronous 同步加载
	 *     加载成功后存入 LoadedCache，下次直接走缓存
	 *
	 * @param ItemID  物品标识符，需与 DataAsset 的 ItemID 字段一致（如 "HP_Potion"）
	 * @return        找到返回物品数据硬指针；未找到返回 nullptr 并打印 Warning 日志
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	UItemDataBase* GetItemData(FName ItemID);

	/**
	 * 获取消耗品数据（便捷方法）
	 *
	 * 内部调用 GetItemData() 后执行 Cast<UConsumableData>()，
	 * 若该物品不是消耗品类型则返回 nullptr。
	 *
	 * @param ConsumableID  消耗品的 ItemID
	 * @return             消耗品数据指针；类型不匹配或未找到返回 nullptr
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	UConsumableData* GetConsumableData(FName ConsumableID);

	/**
	 * 获取武器数据（便捷方法）
	 *
	 * 内部调用 GetItemData() 后执行 Cast<UWeaponData>()，
	 * 若该物品不是武器类型则返回 nullptr。
	 *
	 * @param WeaponID  武器的 ItemID
	 * @return          武器数据指针；类型不匹配或未找到返回 nullptr
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	UWeaponData* GetWeaponData(FName WeaponID);

	/**
	 * 手动注册一个物品 DataAsset 到子系统
	 *
	 * 典型调用时机：
	 *  - GameInstance::Init() 或 BeginPlay() 中批量注册
	 *  - 通过 Project Settings 配置的默认物品列表遍历注册
	 *  - 运行时动态添加新物品（如 DLC/Mod 加载）
	 *
	 * @param ItemData  要注册的物品数据资产（不能为空，ItemID 不能为 None）
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	void RegisterItemData(UItemDataBase* ItemData);

private:

	// ==========================================
	// 内部辅助
	// ==========================================

	/** 确保物品数据已注册（幂等，多次调用只执行一次扫描） */
	void EnsureItemsRegistered();

	/** 是否已完成扫描（防止重复扫描） */
	bool bHasCompletedScan = false;

	// ==========================================
	// 内部存储
	// ==========================================

	/** 软引用映射表：ItemID → DataAsset 软指针
	 *  注册时写入，内存开销极小（仅存路径），支持懒加载 */
	UPROPERTY()
	TMap<FName, TSoftObjectPtr<UItemDataBase>> ItemDataMap;

	/** 硬指针缓存：ItemID → 已加载的数据对象
	 *  首次 GetItemData 触发加载后写入，后续查询直接返回，避免重复 LoadSynchronous */
	UPROPERTY()
	TMap<FName, UItemDataBase*> LoadedCache;
};
