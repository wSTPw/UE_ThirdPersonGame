#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MHWIRathianSourceMovementComponent.h"
#include "MHWIRathianFirstChainData.generated.h"

class USkeletalMesh;
class UAnimSequence;

/**
 * Generated source snapshot and asset references for one qualified source chain.
 * Original binary provenance remains in the parsers' pinned evidence manifests.
 */
UCLASS(BlueprintType)
class INTROCPP_API UMHWIRathianFirstChainData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Source") FString SourceProfile;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Source") FString EvidencePinsJson;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Source") FString ThkProgramJson;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Source") FString CollisionEvidenceJson;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Source") FMHWIRathianQualifiedSourceMotion SourceMotion;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Presentation") TSoftObjectPtr<USkeletalMesh> BodyMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Presentation") TSoftObjectPtr<UAnimSequence> InPlaceSequence;
    /** Native source domain -> imported sequence seconds. This is an asset mapping, not the native clock. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Presentation") double SequenceSecondsPerSourceUnit = 0.0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Qualification") bool bRequireSourceSemantics = true;
};
