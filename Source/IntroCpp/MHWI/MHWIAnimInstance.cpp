#include "MHWIAnimInstance.h"
#include "MHWICharacter.h"
#include "MHWIEquipmentIKProfile.h"
#include "AttributeComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNodeBase.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"

namespace
{
    /** Worker-owned pose buffers. UObject access stays in UAnimInstance's game
     * thread entry points, which wait for an outstanding evaluation via GetProxy.
     * The previous DISPLAYED pose is captured again on an in-flight replacement. */
    struct FMHWINativeBlendProxy : FAnimInstanceProxy
    {
        explicit FMHWINativeBlendProxy(UAnimInstance* Instance) : FAnimInstanceProxy(Instance) {}
        TArray<FTransform> LastPose;
        TArray<int32> LastBones;
        TArray<FTransform> FromPose;
        TArray<int32> FromBones;
        float ElapsedFrames = 0.f;
        float DurationFrames = 0.f;
        bool bCapturePending = false;

        void Begin(int32 Frames)
        {
            FromPose = LastPose;
            FromBones = LastBones;
            ElapsedFrames = 0.f;
            DurationFrames = LastPose.IsEmpty() ? 0.f : float(FMath::Max(0, Frames));
            bCapturePending = DurationFrames > 0.f;
        }
        void Advance(float OwnerFrames)
        {
            // Native nMotion flag100 keeps elapsed at zero until the first
            // destination pose has been evaluated (142256586 / 142368a90).
            if (bCapturePending) { ElapsedFrames = 0.f; return; }
            if (FMath::IsFinite(OwnerFrames) && OwnerFrames > 0.f)
                ElapsedFrames = FMath::Min(DurationFrames, ElapsedFrames + OwnerFrames);
        }
        virtual bool Evaluate_WithRoot(FPoseContext& Output, FAnimNode_Base* InRootNode) override
        {
            EvaluateAnimationNode_WithRoot(Output, InRootNode);
            const int32 Count = Output.Pose.GetNumBones();
            const float Alpha = DurationFrames > 0.f
                ? FMath::Clamp(ElapsedFrames / DurationFrames, 0.f, 1.f) : 1.f;
            bool bCompatible = FromPose.Num() == Count && FromBones.Num() == Count;
            if (bCompatible)
                for (int32 Index = 0; Index < Count; ++Index)
                    if (FromBones[Index] != Output.Pose.GetBoneContainer().GetSkeletonIndex(FCompactPoseBoneIndex(Index)))
                    { bCompatible = false; break; }
            if (bCompatible && Alpha < 1.f)
                for (int32 Index = 0; Index < Count; ++Index)
                {
                    FTransform& Bone = Output.Pose[FCompactPoseBoneIndex(Index)];
                    const FTransform Target = Bone;
                    Bone.Blend(FromPose[Index], Target, Alpha);
                    Bone.NormalizeRotation();
                }
            LastPose.SetNum(Count);
            LastBones.SetNum(Count);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                LastPose[Index] = Output.Pose[FCompactPoseBoneIndex(Index)];
                LastBones[Index] = Output.Pose.GetBoneContainer().GetSkeletonIndex(FCompactPoseBoneIndex(Index));
            }
            bCapturePending = false;
            return true;
        }
    };
}

FAnimInstanceProxy* UMHWIAnimInstance::CreateAnimInstanceProxy()
{
    return new FMHWINativeBlendProxy(this);
}

void UMHWIAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy)
{
    delete static_cast<FMHWINativeBlendProxy*>(InProxy);
}

void UMHWIAnimInstance::BeginNativeBlend(int32 InterpolationFrames)
{
    check(IsInGameThread());
    GetProxyOnGameThread<FMHWINativeBlendProxy>().Begin(InterpolationFrames);
}

void UMHWIAnimInstance::CancelNativeBlend()
{
    check(IsInGameThread());
    GetProxyOnGameThread<FMHWINativeBlendProxy>().Begin(0);
}

