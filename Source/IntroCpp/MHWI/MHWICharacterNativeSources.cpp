#include "MHWICharacter.h"
#include "MHWIAnimInstance.h"
#include "AttributeComponent.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/UObjectGlobals.h"

namespace
{
    FName SourceKey(FName Bank, int32 Motion)
    { return FName(*FString::Printf(TEXT("%s_%03d"), *Bank.ToString(), Motion)); }
}

void AMHWICharacter::InitializeNativeRuntimeMoves()
{
    if (!Moveset) return;
    // Per-character definitions retain their sequence references for GC. The
    // production DA remains the serialized source of gameplay tuning.
    Moveset = DuplicateObject<UMHWIMovesetData>(Moveset, this);
    const FMHWIMoveDefinition* Step = Moveset->Moves.Find(FName(TEXT("StepSlash")));
    if (Step)
    {
        FMHWIMoveDefinition Walk = *Step;
        Walk.DisplayName = FText::FromString(TEXT("Advancing Slash"));
        Moveset->Moves.Add(FName(TEXT("WalkOnSlash")), Walk);
    }
    const FMHWIMoveDefinition* Roll = Moveset->Moves.Find(FName(TEXT("Roll")));
    if (!Roll || !Roll->Montage || Roll->Montage->SlotAnimTracks.Num() != 1) return;
    const FMHWIMoveDefinition Base = *Roll;
    const FName Names[] = {TEXT("Roll"), TEXT("RollLeft"), TEXT("RollRight"), TEXT("RollBack")};
    const int32 Motions[] = {11, 12, 13, 10}; // Native action18/19/20/21/22 constructors.
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Names); ++Index)
    {
        UAnimSequence* Sequence = NativeSourceSequences.FindRef(SourceKey(TEXT("w03_00"), Motions[Index]));
        if (!Sequence || Sequence->GetSkeleton() != Base.Montage->GetSkeleton()) continue;
        FMHWIMoveDefinition Definition = Base;
        Definition.Montage = UAnimMontage::CreateSlotAnimationAsDynamicMontage(Sequence,
            Base.Montage->SlotAnimTracks[0].SlotName, 0.f, 0.f, 1.f, 1);
        if (!Definition.Montage) continue;
        Definition.SheathedMontage = Index == 0 ? Base.SheathedMontage : nullptr;
        Definition.DisplayName = Index == 0 ? Base.DisplayName : FText::FromName(Names[Index]);
        Moveset->Moves.Add(Names[Index], Definition);
    }
}

FName AMHWICharacter::SelectRollMove() const
{
    if (bSheathed) return TEXT("Roll");
    const FVector Intent = GetMoveIntentWorldDirection();
    if (Intent.IsNearlyZero()) return TEXT("Roll");
    const float Forward = FVector::DotProduct(Intent, GetActorForwardVector());
    const float Side = FVector::DotProduct(Intent, GetActorRightVector());
    if (FMath::Abs(Side) > FMath::Abs(Forward)) return Side < 0.f ? TEXT("RollLeft") : TEXT("RollRight");
    return Forward < 0.f ? TEXT("RollBack") : TEXT("Roll");
}

void AMHWICharacter::StartNativeImpact(EMHWIImpactSize Size)
{
    if (bEnding || !Attributes || !Attributes->IsAlive()) return;
    if (bDispatchingHits)
    {
        PendingNativeImpact = Size;
        bPendingInterruption = true;
        return;
    }
    const int32 Index = FMath::Clamp(int32(Size), 0, 2);
    const int32 Common[] = {103, 110, 115};
    if (StartNativeSource(bSheathed ? MHWI::Native::FActionIdentity{1, Common[Index]}
        : MHWI::Native::FActionIdentity{3, 30 + Index}, ENativeSourceKind::Impact))
    {
        // R24: the impact montage owns control until it ends. Input checks read
        // this state instead of inferring hitstun from the montage pointer.
        ControlState = Size == EMHWIImpactSize::Large ? EMHWIControlState::FlinchLarge
            : (Size == EMHWIImpactSize::Medium ? EMHWIControlState::FlinchMedium
                : EMHWIControlState::FlinchSmall);
        PendingInput.Reset();
        bBufferedInsideWindow = false;
        bHelmSlamRequested = false;
    }
    else InterruptMove();
}

