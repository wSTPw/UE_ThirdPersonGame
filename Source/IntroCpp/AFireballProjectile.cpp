// Fill out your copyright notice in the Description page of Project Settings.

#include "AFireballProjectile.h"
#include "Components/SphereComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Particles/ParticleSystemComponent.h"
#include "Components/PointLightComponent.h"
#include "AttributeComponent.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

AAFireballProjectile::AAFireballProjectile()
{
	PrimaryActorTick.bCanEverTick = false;

	// ========== 碰撞体（Root） ==========
	CollisionComp = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComp"));
	SetRootComponent(CollisionComp);
	CollisionComp->SetSphereRadius(CollisionRadius);
	CollisionComp->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	CollisionComp->SetCollisionResponseToAllChannels(ECR_Ignore);
	CollisionComp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	CollisionComp->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Overlap);
	CollisionComp->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
	CollisionComp->CanCharacterStepUpOn = ECanBeCharacterBase::ECB_No;

	CollisionComp->OnComponentHit.AddDynamic(this, &AAFireballProjectile::OnHit);
	CollisionComp->OnComponentBeginOverlap.AddDynamic(this, &AAFireballProjectile::OnOverlapBegin);

	// ========== 抛射体移动组件 ==========
	ProjectileMovement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovement"));
	ProjectileMovement->UpdatedComponent = CollisionComp;
	ProjectileMovement->InitialSpeed = InitialSpeed;
	ProjectileMovement->MaxSpeed = MaxSpeed;
	ProjectileMovement->bRotationFollowsVelocity = true;
	ProjectileMovement->bInitialVelocityInLocalSpace = false;
	ProjectileMovement->ProjectileGravityScale = 0.0f;

	InitialLifeSpan = LifeSpan;

	// ========== 特效组件（代码创建，资产由蓝图指定） ==========
	// 注意：不设 bAutoActivate，在 BeginPlay 中统一管理激活时机

	FlightVFXComp = CreateDefaultSubobject<UParticleSystemComponent>(TEXT("FlightVFXComp"));
	FlightVFXComp->SetupAttachment(RootComponent);
	FlightVFXComp->bAutoActivate = false;

	TrailVFXComp = CreateDefaultSubobject<UParticleSystemComponent>(TEXT("TrailVFXComp"));
	TrailVFXComp->SetupAttachment(RootComponent);
	TrailVFXComp->bAutoActivate = false;

	PointLightComp = CreateDefaultSubobject<UPointLightComponent>(TEXT("PointLightComp"));
	PointLightComp->SetupAttachment(RootComponent);
	PointLightComp->Intensity = LightIntensity;
	PointLightComp->SetLightColor(LightColor);
	PointLightComp->AttenuationRadius = LightRadius;
	PointLightComp->CastShadows = false;
}

void AAFireballProjectile::BeginPlay()
{
	Super::BeginPlay();

	if (GetInstigator())
	{
		CollisionComp->IgnoreActorWhenMoving(GetInstigator(), true);
	}

	// ★ 阶段1：发射特效
	PlayLaunchEffects();

	// ★ 阶段2：激活飞行特效（持续播放直到命中）
	// 支持两种赋值方式：
	//   方式A：通过 FlightParticle UPROPERTY 指定 → SetTemplate 到组件后激活
	//   方式B：直接在蓝图设置 FlightVFXComp.Template → 直接激活
	UE_LOG(LogTemp, Log, TEXT("[FireballVFX] === Activating Flight VFX ==="));
	UE_LOG(LogTemp, Log, TEXT("[FireballVFX] FlightParticle=%s TrailParticle=%s"),
		FlightParticle ? *FlightParticle->GetName() : TEXT("NONE"),
		TrailParticle ? *TrailParticle->GetName() : TEXT("NONE"));

	if (FlightVFXComp)
	{
		// 如果 FlightParticle 有值，优先用它覆盖组件模板
		if (FlightParticle)
		{
			FlightVFXComp->SetTemplate(FlightParticle);
		}
		// 只要组件有有效 Template 就激活（无论来源是方式A还是方式B）
		if (FlightVFXComp->Template)
		{
			FlightVFXComp->Deactivate();
			FlightVFXComp->Activate(true);
			UE_LOG(LogTemp, Log, TEXT("[FireballVFX] FlightVFXComp Activated: %s"),
				*FlightVFXComp->Template->GetName());
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[FireballVFX] FlightVFXComp has no template, skipping"));
		}
	}

	if (TrailVFXComp)
	{
		if (TrailParticle)
		{
			TrailVFXComp->SetTemplate(TrailParticle);
		}
		if (TrailVFXComp->Template)
		{
			TrailVFXComp->Deactivate();
			TrailVFXComp->Activate(true);
			UE_LOG(LogTemp, Log, TEXT("[FireballVFX] TrailVFXComp Activated"));
		}
	}

	if (PointLightComp)
	{
		PointLightComp->SetVisibility(bEnablePointLight);
	}
}

