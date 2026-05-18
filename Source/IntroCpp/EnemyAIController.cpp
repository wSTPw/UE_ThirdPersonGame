// Fill out your copyright notice in the Description page of Project Settings.

#include "EnemyAIController.h"
#include "EnemyBase.h"
#include "EnemyData.h"
#include "AttributeComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "NavigationSystem.h"
#include "Perception/AIPerceptionComponent.h"
#include "Perception/AISenseConfig_Sight.h"
#include "Perception/AISense_Sight.h"

// ==========================================
// 生命周期
// ==========================================

void AEnemyAIController::BeginPlay()
{
	Super::BeginPlay();
}

void AEnemyAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	// 初始化巡逻中心点为敌人出生位置
	if (InPawn)
	{
		PatrolCenter = InPawn->GetActorLocation();
		CurrentPatrolTarget = GetRandomPatrolPoint();
	}

	// ====== 配置 AIPerception 视觉感知系统 ======
	if (AEnemyBase* Enemy = Cast<AEnemyBase>(InPawn))
	{
		UEnemyData* Data = Enemy->EnemyData;
		if (!Data) return;

		// 创建感知组件
		PerceptionComp = CreateDefaultSubobject<UAIPerceptionComponent>(TEXT("AIPerception"));
		SightConfig = CreateDefaultSubobject<UAISenseConfig_Sight>(TEXT("SightConfig"));

		// 从 EnemyData 读取感知参数
		SightConfig->SightRadius = Data->SightRadius;
		SightConfig->LoseSightRadius = Data->SightRadius + 200.f;  // 丢失半径略大于发现半径
		SightConfig->PeripheralVisionAngleDegrees = 60.f;
		SightConfig->SetMaxAge(Data->ChaseLeewayTime);              // 记忆时间 = 追击容差
		SightConfig->DetectionByAffiliation.bDetectEnemies = true;
		SightConfig->DetectionByAffiliation.bDetectNeutrals = true;

		// 配置并激活感知组件
		PerceptionComp->ConfigureSense(*SightConfig);
		// ConfigureSense 自动将第一个配置的 Sense 设为 Dominant，无需手动调用 SetDominantSenseType
		PerceptionComp->OnTargetPerceptionUpdated.AddDynamic(this, &AEnemyAIController::OnPerceptionUpdated);

		// 激活感知（默认在 BeginPlay 时自动激活，但显式调用更安全）
		PerceptionComp->Activate();
	}
}

// ==========================================
// Tick — 每帧状态机驱动
// ==========================================

void AEnemyAIController::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	UpdateState(DeltaTime);
}

// ==========================================
// 状态更新与切换
// ==========================================

void AEnemyAIController::UpdateState(float DeltaTime)
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy || Enemy->IsDead())
	{
		TransitionToState(EAIState::Dead);
		return;
	}

	switch (CurrentState)
	{
	case EAIState::Patrol:
		State_Patrol(DeltaTime);
		break;

	case EAIState::Chase:
		State_Chase(DeltaTime);
		break;

	case EAIState::Attack:
		State_Attack(DeltaTime);
		break;

	case EAIState::Dead:
		State_Dead(DeltaTime);
		break;
	}
}

void AEnemyAIController::TransitionToState(EAIState NewState)
{
	if (CurrentState == NewState) return;

	EAIState OldState = CurrentState;
	CurrentState = NewState;

	// 状态切换时的清理工作
	switch (NewState)
	{
	case EAIState::Patrol:
		LostTargetTimer = 0.f;       // 重置丢失计时
		ClearFocus(EAIFocusPriority::Default);  // 清除焦点
		break;

	case EAIState::Chase:
		// 进入追击时设置移动速度
		if (AEnemyBase* Enemy = GetEnemyPawn())
		{
			if (UCharacterMovementComponent* MoveComp = Enemy->GetCharacterMovement())
			{
				if (Enemy->EnemyData)
				{
					MoveComp->MaxWalkSpeed = Enemy->EnemyData->ChaseSpeed;
				}
			}
		}
		break;

	case EAIState::Attack:
		StopMovement();  // 攻击时停止移动
		break;

	case EAIState::Dead:
		StopMovement();
		ClearFocus(EAIFocusPriority::Gameplay);
		break;
	}
}


