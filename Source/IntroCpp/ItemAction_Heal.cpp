#include "ItemAction_Heal.h"
#include "GameFramework/Character.h"
#include "AttributeComponent.h"
#include "ConsumableData.h"  // 替换原 #include "ItemData.h"

void UItemAction_Heal::InitializeFromItemData(const UItemDataBase* ItemData)
{
	// 尝试将基类指针向下转型为消耗品子类，读取 HealthRestore
	if (const UConsumableData* ConsumableData = Cast<UConsumableData>(ItemData))
	{
		if (ConsumableData->HealthRestore > 0)
		{
			HealAmount = ConsumableData->HealthRestore;
		}
	}
}

bool UItemAction_Heal::Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator)
{
	if (!Instigator) return false;

	// 尝试从 Instigator 获取 AttributeComponent
	if (UAttributeComponent* AttrComp = Instigator->FindComponentByClass<UAttributeComponent>())
	{
		AttrComp->ApplyHeal(static_cast<float>(HealAmount));
		UE_LOG(LogTemp, Log, TEXT("UItemAction_Heal: 为 %s 回复 %d 点生命"), *Instigator->GetName(), HealAmount);
		return true;
	}

	return false;
}
