#include "MHWINativeSources.h"
#include "MHWIR06SourceData.inl"

namespace MHWI::Native
{
    bool ResolveDirectBlendSettings(FName Bank, const FBlendEntry& Entry, FDirectBlendSettings& Out)
    {
        Out = {};
        const bool bWeapon = Bank == FName(TEXT("w03_00"));
        const bool bCommon = Bank == FName(TEXT("co00_00"))
            && Entry.TargetMotion >= 70 && Entry.TargetMotion <= 72;
        if ((!bWeapon && !bCommon) || (bWeapon && Entry.One0 != 1)
            || (bCommon && Entry.One0 != 0)) return false;
        // 141c01624..667. Neither qualified bank has a MotionTree node here;
        // 142255820 therefore injects no envelope/curve request bits100/200.
        Out.RequestFlags = Entry.One0 == 1 ? 2u : 1u;
        Out.PoseInterpolationFrames = FMath::Max(0, Entry.InterpolationPoint);
        return true;
    }

    TConstArrayView<FSourceBinding> GetSourceBindings() { return MakeArrayView(SourceBindings); }
    const FSourceBinding* GetSourceBinding(FActionIdentity Identity)
    {
        for (const FSourceBinding& Row : SourceBindings) if (Row.Identity == Identity) return &Row;
        return nullptr;
    }
    TConstArrayView<FMotionInfo> GetCommonSourceMotions() { return MakeArrayView(CommonSourceMotions); }
    TConstArrayView<FSourceWeaponKey> GetSourceWeaponKeys() { return MakeArrayView(SourceWeaponKeys); }
    TConstArrayView<FBlendEntry> GetSourceBlends(FName Bank)
    {
        if (Bank == FName(TEXT("co00_00"))) return MakeArrayView(CommonSourceBlends);
        return GetLongSwordBlendEntries();
    }
    const FMotionInfo* GetSourceMotionInfo(FName Bank, int32 Motion)
    {
        if (Bank == FName(TEXT("w03_00"))) return GetMotionInfo(Motion);
        if (Bank == FName(TEXT("co00_00")))
            for (const FMotionInfo& Row : CommonSourceMotions) if (Row.Motion == Motion) return &Row;
        return nullptr;
    }
    int32 GetSlingerMotion(FActionIdentity Identity, FActionIdentity Previous)
    {
        const FSourceBinding* Binding = GetSourceBinding(Identity);
        if (!Binding) return INDEX_NONE;
        if (Identity.Group == 3 && Identity.Action >= 107 && Identity.Action <= 109 && Previous.Group == 3)
        {
            const int32 Direction = Identity.Action == 107 ? 0 : (Identity.Action == 108 ? 2 : 1);
            if (Previous.Action == 70) return 347 + Direction;
            if (Previous.Action == 78) return 332 + Direction;
        }
        return Binding->Motion;
    }
    float GetSlingerTriggerFrame(int32 Motion)
    {
        for (const FSourceTrigger& Row : SlingerTriggers) if (Row.Motion == Motion) return Row.Frame;
        return -1.f;
    }
    int32 GetSlingerAction(int32 PreviousNode, int32 Direction)
    {
        int32 Base = INDEX_NONE;
        switch (PreviousNode)
        {
        case 1: case 22: Base = 104; break;
        case 6: case 12: case 25: case 51: Base = 107; break;
        case 2: case 49: Base = 110; break;
        default: return INDEX_NONE;
        }
        return Base + FMath::Clamp(Direction, 0, 2); // F, L, R native action order.
    }
    FName GetSlingerMove(int32 Action)
    {
        return Action >= 104 && Action <= 112 ? FName(*FString::Printf(TEXT("SlingerBurst%d"), Action)) : NAME_None;
    }
    int32 SlingerActionFromMove(FName Move)
    {
        for (int32 Action = 104; Action <= 112; ++Action) if (Move == GetSlingerMove(Action)) return Action;
        return INDEX_NONE;
    }
}
