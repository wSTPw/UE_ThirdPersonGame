#include "MHWIRathianThkExecutor.h"

#include "Templates/UnrealTemplate.h"

namespace
{
bool IsSourceHash(const FString& Hash)
{
    if (Hash.Len() != 64) return false;
    for (const TCHAR C : Hash) if (!FChar::IsHexDigit(C)) return false;
    return true;
}
}

bool FMHWIRathianThkExecutor::Start(const FMHWIRathianThkProgram& Program,
    uint64 ActionRunId, bool bRequireSourceSemantics, FString& OutReason)
{
    OutReason.Reset();
    if (bEvaluating || bActive)
    {
        OutReason = TEXT("Finish or cancel the current THK execution before starting another.");
        return false;
    }
    if (ActionRunId == 0 || ActionRunId <= LastStartedRunId)
    {
        OutReason = TEXT("THK run identity must be nonzero and monotonically newer.");
        return false;
    }
    if (!IsSourceHash(Program.SourceSha256) || Program.SourcePath.IsEmpty()
        || Program.Instructions.Num() == 0 || Program.Instructions.Num() > 100000
        || !Program.Instructions.Contains(Program.Entry))
    {
        OutReason = TEXT("Missing pinned source identity or entry instruction.");
        return false;
    }
    if (bRequireSourceSemantics && !Program.bNativeControlFlowVerified)
    {
        OutReason = TEXT("THK control-flow semantics lack native consumer qualification.");
        return false;
    }
    const auto HasTarget = [&Program](const FString& Key) { return Program.Instructions.Contains(Key); };
    for (const auto& Entry : Program.Instructions)
    {
        const FMHWIRathianThkInstruction& Instruction = Entry.Value;
        if (Instruction.Key != Entry.Key || Instruction.SourceEvidence.IsEmpty())
        {
            OutReason = TEXT("Instruction key/source offset evidence is missing or inconsistent.");
            return false;
        }
        switch (Instruction.Op)
        {
        case EMHWIRathianThkOp::Jump:
            if (!HasTarget(Instruction.Next)) { OutReason = TEXT("Jump target is missing."); return false; }
            break;
        case EMHWIRathianThkOp::Call:
            if (!HasTarget(Instruction.CallTarget) || !HasTarget(Instruction.Next))
            { OutReason = TEXT("Call or return target is missing."); return false; }
            break;
        case EMHWIRathianThkOp::Branch:
            if (!HasTarget(Instruction.Next) || !HasTarget(Instruction.Otherwise))
            { OutReason = TEXT("Branch target is missing."); return false; }
            break;
        case EMHWIRathianThkOp::YieldAction:
            if (Instruction.NativeActionId < 0 || !HasTarget(Instruction.Next))
            { OutReason = TEXT("Action identity or continuation is missing."); return false; }
            break;
        case EMHWIRathianThkOp::Return:
        case EMHWIRathianThkOp::Stop:
            break;
        default:
            OutReason = TEXT("Unsupported normal-form opcode.");
            return false;
        }
    }
    ActiveProgram = Program;
    ActiveRunId = ActionRunId;
    LastStartedRunId = ActionRunId;
    bStrict = bRequireSourceSemantics;
    bRunQualified = Program.bNativeControlFlowVerified;
    ReturnStack.Reset();
    ProgramCounter = Program.Entry;
    bActive = true;
    bWaiting = false;
    return true;
}

FMHWIRathianThkDecision FMHWIRathianThkExecutor::End(EMHWIRathianThkResult Result,
    const FString& Reason, const TArray<FString>& Visited)
{
    FMHWIRathianThkDecision Decision;
    Decision.Result = Result;
    Decision.ActionRunId = ActiveRunId;
    Decision.InstructionKey = ProgramCounter;
    Decision.Reason = Reason;
    Decision.VisitedInstructions = Visited;
    Decision.bSourceSemanticsQualified = bRunQualified;
    bActive = false;
    bWaiting = false;
    ReturnStack.Reset();
    return Decision;
}

