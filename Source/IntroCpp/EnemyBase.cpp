// Fill out your copyright notice in the Description page of Project Settings.

#include "EnemyBase.h"
#include "Components/SceneComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Kismet/GameplayStatics.h"
#include "AnimNotify_EnemyAttack.h"
#include "Animation/AnimInstance.h"

// ==========================================
// 构造函数
// ==========================================

AEnemyBase::AEnemyBase()
{
	PrimaryActorTick.bCanEverTick = true;

	// 禁用玩家控制（敌人不需要）
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	// 创建 AttributeComponent
	AttributeComp = CreateDefaultSubobject<UAttributeComponent>(TEXT("AttributeComp"));

	// 创建攻击检测起始点
	AttackOrigin = CreateDefaultSubobject<USceneComponent>(TEXT("AttackOrigin"));
	AttackOrigin->SetupAttachment(RootComponent);
}

// ==========================================
// BeginPlay — 初始化流程
// ==========================================

void AEnemyBase::BeginPlay()
{
	Super::BeginPlay();

	// 1. 确保 AttributeComp 存在并绑定委托（和 UI 监听 AttributeComp 是同一套模式）
	if (AttributeComp)
	{
		AttributeComp->OnHealthChanged.AddDynamic(this, &AEnemyBase::OnHealthChanged);
		AttributeComp->OnCharacterDeath.AddDynamic(this, &AEnemyBase::OnDeathDelegate);
		AttributeComp->OnDamaged.AddDynamic(this, &AEnemyBase::OnReceiveDamage);  // 受击反馈

		// 从 EnemyData 初始设置 HP
		if (EnemyData)
		{
			AttributeComp->SetMaxHealth(EnemyData->MaxHealth);
			AttributeComp->SetHealth(EnemyData->MaxHealth);
		}
	}

	// 2. 绑定 Montage 结束回调，用于重置 bIsAttacking 状态
	if (GetMesh() && GetMesh()->GetAnimInstance())
	{
		GetMesh()->GetAnimInstance()->OnMontageEnded.AddDynamic(this, &AEnemyBase::OnAttackMontageEnded);
	}

	// 3. 应用 EnemyData 配置的速度、外观等
	ApplyEnemyDataSettings();
	ApplyAppearanceFromData();
}

// ==========================================
// Tick — 每帧更新
// ==========================================

void AEnemyBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// 死亡销毁倒计时处理
	if (bIsDead)
	{
		DeathDestroyTimer -= DeltaTime;
		if (DeathDestroyTimer <= 0.f)
		{
			Destroy();
		}
		return;  // 死亡后不再执行其他逻辑
	}

	// 面向目标插值旋转（如果允许转向且非攻击中）
	if (EnemyData && EnemyData->bCanRotate && TargetActor && !bIsAttacking)
	{
		FVector TargetLoc = TargetActor->GetActorLocation();
		TargetLoc.Z = GetActorLocation().Z;  // 忽略高度差，只水平旋转
		FRotator TargetRot = (TargetLoc - GetActorLocation()).Rotation();
		FRotator NewRot = FMath::RInterpTo(GetActorRotation(), TargetRot, DeltaTime, EnemyData->RotationInterpSpeed);
		SetActorRotation(NewRot);
	}
}

// ==========================================
// AI 接口方法
// ==========================================

void AEnemyBase::SetTargetActor(AActor* Target)
{
	TargetActor = Target;
}

void AEnemyBase::ClearTargetActor()
{
	TargetActor = nullptr;
}

bool AEnemyBase::IsTargetInRange(float Range) const
{
	if (!TargetActor) return false;
	float Dist = FVector::Dist(GetActorLocation(), TargetActor->GetActorLocation());
	return Dist <= Range;
}

bool AEnemyBase::IsAlive() const
{
	return AttributeComp && AttributeComp->IsAlive();
}


// ==========================================
// 攻击系统
// ==========================================

