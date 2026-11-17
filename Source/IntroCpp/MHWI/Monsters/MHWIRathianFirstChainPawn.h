#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "MHWIRathianThkExecutor.h"
#include "MHWIRathianSourceCollisionComponent.h"
#include "MHWIRathianFirstChainPawn.generated.h"

class USceneComponent;
class USkeletalMeshComponent;
class UMHWIRathianFirstChainData;
class UMHWIRathianSourceMovementComponent;

/** Isolated source-chain runner. No automatic AI, guessed clock, or raw-MV damage. */
UCLASS()
class INTROCPP_API AMHWIRathianFirstChainPawn : public APawn
{
    GENERATED_BODY()
public:
    AMHWIRathianFirstChainPawn();
    virtual UPawnMovementComponent* GetMovementComponent() const override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="SourceChain") TObjectPtr<USceneComponent> SourceRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="SourceChain") TObjectPtr<USkeletalMeshComponent> Body;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="SourceChain") TObjectPtr<UMHWIRathianSourceMovementComponent> SourceMovement;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="SourceChain") TObjectPtr<UMHWIRathianSourceCollisionComponent> SourceCollision;

    /** Engineering mode is explicit and never certifies native semantics. */
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|SourceChain")
    bool ConfigureChain(UMHWIRathianFirstChainData* Data, bool bEngineeringEvidenceMode = false);
    /** Test-only input: strict execution refuses these unqualified native replies. */
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|SourceChain")
    void SetEngineeringCondition(int32 FunctionType, int32 Parameter1, int32 Parameter2, bool Value);
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|SourceChain")
    bool StartSourceDecision();
    /** Absolute source domain, not seconds. The runner has no automatic source clock. */
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|SourceChain")
    bool AdvanceSourceTime(double AbsoluteSourceTime);
    UFUNCTION(BlueprintCallable, Category="MHWI|Rathian|SourceChain")
    void CancelSourceAction();
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|SourceChain")
    FString GetChainSnapshotJson() const;

protected:
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UPROPERTY(Transient) TObjectPtr<UMHWIRathianFirstChainData> ChainData;
    FMHWIRathianThkProgram Program;
    FMHWIRathianThkExecutor Thk;
    FMHWIRathianThkDecision LastDecision;
    TMap<FString, FMHWIRathianThkQueryResult> EngineeringConditions;
    TArray<FMHWIRathianSourceContact> ContactObservations;
    uint64 LastIssuedRunId = 0;
    uint64 CurrentRunId = 0;
    double CurrentSourceTime = 0.0;
    bool bConfigured = false;
    bool bActive = false;
    bool bEngineeringMode = false;
    bool bAdvancing = false;
    bool bCompleted = false;
    FString LastFailure;

    bool ReadProgram(const FString& Json, FString& OutReason);
    bool EvaluateSourcePose(double SourceTime);
    bool Fail(const FString& Reason);
};
