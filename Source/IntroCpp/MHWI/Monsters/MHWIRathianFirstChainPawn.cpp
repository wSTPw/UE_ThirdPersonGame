#include "MHWIRathianFirstChainPawn.h"

#include "MHWIRathianFirstChainData.h"
#include "MHWIRathianSourceMovementComponent.h"
#include "Animation/AnimSequence.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/SkeletalMesh.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Templates/UnrealTemplate.h"

namespace
{
FString ConditionKey(int32 Function, int32 Parameter1, int32 Parameter2)
{
    return FString::Printf(TEXT("%d:%d:%d"), Function, Parameter1, Parameter2);
}
}

AMHWIRathianFirstChainPawn::AMHWIRathianFirstChainPawn()
{
    PrimaryActorTick.bCanEverTick = false;
    AutoPossessAI = EAutoPossessAI::Disabled;
    SourceRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SourceRoot"));
    SetRootComponent(SourceRoot);
    Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(SourceRoot);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetComponentTickEnabled(false);
    Body->bEnableUpdateRateOptimizations = false; // UE5.8：USkinnedMeshComponent 成员（旧名 bUseUpdateRateOptimizations 已移除）
    Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    SourceMovement = CreateDefaultSubobject<UMHWIRathianSourceMovementComponent>(TEXT("SourceMovement"));
    SourceMovement->SetUpdatedComponent(SourceRoot);
    SourceCollision = CreateDefaultSubobject<UMHWIRathianSourceCollisionComponent>(TEXT("SourceCollision"));
}

UPawnMovementComponent* AMHWIRathianFirstChainPawn::GetMovementComponent() const
{
    return SourceMovement;
}

bool AMHWIRathianFirstChainPawn::Fail(const FString& Reason)
{
    LastFailure = Reason;
    CancelSourceAction();
    return false;
}

bool AMHWIRathianFirstChainPawn::ReadProgram(const FString& Json, FString& OutReason)
{
    Program = FMHWIRathianThkProgram();
    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Root) || !Root.IsValid())
    { OutReason = TEXT("Cannot read compiled THK normal form."); return false; }
    int32 Schema = 0;
    const TArray<TSharedPtr<FJsonValue>>* Instructions = nullptr;
    if (!Root->TryGetNumberField(TEXT("schema"), Schema) || Schema != 1
        || !Root->TryGetStringField(TEXT("source_sha256"), Program.SourceSha256)
        || !Root->TryGetStringField(TEXT("source_path"), Program.SourcePath)
        || !Root->TryGetStringField(TEXT("entry"), Program.Entry)
        || !Root->TryGetBoolField(TEXT("native_control_flow_verified"), Program.bNativeControlFlowVerified)
        || !Root->TryGetArrayField(TEXT("instructions"), Instructions))
    { OutReason = TEXT("THK normal-form identity/schema is incomplete."); return false; }
    const TMap<FString, EMHWIRathianThkOp> Operations = {
        {TEXT("Jump"),EMHWIRathianThkOp::Jump}, {TEXT("Call"),EMHWIRathianThkOp::Call},
        {TEXT("Return"),EMHWIRathianThkOp::Return}, {TEXT("Branch"),EMHWIRathianThkOp::Branch},
        {TEXT("YieldAction"),EMHWIRathianThkOp::YieldAction}, {TEXT("Stop"),EMHWIRathianThkOp::Stop}};
    for (const auto& Value : *Instructions)
    {
        const TSharedPtr<FJsonObject> Row = Value->AsObject();
        FMHWIRathianThkInstruction I;
        FString Op;
        if (!Row.IsValid() || !Row->TryGetStringField(TEXT("key"), I.Key)
            || !Row->TryGetStringField(TEXT("op"), Op) || !Operations.Contains(Op)
            || !Row->TryGetStringField(TEXT("source_evidence"), I.SourceEvidence)
            || !Row->TryGetBoolField(TEXT("native_consumer_verified"), I.bNativeConsumerVerified)
            || I.Key.IsEmpty() || Program.Instructions.Contains(I.Key))
        { OutReason = TEXT("THK instruction is invalid, unknown, or duplicated."); return false; }
        I.Op = Operations[Op];
        Row->TryGetStringField(TEXT("next"), I.Next);
        Row->TryGetStringField(TEXT("otherwise"), I.Otherwise);
        Row->TryGetStringField(TEXT("call_target"), I.CallTarget);
        const auto ReadInteger = [&Row](const TCHAR* Key, int32& Out)
        {
            double Number = 0;
            if (!Row->TryGetNumberField(Key, Number) || !FMath::IsFinite(Number)
                || Number < MIN_int32 || Number > MAX_int32 || Number != FMath::FloorToDouble(Number)) return false;
            Out = static_cast<int32>(Number); return true;
        };
        if (I.Op == EMHWIRathianThkOp::Branch
            && (!ReadInteger(TEXT("function_type"), I.FunctionType)
                || !ReadInteger(TEXT("parameter1"), I.Parameter1) || !ReadInteger(TEXT("parameter2"), I.Parameter2)))
        { OutReason = TEXT("Native THK predicate identity is not an exact int32."); return false; }
        if (I.Op == EMHWIRathianThkOp::YieldAction
            && !ReadInteger(TEXT("native_action_id"), I.NativeActionId))
        { OutReason = TEXT("Native THK action identity is not an exact int32."); return false; }
        Program.Instructions.Add(I.Key, MoveTemp(I));
    }
    return true;
}

