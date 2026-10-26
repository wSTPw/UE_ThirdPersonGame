#pragma once

#include "CoreMinimal.h"
#include "CharacterActionTypes.generated.h"

UENUM(BlueprintType)
enum class ECharacterActionKind : uint8 { None, Melee, Cast, UseItem };

UENUM(BlueprintType)
enum class ECharacterActionPhase : uint8 { Idle, Windup, Active, Recovery };

UENUM(BlueprintType)
enum class ECharacterActionEndReason : uint8 { Completed, Cancelled, Interrupted, Failed, Dead, OwnerEnded };

UENUM(BlueprintType)
enum class ECharacterActionRequestStatus : uint8 { Started, Buffered, Rejected };

UENUM(BlueprintType)
enum class ECharacterActionFailure : uint8
{
    None, Busy, Dead, UIBlocked, Cooldown, InvalidSource, MissingAnimation,
    MissingEvent, InsufficientMana, SpawnFailed, NoEffect, NotReady
};

enum class ECharacterActionEvent : uint8 { MeleeHit, CastCommit, ItemCommit };

USTRUCT(BlueprintType)
struct FCharacterActionSnapshot
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) int64 RunId = 0;
    UPROPERTY(BlueprintReadOnly) ECharacterActionKind Kind = ECharacterActionKind::None;
    UPROPERTY(BlueprintReadOnly) ECharacterActionPhase Phase = ECharacterActionPhase::Idle;
    UPROPERTY(BlueprintReadOnly) int32 ComboIndex = 0;
    UPROPERTY(BlueprintReadOnly) int32 SegmentGeneration = 0;
    UPROPERTY(BlueprintReadOnly) bool bCommitted = false;
    UPROPERTY(BlueprintReadOnly) float MoveScale = 1.f;
    UPROPERTY(BlueprintReadOnly) bool bAllowJump = true;
};

USTRUCT(BlueprintType)
struct FCharacterActionRequestResult
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) ECharacterActionRequestStatus Status = ECharacterActionRequestStatus::Rejected;
    UPROPERTY(BlueprintReadOnly) ECharacterActionFailure Failure = ECharacterActionFailure::None;
    UPROPERTY(BlueprintReadOnly) int64 RunId = 0;
    bool IsAccepted() const { return Status != ECharacterActionRequestStatus::Rejected; }
};

// Native reservation: never treat an ItemID or a slot number as a unique source.
struct FActionItemReservation
{
    bool bQuickSlot = false;
    int32 SlotIndex = INDEX_NONE;
    FName ItemID;
    int32 Quantity = 0;
    uint64 Revision = 0;
};

// Legacy ItemAction bools report whether an effect requests consumption. A false
// result cannot prove that arbitrary Blueprint/native side effects did not occur.
struct FActionItemCommitResult
{
    bool bApplied = false;
    int32 ConsumedQuantity = 0;
    bool bPartial = false;
    bool IsCommitted() const { return ConsumedQuantity > 0; }
};
