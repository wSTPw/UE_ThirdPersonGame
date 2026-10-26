#include "MHWIAnimInstance.h"
#include "MHWICharacter.h"
#include "MHWIEquipmentIKProfile.h"
#include "MHWIWeaponAttachment.h"
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
    UpdateEquipmentIK(*Character);
}

void UMHWIAnimInstance::UpdateEquipmentIK(const AMHWICharacter& Character)
{
    check(IsInGameThread());
    LeftArmIKAlpha = RightArmIKAlpha = LeftFootIKAlpha = RightFootIKAlpha = 0.f;
    USkeletalMeshComponent* Mesh = Character.GetMesh();
    if (!EquipmentIKProfile || !Mesh || bDead || bInAir) return;

    auto JointGoal = [Mesh](const FMHWIEquipmentIKChain& Chain, FVector& Out)
    {
        if (Chain.MidBone.IsNone() || !Mesh->DoesSocketExist(Chain.MidBone)) return false;
        Out = Mesh->GetSocketTransform(Chain.MidBone, RTS_Component).GetLocation() + Chain.JointTargetOffset;
        return true;
    };
    const FMHWIEquipmentIKChain& LA = EquipmentIKProfile->LeftArm;
    const FMHWIEquipmentIKChain& RA = EquipmentIKProfile->RightArm;
    const FMHWIEquipmentIKChain& LF = EquipmentIKProfile->LeftFoot;
    const FMHWIEquipmentIKChain& RF = EquipmentIKProfile->RightFoot;
    const bool bValidArms = JointGoal(LA, LeftArmJointTarget) && JointGoal(RA, RightArmJointTarget)
        && !LA.RootBone.IsNone() && !LA.EndBone.IsNone() && !RA.RootBone.IsNone() && !RA.EndBone.IsNone()
        && Mesh->DoesSocketExist(LA.RootBone) && Mesh->DoesSocketExist(LA.EndBone)
        && Mesh->DoesSocketExist(RA.RootBone) && Mesh->DoesSocketExist(RA.EndBone);

    const FTransform MeshWorld = Mesh->GetComponentTransform();
    const bool bHandPose = !bInAction || bSpecialSheathHold;
    if (bValidArms && bHandPose && Character.WeaponMesh && Character.ScabbardMesh)
    {
        FMHWIWeaponAttachmentSettings Settings;
        const FVector GripPoint = bSpecialSheathHold ? Settings.SpecialGripPoint : Settings.DrawnGripPoint;
        const FVector LocalGrip = FMHWIWeaponAttachmentRuntime::AnimatedGripPoint(Character.WeaponMesh, GripPoint);
        const FVector WorldGrip = Character.WeaponMesh->GetComponentTransform().TransformPosition(LocalGrip);
        RightArmEffector = MeshWorld.InverseTransformPosition(WorldGrip);
        RightArmIKAlpha = (!bSheathed || bSpecialSheathHold) ? EquipmentIKProfile->ArmAlpha : 0.f;

        if (bSpecialSheathHold)
        {
            const FVector WorldMouth = Character.ScabbardMesh->GetComponentTransform().TransformPosition(Settings.ScabbardMouthPoint);
            LeftArmEffector = MeshWorld.InverseTransformPosition(WorldMouth);
            LeftArmIKAlpha = EquipmentIKProfile->ArmAlpha;
        }
    }

    if (!Character.GetWorld()) return;
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
        const FVector Target = Hit.ImpactPoint + FVector(0.f, 0.f, EquipmentIKProfile->FootSoleOffsetZ);
        Effector = MeshWorld.InverseTransformPosition(Target);
        Alpha = bInAction ? 0.f : EquipmentIKProfile->FootAlpha;
    };
    FootGoal(LF, LeftFootEffector, LeftFootJointTarget, LeftFootIKAlpha);
    FootGoal(RF, RightFootEffector, RightFootJointTarget, RightFootIKAlpha);
}
