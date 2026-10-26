#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MHWIEquipmentIKProfile.generated.h"

/** Project-only TwoBoneIK chain. Source .ik values are not copied into this profile. */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIEquipmentIKChain
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName RootBone;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName MidBone;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName EndBone;
    /** Project bend/pole hint in SkeletalMesh component space, in centimeters. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector JointTargetOffset = FVector::ZeroVector;
};

/** Runtime inputs are produced by UMHWIAnimInstance; this is not a native solver replacement. */
UCLASS(BlueprintType)
class INTROCPP_API UMHWIEquipmentIKProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FMHWIEquipmentIKChain LeftArm;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FMHWIEquipmentIKChain RightArm;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FMHWIEquipmentIKChain LeftFoot;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FMHWIEquipmentIKChain RightFoot;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0")) float FootTraceUp = 35.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0")) float FootTraceDown = 65.f;
    /** Project sole offset above the detected floor, in centimeters. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float FootSoleOffsetZ = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", ClampMax="1")) float ArmAlpha = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0", ClampMax="1")) float FootAlpha = 1.f;
};