bool UMHWIAnimInstance::ReadNativeBaseMotion(MHWI::Native::FMotionSample& OutMotion)
{
    check(IsInGameThread());
    FMHWINativeBlendProxy& Proxy = GetProxyOnGameThread<FMHWINativeBlendProxy>();
    bool bFound = false, bMixed = false;
    int32 Phase = INDEX_NONE;
    auto Add = [&](const UAnimSequenceBase* Sequence, float Time, float Weight)
    {
        if (Weight <= KINDA_SMALL_NUMBER) return;
        MHWI::Native::FMotionSample Sample;
        if (!MHWI::Native::ReadSequenceMotion(Sequence, Time, Sample)) return;
        const int32 LeafPhase = MHWI::Native::SampleLinkPhase(Sample);
        if (!bFound) { OutMotion = Sample; Phase = LeafPhase; }
        else if (Sample.Bank != OutMotion.Bank || Sample.Motion != OutMotion.Motion) bMixed = true;
        if (Phase != LeafPhase) Phase = INDEX_NONE;
        bFound = true;
    };
    auto Read = [&](const FAnimTickRecord& Tick)
    {
        if (!Tick.bActiveContext || Tick.EffectiveBlendWeight <= KINDA_SMALL_NUMBER) return;
        if (Cast<UBlendSpace>(Tick.SourceAsset) && Tick.BlendSpace.BlendSampleDataCache)
            for (const FBlendSampleData& Sample : *Tick.BlendSpace.BlendSampleDataCache)
                Add(Sample.Animation, Sample.Time, Sample.GetClampedWeight() * Tick.EffectiveBlendWeight);
        else if (const UAnimSequenceBase* Sequence = Cast<UAnimSequenceBase>(Tick.SourceAsset))
            if (Tick.TimeAccumulator) Add(Sequence, *Tick.TimeAccumulator, Tick.EffectiveBlendWeight);
    };
    for (const FAnimTickRecord& Tick : Proxy.GetUngroupedActivePlayersRead()) Read(Tick);
    for (const auto& Group : Proxy.GetSyncGroupMapRead())
        for (const FAnimTickRecord& Tick : Group.Value.ActivePlayers) Read(Tick);
    if (bMixed)
    {
        // A live blend has no single bank/motion/frame. Its neutral leaves all
        // have Phase 0, and no dedicated MBD row names this UE blend. Keep the
        // original serialized default; never select a fabricated dominant leaf.
        if (Phase != 0) return false;
        OutMotion = {FName(TEXT("UE_BlendSpace")), INDEX_NONE, 0.f};
    }
    return bFound;
}

void UMHWIAnimInstance::Montage_UpdateWeight(float DeltaSeconds)
{
    Super::Montage_UpdateWeight(DeltaSeconds);
    // 14221ada1 -> 142228f90 -> 141bffd26 -> 142256594. Unit manager
    // copies the scaled global frame step, distinct from source motion speed.
    // Global time owner +58 is 60 (14225c472); +94 is frame delta. UE supplies
    // actor animation delta seconds here; Montage play rate never enters it.
    GetProxyOnGameThread<FMHWINativeBlendProxy>().Advance(DeltaSeconds * 60.f);
}

UMHWIAnimInstance::UMHWIAnimInstance()
{
    RootMotionMode = ERootMotionMode::RootMotionFromMontagesOnly;
}

void UMHWIAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);
    const AMHWICharacter* Character = Cast<AMHWICharacter>(TryGetPawnOwner());
    if (!Character) return;
    const FVector Velocity = Character->GetVelocity();
    const float PreviousSpeed = Speed;
    const bool bWasInAir = bInAir;
    Speed = Velocity.Size2D();
    const FVector LocalVelocity = Character->GetActorRotation().UnrotateVector(Velocity);
    Direction = FMath::RadiansToDegrees(FMath::Atan2(LocalVelocity.Y, LocalVelocity.X));
    bSheathed = Character->IsSheathed();
    bSprinting = Character->IsSprinting();
    const UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
    bInAir = Movement && Movement->IsFalling();
    bJustLanded = bWasInAir && !bInAir;
    const FVector Acceleration = Movement ? Movement->GetCurrentAcceleration() : FVector::ZeroVector;
    bAccelerating = Acceleration.SizeSquared2D() > 1.f && Speed > 1.f;
    bDecelerating = !bAccelerating && PreviousSpeed > 30.f && Speed < PreviousSpeed - 1.f;
    TurnDirection = 0.f;
    if (PreviousVelocity.SizeSquared2D() > 30.f * 30.f && Speed > 30.f)
    {
        const FVector From = PreviousVelocity.GetSafeNormal2D();
        const FVector To = Velocity.GetSafeNormal2D();
        const float Cosine = FMath::Clamp(FVector::DotProduct(From, To), -1.f, 1.f);
        if (Cosine < 0.5f)
        {
            const float Sign = FMath::Sign(FVector::CrossProduct(From, To).Z);
            TurnDirection = Sign * FMath::RadiansToDegrees(FMath::Acos(Cosine));
        }
    }
    PreviousVelocity = Velocity;
    bDead = Character->Attributes && !Character->Attributes->IsAlive();
    bInAction = !Character->GetCurrentMove().IsNone();
    bSpecialSheathHold = Character->IsSpecialSheathHolding();
    UpdateLocomotionTransition(*Character, DeltaSeconds, PreviousSpeed);
    UpdateEquipmentIK(*Character);
}

void UMHWIAnimInstance::UpdateLocomotionTransition(const AMHWICharacter& Character, float DeltaSeconds, float PreviousSpeed)
{
    const UCharacterMovementComponent* Movement = Character.GetCharacterMovement();
    const FVector Intent = Movement ? Movement->GetCurrentAcceleration().GetSafeNormal2D() : FVector::ZeroVector;
    const bool bIntent = !Intent.IsNearlyZero();
    const int32 RollSerial = Character.GetNaturalRollCompletionSerial();
    const bool bFinishedRealRoll = RollSerial != LastNaturalRollCompletionSerial;
    LastNaturalRollCompletionSerial = RollSerial;
    const bool bEligible = Movement && Movement->IsMovingOnGround() && !bSheathed
        && !bDead && !bInAction && !Character.IsInputBlocked();
    if (!bEligible)
    {
        bLocomotionTransitionActive = false;
        bWasLocomotionEligible = bHadLocomotionIntent = false;
        return;
    }

    if (bLocomotionTransitionActive)
    {
        LocomotionTransitionTime = FMath::Min(LocomotionTransitionTime + FMath::Max(0.f, DeltaSeconds),
            LocomotionTransitionSequence ? LocomotionTransitionSequence->GetPlayLength() : 0.f);
        if (!LocomotionTransitionSequence || LocomotionTransitionTime >= LocomotionTransitionSequence->GetPlayLength())
            bLocomotionTransitionActive = false;
    }

    auto Begin = [this](int32 Motion)
    {
        const TObjectPtr<UAnimSequence>* Sequence = LocomotionTransitionClips.Find(Motion);
        if (!Sequence || !*Sequence) return;
        LocomotionTransitionSequence = *Sequence;
        LocomotionTransitionMotion = Motion;
        LocomotionTransitionTime = 0.f;
        bLocomotionTransitionActive = true;
    };
    const FVector Facing = Character.GetActorForwardVector().GetSafeNormal2D();
    const float Angle = bIntent ? FMath::RadiansToDegrees(FMath::Acos(
        FMath::Clamp(FVector::DotProduct(Facing, Intent), -1.f, 1.f))) : 0.f;
    const bool bNewTurn = bIntent && bHadLocomotionIntent
        && Angle >= LocomotionTurnThresholdDegrees
        && FVector::DotProduct(Intent, LastLocomotionIntent) < FMath::Cos(FMath::DegreesToRadians(LocomotionTurnThresholdDegrees));
    if (bIntent && bFinishedRealRoll)
    {
        // Native actions65/66 explicitly request 014/015. This UE state adapter
        // selects only after an actual, naturally completed drawn roll.
        Begin(Angle < LocomotionTurnThresholdDegrees ? 14 : 15);
    }
    else if (bIntent && (!bWasLocomotionEligible || !bHadLocomotionIntent || bNewTurn))
    {
        // Native WALK entry (1417fee40): angle < parameter+348 selects 005;
        // otherwise 142176590 selects 007/006 from the horizontal cross sign.
        Begin(Angle < LocomotionTurnThresholdDegrees ? 5
            : (FVector::CrossProduct(Facing, Intent).Z >= 0.f ? 7 : 6));
    }
    else if (!bIntent && bHadLocomotionIntent && (PreviousSpeed > KINDA_SMALL_NUMBER || bLocomotionTransitionActive))
    {
        Begin(8); // Native WALK_END entry 1417fef70 requests bank12 motion008.
    }
    bWasLocomotionEligible = true;
    bHadLocomotionIntent = bIntent;
    LastLocomotionIntent = Intent;
}

