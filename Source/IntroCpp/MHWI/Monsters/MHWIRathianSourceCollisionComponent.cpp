#include "MHWI/Monsters/MHWIRathianSourceCollisionComponent.h"

#include "CollisionQueryParams.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    bool ReadVector(const TSharedPtr<FJsonObject>& Object, const TCHAR* Key, FVector& Out)
    {
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!Object.IsValid() || !Object->TryGetArrayField(Key, Values) || Values->Num() != 3)
            return false;
        double X, Y, Z;
        if (!(*Values)[0]->TryGetNumber(X) || !(*Values)[1]->TryGetNumber(Y)
            || !(*Values)[2]->TryGetNumber(Z) || !FMath::IsFinite(X)
            || !FMath::IsFinite(Y) || !FMath::IsFinite(Z))
            return false;
        Out = FVector(X, Y, Z);
        return true;
    }

    bool Qualified(const TSharedPtr<FJsonObject>& Object, const TCHAR* Key)
    {
        bool Value = false;
        return Object.IsValid() && Object->TryGetBoolField(Key, Value) && Value;
    }

    bool UniformScale(const FVector& Scale)
    {
        const FVector Magnitude = Scale.GetAbs();
        return !Scale.ContainsNaN() && Magnitude.X > UE_SMALL_NUMBER
            && FMath::IsNearlyEqual(Magnitude.X, Magnitude.Y, 1.e-4)
            && FMath::IsNearlyEqual(Magnitude.X, Magnitude.Z, 1.e-4);
    }
}

UMHWIRathianSourceCollisionComponent::UMHWIRathianSourceCollisionComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

bool UMHWIRathianSourceCollisionComponent::Fail(const FString& Reason)
{
    LastFailure = Reason;
    return false;
}

void UMHWIRathianSourceCollisionComponent::ClearConfiguration()
{
    ActiveRunId = 0;
    bConfigured = false;
    SourceMesh.Reset();
    Capsules.Reset();
    PreviousPose.Reset();
    NativeActionId = TimelineUid = AttackIndex = GeometryIndex = INDEX_NONE;
    WindowStart = WindowEnd = LastSourceTime = UnitsPerSecond = 0.0;
    TimeUnit.Reset();
    bRehitQualified = bDamageQualified = false;
}

bool UMHWIRathianSourceCollisionComponent::ConfigureFromEvidence(
    USkeletalMeshComponent* InMesh, const FString& JsonPath, FString& OutError)
{
    check(IsInGameThread());
    FString JsonText;
    if (!FFileHelper::LoadFileToString(JsonText, *JsonPath))
    {
        ClearConfiguration();
        OutError = TEXT("Cannot read collision evidence file.");
        return Fail(OutError);
    }
    return ConfigureFromEvidenceJson(InMesh, JsonText, true, OutError);
}

