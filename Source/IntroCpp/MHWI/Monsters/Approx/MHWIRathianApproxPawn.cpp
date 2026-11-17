#include "MHWIRathianApproxPawn.h"
#include "MHWIRathianApproxAnimInstance.h"
#include "MHWIRathianApproxFireball.h"
#include "MHWIRathianApproxStateComponent.h"
#include "MHWIRathianDecisionComponent.h"
#include "AttributeComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/SphereComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/Character.h"
#include "MHWI/MHWICharacter.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "DrawDebugHelpers.h"

static TAutoConsoleVariable<int32> CVarRathianDebugBoxes(TEXT("mhwi.RathianApprox.DebugBoxes"), 0, TEXT("Draw Approx Rathian attack boxes."), ECVF_Cheat);

namespace
{
    constexpr double MaxMovementStepCm = 250.0;
    // Engineering geometry tuning: a small floor gap avoids tangent floor sweeps blocking horizontal motion.
    constexpr float GroundClearanceCm = 2.f;

    double ResolveLegacySpeed(const UMHWIRathianApproxStatsData* Stats)
    {
        const float Configured = Stats ? Stats->LocomotionSpeedCmPerSecond : 300.f;
        return FMath::IsFinite(Configured) && Configured > 0.f ? static_cast<double>(Configured) : 300.0;
    }

    double ResolvePatrolSpeed(const UMHWIRathianApproxStatsData* Stats)
    {
        const float Configured = Stats ? Stats->PatrolSpeedCmPerSecond : 0.f;
        return FMath::IsFinite(Configured) && Configured > 0.f
            ? static_cast<double>(Configured)
            : ResolveLegacySpeed(Stats) * 0.5;
    }

    double ResolveApproachSpeed(const UMHWIRathianApproxStatsData* Stats)
    {
        const double Legacy = ResolveLegacySpeed(Stats);
        const double Patrol = ResolvePatrolSpeed(Stats);
        const float Configured = Stats ? Stats->ApproachSpeedCmPerSecond : 0.f;
        double Approach = FMath::IsFinite(Configured) && Configured > 0.f
            ? static_cast<double>(Configured)
            : Legacy;
        if (Approach <= Patrol) Approach = FMath::Max(Legacy, Patrol * 2.0);
        return Approach;
    }

    float BoundedMovementDelta(double SpeedCmPerSecond, float DeltaSeconds)
    {
        if (!FMath::IsFinite(SpeedCmPerSecond) || SpeedCmPerSecond <= 0.0 || !FMath::IsFinite(DeltaSeconds)) return 0.f;
        const double RequestedStep = SpeedCmPerSecond * FMath::Max(0.0, static_cast<double>(DeltaSeconds));
        return static_cast<float>(FMath::Clamp(RequestedStep, 0.0, MaxMovementStepCm));
    }

    float LocomotionBlendAlpha(float SpeedCmPerSecond, const UMHWIRathianApproxStatsData* Stats)
    {
        if (!FMath::IsFinite(SpeedCmPerSecond) || SpeedCmPerSecond <= 0.f) return 0.f;
        const double Speed = SpeedCmPerSecond;
        const double Walk = ResolvePatrolSpeed(Stats);
        const double Run = ResolveApproachSpeed(Stats);
        const double Alpha = Speed <= Walk
            ? 0.5 * (Speed / Walk)
            : 0.5 + 0.5 * ((Speed - Walk) / (Run - Walk));
        return static_cast<float>(FMath::Clamp(Alpha, 0.0, 1.0));
    }
}

AMHWIRathianApproxPawn::AMHWIRathianApproxPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    HitProxy = CreateDefaultSubobject<USphereComponent>(TEXT("HitProxy"));
    SetRootComponent(HitProxy);
    HitProxy->InitSphereRadius(140.f);
    HitProxy->SetCollisionObjectType(ECC_Pawn);
    HitProxy->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    HitProxy->SetCollisionResponseToAllChannels(ECR_Block);
    Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(HitProxy);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->bEnableUpdateRateOptimizations = false;
    Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Attributes = CreateDefaultSubobject<UAttributeComponent>(TEXT("Attributes"));
    ApproxState = CreateDefaultSubobject<UMHWIRathianApproxStateComponent>(TEXT("ApproxState"));
    Decision = CreateDefaultSubobject<UMHWIRathianDecisionComponent>(TEXT("Decision"));
    HealthDisplay = CreateDefaultSubobject<UTextRenderComponent>(TEXT("HealthDisplay"));
    HealthDisplay->SetupAttachment(HitProxy);
    HealthDisplay->SetRelativeLocation(FVector(0,0,240));
    HealthDisplay->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
    HealthDisplay->SetWorldSize(40.f);
    HealthDisplay->SetTextRenderColor(FColor(255,80,60));
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> BodyFinder(TEXT("/Game/MHWI/Rathalos/Mesh/SK_EM001_Body.SK_EM001_Body"));
    if (BodyFinder.Succeeded()) { Body->SetSkeletalMesh(BodyFinder.Object); BodyMesh = BodyFinder.Object; }
}

void AMHWIRathianApproxPawn::BeginPlay()
{
    Super::BeginPlay();
    PatrolOrigin = GetActorLocation(); PatrolGoal = PatrolOrigin;
    ConfigureApprox(); if (ExecState!=EExecState::Dead) SnapToGround(); PatrolOrigin = GetActorLocation();
}

void AMHWIRathianApproxPawn::ConfigureApprox()
{
    if (bConfigured) return;
    if (!MovesetData) MovesetData = NewObject<UMHWIRathianApproxMovesetData>(this);
    if (!StatsData) StatsData = NewObject<UMHWIRathianApproxStatsData>(this);
    if (!MovesetData || !StatsData || !Body || !Attributes) return;
    if (!Attributes->IsAlive())
    {
        bConfigured=true; bDeathHandled=true; ExecState=EExecState::Dead;
        UE_LOG(LogTemp,Warning,TEXT("[RathianApprox] ConfigureApprox rejected already-dead Attributes; health is not reset"));
        return;
    }
    if (!BodyMesh.IsNull())
    {
        if (USkeletalMesh* Mesh = BodyMesh.LoadSynchronous()) Body->SetSkeletalMesh(Mesh);
        else UE_LOG(LogTemp, Error, TEXT("[RathianApprox] BodyMesh load failed: %s"), *BodyMesh.ToString());
    }
    ActiveStats = StatsData;
    Body->SetAnimationMode(EAnimationMode::AnimationBlueprint);
    Body->SetAnimInstanceClass(UMHWIRathianApproxAnimInstance::StaticClass());
    Attributes->bCanDie = true; Attributes->HealthRegenPerSecond = 0.f;
    if (!bAttributesInitialized) { Attributes->SetMaxHealth(StatsData->MaxHealth); Attributes->SetHealth(StatsData->MaxHealth); bAttributesInitialized = true; }
    ApproxState->Configure(StatsData); ApproxState->BindAttributes(Attributes);
    Decision->Configure(MovesetData, StatsData, ApproxState);
    Attributes->OnCharacterDeath.AddUniqueDynamic(this, &AMHWIRathianApproxPawn::HandleDeath);
    bConfigured = true;
    UAnimSequence* Idle = MovesetData->IdleAnimation.LoadSynchronous();
    UAnimSequence* Walk = MovesetData->WalkAnimation.LoadSynchronous();
    UAnimSequence* Run = MovesetData->RunAnimation.LoadSynchronous();
    auto Valid = [this](UAnimSequence* Seq, const TCHAR* Name)
    {
        if (!Seq) { UE_LOG(LogTemp, Warning, TEXT("[RathianApprox] missing %s animation"), Name); return false; }
        if (Body->GetSkeletalMeshAsset() && Seq->GetSkeleton() != Body->GetSkeletalMeshAsset()->GetSkeleton())
        { UE_LOG(LogTemp, Error, TEXT("[RathianApprox] %s animation skeleton mismatch"), Name); return false; }
        return true;
    };
    if (Valid(Idle,TEXT("idle")) && Valid(Walk,TEXT("walk")) && Valid(Run,TEXT("run")))
        if (UMHWIRathianApproxAnimInstance* Anim = Cast<UMHWIRathianApproxAnimInstance>(Body->GetAnimInstance())) Anim->ConfigureLocomotion(Idle,Walk,Run);
    else UE_LOG(LogTemp, Warning, TEXT("[RathianApprox] assign skeleton-matched idle/walk/run to enable locomotion graph"));
    PatrolOrigin = GetActorLocation();
    UE_LOG(LogTemp, Log, TEXT("[RathianApprox] configured hp=%.0f moves=%d"), Attributes->GetMaxHealth(), MovesetData->Moves.Num());
}

