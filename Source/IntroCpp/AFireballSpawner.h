// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFireballSpawner.generated.h"

class USceneComponent;
class AAFireballProjectile;

/**
 * 火球发射器 Actor
 * 可定时自动发射或通过 SpawnFireball() 手动触发
 * 放置到场景中的任何物体上作为发射源
 */
UCLASS()
class INTROCPP_API AAFireballSpawner : public AActor
{
	GENERATED_BODY()

public:
	AAFireballSpawner();

protected:
	virtual void BeginPlay() override;

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
	virtual void Tick(float DeltaTime) override;

	// ==========================================
	// 组件
	// ==========================================

	// 发射点（决定火球的出生位置和初始朝向）
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Components")
	USceneComponent* FireSpawnPoint;

	// ==========================================
	// 配置属性（蓝图可编辑）
	// ==========================================

	// 火球类（在蓝图中选择具体的 BP_FireballProjectile）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawner")
	TSubclassOf<AAFireballProjectile> FireballClass;

	// 是否自动发射
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawner")
	bool bAutoFire = false;

	// 自动发射间隔（秒）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawner", meta = (EditCondition = "bAutoFire", ClampMin = 0.1f))
	float FireInterval = 2.0f;

	// 游戏开始后首次发射延迟（秒）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawner", meta = (ClampMin = 0.0f))
	float InitialDelay = 0.5f;

	// 每次发射数量（1=单发，>1=扇形散射）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, category = "Spawner", meta = (ClampMin = 1))
	int32 ProjectilesPerShot = 1;

	// 扇形散射总角度（度数），仅当 ProjectilesPerShot > 1 时有效
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawner", meta = (ClampMin = 0.0f, ClampMax = 360.0f))
	float SpreadAngle = 30.0f;

	// 发射后是否覆盖火球自身的 InitialSpeed（0=不覆盖，使用火球自身值）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawner", meta = (ClampMin = 0.0f))
	float OverrideSpeed = 0.0f;

	// ==========================================
	// 方法
	// ==========================================

	// 手动发射一颗火球（蓝图可调用）
	UFUNCTION(BlueprintCallable, Category = "Spawner")
	void SpawnFireball();

	// 开始自动发射
	UFUNCTION(BlueprintCallable, Category = "Spawner")
	void StartAutoFire();

	// 停止自动发射
	UFUNCTION(BlueprintCallable, Category = "Spawner")
	void StopAutoFire();

private:
	// 自动发射定时器
	FTimerHandle AutoFireTimerHandle;
};
