#include "MHWITrainingTarget.h"
#include "AttributeComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

AMHWITrainingTarget::AMHWITrainingTarget()
{
    PrimaryActorTick.bCanEverTick = true;
    TargetMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TargetMesh"));
    SetRootComponent(TargetMesh);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (Cylinder.Succeeded()) TargetMesh->SetStaticMesh(Cylinder.Object);
    TargetMesh->SetRelativeScale3D(FVector(0.75f, 0.75f, 1.8f));
    TargetMesh->SetCollisionObjectType(ECC_Pawn);
    TargetMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    TargetMesh->SetCollisionResponseToAllChannels(ECR_Block);
    Attributes = CreateDefaultSubobject<UAttributeComponent>(TEXT("Attributes"));
    Attributes->MaxHealth = 10000.f;
    Attributes->bCanDie = false;
    Attributes->HealthRegenPerSecond = 0.f;
    Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
    Label->SetupAttachment(TargetMesh);
    Label->SetRelativeLocation(FVector(0.f, 0.f, 95.f));
    Label->SetRelativeScale3D(FVector(1.f, 1.f, 0.5556f));
    Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetWorldSize(14.f);
    Label->SetText(FText::FromString(TEXT("TRAINING TARGET")));
}

void AMHWITrainingTarget::BeginPlay()
{
    Super::BeginPlay();
    Attributes->OnDamaged.AddDynamic(this, &AMHWITrainingTarget::HandleDamaged);
}

void AMHWITrainingTarget::HandleDamaged(float Amount, AActor* DamageInstigator)
{
    LastDamage = Amount;
    DamageDisplayRemaining = 1.5f;
}

void AMHWITrainingTarget::ResetTarget()
{
    Attributes->SetHealth(Attributes->GetMaxHealth());
    LastDamage = 0.f;
    DamageDisplayRemaining = 0.f;
    CycleSeconds = 0.f;
}

void AMHWITrainingTarget::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
    if (!IsValid(Player)) return;
    const FVector ToPlayer = Player->GetActorLocation() - GetActorLocation();
    Label->SetWorldRotation(ToPlayer.Rotation());
    DamageDisplayRemaining = FMath::Max(0.f, DamageDisplayRemaining - DeltaSeconds);
    const float Interval = FMath::Max(1.f, AttackInterval);
    CycleSeconds = bEnableAttacks ? CycleSeconds + DeltaSeconds : 0.f;
    const bool bInRange = ToPlayer.Size2D() <= AttackRange && FMath::Abs(ToPlayer.Z) < 200.f;
    const bool bTelegraph = bEnableAttacks && bInRange && CycleSeconds >= Interval - FMath::Clamp(TelegraphSeconds, 0.1f, Interval);
    if (bTelegraph)
    {
        Label->SetTextRenderColor(FColor(255, 90, 50));
        Label->SetText(FText::FromString(TEXT("INCOMING ATTACK\nF / IAI / EVADE")));
    }
    else
    {
        Label->SetTextRenderColor(FColor(235, 220, 170));
        Label->SetText(FText::FromString(DamageDisplayRemaining > 0.f
            ? FString::Printf(TEXT("HIT %.1f\nTRAINING TARGET"), LastDamage)
            : TEXT("TRAINING TARGET\nApproach to practice counters")));
    }
    if (bEnableAttacks && CycleSeconds >= Interval)
    {
        CycleSeconds = FMath::Fmod(CycleSeconds, Interval);
        if (bInRange)
            if (UAttributeComponent* PlayerAttributes = Player->FindComponentByClass<UAttributeComponent>())
                PlayerAttributes->ApplyDamage(FMath::Max(0.f, Damage), this);
    }
    if (Attributes->GetCurrentHealth() < 1000.f) Attributes->SetHealth(Attributes->GetMaxHealth());
}
