#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CharacterActionDefinition.generated.h"

class UAnimMontage;

// Immutable tuning. Existing weapon/consumable data remains a supported adapter.
UCLASS(BlueprintType)
class INTROCPP_API UCharacterActionDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action") FName ActionId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action") TObjectPtr<UAnimMontage> Montage;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0.01")) float PlayRate = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0", ClampMax="1")) float MoveScale = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action") bool bAllowJump = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="0", ClampMax="0.5")) float InputBufferSeconds = 0.15f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Action", meta=(ClampMin="1")) float MaximumActiveSeconds = 30.f;
};
