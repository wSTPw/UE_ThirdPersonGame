#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "MHWI/Monsters/MHWIRathianThkExecutor.h"
#include "MHWI/Monsters/MHWIRathianSourceMovementComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"

namespace RathianEngineeringTests
{
FMHWIRathianThkProgram FixtureProgram()
{
    // An explicit engineering fixture. It does not assert native predicate semantics.
    FMHWIRathianThkProgram P;
    P.SourceSha256 = FString::ChrN(64, TEXT('a'));
    P.SourcePath = TEXT("engineering-only/conditional-call-fixture");
    P.Entry = TEXT("entry");
    const auto Add = [&P](const TCHAR* Key, EMHWIRathianThkOp Op,
        const TCHAR* Next = TEXT(""), const TCHAR* Otherwise = TEXT(""), int32 Action = INDEX_NONE)
    {
        FMHWIRathianThkInstruction I;
        I.Key = Key; I.Op = Op; I.Next = Next; I.Otherwise = Otherwise; I.NativeActionId = Action;
        I.SourceEvidence = TEXT("Engineering test fixture; not native-consumer proof.");
        P.Instructions.Add(Key, I);
    };
    Add(TEXT("entry"), EMHWIRathianThkOp::Call, TEXT("fatigue"));
    P.Instructions[TEXT("entry")].CallTarget = TEXT("guard");
    Add(TEXT("guard"), EMHWIRathianThkOp::Branch, TEXT("unknown"), TEXT("return"));
    P.Instructions[TEXT("guard")].FunctionType = 0x70;
    Add(TEXT("unknown"), EMHWIRathianThkOp::Branch, TEXT("return"), TEXT("return"));
    P.Instructions[TEXT("unknown")].FunctionType = 0xaf;
    P.Instructions[TEXT("unknown")].Parameter1 = 5000;
    Add(TEXT("return"), EMHWIRathianThkOp::Return);
    Add(TEXT("fatigue"), EMHWIRathianThkOp::Branch, TEXT("tired"), TEXT("normal"));
    P.Instructions[TEXT("fatigue")].FunctionType = 0x1f;
    Add(TEXT("tired"), EMHWIRathianThkOp::YieldAction, TEXT("end"), TEXT(""), 87);
    Add(TEXT("normal"), EMHWIRathianThkOp::YieldAction, TEXT("end"), TEXT(""), 86);
    Add(TEXT("end"), EMHWIRathianThkOp::Stop);
    return P;
}

FMHWIRathianThkQueryResult Reply(bool Value)
{
    FMHWIRathianThkQueryResult R;
    R.bAvailable = true; R.Value = Value;
    R.Evidence = TEXT("Engineering condition injection only.");
    return R;
}

struct FWorldFixture
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    APawn* Pawn = nullptr;
    UMHWIRathianSourceMovementComponent* Movement = nullptr;

    FWorldFixture()
    {
        if (!World) return;
        Pawn = World->SpawnActor<APawn>();
        if (!Pawn) return;
        auto* Root = NewObject<USceneComponent>(Pawn, TEXT("EngineeringRoot"));
        Pawn->SetRootComponent(Root);
        Root->RegisterComponent();
        Movement = NewObject<UMHWIRathianSourceMovementComponent>(Pawn);
        Movement->RegisterComponent();
        Movement->SetUpdatedComponent(Root);
    }
    ~FWorldFixture() { if (World) World->DestroyWorld(false); }
};