bool AMHWIRathianFirstChainPawn::ConfigureChain(
    UMHWIRathianFirstChainData* Data, bool bEngineeringEvidenceMode)
{
    check(IsInGameThread());
    if (bAdvancing) return false;
    CancelSourceAction();
    bConfigured = false;
    bCompleted = false;
    LastFailure.Reset();
    ContactObservations.Reset();
    EngineeringConditions.Reset();
    ChainData = nullptr;
    if (!IsValid(Data) || Data->SourceProfile.IsEmpty()
        || !FMath::IsFinite(Data->SequenceSecondsPerSourceUnit) || Data->SequenceSecondsPerSourceUnit <= 0.0)
        return Fail(TEXT("Missing source profile or imported-sequence time mapping."));
    USkeletalMesh* Mesh = Data->BodyMesh.LoadSynchronous();
    UAnimSequence* Sequence = Data->InPlaceSequence.LoadSynchronous();
    if (!Mesh || !Sequence || Mesh->GetSkeleton() != Sequence->GetSkeleton())
        return Fail(TEXT("Body mesh and sequence must exist and share the verified skeleton."));
    if (!Data->bRequireSourceSemantics && !bEngineeringEvidenceMode)
        return Fail(TEXT("An engineering asset requires explicit engineering execution."));
    FString Reason;
    if (!ReadProgram(Data->ThkProgramJson, Reason)) return Fail(Reason);
    if (!SourceMovement->ConfigureQualifiedMotion(Data->SourceMotion, !bEngineeringEvidenceMode, Reason))
        return Fail(Reason);
    if (Data->SourceMotion.Samples.IsEmpty()) return Fail(TEXT("No explicit source trajectory."));
    const double ExpectedSequenceEnd = Data->SourceMotion.Samples.Last().SourceTime * Data->SequenceSecondsPerSourceUnit;
    if (FMath::Abs(ExpectedSequenceEnd - Sequence->GetPlayLength()) > 0.001)
        return Fail(TEXT("Imported sequence duration does not match the explicit source-to-asset mapping."));
    Body->SetSkeletalMesh(Mesh);
    Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    Body->SetAnimation(Sequence);
    Body->SetComponentTickEnabled(false);
    ChainData = Data;
    if (!EvaluateSourcePose(0.0)) { ChainData = nullptr; return false; }
    if (!SourceCollision->ConfigureFromEvidenceJson(Body, Data->CollisionEvidenceJson, !bEngineeringEvidenceMode, Reason))
    { ChainData = nullptr; return Fail(Reason); }
    bEngineeringMode = bEngineeringEvidenceMode;
    bConfigured = true;
    return true;
}

bool AMHWIRathianFirstChainPawn::EvaluateSourcePose(double SourceTime)
{
    if (!IsValid(ChainData) || !IsValid(Body) || !Body->GetSkeletalMeshAsset())
        return Fail(TEXT("Source chain mesh/data ended."));
    const double SequenceTime = SourceTime * ChainData->SequenceSecondsPerSourceUnit;
    Body->SetPosition(static_cast<float>(SequenceTime), false);
    Body->TickAnimation(0.f, false);
    Body->RefreshBoneTransforms();
    Body->UpdateComponentToWorld();
    return true;
}

