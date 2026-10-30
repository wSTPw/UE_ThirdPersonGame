#include "MHWICharacter.h"
#include "MHWIAnimInstance.h"
#include "AttributeComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/UObjectGlobals.h"

namespace
{
    UAnimMontage* CopyNativePlaybackMontage(UAnimMontage* Source, UObject* Owner)
    {
        if (!Source) return nullptr;
        if (!Source->IsDynamicMontage()) return DuplicateObject<UAnimMontage>(Source, Owner);
        // A dynamically created montage has a runtime SequenceLength but no
        // authored editor data-model length. DuplicateObject into a PIE actor
        // resets that length to zero (B20 actual 1.333333 -> 0). Recreate via
        // the engine's supported factory, keeping it transient and strongly
        // referenced by ActiveMontage/NativeMainMontage. Never invent a length.
        if (Source->SlotAnimTracks.Num() != 1) return nullptr;
        const FSlotAnimationTrack& Track = Source->SlotAnimTracks[0];
        if (Track.AnimTrack.AnimSegments.Num() != 1) return nullptr;
        const FAnimSegment& Segment = Track.AnimTrack.AnimSegments[0];
        UAnimSequenceBase* Sequence = Segment.GetAnimReference();
        if (!Sequence || Segment.LoopingCount != 1 || !FMath::IsNearlyZero(Segment.AnimStartTime)
            || !FMath::IsNearlyEqual(Segment.AnimEndTime, Sequence->GetPlayLength())
            || !FMath::IsNearlyEqual(Segment.AnimPlayRate, 1.f) || !Source->Notifies.IsEmpty()) return nullptr;
        UAnimMontage* Copy = UAnimMontage::CreateSlotAnimationAsDynamicMontage(Sequence,
            Track.SlotName, Source->BlendIn.GetBlendTime(), Source->BlendOut.GetBlendTime(),
            1.f, 1, Source->BlendOutTriggerTime);
        if (Copy)
        {
            Copy->bEnableAutoBlendOut = Source->bEnableAutoBlendOut;
            Copy->RateScale = Source->RateScale;
        }
        return Copy;
    }
}

FString AMHWICharacter::GetNativePlaybackDiagnostic() const
{
    check(IsInGameThread());
    UAnimInstance* Anim = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
    UAnimMontage* Carrier = ActiveMontage ? ActiveMontage.Get() : NativeSourceMontage.Get();
    const int32 InstanceId = ActiveMontage ? ActiveMontageInstanceId : NativeSourceInstanceId;
    const FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(InstanceId) : nullptr;
    MHWI::Native::FMotionSample Sample;
    if (!Carrier || !Instance || Instance->Montage != Carrier
        || !MHWI::Native::ReadMotion(Carrier, Instance->GetPosition(), Sample)) return TEXT("none");
    return FString::Printf(
        TEXT("move=%s connector=%d bank=%s body=%d timeline=%d frame=%.3f instance=%d serial=%u gauge_start=%.3f gauge=%.3f"),
        *GetCurrentMove().ToString(), bNativeConnector ? 1 : 0, *Sample.Bank.ToString(),
        Sample.Motion, NativeTimelineMotion, Sample.Frame, InstanceId, ExecutionSerial,
        CapturedSpiritGauge, SpiritGauge);
}

uint32 AMHWICharacter::BindNativeActionSource(UAnimMontage* Montage, int32 InstanceId,
    MHWI::Native::FActionIdentity Identity)
{
    if (!IsInGameThread() || bEnding || bFinishing || !CurrentMove.IsNone()
        || !Attributes || !Attributes->IsAlive()
        || !MHWI::Native::IsKnownSourceIdentity(Identity)) return 0;
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    const FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(InstanceId) : nullptr;
    MHWI::Native::FMotionSample Sample;
    if (!Montage || !Instance || Instance->Montage != Montage || !Instance->IsActive()
        || !GetMesh()->GetSkeletalMeshAsset()
        || Montage->GetSkeleton() != GetMesh()->GetSkeletalMeshAsset()->GetSkeleton()
        || !MHWI::Native::ReadMotion(Montage, Instance->GetPosition(), Sample)) return 0;
    if (const MHWI::Native::FSourceBinding* Binding = MHWI::Native::GetSourceBinding(Identity))
    {
        const bool bSlingerVariant = Identity.Group == 3 && Identity.Action >= 107 && Identity.Action <= 109
            && (Sample.Motion == MHWI::Native::GetSlingerMotion(Identity, {3, 70})
                || Sample.Motion == MHWI::Native::GetSlingerMotion(Identity, {3, 78}));
        if (Sample.Bank != Binding->Bank || (Sample.Motion != Binding->Motion && !bSlingerVariant)) return 0;
    }
    NativeSourceMontage = Montage;
    NativeSourceInstanceId = InstanceId;
    NativeSourceIdentity = Identity;
    if (++NativeSourceGeneration == 0) ++NativeSourceGeneration;
    return NativeSourceGeneration;
}