void AMHWIRathianApproxPawn::SnapToGround()
{
    if (!GetWorld() || !HitProxy || !Body) return;
    FHitResult H; FCollisionQueryParams P(SCENE_QUERY_STAT(RathianGroundSnap),false,this);
    const FVector S=GetActorLocation()+FVector(0,0,800), E=S-FVector(0,0,8000);
    if (GetWorld()->LineTraceSingleByChannel(H,S,E,ECC_WorldStatic,P))
    { SetActorLocation(FVector(GetActorLocation().X,GetActorLocation().Y,H.ImpactPoint.Z+HitProxy->GetScaledSphereRadius()+GroundClearanceCm)); Body->SetRelativeLocation(FVector(0,0,BodyGroundOffsetCm)); }
}

void AMHWIRathianApproxPawn::SetCombatTarget(AActor* NewTarget)
{
    check(IsInGameThread()); ForcedTarget=IsValid(NewTarget)?NewTarget:nullptr; CombatTarget=ForcedTarget;
    if (Decision) Decision->SetTarget(CombatTarget);
}

bool AMHWIRathianApproxPawn::HasLineOfSight(AActor* Target) const
{
    if (!Target || !GetWorld()) return false;
    FHitResult H; FCollisionQueryParams P(SCENE_QUERY_STAT(RathianSight),false,this); P.AddIgnoredActor(Target);
    return !GetWorld()->LineTraceSingleByChannel(H,GetActorLocation()+FVector(0,0,100),Target->GetActorLocation()+FVector(0,0,50),ECC_Visibility,P);
}

AActor* AMHWIRathianApproxPawn::FindOrAcquireTarget()
{
    if (AActor* Forced=ForcedTarget.Get())
    {
        const UAttributeComponent* A=Forced->FindComponentByClass<UAttributeComponent>();
        if (IsValid(Forced) && (!A||A->IsAlive()) && FVector::Dist2D(GetActorLocation(),Forced->GetActorLocation()) <= (ActiveStats?ActiveStats->LoseTargetRangeCm:2400.f)) { CombatTarget=Forced; return Forced; }
        ForcedTarget.Reset();
    }
    if (AActor* Existing=CombatTarget.Get())
    {
        const UAttributeComponent* A=Existing->FindComponentByClass<UAttributeComponent>();
        if (IsValid(Existing) && (!A||A->IsAlive()) && FVector::Dist2D(GetActorLocation(),Existing->GetActorLocation()) <= (ActiveStats?ActiveStats->LoseTargetRangeCm:2400.f) && HasLineOfSight(Existing)) return Existing;
        CombatTarget.Reset();
    }
    APawn* Candidate=UGameplayStatics::GetPlayerPawn(this,0);
    if (!Candidate||Candidate==this) return nullptr;
    const UAttributeComponent* A=Candidate->FindComponentByClass<UAttributeComponent>(); if (A&&!A->IsAlive()) return nullptr;
    const FVector To=Candidate->GetActorLocation()-GetActorLocation();
    const float Range=ActiveStats?ActiveStats->SightRangeCm:1800.f, HalfAngle=ActiveStats?ActiveStats->SightHalfAngleDegrees:70.f;
    const float Angle=FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(GetActorForwardVector(),To.GetSafeNormal2D()),-1.f,1.f)));
    if (To.Size2D()>Range||Angle>HalfAngle||!HasLineOfSight(Candidate)) return nullptr;
    CombatTarget=Candidate; UE_LOG(LogTemp,Log,TEXT("[RathianApprox] acquired %s dist=%.0f angle=%.0f"),*Candidate->GetName(),To.Size2D(),Angle); return Candidate;
}

void AMHWIRathianApproxPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds); const float Dt=FMath::Clamp(DeltaSeconds,0.f,0.1f);
    if (!bConfigured) ConfigureApprox(); TickDisplay(Dt);
    if (ExecState==EExecState::Dead) { if (bFlightActive) TickEmergencyLanding(Dt); return; }
    if (bEmergencyLanding) { TickEmergencyLanding(Dt); return; }
    if (!ActiveStats) return;
    AActor* Target=FindOrAcquireTarget(); if (Decision) Decision->SetTarget(Target);
    if (ExecState==EExecState::Attack) { TickAttack(Dt); return; }
    if (Target) TickCombat(Dt); else TickPatrol(Dt);
    StateElapsed+=Dt;
}

void AMHWIRathianApproxPawn::TickDisplay(float DeltaSeconds)
{
    DisplayAccumulator+=DeltaSeconds; if (DisplayAccumulator<0.2f) return; DisplayAccumulator=0.f;
    if (HealthDisplay&&Attributes) HealthDisplay->SetText(FText::FromString(FString::Printf(TEXT("HP %.0f / %.0f"),Attributes->CurrentHealth,Attributes->MaxHealth)));
}

void AMHWIRathianApproxPawn::TickPatrol(float DeltaSeconds)
{
    ExecState = EExecState::Patrol;
    if (!ActiveStats||ActiveStats->PatrolRadiusCm<=0.f) { CurrentMovementSpeed=0.f; UpdateLocomotionBlend(0.f); return; }
    if (FVector::Dist2D(GetActorLocation(),PatrolGoal)<90.f)
        PatrolGoal=PatrolOrigin+FMath::VRand().GetSafeNormal2D()*FMath::FRandRange(200.f,ActiveStats->PatrolRadiusCm);
    const FVector Dir=(PatrolGoal-GetActorLocation()).GetSafeNormal2D();
    if (!Dir.IsNearlyZero()) SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(),Dir.Rotation(),DeltaSeconds,ActiveStats->TurnSpeedDegPerSecond));
    const float Step=BoundedMovementDelta(ResolvePatrolSpeed(ActiveStats),DeltaSeconds);
    const FVector Before=GetActorLocation(); MoveSwept(Dir*Step,DeltaSeconds);
    CurrentMovementSpeed=FVector::Dist2D(Before,GetActorLocation())/FMath::Max(DeltaSeconds,KINDA_SMALL_NUMBER); UpdateLocomotionBlend(CurrentMovementSpeed);
}

