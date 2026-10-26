#include "Actions/CharacterActionComponent.h"
#include "Actions/CharacterActionDefinition.h"
#include "Actions/CharacterActionExecution.h"
#include "Actions/AnimNotifyState_ActionWindow.h"
#include "MyPlayerCharacter.h"
#include "ConsumableData.h"
#include "AnimNotify_MeleeHit.h"
#include "AnimNotify_Fireball.h"
#include "AnimNotify_UseItemComplete.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimNotifyQueue.h"
#include "Animation/ActiveMontageInstanceScope.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "UObject/StrongObjectPtr.h"

DEFINE_LOG_CATEGORY_STATIC(LogCharacterActions, Log, All);

UCharacterActionComponent::UCharacterActionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    // Consume buffered transitions only after animation notification dispatch.
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UCharacterActionComponent::BeginPlay()
{
    Super::BeginPlay();
    Character = Cast<AMyPlayerCharacter>(GetOwner());
    if (Character && Character->GetMesh()) AddTickPrerequisiteComponent(Character->GetMesh());
    if (Character && Character->AttributeComp)
        Character->AttributeComp->OnCharacterDeath.AddUniqueDynamic(this, &ThisClass::OnOwnerDeath);
}

void UCharacterActionComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    bOwnerEnding = true;
    Finish(ECharacterActionEndReason::OwnerEnded);
    if (Character && Character->AttributeComp)
        Character->AttributeComp->OnCharacterDeath.RemoveDynamic(this, &ThisClass::OnOwnerDeath);
    Super::EndPlay(Reason);
}

bool UCharacterActionComponent::IsBusy() const { return Active != nullptr; }

ECharacterActionFailure UCharacterActionComponent::CheckPermission() const
{
    if (bOwnerEnding || !IsValid(Character) || !Character->AttributeComp || !Character->AttributeComp->IsAlive())
        return ECharacterActionFailure::Dead;
    if (bUIBlocked) return ECharacterActionFailure::UIBlocked;
    if (bFinishing || bDispatching) return ECharacterActionFailure::Busy;
    return ECharacterActionFailure::None;
}

bool UCharacterActionComponent::CanChangeEquipment() const
{
    return !Active && !bFinishing && !bDispatching && !bOwnerEnding && Character &&
        Character->AttributeComp && Character->AttributeComp->IsAlive();
}

void UCharacterActionComponent::SetUIBlocked(bool bBlocked) { bUIBlocked = bBlocked; }

FCharacterActionSnapshot UCharacterActionComponent::GetSnapshot() const
{
    FCharacterActionSnapshot Result = Active ? Active->State : FCharacterActionSnapshot();
    if (bUIBlocked || bOwnerEnding || (Character && Character->AttributeComp && !Character->AttributeComp->IsAlive()))
    {
        Result.MoveScale = 0.f;
        Result.bAllowJump = false;
    }
    return Result;
}

FCharacterActionRequestResult UCharacterActionComponent::Reject(ECharacterActionFailure Failure)
{
    LastFailure = Failure;
    FCharacterActionRequestResult Result;
    Result.Failure = Failure;
    UE_LOG(LogCharacterActions, Verbose, TEXT("Request rejected: reason=%d"), static_cast<int32>(Failure));
    return Result;
}