void AMHWICharacter::ReleaseNativeActionSource(uint32 BindingToken)
{
    if (!IsInGameThread() || BindingToken == 0 || BindingToken != NativeSourceGeneration) return;
    NativeSourceMontage = nullptr;
    NativeSourceInstanceId = INDEX_NONE;
    NativeSourceIdentity = {};
    NativeSourceKind = ENativeSourceKind::None;
    NativeSourceMove = NAME_None;
    NativeSourceInput.Reset();
    NativeSourceLastSample = {};
    bNativeSourceEnded = bNativeSourceInterrupted = bNativeSlingerFired = false;
    if (++NativeSourceGeneration == 0) ++NativeSourceGeneration;
}

bool AMHWICharacter::PrepareNativeLink(FName MoveId, UAnimMontage* Main, FNativeLinkStart& Out)
{
    using namespace MHWI::Native;
    LastNativeEntryDiagnostic.Reset();
    if (!Main || bNativeConnector) return false;
    UMHWIAnimInstance* BaseAnim = Cast<UMHWIAnimInstance>(GetMesh()->GetAnimInstance());
    Out.TargetNode = GetMoveNode(MoveId, bSheathed);
    int32 PreviousNode = NativeActionNode;
    if (ActiveMontage)
    {
        if (ActiveMontage->GetGroupName() != Main->GetGroupName()) return false;
        UAnimInstance* Anim = GetMesh()->GetAnimInstance();
        const FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(ActiveMontageInstanceId) : nullptr;
        if (!Instance || Instance->Montage != ActiveMontage) return false;
        Out.PreviousCarrier = ActiveMontage;
        Out.PreviousPosition = Instance->GetPosition();
        if (!ReadMotion(ActiveMontage, Out.PreviousPosition, Out.Previous)) return false;
        if (NativeTimelineMotion != INDEX_NONE) Out.Previous.Motion = NativeTimelineMotion;
    }
    else if (NativeSourceMontage)
    {
        if (NativeSourceMontage->GetGroupName() != Main->GetGroupName()) return false;
        UAnimInstance* Anim = GetMesh()->GetAnimInstance();
        const FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(NativeSourceInstanceId) : nullptr;
        Out.PreviousCarrier = NativeSourceMontage;
        if (bNativeSourceEnded && !bNativeSourceInterrupted && NativeSourceKind != ENativeSourceKind::None)
        {
            // Natural-end delivery is a fact from this source owner's bound token,
            // not a stale cached position used to authorize an external carrier.
            Out.PreviousPosition = NativeSourceMontage->GetPlayLength();
            if (!ReadMotion(NativeSourceMontage, Out.PreviousPosition, Out.Previous)) return false;
        }
        else
        {
            if (!Instance || !Instance->IsActive() || Instance->Montage != NativeSourceMontage) return false;
            Out.PreviousPosition = Instance->GetPosition();
            if (!ReadMotion(NativeSourceMontage, Out.PreviousPosition, Out.Previous)) return false;
        }
        Out.PreviousIdentity = NativeSourceIdentity;
        Out.bExactPreviousIdentity = true;
    }
    else if (MoveId == FName(TEXT("RollStepSlash")) && CanUseRollRecovery()
        && (!BaseAnim || !BaseAnim->bLocomotionTransitionActive)
        && NativeRollRecoverySample.Motion != INDEX_NONE)
    {
        PreviousNode = NativeRollRecoveryNode;
        Out.Previous = NativeRollRecoverySample;
    }
    else if (!bSheathed)
    {
        if (UMHWIAnimInstance* Anim = Cast<UMHWIAnimInstance>(GetMesh()->GetAnimInstance()))
            if (Anim->ReadNativeBaseMotion(Out.Previous))
            {
                // Use the actual current locomotion owner. A completed roll's
                // cached identity cannot override its now-playing 014/015 exit.
                Out.PreviousIdentity = {3, Anim->Speed > KINDA_SMALL_NUMBER ? 1 : 0};
                if (Anim->bLocomotionTransitionActive && Anim->LocomotionTransitionMotion == 8)
                    Out.PreviousIdentity = {3, 2}; // Actual WALK_END owner, not an IDLE alias.
                if (Anim->bLocomotionTransitionActive && Anim->LocomotionTransitionMotion == 14)
                    Out.PreviousIdentity = {3, 65};
                if (Anim->bLocomotionTransitionActive && Anim->LocomotionTransitionMotion == 15)
                    Out.PreviousIdentity = {3, 66};
                Out.bExactPreviousIdentity = true;
            }
    }
    const bool bHasMain = ReadMainMotion(Main, Out.MainMotion);
    const int32 NativeMain = GetNativeMainMotion(Out.TargetNode);
    if (NativeMain != INDEX_NONE && (!bHasMain || Out.MainMotion != NativeMain)) return false;
    if (!bHasMain) return true; // Existing non-weapon-bank moves have no R06 override.

    TArray<FActionIdentity> PreviousIds = Out.bExactPreviousIdentity
        ? TArray<FActionIdentity>{Out.PreviousIdentity} : GetNodeIdentities(PreviousNode);
    if (PreviousNode == 1 && !Out.bExactPreviousIdentity)
    {
        const FMHWIMoveDefinition* Definition = Moveset ? Moveset->Moves.Find(CurrentMove) : nullptr;
        PreviousIds = {{3, Definition && CapturedSpiritGauge < Definition->SpiritCost ? 12 : 11}};
    }
    if (PreviousIds.IsEmpty()) PreviousIds.Add({});
    TArray<FActionIdentity> Targets = GetNodeIdentities(Out.TargetNode);
    FActionIdentity Target = Targets.IsEmpty() ? FActionIdentity{} : Targets[0];
    if (Out.TargetNode == 1)
    {
        const FMHWIMoveDefinition* Definition = Moveset ? Moveset->Moves.Find(MoveId) : nullptr;
        Target = {3, Definition && Definition->bAllowWeakSpiritAttack && SpiritGauge < Definition->SpiritCost ? 12 : 11};
    }
    const FActionEntryPlan Plan = ResolveActionEntry(Out.TargetNode, Target, PreviousIds[0], !bSheathed,
        Out.MainMotion, Out.Previous);
    for (int32 Index = 1; Index < PreviousIds.Num(); ++Index)
    {
        const FActionEntryPlan Other = ResolveActionEntry(Out.TargetNode, Target, PreviousIds[Index], !bSheathed,
            Out.MainMotion, Out.Previous);
        if (Other.First.Motion != Plan.First.Motion || Other.bFollowMain != Plan.bFollowMain
            || Other.bContinuePrevious != Plan.bContinuePrevious
            || Other.BlendPrevious.Bank != Plan.BlendPrevious.Bank
            || Other.BlendPrevious.Motion != Plan.BlendPrevious.Motion
            || Other.BlendPrevious.Frame != Plan.BlendPrevious.Frame) return false;
    }
    Out.Entry = Plan.Link;
    LastNativeEntryDiagnostic = FString::Printf(
        TEXT("target=%d/%d previous=%d/%d bank=%s motion=%d frame=%.3f phase=%d first=%d main=%d"),
        Target.Group, Target.Action, PreviousIds[0].Group, PreviousIds[0].Action,
        *Out.Previous.Bank.ToString(), Out.Previous.Motion, Out.Previous.Frame,
        SampleLinkPhase(Out.Previous), Plan.First.Motion, Out.MainMotion);
    Out.bFollowMain = Plan.bFollowMain;
    Out.bContinuePrevious = Plan.bContinuePrevious;
    Out.FirstRequest = Plan.First;
    Out.Previous = Plan.BlendPrevious;
    if (Plan.bContinuePrevious && bNativeSourceEnded && !bNativeSourceInterrupted && Plan.bFollowMain)
    {
        // The owned source already delivered its natural end. Commit its custom
        // follow-up now; a retired instance cannot be adopted as a live prefix.
        Out.Entry = nullptr;
        Out.bContinuePrevious = Out.bFollowMain = false;
        Out.FirstRequest = {};
        Out.FirstRequest.Motion = Out.MainMotion;
        if (const FBlendEntry* Blend = FindBlend(GetLongSwordBlendEntries(), Out.MainMotion, Out.Previous))
            Out.FirstRequest.Blend = *Blend;
        return !Out.FirstRequest.Blend.IsSet() || MainPosition(Main, Out.MainMotion,
            Out.FirstRequest.Blend->StartFrame, Out.FirstPosition);
    }
    const bool bPrefix = Plan.bFollowMain || Plan.First.Motion != Out.MainMotion;
    if (!bPrefix)
        return !Plan.First.Blend.IsSet() || MainPosition(Main, Out.MainMotion,
            Plan.First.Blend->StartFrame, Out.FirstPosition);
    Out.ExplicitConnector = Plan.First.Motion;
    if (Plan.bContinuePrevious)
        return Out.PreviousCarrier != nullptr;
    const TObjectPtr<UAnimSequence>* Sequence = NativeConnectorSequences.Find(Plan.First.Motion);
    const FMotionInfo* Info = GetMotionInfo(Plan.First.Motion);
    if (!Sequence || !*Sequence || !Info || Info->Loop >= 0 || Info->Frames <= 1) return false;
    const int32 Frame = Plan.First.Blend.IsSet() ? Plan.First.Blend->StartFrame : 0;
    if (Frame < 0 || Frame >= Info->Frames - 1) return false;
    if (Plan.bFollowMain)
    {
        const FMotionSample End{FName(TEXT("w03_00")), Plan.First.Motion, float(Info->Frames - 1)};
        const FBlendEntry* Blend = FindBlend(GetLongSwordBlendEntries(), Out.MainMotion, End);
        float Position;
        if (!Blend || !MainPosition(Main, Out.MainMotion, Blend->StartFrame, Position)) return false;
    }
    return true;
}

