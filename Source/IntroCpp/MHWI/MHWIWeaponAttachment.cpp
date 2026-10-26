#include "MHWIWeaponAttachment.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

namespace MHWIWeaponAttachment
{
    enum EMode : uint8 { Back, Drawn, Draw, Sheathe, Special, Iai, AttackDraw, Return };

    static float Window(float Position, float Start, float End)
    {
        const float Alpha = FMath::Clamp((Position - Start) / FMath::Max(End - Start, KINDA_SMALL_NUMBER), 0.f, 1.f);
        return Alpha * Alpha * (3.f - 2.f * Alpha);
    }

    static FTransform Blend(const FTransform& From, const FTransform& To, float Alpha)
    {
        FTransform Result;
        Result.Blend(From, To, Alpha);
        Result.NormalizeRotation();
        return Result;
    }

    /** Anchor an actual animated point, rather than an old component-space marker. */
    static FTransform Anchor(const FTransform& Basis, const FVector& LocalPoint, const FVector& WorldPoint)
    {
        FTransform Result = Basis;
        Result.SetTranslation(WorldPoint - Result.TransformVector(LocalPoint));
        return Result;
    }

    static FTransform AimY(const FTransform& Basis, const FVector& Direction)
    {
        if (Direction.IsNearlyZero()) return Basis;
        FTransform Result = Basis;
        const FQuat Aim = FQuat::FindBetweenNormals(Basis.GetRotation().GetAxisY(), Direction.GetSafeNormal());
        Result.SetRotation((Aim * Basis.GetRotation()).GetNormalized());
        return Result;
    }
}

void FMHWIWeaponAttachmentRuntime::Reset()
{
    WeaponState = FPiece();
    ScabbardState = FPiece();
    LastExecutionSerial = 0;
    bHaveExecution = bAttackFromBack = false;
    LastBackAmount = 1.f;
    LastGripPoint = EntryGripPoint = FVector(0.f, -12.f, 0.f);
    GripHandoffElapsed = 0.f;
}

FVector FMHWIWeaponAttachmentRuntime::AnimatedGripPoint(USkeletalMeshComponent* Weapon, const FVector& ReferencePoint)
{
    const USkeletalMesh* Mesh = Weapon ? Weapon->GetSkeletalMeshAsset() : nullptr;
    if (!Mesh) return ReferencePoint;
    const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
    // Twelve nearest source skin vertices at each grip marker. The grip blends
    // functions 1 and 2; treating it as 100% function 2 overcompensates by tens of
    // centimeters. Evidence: author_weapon_transfer.audit_source_skin(). These
    // measured weights belong to the delivered swo001, not arbitrary weapons.
    static constexpr float GripY[] = {-66.485203f, -63.f, -60.f, -55.f, -40.f, -12.f};
    static constexpr float SkinWeight[] = {0.520039097f, 0.520039097f, 0.449657857f,
        0.449657857f, 0.330400785f, 0.149560119f};
    float Weight = SkinWeight[0];
    for (int32 I = 1; I < UE_ARRAY_COUNT(GripY); ++I)
    {
        if (ReferencePoint.Y < GripY[I])
        {
            Weight = FMath::Lerp(SkinWeight[I - 1], SkinWeight[I],
                FMath::Clamp((ReferencePoint.Y - GripY[I - 1]) / (GripY[I] - GripY[I - 1]), 0.f, 1.f));
            break;
        }
        Weight = SkinWeight[I];
    }
    auto SkinnedPoint = [&](FName Bone) -> FVector
    {
        const int32 Index = Ref.FindBoneIndex(Bone);
        if (Index == INDEX_NONE || !Weapon->DoesSocketExist(Bone)) return ReferencePoint;
        FTransform Bind = Ref.GetRefBonePose()[Index];
        for (int32 Parent = Ref.GetParentIndex(Index); Parent != INDEX_NONE; Parent = Ref.GetParentIndex(Parent))
            Bind = Bind * Ref.GetRefBonePose()[Parent];
        return Weapon->GetSocketTransform(Bone, RTS_Component).TransformPosition(Bind.InverseTransformPosition(ReferencePoint));
    };
    return FMath::Lerp(SkinnedPoint(TEXT("bone_001")), SkinnedPoint(TEXT("bone_002")), Weight);
}

