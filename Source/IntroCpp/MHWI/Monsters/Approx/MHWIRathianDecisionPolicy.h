#pragma once
#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "MHWIRathianApproxData.h"
#include "MHWIRathianDecisionPolicy.generated.h"

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianDecisionContext
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) float TargetDistanceCm = 0.f;
    /** Signed horizontal angle in degrees, [-180,180], positive is right. */
    UPROPERTY(BlueprintReadOnly) float TargetAngleDeg = 0.f;
    UPROPERTY(BlueprintReadOnly) bool bTargetAlive = false;
    UPROPERTY(BlueprintReadOnly) bool bInRage = false;
    UPROPERTY(BlueprintReadOnly) float RageBuildup = 0.f;
    UPROPERTY(BlueprintReadOnly) FString LastMoveName;
    UPROPERTY(BlueprintReadOnly) float TimeSinceLastMoveEnd = 0.f;
    UPROPERTY(BlueprintReadOnly) int32 ConsecutiveAttacks = 0;
    UPROPERTY(BlueprintReadOnly) float DefaultStopDistanceCm = 260.f;
    UPROPERTY(BlueprintReadOnly) TArray<FString> CoolingMoveNames;
};

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianActionRequest
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) EMHWIRathianApproxMoveKind Kind = EMHWIRathianApproxMoveKind::Idle;
    UPROPERTY(BlueprintReadOnly) FString RegistryName;
    UPROPERTY(BlueprintReadOnly) float DesiredStopDistanceCm = 0.f;
    UPROPERTY(BlueprintReadOnly) FString Reason;
};

UINTERFACE(MinimalAPI, BlueprintType)
class UMHWIRathianDecisionPolicy : public UInterface
{
    GENERATED_BODY()
};

/** Policy remains replaceable; the component supplies a validated move snapshot. */
class IMHWIRathianDecisionPolicy
{
    GENERATED_BODY()
public:
    virtual FMHWIRathianActionRequest EvaluatePolicy(const FMHWIRathianDecisionContext& Context,
        const TArray<FMHWIRathianApproxMove>& QualifiedMoves) const = 0;
};
