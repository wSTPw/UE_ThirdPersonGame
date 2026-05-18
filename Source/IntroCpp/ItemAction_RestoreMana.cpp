// Fill out your copyright notice in the Description page of Project Settings.

#include "ItemAction_RestoreMana.h"
#include "GameFramework/Character.h"
#include "AttributeComponent.h"
#include "ConsumableData.h"  // UConsumableData (Cast 目标类型)

/**
 * 从物品 DataAsset 初始化回蓝量
 * 与 UItemAction_Heal::InitializeFromItemData() 结构完全对称，
 * 区别是读取 ManaRestore 字段而非 HealthRestore。
 */
void UItemAction_RestoreMana::InitializeFromItemData(const UItemDataBase* ItemData)
{
	if (const UConsumableData* ConsumableData = Cast<UConsumableData>(ItemData))
	{
		if (ConsumableData->ManaRestore > 0)
		{
			ManaAmount = ConsumableData->ManaRestore;
		}
	}
}

/**
 * 执行回蓝效果 — 调用 AttributeComponent.RestoreMana()
 */
bool UItemAction_RestoreMana::Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator)
{
	if (!Instigator) return false;

	if (UAttributeComponent* AttrComp = Instigator->FindComponentByClass<UAttributeComponent>())
	{
		AttrComp->RestoreMana(static_cast<float>(ManaAmount));

		UE_LOG(LogTemp, Log, TEXT("UItemAction_RestoreMana: 为 %s 回复 %d 点魔法"),
			*Instigator->GetName(), ManaAmount);
		return true;
	}

	return false;
}
