#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MHWIContactResponse.h"
#include "MHWITrainingTarget.generated.h"

class UAttributeComponent;
class UStaticMeshComponent;
class UTextRenderComponent;

/** Visible stationary target, telegraphed attribute damage for practicing real counters. */
UCLASS(Blueprintable)
class INTROCPP_API AMHWITrainingTarget : public AActor, public IMHWIContactResponse
{
    GENERATED_BODY()
public:
    AMHWITrainingTarget();
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<UAttributeComponent> Attributes;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<UStaticMeshComponent> TargetMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<UTextRenderComponent> Label;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") bool bEnableAttacks = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") float AttackInterval = 4.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") float TelegraphSeconds = 0.9f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") float AttackRange = 220.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") float Damage = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Contact") EMHWIImpactSize ImpactSize = EMHWIImpactSize::Small;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Contact") bool bDeflectsMelee = false;
    virtual EMHWIImpactSize GetMHWIImpactSize_Implementation() const override { return ImpactSize; }
    virtual bool DeflectsMHWIWeapon_Implementation(AActor* Attacker) const override { return bDeflectsMelee; }
    UFUNCTION(BlueprintCallable, Category="MHWI") void ResetTarget();
protected:
    virtual void BeginPlay() override;
private:
    float CycleSeconds = 0.f;
    float LastDamage = 0.f;
    float DamageDisplayRemaining = 0.f;
    UFUNCTION() void HandleDamaged(float Amount, AActor* DamageInstigator);
};
