// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Subsystems/SubsystemCollection.h"  // FSubsystemCollectionBase（UE5.6 Initialize 参数需要）
#include "ItemDataBase.h"                     // UItemDataBase（存储和返回类型）
#include "ItemDataSubsystem.generated.h"

/**
 * UItemDataSubsystem — 物品数据管理子系统（全局唯一实例）
 *
 * 【设计目标】
 * 集中管理所有物品 DataAsset（DA_xxx）的注册、加载与缓存，
 * 避免各模块（InventoryComponent、UI、Character 等）散落持有硬引用。
 * 任何需要物品数据的类统一通过此 Subsystem 获取。
 *
 * 【生命周期】
 * 继承自 UGameInstanceSubsystem：
 *   - GameInstance 启动时 → Initialize() 自动调用
 *   - 游戏运行期间 → 始终存在，随 GameInstance 存活
 *   - 游戏关闭/切换地图时 → Deinitialize() 自动清理
 *   - 无需手动 new/delete，引擎自动管理
 *
 * 【双层存储架构】
 * ┌─────────────────────────────────────────┐
 * │  Layer 1: ItemDataMap (软引用)           │
 * │  TMap<FName, TSoftObjectPtr<...>>        │
 * │  → 注册时写入，零内存开销（仅存路径）     │
 * │  → 不触发实际资产加载                    │
 * ├─────────────────────────────────────────┤
 * │  Layer 2: LoadedCache (硬指针)           │
 * │  TMap<FName, UItemDataBase*>             │
 * │  → 首次 GetItemData() 时 LoadSynchronous│
 * │  → 后续查询 O(1) 直接返回               │
 * │  → Deinitialize() 时全部清空             │
 * └─────────────────────────────────────────┘
 *
 * 【数据流向】
 * 编辑器创建 DA_HP_Potion.uasset
 *   → Initialize() 调用 EnsureItemsRegistered() 扫描注册到 ItemDataMap
 *   → 外部调用 GetItemData("HP_Potion")
 *     → 查 LoadedCache（命中→直接返回）
 *     → 未命中→查 ItemDataMap→LoadSynchronous→存入 LoadedCache→返回
 *
 * 【使用示例 - C++ 中获取物品数据】
 * @code
 * // 获取 Subsystem 单例
 * auto* Subsystem = GetWorld()->GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
 *
 * // 通用查询
 * if (UItemDataBase* Item = Subsystem->GetItemData("HP_Potion"))
 * {
 *     UE_LOG(LogTemp, Log, TEXT("物品名: %s"), *Item->ItemName.ToString());
 * }
 *
 * // 类型安全便捷查询（内部自动 Cast）
 * if (UConsumableData* Potion = Subsystem->GetConsumableData("MP_Potion"))
 * {
 *     int32 ManaRestore = Potion->ManaRestore;  // 安全访问消耗品特有字段
 * }
 *
 * if (UWeaponData* Staff = Subsystem->GetWeaponData("FireStaff"))
 * {
 *     bool bRanged = Staff->bIsRangedWeapon;    // 安全访问武器特有字段
 * }
 * @endcode
 */
