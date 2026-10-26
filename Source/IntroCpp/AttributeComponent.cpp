// Fill out your copyright notice in the Description page of Project Settings.

#include "AttributeComponent.h"
#include "GameFramework/Actor.h"
#include "IncomingDamageResponse.h"

// Sets default values
UAttributeComponent::UAttributeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	// 初始化属性默认值
	MaxHealth = 100.0f;
	CurrentHealth = MaxHealth;

	MaxMana = 50.0f;
	CurrentMana = MaxMana;
}

void UAttributeComponent::BeginPlay()
{
	Super::BeginPlay();

	// 确保当前值初始化为最大值
	CurrentHealth = MaxHealth;
	CurrentMana = MaxMana;
	bIsAlive = true;

	TimeSinceLastDamage = RegenDelayAfterDamage; // 初始就可以恢复
}

void UAttributeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bIsAlive) return;

	// 更新受伤计时器
	if (TimeSinceLastDamage < RegenDelayAfterDamage)
	{
		TimeSinceLastDamage += DeltaTime;
	}

	// 自然恢复HP
	if (HealthRegenPerSecond > 0.0f && TimeSinceLastDamage >= RegenDelayAfterDamage)
	{
		if (CurrentHealth < MaxHealth)
		{
			float RegenAmount = HealthRegenPerSecond * DeltaTime;
			float OldHealth = CurrentHealth;
			CurrentHealth = FMath::Clamp(CurrentHealth + RegenAmount, 0.0f, MaxHealth);
			
			if (OldHealth != CurrentHealth)
			{
				NotifyHealthChanged();
			}
		}
	}

	// 自然恢复MP
	if (ManaRegenPerSecond > 0.0f && TimeSinceLastDamage >= RegenDelayAfterDamage)
	{
		if (CurrentMana < MaxMana)
		{
			float RegenAmount = ManaRegenPerSecond * DeltaTime;
			float OldMana = CurrentMana;
			CurrentMana = FMath::Clamp(CurrentMana + RegenAmount, 0.0f, MaxMana);

			if (OldMana != CurrentMana)
			{
				NotifyManaChanged();
			}
		}
	}
}

void UAttributeComponent::ApplyDamage(float DamageAmount, AActor* Instigator)
{
	if (bIsAlive && DamageAmount > 0.0f)
	{
		AActor* DamageOwner = GetOwner();
		if (IsValid(DamageOwner) && DamageOwner->Implements<UIncomingDamageResponse>())
		{
			const bool bConsumed = IIncomingDamageResponse::Execute_InterceptIncomingDamage(DamageOwner, DamageAmount, Instigator);
			if (bConsumed || !IsValid(this) || !IsValid(DamageOwner) || !bIsAlive) return;
			float AdjustedDamage = DamageAmount;
			const bool bAdjusted = IIncomingDamageResponse::Execute_AdjustIncomingDamage(DamageOwner, DamageAmount, Instigator, AdjustedDamage);
			if (!IsValid(this) || !IsValid(DamageOwner) || !bIsAlive) return;
			if (bAdjusted && FMath::IsFinite(AdjustedDamage))
			{
				DamageAmount = FMath::Max(0.f, AdjustedDamage);
				if (DamageAmount <= 0.f) return;
			}
		}
	}
	if (!bIsAlive || !bCanDie && (CurrentHealth - DamageAmount <= 0)) return;

	float OldHealth = CurrentHealth;
	CurrentHealth = FMath::Clamp(CurrentHealth - DamageAmount, 0.0f, MaxHealth);

	// 重置受伤计时器（打断自然恢复）
	TimeSinceLastDamage = 0.0f;

	// 触发事件
	if (OldHealth != CurrentHealth)
	{
		NotifyHealthChanged();
	}

	// 检查死亡
	if (CurrentHealth <= 0.0f && bCanDie)
	{
		bIsAlive = false;
		OnCharacterDeath.Broadcast();

		UE_LOG(LogTemp, Log, TEXT("[AttributeComponent] %s 已死亡!"), *GetOwner()->GetName());
	}
	else if (DamageAmount > 0)
	{
		// ★ 存活时广播受击事件（触发受击音效/硬直/粒子等）
		OnDamaged.Broadcast(DamageAmount, Instigator);

		UE_LOG(LogTemp, Log, TEXT("[AttributeComponent] %s 受到 %.1f 点伤害，剩余HP: %.1f/%.1f"), 
			*GetOwner()->GetName(), DamageAmount, CurrentHealth, MaxHealth);
	}
}

