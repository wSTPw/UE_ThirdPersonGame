#include "MHWINativeLinkMotion.h"
#include "MHWINativeLinkMotionData.inl"

namespace MHWI::Native
{
    TConstArrayView<FLinkEntry> GetLongSwordLinkEntries() { return MakeArrayView(LinkEntries); }
    TConstArrayView<FBlendEntry> GetLongSwordBlendEntries() { return MakeArrayView(BlendEntries); }
    const FLinkEntry* FindLink(TConstArrayView<FLinkEntry> Entries,
        FActionIdentity Target, FActionIdentity Previous, int32 SampledPhase)
    {
        // 14178412a..155: first exact identity/phase match. No Phase1 -> Phase0 fallback.
        for (const FLinkEntry& Entry : Entries)
            if (Entry.Motion >= 0 && Entry.Target == Target && Entry.Previous == Previous
                && Entry.Phase == SampledPhase)
                return &Entry;
        return nullptr;
    }

    const FBlendEntry* FindBlend(TConstArrayView<FBlendEntry> Entries,
        int32 TargetMotion, const FMotionSample& Previous)
    {
        // 141c007f0: keep serialized order, bank, source motion and frame threshold.
        // The threshold is NOT an exit timer; zero disables that filter.
        if (!FMath::IsFinite(Previous.Frame)) return nullptr;
        const FBlendEntry* Default = nullptr;
        for (const FBlendEntry& Entry : Entries)
        {
            if (Entry.TargetMotion != TargetMotion) continue;
            // 141c0091f starts at row 1; 141c00ab9..b14 falls back to row 0.
            // This is the serialized original default, never a fabricated zero row.
            if (!Default) { Default = &Entry; continue; }
            if (Entry.PreviousMotion == Previous.Motion
                && Entry.PreviousBank == Previous.Bank
                && !(Entry.PreviousFrameLimit > 0.f && Previous.Frame > Entry.PreviousFrameLimit))
                return &Entry;
        }
        return Default;
    }

    bool IsMotionEnded(uint32 LayerFlags, bool bUseAdditionalEnd, bool bAdditionalEnd)
    {
        return (LayerFlags & 5u) != 0u || (bUseAdditionalEnd && bAdditionalEnd);
    }

    static FPlaybackRequest Request(int32 Motion, TConstArrayView<FBlendEntry> Blends,
        const FMotionSample& Previous)
    {
        FPlaybackRequest Result;
        Result.Motion = Motion;
        if (const FBlendEntry* Entry = FindBlend(Blends, Motion, Previous)) Result.Blend = *Entry;
        return Result;
    }

    FPlaybackRequest FLinkExecution::Begin(TConstArrayView<FLinkEntry> Links,
        TConstArrayView<FBlendEntry> Blends, FActionIdentity Target,
        FActionIdentity PreviousAction, int32 SampledPhase,
        int32 ResolvedMainMotion, const FMotionSample& PreviousMotion)
    {
        Cancel();
        ConnectorBank = FName(TEXT("w03_00"));
        MainMotion = ResolvedMainMotion == 0xffff ? INDEX_NONE : ResolvedMainMotion;
        const FLinkEntry* Entry = FindLink(Links, Target, PreviousAction, SampledPhase);
        if (Entry)
        {
            ConnectorMotion = Entry->Motion & 0x1ff; // Native weapon bank request 0xc000 | motion.
            Stage = ELinkStage::Connector;
            return Request(ConnectorMotion, Blends, PreviousMotion);
        }
        Stage = MainMotion >= 0 ? ELinkStage::Main : ELinkStage::Idle;
        return Request(MainMotion, Blends, PreviousMotion);
    }

    TOptional<FPlaybackRequest> FLinkExecution::Advance(TConstArrayView<FBlendEntry> Blends,
        uint32 Generation, uint32 LayerFlags, bool bUseAdditionalEnd,
        bool bAdditionalEnd, const FMotionSample& CurrentMotion)
    {
        if (Generation != Serial || Stage != ELinkStage::Connector
            || CurrentMotion.Motion != ConnectorMotion || CurrentMotion.Bank != ConnectorBank
            || !IsMotionEnded(LayerFlags, bUseAdditionalEnd, bAdditionalEnd))
            return {};
        // Set state before publishing the request, making reentrant end delivery one-shot.
        Stage = MainMotion >= 0 ? ELinkStage::Main : ELinkStage::Idle;
        if (MainMotion < 0) return {};
        return Request(MainMotion, Blends, CurrentMotion);
    }

    FPlaybackRequest FLinkExecution::BeginExplicitConnector(TConstArrayView<FBlendEntry> Blends,
        int32 Motion, int32 ResolvedMainMotion, const FMotionSample& PreviousMotion, FName Bank)
    {
        Cancel();
        MainMotion = ResolvedMainMotion == 0xffff ? INDEX_NONE : ResolvedMainMotion;
        ConnectorMotion = Motion;
        ConnectorBank = Bank;
        Stage = ELinkStage::Connector;
        return Request(ConnectorMotion, Blends, PreviousMotion);
    }

    void FLinkExecution::Cancel()
    {
        ++Serial;
        Stage = ELinkStage::Idle;
        MainMotion = ConnectorMotion = INDEX_NONE;
    }
}
