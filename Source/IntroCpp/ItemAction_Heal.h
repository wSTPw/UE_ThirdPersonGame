#pragma once

#include "ItemAction.h"
#include "ItemAction_Heal.generated.h"

UCLASS(Blueprintable)
class INTROCPP_API UItemAction_Heal : public UItemAction
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Heal")
	int32 HealAmount = 20;

	// 覆盖初始化接口，从 UItemDataBase（Cast 为 UConsumableData）读取数值
	virtual void InitializeFromItemData(const UItemDataBase* ItemData) override;

	virtual bool Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator) override;
};