// ==========================================
// 状态: Patrol（巡逻）
// ==========================================

void AEnemyAIController::State_Patrol(float DeltaTime)
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy || !Enemy->IsAlive()) { TransitionToState(EAIState::Dead); return; }

	UEnemyData* Data = Enemy->EnemyData;
	if (!Data) return;

	// 优先检测：是否能看到目标？→ 进入追击
	if (CanSeeTarget())
	{
		TransitionToState(EAIState::Chase);
		return;
	}

	// 正在等待？
	if (bWaitingAtPatrolPoint)
	{
		WaitTimer -= DeltaTime;

		if (WaitTimer <= 0.f)
		{
			bWaitingAtPatrolPoint = false;

			// 停止待机动画（如果正在播放）
			if (Enemy && Data->IdleMontage)
			{
				Enemy->StopAnimMontage(Data->IdleMontage);
			}

			// 选下一个巡逻点
			CurrentPatrolTarget = ChooseNextPatrolPoint();
		}
		else if (!bIsPlayingIdleMontage && Data->IdleMontage && Enemy)  // 首次进入等待时播放
		{
			Enemy->PlayAnimMontage(Data->IdleMontage);
			bIsPlayingIdleMontage = true;
		}
		return;  // 等待期间不移动
	}

	// 重置标记（开始移动时）
	bIsPlayingIdleMontage = false;

	// 向当前巡逻目标移动
	float DistToTarget = FVector::Dist2D(GetPawn()->GetActorLocation(), CurrentPatrolTarget);

	if (DistToTarget < 50.f)  // 到达巡逻点
	{
		bWaitingAtPatrolPoint = true;
		WaitTimer = Data->WaitTimeAtPatrolPoint;
		StopMovement();

		// 恢复巡逻速度
		if (UCharacterMovementComponent* MoveComp = Enemy->GetCharacterMovement())
		{
			MoveComp->MaxWalkSpeed = Data->WalkSpeed;
		}
	}
	else
	{
		// 使用 UE 的 AIMoveTo 移动
		MoveToLocation(CurrentPatrolTarget, -1.f, true, true);  // AcceptPartialPath
	}
}


// ==========================================
// 状态: Chase（追击）
// ==========================================

void AEnemyAIController::State_Chase(float DeltaTime)
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy || !Enemy->IsAlive()) { TransitionToState(EAIState::Dead); return; }

	// ★★★ Bug 修复：使用 Enemy->GetTargetActor() 而非 GetPawn<AActor>() ★★★
	// 原代码 GetPawn<AActor>() 返回的是 AI 控制的 Pawn（敌人自身），不是目标！
	AActor* TargetActor = Enemy->GetTargetActor();
	if (!TargetActor) { TransitionToState(EAIState::Patrol); LostTargetTimer = 0.f; return; }

	// 移动到目标位置
	float AttackRange = Enemy->EnemyData ? Enemy->EnemyData->AttackRange : 150.f;
	MoveToActor(TargetActor, AttackRange);

	// 检测目标是否在攻击范围内 → 转入攻击
	if (Enemy->IsTargetInRange(AttackRange))
	{
		TransitionToState(EAIState::Attack);
		LostTargetTimer = 0.f;
		return;
	}

	// 丢失目标检测（带防抖动）
	if (!CanSeeTarget())
	{
		LostTargetTimer += DeltaTime;
		float Leeway = (Enemy->EnemyData) ? Enemy->EnemyData->ChaseLeewayTime : 1.f;
		if (LostTargetTimer >= Leeway)
		{
			// 丢失太久 → 回到巡逻
			TransitionToState(EAIState::Patrol);
			LostTargetTimer = 0.f;
			ClearFocus(EAIFocusPriority::Default);
		}
	}
	else
	{
		LostTargetTimer = 0.f;  // 重置丢失计时
	}
}