bool UMHWIRathianSourceCollisionComponent::ConfigureFromEvidenceJson(
    USkeletalMeshComponent* InMesh, const FString& JsonText, bool bStrict, FString& OutError)
{
    check(IsInGameThread());
    ClearConfiguration();
    LastFailure.Reset();
    auto Reject = [this, &OutError](const FString& Reason)
    {
        ClearConfiguration();
        OutError = Reason;
        return Fail(Reason);
    };
    if (!IsValid(InMesh) || !InMesh->GetSkeletalMeshAsset())
        return Reject(TEXT("Collision evidence requires an actual skeletal mesh."));

    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(JsonText), Root)
        || !Root.IsValid())
        return Reject(TEXT("Cannot read collision evidence JSON."));
    int32 Schema = 0;
    const TSharedPtr<FJsonObject>* Profile = nullptr;
    if (!Root->TryGetNumberField(TEXT("schema"), Schema) || Schema != 1
        || !Root->TryGetObjectField(TEXT("runtime_profile"), Profile))
        return Reject(TEXT("Unsupported collision evidence schema/runtime_profile."));
    const TSharedPtr<FJsonObject>* Qualification = nullptr;
    if (!(*Profile)->TryGetObjectField(TEXT("qualification"), Qualification))
        return Reject(TEXT("Collision report has no qualification record."));
    const TCHAR* Required[] = {TEXT("action_binding"), TEXT("timeline_flags_uid"),
        TEXT("geometry_remap"), TEXT("native_clock"), TEXT("ue_local_basis")};
    for (const TCHAR* Key : Required)
        if ((bStrict || FString(Key) == TEXT("geometry_remap")) && !Qualified(*Qualification, Key))
            return Reject(FString::Printf(TEXT("Unqualified native collision dependency: %s"), Key));

    if (!(*Profile)->TryGetStringField(TEXT("time_unit"), TimeUnit)
        || TimeUnit != TEXT("NativeFrames")
        || !(*Profile)->TryGetNumberField(TEXT("units_per_second"), UnitsPerSecond)
        || !FMath::IsFinite(UnitsPerSecond) || UnitsPerSecond < 0.0 || (bStrict && UnitsPerSecond == 0.0)
        || !(*Profile)->TryGetNumberField(TEXT("window_start"), WindowStart)
        || !(*Profile)->TryGetNumberField(TEXT("window_end"), WindowEnd)
        || !FMath::IsFinite(WindowStart) || !FMath::IsFinite(WindowEnd)
        || WindowStart < 0.0 || WindowEnd <= WindowStart)
        return Reject(TEXT("Invalid or unknown native time domain/window."));
    if (!(*Profile)->TryGetNumberField(TEXT("native_action_id"), NativeActionId)
        || !(*Profile)->TryGetNumberField(TEXT("timeline_uid"), TimelineUid)
        || !(*Profile)->TryGetNumberField(TEXT("attack_index"), AttackIndex)
        || !(*Profile)->TryGetNumberField(TEXT("geometry_index"), GeometryIndex)
        || NativeActionId < 0 || TimelineUid < 0 || AttackIndex < 0 || GeometryIndex < 0)
        return Reject(TEXT("Missing native action/UID/attack/geometry identity."));

    const TArray<TSharedPtr<FJsonValue>>* Shapes = nullptr;
    if (!(*Profile)->TryGetArrayField(TEXT("capsules"), Shapes) || Shapes->IsEmpty())
        return Reject(TEXT("No qualified original capsules."));
    TSet<int32> SeenInner;
    for (const TSharedPtr<FJsonValue>& Value : *Shapes)
    {
        const TSharedPtr<FJsonObject> Shape = Value->AsObject();
        FSourceCapsule Capsule;
        FString Bone0, Bone1;
        int32 ShapeKind = INDEX_NONE;
        if (!Shape.IsValid() || !Shape->TryGetNumberField(TEXT("shape"), ShapeKind)
            || ShapeKind != 1 || !Shape->TryGetNumberField(TEXT("inner_index"), Capsule.InnerIndex)
            || Capsule.InnerIndex < 0 || SeenInner.Contains(Capsule.InnerIndex)
            || !Shape->TryGetStringField(TEXT("bone0"), Bone0)
            || !Shape->TryGetStringField(TEXT("bone1"), Bone1)
            || !ReadVector(Shape, TEXT("offset0_ue_local"), Capsule.Offset0)
            || !ReadVector(Shape, TEXT("offset1_ue_local"), Capsule.Offset1)
            || !Shape->TryGetNumberField(TEXT("radius_ue_units"), Capsule.Radius)
            || !FMath::IsFinite(Capsule.Radius) || Capsule.Radius <= 0.0)
            return Reject(TEXT("Invalid, duplicate or unsupported original capsule geometry."));
        Capsule.Bone0 = FName(*Bone0);
        Capsule.Bone1 = FName(*Bone1);
        if (InMesh->GetBoneIndex(Capsule.Bone0) == INDEX_NONE
            || InMesh->GetBoneIndex(Capsule.Bone1) == INDEX_NONE)
            return Reject(TEXT("COL function-to-imported-bone mapping does not exist on the actual mesh."));
        SeenInner.Add(Capsule.InnerIndex);
        Capsules.Add(Capsule);
    }
    bRehitQualified = Qualified(*Qualification, TEXT("native_rehit"));
    bDamageQualified = Qualified(*Qualification, TEXT("native_damage"));
    // This adapter never applies damage, even if an external settlement later qualifies it.
    SourceMesh = InMesh;
    bConfigured = true;
    bStrictNative = bStrict;
    OutError.Reset();
    return true;
}

