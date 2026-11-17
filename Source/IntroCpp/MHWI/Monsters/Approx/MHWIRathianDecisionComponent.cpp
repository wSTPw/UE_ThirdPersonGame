#include "MHWIRathianDecisionComponent.h"
#include "MHWIRathianApproxStateComponent.h"
#include "MHWIRathianScriptedPolicy.h"
#include "AttributeComponent.h"
#include "GameFramework/Actor.h"

UMHWIRathianDecisionComponent::UMHWIRathianDecisionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.1f;
}

void UMHWIRathianDecisionComponent::Configure(UMHWIRathianApproxMovesetData* InMoveset,
    UMHWIRathianApproxStatsData* InStats, UMHWIRathianApproxStateComponent* InState)
{
    if (Moveset == InMoveset && Stats == InStats && State == InState && Policy) return;
    const bool bDataChanged = Moveset != InMoveset;
    Moveset = InMoveset;
    Stats = InStats;
    State = InState;
    if (!Policy) Policy = NewObject<UMHWIRathianScriptedPolicy>(this);
    if (bDataChanged) MoveCooldowns.Reset();
}

bool UMHWIRathianDecisionComponent::IsMoveConfigured(const FMHWIRathianApproxMove& Move) const
{
    if (Move.Kind != EMHWIRathianApproxMoveKind::Attack || Move.AnimQualification == EMHWIRathianApproxQualification::Unavailable) return false;
    auto HasPath = [](const TSoftObjectPtr<UAnimSequence>& Animation)
    { return Animation.IsValid() || Animation.ToSoftObjectPath().IsValid(); };
    if (Move.Phases.IsEmpty())
        return HasPath(Move.Animation) && Move.AttackWindowQualification != EMHWIRathianApproxQualification::Unavailable;

    bool bHasEffect = false;
    bool bHasTakeoff = false;
    bool bHasLanding = false;
    float TakeoffHeight = 0.f;
    for (const FMHWIRathianAttackPhase& Phase : Move.Phases)
    {
        if (!HasPath(Phase.Animation)) return false;
        if (Phase.bAttackWindowEnabled)
        {
            const bool bRangeValid = Phase.bUseLegacySecondsWindow
                ? Phase.WindowStartSeconds >= 0.f && Phase.WindowEndSeconds > Phase.WindowStartSeconds
                : Phase.WindowStart >= 0.f && Phase.WindowEnd > Phase.WindowStart && Phase.WindowEnd <= 1.f;
            if (!bRangeValid || Phase.WindowQualification == EMHWIRathianApproxQualification::Unavailable) return false;
            bHasEffect |= !Phase.HitBoxes.IsEmpty();
        }
        if (Phase.bSpawnFireballAtStart)
        {
            if (Phase.FireballSocketName.IsNone() || Phase.FireballSpawnQualification == EMHWIRathianApproxQualification::Unavailable) return false;
            bHasEffect = true;
        }
        if (Phase.Kind == EMHWIRathianAttackPhaseKind::TailTakeoff)
        { bHasTakeoff = true; TakeoffHeight = Phase.TakeoffHeightCm; }
        if (Phase.Kind == EMHWIRathianAttackPhaseKind::TailLanding) bHasLanding = true;
    }
    if (Move.RegistryName.StartsWith(TEXT("ACTION::ROLLING_TAIL_ATTACK2")) && (!bHasTakeoff || !bHasLanding || TakeoffHeight <= 0.f)) return false;
    return bHasEffect;
}
void UMHWIRathianDecisionComponent::NotifyMoveFinished(const FString& RegistryName)
{
    LastMoveName = RegistryName;
    LastMoveEndTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
    CooldownRemaining = Stats ? FMath::Max(0.f, Stats->DecisionCooldownSeconds) : 0.35f;
    if (RegistryName.StartsWith(TEXT("ACTION::")))
    {
        ++ConsecutiveAttacks;
        if (Moveset)
            for (const FMHWIRathianApproxMove& Move : Moveset->Moves)
                if (Move.RegistryName == RegistryName)
                    MoveCooldowns.Add(RegistryName, FMath::Max(0.f, Move.CooldownSeconds));
    }
    else ConsecutiveAttacks = 0;
}

