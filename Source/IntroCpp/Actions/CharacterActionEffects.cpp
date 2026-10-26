#include "Actions/CharacterActionComponent.h"
#include "Actions/CharacterActionExecution.h"
#include "MyPlayerCharacter.h"
#include "AFireballProjectile.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"

bool UMeleeActionExecution::ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event)
{ return Event == ECharacterActionEvent::MeleeHit && Component.ApplyMelee(*this); }
bool UCastActionExecution::ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event)
{ return Event == ECharacterActionEvent::CastCommit && Component.ApplyCast(*this); }
bool UUseItemActionExecution::ApplyEvent(UCharacterActionComponent& Component, ECharacterActionEvent Event)
{ return Event == ECharacterActionEvent::ItemCommit && Component.ApplyItem(*this); }

bool UCharacterActionComponent::ApplyMelee(UCharacterActionExecution& Run)
{
    if (!bDispatching || Active != &Run || !Character) return false;
    FComboHitEntry Hit;
    if (Run.Combo)
    {
        if (!Run.Combo->Hits.IsValidIndex(Run.State.ComboIndex)) return false;
        Hit = Run.Combo->Hits[Run.State.ComboIndex];
    }
    else if (Run.DamageOverride != 0) Hit.BaseDamage = Run.DamageOverride;
    const int32 SubIndex = Run.HitCount++;
    if (!Hit.SubHits.IsEmpty())
    {
        if (!Hit.SubHits.IsValidIndex(SubIndex)) return false; // Never wrap excess notifications to hit zero.
        const auto& Sub = Hit.SubHits[SubIndex];
        if (Sub.DamageMultiplierOverride > 0.f) Hit.DamageMultiplier = Sub.DamageMultiplierOverride;
        if (Sub.SphereRadiusOverride > 0.f) Hit.AttackSphereRadius = Sub.SphereRadiusOverride;
        if (Sub.ForwardOffsetOverride > 0.f) Hit.AttackForwardOffset = Sub.ForwardOffsetOverride;
        if (Sub.KnockbackOverride > 0.f) Hit.KnockbackForce = Sub.KnockbackOverride;
    }
    // Pay once per execution, before damage and before any re-entrant delegates.
    if (!Run.bManaSpent)
    {
        Run.bManaSpent = true;
        if (!Character->AttributeComp || !Character->AttributeComp->TrySpendMana(Run.ManaCost))
        { LastFailure = ECharacterActionFailure::InsufficientMana; return false; }
        if (bDeferredFinish || !Character->AttributeComp->IsAlive()) return false;
    }
    const FVector Start = Character->GetActorLocation() + FVector(0, 0, 80);
    const FVector End = Start + Character->GetActorForwardVector() * Hit.AttackForwardOffset;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CharacterActionMelee), false, Character);
    FHitResult Result;
    if (GetWorld()->SweepSingleByChannel(Result, Start, End, FQuat::Identity, ECC_Pawn,
        FCollisionShape::MakeSphere(FMath::Max(1.f, Hit.AttackSphereRadius)), Params))
    {
        if (AActor* Target = Result.GetActor())
        {
            const float Damage = FMath::Max(0.f, Hit.BaseDamage * Hit.DamageMultiplier);
            if (auto* Attributes = Target->FindComponentByClass<UAttributeComponent>())
                Attributes->ApplyDamage(Damage, Character);
            if (auto* HitCharacter = Cast<ACharacter>(Target))
            {
                FVector Direction = (Target->GetActorLocation() - Character->GetActorLocation()).GetSafeNormal();
                Direction.Z = 0.3f;
                HitCharacter->LaunchCharacter(Direction * Hit.KnockbackForce, true, true);
            }
            Character->BP_OnMeleeAttackHit(Result, Run.State.ComboIndex, SubIndex, Damage);
        }
    }
    return true; // A swing is a valid commit even when it misses.
}

bool UCharacterActionComponent::ApplyCast(UCharacterActionExecution& Run)
{
    if (!bDispatching || Active != &Run || !Character || !Run.Weapon || !Character->AttributeComp) return false;
    auto* Attributes = Character->AttributeComp;
    if (!Attributes->IsAlive() || Attributes->GetCurrentMana() < Run.ManaCost)
    { LastFailure = ECharacterActionFailure::InsufficientMana; return false; }
    UClass* ProjectileClass = Run.ProjectileClass.Get();
    if (!ProjectileClass) { LastFailure = ECharacterActionFailure::NotReady; return false; }
    FVector Direction = Character->Camera ? Character->Camera->GetForwardVector() : Character->GetActorForwardVector();
    FVector Location = Character->GetActorLocation() + FVector(0, 0, 80);
    const FName Socket = Run.FireSocket;
    if (Character->GetMesh()->DoesSocketExist(Socket))
        Location = Character->GetMesh()->GetSocketLocation(Socket) + Direction * 10.f;
    const FTransform Transform(Direction.Rotation(), Location);
    AActor* Projectile = GetWorld()->SpawnActorDeferred<AActor>(ProjectileClass, Transform, Character, Character,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Projectile) { LastFailure = ECharacterActionFailure::SpawnFailed; return false; }
    // Owner/instigator and damage exist before BeginPlay or overlap callbacks.
    if (auto* Fireball = Cast<AAFireballProjectile>(Projectile))
    {
        if (Run.DamageOverride != 0) Fireball->Damage = FMath::Max(0, Run.DamageOverride);
        if (Fireball->ProjectileMovement)
        {
            const float Speed = Fireball->ProjectileMovement->InitialSpeed > 0.f ? Fireball->ProjectileMovement->InitialSpeed : 1500.f;
            Fireball->ProjectileMovement->Velocity = Direction.GetSafeNormal() * Speed;
        }
    }
    if (!Attributes->TrySpendMana(Run.ManaCost))
    { Projectile->Destroy(); LastFailure = ECharacterActionFailure::InsufficientMana; return false; }
    if (bDeferredFinish || !IsValid(Character) || !Attributes->IsAlive())
    { Projectile->Destroy(); return false; }
    UGameplayStatics::FinishSpawningActor(Projectile, Transform);
    return true;
}

bool UCharacterActionComponent::ApplyItem(UCharacterActionExecution& Run)
{
    if (!bDispatching || Active != &Run || !Character || !Character->InventoryComponent) return false;
    const auto Result = Character->InventoryComponent->CommitActionItem(Run.Reservation, Run.Item);
    return Result.IsCommitted();
}