const FMHWIRathianApproxMove* AMHWIRathianApproxPawn::FindMove(const FString& Name) const
{
    if (MovesetData) for (const FMHWIRathianApproxMove& M:MovesetData->Moves) if (M.RegistryName==Name) return &M;
    return nullptr;
}

bool AMHWIRathianApproxPawn::IsMoveConfigured(const FMHWIRathianApproxMove& Move) const
{
    if (Move.Kind != EMHWIRathianApproxMoveKind::Attack || Move.AnimQualification == EMHWIRathianApproxQualification::Unavailable) return false;
    if (Move.Phases.IsEmpty())
        return !Move.Animation.IsNull() && Move.AttackWindowQualification != EMHWIRathianApproxQualification::Unavailable && Move.AttackRangeCm > 0.f;
    bool bHasEffect = false;
    bool bHasTakeoff = false;
    bool bHasLanding = false;
    float TakeoffHeight = 0.f;
    for (const FMHWIRathianAttackPhase& Phase : Move.Phases)
    {
        if (Phase.Animation.IsNull()) return false;
        if (Phase.bAttackWindowEnabled)
        {
            const bool bWindowValid = Phase.bUseLegacySecondsWindow
                ? Phase.WindowStartSeconds >= 0.f && Phase.WindowEndSeconds > Phase.WindowStartSeconds
                : Phase.WindowStart >= 0.f && Phase.WindowEnd > Phase.WindowStart && Phase.WindowEnd <= 1.f;
            if (!bWindowValid || Phase.WindowQualification == EMHWIRathianApproxQualification::Unavailable) return false;
            bHasEffect |= !Phase.HitBoxes.IsEmpty();
        }
        if (Phase.bSpawnFireballAtStart)
        {
            if (Phase.FireballSocketName.IsNone() || Phase.FireballSpawnQualification == EMHWIRathianApproxQualification::Unavailable) return false;
            bHasEffect = true;
        }
        if (Phase.Kind == EMHWIRathianAttackPhaseKind::TailTakeoff)
        { bHasTakeoff = true; TakeoffHeight = Phase.TakeoffHeightCm; }
        if (Phase.Kind == EMHWIRathianAttackPhaseKind::TailLanding) bHasLanding = true;
    }
    if (Move.RegistryName.StartsWith(TEXT("ACTION::ROLLING_TAIL_ATTACK2")) && (!bHasTakeoff || !bHasLanding || TakeoffHeight <= 0.f)) return false;
    return bHasEffect;
}
void AMHWIRathianApproxPawn::TickCombat(float DeltaSeconds)
{
    if (!Decision || !CombatTarget.IsValid())
    {
        CurrentMovementSpeed = 0.f;
        UpdateLocomotionBlend(0.f);
        return;
    }
    Dispatch(Decision->Evaluate());
    (void)DeltaSeconds;
}

void AMHWIRathianApproxPawn::Dispatch(const FMHWIRathianActionRequest& Request)
{
    AActor* Target = CombatTarget.Get();
    switch (Request.Kind)
    {
    case EMHWIRathianApproxMoveKind::Attack:
        if (!RequestBasicAttack(Request.RegistryName))
        {
            if (Decision) Decision->NotifyMoveRejected(Request.RegistryName);
            ExecState = EExecState::Approach;
        }
        break;
    case EMHWIRathianApproxMoveKind::Turn:
        ExecState = EExecState::Turn;
        FaceTarget(Target, GetWorld() ? GetWorld()->GetDeltaSeconds() : 0.016f,
            ActiveStats ? ActiveStats->TurnSpeedDegPerSecond : 180.f);
        CurrentMovementSpeed = 0.f;
        UpdateLocomotionBlend(0.f);
        break;
    case EMHWIRathianApproxMoveKind::Locomotion:
    {
        ExecState = EExecState::Approach;
        if (!Target) break;
        FaceTarget(Target, GetWorld() ? GetWorld()->GetDeltaSeconds() : 0.016f,
            ActiveStats ? ActiveStats->TurnSpeedDegPerSecond : 180.f);
        const FVector ToTarget = Target->GetActorLocation() - GetActorLocation();
        const float Distance = ToTarget.Size2D();
        const float Desired = Request.DesiredStopDistanceCm > 0.f ? Request.DesiredStopDistanceCm : 260.f;
        if (Distance > Desired + 45.f || Distance < Desired - 70.f)
        {
            const FVector Direction = ToTarget.GetSafeNormal2D() * (Distance > Desired ? 1.f : -1.f);
            const FVector Before = GetActorLocation();
            const float DeltaSeconds=GetWorld()->GetDeltaSeconds();
            const float SpeedMultiplier=ApproxState->GetSpeedMultiplier();
            const double ApproachSpeed=ResolveApproachSpeed(ActiveStats)*(FMath::IsFinite(SpeedMultiplier)?FMath::Max(0.f,SpeedMultiplier):0.f);
            MoveSwept(Direction*BoundedMovementDelta(ApproachSpeed,DeltaSeconds),DeltaSeconds);
            CurrentMovementSpeed = FVector::Dist2D(Before, GetActorLocation()) / FMath::Max(DeltaSeconds, KINDA_SMALL_NUMBER);
        }
        else CurrentMovementSpeed = 0.f;
        UpdateLocomotionBlend(CurrentMovementSpeed);
        break;
    }
    case EMHWIRathianApproxMoveKind::Idle:
    default:
        ExecState = EExecState::Approach;
        CurrentMovementSpeed = 0.f;
        UpdateLocomotionBlend(0.f);
        break;
    }
}
bool AMHWIRathianApproxPawn::RequestBasicAttack(const FString& Name)
{
    check(IsInGameThread());
    if (ExecState==EExecState::Dead||ExecState==EExecState::Attack||bEmergencyLanding||!Attributes||!Attributes->IsAlive()) return false;
    const FMHWIRathianApproxMove* M=FindMove(Name);
    if (!M||!IsMoveConfigured(*M))
    { UE_LOG(LogTemp,Warning,TEXT("[RathianApprox] reject attack '%s': busy/dead/unconfigured"),*Name); return false; }
    const USkeleton* Skeleton=Body->GetSkeletalMeshAsset()?Body->GetSkeletalMeshAsset()->GetSkeleton():nullptr;
    auto Valid=[Skeleton](const TSoftObjectPtr<UAnimSequence>& Soft)
    { UAnimSequence* S=Soft.LoadSynchronous(); return S&&(!Skeleton||S->GetSkeleton()==Skeleton); };
    if (M->Phases.IsEmpty()) { if (!Valid(M->Animation)) return false; }
    else for (const FMHWIRathianAttackPhase& P:M->Phases)
    {
        UAnimSequence* PhaseSequence=P.Animation.LoadSynchronous();
        if (!PhaseSequence||!Skeleton||PhaseSequence->GetSkeleton()!=Skeleton) { UE_LOG(LogTemp,Error,TEXT("[RathianApprox] reject %s: missing or skeleton-mismatched phase %s"),*Name,*P.Animation.ToString()); return false; }
        if (P.bAttackWindowEnabled&&P.bUseLegacySecondsWindow&&P.WindowEndSeconds>PhaseSequence->GetPlayLength()) return false;
        if (P.bAttackWindowEnabled)
            for (const FMHWIRathianAttackBox& Box:P.HitBoxes)
                if (Box.BoneName.IsNone()||!Body->DoesSocketExist(Box.BoneName)) return false;
        if (P.bSpawnFireballAtStart&&(P.FireballSocketName.IsNone()||!Body->DoesSocketExist(P.FireballSocketName))) return false;
    }
    ActiveMove=*M; ++CurrentRunId; ++ActivePhaseEpoch; ActivePhaseIndex=INDEX_NONE; StateElapsed=0.f; PhaseHitActors.Reset(); PreviousBoxTransforms.Reset(); bHasPreviousBoxSamples=false; bFlightActive=false; bFlightBlocked=false; bEmergencyLanding=false; bPhaseMontageEnded=false; bPhaseMontageInterrupted=false; ExecState=EExecState::Attack; bPhaseFacingLocked=false;
    if (ActiveMove.Phases.IsEmpty())
    {
        UAnimSequence* S=ActiveMove.Animation.LoadSynchronous(); FMHWIRathianAttackPhase P; P.Kind=EMHWIRathianAttackPhaseKind::Active; P.Animation=ActiveMove.Animation;
        P.bAttackWindowEnabled=true; P.bUseLegacySecondsWindow=true;
        P.WindowStartSeconds=ActiveMove.AttackWindowStartSeconds; P.WindowEndSeconds=ActiveMove.AttackWindowEndSeconds;
        P.Damage=ActiveMove.DamageProxyMotionValue; P.HitBoxes.Add(FMHWIRathianAttackBox()); ActiveMove.Phases.Add(P);
    }
    UE_LOG(LogTemp,Log,TEXT("[RathianApprox] attack run=%llu name=%s phases=%d"),CurrentRunId,*Name,ActiveMove.Phases.Num());
    StartPhase(0); return ExecState==EExecState::Attack;
}