bool AMHWICharacter::ApplyNativeBlend(UAnimMontage* Montage,
    const TOptional<MHWI::Native::FBlendEntry>& Blend)
{
    NativeBlendFrames = -1.f;
    if (!Montage) return false;
    if (!Blend.IsSet()) return true;
    MHWI::Native::FMotionSample Sample;
    MHWI::Native::FDirectBlendSettings Settings;
    if (!MHWI::Native::ReadMotion(Montage, 0.f, Sample)) return false;
    if (!MHWI::Native::ResolveDirectBlendSettings(Sample.Bank, Blend.GetValue(), Settings))
    {
        // ProjectAdaptation: all serialized weapon main/connector defaults are
        // mode0, whose native MotionTree/request consumer is still unresolved.
        // Do not reject the animation before playback, and do not pretend the
        // native mode1 pose proxy or automatic tail fade applies. Use the raw
        // interpolation frame count only as a documented UE BlendIn duration.
        if (Sample.Bank != FName(TEXT("w03_00")) || Blend->One0 != 0) return false;
        NativeBlendFrames = -1.f;
        Montage->BlendIn.SetBlendTime(FMath::Max(0, Blend->InterpolationPoint) / 60.f);
        return true;
    }
    // R06 weapon requests go directly to bank12 leaves. wp03_tree.at has
    // only bank1 node IDs 1000..11ff; no node injects request bits100/200 here.
    // MBD mode(one0)=1 adds request bit2, +30/+34 curve selectors remain zero.
    // Thus interpolation is a previous-pose capture; overlap is disabled even
    // when its raw MBD number is nonzero. Common standing reactions use mode0:
    // immediate layer replacement forwards request+c via tree+4368 to the model
    // (142255b98 / 142254e6b), using the same displayed-pose interpolation.
    // Both qualified paths keep the destination root extraction at full weight.
    NativeBlendFrames = float(Settings.PoseInterpolationFrames);
    Montage->BlendIn.SetBlendTime(0.f);
    Montage->BlendOut.SetBlendTime(0.f);
    return true;
}

