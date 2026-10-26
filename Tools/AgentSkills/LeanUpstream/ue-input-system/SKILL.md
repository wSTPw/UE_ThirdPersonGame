---
name: ue-input-system
description: Use for IntroCpp UE 5.8 Enhanced Input actions, mapping contexts, triggers, modifiers, bindings, priorities, UI input modes, or runtime rebinding. Start from actual project mappings and load detailed upstream APIs only when needed.
metadata:
  version: "2.0.0-introcpp-lean"
  engine: "5.8"
---

# Lean input route

Read `Docs/Systems/UI-Assets.md`, route to `ui-input`, and inspect the owning character or controller binding code.

Use UE-MCP to verify assigned InputAction and InputMappingContext assets. Preserve the distinction between gameplay input bindings and UI focus/input mode.

Read `UPSTREAM_SKILL.md` only when an exact UE 5.8 Enhanced Input API, trigger, modifier, priority, or rebinding contract is uncertain.