bool AMHWICharacter::StartNativeSource(MHWI::Native::FActionIdentity Identity, ENativeSourceKind Kind)
{
    using namespace MHWI::Native;
    if (!IsInGameThread() || bEnding || bFinishing || bDispatchingHits || !Moveset
        || !Attributes || !Attributes->IsAlive()) return false;
    const FSourceBinding* Binding = GetSourceBinding(Identity);
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    const FMHWIMoveDefinition* SlotDefinition = Moveset->Moves.Find(FName(TEXT("StepSlash")));
    if (!Binding || !Anim || !SlotDefinition || !SlotDefinition->Montage
        || SlotDefinition->Montage->SlotAnimTracks.Num() != 1) return false;
    FActionIdentity PreviousIdentity;
    const TArray<FActionIdentity> PreviousIds = GetNodeIdentities(NativeActionNode);
    if (!PreviousIds.IsEmpty()) PreviousIdentity = PreviousIds[0];
    if (Kind == ENativeSourceKind::Slinger)
    {
        const int32 Direction = (Identity.Action - 104) % 3;
        if (bSheathed || !ActiveMontage || bNativeConnector || SlingerAmmo <= 0
            || GetSlingerAction(NativeActionNode, Direction) != Identity.Action) return false;
    }
    const int32 Motion = Kind == ENativeSourceKind::Slinger ? GetSlingerMotion(Identity, PreviousIdentity) : Binding->Motion;
    UAnimSequence* Sequence = NativeSourceSequences.FindRef(SourceKey(Binding->Bank, Motion));
    if (!Sequence || !GetMesh()->GetSkeletalMeshAsset()
        || Sequence->GetSkeleton() != GetMesh()->GetSkeletalMeshAsset()->GetSkeleton()) return false;
    UAnimMontage* Montage = UAnimMontage::CreateSlotAnimationAsDynamicMontage(Sequence,
        SlotDefinition->Montage->SlotAnimTracks[0].SlotName, 0.f, 0.f, 1.f, 1);
    if (!Montage) return false;
    Montage->bEnableAutoBlendOut = false;
    UAnimMontage* PreviousCarrier = ActiveMontage ? ActiveMontage.Get() : NativeSourceMontage.Get();
    FMotionSample Previous;
    if (PreviousCarrier)
    {
        const int32 PreviousId = ActiveMontage ? ActiveMontageInstanceId : NativeSourceInstanceId;
        const FAnimMontageInstance* Instance = Anim->GetMontageInstanceForID(PreviousId);
        if (!Instance || Instance->Montage != PreviousCarrier || !ReadMotion(PreviousCarrier, Instance->GetPosition(), Previous)) return false;
        if (ActiveMontage && NativeTimelineMotion != INDEX_NONE) Previous.Motion = NativeTimelineMotion;
    }
    else if (UMHWIAnimInstance* NativeAnim = Cast<UMHWIAnimInstance>(Anim)) NativeAnim->ReadNativeBaseMotion(Previous);
    TOptional<FBlendEntry> Blend;
    if (const FBlendEntry* Entry = FindBlend(GetSourceBlends(Binding->Bank), Motion, Previous)) Blend = *Entry;
    const float StartFrame = Blend.IsSet() ? float(Blend->StartFrame) : 0.f;
    float Start;
    if (!MotionPosition(Montage, Binding->Bank, Motion, StartFrame, Start)) return false;
    const bool bWasSheathed = bSheathed;
    FinishMove(true, false, false, true);
    NativeRetiringMontage = PreviousCarrier;
    if (bEnding || !Attributes->IsAlive()) { FinishMove(true, true); return false; }
    if (!ApplyNativeBlend(Montage, Blend)) { FinishMove(true, true); return false; }
    if (UMHWIAnimInstance* NativeAnim = Cast<UMHWIAnimInstance>(Anim))
        NativeAnim->BeginNativeBlend(FMath::RoundToInt(FMath::Max(0.f, NativeBlendFrames)));
    if (Anim->Montage_Play(Montage, 1.f, EMontagePlayReturnType::MontageLength, Start, true) <= 0.f)
    { FinishMove(true, true); return false; }
    FAnimMontageInstance* Instance = Anim->GetActiveInstanceForMontage(Montage);
    const uint32 Token = Instance ? BindNativeActionSource(Montage, Instance->GetInstanceID(), Identity) : 0;
    if (!Token)
    {
        Anim->Montage_Stop(0.f, Montage);
        FinishMove(true, true);
        return false;
    }
    NativeRetiringMontage = nullptr;
    NativeSourceKind = Kind;
    NativeSourceMove = Kind == ENativeSourceKind::Slinger ? GetSlingerMove(Identity.Action)
        : FName(Kind == ENativeSourceKind::Recoil ? TEXT("WeaponRecoil") : TEXT("HitReaction"));
    NativeSourceLastSample = {Binding->Bank, Motion, StartFrame};
    NativeSourcePosition = Start;
    bMoveStartedSheathed = bWasSheathed;
    bNativeSourceEnded = bNativeSourceInterrupted = bNativeSlingerFired = false;
    FOnMontageEnded End;
    End.BindUObject(this, &AMHWICharacter::NativeSourceEnded, Token);
    Anim->Montage_SetEndDelegate(End, Montage);
    GetCharacterMovement()->StopMovementImmediately();
    AdvanceNativeSourceEvents({Binding->Bank, Motion, -1.f}, NativeSourceLastSample);
    RefreshMovement();
    RefreshWeaponAttachment();
    if (!bEnding && NativeSourceGeneration == Token)
    {
        OnMoveChanged.Broadcast(NativeSourceMove, FText::FromName(NativeSourceMove));
        if (!bEnding && NativeSourceGeneration == Token) OnStateChanged.Broadcast();
    }
    return !bEnding && NativeSourceGeneration == Token;
}

