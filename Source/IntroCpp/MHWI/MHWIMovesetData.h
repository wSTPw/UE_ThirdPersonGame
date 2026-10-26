#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MHWIMovesetData.generated.h"

class UAnimMontage;
class UAnimSequence;

UENUM(BlueprintType)
enum class EMHWIInput : uint8
{
    Light, Thrust, Spirit, Foresight, HelmBreaker, SpecialSheathe, Evade, ToggleSheathe, FadeSlash,
    SlingerBurst
};

/** All times are source montage seconds, before PlayRate. Each window hits each actor once. */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIHitWindow
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float StartTime = 0.3f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float EndTime = 0.45f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float Damage = 15.f;
    /** Optional source attack base values by captured aura level (0..3). Empty keeps Damage. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<int32, float> SpiritLevelDamage;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpiritGain = 8.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float Radius = 35.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float ForwardReach = 200.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SideExtent = 65.f;
    /** Source COL record index, or INDEX_NONE when this window has no single source record. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 ColRecordIndex = INDEX_NONE;
    /**
     * Presentation-only hit-stop. Zero is the compatibility default. Do not
     * derive this field from W03P delayed-shell timers; those are separate clocks.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HitLagSeconds = 0.f;
};

/** Provenance of each damage stage. Unavailable is the only honest "no data" value. */
UENUM(BlueprintType)
enum class EMHWIDamageStageStatus : uint8
{
    FromSource,
    ProjectAdapter,
    Unavailable
};

