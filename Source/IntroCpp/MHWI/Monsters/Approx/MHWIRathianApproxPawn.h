#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "MHWI/MHWIContactResponse.h"
#include "MHWIRathianApproxData.h"
#include "MHWIRathianApproxPawn.generated.h"

class USphereComponent;
class USkeletalMeshComponent;
class UAttributeComponent;
class UMHWIRathianApproxStateComponent;
class UMHWIRathianDecisionComponent;
class UAnimMontage;
class UAnimSequence;
class UTextRenderComponent;
class AMHWIRathianApproxFireball;
struct FMHWIRathianActionRequest;

UCLASS()
class INTROCPP_API AMHWIRathianApproxPawn : public APawn, public IMHWIContactResponse
{
    GENERATED_BODY()
public:
    AMHWIRathianApproxPawn();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<USphereComponent> HitProxy;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<USkeletalMeshComponent> Body;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<UAttributeComponent> Attributes;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<UMHWIRathianApproxStateComponent> ApproxState;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<UMHWIRathianDecisionComponent> Decision;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<UTextRenderComponent> HealthDisplay;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<UMHWIRathianApproxMovesetData> MovesetData;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Approx") TObjectPtr<UMHWIRathianApproxStatsData> StatsData;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Approx") TSoftObjectPtr<USkeletalMesh> BodyMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Approx", meta=(ClampMin="-500", ClampMax="500")) float BodyGroundOffsetCm = 0.f;

    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|Approx") void ConfigureApprox();
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|Approx") void SnapToGround();
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|Approx") void SetCombatTarget(AActor* NewTarget);
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|Approx") bool RequestBasicAttack(const FString& RegistryName);
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx") FString GetCurrentStateName() const;
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx") FString GetCurrentAttackName() const;
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx") int64 GetAttackRunId() const { return static_cast<int64>(CurrentRunId); }
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx") float GetHealthPercent() const;
    virtual void Tick(float DeltaSeconds) override;
    virtual EMHWIImpactSize GetMHWIImpactSize_Implementation() const override;
    virtual bool DeflectsMHWIWeapon_Implementation(AActor* Attacker) const override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
private:
    enum class EExecState : uint8 { Patrol, Approach, Turn, Attack, Landing, Dead };
    UFUNCTION() void HandleDeath();
    void Dispatch(const FMHWIRathianActionRequest& Request);
    void TickPatrol(float DeltaSeconds);
    void TickCombat(float DeltaSeconds);
    void TickAttack(float DeltaSeconds);
    void TickEmergencyLanding(float DeltaSeconds);
    void BeginEmergencyLanding();
    void TickDisplay(float DeltaSeconds);
    void FinishMove();
    void StartPhase(int32 PhaseIndex);
    void AdvancePhase();
    void ApplyAttackWindow(float PreviousPosition, float CurrentPosition);
    void MoveSwept(FVector Delta, float DeltaSeconds);
    void FaceTarget(AActor* Target, float DeltaSeconds, float RateDegPerSecond);
    void KeepOnGround();
    void TickFlightPhase(float NormalizedPosition, float DeltaSeconds);
    bool SetFlightHeightSwept(float TargetZ);
    bool HasAttackLineOfSight(AActor* Target, const FVector& BoxOrigin) const;
    void SpawnFireball(const FMHWIRathianAttackPhase& Phase);
    UAnimMontage* GetOrBuildMontage(UAnimSequence* Sequence, float BlendIn, float BlendOut);
    AActor* FindOrAcquireTarget();
    bool HasLineOfSight(AActor* Target) const;
    const FMHWIRathianApproxMove* FindMove(const FString& RegistryName) const;
    bool IsMoveConfigured(const FMHWIRathianApproxMove& Move) const;
    void UpdateLocomotionBlend(float SpeedCmPerSecond);

    UPROPERTY(Transient) TObjectPtr<UAnimSequence> ActiveSequence;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> ActiveMontage;
    UPROPERTY(Transient) TObjectPtr<const UMHWIRathianApproxStatsData> ActiveStats;
    UPROPERTY(Transient) TMap<FString, TObjectPtr<UAnimMontage>> RuntimeMontages;
    UPROPERTY(Transient) TArray<TObjectPtr<AMHWIRathianApproxFireball>> OwnerProjectiles;
    TWeakObjectPtr<AActor> CombatTarget;
    TWeakObjectPtr<AActor> ForcedTarget;
    TArray<FTransform> PreviousBoxTransforms;
    TSet<TWeakObjectPtr<AActor>> PhaseHitActors;
    FMHWIRathianApproxMove ActiveMove;
    int32 ActivePhaseIndex = INDEX_NONE;
    EExecState ExecState = EExecState::Patrol;
    uint64 CurrentRunId = 0;
    FVector PatrolOrigin = FVector::ZeroVector;
    FVector PatrolGoal = FVector::ZeroVector;
    float StateElapsed = 0.f;
    float PhasePreviousPosition = 0.f;
    float FlightGroundZ = 0.f;
    float FlightStartZ = 0.f;
    float DisplayAccumulator = 0.f;
    float CurrentMovementSpeed = 0.f;
    bool bConfigured = false;
    bool bAttributesInitialized = false;
    bool bPhaseFacingLocked = false;
    bool bSpawnedProjectileThisPhase = false;
    bool bHasPreviousBoxSamples = false;
    bool bFlightActive = false;
    bool bFlightBlocked = false;
    bool bEmergencyLanding = false;
    bool bPhaseMontageEnded = false;
    bool bPhaseMontageInterrupted = false;
    bool bPhaseBlendOutStarted = false;
    bool bPhaseBlendOutInterrupted = false;
    uint64 ActivePhaseEpoch = 0;
    int32 ActiveMontageInstanceId = INDEX_NONE;
    bool bDeathHandled = false;
};
