#include "MHWIRathianSourceMovementComponent.h"

#include "Components/SceneComponent.h"
#include "GameFramework/Pawn.h"
#include "Templates/UnrealTemplate.h"

namespace
{
constexpr double SourceTimeTolerance = 1.e-6;
constexpr int32 MaxSourceSamples = 100000;

bool IsFiniteVector(const FVector& Value)
{
    return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
}

bool IsRigidPose(const FTransform& Value)
{
    const FQuat Rotation = Value.GetRotation();
    return IsFiniteVector(Value.GetTranslation()) && IsFiniteVector(Value.GetScale3D())
        && !Rotation.ContainsNaN() && Rotation.IsNormalized()
        && Value.GetScale3D().Equals(FVector::OneVector, 1.e-4);
}

bool IsQualificationValid(EMHWIRathianMotionQualification Value)
{
    return Value >= EMHWIRathianMotionQualification::EngineeringAdapter
        && Value <= EMHWIRathianMotionQualification::RuntimeCompared;
}

bool HasConsumerEvidence(EMHWIRathianMotionQualification Value)
{
    return Value == EMHWIRathianMotionQualification::NativeConsumerVerified
        || Value == EMHWIRathianMotionQualification::RuntimeCompared;
}

bool IsSha256(const FString& Value)
{
    if (Value.Len() != 64) return false;
    for (const TCHAR Character : Value)
        if (!FChar::IsHexDigit(Character)) return false;
    return true;
}
}

UMHWIRathianSourceMovementComponent::UMHWIRathianSourceMovementComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    bAutoActivate = true;
    bAutoUpdateTickRegistration = false;
}

bool UMHWIRathianSourceMovementComponent::Fail(
    EMHWIRathianSourceMoveResult Result, const TCHAR* Reason, FString* OutReason)
{
    LastMoveResult = Result;
    if (OutReason) *OutReason = Reason;
    return false;
}

bool UMHWIRathianSourceMovementComponent::ConfigureQualifiedMotion(
    const FMHWIRathianQualifiedSourceMotion& InMotion, bool bRequireSourceSemantics, FString& OutReason)
{
    check(IsInGameThread());
    OutReason.Reset();
    if (bAdvancingSource)
        return Fail(EMHWIRathianSourceMoveResult::ReentrantCall, TEXT("Motion is being advanced."), &OutReason);
    if (bMotionActive && !bMotionFinished)
        return Fail(EMHWIRathianSourceMoveResult::StaleAction, TEXT("Cancel the active run before replacing its track."), &OutReason);

    // An unsuccessful configuration never leaves an older track authorized.
    bConfigured = false;
    bSourceSemanticsQualified = false;
    bMotionActive = false;
    bMotionFinished = false;
    Velocity = FVector::ZeroVector;

    const bool bMetadataValid = IsSha256(InMotion.SourceSha256)
        && !InMotion.MotionBank.IsEmpty() && InMotion.MotionSlot >= 0
        && !InMotion.EvidencePath.IsEmpty() && !InMotion.TimeBasis.IsEmpty()
        && !InMotion.CoordinateBasis.IsEmpty()
        && InMotion.TimeUnit >= EMHWIRathianSourceTimeUnit::NativeFrames
        && InMotion.TimeUnit <= EMHWIRathianSourceTimeUnit::NativeTicks
        && FMath::IsFinite(InMotion.UnitsPerSecond) && InMotion.UnitsPerSecond >= 0.0
        && IsQualificationValid(InMotion.MotionBindingQualification)
        && IsQualificationValid(InMotion.TimeBasisQualification)
        && IsQualificationValid(InMotion.CoordinateBasisQualification)
        && IsQualificationValid(InMotion.RootTrackQualification);
    if (!bMetadataValid)
        return Fail(EMHWIRathianSourceMoveResult::Unqualified,
            TEXT("Missing or unverified source identity, time, coordinate, root, or binding qualification."), &OutReason);

    const bool bHasSourceSemantics = InMotion.NativeActionId >= 0 && InMotion.UnitsPerSecond > 0.0
        && HasConsumerEvidence(InMotion.MotionBindingQualification)
        && HasConsumerEvidence(InMotion.TimeBasisQualification)
        && HasConsumerEvidence(InMotion.CoordinateBasisQualification)
        && HasConsumerEvidence(InMotion.RootTrackQualification);
    if (bRequireSourceSemantics && !bHasSourceSemantics)
        return Fail(EMHWIRathianSourceMoveResult::Unqualified,
            TEXT("Strict source mode requires native action, clock conversion, and consumer evidence in every dimension."), &OutReason);

    if (InMotion.Samples.Num() < 2 || InMotion.Samples.Num() > MaxSourceSamples)
        return Fail(EMHWIRathianSourceMoveResult::InvalidSample,
            TEXT("Track must have between 2 and 100000 explicit samples."), &OutReason);

    double PreviousTime = -1.0;
    for (const FMHWIRathianSourceMotionSample& Sample : InMotion.Samples)
    {
        if (!FMath::IsFinite(Sample.SourceTime) || Sample.SourceTime < 0.0
            || Sample.SourceTime <= PreviousTime || !IsRigidPose(Sample.LocalRootTransform))
            return Fail(EMHWIRathianSourceMoveResult::InvalidSample,
                TEXT("Samples require strictly increasing finite nonnegative times and rigid finite normalized poses."), &OutReason);
        PreviousTime = Sample.SourceTime;
    }
    if (!FMath::IsNearlyZero(InMotion.Samples[0].SourceTime, SourceTimeTolerance)
        || InMotion.Samples.Last().SourceTime <= SourceTimeTolerance)
        return Fail(EMHWIRathianSourceMoveResult::InvalidSample,
            TEXT("Track must start at source zero and have a positive duration."), &OutReason);

    QualifiedMotion = InMotion;
    bConfigured = true;
    bSourceSemanticsQualified = bHasSourceSemantics;
    ActiveActionRunId = 0;
    LastSourceTime = 0.0;
    LastMoveResult = EMHWIRathianSourceMoveResult::None;
    return true;
}

