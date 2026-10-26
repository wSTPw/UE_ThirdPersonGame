# IntroCpp Agent Skills

This directory stores the versionable source for project-specific skills and lean wrappers. Installed copies live under `.agents/skills/`, where Codex discovers them.

- `introcpp-context-router`: chooses a small documentation/source/asset slice from the project module manifest.
- `ue-build-log-triage`: extracts bounded diagnostics while preserving the complete Unreal log.
- `LeanUpstream/`: short active wrappers for selected UE 5.8 skills. Their installed folders retain the original upstream `SKILL.md` as `UPSTREAM_SKILL.md` for explicit, on-demand reading.

Do not expand the active wrappers with general UE reference material. Keeping detailed material behind a reference file prevents routine tasks from loading thousands of unnecessary tokens.
