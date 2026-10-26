#pragma once

#include "CoreMinimal.h"
#include "MHWILinkAnimation.h"

namespace MHWI::Native
{
    struct FSourceBinding
    {
        FActionIdentity Identity;
        FName Bank;
        int32 Motion;
        int32 Node;
    };
    struct FSourceWeaponKey { FName Bank; int32 Motion; float Frame; int32 Value; };
    struct FSourceTrigger { int32 Motion; float Frame; };
    struct FDirectBlendSettings
    {
        uint32 RequestFlags = 0;
        int32 PoseInterpolationFrames = 0;
    };
    /** Qualified direct bank12 / canonical bank0 requests. Future modes or
     * tree-controlled banks must be migrated before entering this adapter. */
    bool ResolveDirectBlendSettings(FName Bank, const FBlendEntry& Entry, FDirectBlendSettings& Out);
    TConstArrayView<FSourceBinding> GetSourceBindings();
    const FSourceBinding* GetSourceBinding(FActionIdentity Identity);
    TConstArrayView<FMotionInfo> GetCommonSourceMotions();
    TConstArrayView<FSourceWeaponKey> GetSourceWeaponKeys();
    TConstArrayView<FBlendEntry> GetSourceBlends(FName Bank);
    const FMotionInfo* GetSourceMotionInfo(FName Bank, int32 Motion);
    int32 GetSlingerMotion(FActionIdentity Identity, FActionIdentity Previous);
    float GetSlingerTriggerFrame(int32 Motion);
    int32 GetSlingerAction(int32 PreviousNode, int32 Direction);
    FName GetSlingerMove(int32 Action);
    int32 SlingerActionFromMove(FName Move);
}