bool UMHWIRathianSourceMovementComponent::BeginSourceMotion(uint64 ActionRunId, FString* OutReason)
{
    check(IsInGameThread());
    if (OutReason) OutReason->Reset();
    if (bAdvancingSource)
        return Fail(EMHWIRathianSourceMoveResult::ReentrantCall, TEXT("Cannot begin from a movement callback."), OutReason);
    if (!bConfigured)
        return Fail(EMHWIRathianSourceMoveResult::Unconfigured, TEXT("No qualified track is configured."), OutReason);
    if (ActionRunId == 0 || ActionRunId <= LastStartedActionRunId)
        return Fail(EMHWIRathianSourceMoveResult::StaleAction, TEXT("ActionRunId must be nonzero and newer than prior runs."), OutReason);
    if (!IsValid(UpdatedComponent) || !IsValid(GetPawnOwner()) || UpdatedComponent->GetOwner() != GetOwner()
        || !IsRigidPose(UpdatedComponent->GetComponentTransform()))
        return Fail(EMHWIRathianSourceMoveResult::InvalidOwner, TEXT("A rigid Pawn-owned UpdatedComponent is required."), OutReason);

    MotionOrigin = UpdatedComponent->GetComponentTransform();
    ActiveActionRunId = ActionRunId;
    LastStartedActionRunId = ActionRunId;
    LastSourceTime = 0.0;
    Velocity = FVector::ZeroVector;
    bMotionActive = true;
    bMotionFinished = false;
    LastMoveResult = EMHWIRathianSourceMoveResult::Applied;
    return true;
}

FTransform UMHWIRathianSourceMovementComponent::SampleRoot(double SourceTime) const
{
    const TArray<FMHWIRathianSourceMotionSample>& Samples = QualifiedMotion.Samples;
    if (SourceTime <= Samples[0].SourceTime) return Samples[0].LocalRootTransform;
    if (SourceTime >= Samples.Last().SourceTime) return Samples.Last().LocalRootTransform;

    int32 Lower = 0;
    int32 Upper = Samples.Num() - 1;
    while (Upper - Lower > 1)
    {
        const int32 Middle = Lower + (Upper - Lower) / 2;
        if (Samples[Middle].SourceTime <= SourceTime) Lower = Middle;
        else Upper = Middle;
    }
    const double Alpha = (SourceTime - Samples[Lower].SourceTime)
        / (Samples[Upper].SourceTime - Samples[Lower].SourceTime);
    FTransform Result;
    Result.Blend(Samples[Lower].LocalRootTransform, Samples[Upper].LocalRootTransform, Alpha);
    Result.NormalizeRotation();
    return Result;
}

