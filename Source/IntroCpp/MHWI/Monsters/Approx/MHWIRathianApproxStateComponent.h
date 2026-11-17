#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MHWIRathianApproxData.h"
#include "MHWIRathianApproxStateComponent.generated.h"

class UAttributeComponent;
class UMHWIRathianApproxStatsData;

/**
 * B1 怒/疲劳/耐力状态宿主（approximated-consumption）。
 * 已证字面值：发怒阈值 600/持续 80s/伤害×1.15/速度×1.05（dtt_agr）。
 * 近似消费：受击伤害 1:1 累积发怒值；疲劳/耐力 v1 未实现（显式缺席）。
 */
UCLASS(ClassGroup=(MHWI), meta=(BlueprintSpawnableComponent))
class INTROCPP_API UMHWIRathianApproxStateComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UMHWIRathianApproxStateComponent();

    void Configure(UMHWIRathianApproxStatsData* InStats);
    /** 绑定目标 Attribute 的 OnDamaged/OnCharacterDeath（动态委托，UFUNCTION 目标）。 */
    void BindAttributes(UAttributeComponent* InAttributes);

    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx")
    bool IsInRage() const { return bInRage; }
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx")
    float GetRageBuildup() const { return RageBuildup; }
    /** 发怒伤害/速度乘数（不在怒态时返回 1）。 */
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx")
    float GetDamageMultiplier() const;
    UFUNCTION(BlueprintPure, Category="MHWI|Rathian|Approx")
    float GetSpeedMultiplier() const;

    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    /** 怒态进入/结束（日志与调试用）。 */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRageChanged, bool, bNowInRage);
    UPROPERTY(BlueprintAssignable) FOnRageChanged OnRageChanged;

private:
    UFUNCTION()
    void HandleDamaged(float DamageAmount, AActor* DamageInstigator);
    UFUNCTION()
    void HandleDeath();

    UPROPERTY(Transient) TObjectPtr<UMHWIRathianApproxStatsData> Stats;
    UPROPERTY(Transient) TObjectPtr<UAttributeComponent> BoundAttributes;
    float RageBuildup = 0.f;
    float RageRemainingSeconds = 0.f;
    bool bInRage = false;
};
