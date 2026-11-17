#include "MHWIRathianScriptedPolicy.h"

FMHWIRathianActionRequest UMHWIRathianScriptedPolicy::EvaluatePolicy(
    const FMHWIRathianDecisionContext& Context,
    const TArray<FMHWIRathianApproxMove>& QualifiedMoves) const
{
    FMHWIRathianActionRequest Request;
    if (!Context.bTargetAlive)
    {
        Request.Kind = EMHWIRathianApproxMoveKind::Idle;
        Request.Reason = TEXT("target-unavailable");
        return Request;
    }

    const FMHWIRathianApproxMove* InRange = nullptr;
    const FMHWIRathianApproxMove* AlternateInRange = nullptr;
    const FMHWIRathianApproxMove* ClosestMove = nullptr;
    float ClosestGap = TNumericLimits<float>::Max();
    bool bRangeCandidateCooling = false;
    bool bRangeCandidateMisfacing = false;
    float StopDistance = Context.DefaultStopDistanceCm;

    for (const FMHWIRathianApproxMove& Move : QualifiedMoves)
    {
        if (Move.Kind != EMHWIRathianApproxMoveKind::Attack) continue;
        const float Gap = Context.TargetDistanceCm < Move.PreferredMinDistanceCm
            ? Move.PreferredMinDistanceCm - Context.TargetDistanceCm
            : (Context.TargetDistanceCm > Move.PreferredMaxDistanceCm
                ? Context.TargetDistanceCm - Move.PreferredMaxDistanceCm : 0.f);
        if (Gap < ClosestGap)
        {
            ClosestGap = Gap;
            ClosestMove = &Move;
            StopDistance = (Move.PreferredMinDistanceCm + Move.PreferredMaxDistanceCm) * 0.5f;
        }
        if (Gap > 0.f) continue;
        if (FMath::Abs(Context.TargetAngleDeg) > Move.MaxAngleDegrees)
        {
            bRangeCandidateMisfacing = true;
            continue;
        }
        if (Context.CoolingMoveNames.Contains(Move.RegistryName))
        {
            bRangeCandidateCooling = true;
            continue;
        }
        if (!InRange) InRange = &Move;
        if (Move.RegistryName != Context.LastMoveName) AlternateInRange = &Move;
    }

    if (InRange)
    {
        const FMHWIRathianApproxMove* Chosen = InRange;
        if (Context.ConsecutiveAttacks > 0 && InRange->RegistryName == Context.LastMoveName && AlternateInRange)
            Chosen = AlternateInRange;
        Request.Kind = EMHWIRathianApproxMoveKind::Attack;
        Request.RegistryName = Chosen->RegistryName;
        Request.Reason = FString::Printf(TEXT("distance %.0f angle %.0f -> %s (last=%s chain=%d rage=%d)"),
            Context.TargetDistanceCm, Context.TargetAngleDeg, *Chosen->RegistryName,
            *Context.LastMoveName, Context.ConsecutiveAttacks, Context.bInRage ? 1 : 0);
        return Request;
    }

    if (bRangeCandidateMisfacing)
    {
        Request.Kind = EMHWIRathianApproxMoveKind::Turn;
        Request.Reason = FString::Printf(TEXT("in move range but facing %.0f deg exceeds configured band"), Context.TargetAngleDeg);
        return Request;
    }
    if (bRangeCandidateCooling)
    {
        Request.Kind = EMHWIRathianApproxMoveKind::Idle;
        Request.Reason = TEXT("in move range; configured move cooldown active");
        return Request;
    }

    Request.Kind = EMHWIRathianApproxMoveKind::Locomotion;
    Request.DesiredStopDistanceCm = ClosestMove ? StopDistance : Context.DefaultStopDistanceCm;
    Request.Reason = FString::Printf(TEXT("no available attack band at %.0f cm; adjust to %.0f cm"),
        Context.TargetDistanceCm, Request.DesiredStopDistanceCm);
    return Request;
}
