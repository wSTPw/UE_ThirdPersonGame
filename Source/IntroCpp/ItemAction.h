// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "UObject/Object.h"
#include "ItemAction.generated.h"

class UInventoryComponent;
class UItemDataBase;   // 前向声明：PrimaryDataAsset 基类指针

/**
 * 基础物品动作（Blueprintable）
 * Execute 返回 true 表示该 action 已消耗物品（调用方负责根据返回值减少数量）
 */
UCLASS(Abstract, Blueprintable)
class INTROCPP_API UItemAction : public UObject
{
	GENERATED_BODY()

public:
	// 在服务器执行，用 Inventory 和 SlotIndex 可访问相关数据；Instigator 为触发者（通常是拥有者）
	UFUNCTION(BlueprintNativeEvent, Category = "ItemAction")
	bool Execute(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator);

	// 默认实现（C++）
	virtual bool Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator)
	{
		// 默认不消费
		return false;
	}

	// 从物品数据初始化动作参数（默认空实现，子类根据需要覆盖）
	// 参数改为 UItemDataBase* 指针（替代原 FItemData& 引用），支持 PrimaryDataAsset 继承体系
	virtual void InitializeFromItemData(const UItemDataBase* ItemData) {}
};