void AMHWICharacter::NativeSourceEnded(UAnimMontage* Montage, bool bInterrupted, uint32 Token)
{
    if (bEnding || Token != NativeSourceGeneration || Montage != NativeSourceMontage) return;
    bNativeSourceEnded = true;
    bNativeSourceInterrupted = bInterrupted;
}

bool AMHWICharacter::RequestNativeSourceInput(EMHWIInput Input)
{
    if (NativeSourceKind == ENativeSourceKind::None || !NativeSourceMontage || IsGestureLocked()) return false;
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    const FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(NativeSourceInstanceId) : nullptr;
    MHWI::Native::FMotionSample Sample;
    if (!Instance || Instance->Montage != NativeSourceMontage || !Instance->IsActive()
        || !MHWI::Native::ReadMotion(NativeSourceMontage, Instance->GetPosition(), Sample)) return false;
    NativeSourceInput = Input;
    NativeSourceInputFrame = Sample.Frame;
    NativeSourceInputExpires = GetWorld()->GetTimeSeconds() + FMath::Max(0.f, Moveset->InputBufferSeconds);
    return true;
}

bool AMHWICharacter::ResolveNativeSourceInput(EMHWIInput Input, FName& Move) const
{
    if (NativeSourceKind == ENativeSourceKind::Slinger)
    {
        const int32 Stage = (NativeSourceIdentity.Action - 104) / 3;
        if (Input == EMHWIInput::Spirit) Move = Stage == 0 ? TEXT("SpiritII") : (Stage == 1 ? TEXT("SpiritIII") : TEXT("SpiritRoundslash"));
        else if (Stage < 2 && (Input == EMHWIInput::Light || Input == EMHWIInput::Thrust))
            Move = Stage == 0 ? TEXT("SpiritComboThrust") : TEXT("SpiritComboRisingSlash");
        else if (Input == EMHWIInput::FadeSlash) Move = SelectFadeSlashMove();
        else if (Input == EMHWIInput::HelmBreaker) Move = TEXT("SpiritThrust");
        else if (Input == EMHWIInput::Foresight) Move = TEXT("ForesightSlash");
        else if (Input == EMHWIInput::SpecialSheathe) Move = TEXT("SpecialSheathe");
        else if (Input == EMHWIInput::Evade) Move = SelectRollMove();
    }
    else if (NativeSourceKind == ENativeSourceKind::Recoil)
    {
        if (Input == EMHWIInput::Light || Input == EMHWIInput::Thrust) Move = TEXT("StepSlash");
    }
    else if (NativeSourceKind == ENativeSourceKind::Impact)
    {
        if (Input == EMHWIInput::Spirit) Move = TEXT("SpiritI");
        else if (Input == EMHWIInput::Light) Move = TEXT("StepSlash");
        else if (Input == EMHWIInput::Thrust) Move = bSheathed ? TEXT("StepSlash") : TEXT("Thrust");
        else if (!bSheathed && Input == EMHWIInput::FadeSlash) Move = SelectFadeSlashMove();
        else if (!bSheathed && Input == EMHWIInput::HelmBreaker) Move = TEXT("SpiritThrust");
        else if (!bSheathed && Input == EMHWIInput::SpecialSheathe) Move = TEXT("SpecialSheathe");
    }
    return !Move.IsNone() && Moveset && Moveset->Moves.Contains(Move);
}

