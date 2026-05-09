// Fill out your copyright notice in the Description page of Project Settings.

#include "AttributeComponent.h"
#include "GameFramework/Actor.h"

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
				OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
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
				OnManaChanged.Broadcast(CurrentMana, MaxMana);
			}
		}
	}
}

void UAttributeComponent::ApplyDamage(float DamageAmount, AActor* Instigator)
{
	if (!bIsAlive || !bCanDie && (CurrentHealth - DamageAmount <= 0)) return;

	float OldHealth = CurrentHealth;
	CurrentHealth = FMath::Clamp(CurrentHealth - DamageAmount, 0.0f, MaxHealth);

	// 重置受伤计时器（打断自然恢复）
	TimeSinceLastDamage = 0.0f;

	// 触发事件
	if (OldHealth != CurrentHealth)
	{
		OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
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
		OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
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
		OnManaChanged.Broadcast(CurrentMana, MaxMana);
		UE_LOG(LogTemp, Log, TEXT("[AttributeComponent] %s 消耗 %.1f 点魔法，当前MP: %.1f/%.1f"),
			*GetOwner()->GetName(), ManaAmount, CurrentMana, MaxMana);
	}
}

void UAttributeComponent::RestoreMana(float ManaAmount)
{
	if (!bIsAlive) return;

	float OldMana = CurrentMana;
	CurrentMana = FMath::Clamp(CurrentMana + ManaAmount, 0.0f, MaxMana);

	if (OldMana != CurrentMana)
	{
		OnManaChanged.Broadcast(CurrentMana, MaxMana);
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
		OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);

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
		OnManaChanged.Broadcast(CurrentMana, MaxMana);
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
	
	OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
}

void UAttributeComponent::SetMaxMana(float NewMaxMana)
{
	MaxMana = FMath::Max(0.0f, NewMaxMana);

	// 如果当前MP超过新的最大值，截断
	if (CurrentMana > MaxMana)
	{
		CurrentMana = MaxMana;
	}

	OnManaChanged.Broadcast(CurrentMana, MaxMana);
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