void AMHWIRathianApproxPawn::StartPhase(int32 Index)
{
    if (!ActiveMove.Phases.IsValidIndex(Index)) { FinishMove(); return; }
    ActivePhaseIndex=Index; FMHWIRathianAttackPhase& P=ActiveMove.Phases[Index]; ActiveSequence=P.Animation.LoadSynchronous();
    if (!ActiveSequence) { UE_LOG(LogTemp,Error,TEXT("[RathianApprox] missing sequence phase %d"),Index); FinishMove(); return; }
    if (P.bAttackWindowEnabled && P.bUseLegacySecondsWindow)
    {
        const float Length=FMath::Max(0.001f,ActiveSequence->GetPlayLength());
        P.WindowStart=FMath::Clamp(P.WindowStartSeconds/Length,0.f,1.f);
        P.WindowEnd=FMath::Clamp(P.WindowEndSeconds/Length,P.WindowStart,1.f);
    }
    ActiveMontage=GetOrBuildMontage(ActiveSequence,P.BlendInSeconds,P.BlendOutSeconds);
    UAnimInstance* Anim=Body?Body->GetAnimInstance():nullptr;
    if (!Anim||!ActiveMontage||Anim->Montage_Play(ActiveMontage,1.f,EMontagePlayReturnType::Duration)<=0.f) { FinishMove(); return; }
    FAnimMontageInstance* MontageInstance=Anim->GetActiveInstanceForMontage(ActiveMontage);
    if (!MontageInstance) { FinishMove(); return; }
    const uint64 PhaseEpoch=++ActivePhaseEpoch; const uint64 RunEpoch=CurrentRunId; const int32 MontageInstanceId=MontageInstance->GetInstanceID(); UAnimMontage* PhaseMontage=ActiveMontage;
    ActiveMontageInstanceId=MontageInstanceId;
    bPhaseMontageEnded=false; bPhaseMontageInterrupted=false; bPhaseBlendOutStarted=false; bPhaseBlendOutInterrupted=false;
    FOnMontageBlendingOutStarted BlendDelegate;
    BlendDelegate.BindWeakLambda(this,[this,RunEpoch,PhaseEpoch,MontageInstanceId,PhaseMontage](UAnimMontage* BlendingMontage,bool bInterrupted)
    {
        if (CurrentRunId!=RunEpoch||ActivePhaseEpoch!=PhaseEpoch||ActiveMontageInstanceId!=MontageInstanceId||ActiveMontage!=PhaseMontage||BlendingMontage!=PhaseMontage) return;
        bPhaseBlendOutStarted=true; bPhaseBlendOutInterrupted=bInterrupted;
    });
    Anim->Montage_SetBlendingOutDelegate(BlendDelegate,PhaseMontage);
    FOnMontageEnded EndDelegate;
    EndDelegate.BindWeakLambda(this,[this,RunEpoch,PhaseEpoch,MontageInstanceId,PhaseMontage](UAnimMontage* EndedMontage,bool bInterrupted)
    {
        if (CurrentRunId!=RunEpoch||ActivePhaseEpoch!=PhaseEpoch||ActiveMontageInstanceId!=MontageInstanceId||ActiveMontage!=PhaseMontage||EndedMontage!=PhaseMontage) return;
        bPhaseMontageEnded=true; bPhaseMontageInterrupted=bInterrupted;
    });
    Anim->Montage_SetEndDelegate(EndDelegate,PhaseMontage);
    PhasePreviousPosition=0.f; StateElapsed=0.f; PhaseHitActors.Reset(); PreviousBoxTransforms.SetNum(P.HitBoxes.Num()); bHasPreviousBoxSamples=true;
    for (int32 BoxIndex=0;BoxIndex<P.HitBoxes.Num();++BoxIndex)
    {
        const FMHWIRathianAttackBox& Box=P.HitBoxes[BoxIndex];
        if (!Box.BoneName.IsNone()&&Body->DoesSocketExist(Box.BoneName))
        {
            const FTransform Bone=Body->GetSocketTransform(Box.BoneName,RTS_World);
            PreviousBoxTransforms[BoxIndex]=FTransform(Bone.GetRotation()*Box.LocalRotation.Quaternion(),Bone.TransformPosition(Box.LocalOffsetCm));
        }
    }
    bPhaseFacingLocked=P.Kind!=EMHWIRathianAttackPhaseKind::Windup; bSpawnedProjectileThisPhase=false;
    if (P.Kind==EMHWIRathianAttackPhaseKind::TailTakeoff && (Index==0||ActiveMove.Phases[Index-1].Kind!=EMHWIRathianAttackPhaseKind::TailTakeoff)) { FlightGroundZ=GetActorLocation().Z; bFlightActive=true; bFlightBlocked=false; }
    if (P.Kind==EMHWIRathianAttackPhaseKind::TailLanding) FlightStartZ=GetActorLocation().Z;
    AActor* FireballTarget=CombatTarget.Get();
    const UAttributeComponent* FireballTargetAttributes=IsValid(FireballTarget)?FireballTarget->FindComponentByClass<UAttributeComponent>():nullptr;
    if (P.bSpawnFireballAtStart && P.FireballSpawnTimeSeconds<=0.f && ExecState==EExecState::Attack && Attributes && Attributes->IsAlive() && IsValid(FireballTarget) && (!FireballTargetAttributes||FireballTargetAttributes->IsAlive()))
    { SpawnFireball(P); bSpawnedProjectileThisPhase=true; }
    UE_LOG(LogTemp,Verbose,TEXT("[RathianApprox][Window] run=%llu phase=%d kind=%d normalized=[%.2f,%.2f]"),CurrentRunId,Index,(int32)P.Kind,P.WindowStart,P.WindowEnd);
}

