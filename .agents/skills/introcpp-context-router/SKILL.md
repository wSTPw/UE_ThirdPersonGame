---
name: introcpp-context-router
description: Route work in the IntroCpp Unreal Engine 5.8 project to the smallest relevant documentation, source, and asset context. Use this skill before investigating or changing gameplay, inventory, items, combat, AI, StateTree, UI, input, events, maps, Blueprints, DataAssets, build configuration, plugins, or UE-MCP integration in this repository.
compatibility: Requires Python 3 and the project Docs/Reference/modules.json manifest.
---

# IntroCpp context router

Reduce repeated repository exploration while keeping enough evidence to make correct changes.

## Route first

From the repository root, run:

```powershell
python .agents/skills/introcpp-context-router/scripts/route_context.py "<user task>"
```

The script returns at most three likely modules and their current documents, source roots, interfaces, and asset roots. Treat this as a routing result, not proof of runtime behavior.

## Read in layers

1. Read `Docs/README.md` only when the task boundary or document status is unclear.
2. Read the returned system document or documents. Avoid opening all documents.
3. Use `rg` against the returned source roots for the named symbol, class, delegate, config key, or error. Read the smallest useful code range.
4. Read `Docs/Interfaces.md` only for returned interface IDs or when a public contract may change.
5. Read `Docs/Known-Issues.md` only when the task overlaps an existing risk or observed limitation.
6. Use UE-MCP only for facts that live in assets or the running editor: Blueprint parents and defaults, DataAsset values, map actors, widget bindings, montage/notifies, or live PIE state.

## Expand deliberately

Expand beyond the routed context when direct evidence shows a dependency outside it, compilation names another module, or a Blueprint/config reference crosses the boundary. State the reason before broadening a search.

Do not infer current behavior from old design documents. `Source/` is the UBT source tree; `C++ Source/` is a reference copy. Preserve unrelated user changes and follow the root `AGENTS.md` for documentation and verification.

## Efficient completion

- For documentation-only work, run the documentation checker and `git diff --check`.
- For C++ or reflection changes, compile the smallest relevant target, then broaden only if the result warrants it.
- For asset behavior, verify exact `/Game/...` paths and use a focused UE-MCP read or PIE check.
- Report the files changed, evidence obtained, checks actually run, and anything still unverified. Do not reproduce long logs or whole source files.
