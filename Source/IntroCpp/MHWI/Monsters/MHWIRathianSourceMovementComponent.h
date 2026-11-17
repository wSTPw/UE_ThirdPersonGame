#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PawnMovementComponent.h"
#include "MHWIRathianSourceMovementComponent.generated.h"

/** Provenance is per semantic dimension; loading bytes is not native equivalence. */
UENUM(BlueprintType)
enum class EMHWIRathianMotionQualification : uint8
{
    Unverified,
    EngineeringAdapter,
    StaticSourceVerified,
    NativeConsumerVerified,
    RuntimeCompared
};

UENUM(BlueprintType)
enum class EMHWIRathianSourceTimeUnit : uint8
{
    Unspecified,
    NativeFrames,
    Seconds,
    NativeTicks
};

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianSourceMotionSample
{
    GENERATED_BODY()

    /** Absolute time in the explicitly declared source unit, not implicit UE seconds. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) double SourceTime = 0.0;
    /** Qualified root pose in UE local axes and centimeters; scale must be identity. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform LocalRootTransform = FTransform::Identity;
};

USTRUCT(BlueprintType)
struct INTROCPP_API FMHWIRathianQualifiedSourceMotion
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString SourceSha256;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString MotionBank;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 MotionSlot = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 NativeActionId = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString EvidencePath;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString TimeBasis;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString CoordinateBasis;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EMHWIRathianSourceTimeUnit TimeUnit = EMHWIRathianSourceTimeUnit::Unspecified;
    /** Zero explicitly means the conversion to wall-clock seconds remains unknown. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) double UnitsPerSecond = 0.0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EMHWIRathianMotionQualification MotionBindingQualification = EMHWIRathianMotionQualification::Unverified;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EMHWIRathianMotionQualification TimeBasisQualification = EMHWIRathianMotionQualification::Unverified;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EMHWIRathianMotionQualification CoordinateBasisQualification = EMHWIRathianMotionQualification::Unverified;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EMHWIRathianMotionQualification RootTrackQualification = EMHWIRathianMotionQualification::Unverified;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FMHWIRathianSourceMotionSample> Samples;
};

UENUM(BlueprintType)
enum class EMHWIRathianSourceMoveResult : uint8
{
    None,
    Applied,
    ReachedEnd,
    Blocked,
    Unconfigured,
    Unqualified,
    InvalidOwner,
    StaleAction,
    InvalidTime,
    ReversedTime,
    ReentrantCall,
    InvalidSample
};

/**
 * Explicit source-track adapter. The owning Pawn advances its source clock.
 * No autonomous tick, gravity, navigation, warping, or guessed source frame rate.
 * SafeMove sweeps the UpdatedComponent only; it is not a monster attack shape.
 */
UCLASS(ClassGroup=(MHWI), meta=(BlueprintSpawnableComponent))
class INTROCPP_API UMHWIRathianSourceMovementComponent : public UPawnMovementComponent
{
    GENERATED_BODY()

public:
    UMHWIRathianSourceMovementComponent();

    /** Strict mode refuses dimensions without native consumer evidence. */
    bool ConfigureQualifiedMotion(const FMHWIRathianQualifiedSourceMotion& InMotion,
        bool bRequireSourceSemantics, FString& OutReason);

    /** ActionRunId must be nonzero and strictly newer than previous runs. */
    bool BeginSourceMotion(uint64 ActionRunId, FString* OutReason = nullptr);

    /**
     * Consumes every crossed sample interval, including a large caller step.
     * Blocking invalidates this movement run; caller decides action termination.
     * False may include a partial physical movement; inspect OutHit/last result.
     */
    bool AdvanceToSourceTime(uint64 ActionRunId, double AbsoluteSourceTime,
        FHitResult& OutHit, FString* OutReason = nullptr);

    /** Only the matching action may revoke its movement permission. */
    void CancelSourceMotion(uint64 ActionRunId);

    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|SourceMotion")
    bool IsSourceMotionActive() const { return bMotionActive; }
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|SourceMotion")
    bool HasSourceMotionFinished() const { return bMotionFinished; }
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|SourceMotion")
    bool IsSourceSemanticsQualified() const { return bSourceSemanticsQualified; }
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|SourceMotion")
    double GetLastSourceTime() const { return LastSourceTime; }
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|SourceMotion")
    EMHWIRathianSourceMoveResult GetLastMoveResult() const { return LastMoveResult; }

    uint64 GetActionRunId() const { return ActiveActionRunId; }
    const FMHWIRathianQualifiedSourceMotion& GetQualifiedMotion() const { return QualifiedMotion; }

protected:
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UPROPERTY(Transient) FMHWIRathianQualifiedSourceMotion QualifiedMotion;

    FTransform MotionOrigin = FTransform::Identity;
    uint64 ActiveActionRunId = 0;
    uint64 LastStartedActionRunId = 0;
    double LastSourceTime = 0.0;
    bool bConfigured = false;
    bool bSourceSemanticsQualified = false;
    bool bMotionActive = false;
    bool bMotionFinished = false;
    bool bAdvancingSource = false;
    EMHWIRathianSourceMoveResult LastMoveResult = EMHWIRathianSourceMoveResult::None;

    FTransform SampleRoot(double SourceTime) const;
    bool Fail(EMHWIRathianSourceMoveResult Result, const TCHAR* Reason, FString* OutReason);
};
