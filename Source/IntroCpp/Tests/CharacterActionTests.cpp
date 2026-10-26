#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Actions/CharacterActionComponent.h"
#include "Actions/CharacterActionExecution.h"
#include "AnimNotify_MeleeHit.h"
#include "Animation/ActiveMontageInstanceScope.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimNotifyQueue.h"
#include "Animation/Skeleton.h"
#include "ComboAttackData.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "MyPlayerCharacter.h"
#include "UObject/UnrealType.h"

// Test-only access avoids exposing lifecycle/identity mutation to gameplay or Blueprints.
struct FCharacterActionTestAccess
{
    static void Initialize(UCharacterActionComponent& Component, AMyPlayerCharacter* Character)
    {
        Component.Character = Character;
        Character->AttributeComp->OnCharacterDeath.AddUniqueDynamic(&Component, &UCharacterActionComponent::OnOwnerDeath);
    }
    static void Activate(UCharacterActionComponent& Component, UCharacterActionExecution* Run)
    {
        Component.Active = Run;
    }
    static void End(UCharacterActionComponent& Component, int64 Id, int32 Generation, UAnimMontage* Montage)
    {
        Component.OnMontageEnded(Id, Generation, Montage, false);
    }
    static void BeginDispatch(UCharacterActionComponent& Component) { Component.bDispatching = true; }
    static void Tick(UCharacterActionComponent& Component, float DeltaSeconds)
    {
        Component.TickComponent(DeltaSeconds, LEVELTICK_All, nullptr);
    }
    static bool IsDeferred(const UCharacterActionComponent& Component) { return Component.bDeferredFinish; }
    static void CompleteDispatch(UCharacterActionComponent& Component)
    {
        Component.bDispatching = false;
        if (Component.bDeferredFinish)
        {
            Component.bDeferredFinish = false;
            Component.Finish(Component.DeferredReason);
        }
    }
};

namespace CharacterActionTests
{
    struct FFixture
    {
        UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
        AMyPlayerCharacter* Character = nullptr;

        FFixture()
        {
            // No BeginPlay: these tests deliberately have no UI, controller, asset or map dependency.
            if (World) Character = World->SpawnActor<AMyPlayerCharacter>();
            if (Character) FCharacterActionTestAccess::Initialize(*Character->Actions, Character);
        }
        ~FFixture()
        {
            if (Character && Character->Actions)
                Character->Actions->Interrupt(ECharacterActionEndReason::OwnerEnded);
            if (World) World->DestroyWorld(false);
        }
        UCharacterActionComponent& Actions() const { return *Character->Actions; }
        UMeleeActionExecution* Activate(int64 Id = 17, int32 InstanceId = 42)
        {
            auto* Run = NewObject<UMeleeActionExecution>(Character->Actions);
            Run->Montage = NewObject<UAnimMontage>(Run);
            Run->State.RunId = Id;
            Run->State.Kind = ECharacterActionKind::Melee;
            Run->State.Phase = ECharacterActionPhase::Windup;
            Run->State.SegmentGeneration = 1;
            Run->MontageInstanceId = InstanceId;
            Run->SectionStart = 0.f;
            Run->SectionEnd = 1.f;
            Run->ManaCost = 5.f;
            Run->Montage->Notifies.SetNum(2);
            for (int32 Index = 0; Index < 2; ++Index)
            {
                auto& Notify = Run->Montage->Notifies[Index];
                Notify.Notify = NewObject<UAnimNotify_MeleeHit>(Run->Montage);
                Notify.SetTime(0.1f * (Index + 1));
                Run->ExpectedEvents.Add(Index);
            }
            FCharacterActionTestAccess::Activate(Actions(), Run);
            return Run;
        }
    };

    FAnimNotifyEventReference Reference(UCharacterActionExecution& Run, int32 EventIndex, int32 InstanceId)
    {
        FAnimNotifyEventReference Result(&Run.Montage->Notifies[EventIndex], Run.Montage);
        Result.AddContextData<UE::Anim::FAnimNotifyMontageInstanceContext>(InstanceId);
        return Result;
    }

