---
name: ue-build-log-triage
description: Diagnose Unreal Engine, UBT, UHT, MSVC, linker, editor-startup, PIE, and automation logs without flooding context. Use this skill whenever an IntroCpp build, project generation, editor launch, PIE smoke test, packaging run, or Unreal automation command fails or emits a large log.
compatibility: Requires Python 3. Full logs must remain available on disk.
---

# UE build log triage

Keep the complete command output in a log file. Give the model a bounded diagnostic slice first, while preserving a recovery path to the original evidence.

## First pass

Run:

```powershell
python .agents/skills/ue-build-log-triage/scripts/triage_ue_log.py "<log path>"
```

The script prints the file hash, line counts, matched error groups, bounded context, and the original path. It does not alter the log.

Start with the earliest causal error rather than the final generic failure. Distinguish UHT/reflection errors, C++ compile errors, linker errors, plugin-load errors, ensures/assertions, and gameplay test failures.

## Expand only when needed

Read the original log around an exact line number when:

- the slice begins inside a stack trace or nested exception;
- an error references an earlier warning, generated header, response file, or module;
- multiple targets interleave output;
- encoding damaged an identifier;
- the filtered result contains only a generic exit code;
- the task is security-sensitive or omission-sensitive.

Use `rg -n` for the exact symbol, error code, module, or first failure. Do not paste the whole log into the conversation.

## UE-specific diagnosis order

1. UHT/reflection and generated-code failures.
2. First compiler error in the first failing translation unit.
3. First unresolved external or duplicate symbol, with the owning module and `Build.cs` dependency.
4. Plugin descriptor, engine-version, or module-loading failures.
5. First ensure/assertion and its stack.
6. PIE or automation assertion with the preceding map/test context.

Warnings become primary evidence only when the build treats warnings as errors or the warning explains the failure. Preserve exit codes and distinguish a successful build with warnings from a failed command.

## Report

Return a short diagnosis containing the first causal error, affected target/module/file, likely cause, next focused check, and original log path. After a fix, rerun the smallest command that proves it, then inspect the new log rather than relying on the old slice.
