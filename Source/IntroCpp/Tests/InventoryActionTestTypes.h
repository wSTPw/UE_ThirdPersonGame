#pragma once

#include "CoreMinimal.h"
#include "ItemAction.h"
#include "InventoryActionTestTypes.generated.h"

class UInventoryComponent;

// Concrete legacy action reporting no effect, for transaction regression tests.
UCLASS(Transient)
class UInventoryActionTestNoEffect final : public UItemAction
{
    GENERATED_BODY()
};

// Dynamic attribute delegates require a reflected listener even in native tests.
UCLASS(Transient)
class UInventoryActionTestProbe final : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient) TObjectPtr<UInventoryComponent> Inventory;
    bool bQuickSlot = true;
    int32 SlotIndex = 0;
    int32 ExpectedQuantity = 0;
    int32 ChangedCount = 0;
    bool bObservedCommittedQuantity = true;
    bool bRejectedReentrantMutation = true;

    UFUNCTION() void OnAttributeChanged(float CurrentValue, float MaxValue);
};
