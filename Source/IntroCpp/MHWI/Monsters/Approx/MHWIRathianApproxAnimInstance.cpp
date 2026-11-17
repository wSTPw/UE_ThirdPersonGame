#include "MHWIRathianApproxAnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNode_SequencePlayer.h"
#include "AnimNodes/AnimNode_TwoWayBlend.h"
#include "AnimNodes/AnimNode_Slot.h"
#include "Animation/AnimSequence.h"

namespace
{
    struct FMHWIRathianApproxAnimProxy final : FAnimInstanceProxy
    {
        explicit FMHWIRathianApproxAnimProxy(UAnimInstance* Instance)
            : FAnimInstanceProxy(Instance)
        {
            IdleWalkBlend.A.SetLinkNode(&IdleNode);
            IdleWalkBlend.B.SetLinkNode(&WalkNode);
            WalkRunBlend.A.SetLinkNode(&IdleWalkBlend);
            WalkRunBlend.B.SetLinkNode(&RunNode);
            RootSlot.Source.SetLinkNode(&WalkRunBlend);
            RootSlot.SlotName = TEXT("DefaultSlot");
            RootSlot.bAlwaysUpdateSourcePose = true;
            IdleNode.SetLoopAnimation(true);
            WalkNode.SetLoopAnimation(true);
            RunNode.SetLoopAnimation(true);
        }

        virtual FAnimNode_Base* GetCustomRootNode() override { return &RootSlot; }
        virtual void GetCustomNodes(TArray<FAnimNode_Base*>& OutNodes) override
        {
            OutNodes.Add(&IdleNode);
            OutNodes.Add(&WalkNode);
            OutNodes.Add(&RunNode);
            OutNodes.Add(&IdleWalkBlend);
            OutNodes.Add(&WalkRunBlend);
            OutNodes.Add(&RootSlot);
        }

        void SetSequences(UAnimSequence* Idle, UAnimSequence* Walk, UAnimSequence* Run)
        {
            check(IsInGameThread());
            IdleNode.SetSequence(Idle);
            WalkNode.SetSequence(Walk ? Walk : Idle);
            RunNode.SetSequence(Run ? Run : (Walk ? Walk : Idle));
        }
        void SetBlend(float Speed)
        {
            check(IsInGameThread());
            const float Clamped = FMath::Clamp(Speed, 0.f, 1.f);
            IdleWalkBlend.Alpha = FMath::Clamp(Clamped * 2.f, 0.f, 1.f);
            WalkRunBlend.Alpha = FMath::Clamp((Clamped - 0.5f) * 2.f, 0.f, 1.f);
        }
        void SetDeath(UAnimSequence* Death)
        {
            check(IsInGameThread());
            if (Death)
            {
                IdleNode.SetSequence(Death);
                WalkNode.SetSequence(Death);
                RunNode.SetSequence(Death);
                IdleNode.SetAccumulatedTime(0.f);
                WalkNode.SetAccumulatedTime(0.f);
                RunNode.SetAccumulatedTime(0.f);
                IdleNode.SetStartPosition(0.f);
                WalkNode.SetStartPosition(0.f);
                RunNode.SetStartPosition(0.f);
                IdleNode.SetLoopAnimation(false);
                WalkNode.SetLoopAnimation(false);
                RunNode.SetLoopAnimation(false);
                SetBlend(0.f);
            }
        }

        FAnimNode_SequencePlayer_Standalone IdleNode;
        FAnimNode_SequencePlayer_Standalone WalkNode;
        FAnimNode_SequencePlayer_Standalone RunNode;
        FAnimNode_TwoWayBlend IdleWalkBlend;
        FAnimNode_TwoWayBlend WalkRunBlend;
        FAnimNode_Slot RootSlot;
    };
}

UMHWIRathianApproxAnimInstance::UMHWIRathianApproxAnimInstance() {}

FAnimInstanceProxy* UMHWIRathianApproxAnimInstance::CreateAnimInstanceProxy()
{
    return new FMHWIRathianApproxAnimProxy(this);
}

void UMHWIRathianApproxAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy)
{
    delete static_cast<FMHWIRathianApproxAnimProxy*>(InProxy);
}

void UMHWIRathianApproxAnimInstance::ConfigureLocomotion(UAnimSequence* Idle, UAnimSequence* Walk, UAnimSequence* Run)
{
    check(IsInGameThread());
    IdleSequence = Idle;
    WalkSequence = Walk;
    RunSequence = Run;
    FMHWIRathianApproxAnimProxy& Proxy = GetProxyOnGameThread<FMHWIRathianApproxAnimProxy>();
    Proxy.SetSequences(Idle, Walk, Run);
}

void UMHWIRathianApproxAnimInstance::SetLocomotionBlend(float NormalizedSpeed, float DeltaSeconds)
{
    check(IsInGameThread());
    SmoothedSpeedAlpha = FMath::FInterpTo(SmoothedSpeedAlpha, FMath::Clamp(NormalizedSpeed, 0.f, 1.f), FMath::Clamp(DeltaSeconds, 0.f, 0.1f), 8.f);
    GetProxyOnGameThread<FMHWIRathianApproxAnimProxy>().SetBlend(SmoothedSpeedAlpha);
}
void UMHWIRathianApproxAnimInstance::SetDeathSequence(UAnimSequence* Death)
{
    check(IsInGameThread());
    DeathSequence = Death;
    GetProxyOnGameThread<FMHWIRathianApproxAnimProxy>().SetDeath(Death);
}