void AMHWIRathianApproxPawn::TickAttack(float DeltaSeconds)
{
    if (!ActiveMove.Phases.IsValidIndex(ActivePhaseIndex)) { FinishMove(); return; }
    UAnimInstance* Anim=Body?Body->GetAnimInstance():nullptr; const FMHWIRathianAttackPhase& P=ActiveMove.Phases[ActivePhaseIndex];
    if (bFlightActive&&(bFlightBlocked||!CombatTarget.IsValid())) { BeginEmergencyLanding(); return; }
    if (!CombatTarget.IsValid()) { FinishMove(); return; }
    if (!Anim||!ActiveMontage) { if (bFlightActive) BeginEmergencyLanding(); else FinishMove(); return; }
    auto SpawnFireballIfCrossed=[this,&P](float CurrentPosition)
    {
        if (!P.bSpawnFireballAtStart||bSpawnedProjectileThisPhase||!FMath::IsFinite(P.FireballSpawnTimeSeconds)||P.FireballSpawnTimeSeconds<=0.f||!ActiveSequence||ExecState!=EExecState::Attack||!Attributes||!Attributes->IsAlive()) return;
        AActor* Target=CombatTarget.Get();
        if (!IsValid(Target)) return;
        const UAttributeComponent* TargetAttributes=Target->FindComponentByClass<UAttributeComponent>();
        if (TargetAttributes&&!TargetAttributes->IsAlive()) return;
        const float SequenceLength=ActiveSequence->GetPlayLength();
        if (!FMath::IsFinite(SequenceLength)||SequenceLength<=0.f) return;
        const float PreviousSeconds=FMath::Clamp(PhasePreviousPosition,0.f,1.f)*SequenceLength;
        const float CurrentSeconds=FMath::Clamp(CurrentPosition,0.f,1.f)*SequenceLength;
        if (PreviousSeconds<P.FireballSpawnTimeSeconds&&CurrentSeconds>=P.FireballSpawnTimeSeconds)
        { SpawnFireball(P); bSpawnedProjectileThisPhase=true; }
    };
    if (bPhaseBlendOutStarted||bPhaseMontageEnded)
    {
        if (bPhaseBlendOutInterrupted||bPhaseMontageInterrupted)
        {
            if (bFlightActive) BeginEmergencyLanding(); else FinishMove();
            return;
        }
        TickFlightPhase(1.f,DeltaSeconds);
        if (bFlightBlocked&&bFlightActive) { BeginEmergencyLanding(); return; }
        ApplyAttackWindow(PhasePreviousPosition,1.f);
        if (ExecState==EExecState::Dead) return;
        SpawnFireballIfCrossed(1.f);
        PhasePreviousPosition=1.f;
        AdvancePhase();
        return;
    }
    if (!Anim->Montage_IsPlaying(ActiveMontage))
    {
        if (!ActiveSequence||StateElapsed>ActiveSequence->GetPlayLength()+2.f) { if (bFlightActive) BeginEmergencyLanding(); else FinishMove(); }
        return;
    }
    const float Len=FMath::Max(0.001f,ActiveMontage->GetPlayLength());
    const float Pos=FMath::Clamp(Anim->Montage_GetPosition(ActiveMontage)/Len,0.f,1.f);
    if (!bPhaseFacingLocked&&CombatTarget.IsValid()) FaceTarget(CombatTarget.Get(),DeltaSeconds,ActiveStats->TurnSpeedDegPerSecond);
    if (P.MoveSpeedCmPerSecond>0.f&&P.Kind!=EMHWIRathianAttackPhaseKind::TailLanding)
        MoveSwept(GetActorForwardVector()*P.MoveSpeedCmPerSecond*DeltaSeconds,DeltaSeconds);
    TickFlightPhase(Pos,DeltaSeconds);
    if (bFlightBlocked&&bFlightActive) { BeginEmergencyLanding(); return; }
    ApplyAttackWindow(PhasePreviousPosition,Pos);
    if (ExecState==EExecState::Dead) return;
    SpawnFireballIfCrossed(Pos);
    CurrentMovementSpeed=P.MoveSpeedCmPerSecond; UpdateLocomotionBlend(CurrentMovementSpeed);
    PhasePreviousPosition=Pos; StateElapsed+=DeltaSeconds;
}