bool UMHWIRathianSourceCollisionComponent::CapturePose(TArray<FWorldCapsule>& OutPose)
{
    USkeletalMeshComponent* Mesh = SourceMesh.Get();
    if (!IsValid(Mesh))
        return Fail(TEXT("Source mesh was destroyed."));
    OutPose.Reset(Capsules.Num());
    for (const FSourceCapsule& Capsule : Capsules)
    {
        // GetBoneTransform returns component fallback for missing names: reject that case explicitly.
        if (Mesh->GetBoneIndex(Capsule.Bone0) == INDEX_NONE
            || Mesh->GetBoneIndex(Capsule.Bone1) == INDEX_NONE)
            return Fail(TEXT("Required native bone is no longer available."));
        const FTransform Bone0 = Mesh->GetBoneTransform(Capsule.Bone0, RTS_World);
        const FTransform Bone1 = Mesh->GetBoneTransform(Capsule.Bone1, RTS_World);
        if (Bone0.ContainsNaN() || Bone1.ContainsNaN()
            || !UniformScale(Bone0.GetScale3D()) || !UniformScale(Bone1.GetScale3D()))
            return Fail(TEXT("Nonuniform/invalid bone scale is outside this qualified capsule adapter."));
        FWorldCapsule World;
        World.Point0 = Bone0.TransformPosition(Capsule.Offset0);
        World.Point1 = Bone1.TransformPosition(Capsule.Offset1);
        World.Radius = Capsule.Radius * FMath::Abs(Bone0.GetScale3D().X);
        if (!FMath::IsFinite(World.Radius) || World.Radius <= 0.0)
            return Fail(TEXT("Invalid world-space original capsule radius."));
        OutPose.Add(World);
    }
    return true;
}

bool UMHWIRathianSourceCollisionComponent::BeginAction(uint64 InRunId, int32 InNativeActionId)
{
    check(IsInGameThread());
    if (!bConfigured || InRunId == 0 || ActiveRunId != 0 || InNativeActionId != NativeActionId)
        return Fail(TEXT("Unconfigured, busy, invalid run identity or unsupported native action."));
    TArray<FWorldCapsule> Initial;
    if (!CapturePose(Initial))
        return false;
    ActiveRunId = InRunId;
    LastSourceTime = 0.0;
    PreviousPose = MoveTemp(Initial);
    LastFailure.Reset();
    return true;
}

void UMHWIRathianSourceCollisionComponent::GetSourceBoundaries(TArray<double>& OutTimes) const
{
    OutTimes.Reset();
    if (bConfigured)
    {
        OutTimes.Add(WindowStart);
        OutTimes.Add(WindowEnd);
    }
}

