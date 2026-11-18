#include "MHWIWeaponTrailComponent.h"

#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
    // Three rows across the band: an inner edge that fades in, and the outer edge.
    constexpr int32 TrailRows = 3;
}

UMHWIWeaponTrailComponent::UMHWIWeaponTrailComponent(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    PrimaryComponentTick.bCanEverTick = false;
    SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetGenerateOverlapEvents(false);
    SetCastShadow(false);
    bUseAsyncCooking = false;
    SetVisibility(false);

    // Faint whole-blade wisp: 1.4/0.15 read as an opaque white sail, and an early
    // toning at 0.8/0.10 still stacked into a sheet. Short life keeps overlapping
    // quads down to a brief crescent; the tip filament is the default look.
    // Kept as the alternative look, but narrowed to the outer blade and soft on
    // both edges: a hilt-to-tip band with a hard edge read as a white sail.
    FullBlade.BandStart = 0.35f;
    FullBlade.BandEnd = 1.f;
    FullBlade.Color = FLinearColor(0.86f, 0.94f, 1.f, 1.f);
    FullBlade.Intensity = 0.55f;
    FullBlade.Lifetime = 0.08f;
    FullBlade.bSoftBothEdges = true;

    // A 150 cm blade keeps ~4 cm at the tip: a filament, not a band. Both edges
    // fade so the line reads as a glow instead of a cut-out strip.
    TipOnly.BandStart = 0.97f;
    TipOnly.BandEnd = 1.f;
    TipOnly.Color = FLinearColor(1.f, 0.34f, 0.30f, 1.f);
    TipOnly.Intensity = 1.8f;
    TipOnly.Lifetime = 0.26f;
    TipOnly.bSoftBothEdges = true;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> TrailMaterial(
        TEXT("/Game/MHWI/Materials/M_MHWI_WeaponTrail"));
    if (TrailMaterial.Succeeded()) SetMaterial(0, TrailMaterial.Object);
}

void UMHWIWeaponTrailComponent::SetStyle(EMHWIWeaponTrailStyle NewStyle)
{
    if (NewStyle == Style) return;
    Style = NewStyle;
    ClearTrail();
}

void UMHWIWeaponTrailComponent::ClearTrail()
{
    Samples.Reset();
    if (bHasSection)
    {
        ClearAllMeshSections();
        bHasSection = false;
    }
    SetVisibility(false);
}

void UMHWIWeaponTrailComponent::UpdateTrail(bool bActive, const FVector& BladeBase, const FVector& BladeTip)
{
    const UWorld* World = GetWorld();
    if (!World) return;
    const float Now = World->GetTimeSeconds();
    const float Lifetime = FMath::Max(0.02f, ActiveLook().Lifetime);

    int32 Expired = 0;
    while (Expired < Samples.Num() && Now - Samples[Expired].Time > Lifetime) ++Expired;
    if (Expired > 0) Samples.RemoveAt(0, Expired, EAllowShrinking::No);

    if (bActive)
    {
        const bool bMoved = Samples.Num() == 0
            || FVector::DistSquared(Samples.Last().Tip, BladeTip) >= FMath::Square(MinTipTravel);
        if (bMoved)
        {
            Samples.Add(FSample{BladeBase, BladeTip, Now});
            if (Samples.Num() > MaxSamples) Samples.RemoveAt(0, Samples.Num() - MaxSamples, EAllowShrinking::No);
        }
    }

    if (Samples.Num() < 2)
    {
        if (bHasSection) ClearTrail();
        else SetVisibility(false);
        return;
    }
    Rebuild(Now);
}

void UMHWIWeaponTrailComponent::Rebuild(float Now)
{
    const FMHWIWeaponTrailLook& Look = ActiveLook();
    const float Lifetime = FMath::Max(0.02f, Look.Lifetime);
    const float BandStart = FMath::Min(Look.BandStart, Look.BandEnd);
    const float BandEnd = FMath::Max(Look.BandStart, Look.BandEnd);
    const FTransform ToLocal = GetComponentTransform().Inverse();
    const int32 Count = Samples.Num();
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FLinearColor> Colors;
    Vertices.Reserve(Count * TrailRows);
    Normals.Reserve(Count * TrailRows);
    Colors.Reserve(Count * TrailRows);
    Triangles.Reserve((Count - 1) * (TrailRows - 1) * 6);

    for (const FSample& Sample : Samples)
    {
        const float Age = FMath::Clamp(1.f - (Now - Sample.Time) / Lifetime, 0.f, 1.f);
        // The tail slides toward the outer edge: the fastest point owns the arc.
        // It converges to the band start, so a tip-only band stays a tip streak.
        const float Start = FMath::Lerp(BandStart, BandEnd, (1.f - Age) * 0.35f);
        const FVector Inner = FMath::Lerp(Sample.Base, Sample.Tip, Start);
        const FVector Outer = FMath::Lerp(Sample.Base, Sample.Tip, BandEnd);
        const float Alpha = FMath::Pow(Age, 1.6f);
        for (int32 Row = 0; Row < TrailRows; ++Row)
        {
            const float Along = static_cast<float>(Row) / (TrailRows - 1);
            Vertices.Add(ToLocal.TransformPosition(FMath::Lerp(Inner, Outer, Along)));
            Normals.Add(ToLocal.TransformVectorNoScale(FVector::UpVector));
            const float Shape = Look.bSoftBothEdges
                ? FMath::Sin(Along * PI) : FMath::Lerp(HiltAlpha, 1.f, Along);
            Colors.Add(Look.Color * (Alpha * Shape * Look.Intensity));
        }
    }
    for (int32 Index = 0; Index < Count - 1; ++Index)
    {
        for (int32 Row = 0; Row < TrailRows - 1; ++Row)
        {
            const int32 Current = Index * TrailRows + Row;
            const int32 Next = Current + TrailRows;
            Triangles.Append({Current, Current + 1, Next + 1});
            Triangles.Append({Current, Next + 1, Next});
        }
    }
    CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, TArray<FVector2D>(), Colors,
        TArray<FProcMeshTangent>(), false);
    bHasSection = true;
    // Additive ribbon: no depth write, so leaving the default flags is correct.
    SetVisibility(true);
}
