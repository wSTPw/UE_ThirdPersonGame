#pragma once

#include "CoreMinimal.h"
#include "MHWINativeLinkMotion.h"

class UAnimMontage;
class UAnimSequenceBase;

namespace MHWI::Native
{
    struct FNodeIdentity { int32 Node; FActionIdentity Identity; };
    struct FMoveNode { FName Move; int32 Node; };
    struct FMoveTimeline { FName Move; int32 Motion; };
    struct FMainMotionBinding { int32 Node; int32 Motion; };
    struct FMotionInfo { int32 Motion; int32 Frames; int32 Loop; };
    struct FPhaseKey { FName Bank; int32 Motion; float Frame; int32 Value; };
    struct FConnectorWeaponKey { int32 Motion; float Frame; int32 Value; };
    struct FActionEntryPlan
    {
        FPlaybackRequest First;
        FMotionSample BlendPrevious;
        const FLinkEntry* Link = nullptr;
        bool bFollowMain = false;
        bool bContinuePrevious = false;
    };

    int32 GetMoveNode(FName Move, bool bSheathedRoll);
    int32 GetTimelineMotion(FName Move, int32 SpiritLevel, int32 ActualBodyMotion);
    int32 GetNativeMainMotion(int32 Node);
    const FMotionInfo* GetMotionInfo(int32 Motion);
    TConstArrayView<int32> GetConnectorMotions();
    TConstArrayView<FConnectorWeaponKey> GetConnectorWeaponKeys();
    int32 SampleLinkPhase(const FMotionSample& Motion);
    /** Native forward branch, layer +64 endpoint; no duration/BlendOut heuristic. */
    uint32 ForwardEndFlags(float Frame, float Advance, int32 Endpoint);

    /** Resolve a project FSM adapter without pretending an alias is the live native ID.
     * Every possible source identity must give the same exact match (including none).
     * An ambiguous alias set is rejected, never collapsed to its first member.
     */
    bool ResolveNodeLink(int32 TargetNode, int32 PreviousNode, int32 Phase,
        const FLinkEntry*& OutEntry);
    /** Exact runtime identity path for native source owners (Step/Creep/Shot).
     * The source must be in the original source set for this destination.
     */
    bool ResolveIdentityLink(int32 TargetNode, FActionIdentity Previous, int32 Phase,
        const FLinkEntry*& OutEntry);
    bool IsKnownSourceIdentity(FActionIdentity Identity);
    TArray<FActionIdentity> GetNodeIdentities(int32 Node);
    /** Complete ordered entry policy, including native pre/generic/post requests.
     * bPreviousDrawn is the equipment snapshot before the new action enters.
     */
    FActionEntryPlan ResolveActionEntry(int32 TargetNode, FActionIdentity Target,
        FActionIdentity PreviousAction, bool bPreviousDrawn, int32 MainMotion,
        const FMotionSample& PreviousMotion);

    /** Inspect the actually selected UE segment, including variant and segment trim. */
    bool ReadMotion(const UAnimMontage* Montage, float Position, FMotionSample& OutMotion);
    bool ReadSequenceMotion(const UAnimSequenceBase* Sequence, float Position, FMotionSample& OutMotion);
    bool ReadMainMotion(const UAnimMontage* Montage, int32& OutMotion);
    bool MainPosition(const UAnimMontage* Montage, int32 Motion, int32 SourceFrame, float& OutPosition);
    /** General selected-segment clock, including common-bank predecessor motion. */
    bool MotionPosition(const UAnimMontage* Montage, FName Bank, int32 Motion,
        float SourceFrame, float& OutPosition);
}