void AMHWICharacter::FireNativeSlinger()
{
    if (bNativeSlingerFired || SlingerAmmo <= 0 || !GetWorld()) return;
    bNativeSlingerFired = true;
    --SlingerAmmo;
    const uint32 Token = NativeSourceGeneration;
    const FVector Start = GetPawnViewLocation();
    const FVector Direction = GetControlRotation().Vector();
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(MHWISlingerBurst), false, this);
    if (GetWorld()->LineTraceSingleByChannel(Hit, Start, Start + Direction * 10000.f, ECC_Visibility, Params))
        if (AActor* Target = Hit.GetActor(); IsValid(Target))
            if (UAttributeComponent* TargetAttributes = Target->FindComponentByClass<UAttributeComponent>())
                TargetAttributes->ApplyDamage(FMath::Max(0.f, SlingerBurstDamage), this);
    if (!bEnding && Token == NativeSourceGeneration) OnStateChanged.Broadcast();
}

void AMHWICharacter::AdvanceNativeSourceEvents(const MHWI::Native::FMotionSample& From,
    const MHWI::Native::FMotionSample& To)
{
    const uint32 Token = NativeSourceGeneration;
    for (const MHWI::Native::FSourceWeaponKey& Key : MHWI::Native::GetSourceWeaponKeys())
        if (Key.Bank == To.Bank && Key.Motion == To.Motion && Key.Value >= 0 && Key.Frame > From.Frame && Key.Frame <= To.Frame)
            SetSourceWeaponMotion(Key.Value);
    if (NativeSourceKind == ENativeSourceKind::Slinger && !bNativeSlingerFired)
    {
        const float Trigger = MHWI::Native::GetSlingerTriggerFrame(To.Motion);
        if (Trigger >= 0.f && Trigger > From.Frame && Trigger <= To.Frame) FireNativeSlinger();
    }
    if (Token != NativeSourceGeneration) return;
}

bool AMHWICharacter::TickNativeSource()
{
    using namespace MHWI::Native;
    if (!NativeSourceMontage || NativeSourceKind == ENativeSourceKind::None) return false;
    if (bNativeSourceInterrupted) { FinishMove(true, true); return true; }
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    const FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(NativeSourceInstanceId) : nullptr;
    if (Instance && Instance->Montage == NativeSourceMontage && Instance->IsActive()
        && Instance->GetPosition() >= NativeSourceMontage->GetPlayLength() - KINDA_SMALL_NUMBER)
        bNativeSourceEnded = true; // Auto-blend-out is disabled; the real carrier can hold its end pose.
    if (!bNativeSourceEnded && (!Instance || Instance->Montage != NativeSourceMontage
        || !Instance->IsActive() || !Instance->IsPlaying()))
    { FinishMove(true, true); return true; }
    const float Position = bNativeSourceEnded ? NativeSourceMontage->GetPlayLength() : (Instance ? Instance->GetPosition() : -1.f);
    FMotionSample Current;
    if (Position < NativeSourcePosition || !ReadMotion(NativeSourceMontage, Position, Current)
        || Current.Bank != NativeSourceLastSample.Bank || Current.Motion != NativeSourceLastSample.Motion)
    { FinishMove(true, true); return true; }
    const uint32 Token = NativeSourceGeneration;
    const float Advance = Current.Frame - NativeSourceLastSample.Frame;
    AdvanceNativeSourceEvents(NativeSourceLastSample, Current);
    if (Token != NativeSourceGeneration || bEnding || !Attributes->IsAlive()) return true;
    NativeSourceLastSample = Current;
    NativeSourcePosition = Position;
    if (NativeSourceInput.IsSet())
    {
        const float Cancel = 60.f * (NativeSourceKind == ENativeSourceKind::Impact ? ImpactCancelStart
            : (NativeSourceKind == ENativeSourceKind::Recoil ? RecoilCancelStart : SlingerCancelStart));
        FName Next;
        if (GetWorld()->GetTimeSeconds() <= NativeSourceInputExpires && Current.Frame >= FMath::Max(Cancel, NativeSourceInputFrame)
            && (NativeSourceKind != ENativeSourceKind::Slinger || bNativeSlingerFired)
            && ResolveNativeSourceInput(NativeSourceInput.GetValue(), Next) && StartResolvedMove(Next)) return true;
        if (Token != NativeSourceGeneration || bEnding) return true;
        if (GetWorld()->GetTimeSeconds() > NativeSourceInputExpires) NativeSourceInput.Reset();
    }
    const FMotionInfo* Info = GetSourceMotionInfo(Current.Bank, Current.Motion);
    if (!Info || IsMotionEnded(ForwardEndFlags(Current.Frame, Advance, Info->Frames - 1), false, false) || bNativeSourceEnded)
        FinishMove(false, true);
    return true;
}