void FMHWIWeaponAttachmentRuntime::Apply(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Piece,
    FPiece& State, FName Socket, const FTransform& DesiredWorld, uint8 Mode,
    uint32 ExecutionSerial, float DeltaSeconds, float BlendSeconds, float SourceBlend,
    const FVector* ContactPoint, const FVector* ContactWorld)
{
    if (!Hunter || !Piece || Socket.IsNone() || !Hunter->DoesSocketExist(Socket) || DesiredWorld.ContainsNaN()) return;
    const FTransform ParentWorld = Hunter->GetSocketTransform(Socket);
    const bool bNewMode = State.Mode != Mode || State.Socket != Socket
        || (Mode >= MHWIWeaponAttachment::Draw && State.ExecutionSerial != ExecutionSerial)
        || Piece->GetAttachParent() != Hunter || Piece->GetAttachSocketName() != Socket;
    const bool bFirst = !State.bInitialized;
    if (bFirst || bNewMode)
    {
        State.EntryRelative = Piece->GetComponentTransform().GetRelativeTransform(ParentWorld);
        State.Elapsed = 0.f;
        State.Mode = Mode;
        State.Socket = Socket;
        State.bInitialized = true;
        Piece->AttachToComponent(Hunter, FAttachmentTransformRules::KeepWorldTransform, Socket);
    }
    State.ExecutionSerial = ExecutionSerial;
    State.Elapsed += FMath::Max(0.f, DeltaSeconds);
    const float Alpha = bFirst ? 1.f : (SourceBlend >= 0.f ? FMath::Clamp(SourceBlend, 0.f, 1.f)
        : MHWIWeaponAttachment::Window(State.Elapsed, 0.f, BlendSeconds));
    const FTransform TargetRelative = DesiredWorld.GetRelativeTransform(ParentWorld);
    FTransform Result = MHWIWeaponAttachment::Blend(State.EntryRelative, TargetRelative, Alpha) * ParentWorld;
    // Interpolating component origins does not interpolate the animated material
    // contact. In particular, Iai switches the internal hilt pose at frame zero.
    // Enforce contact AFTER blending, so rotation may blend without hand drift.
    if (ContactPoint && ContactWorld)
        Result = MHWIWeaponAttachment::Anchor(Result, *ContactPoint, *ContactWorld);
    Piece->SetRelativeTransform(Result.GetRelativeTransform(ParentWorld));
}