FCharacterActionRequestResult UCharacterActionComponent::RequestAttack()
{
    const auto Permission = CheckPermission();
    if (Permission != ECharacterActionFailure::None) return Reject(Permission);
    if (Active)
    {
        if (Active->State.Kind != ECharacterActionKind::Melee || Active->bBlendOut)
            return Reject(ECharacterActionFailure::Busy);
        bool bAcceptedInWindow = false;
        if (Active->Combo && Character->GetMesh())
            if (const auto* Anim = Character->GetMesh()->GetAnimInstance())
            {
                const float Relative = Anim->Montage_GetPosition(Active->Montage) - Active->SectionStart;
                if (Relative > Active->ChainEnd) return Reject(ECharacterActionFailure::Busy);
                if (Relative >= Active->ChainStart)
                {
                    // Accept now; a low frame rate must not expire an input
                    // already received inside the authored chain window.
                    Active->bNextHitQueued = true;
                    Active->BufferedUntil = -1;
                    bAcceptedInWindow = true;
                }
            }
        if (!bAcceptedInWindow && !Active->bNextHitQueued)
        {
            const float TTL = Active->Definition ? Active->Definition->InputBufferSeconds : InputBufferSeconds;
            Active->BufferedUntil = GetWorld()->GetTimeSeconds() + TTL;
        }
        FCharacterActionRequestResult Result;
        Result.Status = ECharacterActionRequestStatus::Buffered;
        Result.RunId = Active->State.RunId;
        return Result;
    }
    UWeaponData* Weapon = Character->CurrentWeaponData;
    if (!Weapon) return Reject(ECharacterActionFailure::InvalidSource);
    if (CooldownUntil.FindRef(Weapon->ItemID) > GetWorld()->GetTimeSeconds()) return Reject(ECharacterActionFailure::Cooldown);
    if (!FMath::IsFinite(Weapon->WeaponManaCost) || Weapon->WeaponManaCost < 0.f ||
        Character->AttributeComp->GetCurrentMana() < Weapon->WeaponManaCost)
        return Reject(ECharacterActionFailure::InsufficientMana);

    UCharacterActionExecution* Run = Weapon->bIsRangedWeapon
        ? static_cast<UCharacterActionExecution*>(NewObject<UCastActionExecution>(this))
        : static_cast<UCharacterActionExecution*>(NewObject<UMeleeActionExecution>(this));
    Run->Weapon = Weapon;
    Run->Definition = Weapon->ActionDefinition;
    Run->ManaCost = Weapon->WeaponManaCost;
    Run->Cooldown = FMath::Max(0.f, Weapon->WeaponAttackCooldown);
    Run->DamageOverride = Weapon->WeaponDamageOverride;
    Run->ProjectileClass = Weapon->WeaponProjectileClass.Get();
    Run->FireSocket = Weapon->WeaponFireSocketName;
    Run->State.Kind = Weapon->bIsRangedWeapon ? ECharacterActionKind::Cast : ECharacterActionKind::Melee;
    Run->Montage = Weapon->OverrideAttackMontage;
    if (!Run->Montage) Run->Montage = Character->AttackMontageMap.FindRef(Weapon->WeaponAnimType);
    if (!Weapon->bIsRangedWeapon && !Weapon->MeleeComboData.IsNull())
    {
        Run->Combo = Weapon->MeleeComboData.LoadSynchronous();
        if (!Run->Combo || !Run->Combo->ComboMontage || Run->Combo->Hits.IsEmpty()) return Reject(ECharacterActionFailure::MissingAnimation);
        Run->Montage = Run->Combo->ComboMontage;
    }
    if (Run->Definition && Run->Definition->Montage) Run->Montage = Run->Definition->Montage;
    if (!Run->Montage) return Reject(ECharacterActionFailure::MissingAnimation);
    return Start(Run);
}

FCharacterActionRequestResult UCharacterActionComponent::RequestUseItem(bool bQuickSlot, int32 SlotIndex)
{
    const auto Permission = CheckPermission();
    if (Permission != ECharacterActionFailure::None) return Reject(Permission);
    if (Active || !Character->InventoryComponent) return Reject(ECharacterActionFailure::Busy);
    auto* Run = NewObject<UUseItemActionExecution>(this);
    if (!Character->InventoryComponent->ReserveActionItem(bQuickSlot, SlotIndex, Run->Reservation))
        return Reject(ECharacterActionFailure::InvalidSource);
    Run->Item = Character->InventoryComponent->GetItemData(Run->Reservation.ItemID);
    if (!Run->Item || !Run->Item->bCanUse || Run->Item->ItemType == EItemType::Weapon)
        return Reject(ECharacterActionFailure::InvalidSource);
    Run->State.Kind = ECharacterActionKind::UseItem;
    if (auto* Consumable = Cast<UConsumableData>(Run->Item))
    {
        Run->Montage = Consumable->UseMontage;
        Run->Definition = Consumable->ActionDefinition;
    }
    if (Run->Definition && Run->Definition->Montage) Run->Montage = Run->Definition->Montage;
    return Start(Run);
}

