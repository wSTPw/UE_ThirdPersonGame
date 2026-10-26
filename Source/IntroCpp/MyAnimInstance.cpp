#include "MyAnimInstance.h"
#include "MyPlayerCharacter.h"
#include "GameFramework/CharacterMovementComponent.h"

void UMyAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);
    // UObject access stays in the game-thread update, not NativeThreadSafeUpdateAnimation.
    const auto* Character = Cast<AMyPlayerCharacter>(TryGetPawnOwner());
    if (!Character) { LocomotionContext = FLocomotionAnimContext(); return; }
    FLocomotionAnimContext Context;
    Context.Velocity = Character->GetVelocity();
    Context.Facing = Character->GetActorRotation();
    Context.Stance = CurrentWeaponAnimType;
    if (Character->Actions) Context.Action = Character->Actions->GetSnapshot();
    if (const auto* Movement = Character->GetCharacterMovement())
    {
        Context.Acceleration = Movement->GetCurrentAcceleration();
        Context.bGrounded = Movement->IsMovingOnGround();
        if (Context.Action.MoveScale > 0.f)
            Context.DesiredVelocity = Context.Acceleration.GetSafeNormal2D() * Movement->GetMaxSpeed() * Context.Action.MoveScale;
    }
    LocomotionContext = Context;
}
