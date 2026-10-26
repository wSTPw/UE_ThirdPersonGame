#include "MHWILinkAnimation.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "MHWILinkRuntimeData.inl"

namespace MHWI::Native
{
    int32 GetMoveNode(FName Move, bool bSheathedRoll)
    {
        if (Move == FName(TEXT("WalkOnSlash"))) return 41;
        if (Move == FName(TEXT("RollRight"))) return 14;
        if (Move == FName(TEXT("RollBack"))) return 15;
        if (Move == FName(TEXT("RollLeft"))) return 16;
        if (Move == FName(TEXT("Roll")) && bSheathedRoll) return INDEX_NONE;
        for (const FMoveNode& Row : MoveNodes) if (Row.Move == Move) return Row.Node;
        return INDEX_NONE;
    }

    const FMotionInfo* GetMotionInfo(int32 Motion)
    {
        for (const FMotionInfo& Row : MotionInfos) if (Row.Motion == Motion) return &Row;
        return nullptr;
    }
    int32 GetNativeMainMotion(int32 Node)
    {
        if (Node == 41) return 101; // 141800376: source action7, 115 -> 101.
        for (const FMainMotionBinding& Row : MainMotionBindings)
            if (Row.Node == Node) return Row.Motion;
        return INDEX_NONE;
    }
    int32 GetTimelineMotion(FName Move, int32 SpiritLevel, int32 ActualBodyMotion)
    {
        // Existing 309/310/311 montages share the qualified 308 bone animation.
        // Restore their separate original TIML identity; never sample red as 308.
        if (Move == FName(TEXT("IaiSpiritSlash")))
        {
            if (SpiritLevel == 1) Move = FName(TEXT("IaiSpiritSlashWhite"));
            else if (SpiritLevel == 2) Move = FName(TEXT("IaiSpiritSlashYellow"));
            else if (SpiritLevel == 3) Move = FName(TEXT("IaiSpiritSlashRed"));
        }
        if (ActualBodyMotion == 308)
            for (const FMoveTimeline& Row : MoveTimelines)
                if (Row.Move == Move) return Row.Motion;
        return ActualBodyMotion;
    }
    TConstArrayView<int32> GetConnectorMotions() { return MakeArrayView(ConnectorMotions); }
    TConstArrayView<FConnectorWeaponKey> GetConnectorWeaponKeys() { return MakeArrayView(ConnectorWeaponKeys); }

    int32 SampleLinkPhase(const FMotionSample& Motion)
    {
        // TIML binding resets +10c before evaluation. 1424a7440 advances on >= key;
        // transition 1 -> 1424a8580 -> 1424a8770 copies the current integer key.
        int32 Value = 0;
        for (const FPhaseKey& Key : PhaseKeys)
            if (Key.Bank == Motion.Bank && Key.Motion == Motion.Motion && Key.Frame <= Motion.Frame) Value = Key.Value;
        return Value;
    }

    uint32 ForwardEndFlags(float Frame, float Advance, int32 Endpoint)
    {
        if (!FMath::IsFinite(Frame) || !FMath::IsFinite(Advance) || Advance < 0.f || Endpoint < 0) return 0;
        // 14224e340..47b: flags1 predicts next source step, flags4 marks current
        // boundary. RIP 143506af4 is 0.0005, NOT a half-frame rounding constant.
        const int32 Current = FMath::TruncToInt(Frame + 0.0005f);
        const int32 Next = FMath::TruncToInt(Frame + Advance + 0.0005f);
        return (Next >= Endpoint ? 1u : 0u) | (Current >= Endpoint ? 4u : 0u);
    }

    bool ResolveNodeLink(int32 TargetNode, int32 PreviousNode, int32 Phase, const FLinkEntry*& OutEntry)
    {
        OutEntry = nullptr;
        FActionIdentity Target;
        bool bTargetFound = false;
        for (const FNodeIdentity& Row : NodeIdentities)
            if (Row.Node == TargetNode) { Target = Row.Identity; bTargetFound = true; break; }
        if (!bTargetFound || PreviousNode == INDEX_NONE) return true;
        bool bSampled = false;
        for (const FNodeIdentity& Row : NodeIdentities)
        {
            if (Row.Node != PreviousNode) continue;
            const FLinkEntry* Match = FindLink(GetLongSwordLinkEntries(), Target, Row.Identity, Phase);
            if (bSampled && ((Match == nullptr) != (OutEntry == nullptr)
                || (Match && (Match->Motion != OutEntry->Motion || Match->Node != OutEntry->Node))))
            { OutEntry = nullptr; return false; }
            OutEntry = Match;
            bSampled = true;
        }
        return true;
    }

