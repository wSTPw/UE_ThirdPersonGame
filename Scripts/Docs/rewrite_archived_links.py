"""Rewrite links pointing at archived docs to their new locations.

Run after moving docs into Docs/Archive. Only touches files under Docs/
(excluding Docs/Archive) and Tools/ue-mcp/README.md.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "Docs"
ARCHIVE = DOCS / "Archive"
LINK = re.compile(r"(?<!!)\[([^\]\n]+)\]\((?:<([^>]+)>|([^\s)]+))\)")


def find_in_archive(name: str) -> Path | None:
    hits = [p for p in ARCHIVE.rglob(name) if p.is_file()]
    return hits[0] if len(hits) == 1 else None


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "Scripts/Docs/check_docs.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    errors = [l for l in (proc.stdout or "").splitlines() if l.startswith("ERROR:")]
    missing: dict[Path, set[str]] = {}
    for line in errors:
        m = re.match(r"ERROR: (.+?): missing link target: (.+)$", line)
        if not m:
            continue
        page = ROOT / m.group(1).replace("\\", "/")
        missing.setdefault(page, set()).add(m.group(2))

    changed_files = 0
    changed_links = 0
    unresolved: list[str] = []

    for page, targets in missing.items():
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8-sig")
        original = text
        for target in targets:
            resolved = (page.parent / target).resolve()
            found = find_in_archive(resolved.name)
            if not found:
                unresolved.append(f"{page.relative_to(ROOT)} -> {target}")
                continue
            rel = _relpath(found, page.parent)            # replace both plain and angle-bracket forms
            for old in (f"]({target})", f"](<{target}>)"):
                if old in text:
                    new = f"]({rel})" if not old.startswith("](<") else f"](<{rel}>)"
                    changed_links += text.count(old)
                    text = text.replace(old, new)
        if text != original:
            page.write_text(text, encoding="utf-8-sig")
            changed_files += 1

    print(f"rewrote {changed_links} links in {changed_files} files")
    if unresolved:
        print(f"unresolved ({len(unresolved)}):")
        for item in unresolved:
            print("  ", item)
    return 0


def _relpath(target: Path, start: Path) -> str:
    import os

    return Path(os.path.relpath(target, start)).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