void AMHWIRathianApproxPawn::ApplyAttackWindow(float PreviousPosition,float CurrentPosition)
{
    if (!GetWorld()||!Body||!ActiveMove.Phases.IsValidIndex(ActivePhaseIndex)) return;
    const FMHWIRathianAttackPhase& P=ActiveMove.Phases[ActivePhaseIndex];
    const float ClipStart=FMath::Max(PreviousPosition,P.WindowStart), ClipEnd=FMath::Min(CurrentPosition,P.WindowEnd);
    const bool bWindowOverlap=P.bAttackWindowEnabled && ClipEnd>=ClipStart && CurrentPosition>=PreviousPosition;
    if (bWindowOverlap) bPhaseFacingLocked=true;
    for (int32 I=0;I<P.HitBoxes.Num();++I)
    {
        const FMHWIRathianAttackBox& B=P.HitBoxes[I];
        if (!Body->DoesSocketExist(B.BoneName)) { UE_LOG(LogTemp,Warning,TEXT("[RathianApprox] missing hitbox bone/socket %s"),*B.BoneName.ToString()); continue; }
        const FTransform Bone=Body->GetSocketTransform(B.BoneName,RTS_World);
        const FTransform Curr(Bone.GetRotation()*B.LocalRotation.Quaternion(),Bone.TransformPosition(B.LocalOffsetCm));
        const FTransform Prev=bHasPreviousBoxSamples&&PreviousBoxTransforms.IsValidIndex(I)?PreviousBoxTransforms[I]:Curr;
        if (!bWindowOverlap) { PreviousBoxTransforms[I]=Curr; continue; }
        const float Span=FMath::Max(KINDA_SMALL_NUMBER,CurrentPosition-PreviousPosition);
        const float AlphaStart=FMath::Clamp((ClipStart-PreviousPosition)/Span,0.f,1.f), AlphaEnd=FMath::Clamp((ClipEnd-PreviousPosition)/Span,0.f,1.f);
        const FTransform WindowPrev(FQuat::Slerp(Prev.GetRotation(),Curr.GetRotation(),AlphaStart),FMath::Lerp(Prev.GetLocation(),Curr.GetLocation(),AlphaStart));
        const FTransform WindowCurr(FQuat::Slerp(Prev.GetRotation(),Curr.GetRotation(),AlphaEnd),FMath::Lerp(Prev.GetLocation(),Curr.GetLocation(),AlphaEnd));
        const float Degrees=FMath::RadiansToDegrees(WindowPrev.GetRotation().AngularDistance(WindowCurr.GetRotation()));
        const float Travel=FVector::Distance(WindowPrev.GetLocation(),WindowCurr.GetLocation());
        const float Ext=FMath::Max(10.f,FMath::Min3(B.HalfExtentCm.X,B.HalfExtentCm.Y,B.HalfExtentCm.Z));
        const int32 Steps=FMath::Clamp(FMath::Max(FMath::CeilToInt(Degrees/10.f),FMath::CeilToInt(Travel/(Ext*0.5f))),1,16);
        FCollisionQueryParams Params(SCENE_QUERY_STAT(RathianAttackBox),false,this); TArray<FHitResult> Hits; bool bWorldBlocked=false;
        for (int32 Step=1;Step<=Steps&&!bWorldBlocked;++Step)
        {
            const float A=(float)Step/Steps, PrevA=(float)(Step-1)/Steps;
            const FVector Start=FMath::Lerp(WindowPrev.GetLocation(),WindowCurr.GetLocation(),PrevA), End=FMath::Lerp(WindowPrev.GetLocation(),WindowCurr.GetLocation(),A);
            const FQuat Rot=FQuat::Slerp(WindowPrev.GetRotation(),WindowCurr.GetRotation(),A);
            Hits.Reset(); GetWorld()->SweepMultiByChannel(Hits,Start,End,Rot,ECC_Pawn,FCollisionShape::MakeBox(B.HalfExtentCm),Params);
            Hits.Sort([](const FHitResult& X,const FHitResult& Y){return X.Time<Y.Time;});
            for (const FHitResult& H:Hits)
            {
                AActor* Other=H.GetActor();
                if (H.bBlockingHit&&H.Component.IsValid()&&H.Component->GetCollisionObjectType()==ECC_WorldStatic) { bWorldBlocked=true; break; }
                if (!Other||Other==this) continue;
                const TWeakObjectPtr<AActor> WeakOther(Other);
                if (PhaseHitActors.Contains(WeakOther)) continue;
                UAttributeComponent* Attr=Other->FindComponentByClass<UAttributeComponent>(); if (!Attr||!Attr->IsAlive()) continue;
                if (!HasAttackLineOfSight(Other,Start)) continue;
                PhaseHitActors.Add(WeakOther); const TWeakObjectPtr<UAttributeComponent> WeakAttr(Attr); const float Before=Attr->CurrentHealth;
                Attr->ApplyDamage(P.Damage*ApproxState->GetDamageMultiplier(),this);
                if (ExecState==EExecState::Dead) return;
                AActor* SafeOther=WeakOther.Get(); Attr=WeakAttr.Get();
                if (!IsValid(SafeOther)||!IsValid(Attr)) continue;
                if (Attr->CurrentHealth<Before&&Attr->IsAlive())
                    if (ACharacter* Character=Cast<ACharacter>(Other))
                    { const AMHWICharacter* MHWI=Cast<AMHWICharacter>(SafeOther); if (!MHWI||MHWI->GetCounterArmorRemaining()<=0.f) { const FVector Away=(SafeOther->GetActorLocation()-GetActorLocation()).GetSafeNormal2D(); Character->LaunchCharacter(Away*P.KnockbackVelocity.Size2D()+FVector(0,0,P.KnockbackVelocity.Z),true,true); } }
                UE_LOG(LogTemp,Log,TEXT("[RathianApprox] hit run=%llu phase=%d target=%s hp %.1f->%.1f"),CurrentRunId,ActivePhaseIndex,*SafeOther->GetName(),Before,Attr->CurrentHealth);
            }
        }
        PreviousBoxTransforms[I]=Curr;
        if (CVarRathianDebugBoxes.GetValueOnGameThread()) DrawDebugBox(GetWorld(),Curr.GetLocation(),B.HalfExtentCm,Curr.GetRotation(),FColor::Red,false,0.05f,0,2.f);
    }
    bHasPreviousBoxSamples=true;
}

void AMHWIRathianApproxPawn::TickFlightPhase(float NormalizedPosition,float)
{
    if (!ActiveMove.Phases.IsValidIndex(ActivePhaseIndex)) return;
    const FMHWIRathianAttackPhase& P=ActiveMove.Phases[ActivePhaseIndex]; const float A=FMath::Clamp(NormalizedPosition,0.f,1.f), S=A*A*(3.f-2.f*A);
    const FVector L=GetActorLocation();
    if (P.Kind==EMHWIRathianAttackPhaseKind::TailTakeoff)
    { const float Height=P.TakeoffHeightCm; if (Height>0.f) SetFlightHeightSwept(FlightGroundZ+Height*S); }
    else if (P.Kind==EMHWIRathianAttackPhaseKind::TailLanding)
    {
        const float Ground=FMath::Min(FlightGroundZ,FlightStartZ);
        if (SetFlightHeightSwept(FMath::Lerp(FlightStartZ,Ground,S))&&A>=0.999f)
        {
            FHitResult GroundHit; FCollisionQueryParams Params(SCENE_QUERY_STAT(RathianLandingConfirm),false,this);
            const FVector Here=GetActorLocation();
            const float FootProbeDepth=HitProxy->GetScaledSphereRadius()+GroundClearanceCm+20.f;
            if (GetWorld()->LineTraceSingleByChannel(GroundHit,Here+FVector(0,0,10),Here-FVector(0,0,FootProbeDepth),ECC_WorldStatic,Params))
            {
                const float GroundRootZ=GroundHit.ImpactPoint.Z+HitProxy->GetScaledSphereRadius()+GroundClearanceCm;
                if (FMath::Abs(Here.Z-GroundRootZ)<=8.f)
                {
                    FHitResult ClearanceHit;
                    SetActorLocation(FVector(Here.X,Here.Y,GroundRootZ),true,&ClearanceHit);
                    const float AlignedZ=GetActorLocation().Z;
                    const bool bWithinLandingTolerance=FMath::Abs(AlignedZ-GroundRootZ)<=3.f;
                    const bool bRetainsFullFloorGap=AlignedZ>=GroundRootZ;
                    if (bWithinLandingTolerance&&bRetainsFullFloorGap) { bFlightActive=false; FlightGroundZ=GroundRootZ; }
                }
            }
        }
    }
}

void AMHWIRathianApproxPawn::AdvancePhase()
{
    const int32 Next=ActivePhaseIndex+1;
    if (ActiveMove.Phases.IsValidIndex(Next))
    { if (ActiveMove.Phases[Next].Kind==EMHWIRathianAttackPhaseKind::TailLanding) FlightStartZ=GetActorLocation().Z; StartPhase(Next); }
    else { if (bFlightActive) BeginEmergencyLanding(); else FinishMove(); }
}

void AMHWIRathianApproxPawn::SpawnFireball(const FMHWIRathianAttackPhase& P)
{
    if (!GetWorld()||!CombatTarget.IsValid()||!Body||P.FireballSocketName.IsNone()||!Body->DoesSocketExist(P.FireballSocketName)) return;
    const FTransform Socket=Body->GetSocketTransform(P.FireballSocketName,RTS_World);
    const FTransform SpawnTransform=FTransform(Socket.GetRotation(),Socket.TransformPosition(P.FireballLocalOffsetCm));
    FActorSpawnParameters Params; Params.Owner=this; Params.Instigator=this; Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AMHWIRathianApproxFireball* Projectile=GetWorld()->SpawnActorDeferred<AMHWIRathianApproxFireball>(AMHWIRathianApproxFireball::StaticClass(),SpawnTransform,this,this,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Projectile) return;
    Projectile->InitializeProjectile(this,CombatTarget.Get(),P.Damage,P.KnockbackVelocity,P.ImpactSize);
    Projectile->FinishSpawning(SpawnTransform);
    OwnerProjectiles.Add(Projectile);
}


