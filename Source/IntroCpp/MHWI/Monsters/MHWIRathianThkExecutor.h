#pragma once

#include "CoreMinimal.h"

/** Narrow normal form compiled from pinned THK bytes; it is not a general THK VM. */
enum class EMHWIRathianThkOp : uint8 { Jump, Call, Return, Branch, YieldAction, Stop };

struct INTROCPP_API FMHWIRathianThkInstruction
{
    FString Key;
    EMHWIRathianThkOp Op = EMHWIRathianThkOp::Stop;
    FString Next;
    FString Otherwise;
    FString CallTarget;
    int32 FunctionType = 0;
    int32 Parameter1 = 0;
    int32 Parameter2 = 0;
    int32 NativeActionId = INDEX_NONE;
    FString SourceEvidence;
    bool bNativeConsumerVerified = false;
};

struct INTROCPP_API FMHWIRathianThkProgram
{
    FString SourceSha256;
    FString SourcePath;
    FString Entry;
    bool bNativeControlFlowVerified = false;
    TMap<FString, FMHWIRathianThkInstruction> Instructions;
};

struct INTROCPP_API FMHWIRathianThkQueryResult
{
    bool bAvailable = false;
    bool Value = false;
    bool bNativeConsumerVerified = false;
    FString Evidence;
};

enum class EMHWIRathianThkResult : uint8
{
    YieldedAction, Finished, UnknownCondition, Unqualified, InvalidProgram,
    InstructionBudgetExceeded, WaitingForAction, StaleRun, ReentrantCall
};

struct INTROCPP_API FMHWIRathianThkDecision
{
    EMHWIRathianThkResult Result = EMHWIRathianThkResult::InvalidProgram;
    int32 NativeActionId = INDEX_NONE;
    uint64 ActionRunId = 0;
    FString InstructionKey;
    FString Reason;
    TArray<FString> VisitedInstructions;
    bool bSourceSemanticsQualified = false;
};

/**
 * Explicit call/return and branch execution with source evidence and a bounded step count.
 * Missing condition data aborts; it never silently chooses the false branch.
 * An action yield remains pending until acknowledged, preventing duplicate requests.
 */
class INTROCPP_API FMHWIRathianThkExecutor
{
public:
    using FQueryResolver = TFunction<FMHWIRathianThkQueryResult(int32, int32, int32)>;

    bool Start(const FMHWIRathianThkProgram& Program, uint64 ActionRunId,
        bool bRequireSourceSemantics, FString& OutReason);
    FMHWIRathianThkDecision RunUntilAction(const FQueryResolver& Query, int32 InstructionBudget = 256);
    bool ResumeAfterAction(uint64 ActionRunId);
    void Cancel(uint64 ActionRunId);

    bool IsActive() const { return bActive; }
    bool IsWaitingForAction() const { return bWaiting; }
    uint64 GetActionRunId() const { return ActiveRunId; }

private:
    FMHWIRathianThkProgram ActiveProgram;
    FString ProgramCounter;
    TArray<FString> ReturnStack;
    uint64 ActiveRunId = 0;
    uint64 LastStartedRunId = 0;
    bool bActive = false;
    bool bWaiting = false;
    bool bStrict = true;
    bool bEvaluating = false;
    bool bRunQualified = false;

    FMHWIRathianThkDecision End(EMHWIRathianThkResult Result,
        const FString& Reason, const TArray<FString>& Visited);
};
