// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "UObject/Object.h"
#include "ItemAction.generated.h"

// 前向声明（避免头文件循环依赖）
class UInventoryComponent;
class UItemDataBase;   // PrimaryDataAsset 基类指针（用于 InitializeFromItemData 参数）

/**
 * UItemAction — 物品使用效果基类（抽象策略模式）
 *
 * 【设计模式】Strategy Pattern (策略模式) + Template Method (模板方法)
 *
 * 每种物品的"使用效果"封装为一个 UItemAction 子类实例。
 * 物品 DataAsset 通过 ItemActionClasses 字段注册一个或多个 Action，
 * InventoryComponent::UseItem() 在使用物品时按顺序执行它们。
 *
 * 【生命周期】
 *   UseItem() 中通过 NewObject<Action>(this, Class) 创建 → Execute() → 随组件 GC 回收
 *   不需要手动 Delete，UObject GC 自动管理
 *
 * 【扩展新效果的方式】
 *   1. 新建 class UItemAction_xxx : public UItemAction
 *   2. 覆写 InitializeFromItemData() 从 DataAsset 读取参数
 *   3. 覆写 Execute_Implementation() 实现具体效果逻辑
 *   4. 在 ConsumableData/WeaponData 的 ItemActionClasses 中填入新 Action 类
 *
 * 【已实现的子类】
 *   - UItemAction_Heal:        治疗效果 (AttributeComponent.ApplyHeal)
 *   - UItemAction_RestoreMana:  回蓝效果 (AttributeComponent.RestoreMana)
 *   - 未来可扩展：Buff、伤害AOE、传送、召唤等
 */
UCLASS(Abstract, Blueprintable)
class INTROCPP_API UItemAction : public UObject
{
	GENERATED_BODY()

public:

	/**
	 * 执行物品效果的入口方法（BlueprintNativeEvent，蓝图可覆写）
	 *
	 * @param Inventory  背包组件引用（可用于访问背包数据、移除物品等）
	 * @param SlotIndex  触发使用的槽位索引
	 * @param Instigator 触发者 Actor（通常是拥有背包的角色，用于获取 AttributeComp 等）
	 * @return           true = 该 Action 已消费物品（调用方应扣减数量）
	 *                   false = 该 Action 未消费（如条件不满足、CD未好等）
	 */
	UFUNCTION(BlueprintNativeEvent, Category = "ItemAction")
	bool Execute(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator);

	/** C++ 默认实现：不做任何事，返回 false（不消费）*/
	virtual bool Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator)
	{
		// 默认行为：不消费物品。子类根据需要覆写此方法。
		return false;
	}

	/**
	 * 从物品数据初始化 Action 的参数配置。
	 *
	 * 由 InventoryComponent::UseItem() 在 Execute() **之前**调用。
	 * 子类应在此方法中将 DataAsset 的字段值复制到自己的成员变量中。
	 *
	 * 示例：
	 *   UItemAction_Heal 会 Cast 到 UConsumableData 并读取 HealthRestore → 设置 HealAmount
	 *   UItemAction_RestoreMana 会读取 ManaRestore → 设置 ManaAmount
	 *
	 * @param ItemData 物品的静态配置数据（通常是 UConsumableData* 或 UWeaponData*）
	 */
	virtual void InitializeFromItemData(const UItemDataBase* ItemData) {}
};
