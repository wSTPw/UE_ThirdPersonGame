#pragma once

#include "CoreMinimal.h"
#include "MHWINativeLinkMotion.h"

class USkeletalMeshComponent;

struct INTROCPP_API FMHWIWeaponAttachmentContext
{
    MHWI::Native::FMotionSample Action;
    MHWI::Native::FMotionSample Base;
    bool bSheathed = true;
};

/** Native main/sub equipment mounting; separate from internal weapon animation.
 * Game-thread Update follows final hunter evaluation. LMT control channels select
 * helper47/helper30 or the fixed back descriptor; never propagate selector scale.
 */
struct INTROCPP_API FMHWIWeaponAttachmentRuntime
{
    void Update(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Weapon,
        USkeletalMeshComponent* Scabbard, const FMHWIWeaponAttachmentContext& Context,
        float DeltaSeconds = 0.f);
    void Reset();
    bool IsBackMounted() const { return bInitialized && MainMount == 0; }

private:
    struct FScale
    {
        float Update(float Target, float DeltaSeconds);
        float Value = 1.f, Start = 1.f, Goal = 1.f, Elapsed = 0.f;
        bool bInitialized = false;
    };
    FScale MainScale, SubScale;
    bool bInitialized = false;
    uint8 MainMount = 0;
};