// ==========================================
// 状态: Attack（攻击）
// ==========================================

void AEnemyAIController::State_Attack(float DeltaTime)
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy || !Enemy->IsAlive()) { TransitionToState(EAIState::Dead); return; }

	// ★★★ 同样修复：使用正确的目标获取方式 ★★★
	AActor* TargetActor = Enemy->GetTargetActor();
	if (!TargetActor) { TransitionToState(EAIState::Patrol); ClearFocus(EAIFocusPriority::Default); return; }

	// 面向目标
	SetFocus(TargetActor);

	// 停止移动（站在原地攻击）
	StopMovement();

	// 检查目标是否还在攻击范围内（带容差防抖动）
	float AttackRange = (Enemy->EnemyData) ? Enemy->EnemyData->AttackRange : 150.f;
	float GraceTime = (Enemy->EnemyData) ? Enemy->EnemyData->ExitAttackRangeGraceTime : 0.5f;
	float Distance = FVector::Dist(GetPawn()->GetActorLocation(), TargetActor->GetActorLocation());

	if (Distance > AttackRange * 1.2f)
	{
		// 目标脱离攻击范围 → 启动容差倒计时（防止边缘抖动）
		if (!bAttackGraceActive)
		{
			bAttackGraceActive = true;
			AttackGraceTimer = GraceTime;
		}
		else
		{
			AttackGraceTimer -= DeltaTime;
			if (AttackGraceTimer <= 0.f)
			{
				// 容差时间耗尽 → 真正回到追击
				bAttackGraceActive = false;
				AttackGraceTimer = 0.f;
				TransitionToState(EAIState::Chase);
				return;
			}
		}
	}
	else
	{
		// 目标回到范围内 → 取消容差计时
		if (bAttackGraceActive)
		{
			bAttackGraceActive = false;
			AttackGraceTimer = 0.f;
		}
	}

	// 目标还活着吗？（检查 AttributeComponent 的存活状态）
	if (UAttributeComponent* TargetAttr = TargetActor->FindComponentByClass<UAttributeComponent>())
	{
		if (!TargetAttr->IsAlive())
		{
			// 目标已死 → 回到巡逻
			TransitionToState(EAIState::Patrol);
			ClearFocus(EAIFocusPriority::Default);
			return;
		}
	}

	// 执行攻击（冷却由 EnemyBase.PerformAttack() 内部控制）
	Enemy->PerformAttack();
}


// ==========================================
// 状态: Dead（死亡）
// ==========================================

void AEnemyAIController::State_Dead(float DeltaTime)
{
	// 死亡状态不做任何事，仅保持停止
	// 实际销毁由 EnemyBase::Die() 处理
}


// ==========================================
// 辅助方法
// ==========================================

bool AEnemyAIController::CanSeeTarget() const
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy) return false;

	AActor* Target = Enemy->GetTargetActor();
	if (!Target) return false;

	UEnemyData* Data = Enemy->EnemyData;
	if (!Data) return false;

	// 1. 距离检测
	float Distance = FVector::Dist(GetPawn()->GetActorLocation(), Target->GetActorLocation());
	if (Distance > Data->SightRadius) return false;

	// 2. 视线检测（LineOfSight）— 防止隔墙看到玩家
	FVector Start = GetPawn()->GetActorLocation();
	Start.Z += 60.f;  // 从眼睛高度发出（约胶囊体上方）

	FVector End = Target->GetActorLocation();
	End.Z += 50.f;     // 目标中心高度

	FHitResult HitResult;
	bool bBlocked = GetWorld()->LineTraceSingleByChannel(
		HitResult,
		Start,
		End,
		ECC_Visibility,
		FCollisionQueryParams::DefaultQueryParam
	);

	// 如果视线被阻挡，且阻挡物不是目标本身 → 看不到
	if (bBlocked && HitResult.GetActor() != Target)
	{
		return false;
	}

	// 即使暂时看不到（刚出视野），如果在记忆时间内也视为可见
	return true;
}

