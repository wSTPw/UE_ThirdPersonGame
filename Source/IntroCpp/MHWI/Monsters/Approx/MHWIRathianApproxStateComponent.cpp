#include "MHWIRathianApproxStateComponent.h"
#include "AttributeComponent.h"

UMHWIRathianApproxStateComponent::UMHWIRathianApproxStateComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.1f; // 怒态计时 0.1s 粒度足够
}

void UMHWIRathianApproxStateComponent::Configure(UMHWIRathianApproxStatsData* InStats)
{
    Stats = InStats;
    RageBuildup = 0.f;
    RageRemainingSeconds = 0.f;
    const bool bWasInRage = bInRage;
    bInRage = false;
    if (bWasInRage)
    {
        OnRageChanged.Broadcast(false);
    }
}

void UMHWIRathianApproxStateComponent::BindAttributes(UAttributeComponent* InAttributes)
{
    if (BoundAttributes)
    {
        BoundAttributes->OnDamaged.RemoveAll(this);
        BoundAttributes->OnCharacterDeath.RemoveAll(this);
    }
    BoundAttributes = InAttributes;
    if (BoundAttributes)
    {
        BoundAttributes->OnDamaged.AddDynamic(this, &UMHWIRathianApproxStateComponent::HandleDamaged);
        BoundAttributes->OnCharacterDeath.AddDynamic(this, &UMHWIRathianApproxStateComponent::HandleDeath);
    }
}

void UMHWIRathianApproxStateComponent::HandleDamaged(float DamageAmount, AActor* /*DamageInstigator*/)
{
    // 近似消费：受击伤害 1:1 累积发怒值（原作逐招累积未闭合，NUM/BEH 缺口）。
    const float Amount = FMath::Abs(DamageAmount);
    RageBuildup += Amount * (Stats ? Stats->RageBuildupPerDamagePoint : 1.f);
    const float Threshold = Stats ? Stats->RageBuildToTrigger : 600.f;
    if (!bInRage && RageBuildup >= Threshold)
    {
        bInRage = true;
        RageRemainingSeconds = Stats ? Stats->RageDurationSeconds : 80.f;
        UE_LOG(LogTemp, Log, TEXT("[RathianApprox] Rage ON buildup=%.1f"), RageBuildup);
        OnRageChanged.Broadcast(true);
    }
}

void UMHWIRathianApproxStateComponent::HandleDeath()
{
    bInRage = false;
    OnRageChanged.Broadcast(false);
}

void UMHWIRathianApproxStateComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (bInRage)
    {
        RageRemainingSeconds -= DeltaTime;
        if (RageRemainingSeconds <= 0.f)
        {
            bInRage = false;
            RageBuildup = 0.f; // 怒结束清零；原作衰减规则未闭合（近似消费）。
            UE_LOG(LogTemp, Log, TEXT("[RathianApprox] Rage OFF"));
            OnRageChanged.Broadcast(false);
        }
    }
}

float UMHWIRathianApproxStateComponent::GetDamageMultiplier() const
{
    return (bInRage && Stats) ? Stats->RageDamageModifier : 1.f;
}

float UMHWIRathianApproxStateComponent::GetSpeedMultiplier() const
{
    return (bInRage && Stats) ? Stats->RageSpeedModifier : 1.f;
}