FCharacterActionRequestResult UCharacterActionComponent::Start(UCharacterActionExecution* Run)
{
    // Publish and Montage_Play can execute external callbacks, including GC or
    // cancellation. Keep this execution alive even if a callback releases Active.
    TStrongObjectPtr<UCharacterActionExecution> KeepAlive(Run);
    Active = Run;
    Run->State.RunId = NextRunId++;
    Run->State.Phase = ECharacterActionPhase::Windup;
    Run->State.MoveScale = Run->Definition ? Run->Definition->MoveScale : 0.f;
    Run->State.bAllowJump = Run->Definition && Run->Definition->bAllowJump;
    Run->StartedAt = Run->LastProgressAt = GetWorld()->GetTimeSeconds();
    LastFailure = ECharacterActionFailure::None;
    const int64 RunId = Run->State.RunId;
    if (Run->Montage && !PlaySegment())
    {
        const auto Failure = LastFailure == ECharacterActionFailure::None ? ECharacterActionFailure::MissingAnimation : LastFailure;
        if (Active == Run) Finish(ECharacterActionEndReason::Failed, Failure);
        return Reject(Failure);
    }
    Publish();
    UE_LOG(LogCharacterActions, Log, TEXT("Run=%lld started kind=%d montage=%s"), RunId, static_cast<int32>(Run->State.Kind), *GetNameSafe(Run->Montage));
    // An explicit instant item has no animation to wait for.
    if (Active == Run && !Run->Montage)
    {
        bDispatching = true;
        Run->State.bCommitted = Run->ApplyEvent(*this, ECharacterActionEvent::ItemCommit);
        bDispatching = false;
        if (bDeferredFinish)
        {
            bDeferredFinish = false;
            Finish(DeferredReason);
        }
        else Finish(Run->State.bCommitted ? ECharacterActionEndReason::Completed : ECharacterActionEndReason::Failed,
            Run->State.bCommitted ? ECharacterActionFailure::None : ECharacterActionFailure::NoEffect);
    }
    FCharacterActionRequestResult Result;
    Result.Status = ECharacterActionRequestStatus::Started;
    Result.RunId = RunId;
    return Result;
}