void AEnemyBase::PerformAttack()
{
	// 条件守卫
	if (bIsDead || !IsAlive()) return;
	if (!EnemyData || !EnemyData->AttackMontage) return;

	// 冷却检查
	float CurrentTime = GetWorld()->GetTimeSeconds();
	if (CurrentTime - LastAttackTime < EnemyData->AttackCooldown) return;

	// 标记状态
	bIsAttacking = true;
	LastAttackTime = CurrentTime;

	// 播放攻击 Montage（和 UseHeldItem() 完全一样的模式）
	float Duration = PlayAnimMontage(EnemyData->AttackMontage);

	if (Duration <= 0.f)
	{
		// 没有 Montage 或播放失败 → 直接执行伤害后立即重置
		ExecuteMeleeDamage();
		bIsAttacking = false;
	}
	// 有 Montage → 等 AnimNotify 触发 OnAttackAnimNotify()
	// Montage 结束时由 OnAttackMontageEnded 回调重置 bIsAttacking
}

void AEnemyBase::OnAttackAnimNotify()
{
	ExecuteMeleeDamage();
}

void AEnemyBase::OnAttackMontageEnded(UAnimMontage* Montage, bool bInterrupted)
{
	if (bIsAttacking)
	{
		bIsAttacking = false;
	}
}

// ==========================================
// 核心伤害检测
// ==========================================

void AEnemyBase::ExecuteMeleeDamage()
{
	if (!TargetActor || !EnemyData) return;

	// === SphereTrace 攻击检测 ===
	FVector Start = AttackOrigin ? AttackOrigin->GetComponentLocation() : GetActorLocation();
	Start.Z += EnemyData->AttackZOffset;  // Z 轴偏移

	FVector ForwardDir = GetActorForwardVector();
	FVector End = Start + ForwardDir * EnemyData->AttackForwardOffset;

	FCollisionQueryParams Params;
	Params.AddIgnoredActor(this);          // 忽略自己

	FHitResult HitResult;
	bool bHit = GetWorld()->SweepSingleByChannel(
		HitResult,
		Start,
		End,
		FQuat::Identity,
		ECC_Pawn,                          // 检测 Pawn 通道（玩家/敌人都是 Pawn）
		FCollisionShape::MakeSphere(EnemyData->AttackSphereRadius),
		Params
	);

	// === 命中判定 ===
	if (bHit && HitResult.GetActor())
	{
		AActor* HitActor = HitResult.GetActor();

		// ★★★ 和火球 ProcessHit 完全相同的伤害调用方式 ★★★
		if (UAttributeComponent* TargetAttr = HitActor->FindComponentByClass<UAttributeComponent>())
		{
			TargetAttr->ApplyDamage(EnemyData->AttackDamage, this);

			// 击退效果
			if (EnemyData->KnockbackForce > 0.f)
			{
				FVector KnockbackDir = (HitActor->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
				KnockbackDir.Z = 0.3f;  // 轻微向上

				// 对 Character 类型施加冲量
				if (ACharacter* HitChar = Cast<ACharacter>(HitActor))
				{
					HitChar->LaunchCharacter(KnockbackDir * EnemyData->KnockbackForce, true, true);
				}
			}
		}

		// 蓝图扩展点（给美术加 VFX/Sound）
		BP_OnEnemyAttackHit(HitResult);
	}

	// 播放攻击音效
	if (EnemyData && EnemyData->AttackSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, EnemyData->AttackSound, GetActorLocation());
	}
}


// ==========================================
// 死亡 / 受击
// ==========================================

