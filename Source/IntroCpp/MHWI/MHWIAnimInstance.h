#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "MHWILinkAnimation.h"
#include "MHWIAnimInstance.generated.h"

/** Locomotion graph reads these values; the character alone owns combat state. */
UCLASS(Blueprintable, BlueprintType)
class INTROCPP_API UMHWIAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UMHWIAnimInstance();
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;
    /** R06 direct weapon-bank requests use native mode 1: capture the displayed
     * pose, then interpolate on the independent owner-frame clock. */
    void BeginNativeBlend(int32 InterpolationFrames);
    void CancelNativeBlend();
    bool ReadNativeBaseMotion(MHWI::Native::FMotionSample& OutMotion);
    UPROPERTY(BlueprintReadOnly, Category="MHWI") float Speed = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") float Direction = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") bool bSheathed = true;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") bool bSprinting = false;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") bool bInAir = false;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") bool bDead = false;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") bool bInAction = false;
    UPROPERTY(BlueprintReadOnly, Category="MHWI") bool bSpecialSheathHold = false;
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
    virtual void Montage_UpdateWeight(float DeltaSeconds) override;
};
