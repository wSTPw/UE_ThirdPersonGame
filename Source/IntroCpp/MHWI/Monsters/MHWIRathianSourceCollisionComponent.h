#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/HitResult.h"
#include "MHWIRathianSourceCollisionComponent.generated.h"

class USkeletalMeshComponent;

/** Geometric observation only. Native damage and re-hit permission are independent. */
USTRUCT()
struct INTROCPP_API FMHWIRathianSourceContact
{
    GENERATED_BODY()

    UPROPERTY() uint64 ActionRunId = 0;
    UPROPERTY() int32 NativeActionId = INDEX_NONE;
    UPROPERTY() int32 TimelineUid = INDEX_NONE;
    UPROPERTY() int32 AttackIndex = INDEX_NONE;
    UPROPERTY() int32 GeometryIndex = INDEX_NONE;
    UPROPERTY() int32 InnerGeometryIndex = INDEX_NONE;
    UPROPERTY() double SourceTime = 0.0;
    UPROPERTY() TWeakObjectPtr<AActor> Target;
    UPROPERTY() FHitResult Hit;
    UPROPERTY() bool bCurrentPoseOverlap = false;
    UPROPERTY() bool bEngineeringEvidenceMode = false;
    UPROPERTY() bool bConservativeQueryCandidate = false;
    UPROPERTY() bool bNativeRehitQualified = false;
    UPROPERTY() bool bNativeDamageQualified = false;
};

/** Non-ticking adapter: the owning source clock supplies evaluated mesh poses. */
UCLASS(ClassGroup=(MHWI), meta=(BlueprintSpawnableComponent))
class INTROCPP_API UMHWIRathianSourceCollisionComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UMHWIRathianSourceCollisionComponent();

    /** Loads the extractor report. Unqualified native clock/basis/action data is rejected. */
    bool ConfigureFromEvidence(USkeletalMeshComponent* InMesh, const FString& JsonPath, FString& OutError);
    bool ConfigureFromEvidenceJson(USkeletalMeshComponent* InMesh, const FString& JsonText,
        bool bStrict, FString& OutError);
    bool BeginAction(uint64 InRunId, int32 InNativeActionId);
    /** Call after evaluating InMesh at CurrentSourceTime. Split at GetSourceBoundaries(). */
    bool AdvanceSourceInterval(uint64 InRunId, double PreviousSourceTime,
        double CurrentSourceTime, TArray<FMHWIRathianSourceContact>& OutContacts);
    void EndAction(uint64 InRunId);
    void GetSourceBoundaries(TArray<double>& OutTimes) const;
    bool IsConfigured() const { return bConfigured; }
    const FString& GetLastFailure() const { return LastFailure; }

protected:
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    struct FSourceCapsule
    {
        FName Bone0;
        FName Bone1;
        FVector Offset0 = FVector::ZeroVector;
        FVector Offset1 = FVector::ZeroVector;
        double Radius = 0.0;
        int32 InnerIndex = INDEX_NONE;
    };
    struct FWorldCapsule
    {
        FVector Point0 = FVector::ZeroVector;
        FVector Point1 = FVector::ZeroVector;
        double Radius = 0.0;
    };

    bool CapturePose(TArray<FWorldCapsule>& OutPose);
    bool Fail(const FString& Reason);
    void ClearConfiguration();

    UPROPERTY(Transient) TWeakObjectPtr<USkeletalMeshComponent> SourceMesh;
    TArray<FSourceCapsule> Capsules;
    TArray<FWorldCapsule> PreviousPose;
    FString LastFailure;
    FString TimeUnit;
    double UnitsPerSecond = 0.0;
    double WindowStart = 0.0;
    double WindowEnd = 0.0;
    double LastSourceTime = 0.0;
    uint64 ActiveRunId = 0;
    int32 NativeActionId = INDEX_NONE;
    int32 TimelineUid = INDEX_NONE;
    int32 AttackIndex = INDEX_NONE;
    int32 GeometryIndex = INDEX_NONE;
    bool bConfigured = false;
    bool bStrictNative = true;
    bool bRehitQualified = false;
    bool bDamageQualified = false;
};