void AMHWIRathianFirstChainPawn::SetEngineeringCondition(
    int32 FunctionType, int32 Parameter1, int32 Parameter2, bool Value)
{
    check(IsInGameThread());
    if (!bConfigured || !bEngineeringMode || bActive || bAdvancing) return;
    FMHWIRathianThkQueryResult Reply;
    Reply.bAvailable = true;
    Reply.Value = Value;
    Reply.bNativeConsumerVerified = false;
    Reply.Evidence = TEXT("Explicit controlled-context injection; not a native consumer observation.");
    EngineeringConditions.Add(ConditionKey(FunctionType, Parameter1, Parameter2), MoveTemp(Reply));
}

bool AMHWIRathianFirstChainPawn::StartSourceDecision()
{
    check(IsInGameThread());
    if (!bConfigured || !IsValid(ChainData) || bActive || bAdvancing) return false;
    CurrentRunId = ++LastIssuedRunId;
    FString Reason;
    if (!Thk.Start(Program, CurrentRunId, !bEngineeringMode, Reason)) return Fail(Reason);
    LastDecision = Thk.RunUntilAction([this](int32 Function, int32 P1, int32 P2)
    {
        const FMHWIRathianThkQueryResult* Reply = EngineeringConditions.Find(ConditionKey(Function, P1, P2));
        return Reply ? *Reply : FMHWIRathianThkQueryResult();
    });
    if (LastDecision.Result != EMHWIRathianThkResult::YieldedAction)
        return Fail(LastDecision.Reason.IsEmpty() ? TEXT("THK did not yield a qualified action.") : LastDecision.Reason);
    if (LastDecision.NativeActionId != ChainData->SourceMotion.NativeActionId)
        return Fail(TEXT("THK action has no matching qualified motion in this chain."));
    if (!EvaluateSourcePose(0.0)
        || !SourceMovement->BeginSourceMotion(CurrentRunId, &Reason)
        || !SourceCollision->BeginAction(CurrentRunId, LastDecision.NativeActionId))
        return Fail(Reason.IsEmpty() ? SourceCollision->GetLastFailure() : Reason);
    CurrentSourceTime = 0.0;
    bActive = true;
    bCompleted = false;
    TArray<FMHWIRathianSourceContact> Initial;
    if (!SourceCollision->AdvanceSourceInterval(CurrentRunId, 0.0, 0.0, Initial))
        return Fail(SourceCollision->GetLastFailure());
    ContactObservations.Append(Initial);
    return true;
}

bool AMHWIRathianFirstChainPawn::AdvanceSourceTime(double AbsoluteSourceTime)
{
    check(IsInGameThread());
    if (!bActive || !IsValid(ChainData) || bAdvancing) return false;
    const double EndTime = ChainData->SourceMotion.Samples.Last().SourceTime;
    if (!FMath::IsFinite(AbsoluteSourceTime) || AbsoluteSourceTime < CurrentSourceTime || AbsoluteSourceTime > EndTime)
        return Fail(TEXT("Source time is invalid, reversed or past the declared trajectory."));
    if (AbsoluteSourceTime == CurrentSourceTime) return true;
    TGuardValue<bool> Guard(bAdvancing, true);
    const uint64 ExpectedRun = CurrentRunId;
    TArray<double> Stops;
    for (const auto& Sample : ChainData->SourceMotion.Samples)
        if (Sample.SourceTime > CurrentSourceTime && Sample.SourceTime < AbsoluteSourceTime) Stops.Add(Sample.SourceTime);
    TArray<double> Boundaries;
    SourceCollision->GetSourceBoundaries(Boundaries);
    for (const double Boundary : Boundaries)
        if (Boundary > CurrentSourceTime && Boundary < AbsoluteSourceTime) Stops.AddUnique(Boundary);
    Stops.AddUnique(AbsoluteSourceTime);
    Stops.Sort();
    for (const double Stop : Stops)
    {
        FHitResult Blocking;
        FString Reason;
        if (!SourceMovement->AdvanceToSourceTime(ExpectedRun, Stop, Blocking, &Reason)) return Fail(Reason);
        if (!bActive || CurrentRunId != ExpectedRun || !IsValid(ChainData)) return false;
        if (!EvaluateSourcePose(Stop)) return false;
        TArray<FMHWIRathianSourceContact> Contacts;
        if (!SourceCollision->AdvanceSourceInterval(ExpectedRun, CurrentSourceTime, Stop, Contacts))
            return Fail(SourceCollision->GetLastFailure());
        ContactObservations.Append(Contacts);
        CurrentSourceTime = Stop;
        if (ContactObservations.Num() > 100000) return Fail(TEXT("Contact observation budget exceeded."));
    }
    if (CurrentSourceTime == EndTime)
    {
        SourceMovement->CancelSourceMotion(ExpectedRun);
        SourceCollision->EndAction(ExpectedRun);
        Thk.Cancel(ExpectedRun);
        bActive = false;
        bCompleted = true;
    }
    return true;
}