UCLASS()
class INTROCPP_API UItemDataSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:

	// ==========================================
	// 生命周期回调（引擎自动调用）
	// ==========================================

	/**
	 * 初始化：GameInstance 启动时由引擎自动调用。
	 * 执行预扫描，尽早将所有物品 DataAsset 注册到 ItemDataMap。
	 * 如果此时 AssetRegistry 未就绪（某些平台时序问题），
	 * 会在首次 GetItemData() 调用时由 EnsureItemsRegistered() 补扫。
	 */
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/**
	 * 清理：GameInstance 关闭/销毁时由引擎自动调用。
	 * 清空软引用映射和硬指针缓存，释放所有引用。
	 * （UPrimaryDataAsset 本身由引擎 GC 管理生命周期，此处仅断开引用）
	 */
	virtual void Deinitialize() override;

	// ==========================================
	// 公开查询接口（全部 UFUNCTION 支持蓝图调用）
	// ==========================================

	/**
	 * 按 ItemID 获取物品基础数据（通用接口）
	 *
	 * 查找策略（两级缓存）：
	 *  1. 先查 LoadedCache 硬指针缓存 → 命中则直接返回（O(1)）
	 *  2. 未命中则查 ItemDataMap 软引用映射 → 执行 LoadSynchronous 同步加载
	 *     加载成功后存入 LoadedCache，下次同 ID 查询直接走第一级
	 *
	 * @param ItemID  物品标识符，需与 DataAsset 的 ItemID 字段一致（如 "HP_Potion"）
	 * @return        找到返回物品数据硬指针；未找到返回 nullptr 并打印 Warning 日志
	 *
	 * @note 内部会调用 EnsureItemsRegistered() 确保扫描已完成（懒加载兜底）
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	UItemDataBase* GetItemData(FName ItemID);

	/**
	 * 获取消耗品数据（便捷方法 — 类型安全封装）
	 *
	 * 内部实现：调用 GetItemData() 后执行 Cast<UConsumableData>()
	 * 若该物品实际不是消耗品类型（如武器），Cast 失败返回 nullptr
	 *
	 * @param ConsumableID  消耗品的 ItemID
	 * @return             消耗品子类数据指针；类型不匹配或未找到返回 nullptr
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	UConsumableData* GetConsumableData(FName ConsumableID);

	/**
	 * 获取武器数据（便捷方法 — 类型安全封装）
	 *
	 * 内部实现：调用 GetItemData() 后执行 Cast<UWeaponData>()
	 * 若该物品实际不是武器类型，Cast 失败返回 nullptr
	 *
	 * @param WeaponID  武器的 ItemID
	 * @return          武器子类数据指针；类型不匹配或未找到返回 nullptr
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	UWeaponData* GetWeaponData(FName WeaponID);

	/**
	 * 手动注册一个物品 DataAsset 到子系统
	 *
	 * 典型调用时机：
	 *  - GameInstance::Init() 或 Level BeginPlay() 中批量注册
	 *  - DLC/Mod 运行时动态添加新物品
	 *  - 测试代码中手动注入测试数据
	 *
	 * @param ItemData  要注册的物品数据资产（不能为空，ItemID 不能为 NAME_None）
	 *
	 * @note 注册仅写入 ItemDataMap（软引用），不触发实际加载。
	 *       实际加载延迟到第一次 GetItemData() 调用时执行。
	 */
	UFUNCTION(BlueprintCallable, Category = "Item Data")
	void RegisterItemData(UItemDataBase* ItemData);

private:

	// ==========================================
	// 内部辅助方法
	// ==========================================

	/**
	 * 确保物品数据已注册完成（幂等操作，多次调用只执行一次扫描）
	 *
	 * 扫描策略（优先级排序）：
	 *  1. AssetManager PrimaryAsset 扫描（Type="Item" 的资产）
	 *  2. AssetRegistry 手动扫描 /Game/Data/Items 目录（方案1无结果时的兜底）
	 *
	 * 幂等保护：bHasCompletedScan 标志位确保只扫描一次
	 */
	void EnsureItemsRegistered();

	/** 是否已完成扫描（防止重复扫描的幂等标志）*/
	bool bHasCompletedScan = false;

	// ==========================================
	// 内部存储
	// ==========================================

	/**
	 * 软引用映射表：ItemID → DataAsset 软指针
	 * 注册时写入此 Map，内存开销极小（仅存储资产路径字符串）。
	 * 支持 TSoftObjectPtr 的延迟加载特性——不主动加载到内存。
	 */
	UPROPERTY()
	TMap<FName, TSoftObjectPtr<UItemDataBase>> ItemDataMap;

	/**
	 * 硬指针缓存：ItemID → 已加载的数据对象
	 * 首次 GetItemData 触发 LoadSynchronous 后写入此缓存。
	 * 后续查询直接返回缓存的原始指针（O(1)），避免重复同步加载。
	 * 注意：不负责释放对象所有权（GC 管理 PrimaryDataAsset 生命周期）
	 */
	UPROPERTY()
	TMap<FName, UItemDataBase*> LoadedCache;
};