bool AMHWICharacter::BeginNativeLink(const FNativeLinkStart& Start)
{
    using namespace MHWI::Native;
    if (!ActiveMontage) return false;
    NativeInitialPosition = Start.FirstPosition;
    NativeBlendFrames = -1.f;
    if (!Start.Entry && Start.ExplicitConnector == INDEX_NONE)
    {
        if (Start.FirstRequest.Blend.IsSet())
        {
            UAnimMontage* Main = CopyNativePlaybackMontage(ActiveMontage, this);
            if (!Main) return false;
            if (!ApplyNativeBlend(Main, Start.FirstRequest.Blend)) return false;
            ActiveMontage = Main;
        }
        return true;
    }
    NativeMainMontage = ActiveMontage;
    const int32 MainMotion = Start.bFollowMain ? Start.MainMotion : INDEX_NONE;
    const FPlaybackRequest Request = NativeLinkExecution.BeginExplicitConnector(GetLongSwordBlendEntries(),
        Start.ExplicitConnector, MainMotion, Start.Previous,
        Start.bContinuePrevious ? Start.Previous.Bank : FName(TEXT("w03_00")));
    if (Start.bContinuePrevious)
    {
        ActiveMontage = Start.PreviousCarrier;
        NativeConnectorPosition = NativeInitialPosition = Start.PreviousPosition;
        NativeConnectorSourceFrame = Start.Previous.Frame;
        bNativeConnector = true;
        return ActiveMontage != nullptr;
    }
    UAnimSequence* Sequence = NativeConnectorSequences.FindRef(Request.Motion);
    if (!Sequence || Sequence->GetSkeleton() != NativeMainMontage->GetSkeleton()
        || NativeMainMontage->SlotAnimTracks.Num() != 1) return false;
    UAnimMontage* Connector = UAnimMontage::CreateSlotAnimationAsDynamicMontage(Sequence,
        NativeMainMontage->SlotAnimTracks[0].SlotName, 0.f, 0.f, 1.f, 1);
    if (!Connector) return false;
    Connector->bEnableAutoBlendOut = false;
    if (!ApplyNativeBlend(Connector, Start.FirstRequest.Blend)) return false;
    const int32 EntryFrame = Start.FirstRequest.Blend.IsSet() ? Start.FirstRequest.Blend->StartFrame : 0;
    if (!MotionPosition(Connector, FName(TEXT("w03_00")), Request.Motion,
        float(EntryFrame), NativeConnectorPosition)) return false;
    NativeConnectorSourceFrame = float(EntryFrame);
    NativeInitialPosition = NativeConnectorPosition;
    ActiveMontage = Connector;
    bNativeConnector = true;
    return true;
}