    bool ResolveIdentityLink(int32 TargetNode, FActionIdentity Previous, int32 Phase,
        const FLinkEntry*& OutEntry)
    {
        OutEntry = nullptr;
        for (const FNodeIdentity& Row : NodeIdentities)
            if (Row.Node == TargetNode)
            {
                OutEntry = FindLink(GetLongSwordLinkEntries(), Row.Identity, Previous, Phase);
                return true;
            }
        return true; // Unknown destination has no LinkMotion table, as in ResolveNodeLink.
    }

    bool IsKnownSourceIdentity(FActionIdentity Identity)
    {
        for (const FNodeIdentity& Row : NodeIdentities) if (Row.Identity == Identity) return true;
        for (const FLinkEntry& Row : GetLongSwordLinkEntries())
            if (Row.Previous == Identity) return true;
        return false;
    }

    TArray<FActionIdentity> GetNodeIdentities(int32 Node)
    {
        TArray<FActionIdentity> Result;
        for (const FNodeIdentity& Row : NodeIdentities)
            if (Row.Node == Node) Result.Add(Row.Identity);
        return Result;
    }

    FActionEntryPlan ResolveActionEntry(int32 TargetNode, FActionIdentity Target,
        FActionIdentity PreviousAction, bool bPreviousDrawn, int32 MainMotion,
        const FMotionSample& PreviousMotion)
    {
        FActionEntryPlan Result;
        FMotionSample Current = PreviousMotion;
        bool bRequested = false;
        auto Play = [&](int32 Motion)
        {
            Result.BlendPrevious = Current;
            Result.First = {};
            Result.First.Motion = Motion;
            if (const FBlendEntry* Blend = FindBlend(GetLongSwordBlendEntries(), Motion, Current))
                Result.First.Blend = *Blend;
            Current = {FName(TEXT("w03_00")), Motion,
                float(Result.First.Blend.IsSet() ? Result.First.Blend->StartFrame : 0)};
            bRequested = true;
        };
        auto GenericEntry = [&](int32 GenericMain)
        {
            // The Phase is sampled AFTER any explicit pre-request rebinds TIML.
            Result.Link = FindLink(GetLongSwordLinkEntries(), Target, PreviousAction, SampleLinkPhase(Current));
            if (Result.Link) { Play(Result.Link->Motion); return 0; }
            if (GenericMain >= 0) { Play(GenericMain); return 1; }
            return 3; // 1417896f8: no main and no ending motion; keep current carrier.
        };
        const bool bWeapon = PreviousAction.Group == 3;
        const int32 Previous = PreviousAction.Action;
        const bool bCommonStandingStep = PreviousAction.Group == 1
            && (Previous == 103 || Previous == 110 || Previous == 115);
        if (TargetNode == 3 || TargetNode == 41)
        {
            Play(TargetNode == 3 ? 119 : 115);
            Result.bFollowMain = true;
        }
        else if (TargetNode == 1)
        {
            // 1417fe610: +76aa is the prior +76a8 draw state; +628c/6290
            // are prior identity, +6274/6278 current target identity. The action's
            // generic +30 stays ffff; custom state +cd0 owns the final 104 commit.
            const bool bDrawEntry = !bPreviousDrawn || (bWeapon && (Previous == 6 || Previous == 9));
            bool bMainAlreadyPlaying = false;
            if (bDrawEntry)
                Play(bCommonStandingStep ? 152 : (Target.Group == 3 && Target.Action == 12 ? 113 : 116));
            else if (!bWeapon) { Play(104); bMainAlreadyPlaying = true; }
            else if (Previous == 1 || Previous == 65 || Previous == 66) Play(132);
            else if (Previous >= 18 && Previous <= 22) Play(130);
            else if (Previous == 72 || Previous == 80) Play(126);
            else if (!((Previous >= 30 && Previous <= 32) || (Previous >= 55 && Previous <= 63) || Previous == 101))
            { Play(104); bMainAlreadyPlaying = true; }
            GenericEntry(INDEX_NONE);
            // Post-entry override is deliberately after the generic table lookup.
            if (!bDrawEntry && bWeapon && (Previous == 57 || Previous == 60 || Previous == 63)) Play(132);
            Result.bFollowMain = !bMainAlreadyPlaying;
        }
        else if (TargetNode == 11)
        {
            // 1417fed20 / 141800190. A missing P1 match can play 101 in the
            // generic call then replace it with 151 in the SAME entry.
            if (!bPreviousDrawn && bCommonStandingStep)
            { Play(151); Result.bFollowMain = true; }
            else
            {
                const int32 Stage = GenericEntry(MainMotion);
                if (bPreviousDrawn && bWeapon
                    && ((Previous >= 30 && Previous <= 32) || (Previous >= 55 && Previous <= 63)))
                {
                    if (Stage != 0) Play(151);
                    Result.bFollowMain = true;
                }
                else Result.bFollowMain = bPreviousDrawn && Stage == 0;
            }
        }
        else Result.bFollowMain = GenericEntry(MainMotion) == 0;
        Result.bContinuePrevious = !bRequested;
        if (!bRequested)
        {
            Result.First.Motion = PreviousMotion.Motion;
            Result.BlendPrevious = PreviousMotion;
        }
        return Result;
    }