void FMHWIWeaponAttachmentRuntime::Update(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Weapon,
    USkeletalMeshComponent* Scabbard, const FMHWIWeaponAttachmentSettings& S,
    const FMHWIWeaponAttachmentContext& C, float DeltaSeconds)
{
    using namespace MHWIWeaponAttachment;
    if (!Hunter || !Weapon || !Scabbard || !Hunter->DoesSocketExist(S.WeaponBone)
        || !Hunter->DoesSocketExist(S.ScabbardBone) || !Hunter->DoesSocketExist(S.SheathedWeaponBone)
        || !Hunter->DoesSocketExist(S.SpecialScabbardBone)) return;
    if (!bHaveExecution || LastExecutionSerial != C.ExecutionSerial)
    {
        EntryGripPoint = LastGripPoint;
        GripHandoffElapsed = 0.f;
        bAttackFromBack = C.bUnsheathAtStart && (C.bMoveStartedSheathed || LastBackAmount >= 0.95f);
        LastExecutionSerial = C.ExecutionSerial;
        bHaveExecution = true;
    }
    GripHandoffElapsed += FMath::Max(0.f, DeltaSeconds);
    EMode Mode = C.bSheathed ? Back : Drawn;
    if (C.CurrentMove == TEXT("Draw")) Mode = Draw;
    else if (C.CurrentMove == TEXT("Sheathe")) Mode = Sheathe;
    else if (C.CurrentMove == TEXT("SpecialSheathe")) Mode = Special;
    else if (C.CurrentMove.ToString().StartsWith(TEXT("Iai"))) Mode = Iai;
    else if (!C.CurrentMove.IsNone() && C.ReturnToSheathTime >= 0.f) Mode = Return;
    else if (!C.CurrentMove.IsNone() && bAttackFromBack) Mode = AttackDraw;

    const float Position = FMath::Max(0.f, C.MontagePosition);
    const FTransform Right = Hunter->GetSocketTransform(S.WeaponBone);
    const FTransform Left = Hunter->GetSocketTransform(S.SpecialScabbardBone);
    const FVector RightPalm = Right.TransformPosition(S.RightPalmPoint);
    const FVector LeftPalm = Left.TransformPosition(S.LeftPalmPoint);
    const FTransform BackSword = S.SheathedWeaponRelativeTransform * Hunter->GetSocketTransform(S.SheathedWeaponBone);
    const FTransform BackSheath = S.ScabbardRelativeTransform * Hunter->GetSocketTransform(S.ScabbardBone);
    const FTransform DrawnBasis = S.WeaponRelativeTransform * Right;
    const FTransform HandSword = Anchor(DrawnBasis, AnimatedGripPoint(Weapon, S.DrawnGripPoint), RightPalm);
    // The old fixed fitting was measured against the RIGHT-hand offset reused
    // on the left wrist. Keep its roll/scale, but put the mouth at the actual
    // left-hand marker throughout the transfer, not only on the final hold.
    const FTransform LeftSheath = Anchor(S.SpecialScabbardRelativeTransform * Left,
        S.ScabbardMouthPoint, LeftPalm);
    FTransform Sword = C.bSheathed ? BackSword : HandSword;
    FTransform Sheath = BackSheath;
    FName SwordSocket = C.bSheathed ? S.SheathedWeaponBone : S.WeaponBone;
    FName SheathSocket = S.ScabbardBone;
    float SwordBlend = -1.f;
    FVector GripPoint = S.DrawnGripPoint;
    bool bLockGrip = Mode == Drawn;
    bool bLockMouth = false;
    float BackAmount = Mode == Back ? 1.f : 0.f;

    if (Mode == Drawn)
    {
        // A cancelled special sheath can return directly to idle/roll. Keep its
        // last material grip during the zero-delta switch, then slide to normal.
        GripPoint = FMath::Lerp(EntryGripPoint, S.DrawnGripPoint,
            Window(GripHandoffElapsed, 0.f, S.HandOffBlendSeconds));
        Sword = Anchor(DrawnBasis, AnimatedGripPoint(Weapon, GripPoint), RightPalm);
    }
    else if (Mode == Draw || Mode == AttackDraw)
    {
        const float Start = Mode == Draw ? S.DrawTransferStart : 0.f;
        const float End = Mode == Draw ? S.DrawTransferEnd : S.AttackDrawEnd;
        const float Amount = Window(Position, Start, End);
        // Attack entries may interrupt a partly completed return-to-back. Blend
        // from the actual entry pose, so the 95% visual classification cannot
        // cause a snap to a hypothetical fully sheathed component transform.
        Sword = Mode == AttackDraw ? HandSword : Blend(BackSword, HandSword, Amount);
        SwordSocket = S.WeaponBone;
        SwordBlend = Mode == AttackDraw ? Amount : 1.f;
        BackAmount = 1.f - Amount;
        bLockGrip = Amount >= 1.f;
    }
    else if (Mode == Sheathe || Mode == Return)
    {
        const float End = Mode == Sheathe ? S.SheatheTransferEnd : C.ReturnToSheathTime;
        const float Start = Mode == Sheathe ? S.SheatheTransferStart : FMath::Max(0.f, End - S.ReturnTransferSeconds);
        const float Amount = Window(Position, Start, End);
        Sword = Blend(HandSword, BackSword, Amount);
        SwordSocket = S.SheathedWeaponBone;
        SwordBlend = 1.f;
        BackAmount = Amount;
        bLockGrip = Amount <= 0.f;
    }
    else if (Mode == Special)
    {
        const float Insert = C.bSpecialSheathHeld ? 1.f : Window(Position, S.SpecialInsertStart, S.SpecialInsertEnd);
        // Fix roll to the left-hand fitting and steer only the longitudinal axis.
        // This avoids global-up singularities while the character turns or leans.
        const FTransform AxisBasis = AimY(LeftSheath, LeftPalm - RightPalm);
        const FTransform AimedSheath = Anchor(AxisBasis, S.ScabbardMouthPoint, LeftPalm);
        Sheath = Blend(LeftSheath, AimedSheath, Insert);
        SheathSocket = S.SpecialScabbardBone;
        const FTransform SwordAxisBasis = AimY(S.SpecialWeaponRelativeTransform * Left, LeftPalm - RightPalm);
        const FTransform SwordBasis = Blend(DrawnBasis, SwordAxisBasis, Insert);
        const FVector Grip = FMath::Lerp(S.DrawnGripPoint, S.SpecialGripPoint, Insert);
        Sword = Anchor(SwordBasis, AnimatedGripPoint(Weapon, Grip), RightPalm);
        GripPoint = Grip;
        SwordSocket = S.WeaponBone;
        SwordBlend = 1.f;
        bLockGrip = true;
        bLockMouth = Insert >= 1.f;
        // The source internal motion retracts the grip by 80 cm. Requiring the
        // component origins to coincide would detach the actual grip from the
        // right palm. Preserve the source pose and permit axial blade withdrawal.
    }
    else if (Mode == Iai)
    {
        Sheath = LeftSheath;
        SheathSocket = S.SpecialScabbardBone;
        // Transfer the SAME material grip used by the preceding hold, rather
        // than changing it to the ordinary grip in a single frame.
        GripPoint = FMath::Lerp(EntryGripPoint, S.DrawnGripPoint, Window(Position, 0.f, S.IaiTransferEnd));
        Sword = Anchor(DrawnBasis, AnimatedGripPoint(Weapon, GripPoint), RightPalm);
        SwordSocket = S.WeaponBone;
        SwordBlend = Window(Position, 0.f, S.IaiTransferEnd);
        bLockGrip = bLockMouth = true;
    }
    const FVector AnimatedGrip = AnimatedGripPoint(Weapon, GripPoint);
    Apply(Hunter, Weapon, WeaponState, SwordSocket, Sword, Mode,
        C.ExecutionSerial, DeltaSeconds, S.HandOffBlendSeconds, SwordBlend,
        bLockGrip ? &AnimatedGrip : nullptr, bLockGrip ? &RightPalm : nullptr);
    // Left-hand ownership is unchanged across Special -> Iai and Iai variants;
    // do not restart a sheath handoff for each action's execution serial.
    const uint8 SheathMode = SheathSocket == S.SpecialScabbardBone ? Drawn : Back;
    Apply(Hunter, Scabbard, ScabbardState, SheathSocket, Sheath, SheathMode,
        C.ExecutionSerial, DeltaSeconds, S.HandOffBlendSeconds, -1.f,
        bLockMouth ? &S.ScabbardMouthPoint : nullptr, bLockMouth ? &LeftPalm : nullptr);
    LastGripPoint = GripPoint;
    LastBackAmount = BackAmount;
}