    UAnimInstance* CreatePlayback(FFixture& Fixture, UCharacterActionExecution& Run)
    {
        auto* Mesh = Fixture.Character->GetMesh();
        auto* Anim = NewObject<UAnimInstance>(Mesh);
        Mesh->AnimScriptInstance = Anim;
        Anim->CurrentSkeleton = NewObject<USkeleton>(Anim);
        Run.Montage->SetSkeleton(Anim->CurrentSkeleton);
        // The transient montage has no sequence data model. Set only its
        // reflected length so the real native montage instance can be played.
        auto* Length = FindFProperty<FFloatProperty>(UAnimSequenceBase::StaticClass(), TEXT("SequenceLength"));
        if (!Length) return nullptr;
        Length->SetPropertyValue_InContainer(Run.Montage, 1.f);
        if (Anim->Montage_Play(Run.Montage, 1.f, EMontagePlayReturnType::MontageLength, 0.f, false) <= 0.f)
            return nullptr;
        return Anim;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCharacterActionPermissionsTest, "IntroCpp.Actions.Permissions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCharacterActionPermissionsTest::RunTest(const FString& Parameters)
{
    CharacterActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native character created"), Fixture.Character)) return false;
    auto& Actions = Fixture.Actions();
    Actions.SetUIBlocked(true);
    TestEqual(TEXT("Attack observes UI gate"), Actions.RequestAttack().Failure, ECharacterActionFailure::UIBlocked);
    TestEqual(TEXT("Direct item API observes same UI gate"), Actions.RequestUseItem(true, 0).Failure, ECharacterActionFailure::UIBlocked);
    TestFalse(TEXT("UI gate prevents jumping"), Actions.GetSnapshot().bAllowJump);
    TestEqual(TEXT("UI gate prevents movement"), Actions.GetSnapshot().MoveScale, 0.f);
    Actions.SetUIBlocked(false);
    TestEqual(TEXT("Unarmed attack rejected before starting"), Actions.RequestAttack().Failure, ECharacterActionFailure::InvalidSource);
    TestEqual(TEXT("Empty original source rejected"), Actions.RequestUseItem(true, 0).Failure, ECharacterActionFailure::InvalidSource);
    Fixture.Character->AttributeComp->SetHealth(0.f);
    TestEqual(TEXT("Dead attack rejected"), Actions.RequestAttack().Failure, ECharacterActionFailure::Dead);
    TestEqual(TEXT("Dead item API rejected"), Actions.RequestUseItem(false, 0).Failure, ECharacterActionFailure::Dead);
    TestFalse(TEXT("Dead equipment change rejected"), Actions.CanChangeEquipment());
    TestFalse(TEXT("Rejected requests do not acquire foreground"), Actions.IsBusy());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCharacterActionNotifyIdentityTest, "IntroCpp.Actions.NotifyIdentityAndExactlyOnce",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCharacterActionNotifyIdentityTest::RunTest(const FString& Parameters)
{
    CharacterActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native character created"), Fixture.Character)) return false;
    auto& Actions = Fixture.Actions();
    auto* Run = Fixture.Activate();
    auto* Mesh = Fixture.Character->GetMesh();
    const auto First = CharacterActionTests::Reference(*Run, 0, 42);
    const FAnimNotifyEventReference NoIdentity(&Run->Montage->Notifies[0], Run->Montage);
    const auto WrongIdentity = CharacterActionTests::Reference(*Run, 0, 41);
    TestFalse(TEXT("Missing montage identity rejected"), Actions.HandleNotify(Mesh, Run->Montage, NoIdentity, ECharacterActionEvent::MeleeHit));
    TestFalse(TEXT("Old montage instance rejected"), Actions.HandleNotify(Mesh, Run->Montage, WrongIdentity, ECharacterActionEvent::MeleeHit));
    TestFalse(TEXT("Wrong mesh rejected"), Actions.HandleNotify(nullptr, Run->Montage, First, ECharacterActionEvent::MeleeHit));
    TestFalse(TEXT("Wrong source animation rejected"), Actions.HandleNotify(Mesh, nullptr, First, ECharacterActionEvent::MeleeHit));
    TestFalse(TEXT("Wrong effect kind rejected"), Actions.HandleNotify(Mesh, Run->Montage, First, ECharacterActionEvent::CastCommit));
    TestEqual(TEXT("Rejected events never pay mana"), Fixture.Character->AttributeComp->GetCurrentMana(), 50.f);
    TestTrue(TEXT("Matching event commits a real melee swing"), Actions.HandleNotify(Mesh, Run->Montage, First, ECharacterActionEvent::MeleeHit));
    TestEqual(TEXT("First swing pays resource once"), Fixture.Character->AttributeComp->GetCurrentMana(), 45.f);
    TestFalse(TEXT("Replayed same event rejected"), Actions.HandleNotify(Mesh, Run->Montage, First, ECharacterActionEvent::MeleeHit));
    const auto Second = CharacterActionTests::Reference(*Run, 1, 42);
    TestTrue(TEXT("Distinct second hit in same section remains valid"), Actions.HandleNotify(Mesh, Run->Montage, Second, ECharacterActionEvent::MeleeHit));
    TestEqual(TEXT("Second hit does not pay execution mana twice"), Fixture.Character->AttributeComp->GetCurrentMana(), 45.f);
    TestEqual(TEXT("Both distinct events recorded"), Run->ProcessedEvents.Num(), 2);

    Run->State.SegmentGeneration = 2;
    Run->MontageInstanceId = 43;
    Run->ProcessedEvents.Reset();
    TestFalse(TEXT("Old same-asset event rejected after next segment"), Actions.HandleNotify(Mesh, Run->Montage, First, ECharacterActionEvent::MeleeHit));
    FCharacterActionTestAccess::End(Actions, 17, 1, Run->Montage);
    TestTrue(TEXT("Old segment end cannot release current segment"), Actions.IsBusy());
    const auto CurrentSegment = CharacterActionTests::Reference(*Run, 0, 43);
    TestTrue(TEXT("New segment has independent event ledger"), Actions.HandleNotify(Mesh, Run->Montage, CurrentSegment, ECharacterActionEvent::MeleeHit));
    const auto CurrentSecond = CharacterActionTests::Reference(*Run, 1, 43);
    TestTrue(TEXT("Second expected event in new segment commits"), Actions.HandleNotify(Mesh, Run->Montage, CurrentSecond, ECharacterActionEvent::MeleeHit));
    FCharacterActionTestAccess::End(Actions, 17, 2, Run->Montage);
    TestFalse(TEXT("Current completed end releases foreground"), Actions.IsBusy());
    TestTrue(TEXT("Completed run marked terminal"), Run->bTerminal);
    TestFalse(TEXT("Late completed event rejected"), Actions.HandleNotify(Mesh, Run->Montage, CurrentSegment, ECharacterActionEvent::MeleeHit));

    auto* NewRun = Fixture.Activate(18, 44);
    FCharacterActionTestAccess::End(Actions, 17, 2, NewRun->Montage);
    TestTrue(TEXT("Old run end cannot release a newer action"), Actions.IsBusy());
    TestEqual(TEXT("New action identity preserved"), Actions.GetSnapshot().RunId, int64(18));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCharacterActionMissingCommitTest, "IntroCpp.Actions.MissingCommitAndTermination",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCharacterActionMissingCommitTest::RunTest(const FString& Parameters)
{
    CharacterActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native character created"), Fixture.Character)) return false;
    auto& Actions = Fixture.Actions();
    auto* Run = Fixture.Activate();
    FCharacterActionTestAccess::End(Actions, 17, 1, Run->Montage);
    TestFalse(TEXT("Ending without a commit releases foreground"), Actions.IsBusy());
    TestEqual(TEXT("Missing commit reports failure"), Actions.GetLastFailure(), ECharacterActionFailure::MissingEvent);
    TestEqual(TEXT("Missing commit spends no mana"), Fixture.Character->AttributeComp->GetCurrentMana(), 50.f);
    Actions.Interrupt();
    TestEqual(TEXT("Repeated termination preserves previous result"), Actions.GetLastFailure(), ECharacterActionFailure::MissingEvent);
    Fixture.Activate(18, 43);
    Actions.Interrupt(ECharacterActionEndReason::OwnerEnded);
    TestFalse(TEXT("Owner ending releases foreground"), Actions.IsBusy());
    TestEqual(TEXT("Owner-ended component cannot start another action"), Actions.RequestAttack().Failure, ECharacterActionFailure::Dead);
    TestFalse(TEXT("Owner-ended component cannot equip"), Actions.CanChangeEquipment());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCharacterActionDeferredDeathTest, "IntroCpp.Actions.DeferredDeathDuringDispatch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCharacterActionDeferredDeathTest::RunTest(const FString& Parameters)
{
    CharacterActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native character created"), Fixture.Character)) return false;
    auto& Actions = Fixture.Actions();
    auto* Run = Fixture.Activate();
    FCharacterActionTestAccess::BeginDispatch(Actions);
    Fixture.Character->AttributeComp->SetHealth(0.f); // Real dynamic death delegate, during a controlled dispatch scope.
    TestTrue(TEXT("Death defers cleanup until effect dispatch completes"), FCharacterActionTestAccess::IsDeferred(Actions));
    TestTrue(TEXT("Execution stays held while callback stack is active"), Actions.IsBusy());
    TestEqual(TEXT("Reentrant dead request is rejected"), Actions.RequestUseItem(true, 0).Failure, ECharacterActionFailure::Dead);
    FCharacterActionTestAccess::CompleteDispatch(Actions);
    TestFalse(TEXT("Deferred death releases foreground after dispatch"), Actions.IsBusy());
    TestTrue(TEXT("Deferred death marks execution terminal"), Run->bTerminal);
    TestEqual(TEXT("Deferred death invalidates montage identity"), Run->MontageInstanceId, INDEX_NONE);
    TestFalse(TEXT("Death locks jumping after foreground released"), Actions.GetSnapshot().bAllowJump);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCharacterActionLowFrameBufferTest, "IntroCpp.Actions.ChainWindowSurvivesLowFrameRate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCharacterActionLowFrameBufferTest::RunTest(const FString& Parameters)
{
    CharacterActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native character created"), Fixture.Character)) return false;
    auto& Actions = Fixture.Actions();
    auto* Run = Fixture.Activate();
    auto* Anim = CharacterActionTests::CreatePlayback(Fixture, *Run);
    if (!TestNotNull(TEXT("Real native montage playback created"), Anim)) return false;
    Run->MontageInstanceId = Anim->GetActiveInstanceForMontage(Run->Montage)->GetInstanceID();
    Run->Combo = NewObject<UComboAttackData>(Run);
    Run->Combo->Hits.SetNum(1); // Non-looping last segment must never start a fresh first attack.
    Run->ChainStart = 0.3f;
    Run->ChainEnd = 0.5f;
    Run->LastHitTime = 0.9f;
    for (int32 Index = 0; Index < 2; ++Index)
    {
        const auto Event = CharacterActionTests::Reference(*Run, Index, Run->MontageInstanceId);
        if (!TestTrue(TEXT("Expected hit committed before transition test"),
            Actions.HandleNotify(Fixture.Character->GetMesh(), Run->Montage, Event, ECharacterActionEvent::MeleeHit))) return false;
    }

    Fixture.World->TimeSeconds = 0.;
    Anim->Montage_SetPosition(Run->Montage, 0.1f);
    Run->LastPosition = 0.1f;
    TestEqual(TEXT("Early input accepted as short-lived buffer"), Actions.RequestAttack().Status, ECharacterActionRequestStatus::Buffered);
    TestFalse(TEXT("Early input is not yet a queued chain"), Run->bNextHitQueued);
    TestTrue(TEXT("Early buffer has finite expiry"), Run->BufferedUntil > 0. && Run->BufferedUntil < 0.2);
    Fixture.World->TimeSeconds = 1. / 3.;
    Anim->Montage_SetPosition(Run->Montage, 0.4f);
    FCharacterActionTestAccess::Tick(Actions, 1.f / 3.f);
    TestFalse(TEXT("Expired early input does not auto chain"), Run->bNextHitQueued);

    TestEqual(TEXT("Input inside window still reports Buffered"), Actions.RequestAttack().Status, ECharacterActionRequestStatus::Buffered);
    TestTrue(TEXT("Input inside window is queued immediately"), Run->bNextHitQueued);
    TestEqual(TEXT("Accepted chain is not governed by pre-window TTL"), Run->BufferedUntil, -1.);
    TestEqual(TEXT("Repeated press remains a single accepted request"), Actions.RequestAttack().Status, ECharacterActionRequestStatus::Buffered);
    TestEqual(TEXT("Press does not immediately advance the section"), Run->State.SegmentGeneration, 1);
    Fixture.World->TimeSeconds = 2. / 3.;
    Anim->Montage_SetPosition(Run->Montage, 0.6f);
    FCharacterActionTestAccess::Tick(Actions, 1.f / 3.f);
    TestTrue(TEXT("Accepted chain survives a 333 ms frame, beyond 150 ms TTL"), Run->bNextHitQueued);
    TestEqual(TEXT("Late repeated request is rejected after window"), Actions.RequestAttack().Failure, ECharacterActionFailure::Busy);
    TestTrue(TEXT("Late rejected press cannot erase the accepted chain"), Run->bNextHitQueued);
    Anim->Montage_SetPosition(Run->Montage, 0.95f);
    FCharacterActionTestAccess::Tick(Actions, 1.f / 3.f);
    TestFalse(TEXT("Last non-looping segment consumes queued intent"), Run->bNextHitQueued);
    TestEqual(TEXT("Last segment never restarts the first segment"), Run->State.SegmentGeneration, 1);
    TestTrue(TEXT("Last segment remains held until its end callback"), Actions.IsBusy());
    FCharacterActionTestAccess::End(Actions, Run->State.RunId, Run->State.SegmentGeneration, Run->Montage);
    TestFalse(TEXT("Natural end releases the final segment"), Actions.IsBusy());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCharacterActionChainWindowBoundaryTest, "IntroCpp.Actions.ChainWindowBoundaries",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCharacterActionChainWindowBoundaryTest::RunTest(const FString& Parameters)
{
    CharacterActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native character created"), Fixture.Character)) return false;
    auto& Actions = Fixture.Actions();
    auto* Run = Fixture.Activate();
    auto* Anim = CharacterActionTests::CreatePlayback(Fixture, *Run);
    if (!TestNotNull(TEXT("Real native montage playback created"), Anim)) return false;
    Run->Combo = NewObject<UComboAttackData>(Run);
    Run->Combo->Hits.SetNum(2);
    Run->ChainStart = 0.3f;
    Run->ChainEnd = 0.5f;
    for (float Boundary : { Run->ChainStart, Run->ChainEnd })
    {
        Run->bNextHitQueued = false;
        Run->BufferedUntil = -1.;
        Anim->Montage_SetPosition(Run->Montage, Boundary);
        TestEqual(TEXT("Exact window boundary is accepted"), Actions.RequestAttack().Status, ECharacterActionRequestStatus::Buffered);
        TestTrue(TEXT("Exact boundary immediately queues the single next hit"), Run->bNextHitQueued);
        TestEqual(TEXT("Queued boundary has no early-input expiry"), Run->BufferedUntil, -1.);
    }
    Run->bNextHitQueued = false;
    Anim->Montage_SetPosition(Run->Montage, Run->ChainEnd + 0.001f);
    TestEqual(TEXT("Beyond window is rejected"), Actions.RequestAttack().Failure, ECharacterActionFailure::Busy);
    TestFalse(TEXT("Beyond window never creates queued input"), Run->bNextHitQueued);
    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