bool UCharacterActionComponent::PlaySegment()
{
    if (!Active || !Character || !Character->GetMesh()) return false;
    auto* Anim = Character->GetMesh()->GetAnimInstance();
    if (!Anim) return false;
    TStrongObjectPtr<UCharacterActionExecution> KeepAlive(Active.Get());
    auto& Run = *KeepAlive.Get();
    Run.MontageInstanceId = INDEX_NONE; // Invalidate old callbacks BEFORE restarting the same asset.
    ++Run.State.SegmentGeneration;
    Run.bBlendOut = false;
    Run.State.bCommitted = false;
    Run.bNextHitQueued = false;
    Run.ProcessedEvents.Reset();
    Run.ExpectedEvents.Reset();
    Run.HitCount = 0;
    Run.BufferedUntil = -1;
    Run.State.Phase = ECharacterActionPhase::Windup;
    Run.SectionStart = 0.f;
    Run.SectionEnd = Run.Montage->GetPlayLength();
    Run.CancelStart = 0.f;
    Run.CancelEnd = -1.f;
    FName Section = NAME_None;
    if (Run.Combo)
    {
        if (!Run.Combo->Hits.IsValidIndex(Run.State.ComboIndex)) return false;
        const auto& Hit = Run.Combo->Hits[Run.State.ComboIndex];
        Section = Hit.SectionName;
        const int32 Index = Run.Montage->GetSectionIndex(Section);
        if (Index == INDEX_NONE) return false;
        Run.Montage->GetSectionStartAndEndTime(Index, Run.SectionStart, Run.SectionEnd);
        Run.ChainStart = FMath::Max(0.f, Hit.HitWindowStart);
        Run.ChainEnd = FMath::Max(Run.ChainStart, Hit.HitWindowEnd);
    }
    Run.FirstHitTime = Run.LastHitTime = 0.f;
    bool bHasRequiredEvent = false;
    for (const auto& Event : Run.Montage->Notifies)
    {
        if (Event.GetTime() >= Run.SectionStart && Event.GetTime() < Run.SectionEnd)
        {
            if (const auto* Window = Cast<UAnimNotifyState_ActionWindow>(Event.NotifyStateClass))
            {
                const float Start = Event.GetTime() - Run.SectionStart;
                const float End = FMath::Min(Event.GetEndTriggerTime(), Run.SectionEnd) - Run.SectionStart;
                if (Window->Window == ECharacterActionWindow::Chain)
                { Run.ChainStart = Start; Run.ChainEnd = End; }
                else { Run.CancelStart = Start; Run.CancelEnd = End; }
            }
        }
        if (Event.GetTime() < Run.SectionStart || Event.GetTime() >= Run.SectionEnd || !Event.Notify) continue;
        const bool bExpected = (Run.State.Kind == ECharacterActionKind::Melee && Event.Notify->IsA<UAnimNotify_MeleeHit>()) ||
            (Run.State.Kind == ECharacterActionKind::Cast && Event.Notify->IsA<UAnimNotify_Fireball>()) ||
            (Run.State.Kind == ECharacterActionKind::UseItem && Event.Notify->IsA<UAnimNotify_UseItemComplete>());
        if (bExpected)
        {
            Run.ExpectedEvents.Add(static_cast<int32>(&Event - Run.Montage->Notifies.GetData()));
            const float Relative = Event.GetTime() - Run.SectionStart;
            if (!bHasRequiredEvent) Run.FirstHitTime = Relative;
            else Run.FirstHitTime = FMath::Min(Run.FirstHitTime, Relative);
            Run.LastHitTime = FMath::Max(Run.LastHitTime, Relative);
            bHasRequiredEvent = true;
        }
    }
    if (!bHasRequiredEvent) { LastFailure = ECharacterActionFailure::MissingEvent; return false; }
    if ((Run.State.Kind != ECharacterActionKind::Melee && Run.ExpectedEvents.Num() != 1) ||
        (Run.Combo && !Run.Combo->Hits[Run.State.ComboIndex].SubHits.IsEmpty() &&
        Run.ExpectedEvents.Num() != Run.Combo->Hits[Run.State.ComboIndex].SubHits.Num()))
    { LastFailure = ECharacterActionFailure::MissingEvent; return false; }
    const float Rate = Run.Definition ? FMath::Max(0.01f, Run.Definition->PlayRate) : 1.f;
    if (Anim->Montage_Play(Run.Montage, Rate, EMontagePlayReturnType::MontageLength, Run.SectionStart, true) <= 0.f) return false;
    // OnMontageStarted and interrupted-montage callbacks are synchronous. Never
    // attach this old execution's delegates to a replacement started by one.
    if (Active != &Run || Run.bTerminal || bOwnerEnding || !IsValid(Character)) return false;
    auto* Instance = Anim->GetActiveInstanceForMontage(Run.Montage);
    if (!Instance) return false;
    Run.MontageInstanceId = Instance->GetInstanceID();
    if (Section != NAME_None) Anim->Montage_SetNextSection(Section, NAME_None, Run.Montage);
    const int64 Id = Run.State.RunId;
    const int32 Generation = Run.State.SegmentGeneration;
    FOnMontageBlendingOutStarted Blend;
    Blend.BindWeakLambda(this, [this, Id, Generation](UAnimMontage* M, bool Interrupted) { OnMontageBlendOut(Id, Generation, M, Interrupted); });
    Anim->Montage_SetBlendingOutDelegate(Blend, Run.Montage);
    FOnMontageEnded End;
    End.BindWeakLambda(this, [this, Id, Generation](UAnimMontage* M, bool Interrupted) { OnMontageEnded(Id, Generation, M, Interrupted); });
    Anim->Montage_SetEndDelegate(End, Run.Montage);
    Run.LastPosition = -1.f;
    Run.LastProgressAt = GetWorld()->GetTimeSeconds();
    return true;
}

