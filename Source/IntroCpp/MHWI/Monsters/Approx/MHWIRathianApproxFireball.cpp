#include "MHWIRathianApproxFireball.h"
#include "AttributeComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "GameFramework/Character.h"
#include "MHWI/MHWICharacter.h"
#include "UObject/ConstructorHelpers.h"

AMHWIRathianApproxFireball::AMHWIRathianApproxFireball()
{
    PrimaryActorTick.bCanEverTick = true;
    InitialLifeSpan = 6.f;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    SetRootComponent(Collision);
    Collision->InitSphereRadius(42.f);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Collision->SetCollisionObjectType(ECC_WorldDynamic);
    Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
    Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Collision->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
    Collision->SetGenerateOverlapEvents(true);
    Collision->OnComponentHit.AddDynamic(this, &AMHWIRathianApproxFireball::HandleHit);
    Collision->OnComponentBeginOverlap.AddDynamic(this, &AMHWIRathianApproxFireball::HandleOverlap);

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisibleFireball"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.65f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded()) Visual->SetStaticMesh(SphereMesh.Object);

    Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovement"));
    Movement->UpdatedComponent = Collision;
    Movement->InitialSpeed = 1150.f;
    Movement->MaxSpeed = 1150.f;
    Movement->ProjectileGravityScale = 0.f;
    Movement->bRotationFollowsVelocity = true;
    Movement->bInitialVelocityInLocalSpace = false;
    Movement->bSweepCollision = true;
}

void AMHWIRathianApproxFireball::InitializeProjectile(AActor* InOwner, AActor* InTarget, float InDamage, FVector InKnockback, EMHWIImpactSize InImpactSize)
{
    check(IsInGameThread());
    SourceOwner = InOwner;
    Target = InTarget;
    DamageAmount = FMath::Max(0.f, InDamage);
    KnockbackVelocity = InKnockback;
    ImpactSize = InImpactSize;
    SetOwner(InOwner);
    Collision->IgnoreActorWhenMoving(InOwner, true);
    const FVector Aim = InTarget ? (InTarget->GetActorLocation() + FVector(0,0,55.f) - GetActorLocation()).GetSafeNormal() : GetActorForwardVector();
    Movement->Velocity = Aim * Movement->InitialSpeed;
}

void AMHWIRathianApproxFireball::BeginPlay()
{
    Super::BeginPlay();
    if (AActor* OwnerActor = SourceOwner.Get()) Collision->IgnoreActorWhenMoving(OwnerActor, true);
}

void AMHWIRathianApproxFireball::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (AActor* OwnerActor = SourceOwner.Get())
    {
        if (const UAttributeComponent* Attr = OwnerActor->FindComponentByClass<UAttributeComponent>(); !Attr || !Attr->IsAlive())
        {
            Destroy();
        }
    } else Destroy();
}

void AMHWIRathianApproxFireball::HandleHit(UPrimitiveComponent*, AActor* OtherActor, UPrimitiveComponent*, FVector, const FHitResult& Hit)
{
    Consume(OtherActor, Hit);
}
void AMHWIRathianApproxFireball::HandleOverlap(UPrimitiveComponent*, AActor* OtherActor, UPrimitiveComponent*, int32, bool, const FHitResult& Hit)
{
    Consume(OtherActor, Hit);
}

void AMHWIRathianApproxFireball::Consume(AActor* OtherActor, const FHitResult& Hit)
{
    if (bConsumed || OtherActor == SourceOwner.Get()) return;
    bConsumed = true;
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Movement->StopMovementImmediately();
    if (OtherActor)
    {
        if (UAttributeComponent* Attr = OtherActor->FindComponentByClass<UAttributeComponent>(); Attr && Attr->IsAlive())
        {
            const TWeakObjectPtr<UAttributeComponent> WeakAttr(Attr); const TWeakObjectPtr<AActor> WeakTarget(OtherActor); const float Before = Attr->CurrentHealth;
            Attr->ApplyDamage(DamageAmount, this);
            Attr=WeakAttr.Get(); OtherActor=WeakTarget.Get();
            if (IsValid(Attr)&&IsValid(OtherActor)&&Attr->CurrentHealth < Before && Attr->IsAlive())
            {
                if (ACharacter* Character = Cast<ACharacter>(OtherActor))
                {
                    const AMHWICharacter* MHWI=Cast<AMHWICharacter>(OtherActor);
                    if (!MHWI||MHWI->GetCounterArmorRemaining()<=0.f)
                    { const FVector Away = (OtherActor->GetActorLocation() - GetActorLocation()).GetSafeNormal2D(); Character->LaunchCharacter(Away * KnockbackVelocity.Size2D() + FVector(0,0,KnockbackVelocity.Z), true, true); }
                }
            }
        }
    }
    SetLifeSpan(0.1f);
}
