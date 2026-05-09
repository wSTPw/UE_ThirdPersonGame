// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AttributeComponent.generated.h"

// 属性变化委托：当前值, 最大值
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnAttributeChanged, float, CurrentValue, float, MaxValue);

// 死亡委托
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCharacterDeath);


UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class INTROCPP_API UAttributeComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	UAttributeComponent();

protected:
	virtual void BeginPlay() override;

public:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// ==========================================
	// 基础属性（蓝图可编辑）
	// ==========================================

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attributes|Health")
	float MaxHealth = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Attributes|Health")
	float CurrentHealth;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attributes|Mana")
	float MaxMana = 50.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Attributes|Mana")
	float CurrentMana;

	// ==========================================
	// 恢复设置（蓝图可编辑）
	// ==========================================

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attributes|Regeneration")
	float HealthRegenPerSecond = 0.0f;  // 每秒恢复HP（0表示不自动恢复）

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attributes|Regeneration")
	float ManaRegenPerSecond = 2.0f;   // 每秒恢复MP

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attributes|Regeneration")
	float RegenDelayAfterDamage = 3.0f; // 受伤后延迟多少秒开始恢复

	// ==========================================
	// 状态标记
	// ==========================================

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Attributes|State")
	bool bIsAlive = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attributes|State")
	bool bCanDie = true;

	// ==========================================
	// 事件委托（蓝图可绑定）
	// ==========================================

	UPROPERTY(BlueprintAssignable, Category = "Attributes|Events")
	FOnAttributeChanged OnHealthChanged;

	UPROPERTY(BlueprintAssignable, Category = "Attributes|Events")
	FOnAttributeChanged OnManaChanged;

	UPROPERTY(BlueprintAssignable, Category = "Attributes|Events")
	FOnCharacterDeath OnCharacterDeath;

public:
	// ==========================================
	// 修改属性接口
	// ==========================================

	// 受到伤害（负数=受伤）
	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void ApplyDamage(float DamageAmount, AActor* Instigator = nullptr);

	// 治疗生命值（正数=回血）
	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void ApplyHeal(float HealAmount);

	// 消耗魔法值（负数=消耗）
	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void UseMana(float ManaAmount);

	// 恢复魔法值（正数=回复）
	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void RestoreMana(float ManaAmount);

	// 直接设置属性值
	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void SetHealth(float NewHealth);

	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void SetMana(float NewMana);

	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void SetMaxHealth(float NewMaxHealth);

	UFUNCTION(BlueprintCallable, Category = "Attributes")
	void SetMaxMana(float NewMaxMana);

	// ==========================================
	// 查询接口
	// ==========================================

	// 获取HP百分比 (0.0 ~ 1.0)
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetHealthPercent() const;

	// 获取MP百分比 (0.0 ~ 1.0)
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetManaPercent() const;

	// 是否存活
	UFUNCTION(BlueprintPure, Category = "Attributes")
	bool IsAlive() const { return bIsAlive; }

	// HP是否满
	UFUNCTION(BlueprintPure, Category = "Attributes")
	bool IsFullHealth() const { return CurrentHealth >= MaxHealth; }

	// MP是否满
	UFUNCTION(BlueprintPure, Category = "Attributes")
	bool IsFullMana() const { return CurrentMana >= MaxMana; }

	// 获取当前HP
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetCurrentHealth() const { return CurrentHealth; }

	// 获取最大HP
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetMaxHealth() const { return MaxHealth; }

	// 获取当前MP
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetCurrentMana() const { return CurrentMana; }

	// 获取最大MP
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetMaxMana() const { return MaxMana; }

private:
	// 受伤计时器
	float TimeSinceLastDamage = 0.0f;
};