bool UCharacterActionComponent::HandleNotify(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation,
    const FAnimNotifyEventReference& Reference, ECharacterActionEvent Event)
{
    if (!Active || Active->bTerminal || bFinishing || bDispatching || Active->bBlendOut ||
        !Character || Mesh != Character->GetMesh() || CheckPermission() != ECharacterActionFailure::None) return false;
    const auto* Context = Reference.GetContextData<UE::Anim::FAnimNotifyMontageInstanceContext>();
    const auto* Notify = Reference.GetNotify();
    if (!Context || !Notify || Context->MontageInstanceID != Active->MontageInstanceId || Animation != Active->Montage) return false;
    if (Notify->GetTime() < Active->SectionStart || Notify->GetTime() >= Active->SectionEnd) return false;
    const int32 Index = Active->Montage->Notifies.IndexOfByPredicate([Notify](const FAnimNotifyEvent& N) { return &N == Notify; });
    if (Index == INDEX_NONE || Active->ProcessedEvents.Contains(Index)) return false;
    if (!Active->ExpectedEvents.Contains(Index)) return false;
    if ((Event == ECharacterActionEvent::MeleeHit) != (Active->State.Kind == ECharacterActionKind::Melee)) return false;
    if (Event == ECharacterActionEvent::CastCommit && Active->State.Kind != ECharacterActionKind::Cast) return false;
    if (Event == ECharacterActionEvent::ItemCommit && Active->State.Kind != ECharacterActionKind::UseItem) return false;
    if (Active->State.Kind != ECharacterActionKind::Melee && Active->State.bCommitted) return false;
    TStrongObjectPtr<UCharacterActionExecution> KeepAlive(Active.Get());
    auto* Run = KeepAlive.Get();
    Run->ProcessedEvents.Add(Index); // Register before effects can broadcast/re-enter.
    Run->State.Phase = ECharacterActionPhase::Active;
    bDispatching = true;
    const bool bApplied = Run->ApplyEvent(*this, Event);
    bDispatching = false;
    Run->State.bCommitted |= bApplied;
    UE_LOG(LogCharacterActions, Log, TEXT("Run=%lld segment=%d event=%d applied=%d instance=%d"),
        Run->State.RunId, Run->State.SegmentGeneration, Index, bApplied, Run->MontageInstanceId);
    if (bApplied && Run->Weapon)
        CooldownUntil.FindOrAdd(Run->Weapon->ItemID) = GetWorld()->GetTimeSeconds() + Run->Cooldown;
    if (bDeferredFinish)
    {
        bDeferredFinish = false;
        Finish(DeferredReason);
    }
    else if (!bApplied)
        Finish(ECharacterActionEndReason::Failed, LastFailure == ECharacterActionFailure::None ? ECharacterActionFailure::NoEffect : LastFailure);
    else Publish();
    return bApplied;
}

void UCharacterActionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    if (!Active) return;
    if (!Character || !Character->AttributeComp || !Character->AttributeComp->IsAlive()) { Finish(ECharacterActionEndReason::Dead); return; }
    auto* Anim = Character->GetMesh()->GetAnimInstance();
    if (!Anim) { Finish(ECharacterActionEndReason::Failed, ECharacterActionFailure::MissingAnimation); return; }
    const double Now = GetWorld()->GetTimeSeconds();
    const float Position = Anim->Montage_GetPosition(Active->Montage);
    const float PreviousPosition = Active->LastPosition;
    if (!FMath::IsNearlyEqual(Position, Active->LastPosition)) { Active->LastPosition = Position; Active->LastProgressAt = Now; }
    const float MaxTime = Active->Definition ? Active->Definition->MaximumActiveSeconds : 30.f;
    if (Now - Active->StartedAt > MaxTime || (!Active->bBlendOut && Now - Active->LastProgressAt > 5.f && Anim->Montage_IsPlaying(Active->Montage)))
    { Finish(ECharacterActionEndReason::Failed, ECharacterActionFailure::MissingEvent); return; }
    const float Relative = Position - Active->SectionStart;
    if (Active->State.bCommitted && Relative > Active->LastHitTime && Active->State.Phase != ECharacterActionPhase::Recovery)
    { Active->State.Phase = ECharacterActionPhase::Recovery; Publish(); }
    if (Active && Active->Combo && !Active->bBlendOut)
    {
        // A frame may cross the complete authored window; still consume a live
        // buffer if the animation traversed it, rather than requiring a sample inside.
        const float PreviousRelative = PreviousPosition < 0.f ? 0.f : PreviousPosition - Active->SectionStart;
        if (Active->BufferedUntil >= Now && Relative >= Active->ChainStart && PreviousRelative <= Active->ChainEnd)
        { Active->bNextHitQueued = true; Active->BufferedUntil = -1; }
        const float Transition = FMath::Max(Active->ChainEnd, Active->LastHitTime + 0.001f);
        if (Active->bNextHitQueued && Relative >= Transition)
        {
            if (Active->ProcessedEvents.Num() != Active->ExpectedEvents.Num() || !Active->State.bCommitted)
            { Finish(ECharacterActionEndReason::Failed, ECharacterActionFailure::MissingEvent); return; }
            const int32 Next = Active->State.ComboIndex + 1;
            if (Next < Active->Combo->Hits.Num() || Active->Combo->bLoopFromLastHit)
            {
                Active->State.ComboIndex = Next % Active->Combo->Hits.Num();
                TStrongObjectPtr<UCharacterActionExecution> AdvancingRun(Active.Get());
                if (!PlaySegment())
                {
                    if (Active == AdvancingRun.Get()) Finish(ECharacterActionEndReason::Failed, ECharacterActionFailure::MissingAnimation);
                }
                else { Character->BP_OnComboAdvanced(Active->State.ComboIndex); Publish(); }
            }
            else { Active->bNextHitQueued = false; Active->BufferedUntil = -1; }
        }
    }
}

