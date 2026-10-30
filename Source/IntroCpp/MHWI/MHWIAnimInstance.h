#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "MHWILinkAnimation.h"
#include "MHWIAnimInstance.generated.h"

class AMHWICharacter;
class UMHWIEquipmentIKProfile;
class UAnimSequence;

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
    /** R28 project transition facts; never drive CharacterMovement from these. */
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") bool bAccelerating = false;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") bool bDecelerating = false;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") bool bJustLanded = false;
    /** Signed turn intent in degrees; zero below the project speed/angle gates. */
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") float TurnDirection = 0.f;
    FVector PreviousVelocity = FVector::ZeroVector;

    /** Source-qualified WALK entry/turn/end clips, consumed by the AnimGraph evaluator. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="MHWI|Locomotion") TMap<int32, TObjectPtr<UAnimSequence>> LocomotionTransitionClips;
    /** W03P file 0x18c -> parameter +0x348 -> WALK entry angle gate (degrees). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="MHWI|Locomotion") float LocomotionTurnThresholdDegrees = 70.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") TObjectPtr<UAnimSequence> LocomotionTransitionSequence;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") float LocomotionTransitionTime = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") int32 LocomotionTransitionMotion = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|Locomotion") bool bLocomotionTransitionActive = false;

    /** R30 project IK profile. Effector/joint vectors are OFFSETS relative to
     * the evaluated end/mid bone, respectively. This preserves the base pose
     * and avoids feeding last frame's solved positions back into the solver. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="MHWI|IK") TObjectPtr<UMHWIEquipmentIKProfile> EquipmentIKProfile;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector LeftArmEffector = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector RightArmEffector = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector LeftFootEffector = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector RightFootEffector = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector LeftArmJointTarget = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector RightArmJointTarget = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector LeftFootJointTarget = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") FVector RightFootJointTarget = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") float LeftArmIKAlpha = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") float RightArmIKAlpha = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") float LeftFootIKAlpha = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="MHWI|IK") float RightFootIKAlpha = 0.f;
protected:
    void UpdateLocomotionTransition(const AMHWICharacter& Character, float DeltaSeconds, float PreviousSpeed);
    bool bWasLocomotionEligible = false;
    bool bHadLocomotionIntent = false;
    FVector LastLocomotionIntent = FVector::ZeroVector;
    int32 LastNaturalRollCompletionSerial = 0;
    void UpdateEquipmentIK(const AMHWICharacter& Character);
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
    virtual void Montage_UpdateWeight(float DeltaSeconds) override;
};
