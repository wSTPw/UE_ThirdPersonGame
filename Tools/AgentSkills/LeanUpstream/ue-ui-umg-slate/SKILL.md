---
name: ue-ui-umg-slate
description: Use for IntroCpp UE 5.8 UMG, Slate, widget bindings, inventory/status UI, drag-and-drop, UI delegates, focus, and Common UI. Read project widget contracts first; load detailed upstream patterns only when needed.
metadata:
  version: "2.0.0-introcpp-lean"
  engine: "5.8"
---

# Lean UI route

Read `Docs/Systems/UI-Assets.md` and the relevant UI entries in `Docs/Interfaces.md`. Inspect the matching widget source rather than the full UI directory.

Use UE-MCP to verify widget Blueprint parents, named bindings, animations, and defaults. Check delegate cleanup and `UFUNCTION()` requirements when changing bindings.

Read `UPSTREAM_SKILL.md` only for an exact UE 5.8 UMG, Slate, Common UI, MVVM, focus, or widget-lifecycle API question.
