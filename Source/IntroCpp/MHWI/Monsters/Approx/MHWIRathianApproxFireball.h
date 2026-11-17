#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MHWI/MHWIContactResponse.h"
#include "MHWIRathianApproxFireball.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UProjectileMovementComponent;

UCLASS()
class INTROCPP_API AMHWIRathianApproxFireball : public AActor, public IMHWIContactResponse
{
    GENERATED_BODY()
public:
    AMHWIRathianApproxFireball();
    void InitializeProjectile(AActor* InOwner, AActor* InTarget, float Damage, FVector Knockback, EMHWIImpactSize ImpactSize);
protected:
    virtual void BeginPlay() override;
public:
    virtual void Tick(float DeltaSeconds) override;
private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UProjectileMovementComponent> Movement;
    UPROPERTY() TWeakObjectPtr<AActor> Target;
    UPROPERTY() TWeakObjectPtr<AActor> SourceOwner;
    float DamageAmount = 24.f;
    EMHWIImpactSize ImpactSize = EMHWIImpactSize::Medium;
    FVector KnockbackVelocity = FVector(450.f, 0.f, 250.f);
    bool bConsumed = false;
public:
    virtual EMHWIImpactSize GetMHWIImpactSize_Implementation() const override { return ImpactSize; }
    virtual bool DeflectsMHWIWeapon_Implementation(AActor* Attacker) const override { return false; }
private:
    UFUNCTION() void HandleHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit);
    UFUNCTION() void HandleOverlap(UPrimitiveComponent* Overlapped, AActor* OtherActor, UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& Hit);
    void Consume(AActor* OtherActor, const FHitResult& Hit);
};