void UMHWIRathianDecisionComponent::NotifyMoveRejected(const FString& RegistryName)
{
    if (!RegistryName.StartsWith(TEXT("ACTION::"))) return;
    if (Moveset)
        for (const FMHWIRathianApproxMove& Move : Moveset->Moves)
            if (Move.RegistryName == RegistryName)
                MoveCooldowns.Add(RegistryName, FMath::Max(0.f, Move.CooldownSeconds));
    CooldownRemaining = Stats ? FMath::Max(0.f, Stats->DecisionCooldownSeconds) : 0.35f;
}
void UMHWIRathianDecisionComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    const float Step = FMath::Max(0.f, DeltaTime);
    CooldownRemaining = FMath::Max(0.f, CooldownRemaining - Step);
    for (auto It = MoveCooldowns.CreateIterator(); It; ++It)
    {
        It.Value() = FMath::Max(0.f, It.Value() - Step);
        if (It.Value() <= 0.f) It.RemoveCurrent();
    }
}

FMHWIRathianActionRequest UMHWIRathianDecisionComponent::Evaluate()
{
    FMHWIRathianDecisionContext Context;
    AActor* Owner = GetOwner();
    AActor* TargetActor = Target.Get();
    if (Owner && IsValid(TargetActor))
    {
        const FVector Delta = TargetActor->GetActorLocation() - Owner->GetActorLocation();
        Context.TargetDistanceCm = Delta.Size2D();
        const FVector Flat = Delta.GetSafeNormal2D();
        const FVector Forward = Owner->GetActorForwardVector().GetSafeNormal2D();
        const FVector Right = Owner->GetActorRightVector().GetSafeNormal2D();
        const float ForwardDot = FVector::DotProduct(Forward, Flat);
        const float RightDot = FVector::DotProduct(Right, Flat);
        Context.TargetAngleDeg = FMath::RadiansToDegrees(FMath::Atan2(RightDot, ForwardDot));
        const UAttributeComponent* TargetAttributes = TargetActor->FindComponentByClass<UAttributeComponent>();
        Context.bTargetAlive = !TargetAttributes || TargetAttributes->IsAlive();
    }
    Context.bInRage = State && State->IsInRage();
    Context.RageBuildup = State ? State->GetRageBuildup() : 0.f;
    Context.LastMoveName = LastMoveName;
    Context.TimeSinceLastMoveEnd = GetWorld() ? GetWorld()->GetTimeSeconds() - LastMoveEndTime : 0.f;
    Context.ConsecutiveAttacks = ConsecutiveAttacks;
    Context.DefaultStopDistanceCm = 260.f;

    TArray<FMHWIRathianApproxMove> Qualified;
    if (Moveset)
    {
        for (const FMHWIRathianApproxMove& Move : Moveset->Moves)
        {
            if (!IsMoveConfigured(Move)) continue;
            Qualified.Add(Move);
            const float* Remaining = MoveCooldowns.Find(Move.RegistryName);
            if ((Remaining && *Remaining > 0.f) || CooldownRemaining > 0.f)
                Context.CoolingMoveNames.AddUnique(Move.RegistryName);
        }
    }

    FMHWIRathianActionRequest Request;
    if (Policy) Request = Policy->EvaluatePolicy(Context, Qualified);
    const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
    if (LastDecisionLogTime < 0.f || Now - LastDecisionLogTime >= 0.5f)
    {
        UE_LOG(LogTemp, Log,
            TEXT("[RathianApprox][Decision] dist=%.0f angle=%.0f rage=%d(%.0f) candidates=%d cooling=%d -> kind=%d '%s': %s"),
            Context.TargetDistanceCm, Context.TargetAngleDeg, Context.bInRage ? 1 : 0, Context.RageBuildup,
            Qualified.Num(), Context.CoolingMoveNames.Num(), static_cast<int32>(Request.Kind), *Request.RegistryName, *Request.Reason);
        LastDecisionLogTime = Now;
    }
    return Request;
}
