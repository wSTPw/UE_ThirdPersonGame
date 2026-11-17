#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MHWI/MHWIContactResponse.h"
#include "MHWIRathianApproxData.generated.h"

class UAnimSequence;

UENUM(BlueprintType)
enum class EMHWIRathianApproxQualification : uint8
{
    Evidenced,
    EvidencedConsumptionApprox,
    EngineeringFixture,
    Unavailable
};

UENUM(BlueprintType)
enum class EMHWIRathianApproxMoveKind : uint8
{
    Idle,
    Locomotion,
    Attack,
    Turn,
    SkipNotInV1
};

UENUM(BlueprintType)
enum class EMHWIRathianAttackPhaseKind : uint8
{
    Windup,
    Active,
    Recovery,
    TailTakeoff,
    TailLanding
};

/** Local oriented collision box sampled from BoneName on the current skeletal pose. */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianAttackBox
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName BoneName = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FVector LocalOffsetCm = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FRotator LocalRotation = FRotator::ZeroRotator;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FVector HalfExtentCm = FVector(45.f, 45.f, 45.f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification Qualification = EMHWIRathianApproxQualification::EngineeringFixture;
};

/** Phase times are normalized [0,1] of its sequence; speeds are cm/s, durations seconds. */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianAttackPhase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianAttackPhaseKind Kind = EMHWIRathianAttackPhaseKind::Windup;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UAnimSequence> Animation;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0", ClampMax="1")) float WindowStart = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0", ClampMax="1")) float WindowEnd = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bAttackWindowEnabled = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bUseLegacySecondsWindow = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float WindowStartSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float WindowEndSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification WindowQualification = EMHWIRathianApproxQualification::EngineeringFixture;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<FMHWIRathianAttackBox> HitBoxes;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float Damage = 20.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIImpactSize ImpactSize = EMHWIImpactSize::Medium;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification ImpactSizeQualification = EMHWIRathianApproxQualification::EngineeringFixture;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FVector KnockbackVelocity = FVector(500.f, 0.f, 250.f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float MoveSpeedCmPerSecond = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification MovementQualification = EMHWIRathianApproxQualification::EngineeringFixture;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float TakeoffHeightCm = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification FlightQualification = EMHWIRathianApproxQualification::EngineeringFixture;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0.01")) float BlendInSeconds = 0.12f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float BlendOutSeconds = 0.12f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bSpawnFireballAtStart = false;
    /** Engineering adapter event time in source-sequence seconds; positive values fire once when phase progress crosses the time. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float FireballSpawnTimeSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName FireballSocketName = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FVector FireballLocalOffsetCm = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification FireballSpawnQualification = EMHWIRathianApproxQualification::EngineeringFixture;
};

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianApproxMove
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FString RegistryName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 RegistryId = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 LegacyThkActionId = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxMoveKind Kind = EMHWIRathianApproxMoveKind::Attack;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification AnimQualification = EMHWIRathianApproxQualification::Unavailable;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UAnimSequence> Animation;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<FMHWIRathianAttackPhase> Phases;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float AttackWindowStartSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float AttackWindowEndSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification AttackWindowQualification = EMHWIRathianApproxQualification::Unavailable;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float DamageProxyMotionValue = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification DamageQualification = EMHWIRathianApproxQualification::Unavailable;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float AttackRangeCm = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float PreferredMinDistanceCm = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float PreferredMaxDistanceCm = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float MaxAngleDegrees = 180.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float CooldownSeconds = 0.8f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EMHWIRathianApproxQualification DecisionQualification = EMHWIRathianApproxQualification::EngineeringFixture;
};

UCLASS(BlueprintType)
class INTROCPP_API UMHWIRathianApproxStatsData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Health") float MaxHealth = 3000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Health") EMHWIRathianApproxQualification MaxHealthQualification = EMHWIRathianApproxQualification::EvidencedConsumptionApprox;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Rage") float RageBuildToTrigger = 600.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Rage") float RageDurationSeconds = 80.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Rage") float RageDamageModifier = 1.15f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Rage") float RageSpeedModifier = 1.05f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Rage") float RageBuildupPerDamagePoint = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Rage") EMHWIRathianApproxQualification RageQualification = EMHWIRathianApproxQualification::EvidencedConsumptionApprox;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") float DecisionCooldownSeconds = 0.35f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") float LocomotionSpeedCmPerSecond = 300.f;
    /** Engineering tuning for patrol gait; zero falls back to half of the legacy locomotion speed. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Locomotion|Engineering") float PatrolSpeedCmPerSecond = 0.f;
    /** Engineering tuning for combat approach gait; zero falls back to the legacy locomotion speed. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Locomotion|Engineering") float ApproachSpeedCmPerSecond = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") float TurnSpeedDegPerSecond = 240.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") float PatrolRadiusCm = 900.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") float SightRangeCm = 1800.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision", meta=(ClampMin="0", ClampMax="180")) float SightHalfAngleDegrees = 70.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") float LoseTargetRangeCm = 2400.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Decision") EMHWIRathianApproxQualification DecisionQualification = EMHWIRathianApproxQualification::EngineeringFixture;
};

UCLASS(BlueprintType)
class INTROCPP_API UMHWIRathianApproxMovesetData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<FMHWIRathianApproxMove> Moves;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Locomotion") TSoftObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Locomotion") TSoftObjectPtr<UAnimSequence> WalkAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Locomotion") TSoftObjectPtr<UAnimSequence> RunAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Locomotion") TSoftObjectPtr<UAnimSequence> DeathAnimation;
    UMHWIRathianApproxMovesetData();
};