bool UMHWIRathianSourceCollisionComponent::AdvanceSourceInterval(uint64 InRunId,
    double PreviousSourceTime, double CurrentSourceTime,
    TArray<FMHWIRathianSourceContact>& OutContacts)
{
    check(IsInGameThread());
    OutContacts.Reset();
    if (!bConfigured || InRunId == 0 || InRunId != ActiveRunId)
        return Fail(TEXT("Stale or inactive source collision run."));
    if (!FMath::IsFinite(PreviousSourceTime) || !FMath::IsFinite(CurrentSourceTime)
        || PreviousSourceTime < 0.0 || CurrentSourceTime < PreviousSourceTime
        || !FMath::IsNearlyEqual(PreviousSourceTime, LastSourceTime, 1.e-7))
        return Fail(TEXT("Noncontiguous, backward or invalid source-time interval."));
    for (double Boundary : {WindowStart, WindowEnd})
        if (PreviousSourceTime < Boundary && CurrentSourceTime > Boundary)
            return Fail(TEXT("Evaluate the source pose at the collision boundary before advancing across it."));

    TArray<FWorldCapsule> CurrentPose;
    if (!CapturePose(CurrentPose))
        return false;
    UWorld* World = GetWorld();
    if (!World || PreviousPose.Num() != CurrentPose.Num())
        return Fail(TEXT("Source collision world/pose unavailable."));

    const bool bCurrentActive = CurrentSourceTime >= WindowStart && CurrentSourceTime < WindowEnd;
    const bool bIntervalActive = CurrentSourceTime > PreviousSourceTime
        && PreviousSourceTime >= WindowStart && PreviousSourceTime < WindowEnd;
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(MHWIRathianSourceCollision), false, GetOwner());
    Query.bFindInitialOverlaps = true;

    for (int32 Index = 0; Index < CurrentPose.Num(); ++Index)
    {
        const FWorldCapsule& Before = PreviousPose[Index];
        const FWorldCapsule& After = CurrentPose[Index];
        const FVector Center = (After.Point0 + After.Point1) * 0.5;
        const FVector Delta = After.Point1 - After.Point0;
        const double HalfHeight = Delta.Size() * 0.5 + After.Radius;
        const FQuat Rotation = Delta.IsNearlyZero() ? FQuat::Identity
            : FQuat::FindBetweenNormals(FVector::UpVector, Delta.GetSafeNormal());
        const FCollisionShape Shape = FCollisionShape::MakeCapsule(
            static_cast<float>(After.Radius), static_cast<float>(HalfHeight));
        TMap<TWeakObjectPtr<AActor>, FMHWIRathianSourceContact> ThisShape;
        auto MakeContact = [this, InRunId, Index](AActor* Target, double Time)
        {
            FMHWIRathianSourceContact Contact;
            Contact.ActionRunId = InRunId;
            Contact.NativeActionId = NativeActionId;
            Contact.TimelineUid = TimelineUid;
            Contact.AttackIndex = AttackIndex;
            Contact.GeometryIndex = GeometryIndex;
            Contact.InnerGeometryIndex = Capsules[Index].InnerIndex;
            Contact.SourceTime = Time;
            Contact.Target = Target;
            Contact.bEngineeringEvidenceMode = !bStrictNative;
            Contact.bNativeRehitQualified = bStrictNative && bRehitQualified;
            Contact.bNativeDamageQualified = bStrictNative && bDamageQualified;
            return Contact;
        };
        if (bIntervalActive)
        {
            const FVector BeforeCenter = (Before.Point0 + Before.Point1) * 0.5;
            const FVector BeforeDelta = Before.Point1 - Before.Point0;
            const bool bPureTranslation = BeforeDelta.Equals(Delta, 1.e-4)
                && FMath::IsNearlyEqual(Before.Radius, After.Radius, 1.e-4);
            // UE capsule sweep has one orientation. A changing-axis sweep is only a bound
            // on linear endpoint interpolation, never an exact rotating-capsule hit.
            const FCollisionShape SweepShape = bPureTranslation ? Shape
                : FCollisionShape::MakeSphere(static_cast<float>(
                    FMath::Max(Before.Radius, After.Radius)
                    + 0.5 * FMath::Max(BeforeDelta.Size(), Delta.Size())));
            TArray<FHitResult> Hits;
            World->SweepMultiByObjectType(Hits, BeforeCenter, Center,
                bPureTranslation ? Rotation : FQuat::Identity, Objects, SweepShape, Query);
            for (const FHitResult& Hit : Hits)
            {
                AActor* Target = Hit.GetActor();
                const double Time = FMath::Lerp(PreviousSourceTime, CurrentSourceTime,
                    static_cast<double>(Hit.Time));
                if (!IsValid(Target) || Target == GetOwner() || Time >= WindowEnd)
                    continue;
                FMHWIRathianSourceContact Contact = MakeContact(Target, Time);
                Contact.Hit = Hit;
                Contact.bConservativeQueryCandidate = !bPureTranslation;
                ThisShape.Add(Target, MoveTemp(Contact));
            }
        }
        if (bCurrentActive)
        {
            TArray<FOverlapResult> Overlaps;
            World->OverlapMultiByObjectType(Overlaps, Center, Rotation, Objects, Shape, Query);
            for (const FOverlapResult& Overlap : Overlaps)
            {
                AActor* Target = Overlap.GetActor();
                if (!IsValid(Target) || Target == GetOwner())
                    continue;
                FMHWIRathianSourceContact Contact = MakeContact(Target, CurrentSourceTime);
                Contact.bCurrentPoseOverlap = true;
                // Exact current-pose overlap supersedes a conservative continuous candidate.
                // Overlap has no impact point/normal: leave Hit default instead of fabricating one.
                ThisShape.Add(Target, MoveTemp(Contact));
            }
        }
        for (const auto& Pair : ThisShape)
            OutContacts.Add(Pair.Value);
    }
    PreviousPose = MoveTemp(CurrentPose);
    LastSourceTime = CurrentSourceTime;
    LastFailure.Reset();
    // No cross-interval hit ledger: contacts are observations, not native re-hit authorization.
    return true;
}

void UMHWIRathianSourceCollisionComponent::EndAction(uint64 InRunId)
{
    check(IsInGameThread());
    if (InRunId == 0 || InRunId != ActiveRunId)
        return;
    ActiveRunId = 0;
    PreviousPose.Reset();
    LastSourceTime = 0.0;
}

void UMHWIRathianSourceCollisionComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    ClearConfiguration();
    Super::EndPlay(EndPlayReason);
}