void AEnemyBase::Die()
{
	if (bIsDead) return;
	bIsDead = true;
	bIsAttacking = false;       // 中断攻击状态
	ClearTargetActor();          // 清除目标

	// 停止移动和所有行为
	GetCharacterMovement()->StopMovementImmediately();

	// 停止当前正在播放的 Montage（如果正在播放攻击动画）
	if (GetMesh() && GetMesh()->GetAnimInstance())
	{
		GetMesh()->GetAnimInstance()->StopAllMontages(0.2f);
	}

	// 播放死亡动画
	if (EnemyData && EnemyData->DeathMontage)
	{
		float Duration = PlayAnimMontage(EnemyData->DeathMontage);
		if (Duration <= 0.f)
		{
			Duration = 1.f;  // 最小等待
		}
		DeathDestroyTimer = Duration + DEATH_DESTROY_DELAY;
	}
	else
	{
		// 无死亡动画 → 快速消失
		DeathDestroyTimer = 0.5f;
	}

	// 碰撞禁用（防止死后还能被攻击/阻挡）
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// 死亡音效
	if (EnemyData && EnemyData->DeathSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, EnemyData->DeathSound, GetActorLocation());
	}

	// 蓝图扩展点：掉落物/VFX 等
	BP_OnEnemyDeath();
}

void AEnemyBase::OnReceiveDamage(float DamageAmount, AActor* DamageCauser)
{
	UE_LOG(LogTemp, Log, TEXT("[EnemyBase] %s 被攻击！本次伤害: %.1f，剩余HP: %.1f/%.1f，攻击者: %s"),
		*GetName(), DamageAmount,
		AttributeComp ? AttributeComp->GetCurrentHealth() : 0.f,
		AttributeComp ? AttributeComp->GetMaxHealth() : 0.f,
		DamageCauser ? *DamageCauser->GetName() : TEXT("None"));

	// 播放受击音效
	if (EnemyData && EnemyData->HitSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, EnemyData->HitSound, GetActorLocation());
	}

	// 中断正在进行的攻击
	if (bIsAttacking && GetMesh() && GetMesh()->GetAnimInstance())
	{
		GetMesh()->GetAnimInstance()->StopAllMontages(0.1f);
		bIsAttacking = false;
	}

	// ★ 播放受击动画（带硬直：播放期间禁用移动）
	if (EnemyData && EnemyData->HitReactMontage && !bIsDead)
	{
		float Duration = PlayAnimMontage(EnemyData->HitReactMontage);
		if (Duration > 0.f && GetCharacterMovement())
		{
			// 硬直期间禁用移动
			GetCharacterMovement()->DisableMovement();

			FTimerHandle Handle;
			GetWorldTimerManager().SetTimer(Handle, [this]()
			{
				if (!bIsDead && GetCharacterMovement())
				{
					GetCharacterMovement()->SetMovementMode(MOVE_Walking);
				}
			}, Duration, false);
		}
	}
}


// ==========================================
// 委托回调
// ==========================================

void AEnemyBase::OnHealthChanged(float CurrentHP, float MaxHP)
{
	// HP 变化时可在此处更新敌人血条 UI（后续扩展）
	// 当前仅作为日志/调试用途
}

void AEnemyBase::OnDeathDelegate()
{
	Die();
}


// ==========================================
// 数据应用
// ==========================================

void AEnemyBase::ApplyEnemyDataSettings()
{
	if (!EnemyData) return;

	// 设置移动速度
	if (UCharacterMovementComponent* MoveComp = GetCharacterMovement())
	{
		MoveComp->MaxWalkSpeed = EnemyData->WalkSpeed;
	}
}

void AEnemyBase::ApplyAppearanceFromData()
{
	if (!EnemyData) return;

	// 设置骨骼网格体
	if (EnemyData->BodyMesh && GetMesh())
	{
		GetMesh()->SetSkeletalMesh(EnemyData->BodyMesh);
	}

	// 设置材质覆盖
	if (EnemyData->BodyMaterial && GetMesh())
	{
		GetMesh()->SetMaterial(0, EnemyData->BodyMaterial);
	}

	// 设置缩放
	SetActorScale3D(EnemyData->MeshScale);
}