FMHWIRathianThkDecision FMHWIRathianThkExecutor::RunUntilAction(
    const FQueryResolver& Query, int32 InstructionBudget)
{
    FMHWIRathianThkDecision Immediate;
    Immediate.ActionRunId = ActiveRunId;
    if (bEvaluating) { Immediate.Result = EMHWIRathianThkResult::ReentrantCall; return Immediate; }
    if (!bActive) { Immediate.Result = EMHWIRathianThkResult::StaleRun; return Immediate; }
    if (bWaiting) { Immediate.Result = EMHWIRathianThkResult::WaitingForAction; return Immediate; }
    if (InstructionBudget < 1 || InstructionBudget > 100000)
        return End(EMHWIRathianThkResult::InstructionBudgetExceeded, TEXT("Invalid instruction budget."), {});

    TGuardValue<bool> EvaluationGuard(bEvaluating, true);
    const uint64 ExpectedRun = ActiveRunId;
    TArray<FString> Visited;
    for (int32 Step = 0; Step < InstructionBudget; ++Step)
    {
        const FMHWIRathianThkInstruction* Found = ActiveProgram.Instructions.Find(ProgramCounter);
        if (!Found) return End(EMHWIRathianThkResult::InvalidProgram, TEXT("Program counter is missing."), Visited);
        const FMHWIRathianThkInstruction Instruction = *Found;
        Visited.Add(Instruction.Key);
        bRunQualified &= Instruction.bNativeConsumerVerified;
        if (bStrict && !Instruction.bNativeConsumerVerified)
            return End(EMHWIRathianThkResult::Unqualified, TEXT("Instruction semantics lack consumer evidence."), Visited);

        switch (Instruction.Op)
        {
        case EMHWIRathianThkOp::Jump:
            ProgramCounter = Instruction.Next;
            break;
        case EMHWIRathianThkOp::Call:
            if (ReturnStack.Num() >= 128)
                return End(EMHWIRathianThkResult::InstructionBudgetExceeded, TEXT("Call depth exceeded."), Visited);
            ReturnStack.Add(Instruction.Next);
            ProgramCounter = Instruction.CallTarget;
            break;
        case EMHWIRathianThkOp::Return:
            if (ReturnStack.IsEmpty())
                return End(EMHWIRathianThkResult::Finished, TEXT("Returned from the entry call."), Visited);
            ProgramCounter = ReturnStack.Pop(EAllowShrinking::No);
            break;
        case EMHWIRathianThkOp::Branch:
        {
            const FMHWIRathianThkQueryResult Reply = Query
                ? Query(Instruction.FunctionType, Instruction.Parameter1, Instruction.Parameter2)
                : FMHWIRathianThkQueryResult();
            if (!bActive || ActiveRunId != ExpectedRun)
                return End(EMHWIRathianThkResult::StaleRun, TEXT("THK execution was cancelled during a query."), Visited);
            if (!Reply.bAvailable)
                return End(EMHWIRathianThkResult::UnknownCondition, TEXT("Condition is unavailable; no branch was taken."), Visited);
            bRunQualified &= Reply.bNativeConsumerVerified && !Reply.Evidence.IsEmpty();
            if (bStrict && (!Reply.bNativeConsumerVerified || Reply.Evidence.IsEmpty()))
                return End(EMHWIRathianThkResult::Unqualified, TEXT("Condition reply lacks consumer evidence."), Visited);
            ProgramCounter = Reply.Value ? Instruction.Next : Instruction.Otherwise;
            break;
        }
        case EMHWIRathianThkOp::YieldAction:
        {
            FMHWIRathianThkDecision Decision;
            Decision.Result = EMHWIRathianThkResult::YieldedAction;
            Decision.ActionRunId = ActiveRunId;
            Decision.NativeActionId = Instruction.NativeActionId;
            Decision.InstructionKey = Instruction.Key;
            Decision.VisitedInstructions = Visited;
            Decision.bSourceSemanticsQualified = bRunQualified;
            ProgramCounter = Instruction.Next;
            bWaiting = true;
            return Decision;
        }
        case EMHWIRathianThkOp::Stop:
            return End(EMHWIRathianThkResult::Finished, TEXT("Source program stopped."), Visited);
        default:
            return End(EMHWIRathianThkResult::InvalidProgram, TEXT("Unsupported normal-form opcode."), Visited);
        }
    }
    return End(EMHWIRathianThkResult::InstructionBudgetExceeded,
        TEXT("Instruction budget exceeded; no action request was emitted."), Visited);
}

bool FMHWIRathianThkExecutor::ResumeAfterAction(uint64 ActionRunId)
{
    if (bEvaluating || !bActive || !bWaiting || ActionRunId != ActiveRunId) return false;
    bWaiting = false;
    return true;
}

void FMHWIRathianThkExecutor::Cancel(uint64 ActionRunId)
{
    if (ActionRunId == 0 || ActionRunId != ActiveRunId) return;
    bActive = false;
    bWaiting = false;
    ReturnStack.Reset();
}
