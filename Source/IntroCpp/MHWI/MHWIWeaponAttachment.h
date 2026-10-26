#pragma once

#include "CoreMinimal.h"

class USkeletalMeshComponent;

/** Existing Blueprint fitting, plus explicitly project-tuned transfer windows. */
struct INTROCPP_API FMHWIWeaponAttachmentSettings
{
    FName WeaponBone = TEXT("bone_012");
    FName ScabbardBone = TEXT("bone_002");
    FName SheathedWeaponBone = TEXT("bone_002");
    FName SpecialScabbardBone = TEXT("bone_008");
    FTransform WeaponRelativeTransform;
    FTransform ScabbardRelativeTransform;
    FTransform SheathedWeaponRelativeTransform;
    FTransform SpecialScabbardRelativeTransform;
    FTransform SpecialWeaponRelativeTransform;

    /** Opposite X directions in the delivered hunter's otherwise matching wrist frames. */
    FVector RightPalmPoint = FVector(-7.f, 2.f, 0.f);
    FVector LeftPalmPoint = FVector(7.f, 2.f, 0.f);
    FVector DrawnGripPoint = FVector(0.f, -12.f, 0.f);
    FVector SpecialGripPoint = FVector(0.f, -66.485203f, 0.f);
    FVector ScabbardMouthPoint = FVector(0.f, 21.f, 0.f);
    /** Source-pose contact minima are 25/52; these are fitting windows, not decoded mount events. */
    float DrawTransferStart = 10.f / 60.f;
    float DrawTransferEnd = 25.f / 60.f;
    float SheatheTransferStart = 40.f / 60.f;
    float SheatheTransferEnd = 52.f / 60.f;
    float SpecialInsertStart = 60.f / 60.f;
    float SpecialInsertEnd = 73.f / 60.f;
    /** Iai source internal weapon changes at 0/8; no original mount event is inferred. */
    float IaiTransferEnd = 8.f / 60.f;
    /** Project fitting for attacks entered with the blade still on the back. */
    float AttackDrawEnd = 10.f / 60.f;
    /** Approach the explicit sheathed internal state without waiting for action end. */
    float ReturnTransferSeconds = 12.f / 60.f;
    float HandOffBlendSeconds = 0.16f;
};

struct INTROCPP_API FMHWIWeaponAttachmentContext
{
    FName CurrentMove;
    float MontagePosition = 0.f;
    bool bSheathed = true;
    bool bSpecialSheathHeld = false;
    bool bMoveStartedSheathed = false;
    bool bUnsheathAtStart = false;
    /** Qualified only for a move that explicitly sheaths at end; -1 disables. */
    float ReturnToSheathTime = -1.f;
    uint32 ExecutionSerial = 0;
};

/**
 * Game-thread whole-equipment fitting, separate from source internal animation.
 * Owns no UObject pointers, timers, or delegates. Call after the hunter and weapon
 * pose refresh, including paused-hold and action-end paths. A zero-delta call
 * transfers parenting without advancing the handoff clock. Contact locks can
 * adjust the component origin to retain the animated material point in hand.
 */
struct INTROCPP_API FMHWIWeaponAttachmentRuntime
{
    void Update(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Weapon,
        USkeletalMeshComponent* Scabbard, const FMHWIWeaponAttachmentSettings& Settings,
        const FMHWIWeaponAttachmentContext& Context, float DeltaSeconds = 0.f);
    void Reset();
    /** Visual equipment state, independent of the action's gameplay sheathe flag. */
    bool IsBackMounted() const { return bHaveExecution && LastBackAmount >= 0.95f; }
    /** Project fitted material grip in Weapon component space, for game-thread IK goals. */
    static FVector AnimatedGripPoint(USkeletalMeshComponent* Weapon, const FVector& ReferencePoint);

private:
    struct FPiece
    {
        FName Socket;
        FTransform EntryRelative;
        float Elapsed = 0.f;
        uint32 ExecutionSerial = 0;
        uint8 Mode = 255;
        bool bInitialized = false;
    };
    FPiece WeaponState;
    FPiece ScabbardState;
    uint32 LastExecutionSerial = 0;
    bool bHaveExecution = false;
    bool bAttackFromBack = false;
    float LastBackAmount = 1.f;
    FVector LastGripPoint = FVector(0.f, -12.f, 0.f);
    FVector EntryGripPoint = FVector(0.f, -12.f, 0.f);
    float GripHandoffElapsed = 0.f;
    static void Apply(USkeletalMeshComponent* Hunter, USkeletalMeshComponent* Piece,
        FPiece& State, FName Socket, const FTransform& DesiredWorld, uint8 Mode,
        uint32 ExecutionSerial, float DeltaSeconds, float BlendSeconds, float SourceBlend = -1.f,
        const FVector* ContactPoint = nullptr, const FVector* ContactWorld = nullptr);
};