    static bool SequenceMotion(const UAnimSequenceBase* Sequence, FMotionSample& Out)
    {
        if (!Sequence) return false;
        const FString Name = Sequence->GetName();
        FString Prefix(TEXT("A_w03_00_"));
        FName Bank(TEXT("w03_00"));
        if (Name.StartsWith(TEXT("A_co00_00_")))
        { Prefix = TEXT("A_co00_00_"); Bank = FName(TEXT("co00_00")); }
        if (!Name.StartsWith(Prefix)) return false;
        const FString Suffix = Name.Mid(Prefix.Len());
        if (Suffix.IsEmpty() || !Suffix.IsNumeric()) return false;
        Out.Bank = Bank;
        Out.Motion = FCString::Atoi(*Suffix);
        return Bank == FName(TEXT("co00_00")) || GetMotionInfo(Out.Motion) != nullptr;
    }

    bool ReadSequenceMotion(const UAnimSequenceBase* Sequence, float Position, FMotionSample& Out)
    {
        if (!Sequence || !FMath::IsFinite(Position) || Position < 0.f || Position > Sequence->GetPlayLength()
            || !SequenceMotion(Sequence, Out)) return false;
        Out.Frame = Position * 60.f;
        return true;
    }

    bool ReadMotion(const UAnimMontage* Montage, float Position, FMotionSample& Out)
    {
        if (!Montage || Montage->SlotAnimTracks.Num() != 1 || !FMath::IsFinite(Position)
            || Position < 0.f || Position > Montage->GetPlayLength()) return false;
        const FAnimSegment* Segment = Montage->SlotAnimTracks[0].AnimTrack.GetSegmentAtTime(Position);
        if (!Segment || Segment->GetValidPlayRate() <= 0.f || Segment->LoopingCount != 1
            || !SequenceMotion(Segment->GetAnimReference(), Out)) return false;
        Out.Frame = (Segment->AnimStartTime + (Position - Segment->StartPos) * Segment->GetValidPlayRate()) * 60.f;
        return FMath::IsFinite(Out.Frame);
    }

    bool MotionPosition(const UAnimMontage* Montage, FName Bank, int32 Motion,
        float SourceFrame, float& OutPosition)
    {
        if (!Montage || Montage->SlotAnimTracks.Num() != 1
            || !FMath::IsFinite(SourceFrame) || SourceFrame < 0.f) return false;
        bool bFound = false;
        for (const FAnimSegment& Segment : Montage->SlotAnimTracks[0].AnimTrack.AnimSegments)
        {
            FMotionSample Sample;
            if (!SequenceMotion(Segment.GetAnimReference(), Sample)
                || Sample.Bank != Bank || Sample.Motion != Motion) continue;
            if (bFound || Segment.GetValidPlayRate() <= 0.f || Segment.LoopingCount != 1
                || SourceFrame / 60.f < Segment.AnimStartTime
                || SourceFrame / 60.f >= Segment.AnimEndTime) return false;
            OutPosition = Segment.StartPos + (SourceFrame / 60.f - Segment.AnimStartTime)
                / Segment.GetValidPlayRate();
            bFound = FMath::IsFinite(OutPosition);
        }
        return bFound;
    }

    bool ReadMainMotion(const UAnimMontage* Montage, int32& OutMotion)
    {
        if (!Montage || Montage->SlotAnimTracks.Num() != 1
            || Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.IsEmpty()) return false;
        const FAnimSegment& Segment = Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.Last();
        FMotionSample Sample;
        if (!SequenceMotion(Segment.GetAnimReference(), Sample) || Sample.Bank != FName(TEXT("w03_00"))
            || Segment.GetValidPlayRate() <= 0.f
            || Segment.LoopingCount != 1) return false;
        // Only the existing 129 + 101 composite is supported as a multi-segment main.
        // Never silently reinterpret an arbitrary Montage's last segment as the action.
        if (Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.Num() != 1)
        {
            const auto& Segments = Montage->SlotAnimTracks[0].AnimTrack.AnimSegments;
            FMotionSample Prefix;
            if (Segments.Num() != 2 || !SequenceMotion(Segments[0].GetAnimReference(), Prefix)
                || Prefix.Motion != 129 || Sample.Motion != 101) return false;
        }
        OutMotion = Sample.Motion;
        return true;
    }

    bool MainPosition(const UAnimMontage* Montage, int32 Motion, int32 SourceFrame, float& OutPosition)
    {
        int32 ActualMain = INDEX_NONE;
        if (!ReadMainMotion(Montage, ActualMain) || ActualMain != Motion || SourceFrame < 0) return false;
        return MotionPosition(Montage, FName(TEXT("w03_00")), Motion, float(SourceFrame), OutPosition);
    }
}