/**
 * Read-only record of one resolved hit. It intentionally keeps the current
 * FinalDamage semantics; the additional stages document what is source-backed
 * and what is still missing (weapon attack, sharpness, hitzone, affinity).
 */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIResolvedHit
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FName MoveId;
    UPROPERTY(BlueprintReadOnly) int32 WindowIndex = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) int32 ColRecordIndex = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) float MotionValueBase = 0.f;
    UPROPERTY(BlueprintReadOnly) float ColorMultiplier = 1.f;
    UPROPERTY(BlueprintReadOnly) float WeakMultiplier = 1.f;
    UPROPERTY(BlueprintReadOnly) float CounterMultiplier = 1.f;
    UPROPERTY(BlueprintReadOnly) float FinalDamage = 0.f;
    /** True only for a contact-scheduled delayed shell, never a direct montage window. */
    UPROPERTY(BlueprintReadOnly) bool bDelayedShell = false;
    /** Zero-based delayed sequence index; INDEX_NONE for direct hits. */
    UPROPERTY(BlueprintReadOnly) int32 ShellHitIndex = INDEX_NONE;
    /** Direct contact, or the saved relative contact evaluated at delayed emission. */
    UPROPERTY(BlueprintReadOnly) FVector ContactLocation = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) EMHWIDamageStageStatus Sharpness = EMHWIDamageStageStatus::Unavailable;
    UPROPERTY(BlueprintReadOnly) EMHWIDamageStageStatus Affinity = EMHWIDamageStageStatus::Unavailable;
    UPROPERTY(BlueprintReadOnly) EMHWIDamageStageStatus Part = EMHWIDamageStageStatus::Unavailable;
};

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRoute
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EMHWIInput Input = EMHWIInput::Light;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName NextMove;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool RequireHit = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool RequireCounter = false;
    /** Route only matches while the weapon is drawn (e.g. Roll Light -> RollStepSlash). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool RequireDrawn = false;
    /** Opt-in native gauge condition; compare with the target move's full SpiritCost. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool RequireFullSpiritCost = false;
    /** Source Montage seconds; each negative endpoint inherits the move window. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CancelStart = -1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CancelEnd = -1.f;
    /**
     * Route exists only as a project input adaptation, not as a source FSM edge.
     * The original-input preset skips these; the shortcut preset keeps them.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bProjectAdaptation = false;
};

/** Source TIML mWeaponMotionNo: an internal weapon animation, not a mount switch. */
USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIWeaponMotionEvent
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float Time = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 MotionNo = -1;
};

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIMoveDefinition
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FText DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimMontage> Montage;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimMontage> SheathedMontage;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<int32, TObjectPtr<UAnimMontage>> SpiritLevelMontages;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float PlayRate = 1.f;
    /** Source montage seconds -> speed multiplier; linearly interpolated by the local adapter. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<float, float> SourcePlayRates;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<float, float> EmpoweredSourcePlayRates;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float BlendOut = 0.12f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CancelStart = 0.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CancelEnd = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FMHWIHitWindow> DamageWindows;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FMHWIRoute> Routes;
    /** Ordered, source-montage seconds. Negative numbers retain the current motion. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FMHWIWeaponMotionEvent> WeaponMotionEvents;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpiritCost = 0.f;
    /** Spirit Blade I may use its weak attack when the normal cost is unavailable. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bAllowWeakSpiritAttack = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float WeakDamageMultiplier = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float WeakSpiritGain = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpiritGainOnStart = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bRequireSpiritLevel = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bRequireNonzeroGauge = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bConsumeAllGauge = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bRaiseSpiritOnHit = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bSpendSpiritLevel = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bPreserveLevelOnCounter = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCounter = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCounterOnlyForIai = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bInvulnerable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterStart = 0.05f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterEnd = 0.35f;
    /** Opt-in migration: defense windows are [start,end), independently of routes. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bIndependentDefenseWindows = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float InvulnerabilityStart = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float InvulnerabilityEnd = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float EmpoweredInvulnerabilityEnd = -1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float LowGaugeInvulnerabilityEnd = -1.f;
    /** Checked against gauge before this move consumes it, not the remaining gauge. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterMinimumGauge = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCounterRestoresGaugeOnHit = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterHyperArmorSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterDamageMultiplier = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float GaugeRegenOnHitSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterGaugeRegenOnHitSeconds = -1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float GaugeRegenOnCommitSeconds = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float RedGaugeRegenOnCommitSeconds = -1.f;
    /**
     * Direction correction. Values are project tuning, not original-game constants.
     * Montage seconds; TurnMaxAngle/ReturnTurnMaxAngle are total degrees per window
     * (0 disables), TurnSpeed is degrees per second. ReturnTurnStartTime < 0 disables
     * the optional second window (e.g. Foresight retreat vs. return slash).
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float TurnStartTime = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float TurnEndTime = 0.12f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float TurnMaxAngle = 25.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float TurnSpeed = 360.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float ReturnTurnStartTime = -1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float ReturnTurnEndTime = -1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float ReturnTurnMaxAngle = 45.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bSheathAtEnd = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bUnsheathAtStart = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bHoldsSpecialSheath = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpecialSheathHoldTime = -1.f;
    /** Enables vertical montage root motion only for hit-confirmed aerial stages. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bUseFullRootMotion = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName AutoFollowUp;
    /** A hit-confirmed automatic link, e.g. SpiritThrust -> SpiritHelmBreaker. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName AutoFollowUpOnHit;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float AutoFollowUpTime = 0.f;
};

/** Separate MHWI sandbox data. Does not replace the existing player's action component. */
UCLASS(BlueprintType)
class INTROCPP_API UMHWIMovesetData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, FMHWIMoveDefinition> Moves;
    /** Optional, independent weapon skeleton. swo001 EVWP mMotNo=0 selects wg03_00. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<int32, TObjectPtr<UAnimSequence>> WeaponMotions;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> Idle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> Walk;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> Run;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> SheathedIdle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> SheathedWalk;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> SheathedRun;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequence> SpecialSheathedIdle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float WalkSpeed = 180.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float RunSpeed = 420.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float BaseDamageMultiplier = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float InputBufferSeconds = 0.3f;
    /** Action99 wait in Actor seconds; the 73/80/129 animation policy remains separate. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpecialSheathHoldSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float GaugeRegenPerSecond = 100.f / 15.f;
    /** W03P 0x51d: colour-T pause assigned by a qualified Roundslash commit, not Q decay. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpiritDecayPauseOnRaiseSeconds = 10.f;
    /** W03P 0x499/0x49d: countdown -= dt / scale; one 0.05 Q step per expiry. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpiritGaugeDecayTimeScale = 120.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpiritGaugeDecayFraction = 0.05f;
    /** Action91/92 contact-scheduled shell timing and colour-indexed base values. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmShellFirstDelay = 0.4f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmShellInterval = 0.05f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 HelmShellHitLimit = 7;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> HelmShellDamageByLevel = {0.f, 10.f, 15.f, 25.f};
    /** Action102: one second hit after 0.5 s; level zero emits no valid shell. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float IaiShellDelay = 0.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> IaiShellDamageByLevel = {0.f, 55.f, 72.f, 86.f};
    /** PLP protection row, in floating-point source frames rather than montage seconds. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> EvasionProtectionFrames = {13.f, 15.f, 17.f, 19.f, 22.f, 25.f};
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float EvasionMantleProtectionFrames = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float CounterArmorDamageMultiplier = 0.5f;
    /**
     * Helm Breaker aerial motion. Project tuning, not verified original-game
     * constants: cm/s, cm/s^2, and Montage seconds respectively.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmAirVerticalSpeed = 700.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmAirForwardSpeed = 200.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmAirGravity = 1250.f;
    /** Positive magnitude of the downward speed applied when the air slash commits. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmStrikeSpeed = 3000.f;
    /** Strike-montage seconds where the fast descent commits (25/60 s); not at 0 s. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float HelmStrikeStartTime = 0.4166667f;
    /** Index 0..3: no aura / white / yellow / red. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> SpiritLevelDurations = {0.f, 195.f, 135.f, 60.f};
};