FVector AEnemyAIController::ChooseNextPatrolPoint()
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy || !Enemy->EnemyData) return GetRandomPatrolPoint();

	switch (Enemy->EnemyData->PatrolBehavior)
	{
	case EPatrolType::Circular:
	{
		// 环形巡逻：循环遍历（当前用随机点模拟，可后续扩展为预定义点数组）
		// 暂时退化为随机，保持向后兼容
		PatrolIndex++;
		break;
	}

	case EPatrolType::BackAndForth:
	{
		// 来回巡逻：到端点后翻转方向
		if (bPatrolForward)
		{
			PatrolIndex++;
			if (PatrolIndex >= 4) bPatrolForward = false;  // 到右端折返
		}
		else
		{
			PatrolIndex--;
			if (PatrolIndex <= 0) bPatrolForward = true;   // 到左端折返
		}
		break;
	}

	case EPatrolType::Random:
	default:
		break;
	}

	return GetRandomPatrolPoint();
}

FVector AEnemyAIController::GetRandomPatrolPoint() const
{
	if (!GetPawn()) return FVector::ZeroVector;

	// 在 PatrolRadius 内随机生成一个点
	FVector RandomOffset = FMath::VRand() * FMath::RandRange(0.f, 1000.f);
	if (AEnemyBase* Enemy = GetEnemyPawn())
	{
		if (Enemy->EnemyData)
		{
			RandomOffset = FMath::VRand() * FMath::RandRange(0.f, Enemy->EnemyData->PatrolRadius);
		}
	}

	// 限制在 X-Y 平面内，Z 保持与出生位置一致
	FVector Result = PatrolCenter + RandomOffset;
	Result.Z = PatrolCenter.Z;

	return Result;
}

AEnemyBase* AEnemyAIController::GetEnemyPawn() const
{
	if (!GetPawn()) return nullptr;
	return Cast<AEnemyBase>(GetPawn());
}

void AEnemyAIController::OnOwnerDied()
{
	TransitionToState(EAIState::Dead);
	StopMovement();
	ClearFocus(EAIFocusPriority::Gameplay);
}

// ==========================================
// AIPerception 回调 — 目标发现/丢失
// ==========================================

void AEnemyAIController::OnPerceptionUpdated(AActor* Actor, FAIStimulus Stimulus)
{
	AEnemyBase* Enemy = GetEnemyPawn();
	if (!Enemy || Enemy->IsDead()) return;

	if (Stimulus.WasSuccessfullySensed())
	{
		// ★ 发现目标 → 设置目标并进入追击
		// 过滤：只追踪有 AttributeComponent 的 Actor（即玩家/可攻击单位）
		if (Actor->FindComponentByClass<UAttributeComponent>())
		{
			Enemy->SetTargetActor(Actor);
			SetFocus(Actor);

			if (CurrentState == EAIState::Patrol)
			{
				TransitionToState(EAIState::Chase);
			}
			// 如果已在 Chase/Attack，更新焦点即可（不强制切状态，避免打断攻击）
		}
	}
	else
	{
		// ★ 丢失目标
		// 不立即清除 TargetActor，而是清除 Focus
		// 让 State_Chase 中的 LostTargetTimer + ChaseLeewayTime 来决定何时回 Patrol
		if (Actor == Enemy->GetTargetActor())
		{
			ClearFocus(EAIFocusPriority::Default);
			// LostTargetTimer 在 State_Chase 中递增，超时后自动回 Patrol
		}
	}
}
