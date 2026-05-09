// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFireballProjectile.generated.h"

class USphereComponent;
class UProjectileMovementComponent;
class UParticleSystemComponent;
class UPointLightComponent;
class USoundBase;
class UParticleSystem;

/**
 * 火球抛射体 - 完全自包含的飞行物
 * 
 * 架构设计：
 *   所有特效资产定义在本类中（蓝图子类赋值）
 *   发射者只需 SpawnActor，无需关心任何特效逻辑
 *   无论从角色、发射器、还是其他 Actor 发射，效果一致
 *   
 * 特效生命周期（全自动）：
 *   [Spawn] → BeginPlay() → 激活飞行组件（粒子+光源+音效）
 *   [Flight] → Tick          → 飞行中持续显示
 *   [Hit]   → ProcessHit()   → 关闭飞行组件 + 播放击中特效 + 延迟销毁
 */
UCLASS()
class INTROCPP_API AAFireballProjectile : public AActor
{
	GENERATED_BODY()

public:
	AAFireballProjectile();

protected:
	virtual void BeginPlay() override;

public:
	virtual void Tick(float DeltaTime) override;

	// ==========================================
	// 基础组件
	// ==========================================

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USphereComponent* CollisionComp;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UProjectileMovementComponent* ProjectileMovement;

	// ==========================================
	// 战斗属性（蓝图可编辑）
	// ==========================================

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat")
	float Damage = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat", meta = (ClampMin = 100.0f))
	float InitialSpeed = 1500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat", meta = (ClampMin = 100.0f))
	float MaxSpeed = 2000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat", meta = (ClampMin = 1.0f))
	float CollisionRadius = 20.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat")
	float LifeSpan = 3.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat", meta = (ClampMin = 0.0f))
	float DestroyDelay = 0.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|Combat")
	bool bStopOnHit = true;

	// ==========================================
	// ★ 特效资产 — 全部在此处配置（蓝图拖入即可）
	// ==========================================

	// --- 发射特效（Spawn 时在出生位置播放，一次性） ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Launch")
	UParticleSystem* LaunchParticle;     // 出生闪光

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Launch")
	USoundBase* LaunchSound;             // 发射音效

	// --- 飞行特效（Looping，附着在火球上随它飞） ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Flight")
	UParticleSystem* FlightParticle;      // 火球本体粒子

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Flight")
	UParticleSystem* TrailParticle;       // 拖尾粒子

	// --- 击中特效（命中时一次性爆发） ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Impact")
	UParticleSystem* ImpactParticle;      // 爆炸/击中粒子

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Impact")
	USoundBase* ImpactSound;              // 击中音效

	// --- 光源设置 ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Light")
	bool bEnablePointLight = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Light")
	FLinearColor LightColor = FLinearColor(1.f, 0.4f, 0.05f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Light", meta = (ClampMin = 0.f))
	float LightIntensity = 300.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fireball|VFX|Light", meta = (ClampMin = 0.f))
	float LightRadius = 400.f;

	// ==========================================
	// 运行时组件（代码管理生命周期）
	// ==========================================

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components|VFX")
	UParticleSystemComponent* FlightVFXComp;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components|VFX")
	UParticleSystemComponent* TrailVFXComp;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components|VFX")
	UPointLightComponent* PointLightComp;

private:
	bool bHasHit = false;
	FTimerHandle DestroyTimerHandle;

	// ==========================================
	// 内部方法
	// ==========================================

	UFUNCTION()
	void OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);

	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
		const FHitResult& SweepResult);

	void ProcessHit(AActor* HitActor, const FHitResult& Hit);
	void PlayLaunchEffects();              // 发射特效（BeginPlay 调用）
	void PlayImpactEffects(FVector Location); // 击中特效（ProcessHit 调用）
	void StopFlightEffects();             // 停止所有飞行组件（命中后调用）
	void DeferredDestroy();

public:
	// ==========================================
	// 蓝图扩展事件（可选覆盖）
	// ==========================================

	// C++已处理基础特效后调用，BP可添加额外逻辑（震动/飘字/受击动画等）
	UFUNCTION(BlueprintImplementableEvent, Category = "Fireball", meta = (DisplayName = "On Fireball Hit"))
	void BP_OnFireballHit(const FHitResult& Hit);
};