void UCharacterActionComponent::OnMontageBlendOut(int64 Id, int32 Generation, UAnimMontage* Montage, bool bInterrupted)
{
    if (!Active || Active->State.RunId != Id || Active->State.SegmentGeneration != Generation ||
        Active->MontageInstanceId == INDEX_NONE || Active->Montage != Montage) return;
    Active->bBlendOut = true;
    Active->BufferedUntil = -1;
    Active->bNextHitQueued = false;
    if (bInterrupted) Finish(ECharacterActionEndReason::Interrupted);
}

void UCharacterActionComponent::OnMontageEnded(int64 Id, int32 Generation, UAnimMontage* Montage, bool bInterrupted)
{
    if (!Active || Active->State.RunId != Id || Active->State.SegmentGeneration != Generation ||
        Active->MontageInstanceId == INDEX_NONE || Active->Montage != Montage) return;
    if (bInterrupted) Finish(ECharacterActionEndReason::Interrupted);
    else
    {
        const bool bComplete = Active->State.bCommitted && Active->ProcessedEvents.Num() == Active->ExpectedEvents.Num();
        Finish(bComplete ? ECharacterActionEndReason::Completed : ECharacterActionEndReason::Failed,
            bComplete ? ECharacterActionFailure::None : ECharacterActionFailure::MissingEvent);
    }
}

void UCharacterActionComponent::Publish()
{
    if (!Character) return;
    Character->SetAttacking(Active && Active->State.Kind != ECharacterActionKind::UseItem);
    Character->bIsUsingItem = Active && Active->State.Kind == ECharacterActionKind::UseItem;
    if (!bOwnerEnding) OnActionChanged.Broadcast(GetSnapshot());
}

void UCharacterActionComponent::Interrupt(ECharacterActionEndReason Reason)
{
    if (Reason == ECharacterActionEndReason::OwnerEnded) bOwnerEnding = true;
    Finish(Reason);
}
bool UCharacterActionComponent::TryCancelAction(int64 RunId)
{
    if (!Active || Active->State.RunId != RunId || bDispatching || bFinishing || Active->bBlendOut ||
        !Character || !Character->GetMesh()) return false;
    const auto* Anim = Character->GetMesh()->GetAnimInstance();
    if (!Anim) return false;
    const float Position = Anim->Montage_GetPosition(Active->Montage) - Active->SectionStart;
    if (Position < Active->CancelStart || Position > Active->CancelEnd) return false;
    Finish(ECharacterActionEndReason::Cancelled);
    return true;
}
void UCharacterActionComponent::OnOwnerDeath() { Finish(ECharacterActionEndReason::Dead); }

void UCharacterActionComponent::Finish(ECharacterActionEndReason Reason, ECharacterActionFailure Failure)
{
    if (bDispatching) { bDeferredFinish = true; DeferredReason = Reason; return; }
    if (!Active || bFinishing) return;
    bFinishing = true;
    TStrongObjectPtr<UCharacterActionExecution> KeepAlive(Active.Get());
    auto* Run = KeepAlive.Get();
    Run->bTerminal = true;
    Run->MontageInstanceId = INDEX_NONE;
    const int64 Id = Run->State.RunId;
    const bool bMelee = Run->State.Kind == ECharacterActionKind::Melee;
    Active = nullptr; // Invalidate identity before Montage_Stop can synchronously call back.
    LastFailure = Failure;
    if (Character && Character->GetMesh())
        if (auto* Anim = Character->GetMesh()->GetAnimInstance())
            if (Run->Montage) Anim->Montage_Stop(0.1f, Run->Montage);
    Publish();
    if (Character && !bOwnerEnding)
    {
        if (bMelee) Character->BP_OnComboReset(Reason != ECharacterActionEndReason::Completed);
        OnActionEnded.Broadcast(Id, Reason, Failure);
    }
    bFinishing = false;
    if (Character && !bOwnerEnding) Character->RefreshHeldItemDisplay();
    UE_LOG(LogCharacterActions, Log, TEXT("Run=%lld ended: reason=%d failure=%d"), Id, static_cast<int32>(Reason), static_cast<int32>(Failure));
}
