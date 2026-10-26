#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "IncomingDamageResponse.generated.h"

/** Optional owner policy consulted before positive attribute damage is applied. */
UINTERFACE(BlueprintType)
class INTROCPP_API UIncomingDamageResponse : public UInterface
{
    GENERATED_BODY()
};

class INTROCPP_API IIncomingDamageResponse
{
    GENERATED_BODY()

public:
    /** True consumes this damage request: the attribute component must not deduct HP. */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Combat|Damage")
    bool InterceptIncomingDamage(float DamageAmount, AActor* DamageInstigator);

    /** Optional: true uses finite nonnegative AdjustedDamage; false preserves input. */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Combat|Damage")
    bool AdjustIncomingDamage(float DamageAmount, AActor* DamageInstigator, float& AdjustedDamage);
};