void AAFireballProjectile::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}

void AAFireballProjectile::OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
	if (bHasHit) return;
	ProcessHit(OtherActor, Hit);
}

void AAFireballProjectile::OnOverlapBegin(UPrimitiveComponent* OverlappedComponent,
	AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	bool bFromSweep, const FHitResult& SweepResult)
{
	if (bHasHit) return;
	ProcessHit(OtherActor, SweepResult);
}

void AAFireballProjectile::ProcessHit(AActor* HitActor, const FHitResult& Hit)
{
	if (bHasHit) return;

	if (HitActor && GetInstigator() && HitActor == GetInstigator())
	{
		return;
	}

	bHasHit = true;

	// 停止移动和碰撞
	if (bStopOnHit)
	{
		ProjectileMovement->Velocity = FVector::ZeroVector;
		ProjectileMovement->SetComponentTickEnabled(false);
		CollisionComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	// 伤害逻辑
	if (HitActor)
	{
		if (UAttributeComponent* TargetAttr = HitActor->FindComponentByClass<UAttributeComponent>())
		{
			TargetAttr->ApplyDamage(Damage, GetInstigator());
		}
	}

	// ★ 阶段3：击中特效（C++ 基础层）
	PlayImpactEffects(Hit.Location);

	// 关闭飞行组件（命中后不再需要）
	StopFlightEffects();

	// 蓝图扩展事件
	BP_OnFireballHit(Hit);

	// 延迟销毁，给击中特效留时间
	if (DestroyDelay > 0.0f)
	{
		GetWorld()->GetTimerManager().SetTimer(DestroyTimerHandle, this,
			&AAFireballProjectile::DeferredDestroy, DestroyDelay, false);
	}
	else
	{
		Destroy();
	}
}

// ==========================================
// 发射特效 — Spawn 时在出生位置播放一次
// ==========================================
void AAFireballProjectile::PlayLaunchEffects()
{
	FVector Location = GetActorLocation();

	// 出生闪光粒子（一次性，自动销毁）
	if (LaunchParticle)
	{
		UGameplayStatics::SpawnEmitterAtLocation(
			this,
			LaunchParticle,
			Location,
			GetActorRotation(),
			FVector(1.f)
		);
	}

	// 发射音效
	if (LaunchSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, LaunchSound, Location);
	}
}

// ==========================================
// 击中特效 — 在碰撞位置播放爆炸+音效
// ==========================================
void AAFireballProjectile::PlayImpactEffects(FVector Location)
{
	// 击中爆炸粒子（一次性，自动销毁）
	if (ImpactParticle)
	{
		UGameplayStatics::SpawnEmitterAtLocation(
			this,
			ImpactParticle,
			Location,
			FRotator::ZeroRotator,
			FVector(1.f)
		);
	}

	// 击中音效
	if (ImpactSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ImpactSound, Location);
	}
}

// ==========================================
// 停止所有飞行中的视觉组件
// ==========================================
void AAFireballProjectile::StopFlightEffects()
{
	if (FlightVFXComp) FlightVFXComp->Deactivate();
	if (TrailVFXComp) TrailVFXComp->Deactivate();
	if (PointLightComp) PointLightComp->SetVisibility(false);
}

void AAFireballProjectile::DeferredDestroy()
{
	Destroy();
}