void AMHWIRathianApproxPawn::FinishMove()
{
    if (bFlightActive||bEmergencyLanding) return;
    ++ActivePhaseEpoch;
    if (UAnimInstance* Anim=Body?Body->GetAnimInstance():nullptr;Anim&&ActiveMontage&&Anim->Montage_IsPlaying(ActiveMontage)) Anim->Montage_Stop(0.05f,ActiveMontage);
    const FString Name=ActiveMove.RegistryName;
    if (!Name.IsEmpty())
    {
        if (Decision) Decision->NotifyMoveFinished(Name);
    }
    ActiveSequence=nullptr; ActiveMontage=nullptr; ActiveMontageInstanceId=INDEX_NONE; ActiveMove=FMHWIRathianApproxMove(); ActivePhaseIndex=INDEX_NONE;
    PreviousBoxTransforms.Reset(); PhaseHitActors.Reset(); bHasPreviousBoxSamples=false; bPhaseMontageEnded=false; bPhaseMontageInterrupted=false; bPhaseBlendOutStarted=false; bPhaseBlendOutInterrupted=false; CurrentMovementSpeed=0.f;
    ExecState=CombatTarget.IsValid()?EExecState::Approach:EExecState::Patrol; UpdateLocomotionBlend(0.f);
}

UAnimMontage* AMHWIRathianApproxPawn::GetOrBuildMontage(UAnimSequence* Sequence,float BlendIn,float BlendOut)
{
    if (!Sequence) return nullptr;
    const FString CacheKey=FString::Printf(TEXT("%s|%.6f|%.6f"),*Sequence->GetPathName(),BlendIn,BlendOut);
    if (TObjectPtr<UAnimMontage>* Found=RuntimeMontages.Find(CacheKey)) return *Found;
    UAnimMontage* Montage=UAnimMontage::CreateSlotAnimationAsDynamicMontage(Sequence,TEXT("DefaultSlot"),BlendIn,BlendOut,1.f,1,0.f);
    if (!Montage) return nullptr;
    Montage->BlendIn.SetBlendTime(BlendIn); Montage->BlendOut.SetBlendTime(BlendOut); Montage->BlendOutTriggerTime=0.f;
    RuntimeMontages.Add(CacheKey,Montage); return Montage;
}

void AMHWIRathianApproxPawn::MoveSwept(FVector Delta,float DeltaSeconds)
{
    const float MaxStep=250.f;
    Delta=Delta.GetClampedToMaxSize(FMath::Max(10.f,MaxStep)); FHitResult Hit; SetActorLocation(GetActorLocation()+Delta,true,&Hit);
    const bool bAir=bFlightActive||(ActiveMove.Phases.IsValidIndex(ActivePhaseIndex)&&(ActiveMove.Phases[ActivePhaseIndex].Kind==EMHWIRathianAttackPhaseKind::TailTakeoff||ActiveMove.Phases[ActivePhaseIndex].Kind==EMHWIRathianAttackPhaseKind::TailLanding));
    if (!bAir) KeepOnGround();
    if (Hit.bBlockingHit&&Hit.GetActor()&&Hit.GetActor()!=CombatTarget.Get()) UE_LOG(LogTemp,VeryVerbose,TEXT("[RathianApprox] movement blocked by %s"),*Hit.GetActor()->GetName());
}

void AMHWIRathianApproxPawn::KeepOnGround()
{
    if (!GetWorld()||!HitProxy) return;
    FHitResult H; FCollisionQueryParams P(SCENE_QUERY_STAT(RathianGround),false,this);
    if (GetWorld()->LineTraceSingleByChannel(H,GetActorLocation()+FVector(0,0,400),GetActorLocation()-FVector(0,0,4000),ECC_WorldStatic,P))
        SetActorLocation(FVector(GetActorLocation().X,GetActorLocation().Y,H.ImpactPoint.Z+HitProxy->GetScaledSphereRadius()+GroundClearanceCm),true);
}

bool AMHWIRathianApproxPawn::SetFlightHeightSwept(float TargetZ)
{
    const FVector Here=GetActorLocation(); FHitResult Hit;
    SetActorLocation(FVector(Here.X,Here.Y,TargetZ),true,&Hit);
    if (Hit.bBlockingHit)
    {
        const bool bStaticGround=Hit.Component.IsValid()&&Hit.Component->GetCollisionObjectType()==ECC_WorldStatic;
        const bool bGroundContact=bStaticGround&&TargetZ<Here.Z&&Hit.ImpactNormal.Z>0.5f;
        if (!bGroundContact) bFlightBlocked=true;
        return bGroundContact;
    }
    return true;
}

void AMHWIRathianApproxPawn::BeginEmergencyLanding()
{
    if (!bFlightActive||bEmergencyLanding||ExecState==EExecState::Dead) return;
    bEmergencyLanding=true; bPhaseMontageEnded=false; bPhaseMontageInterrupted=true; bPhaseBlendOutStarted=false; bPhaseBlendOutInterrupted=true; bPhaseFacingLocked=true;
    for (FMHWIRathianAttackPhase& Phase:ActiveMove.Phases) Phase.bAttackWindowEnabled=false;
    ++ActivePhaseEpoch;
    if (UAnimInstance* Anim=Body?Body->GetAnimInstance():nullptr;Anim&&ActiveMontage) Anim->Montage_Stop(0.05f,ActiveMontage);
    ActiveMontage=nullptr; ActiveMontageInstanceId=INDEX_NONE; ActiveSequence=nullptr; CurrentMovementSpeed=0.f;
    for (AMHWIRathianApproxFireball* Projectile:OwnerProjectiles) if (IsValid(Projectile)) Projectile->Destroy();
    OwnerProjectiles.Reset();
    ExecState=EExecState::Landing;
    UpdateLocomotionBlend(0.f);
    UE_LOG(LogTemp,Warning,TEXT("[RathianApprox] run=%llu interrupted in flight; entering swept emergency landing"),CurrentRunId);
}

