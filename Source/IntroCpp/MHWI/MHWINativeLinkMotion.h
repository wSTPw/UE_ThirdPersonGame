#pragma once

#include "CoreMinimal.h"

/** Native-frame control policy, independent of UE montage/blend-time adaptation.
 * Evidence: Tools/MHW/native-link-motion-policy.json. This does not execute game code.
 */
namespace MHWI::Native
{
    struct FActionIdentity
    {
        int32 Group = INDEX_NONE;
        int32 Action = INDEX_NONE;
        bool operator==(const FActionIdentity& Other) const
        { return Group == Other.Group && Action == Other.Action; }
    };

    /** Destination-owned, ordered native 16-byte record plus diagnostic identity. */
    struct FLinkEntry
    {
        FActionIdentity Target;
        FActionIdentity Previous;
        int32 Motion = INDEX_NONE;
        int32 Phase = 0;
        int32 Node = INDEX_NONE;
    };

    struct FMotionSample
    {
        FName Bank;
        /** Decoded low-nine-bit motion ID, not the packed bank/motion request. */
        int32 Motion = INDEX_NONE;
        float Frame = 0.f;
    };

    /** MBD values retain native units; unknown blend semantics are not UE seconds. */
    struct FBlendEntry
    {
        int32 TargetMotion = INDEX_NONE;
        int32 PreviousMotion = INDEX_NONE;
        FName PreviousBank;
        float PreviousFrameLimit = 0.f;
        int32 StartFrame = 0;
        int32 InterpolationPoint = 0;
        int32 OverlapBlending = 0;
        float Unknown8 = 0.f;
        int32 One0 = 0;
        int32 Min1 = 0;
    };

    struct FPlaybackRequest
    {
        int32 Motion = INDEX_NONE;
        /** Serialized row zero is the native fallback; unset means no target entry. */
        TOptional<FBlendEntry> Blend;
    };

    const FLinkEntry* FindLink(TConstArrayView<FLinkEntry> Entries,
        FActionIdentity Target, FActionIdentity Previous, int32 SampledPhase);
    const FBlendEntry* FindBlend(TConstArrayView<FBlendEntry> Entries,
        int32 TargetMotion, const FMotionSample& Previous);
    TConstArrayView<FLinkEntry> GetLongSwordLinkEntries();
    TConstArrayView<FBlendEntry> GetLongSwordBlendEntries();

    /** uPlayer +0x2b0: layer flags 1/4, optionally the player's additional end path. */
    bool IsMotionEnded(uint32 LayerFlags, bool bUseAdditionalEnd, bool bAdditionalEnd);

    enum class ELinkStage : uint8 { Idle, Connector, Main };

    /** Caller supplies the actual native action identity, sampled phase and motion.
     * Do not substitute FSM ActionNo for native action ID or infer a motion from it.
     * UE asset/clock integration remains a separate adapter until qualified.
     */
    class FLinkExecution
    {
    public:
        FPlaybackRequest Begin(TConstArrayView<FLinkEntry> Links,
            TConstArrayView<FBlendEntry> Blends, FActionIdentity Target,
            FActionIdentity PreviousAction, int32 SampledPhase,
            int32 ResolvedMainMotion, const FMotionSample& PreviousMotion);
        /** Custom native action entry, e.g. cUpper always plays 119 before 107. */
        FPlaybackRequest BeginExplicitConnector(TConstArrayView<FBlendEntry> Blends,
            int32 Motion, int32 ResolvedMainMotion, const FMotionSample& PreviousMotion,
            FName Bank = FName(TEXT("w03_00")));
        /** One connector -> main commit, only after the actual animation-end predicate.
         * A stale callback or interruption must never start the pending main motion.
         */
        TOptional<FPlaybackRequest> Advance(TConstArrayView<FBlendEntry> Blends,
            uint32 Generation, uint32 LayerFlags, bool bUseAdditionalEnd,
            bool bAdditionalEnd, const FMotionSample& CurrentMotion);
        void Cancel();
        ELinkStage GetStage() const { return Stage; }
        uint32 GetGeneration() const { return Serial; }
        int32 GetConnectorMotion() const { return ConnectorMotion; }
        FName GetConnectorBank() const { return ConnectorBank; }
    private:
        ELinkStage Stage = ELinkStage::Idle;
        uint32 Serial = 0;
        int32 MainMotion = INDEX_NONE;
        int32 ConnectorMotion = INDEX_NONE;
        FName ConnectorBank = FName(TEXT("w03_00"));
    };
}
