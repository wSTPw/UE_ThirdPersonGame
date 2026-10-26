#pragma once

#include "CoreMinimal.h"
#include "EWeaponTypes.h"
#include "CharacterActionTypes.h"
#include "LocomotionAnimContext.generated.h"

/** Immutable to graph consumers; cm, cm/s and cm/s^2 in world coordinates. */
USTRUCT(BlueprintType)
struct FLocomotionAnimContext
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FVector Velocity = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) FVector Acceleration = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) FVector DesiredVelocity = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) FRotator Facing = FRotator::ZeroRotator;
    UPROPERTY(BlueprintReadOnly) EWeaponAnimType Stance = EWeaponAnimType::None;
    UPROPERTY(BlueprintReadOnly) bool bGrounded = true;
    UPROPERTY(BlueprintReadOnly) FCharacterActionSnapshot Action;
};