void AMHWIRathianApproxPawn::TickEmergencyLanding(float DeltaSeconds)
{
    if (!bFlightActive)
    {
        bEmergencyLanding=false;
        if (ExecState!=EExecState::Dead) FinishMove();
        return;
    }
    if (!GetWorld()||!HitProxy) return;
    FHitResult Ground; FCollisionQueryParams Params(SCENE_QUERY_STAT(RathianEmergencyLanding),false,this);
    const FVector Here=GetActorLocation();
    float GroundZ=FlightGroundZ; bool bFoundGround=false;
    const FVector Start=Here+FVector(0,0,100.f), End=Here-FVector(0,0,6000.f);
    if (GetWorld()->LineTraceSingleByChannel(Ground,Start,End,ECC_WorldStatic,Params))
    { GroundZ=Ground.ImpactPoint.Z+HitProxy->GetScaledSphereRadius()+GroundClearanceCm; bFoundGround=true; }
    const float Step=FMath::Max(1.f,800.f*FMath::Clamp(DeltaSeconds,0.f,0.1f));
    const float TargetZ=FMath::Max(GroundZ,Here.Z-Step);
    FHitResult Hit;
    SetActorLocation(FVector(Here.X,Here.Y,TargetZ),true,&Hit);
    const bool bStaticGround=Hit.Component.IsValid()&&Hit.Component->GetCollisionObjectType()==ECC_WorldStatic;
    const bool bContact=Hit.bBlockingHit&&bStaticGround&&Hit.ImpactNormal.Z>0.45f;
    if (bContact&&!bFoundGround)
    {
        GroundZ=Hit.ImpactPoint.Z+HitProxy->GetScaledSphereRadius()+GroundClearanceCm;
        bFoundGround=true;
    }
    if (bContact&&bFoundGround)
    {
        const FVector ContactLocation=GetActorLocation(); FHitResult ClearanceHit;
        SetActorLocation(FVector(ContactLocation.X,ContactLocation.Y,GroundZ),true,&ClearanceHit);
    }
    const float AlignedZ=GetActorLocation().Z;
    const bool bWithinLandingTolerance=FMath::Abs(AlignedZ-GroundZ)<=3.f;
    const bool bRetainsFullFloorGap=AlignedZ>=GroundZ;
    const bool bAtGround=bFoundGround&&bWithinLandingTolerance&&bRetainsFullFloorGap;
    if (bAtGround)
    {
        bFlightActive=false; bEmergencyLanding=false; bFlightBlocked=false; FlightGroundZ=GroundZ;
        if (ExecState!=EExecState::Dead) FinishMove();
    }
}

bool AMHWIRathianApproxPawn::HasAttackLineOfSight(AActor* Target,const FVector& BoxOrigin) const
{
    if (!IsValid(Target)||!GetWorld()) return false;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(RathianAttackLOS),false,this); Params.AddIgnoredActor(Target);
    FHitResult Hit;
    const FVector AttackSource=GetActorLocation()+FVector(0,0,HitProxy?HitProxy->GetScaledSphereRadius()*0.7f:100.f);
    if (GetWorld()->LineTraceSingleByChannel(Hit,AttackSource,BoxOrigin,ECC_Visibility,Params)) return false;
    return !GetWorld()->LineTraceSingleByChannel(Hit,BoxOrigin,Target->GetActorLocation()+FVector(0,0,50),ECC_Visibility,Params);
}

void AMHWIRathianApproxPawn::FaceTarget(AActor* Target,float DeltaSeconds,float Rate)
{
    if (!Target||Rate<=0.f) return; const FVector To=Target->GetActorLocation()-GetActorLocation();
    if (!To.IsNearlyZero()) SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(),FRotator(0,To.Rotation().Yaw,0),DeltaSeconds,Rate));
}

void AMHWIRathianApproxPawn::UpdateLocomotionBlend(float Speed)
{
    if (UMHWIRathianApproxAnimInstance* Anim=Body?Cast<UMHWIRathianApproxAnimInstance>(Body->GetAnimInstance()):nullptr)
        Anim->SetLocomotionBlend(LocomotionBlendAlpha(Speed,ActiveStats),GetWorld()?GetWorld()->GetDeltaSeconds():0.016f);
}

void AMHWIRathianApproxPawn::HandleDeath()
{
    if (bDeathHandled) return; bDeathHandled=true; ExecState=EExecState::Dead; CurrentMovementSpeed=0.f;
    ++ActivePhaseEpoch; bPhaseMontageEnded=false; bPhaseBlendOutStarted=false; bEmergencyLanding=bFlightActive; ActiveMontage=nullptr; ActiveMontageInstanceId=INDEX_NONE; ActiveSequence=nullptr; ActivePhaseIndex=INDEX_NONE; PreviousBoxTransforms.Reset(); PhaseHitActors.Reset(); if (!bFlightActive) KeepOnGround();
    if (UAnimInstance* Anim=Body?Body->GetAnimInstance():nullptr) Anim->Montage_Stop(0.f);
    for (AMHWIRathianApproxFireball* P:OwnerProjectiles) if (IsValid(P)) P->Destroy(); OwnerProjectiles.Reset();
    if (HitProxy)
    {
        HitProxy->SetGenerateOverlapEvents(false);
        HitProxy->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        HitProxy->SetCollisionResponseToAllChannels(ECR_Ignore);
        HitProxy->SetCollisionResponseToChannel(ECC_WorldStatic,ECR_Block);
    }
    UAnimSequence* Death=MovesetData?MovesetData->DeathAnimation.LoadSynchronous():nullptr;
    if (Death&&Body->GetSkeletalMeshAsset()&&Death->GetSkeleton()==Body->GetSkeletalMeshAsset()->GetSkeleton())
    { if (UMHWIRathianApproxAnimInstance* Anim=Cast<UMHWIRathianApproxAnimInstance>(Body->GetAnimInstance())) Anim->SetDeathSequence(Death); }
    else { UE_LOG(LogTemp,Warning,TEXT("[RathianApprox] death sequence missing or skeleton mismatch; freeze current pose")); if (Body) Body->bPauseAnims=true; }
    UE_LOG(LogTemp,Log,TEXT("[RathianApprox] terminal death run=%llu"),CurrentRunId);
}

FString AMHWIRathianApproxPawn::GetCurrentStateName() const
{
    switch (ExecState) { case EExecState::Patrol:return TEXT("Patrol"); case EExecState::Approach:return TEXT("Approach"); case EExecState::Turn:return TEXT("Turn"); case EExecState::Attack:return TEXT("Attack"); case EExecState::Landing:return TEXT("Landing"); case EExecState::Dead:return TEXT("Dead"); }
    return TEXT("Unknown");
}
FString AMHWIRathianApproxPawn::GetCurrentAttackName() const { return ExecState==EExecState::Attack?ActiveMove.RegistryName:FString(); }
float AMHWIRathianApproxPawn::GetHealthPercent() const { return Attributes?Attributes->GetHealthPercent():0.f; }
EMHWIImpactSize AMHWIRathianApproxPawn::GetMHWIImpactSize_Implementation() const
{ return ActiveMove.Phases.IsValidIndex(ActivePhaseIndex)?ActiveMove.Phases[ActivePhaseIndex].ImpactSize:EMHWIImpactSize::Medium; }
bool AMHWIRathianApproxPawn::DeflectsMHWIWeapon_Implementation(AActor*) const { return false; }

void AMHWIRathianApproxPawn::EndPlay(const EEndPlayReason::Type Reason)
{
    ++ActivePhaseEpoch;
    if (UAnimInstance* Anim=Body?Body->GetAnimInstance():nullptr;Anim&&ActiveMontage) Anim->Montage_Stop(0.f,ActiveMontage);
    if (Attributes) Attributes->OnCharacterDeath.RemoveDynamic(this,&AMHWIRathianApproxPawn::HandleDeath);
    for (AMHWIRathianApproxFireball* P:OwnerProjectiles) if (IsValid(P)) P->Destroy(); OwnerProjectiles.Reset();
    Super::EndPlay(Reason);
}
