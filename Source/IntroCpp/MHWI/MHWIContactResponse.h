#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "MHWIContactResponse.generated.h"

UENUM(BlueprintType)
enum class EMHWIImpactSize : uint8 { Small, Medium, Large };

/** Explicit contact facts used by R06 source owners. Damage amount is never
 * interpreted as a native knockback magnitude or a deflection result. */
UINTERFACE(BlueprintType)
class INTROCPP_API UMHWIContactResponse : public UInterface
{
    GENERATED_BODY()
};

class INTROCPP_API IMHWIContactResponse
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="MHWI|Contact")
    EMHWIImpactSize GetMHWIImpactSize() const;
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="MHWI|Contact")
    bool DeflectsMHWIWeapon(AActor* Attacker) const;
};
