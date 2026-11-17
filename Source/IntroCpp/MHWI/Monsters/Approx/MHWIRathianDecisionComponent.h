#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MHWIRathianDecisionPolicy.h"
#include "MHWIRathianDecisionComponent.generated.h"

class UMHWIRathianApproxMovesetData;
class UMHWIRathianApproxStatsData;
class UMHWIRathianApproxStateComponent;
class UMHWIRathianScriptedPolicy;

UCLASS(ClassGroup=(MHWI), meta=(BlueprintSpawnableComponent))
class INTROCPP_API UMHWIRathianDecisionComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UMHWIRathianDecisionComponent();
    void Configure(UMHWIRathianApproxMovesetData* InMoveset, UMHWIRathianApproxStatsData* InStats,
        UMHWIRathianApproxStateComponent* InState);
    void SetTarget(TWeakObjectPtr<AActor> InTarget) { Target = InTarget; }
    FMHWIRathianActionRequest Evaluate();
    void NotifyMoveFinished(const FString& RegistryName);
    void NotifyMoveRejected(const FString& RegistryName);
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx") float GetCooldownRemaining() const { return CooldownRemaining; }
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
private:
    bool IsMoveConfigured(const FMHWIRathianApproxMove& Move) const;
    UPROPERTY(Transient) TObjectPtr<UMHWIRathianApproxMovesetData> Moveset;
    UPROPERTY(Transient) TObjectPtr<UMHWIRathianApproxStatsData> Stats;
    UPROPERTY(Transient) TObjectPtr<UMHWIRathianApproxStateComponent> State;
    UPROPERTY(Transient) TObjectPtr<UMHWIRathianScriptedPolicy> Policy;
    TWeakObjectPtr<AActor> Target;
    TMap<FString, float> MoveCooldowns;
    float CooldownRemaining = 0.f;
    float LastMoveEndTime = 0.f;
    int32 ConsecutiveAttacks = 0;
    FString LastMoveName;
    float LastDecisionLogTime = -1.f;
};