bool UMHWIRathianSourceMovementComponent::AdvanceToSourceTime(
    uint64 ActionRunId, double AbsoluteSourceTime, FHitResult& OutHit, FString* OutReason)
{
    check(IsInGameThread());
    OutHit = FHitResult();
    if (OutReason) OutReason->Reset();
    if (bAdvancingSource)
        return Fail(EMHWIRathianSourceMoveResult::ReentrantCall, TEXT("Recursive source advancement is not allowed."), OutReason);
    if (!bConfigured)
        return Fail(EMHWIRathianSourceMoveResult::Unconfigured, TEXT("No qualified track is configured."), OutReason);
    if (!bMotionActive || ActionRunId == 0 || ActionRunId != ActiveActionRunId)
        return Fail(EMHWIRathianSourceMoveResult::StaleAction, TEXT("Action no longer owns movement."), OutReason);
    if (!IsValid(UpdatedComponent) || !IsValid(GetPawnOwner()))
        return Fail(EMHWIRathianSourceMoveResult::InvalidOwner, TEXT("Movement owner or updated component ended."), OutReason);

    const double EndTime = QualifiedMotion.Samples.Last().SourceTime;
    if (!FMath::IsFinite(AbsoluteSourceTime) || AbsoluteSourceTime < -SourceTimeTolerance
        || AbsoluteSourceTime > EndTime + SourceTimeTolerance)
        return Fail(EMHWIRathianSourceMoveResult::InvalidTime, TEXT("Source time is outside the explicit track."), OutReason);
    const double TargetTime = FMath::Clamp(AbsoluteSourceTime, 0.0, EndTime);
    if (TargetTime + SourceTimeTolerance < LastSourceTime)
        return Fail(EMHWIRathianSourceMoveResult::ReversedTime, TEXT("Source time cannot run backwards within an action."), OutReason);
    if (TargetTime <= LastSourceTime)
    {
        Velocity = FVector::ZeroVector;
        LastMoveResult = bMotionFinished ? EMHWIRathianSourceMoveResult::ReachedEnd : EMHWIRathianSourceMoveResult::Applied;
        return true;
    }

    TGuardValue<bool> AdvanceGuard(bAdvancingSource, true);
    const TWeakObjectPtr<USceneComponent> MovingComponent(UpdatedComponent);
    const FVector StartLocation = UpdatedComponent->GetComponentLocation();
    const double FromTime = LastSourceTime;

    // Sweep through each source polyline segment instead of cutting a large
    // caller step directly across a curved source trajectory.
    TArray<double, TInlineAllocator<64>> Stops;
    for (const FMHWIRathianSourceMotionSample& Sample : QualifiedMotion.Samples)
        if (Sample.SourceTime > FromTime && Sample.SourceTime < TargetTime) Stops.Add(Sample.SourceTime);
    Stops.Add(TargetTime);

    for (const double StopTime : Stops)
    {
        const FTransform RelativeRoot = SampleRoot(StopTime).GetRelativeTransform(
            QualifiedMotion.Samples[0].LocalRootTransform);
        const FTransform DesiredWorld = RelativeRoot * MotionOrigin;
        const FVector Delta = DesiredWorld.GetLocation() - UpdatedComponent->GetComponentLocation();
        SafeMoveUpdatedComponent(Delta, DesiredWorld.GetRotation(), true, OutHit);

        // Collision delegates can revoke this run or end/change its owner.
        if (!IsValid(this) || !MovingComponent.IsValid() || UpdatedComponent != MovingComponent.Get()
            || !bMotionActive || ActionRunId != ActiveActionRunId)
        {
            Velocity = FVector::ZeroVector;
            return Fail(EMHWIRathianSourceMoveResult::StaleAction, TEXT("Movement authorization changed during collision callbacks."), OutReason);
        }
        if (OutHit.bBlockingHit || OutHit.bStartPenetrating)
        {
            // The source time is not advanced beyond the last completely
            // accepted segment. No implicit sliding or future catch-up.
            bMotionActive = false;
            Velocity = FVector::ZeroVector;
            return Fail(EMHWIRathianSourceMoveResult::Blocked, TEXT("Blocking collision invalidated this movement run."), OutReason);
        }
        LastSourceTime = StopTime;
    }

    if (QualifiedMotion.UnitsPerSecond > 0.0)
    {
        const double ElapsedSeconds = (TargetTime - FromTime) / QualifiedMotion.UnitsPerSecond;
        Velocity = (UpdatedComponent->GetComponentLocation() - StartLocation) / ElapsedSeconds;
    }
    else Velocity = FVector::ZeroVector;
    UpdateComponentVelocity();

    bMotionFinished = TargetTime >= EndTime;
    LastMoveResult = bMotionFinished ? EMHWIRathianSourceMoveResult::ReachedEnd : EMHWIRathianSourceMoveResult::Applied;
    return true;
}

void UMHWIRathianSourceMovementComponent::CancelSourceMotion(uint64 ActionRunId)
{
    check(IsInGameThread());
    if (ActionRunId == 0 || ActionRunId != ActiveActionRunId) return;
    bMotionActive = false;
    bMotionFinished = false;
    ActiveActionRunId = 0;
    Velocity = FVector::ZeroVector;
    UpdateComponentVelocity();
}

void UMHWIRathianSourceMovementComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bMotionActive = false;
    ActiveActionRunId = 0;
    Velocity = FVector::ZeroVector;
    Super::EndPlay(EndPlayReason);
}
