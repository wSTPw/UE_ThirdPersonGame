#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "IncomingDamageResponse.h"
#include "Animation/AnimEnums.h"
#include "MHWIMovesetData.h"
#include "MHWIWeaponAttachment.h"
#include "MHWILinkAnimation.h"
#include "MHWINativeSources.h"
#include "MHWIContactResponse.h"
#include "MHWICharacter.generated.h"

class UAttributeComponent;
class UCameraComponent;
class USpringArmComponent;
class UInputMappingContext;
class UInputAction;
class UEnhancedInputLocalPlayerSubsystem;
class USkeletalMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMHWIStateChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMHWIMoveChanged, FName, MoveId, FText, DisplayName);
/** One resolved hit; the only entry point for future audio/VFX/camera consumers. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FMHWIHitResolved, float, SourceTime, int32, WindowIndex, int32, ColRecordIndex);

/** Public control state. Hit reactions own input until their native source ends. */
UENUM(BlueprintType)
enum class EMHWIControlState : uint8
{
    Free,
    FlinchSmall,
    FlinchMedium,
    FlinchLarge,
    Dead
};

/** Independent playable MHWI sandbox with one montage-position-driven action authority. */
UCLASS(Blueprintable)
class INTROCPP_API AMHWICharacter : public ACharacter, public IIncomingDamageResponse
{
    GENERATED_BODY()
public:
    AMHWICharacter();
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void PawnClientRestart() override;
    virtual void UnPossessed() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Landed(const FHitResult& Hit) override;
    virtual float TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
    virtual bool InterceptIncomingDamage_Implementation(float DamageAmount, AActor* DamageInstigator) override;
    virtual bool AdjustIncomingDamage_Implementation(float DamageAmount, AActor* DamageInstigator, float& AdjustedDamage) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<UAttributeComponent> Attributes;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<USpringArmComponent> SpringArm;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<USkeletalMeshComponent> WeaponMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="MHWI") TObjectPtr<USkeletalMeshComponent> ScabbardMesh;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") TObjectPtr<UMHWIMovesetData> Moveset;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FName WeaponBone = TEXT("bone_012");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FName ScabbardBone = TEXT("bone_000");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FTransform WeaponRelativeTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FTransform ScabbardRelativeTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FName SheathedWeaponBone = TEXT("bone_000");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FTransform SheathedWeaponRelativeTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FName SpecialScabbardBone = TEXT("bone_008");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FTransform SpecialScabbardRelativeTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI") FTransform SpecialWeaponRelativeTransform;
    UPROPERTY(BlueprintAssignable, Category="MHWI") FMHWIStateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="MHWI") FMHWIMoveChanged OnMoveChanged;
    UPROPERTY(BlueprintAssignable, Category="MHWI|Combat") FMHWIHitResolved OnHitResolved;

    UFUNCTION(BlueprintCallable, Category="MHWI") bool RequestInput(EMHWIInput Input);
    /** Monotonic count of received command attempts, including rejected requests.
     *  Exposed as int32 because blueprint does not support uint32. */
    UFUNCTION(BlueprintPure, Category="MHWI|Input") int32 GetInputRequestSerial() const { return static_cast<int32>(InputRequestSerial); }
    /** Last command passed to RequestInput; this is not proof that a move started. */
    UFUNCTION(BlueprintPure, Category="MHWI|Input") EMHWIInput GetLastRequestedInput() const { return LastRequestedInput; }
    UFUNCTION(BlueprintCallable, Category="MHWI") bool StartMove(FName MoveId);
    UFUNCTION(BlueprintCallable, Category="MHWI") void InterruptMove();
    /**
     * Original-gamepad chord preset. PC keyboard/mouse has an independent
     * official-style Ctrl chord path and is not affected by this flag.
     * Arbitration between simultaneously true gamepad chords is a project adapter.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Input") bool bOriginalInputPreset = false;
    /** External UI/menu gate. Setting it clears any buffered command. */
    UFUNCTION(BlueprintCallable, Category="MHWI|Input") void SetInputBlocked(bool bBlocked);
    UFUNCTION(BlueprintPure, Category="MHWI|Input") bool IsInputBlocked() const { return bInputBlocked; }
    UFUNCTION(BlueprintPure, Category="MHWI") EMHWIControlState GetControlState() const { return ControlState; }
    /** Natural end of a real drawn roll only; no debug setter or fabricated source. */
    UFUNCTION(BlueprintPure, Category="MHWI|Locomotion") int32 GetNaturalRollCompletionSerial() const { return static_cast<int32>(NaturalRollCompletionSerial); }
    /** Diagnostic only: last rejected move-start stage; never affects permission. */
    UFUNCTION(BlueprintPure, Category="MHWI|Debug") FString GetLastMoveStartFailure() const { return LastMoveStartFailure; }
    /** Read-only accepted R06 entry plan; never authorizes an action. */
    UFUNCTION(BlueprintPure, Category="MHWI|Debug") FString GetLastNativeEntryDiagnostic() const { return LastNativeEntryDiagnostic; }
    /** Actual bound montage instance clock; distinguishes prefix from main. */
    UFUNCTION(BlueprintPure, Category="MHWI|Debug") FString GetNativePlaybackDiagnostic() const;
    /** Latest resolved hit, including explicit Unavailable stages (R22). */
    UFUNCTION(BlueprintPure, Category="MHWI|Combat") FMHWIResolvedHit GetLastResolvedHit() const { return LastResolvedHit; }
    /** Game-thread handoff from a real native action owner. Returns a nonzero
     * revocation token, or zero on failure. Bound to the exact montage instance.
     * This supplies provenance, not an input/cancel permission or a playable Shot.
     */
    uint32 BindNativeActionSource(UAnimMontage* Montage, int32 InstanceId,
        MHWI::Native::FActionIdentity Identity);
    void ReleaseNativeActionSource(uint32 BindingToken);
    /** True means damage was consumed by this character's current avoidance/counter window. */
    UFUNCTION(BlueprintCallable, Category="MHWI") bool HandleIncomingDamage(float DamageAmount, AActor* DamageInstigator);
    UFUNCTION(BlueprintPure, Category="MHWI") float GetSpiritGauge() const { return SpiritGauge; }
    UFUNCTION(BlueprintPure, Category="MHWI") int32 GetSpiritLevel() const { return SpiritLevel; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetSpiritTimeRemaining() const { return SpiritTimeRemaining; }
    UFUNCTION(BlueprintPure, Category="MHWI") bool IsSheathed() const { return bSheathed; }
    UFUNCTION(BlueprintPure, Category="MHWI") bool IsSpecialSheathHolding() const { return bSpecialSheathHeld; }
    UFUNCTION(BlueprintPure, Category="MHWI") bool IsSprinting() const { return bSprintHeld && bSheathed && CurrentMove.IsNone() && !NativeSourceMontage; }
    UFUNCTION(BlueprintPure, Category="MHWI") FName GetCurrentMove() const { return CurrentMove.IsNone() ? NativeSourceMove : CurrentMove; }
    /** Training adapter ammunition/damage; original ammo types/parts remain R25. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Slinger", meta=(ClampMin="0")) int32 SlingerAmmo = 30;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Slinger", meta=(ClampMin="0")) float SlingerBurstDamage = 1.f;
    /** Training-only selectors for the sourced PLP table, not an equipment/skill system. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Defense", meta=(ClampMin="0", ClampMax="5")) int32 EvadeWindowLevel = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Defense") bool bEvasionMantleActive = false;
    /** Project cancel adapters, in source seconds; exact original masks remain R07. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Timing", meta=(ClampMin="0")) float ImpactCancelStart = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Timing", meta=(ClampMin="0")) float RecoilCancelStart = 10.f / 60.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MHWI|Timing", meta=(ClampMin="0")) float SlingerCancelStart = 45.f / 60.f;
    UFUNCTION(BlueprintPure, Category="MHWI") FString GetMoveStatus() const;
    UFUNCTION(BlueprintPure, Category="MHWI") FText GetMoveDisplayName() const;
    UFUNCTION(BlueprintPure, Category="MHWI") int32 GetWeaponMotionNo() const { return WeaponMotionNo; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetWeaponMotionPosition() const { return WeaponMotionPosition; }
    UFUNCTION(BlueprintPure, Category="MHWI") bool HasCounterConfirmed() const { return bCounterConfirmed; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetCounterArmorRemaining() const { return CounterArmorRemaining; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetGaugeRegenTimeRemaining() const { return GaugeRegenSeconds; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetSpiritDecayPauseRemaining() const { return SpiritDecayPauseRemaining; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetSpiritGaugeAtMoveStart() const { return CapturedSpiritGauge; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetSpiritGaugeDecayCountdown() const { return SpiritGaugeDecayCountdown; }
    UFUNCTION(BlueprintPure, Category="MHWI") float GetRollProtectionFramesRemaining() const { return RollProtectionFramesRemaining; }
    UFUNCTION(BlueprintPure, Category="MHWI") int32 GetPendingHelmShellCount() const { return HelmDelayedHits.Num(); }
    UFUNCTION(BlueprintPure, Category="MHWI") int32 GetPendingIaiShellCount() const { return IaiDelayedHit.IsSet() ? 1 : 0; }
protected:
    virtual void BeginPlay() override;

private:
    UPROPERTY(Transient) TObjectPtr<UInputMappingContext> RuntimeMapping;
    UPROPERTY(Transient) TObjectPtr<UInputAction> MoveAction;
    UPROPERTY(Transient) TObjectPtr<UInputAction> LookAction;
    UPROPERTY(Transient) TObjectPtr<UInputAction> SprintAction;
    UPROPERTY(Transient) TObjectPtr<UInputAction> KeyboardSprintAction;
    UPROPERTY(Transient) TArray<TObjectPtr<UInputAction>> CommandActions;
    UPROPERTY(Transient) TArray<TObjectPtr<UInputAction>> KeyboardCommandActions;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> ActiveMontage;
    UPROPERTY(Transient) FMHWIMoveDefinition ActiveDefinition;
    /** CDO hard references retain connector assets during cooking. */
    UPROPERTY() TMap<int32, TObjectPtr<UAnimSequence>> NativeConnectorSequences;
    UPROPERTY() TMap<FName, TObjectPtr<UAnimSequence>> NativeSourceSequences;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> NativeMainMontage;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> NativeRetiringMontage;
    MHWI::Native::FLinkExecution NativeLinkExecution;
    MHWI::Native::FMotionSample NativeRollRecoverySample;
    int32 NativeActionNode = INDEX_NONE;
    int32 NativeTimelineMotion = INDEX_NONE;
    float NativeConnectorPosition = 0.f;
    float NativeConnectorSourceFrame = 0.f;
    float NativeInitialPosition = 0.f;
    bool bNativeConnector = false;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> NativeSourceMontage;
    MHWI::Native::FActionIdentity NativeSourceIdentity;
    uint32 NativeSourceGeneration = 0;
    int32 NativeSourceInstanceId = INDEX_NONE;
    enum class ENativeSourceKind : uint8 { None, Impact, Recoil, Slinger };
    ENativeSourceKind NativeSourceKind = ENativeSourceKind::None;
    FName NativeSourceMove;
    MHWI::Native::FMotionSample NativeSourceLastSample;
    float NativeSourcePosition = 0.f;
    bool bNativeSourceEnded = false;
    bool bNativeSourceInterrupted = false;
    bool bNativeSlingerFired = false;
    TOptional<EMHWIInput> NativeSourceInput;
    float NativeSourceInputFrame = 0.f;
    float NativeSourceInputExpires = 0.f;
    TOptional<EMHWIImpactSize> PendingNativeImpact;
    bool bPendingNativeRecoil = false;
    int32 NativeRollRecoveryNode = INDEX_NONE;
    float NativeBlendFrames = 0.f;
    FName CurrentMove;
    float SpiritGauge = 0.f;
    int32 SpiritLevel = 0;
    float SpiritTimeRemaining = 0.f;
    float PreviousPosition = 0.f;
    float CurrentPosition = 0.f;
    float ActionStartWorldTime = 0.f;
    float SpecialSheathElapsed = 0.f;
    float GaugeRegenSeconds = 0.f;
    float CounterArmorRemaining = 0.f;
    float SpiritDecayPauseRemaining = 0.f;
    /** Native normalized countdown; initial 0.05 gives the first decay after 120*0.05 seconds. */
    float SpiritGaugeDecayCountdown = 0.05f;
    float RollProtectionFramesRemaining = 0.f;
    bool bRoundslashHitLatched = false;
    struct FMHWIDelayedHitRuntime
    {
        TWeakObjectPtr<AActor> Target;
        FVector RelativeContact = FVector::ZeroVector;
        float RemainingSeconds = 0.f;
        float MotionValue = 0.f;
        float DamageMultiplier = 1.f;
        int32 HitIndex = INDEX_NONE;
    };
    TArray<FMHWIDelayedHitRuntime> HelmDelayedHits;
    int32 HelmShellScheduledCount = 0;
    TOptional<FMHWIDelayedHitRuntime> IaiDelayedHit;
    float CapturedSpiritGauge = 0.f;
    FMHWIWeaponAttachmentRuntime WeaponAttachmentRuntime;
    float PendingExpiresAt = 0.f;
    float CapturedDamageMultiplier = 1.f;
    /** Weak-attack component captured at move start; color/base stay separate. */
    float CapturedWeakMultiplier = 1.f;
    int32 CapturedSpiritLevel = 0;
    FVector PreviousActorLocation = FVector::ZeroVector;
    FVector2D MoveInput = FVector2D::ZeroVector;
    TMap<int32, TSet<TWeakObjectPtr<AActor>>> HitActors;
    TSet<int32> WindowsThatGrantedGauge;
    TOptional<EMHWIInput> PendingInput;
    uint32 InputRequestSerial = 0;
    EMHWIInput LastRequestedInput = EMHWIInput::Light;
    TWeakObjectPtr<UEnhancedInputLocalPlayerSubsystem> InstalledInputSubsystem;
    uint32 ExecutionSerial = 0;
    int32 ActiveMontageInstanceId = INDEX_NONE;
    bool bSheathed = true;
    bool bSprintHeld = false;
    bool bSpecialSheathHeld = false;
    bool bInputBlocked = false;
    /** Held physical semantics for the original gamepad chord preset. */
    bool bSpiritHeld = false;
    bool bLightHeld = false;
    bool bThrustHeld = false;
    TArray<EMHWIInput> FrameInputEdges;
    /** PC input is device-separated so the gamepad preset cannot reinterpret it. */
    bool bKeyboardSpiritHeld = false;
    bool bKeyboardLightHeld = false;
    bool bKeyboardThrustHeld = false;
    bool bKeyboardEvadeHeld = false;
    TArray<EMHWIInput> KeyboardFrameInputEdges;
    EMHWIControlState ControlState = EMHWIControlState::Free;
    /** Hit-stop countdown; presentation clock only, never a resource timer. */
    float PendingHitLag = 0.f;
    FMHWIResolvedHit LastResolvedHit;
    /** Equipment state before this move, distinct from bUnsheathAtStart's gameplay state. */
    bool bMoveStartedSheathed = true;
    bool bHitConfirmed = false;
    bool bCounterConfirmed = false;
    bool bRaisedLevelThisAction = false;
    bool bBufferedInsideWindow = false;
    float PendingMontagePosition = 0.f;
    /** Internal weapon pose clock; source events reset it without timers/notifies. */
    int32 WeaponMotionNo = INDEX_NONE;
    float WeaponMotionPosition = 0.f;
    int32 NextWeaponMotionEvent = 0;
    bool bEnding = false;
    bool bDispatchingHits = false;
    bool bPendingDeath = false;
    bool bPendingInterruption = false;
    bool bFinishing = false;

    /**
     * Internal Helm Breaker stage. Action identity (CurrentMove) remains the
     * authoritative external fact; this enum only gates motion/lifecycle rules.
     */
    enum class EHelmPhase : uint8 { None, Rise, Air, Strike, Land };
    EHelmPhase HelmPhase = EHelmPhase::None;

    /** Roll -> Light recovery route, scoped by time and to a drawn weapon only. */
    FName RollRecoveryMove;
    uint32 NaturalRollCompletionSerial = 0;
    FString LastMoveStartFailure;
    FString LastNativeEntryDiagnostic;
    float RollRecoveryExpiresAt = -1.f;
    /** Drawn state sampled at Roll start; a sheathed Roll never consumes that route. */
    bool bRollStartedDrawn = false;
    /** A slam request queued during the Rise tail (0.3 s buffer) or pressed in Air. */
    float HelmSlamExpiresAt = -1.f;
    /** Total degrees already spent inside each turn window for this action. */
    float MainTurnAccumulated = 0.f;
    float ReturnTurnAccumulated = 0.f;
    uint32 PendingHelmLandSerial = 0;

    /** One snapshot for the whole aerial chain; restored exactly once on exit. */
    uint8 SavedMovementMode = 0;
    uint8 SavedCustomMovementMode = 0;
    float SavedGravityScale = 1.f;
    float SavedMaxFlySpeed = 600.f;
    TEnumAsByte<ERootMotionMode::Type> SavedRootMotionMode = ERootMotionMode::RootMotionFromMontagesOnly;
    bool SavedOrientRotationToMovement = true;
    bool bHelmSnapshotValid = false;
    bool bHelmSlamRequested = false;
    bool bHelmSlamAuthorized = false;
    /** One-shot: the Strike clip reached HelmStrikeStartTime and applied its descent. */
    bool bHelmStrikeCommitted = false;
    bool bHelmPoseHeld = false;
    bool bPendingHelmLanded = false;
    bool bHelmLandTransitioning = false;

    void BuildInputMapping();
    void InstallInputMapping();
    void Move(const FInputActionValue& Value);
    void Look(const FInputActionValue& Value);
    void SprintStarted();
    void SprintStopped();
    void KeyboardSprintStarted();
    void SampleMoveInputForCommand();
    void CommandStarted(EMHWIInput Input);
    void CommandReleased(EMHWIInput Input);
    void KeyboardCommandStarted(EMHWIInput Input);
    void KeyboardCommandReleased(EMHWIInput Input);
    /** Resolves one frame's edges after every Started/Completed callback ran. */
    void ResolveFrameInputEdges();
    /** Official-style PC chords; a chord needs a new member edge this frame. */
    void ResolveKeyboardFrameInputEdges();
    bool IsGestureLocked() const { return ControlState != EMHWIControlState::Free; }
    /** Camera-yaw-relative world direction from the current MoveInput; zero when idle. */
    FVector GetMoveIntentWorldDirection() const;
    /** Shared Fade Slash choice for neutral and active derivations. */
    FName SelectFadeSlashMove() const;
    bool ResolveInput(EMHWIInput Input, FName& OutMove, float* OutCancelStart = nullptr, float* OutCancelEnd = nullptr) const;
    bool StartResolvedMove(FName MoveId);
    void AdvanceAction(float NewPosition, bool bAllowTransition);
    void SweepWindow(int32 WindowIndex, const FMHWIHitWindow& Window);
    bool TryConsumeBuffered(float From, float To);
    void FinishMove(bool bInterrupted, bool bStopMontage, bool bContinueHelm = false, bool bDeferEquipmentReset = false);
    void MontageEnded(UAnimMontage* Montage, bool bInterrupted, uint32 Serial);
    struct FNativeLinkStart
    {
        const MHWI::Native::FLinkEntry* Entry = nullptr;
        MHWI::Native::FMotionSample Previous;
        int32 TargetNode = INDEX_NONE;
        int32 MainMotion = INDEX_NONE;
        int32 ExplicitConnector = INDEX_NONE;
        MHWI::Native::FActionIdentity PreviousIdentity;
        bool bExactPreviousIdentity = false;
        MHWI::Native::FPlaybackRequest FirstRequest;
        float FirstPosition = 0.f;
        bool bFollowMain = true;
        bool bContinuePrevious = false;
        UAnimMontage* PreviousCarrier = nullptr;
        float PreviousPosition = 0.f;
    };
    bool PrepareNativeLink(FName MoveId, UAnimMontage* Main, FNativeLinkStart& Out);
    bool BeginNativeLink(const FNativeLinkStart& Start);
    bool AdvanceNativeLink(float Position, bool bNaturalEnd = false);
    bool CommitNativeMain(const MHWI::Native::FPlaybackRequest& Request);
    void InitializeMainEventClock(float Start);
    void AdvanceConnectorWeaponEvents(float FromSourceFrame, float ToSourceFrame);
    void InitializeNativeRuntimeMoves();
    bool StartNativeSource(MHWI::Native::FActionIdentity Identity, ENativeSourceKind Kind);
    void StartNativeImpact(EMHWIImpactSize Size);
    bool TickNativeSource();
    bool RequestNativeSourceInput(EMHWIInput Input);
    bool ResolveNativeSourceInput(EMHWIInput Input, FName& Move) const;
    void NativeSourceEnded(UAnimMontage* Montage, bool bInterrupted, uint32 Token);
    void AdvanceNativeSourceEvents(const MHWI::Native::FMotionSample& From, const MHWI::Native::FMotionSample& To);
    void FireNativeSlinger();
    bool ApplyNativeBlend(UAnimMontage* Montage, const TOptional<MHWI::Native::FBlendEntry>& Blend);
    FName SelectRollMove() const;
    void RefreshMovement();
    void RefreshWeaponAttachment(float DeltaSeconds = 0.f);
    void SetSourceWeaponMotion(int32 MotionNo, float Position = 0.f);
    void AdvanceSourceWeaponEvents(float FromPosition, float NewPosition);
    void UpdateSourceWeaponPose(float DeltaSeconds);
    float EvaluateSourcePlayRate(float Position) const;
    void EnterSpecialSheathHold();
    void SetSpiritGauge(float NewValue);
    void ResetSpiritGaugeDecayClock();
    void SetSpiritLevel(int32 NewLevel, bool bPauseDecay = false);
    void CommitRoundslash();
    float SelectEvasionProtectionFrames() const;
    void ScheduleHelmShell(AActor* Target, const FVector& ContactLocation);
    void ScheduleIaiShell(AActor* Target, const FVector& ContactLocation);
    void TickDelayedShells(float DeltaSeconds);
    void EmitDelayedShell(const FMHWIDelayedHitRuntime& Hit, FName SourceMove);
    void ClearDelayedShells();

    /** Direction correction windows; values come from FMHWIMoveDefinition. */
    void ApplyTurnWindows(float FromPosition, float ToPosition);
    void TurnTowardYaw(float DesiredYaw, float MaxAngle, float DurationSeconds, float& AccumulatedDegrees);
    /** Data-driven Roll Light route (RequireDrawn) retained for a short recovery boundary. */
    void CaptureRollRecovery(const FMHWIMoveDefinition& Definition, const UAnimMontage* PlayedMontage);
    void ClearRollRecovery();
    bool CanUseRollRecovery() const;
    /** Snapshot/restore and per-stage motion for Rise/Air/Strike/Land. */
    void BeginAerialSnapshot();
    void RestoreAerialSnapshot();
    void ResetHelmChain();
    void ApplyStageMovement(FName MoveId, const FMHWIMoveDefinition& Definition);
    void ApplyHelmAirGravity();
    bool CanStartHelmStage(FName MoveId) const;
    void MaybeCommitHelmStrike();
    /** Applies HelmStrikeSpeed only once the Strike clip reaches its descent point. */
    void MaybeStartHelmDescent();
    void HandleHelmLanding();

    UFUNCTION() void HandleDeath();
    UFUNCTION() void HandleDamaged(float DamageAmount, AActor* DamageInstigator);
};