void AMHWICharacter::AdvanceConnectorWeaponEvents(float FromSourceFrame, float ToSourceFrame)
{
    const int32 Motion = NativeLinkExecution.GetConnectorMotion();
    for (const MHWI::Native::FSourceWeaponKey& Key : MHWI::Native::GetSourceWeaponKeys())
        if (Key.Bank == NativeLinkExecution.GetConnectorBank() && Key.Motion == Motion && Key.Value >= 0 && Key.Frame > FromSourceFrame && Key.Frame <= ToSourceFrame)
        {
            const float SourceDelta = ToSourceFrame - FromSourceFrame;
            const float CatchUp = FromSourceFrame >= 0.f && SourceDelta > SMALL_NUMBER && GetWorld()
                ? GetWorld()->GetDeltaSeconds() * CustomTimeDilation
                    * FMath::Clamp((ToSourceFrame - Key.Frame) / SourceDelta, 0.f, 1.f) : 0.f;
            SetSourceWeaponMotion(Key.Value, CatchUp);
        }
}

bool AMHWICharacter::AdvanceNativeLink(float Position, bool bNaturalEnd)
{
    using namespace MHWI::Native;
    if (!bNativeConnector || !ActiveMontage || !NativeMainMontage) return false;
    FMotionSample Current;
    const FMotionInfo* Info = GetSourceMotionInfo(NativeLinkExecution.GetConnectorBank(), NativeLinkExecution.GetConnectorMotion());
    if (bNaturalEnd && Info)
        Current = {NativeLinkExecution.GetConnectorBank(), Info->Motion, float(Info->Frames - 1)};
    else if (!ReadMotion(ActiveMontage, Position, Current))
    {
        FinishMove(true, true);
        return false;
    }
    if (!Info || Position < NativeConnectorPosition || Current.Frame < NativeConnectorSourceFrame)
    {
        FinishMove(true, true);
        return false;
    }
    AdvanceConnectorWeaponEvents(NativeConnectorSourceFrame, Current.Frame);
    const float Advance = Current.Frame - NativeConnectorSourceFrame;
    NativeConnectorPosition = Position;
    NativeConnectorSourceFrame = Current.Frame;
    // Forward one-shot connector branch only. No timer, blend-out threshold or
    // source frame-count-as-duration shortcut; retain the native predictive bit.
    const uint32 Flags = ForwardEndFlags(Current.Frame, Advance, Info->Frames - 1)
        | (bNaturalEnd ? 4u : 0u);
    const TOptional<FPlaybackRequest> Main = NativeLinkExecution.Advance(GetLongSwordBlendEntries(),
        NativeLinkExecution.GetGeneration(), Flags, false, false, Current);
    if (!Main.IsSet())
    {
        if (NativeLinkExecution.GetStage() == ELinkStage::Idle)
        { FinishMove(false, true); return true; }
        return false;
    }
    return CommitNativeMain(Main.GetValue());
}

