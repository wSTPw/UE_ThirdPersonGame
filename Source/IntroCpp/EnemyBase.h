// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "EnemyData.h"
#include "AttributeComponent.h"
#include "EnemyBase.generated.h"

class UAnimMontage;
class USoundBase;

/**
 * 近战敌人基类
 *
 * 继承自 ACharacter，挂载 UAttributeComponent 实现生命值管理。
 * 通过 EnemyData (PrimaryDataAsset) 数据驱动所有行为参数。
 * 攻击采用 AnimNotify 精确帧触发模式（与火球攻击/物品使用同一套方案）。
 *
 * 子类化方式:
 *   - C++ 继承: class ASlimeEnemy : public AEnemyBase { ... };
 *   - 蓝图继承: 创建 BP_Enemy_Slime 基于 AEnemyBase
 */
UCLASS(Abstract, Blueprintable)
class INTROCPP_API AEnemyBase : public ACharacter
{
	GENERATED_BODY()

public:

	// ====== 构造函数 / 生命周期 ======
	AEnemyBase();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

protected:

	// ====== 组件声明（对齐 MyPlayerCharacter 的组织方式）======

	/** 属性组件（HP/MP/死亡系统）— 与玩家共享同一个组件类！ */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UAttributeComponent* AttributeComp;

	/** 攻击检测起始点组件（类似玩家的 Socket） */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USceneComponent* AttackOrigin;


public:

	// ====== 数据驱动配置（蓝图中指定具体的 EnemyData 资产）======

	/**
	 * 此敌人的数值配置数据资产。
	 * 在蓝图子类的 Defaults 中拖入对应的 DA_Enemy_xxx 资产。
	 * BeginPlay 时自动读取并初始化所有参数。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
	UEnemyData* EnemyData;


	// ====== AI 状态查询接口（BlueprintCallable，给 AIController 调用）======

	/** 设置当前追踪的目标 Actor（通常是玩家） */
	UFUNCTION(BlueprintCallable, Category = "AI")
	void SetTargetActor(AActor* Target);

	/** 清除当前目标 */
	UFUNCTION(BlueprintCallable, Category = "AI")
	void ClearTargetActor();

	/** 获取当前目标 */
	UFUNCTION(BlueprintPure, Category = "AI")
	AActor* GetTargetActor() const { return TargetActor; }

	/** 目标是否在指定距离内 */
	UFUNCTION(BlueprintPure, Category = "AI")
	bool IsTargetInRange(float Range) const;

	/** 是否存活 */
	UFUNCTION(BlueprintPure, Category = "AI")
	bool IsAlive() const;

	/** 是否正在执行攻击动作 */
	UFUNCTION(BlueprintPure, Category = "AI")
	bool IsAttacking() const { return bIsAttacking; }

	/** 是否正在执行死亡流程 */
	UFUNCTION(BlueprintPure, Category = "AI")
	bool IsDead() const { return bIsDead; }


	// ====== 行为接口 ======

	/**
	 * 执行攻击动作
	 *
	 * 流程（与 UseHeldItem/Attack 同一模式）：
	 * 1. 检查冷却/条件
	 * 2. 设置 bIsAttacking = true
	 * 3. PlayAnimMontage(AttackMontage)
	 * 4. 等待 AnimNotify_EnemyAttack 触发 → OnAttackAnimNotify()
	 * 5. Montage 结束回调重置 bIsAttacking
	 */
	UFUNCTION(BlueprintCallable, Category = "Combat")
	void PerformAttack();

	/**
	 * AnimNotify 攻击帧回调入口
	 * 由 AnimNotify_EnemyAttack::Notify() 在动画精确帧调用。
	 * 在此处执行实际的伤害检测（SphereTrace）。
	 */
	void OnAttackAnimNotify();

	/** 死亡处理 */
	UFUNCTION(BlueprintCallable, Category = "Combat")
	void Die();

	/** 受击处理（被玩家攻击时由 AttributeComponent.OnDamaged 委托自动调用） */
	UFUNCTION(BlueprintCallable, Category = "Combat")
	void OnReceiveDamage(float DamageAmount, AActor* DamageCauser);


	// ====== 蓝图扩展点（蓝图子类中覆写以添加 VFX/Sound/掉落物等）======

	/**
	 * 攻击命中时的蓝图扩展点
	 * 在 SphereTrace 命中目标后调用，蓝图中可添加命中特效、音效等
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Combat", meta = (DisplayName = "On Attack Hit"))
	void BP_OnEnemyAttackHit(const FHitResult& HitResult);

	/**
	 * 死亡时的蓝图扩展点
	 * 在 Die() 中调用，蓝图中可添加死亡特效、掉落物生成等
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Combat", meta = (DisplayName = "On Death"))
	void BP_OnEnemyDeath();


protected:

	// ====== 核心攻击检测逻辑 ======

	/**
	 * 执行近战伤害检测
	 *
	 * 方式: SphereTrace（球体扫描）
	 * 流程:
	 *   1. 从 AttackOrigin 或 GetActorLocation 发出 SphereTrace
	 *   2. 方向 = GetActorForwardVector()
	 *   3. 忽略自己
	 *   4. 如果命中 Actor 且有 UAttributeComponent → ApplyDamage
	 *
	 * ★★★ 与火球 ProcessHit 完全相同的伤害调用方式 ★★★
	 */
	void ExecuteMeleeDamage();

	/** 应用 EnemyData 中的属性初始化角色（速度、碰撞等） */
	void ApplyEnemyDataSettings();

	/** 应用外观设置（Mesh/Material/Scale） */
	void ApplyAppearanceFromData();

private:

	// ====== 内部状态（不加 UPROPERTY，纯 C++ 管理）======

	/** 当前追踪的目标（通常由 AIController 设置） */
	AActor* TargetActor = nullptr;

	/** 是否正在攻击动画中 */
	bool bIsAttacking = false;

	/** 是否已死亡 */
	bool bIsDead = false;

	/** 上次攻击时间戳（用于冷却判断） */
	float LastAttackTime = 0.f;

	/** 死亡后销毁倒计时 */
	float DeathDestroyTimer = 0.f;

	/** 死亡后多久销毁（秒） */
	static constexpr float DEATH_DESTROY_DELAY = 3.f;

protected:

	// ====== 委托绑定方法 ======

	UFUNCTION()
	void OnHealthChanged(float CurrentHP, float MaxHP);

	UFUNCTION()
	void OnDeathDelegate();

	/** Montage 播放结束回调 — 重置 bIsAttacking 状态 */
	UFUNCTION()
	void OnAttackMontageEnded(UAnimMontage* Montage, bool bInterrupted);
};