void UMHWIAnimInstance::UpdateEquipmentIK(const AMHWICharacter& Character)
{
    check(IsInGameThread());
    LeftArmIKAlpha = RightArmIKAlpha = LeftFootIKAlpha = RightFootIKAlpha = 0.f;
    USkeletalMeshComponent* Mesh = Character.GetMesh();
    if (!EquipmentIKProfile || !Mesh || bDead || bInAir || Character.IsInputBlocked()) return;

    auto JointGoal = [Mesh](const FMHWIEquipmentIKChain& Chain, FVector& Out)
    {
        if (Chain.MidBone.IsNone() || !Mesh->DoesSocketExist(Chain.MidBone)) return false;
        Out = Mesh->GetSocketTransform(Chain.MidBone, RTS_Component).InverseTransformVector(Chain.JointTargetOffset);
        return true;
    };
    const FMHWIEquipmentIKChain& LF = EquipmentIKProfile->LeftFoot;
    const FMHWIEquipmentIKChain& RF = EquipmentIKProfile->RightFoot;
    // Source helper bones carry the equipment pose. Pulling wrists toward a
    // fitted point on last frame's weapon creates a feedback loop and changes
    // the authored hand pose. Keep source arms; terrain feet remain independent.

    const UCharacterMovementComponent* Movement = Character.GetCharacterMovement();
    if (!Character.GetWorld() || !Movement || !Movement->IsMovingOnGround()
        || !Movement->CurrentFloor.IsWalkableFloor()) return;
    auto FootGoal = [&](const FMHWIEquipmentIKChain& Chain, FVector& Effector, FVector& Joint, float& Alpha)
    {
        if (!JointGoal(Chain, Joint) || Chain.RootBone.IsNone() || Chain.EndBone.IsNone()
            || !Mesh->DoesSocketExist(Chain.RootBone) || !Mesh->DoesSocketExist(Chain.EndBone)) return;
        const FVector FootWorld = Mesh->GetSocketTransform(Chain.EndBone, RTS_World).GetLocation();
        const FVector Start = FootWorld + FVector(0.f, 0.f, EquipmentIKProfile->FootTraceUp);
        const FVector End = FootWorld - FVector(0.f, 0.f, EquipmentIKProfile->FootTraceDown);
        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(MHWIEquipmentIK), false);
        Params.AddIgnoredActor(&Character);
        if (!Character.GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params)) return;
        if (!Movement->IsWalkable(Hit)) return;
        // Feed an offset relative to the SAME end bone of the evaluated base
        // pose, not last frame's solved ankle position. Flat ground => zero;
        // local height differences adjust terrain without erasing swing lift
        // or accumulating the previous frame's IK displacement.
        const float TerrainDelta = Hit.ImpactPoint.Z - Movement->CurrentFloor.HitResult.ImpactPoint.Z;
        const FVector WorldOffset(0.f, 0.f, TerrainDelta + EquipmentIKProfile->FootSoleOffsetZ);
        Effector = Mesh->GetSocketTransform(Chain.EndBone, RTS_World).InverseTransformVector(WorldOffset);
        Alpha = bInAction ? 0.f : EquipmentIKProfile->FootAlpha;
    };
    FootGoal(LF, LeftFootEffector, LeftFootJointTarget, LeftFootIKAlpha);
    FootGoal(RF, RightFootEffector, RightFootJointTarget, RightFootIKAlpha);
}
