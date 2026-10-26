#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "CharacterActionTypes.h"
#include "CharacterActionExecution.generated.h"

class UAnimMontage;
class UWeaponData;
class UComboAttackData;
class UItemDataBase;
class UCharacterActionDefinition;
class UCharacterActionComponent;

UCLASS(Abstract)
class INTROCPP_API UCharacterActionExecution : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY() TObjectPtr<UAnimMontage> Montage;
    UPROPERTY() TObjectPtr<UWeaponData> Weapon;
    UPROPERTY() TObjectPtr<UComboAttackData> Combo;
    UPROPERTY() TObjectPtr<UItemDataBase> Item;
    UPROPERTY() TObjectPtr<UCharacterActionDefinition> Definition;
    UPROPERTY() TObjectPtr<UClass> ProjectileClass;
    FName FireSocket = NAME_None;
    FCharacterActionSnapshot State;
    FActionItemReservation Reservation;
    int32 MontageInstanceId = INDEX_NONE;
    float SectionStart = 0.f;
    float SectionEnd = 0.f;
    float LastHitTime = 0.f;
    float FirstHitTime = 0.f;
    float ChainStart = 0.f;
    float ChainEnd = 0.f;
    float CancelStart = 0.f;
    float CancelEnd = -1.f;
    double StartedAt = 0;
    double BufferedUntil = -1;
    double LastProgressAt = 0;
    float LastPosition = -1.f;
    float ManaCost = 0.f;
    float Cooldown = 0.f;
    int32 DamageOverride = 0;
    int32 HitCount = 0;
    bool bNextHitQueued = false;
    bool bBlendOut = false;
    bool bTerminal = false;
    bool bManaSpent = false;
    TSet<int32> ProcessedEvents;
    TSet<int32> ExpectedEvents;
    virtual bool ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event) { return false; }
};

UCLASS()
class INTROCPP_API UMeleeActionExecution : public UCharacterActionExecution
{
    GENERATED_BODY()
public:
    virtual bool ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event) override;
};

UCLASS()
class INTROCPP_API UCastActionExecution : public UCharacterActionExecution
{
    GENERATED_BODY()
public:
    virtual bool ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event) override;
};

UCLASS()
class INTROCPP_API UUseItemActionExecution : public UCharacterActionExecution
{
    GENERATED_BODY()
public:
    virtual bool ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event) override;
};