void AMHWIRathianFirstChainPawn::CancelSourceAction()
{
    if (CurrentRunId)
    {
        Thk.Cancel(CurrentRunId);
        if (SourceMovement) SourceMovement->CancelSourceMotion(CurrentRunId);
        if (SourceCollision) SourceCollision->EndAction(CurrentRunId);
    }
    bActive = false;
    CurrentRunId = 0;
}

FString AMHWIRathianFirstChainPawn::GetChainSnapshotJson() const
{
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetBoolField(TEXT("configured"), bConfigured);
    Root->SetBoolField(TEXT("active"), bActive);
    Root->SetBoolField(TEXT("completed"), bCompleted);
    Root->SetBoolField(TEXT("engineering_evidence_mode"), bEngineeringMode);
    Root->SetBoolField(TEXT("original_game_runtime_compared"), false);
    Root->SetStringField(TEXT("action_run_id"), LexToString(CurrentRunId));
    Root->SetNumberField(TEXT("source_time"), CurrentSourceTime);
    Root->SetNumberField(TEXT("native_action_id"), LastDecision.NativeActionId);
    Root->SetBoolField(TEXT("decision_native_qualified"), LastDecision.bSourceSemanticsQualified);
    Root->SetBoolField(TEXT("movement_native_qualified"), SourceMovement && SourceMovement->IsSourceSemanticsQualified());
    Root->SetStringField(TEXT("last_failure"), LastFailure);
    Root->SetStringField(TEXT("source_profile"), ChainData ? ChainData->SourceProfile : TEXT(""));
    const FVector Location = GetActorLocation();
    TArray<TSharedPtr<FJsonValue>> Position = {MakeShared<FJsonValueNumber>(Location.X),
        MakeShared<FJsonValueNumber>(Location.Y), MakeShared<FJsonValueNumber>(Location.Z)};
    Root->SetArrayField(TEXT("actor_location"), Position);
    TArray<TSharedPtr<FJsonValue>> Trace;
    for (const FString& Key : LastDecision.VisitedInstructions) Trace.Add(MakeShared<FJsonValueString>(Key));
    Root->SetArrayField(TEXT("decision_trace"), Trace);
    TArray<TSharedPtr<FJsonValue>> Contacts;
    for (const auto& C : ContactObservations)
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("target"), C.Target.IsValid() ? C.Target->GetPathName() : TEXT("expired"));
        Row->SetNumberField(TEXT("source_time"), C.SourceTime);
        Row->SetNumberField(TEXT("uid"), C.TimelineUid);
        Row->SetNumberField(TEXT("attack_index"), C.AttackIndex);
        Row->SetNumberField(TEXT("geometry_index"), C.GeometryIndex);
        Row->SetNumberField(TEXT("inner_geometry_index"), C.InnerGeometryIndex);
        Row->SetBoolField(TEXT("current_pose_overlap"), C.bCurrentPoseOverlap);
        Row->SetBoolField(TEXT("conservative_candidate"), C.bConservativeQueryCandidate);
        Row->SetBoolField(TEXT("native_damage_qualified"), C.bNativeDamageQualified);
        Row->SetBoolField(TEXT("native_rehit_qualified"), C.bNativeRehitQualified);
        Contacts.Add(MakeShared<FJsonValueObject>(Row));
    }
    Root->SetArrayField(TEXT("contacts"), Contacts);
    Root->SetNumberField(TEXT("contact_observations"), ContactObservations.Num());
    FString Json;
    FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Json));
    return Json;
}

void AMHWIRathianFirstChainPawn::EndPlay(const EEndPlayReason::Type Reason)
{
    CancelSourceAction();
    bConfigured = false;
    Super::EndPlay(Reason);
}