void UAttributeComponent::ApplyHeal(float HealAmount)
{
	if (!bIsAlive) return;

	float OldHealth = CurrentHealth;
	CurrentHealth = FMath::Clamp(CurrentHealth + HealAmount, 0.0f, MaxHealth);

	if (OldHealth != CurrentHealth)
	{
		NotifyHealthChanged();
		UE_LOG(LogTemp, Log, TEXT("[AttributeComponent] %s 恢复 %.1f 点生命，当前HP: %.1f/%.1f"),
			*GetOwner()->GetName(), HealAmount, CurrentHealth, MaxHealth);
	}
}

void UAttributeComponent::UseMana(float ManaAmount)
{
	if (!bIsAlive) return;

	float OldMana = CurrentMana;
	CurrentMana = FMath::Clamp(CurrentMana - ManaAmount, 0.0f, MaxMana);

	if (OldMana != CurrentMana)
	{
		NotifyManaChanged();
		UE_LOG(LogTemp, Log, TEXT("[AttributeComponent] %s 消耗 %.1f 点魔法，当前MP: %.1f/%.1f"),
			*GetOwner()->GetName(), ManaAmount, CurrentMana, MaxMana);
	}
}

bool UAttributeComponent::TrySpendMana(float ManaAmount)
{
	if (!bIsAlive || !FMath::IsFinite(ManaAmount) || ManaAmount < 0.f || CurrentMana < ManaAmount) return false;
	UseMana(ManaAmount);
	return true;
}

void UAttributeComponent::RestoreMana(float ManaAmount)
{
	if (!bIsAlive) return;

	float OldMana = CurrentMana;
	CurrentMana = FMath::Clamp(CurrentMana + ManaAmount, 0.0f, MaxMana);

	if (OldMana != CurrentMana)
	{
		NotifyManaChanged();
		UE_LOG(LogTemp, Log, TEXT("[AttributeComponent] %s 恢复 %.1f 点魔法，当前MP: %.1f/%.1f"),
			*GetOwner()->GetName(), ManaAmount, CurrentMana, MaxMana);
	}
}

void UAttributeComponent::SetHealth(float NewHealth)
{
	float OldHealth = CurrentHealth;
	CurrentHealth = FMath::Clamp(NewHealth, 0.0f, MaxHealth);

	if (OldHealth != CurrentHealth)
	{
		NotifyHealthChanged();

		if (CurrentHealth <= 0.0f && bCanDie)
		{
			bIsAlive = false;
			OnCharacterDeath.Broadcast();
		}
	}
}

void UAttributeComponent::SetMana(float NewMana)
{
	float OldMana = CurrentMana;
	CurrentMana = FMath::Clamp(NewMana, 0.0f, MaxMana);

	if (OldMana != CurrentMana)
	{
		NotifyManaChanged();
	}
}

void UAttributeComponent::SetMaxHealth(float NewMaxHealth)
{
	MaxHealth = FMath::Max(0.0f, NewMaxHealth);
	
	// 如果当前HP超过新的最大值，截断
	if (CurrentHealth > MaxHealth)
	{
		CurrentHealth = MaxHealth;
	}
	
	NotifyHealthChanged();
}

void UAttributeComponent::SetMaxMana(float NewMaxMana)
{
	MaxMana = FMath::Max(0.0f, NewMaxMana);

	// 如果当前MP超过新的最大值，截断
	if (CurrentMana > MaxMana)
	{
		CurrentMana = MaxMana;
	}

	NotifyManaChanged();
}

float UAttributeComponent::GetHealthPercent() const
{
	if (MaxHealth <= 0.0f) return 0.0f;
	return CurrentHealth / MaxHealth;
}

float UAttributeComponent::GetManaPercent() const
{
	if (MaxMana <= 0.0f) return 0.0f;
	return CurrentMana / MaxMana;
}

void UAttributeComponent::BeginNotificationBatch()
{
    check(IsInGameThread());
    ++NotificationBatchDepth;
}

void UAttributeComponent::EndNotificationBatch()
{
    check(IsInGameThread());
    if (!ensure(NotificationBatchDepth > 0) || --NotificationBatchDepth != 0) return;
    const bool bHealth = bHealthNotificationPending;
    const bool bMana = bManaNotificationPending;
    bHealthNotificationPending = bManaNotificationPending = false;
    if (bHealth) OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
    if (bMana) OnManaChanged.Broadcast(CurrentMana, MaxMana);
}

void UAttributeComponent::NotifyHealthChanged()
{
    if (NotificationBatchDepth > 0) bHealthNotificationPending = true;
    else OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
}

void UAttributeComponent::NotifyManaChanged()
{
    if (NotificationBatchDepth > 0) bManaNotificationPending = true;
    else OnManaChanged.Broadcast(CurrentMana, MaxMana);
}
