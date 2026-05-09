// Fill out your copyright notice in the Description page of Project Settings.

#include "AFireballSpawner.h"
#include "Components/SceneComponent.h"
#include "AFireballProjectile.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Engine/World.h"
#include "Kismet/KismetMathLibrary.h"

AAFireballSpawner::AAFireballSpawner()
{
	PrimaryActorTick.bCanEverTick = false;  // 不需要Tick

	// 创建发射点组件
	FireSpawnPoint = CreateDefaultSubobject<USceneComponent>(TEXT("FireSpawnPoint"));
	SetRootComponent(FireSpawnPoint);
}

void AAFireballSpawner::BeginPlay()
{
	Super::BeginPlay();

	// 如果启用自动发射，启动定时器
	if (bAutoFire && FireballClass)
	{
		StartAutoFire();
	}
}

void AAFireballSpawner::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);

	// 清理定时器
	UWorld* World = GetWorld();
	if (World)
	{
		World->GetTimerManager().ClearTimer(AutoFireTimerHandle);
	}
}

void AAFireballSpawner::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}

void AAFireballSpawner::SpawnFireball()
{
	if (!FireballClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("[FireballSpawner] FireballClass 未设置！"));
		return;
	}

	UWorld* World = GetWorld();
	if (!World) return;

	// 计算发射变换
	const FTransform SpawnTransform = FireSpawnPoint->GetComponentTransform();
	const FVector ForwardDir = FireSpawnPoint->GetForwardVector();

	for (int32 i = 0; i < ProjectilesPerShot; ++i)
	{
		// 扇形散射计算
		FVector FireDirection = ForwardDir;

		if (ProjectilesPerShot > 1)
		{
			// 将总角度均匀分配到N颗火球上
			float AngleOffset = 0.0f;
			if (ProjectilesPerShot > 1)
			{
				AngleOffset = -SpreadAngle * 0.5f + (SpreadAngle / (ProjectilesPerShot - 1)) * i;
			}

			// 绕Z轴旋转（水平扇形）
			FireDirection = ForwardDir.RotateAngleAxis(AngleOffset, FVector(0.0f, 0.0f, 1.0f));
		}

		// 生成火球
		AAFireballProjectile* Projectile = World->SpawnActor<AAFireballProjectile>(
			FireballClass, SpawnTransform);

		if (Projectile)
		{
			// 设置发射者（Spawner不是Pawn，不设Instigator，通过Owner关联）
			Projectile->SetOwner(this);

			// 如果需要覆盖速度
			if (OverrideSpeed > 0.0f)
			{
				Projectile->ProjectileMovement->InitialSpeed = OverrideSpeed;
				Projectile->ProjectileMovement->MaxSpeed = OverrideSpeed;
			}

			// 设置初速度方向
			Projectile->ProjectileMovement->Velocity = FireDirection.GetSafeNormal() *
				Projectile->ProjectileMovement->InitialSpeed;
		}
	}
}

void AAFireballSpawner::StartAutoFire()
{
	if (!FireballClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("[FireballSpawner] 无法开始自动发射：FireballClass 未设置"));
		return;
	}

	bAutoFire = true;

	GetWorld()->GetTimerManager().SetTimer(
		AutoFireTimerHandle,
		this,
		&AAFireballSpawner::SpawnFireball,
		FireInterval,
		true,   // 循环
		InitialDelay);  // 首次延迟
}

void AAFireballSpawner::StopAutoFire()
{
	bAutoFire = false;
	GetWorld()->GetTimerManager().ClearTimer(AutoFireTimerHandle);
}
