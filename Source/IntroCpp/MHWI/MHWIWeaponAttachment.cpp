#include "MHWIWeaponAttachment.h"

#include "Components/SkeletalMeshComponent.h"
#include "MHWINativeMountData.inl"

namespace
{
    // Exact source-model -> imported-component basis, verified against UE poses.
    const FQuat EquipmentBasis(FVector::XAxisVector, UE_HALF_PI);

    FTransform BackDescriptor()
    {
        // uWp03 0x143fd4390, main/sub: XYZ (89,-4,41), (-47,51,-24), .8.
        // Native qz*qy*qx, reflected by D=diag(1,-1,1) in imported bone space.
        const FQuat Native = FQuat(FVector::ZAxisVector, FMath::DegreesToRadians(41.0))
            * FQuat(FVector::YAxisVector, FMath::DegreesToRadians(-4.0))
            * FQuat(FVector::XAxisVector, FMath::DegreesToRadians(89.0));
        return FTransform(FQuat(-Native.X, Native.Y, -Native.Z, Native.W),
            FVector(-47.f, -51.f, -24.f), FVector(0.8f));
    }

    void Mount(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Piece, uint8 Selection,
        float VisualScale)
    {
        if (!Piece) return;
        const FName Bone = Selection == 1 ? TEXT("bone_047")
            : Selection == 2 ? TEXT("bone_030") : TEXT("bone_002");
        if (!Hunter->DoesSocketExist(Bone)) return;
        FTransform Parent = Hunter->GetSocketTransform(Bone);
        // Helper scale encodes selection, and native normalizes all three axes.
        Parent.SetScale3D(FVector::OneVector);
        FTransform Desired(EquipmentBasis);
        if (Selection == 0) Desired = Desired * BackDescriptor();
        Desired = Desired * Parent;
        if (Piece->GetAttachParent() != Hunter || Piece->GetAttachSocketName() != Bone)
            Piece->AttachToComponent(Hunter, FAttachmentTransformRules::KeepWorldTransform, Bone);
        Piece->SetAbsolute(false, false, true);
        Piece->SetWorldLocationAndRotation(Desired.GetLocation(), Desired.GetRotation());
        Piece->SetWorldScale3D(Hunter->GetComponentScale() * VisualScale);
    }
}

void FMHWIWeaponAttachmentRuntime::Reset()
{
    bInitialized = false;
    MainMount = 0;
    MainScale = FScale();
    SubScale = FScale();
}

float FMHWIWeaponAttachmentRuntime::FScale::Update(float Target, float DeltaSeconds)
{
    if (!bInitialized) { Value = Start = Target; bInitialized = true; }
    if (Target != Goal) { Start = Value; Goal = Target; Elapsed = 0.f; }
    Elapsed = FMath::Min(Elapsed + FMath::Max(DeltaSeconds, 0.f), 0.15f);
    // 0x142174b10: original circular ease-out, duration 0.15 at 0x142fb2344.
    const float T = Elapsed / 0.15f - 1.f;
    Value = FMath::Lerp(Start, Goal, FMath::Sqrt(FMath::Max(0.f, 1.f - T * T)));
    return Value;
}

void FMHWIWeaponAttachmentRuntime::Update(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Weapon,
    USkeletalMeshComponent* Scabbard, const FMHWIWeaponAttachmentContext& Context, float DeltaSeconds)
{
    if (!Hunter || !Weapon || !Scabbard) return;
    // The production full-body Slot replaces the primary native layer 0.
    // A valid zero selector means the back descriptor, not the neutral pose
    // underneath the Slot. Other native layers are not UE neutral playback.
    FMHWINativeMountSelection Base, Action;
    const bool bBase = SampleMHWINativeMount(Context.Base.Bank, Context.Base.Motion, Context.Base.Frame, Base);
    const bool bAction = SampleMHWINativeMount(Context.Action.Bank, Context.Action.Motion, Context.Action.Frame, Action);
    // FinishMove changes equipment state before this frame's evaluated neutral
    // players update. Resolve qualified neutral leaves from the new state so a
    // completed sheath cannot reattach to last frame's drawn idle for one tick.
    const bool bNeutral = (Context.Base.Bank == FName(TEXT("w03_00"))
            && (Context.Base.Motion == 1 || Context.Base.Motion == 4))
        || (Context.Base.Bank == FName(TEXT("co00_00"))
            && (Context.Base.Motion == 1 || Context.Base.Motion == 203 || Context.Base.Motion == 90))
        || Context.Base.Bank == FName(TEXT("UE_BlendSpace"));
    if (!bBase || bNeutral) Base.Main = Context.bSheathed ? 0 : 2;
    MainMount = bAction ? Action.Main : Base.Main;
    const uint8 SubMount = bAction ? Action.Sub : Base.Sub;
    Mount(Hunter, Weapon, MainMount, MainScale.Update(MainMount == 0 ? 0.8f : 1.f, DeltaSeconds));
    Mount(Hunter, Scabbard, SubMount, SubScale.Update(SubMount == 0 ? 0.8f : 1.f, DeltaSeconds));
    bInitialized = true;
}
