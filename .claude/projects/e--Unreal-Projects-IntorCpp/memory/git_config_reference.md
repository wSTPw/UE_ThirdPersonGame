---
name: git-config-reference
description: Git LFS tracking rules and .gitignore patterns for this UE5 project
metadata:
  type: reference
---

# Git Configuration Reference

## Remote
- Repo: `wSTPw/UE_ThirdPersonGame` on GitHub
- Branch: `master` (tracks `origin/master`)
- Auth: PAT-based

## Git LFS (via .gitattributes)
LFS tracks the following UE5 binary/asset file types:
- `.uasset` / `.uassets` — UE5 assets
- `.umap` — UE5 maps
- `.fbx` / `.obj` — 3D models
- `.wav` / `.mp3` — Audio
- `.tga` / `.psd` / `.exr` — Textures / source images
- `.mp4` / `.webm` — Video
- `.zip` / `.pak` — Archives

All with: `filter=lfs diff=lfs merge=lfs -text`
LFS locksverify: false

## .gitignore
Covers these categories:
- **Build artifacts:** Binaries/, DerivedDataCache/, Intermediate/, Saved/
- **IDE:** .vscode/, .vs/, *.sln, *.suo, *.xcodeproj, *.xcworkspace
- **UE5 auto-gen:** __ExternalActors__/, __ExternalObjects__/, *.Build.cs.xml
- **OS junk:** Thumbs.db, .DS_Store, Desktop.ini

## Gaps (not yet in .gitignore)
- `.agents/` — Claude Code agent worktrees
- `.claude/` — Claude Code project data
- `skills-lock.json` — Claude Code skills manifest
