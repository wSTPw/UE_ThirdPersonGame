// Fill out your copyright notice in the Description page of Project Settings.


#include "ItemAction_RestoreMana.h"
#include "GameFramework/Character.h"
#include "AttributeComponent.h"
#include "ConsumableData.h"  // 替换原 #include "ItemData.h"

void UItemAction_RestoreMana::InitializeFromItemData(const UItemDataBase* ItemData)
{
	// 尝试将基类指针向下转型为消耗品子类，读取 ManaRestore
	if (const UConsumableData* ConsumableData = Cast<UConsumableData>(ItemData))
	{
		if (ConsumableData->ManaRestore > 0)
		{
			ManaAmount = ConsumableData->ManaRestore;
		}
	}
}

bool UItemAction_RestoreMana::Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator)
{
	if (!Instigator) return false;

	// 尝试从 Instigator 获取 AttributeComponent
	if (UAttributeComponent* AttrComp = Instigator->FindComponentByClass<UAttributeComponent>())
	{
		AttrComp->RestoreMana(static_cast<float>(ManaAmount));
		UE_LOG(LogTemp, Log, TEXT("UItemAction_RestoreMana: 为 %s 回复 %d 点魔法"), *Instigator->GetName(), ManaAmount);
		return true;
	}

	return false;
}

