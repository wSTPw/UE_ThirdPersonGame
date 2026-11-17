#pragma once
#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "MHWIRathianDecisionPolicy.h"
#include "MHWIRathianScriptedPolicy.generated.h"

UCLASS()
class INTROCPP_API UMHWIRathianScriptedPolicy : public UObject, public IMHWIRathianDecisionPolicy
{
    GENERATED_BODY()
public:
    virtual FMHWIRathianActionRequest EvaluatePolicy(const FMHWIRathianDecisionContext& Context,
        const TArray<FMHWIRathianApproxMove>& QualifiedMoves) const override;
};
