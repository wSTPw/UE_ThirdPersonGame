---
name: ue-module-build-system
description: Use for IntroCpp UE 5.8 Build.cs, Target.cs, uproject/uplugin, modules, plugins, include order, unresolved symbols, UBT/UHT, project generation, or Live Coding failures. Triage the project log first; load full upstream build guidance only when needed.
metadata:
  version: "2.0.0-introcpp-lean"
  engine: "5.8"
---

# Lean build route

Read `Docs/Development.md` and, for upgrade-specific history, `Docs/UE58-Upgrade.md`. Run `ue-build-log-triage` on the full saved log before opening broad source or engine trees.

Start with the first UHT, compiler, or linker cause. Inspect the affected module's `Build.cs`, target file, descriptor, and exact symbol ownership.

Read `UPSTREAM_SKILL.md` only when an exact UE 5.8 module-rule, target-rule, plugin-loading, dependency, IWYU, or generated-code contract is uncertain.