bool AMHWICharacter::CommitNativeMain(const MHWI::Native::FPlaybackRequest& Request)
{
    using namespace MHWI::Native;
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    float Start = 0.f;
    if (!Anim || !NativeMainMontage || !Request.Blend.IsSet()
        || !MainPosition(NativeMainMontage, Request.Motion, Request.Blend->StartFrame, Start))
    {
        FinishMove(true, true);
        return false;
    }
    UAnimMontage* Main = CopyNativePlaybackMontage(NativeMainMontage, this);
    if (!Main) { FinishMove(true, true); return false; }
    // Replace the physical root-motion carrier at full weight; the proxy owns
    // the qualified linear displayed-pose interpolation on the owner clock.
    if (!ApplyNativeBlend(Main, Request.Blend)) { FinishMove(true, true); return false; }
    NativeRetiringMontage = ActiveMontage;
    ActiveMontage = Main; // Old connector's end callback cannot finish the main.
    ActiveMontageInstanceId = INDEX_NONE;
    NativeMainMontage = nullptr;
    bNativeConnector = false;
    // Montage_Play itself stops the previous root-motion instance using the new
    // blend settings. Do not first stop it with another curve/duration.
    const uint32 Serial = ExecutionSerial;
    InitializeMainEventClock(Start);
    if (UMHWIAnimInstance* NativeAnim = Cast<UMHWIAnimInstance>(Anim))
        NativeAnim->BeginNativeBlend(FMath::RoundToInt(NativeBlendFrames));
    if (Anim->Montage_Play(Main, ActiveDefinition.PlayRate * EvaluateSourcePlayRate(Start),
        EMontagePlayReturnType::MontageLength, Start, true) <= 0.f)
    {
        FinishMove(true, true);
        return false;
    }
    NativeRetiringMontage = nullptr;
    if (FAnimMontageInstance* Instance = Anim->GetActiveInstanceForMontage(Main))
        ActiveMontageInstanceId = Instance->GetInstanceID();
    FOnMontageEnded EndDelegate;
    EndDelegate.BindUObject(this, &AMHWICharacter::MontageEnded, Serial);
    Anim->Montage_SetEndDelegate(EndDelegate, Main);
    // Same action identity/captured gauge/hit sets and costs; this is a motion commit.
    return Serial == ExecutionSerial && !bEnding && Attributes->IsAlive();
}

void AMHWICharacter::InitializeMainEventClock(float Start)
{
    CurrentPosition = PreviousPosition = Start;
    PreviousActorLocation = GetActorLocation();
    ActionStartWorldTime = GetWorld()->GetTimeSeconds();
    // State-at-entry is applied once. Earlier weapon keys are not replayed and
    // skipped damage/turn/cancel intervals are never advanced from zero.
    NextWeaponMotionEvent = 0;
    int32 EntryWeapon = INDEX_NONE;
    for (const FMHWIWeaponMotionEvent& Event : ActiveDefinition.WeaponMotionEvents)
    {
        if (!FMath::IsFinite(Event.Time) || Event.Time < 0.f) { ++NextWeaponMotionEvent; continue; }
        if (Event.Time > Start) break;
        if (Event.MotionNo >= 0) EntryWeapon = Event.MotionNo;
        ++NextWeaponMotionEvent;
    }
    if (EntryWeapon >= 0) SetSourceWeaponMotion(EntryWeapon);
    if (PendingInput.IsSet())
    {
        PendingMontagePosition = Start;
        bBufferedInsideWindow = false;
    }
}
