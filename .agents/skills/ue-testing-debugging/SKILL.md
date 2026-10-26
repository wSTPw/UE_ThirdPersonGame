---
name: ue-testing-debugging
description: Use for IntroCpp UE 5.8 tests, UE_LOG, ensure/assert diagnosis, PIE smoke tests, automation, Unreal Insights, profiling, debug drawing, or console variables. Keep evidence bounded and load detailed upstream test APIs only when needed.
metadata:
  version: "2.0.0-introcpp-lean"
  engine: "5.8"
---

# Lean testing route

Read `Docs/Development.md` and choose verification proportional to the change. Use `ue-build-log-triage` for large logs and preserve the full original log on disk.

Distinguish historical evidence from checks run in the current task. Prefer the smallest compile, PIE, MCP, or automation check that proves the behavior.

Read `UPSTREAM_SKILL.md` only for exact UE 5.8 automation macros, CQTest, logging, Insights, stats, visual logger, or profiling APIs.