FMHWIRathianQualifiedSourceMotion FixtureMotion()
{
    FMHWIRathianQualifiedSourceMotion M;
    M.SourceSha256 = FString::ChrN(64, TEXT('b'));
    M.MotionBank = TEXT("engineering-fixture");
    M.MotionSlot = 0;
    M.EvidencePath = TEXT("Engineering movement test; not original trajectory.");
    M.TimeBasis = TEXT("Explicit fixture units with no wall-clock conversion.");
    M.CoordinateBasis = TEXT("UE centimeters, local XY, identity scale.");
    M.TimeUnit = EMHWIRathianSourceTimeUnit::NativeTicks;
    M.UnitsPerSecond = 0.0;
    M.MotionBindingQualification = EMHWIRathianMotionQualification::EngineeringAdapter;
    M.TimeBasisQualification = EMHWIRathianMotionQualification::EngineeringAdapter;
    M.CoordinateBasisQualification = EMHWIRathianMotionQualification::EngineeringAdapter;
    M.RootTrackQualification = EMHWIRathianMotionQualification::EngineeringAdapter;
    for (int32 I = 0; I < 3; ++I)
    {
        FMHWIRathianSourceMotionSample S;
        S.SourceTime = I;
        S.LocalRootTransform = FTransform(FQuat::Identity,
            I == 0 ? FVector::ZeroVector : (I == 1 ? FVector(100, 0, 0) : FVector(100, 100, 0)));
        M.Samples.Add(S);
    }
    return M;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRathianThkUnknownRefusal,
    "IntroCpp.MHWI.Rathian.Engineering.ThkUnknownRefusal",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRathianThkUnknownRefusal::RunTest(const FString&)
{
    using namespace RathianEngineeringTests;
    const auto Program = FixtureProgram();
    FMHWIRathianThkExecutor E;
    FString Reason;
    TestFalse(TEXT("Strict mode refuses fixture control-flow qualification"), E.Start(Program, 1, true, Reason));
    TestTrue(TEXT("Explicit engineering mode may start"), E.Start(Program, 1, false, Reason));
    const auto Missing = E.RunUntilAction([](int32, int32, int32) { return FMHWIRathianThkQueryResult(); });
    TestEqual(TEXT("Unknown is not a false predicate"), int32(Missing.Result), int32(EMHWIRathianThkResult::UnknownCondition));
    TestEqual(TEXT("No guessed action was requested"), Missing.NativeActionId, INDEX_NONE);
    TestFalse(TEXT("Unknown aborts this execution"), E.IsActive());

    TestTrue(TEXT("A newer run can be started"), E.Start(Program, 2, false, Reason));
    const auto Air = E.RunUntilAction([](int32 Function, int32, int32)
    {
        return Function == 0x70 ? Reply(true) : FMHWIRathianThkQueryResult();
    });
    TestEqual(TEXT("Unknown function in an entered branch is refused"), int32(Air.Result), int32(EMHWIRathianThkResult::UnknownCondition));
    TestEqual(TEXT("No fallback action on unknown native side effect"), Air.NativeActionId, INDEX_NONE);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRathianThkYieldIdentity,
    "IntroCpp.MHWI.Rathian.Engineering.ThkYieldIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRathianThkYieldIdentity::RunTest(const FString&)
{
    using namespace RathianEngineeringTests;
    FMHWIRathianThkExecutor E;
    FString Reason;
    TestTrue(TEXT("Start fixture"), E.Start(FixtureProgram(), 10, false, Reason));
    const auto Normal = E.RunUntilAction([](int32, int32, int32) { return Reply(false); });
    TestEqual(TEXT("Call/return reaches normal branch"), Normal.NativeActionId, 86);
    TestFalse(TEXT("Engineering fixture is never certified native"), Normal.bSourceSemanticsQualified);
    const auto Duplicate = E.RunUntilAction({});
    TestEqual(TEXT("Pending action cannot be issued twice"), int32(Duplicate.Result), int32(EMHWIRathianThkResult::WaitingForAction));
    TestFalse(TEXT("Old action cannot acknowledge new run"), E.ResumeAfterAction(9));
    TestTrue(TEXT("Matching action may acknowledge"), E.ResumeAfterAction(10));
    TestEqual(TEXT("Continue to source stop"), int32(E.RunUntilAction({}).Result), int32(EMHWIRathianThkResult::Finished));
    TestFalse(TEXT("Run identity cannot be reused"), E.Start(FixtureProgram(), 10, false, Reason));

    TestTrue(TEXT("New fixture run"), E.Start(FixtureProgram(), 11, false, Reason));
    const auto Cancelled = E.RunUntilAction([&E](int32, int32, int32)
    {
        E.Cancel(11);
        return Reply(false);
    });
    TestEqual(TEXT("Cancellation inside query prevents action"), int32(Cancelled.Result), int32(EMHWIRathianThkResult::StaleRun));
    TestEqual(TEXT("No action after cancellation"), Cancelled.NativeActionId, INDEX_NONE);

    auto Cycle = FixtureProgram();
    auto& Entry = Cycle.Instructions[Cycle.Entry];
    Entry.Op = EMHWIRathianThkOp::Jump; Entry.Next = Cycle.Entry;
    TestTrue(TEXT("Bounded recursive/cyclic fixture"), E.Start(Cycle, 12, false, Reason));
    TestEqual(TEXT("Bad data cannot run forever"), int32(E.RunUntilAction({}, 8).Result),
        int32(EMHWIRathianThkResult::InstructionBudgetExceeded));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRathianSourceMovementIdentity,
    "IntroCpp.MHWI.Rathian.Engineering.SourceMovementIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRathianSourceMovementIdentity::RunTest(const FString&)
{
    using namespace RathianEngineeringTests;
    FWorldFixture F;
    if (!TestNotNull(TEXT("Transient world Pawn"), F.Pawn)
        || !TestNotNull(TEXT("Explicit movement adapter"), F.Movement)) return false;
    const auto Motion = FixtureMotion();
    FString Reason;
    TestFalse(TEXT("Strict source gate refuses fixture"), F.Movement->ConfigureQualifiedMotion(Motion, true, Reason));
    TestTrue(TEXT("Engineering adapter is explicit"), F.Movement->ConfigureQualifiedMotion(Motion, false, Reason));
    F.Pawn->SetActorLocationAndRotation(FVector(10, 20, 0), FRotator(0, 90, 0));
    TestTrue(TEXT("New motion run"), F.Movement->BeginSourceMotion(1, &Reason));
    FHitResult Hit;
    TestFalse(TEXT("Wrong action does not move"), F.Movement->AdvanceToSourceTime(2, 1, Hit, &Reason));
    TestTrue(TEXT("Wrong action preserves location"), F.Pawn->GetActorLocation().Equals(FVector(10, 20, 0), 0.01));
    TestTrue(TEXT("Large step consumes source segments"), F.Movement->AdvanceToSourceTime(1, 2, Hit, &Reason));
    TestTrue(TEXT("Source XY transformed by start yaw exactly once"),
        F.Pawn->GetActorLocation().Equals(FVector(-90, 120, 0), 0.01));
    TestFalse(TEXT("No native wall-clock conversion was guessed"), F.Movement->IsSourceSemanticsQualified());
    TestFalse(TEXT("Reverse seek is refused"), F.Movement->AdvanceToSourceTime(1, 1, Hit, &Reason));
    F.Movement->CancelSourceMotion(1);
    TestFalse(TEXT("Cancelled action cannot move again"), F.Movement->AdvanceToSourceTime(1, 2, Hit, &Reason));
    TestFalse(TEXT("Old action identity cannot be reused"), F.Movement->BeginSourceMotion(1, &Reason));
    return true;
}
#endif
