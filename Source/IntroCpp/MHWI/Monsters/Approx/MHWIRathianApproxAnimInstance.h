#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "MHWIRathianApproxAnimInstance.generated.h"

class UAnimSequence;

UCLASS(BlueprintType)
class INTROCPP_API UMHWIRathianApproxAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UMHWIRathianApproxAnimInstance();
    void ConfigureLocomotion(UAnimSequence* Idle, UAnimSequence* Walk, UAnimSequence* Run);
    void SetLocomotionBlend(float NormalizedSpeed, float DeltaSeconds);
    void SetDeathSequence(UAnimSequence* Death);
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
private:
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> IdleSequence;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> WalkSequence;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> RunSequence;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> DeathSequence;
    float SmoothedSpeedAlpha = 0.f;
};
