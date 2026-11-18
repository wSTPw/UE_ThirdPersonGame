#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "MHWIWeaponTrailComponent.generated.h"

/** Two authored looks for the same ribbon; switching clears the stored samples. */
UENUM(BlueprintType)
enum class EMHWIWeaponTrailStyle : uint8
{
    /** Whole blade sweeps a broad, cool-white band. */
    FullBlade,
    /** Only the last stretch of the blade sweeps, with a faint red glow. */
    TipOnly
};

/** Band geometry along the blade plus the additive colour it is premultiplied with. */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIWeaponTrailLook
{
    GENERATED_BODY()
    /** Start and end of the band along the blade: 0 = guard, 1 = tip. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0.0", ClampMax="1.0")) float BandStart = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0.0", ClampMax="1.0")) float BandEnd = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Color = FLinearColor(0.86f, 0.94f, 1.f, 1.f);
    /** Premultiplied brightness; above 1 reads as a glow on additive blending. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0.0")) float Intensity = 1.4f;
    /** Seconds a sample stays visible for this look. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0.02", ClampMax="1.0")) float Lifetime = 0.15f;
    /** Fade both band edges instead of only the inner one: a glowing filament. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bSoftBothEdges = false;
};

/**
 * Blade trail rebuilt from the weapon's blade base/tip line.
 * Samples are recorded only while an attack window is open; each vertex keeps
 * its own age, so the tail fades without touching a material parameter.
 * Presentation only: it never queries or authorizes damage.
 */
UCLASS(ClassGroup=(MHWI), meta=(BlueprintSpawnableComponent))
class INTROCPP_API UMHWIWeaponTrailComponent : public UProceduralMeshComponent
{
    GENERATED_BODY()
public:
    UMHWIWeaponTrailComponent(const FObjectInitializer& ObjectInitializer);

    /** One call per rendered frame, after the weapon pose has been evaluated. */
    void UpdateTrail(bool bActive, const FVector& BladeBase, const FVector& BladeTip);
    void ClearTrail();
    /** Diagnostic only: recorded samples feeding the current ribbon. */
    int32 GetSampleCount() const { return Samples.Num(); }

    EMHWIWeaponTrailStyle GetStyle() const { return Style; }
    /**
     * Switches the look. Samples from the previous look describe a different band,
     * so they are dropped instead of snapping to the new geometry mid-swing.
     */
    UFUNCTION(BlueprintCallable, Category="MHWI|Trail")
    void SetStyle(EMHWIWeaponTrailStyle NewStyle);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Trail") EMHWIWeaponTrailStyle Style = EMHWIWeaponTrailStyle::TipOnly;
    /** Whole-blade sweep: broad white band along the full edge. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Trail") FMHWIWeaponTrailLook FullBlade;
    /** Tip streak: only the last ~22 cm of the blade, faint red. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Trail") FMHWIWeaponTrailLook TipOnly;
    /** Samples kept for the ribbon. */
    UPROPERTY(EditAnywhere, Category="MHWI|Trail", meta=(ClampMin="3", ClampMax="64"))
    int32 MaxSamples = 20;
    /** Tip travel needed for a new sample, in cm; a frozen pose stops adding. */
    UPROPERTY(EditAnywhere, Category="MHWI|Trail", meta=(ClampMin="0.0"))
    float MinTipTravel = 2.f;
    /** Alpha at the inner band edge; the outer edge always stays at full strength. */
    UPROPERTY(EditAnywhere, Category="MHWI|Trail", meta=(ClampMin="0.0", ClampMax="1.0"))
    float HiltAlpha = 0.0f;

private:
    struct FSample
    {
        FVector Base = FVector::ZeroVector;
        FVector Tip = FVector::ZeroVector;
        float Time = 0.f;
    };
    TArray<FSample> Samples;
    bool bHasSection = false;
    const FMHWIWeaponTrailLook& ActiveLook() const { return Style == EMHWIWeaponTrailStyle::TipOnly ? TipOnly : FullBlade; }
    void Rebuild(float Now);
};
