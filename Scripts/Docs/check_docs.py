"""Validate local documentation links and the curated module manifest.

Standard library only. Does not compile C++, inspect assets, or validate heading anchors.
Run from any working directory: python <project>/Scripts/Docs/check_docs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\((?:<([^>]+)>|([^\s)]+))\)")
FENCES = re.compile(r"^\s*```[^\n]*\n.*?^\s*```\s*$", re.MULTILINE | re.DOTALL)


def main() -> int:
    errors: list[str] = []
    checked_links = 0
    pages = sorted((ROOT / "Docs").rglob("*.md"))
    pages += [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "Tools/ue-mcp/README.md"]
    for page in pages:
        source = FENCES.sub("", page.read_text(encoding="utf-8-sig"))
        for match in LINK.finditer(source):
            target = match.group(1) or match.group(2)
            parts = urlsplit(target)
            if parts.scheme or target.startswith(("#", "//")):
                continue
            if not parts.path:
                continue
            resolved = (page.parent / unquote(parts.path)).resolve()
            checked_links += 1
            if not resolved.is_relative_to(ROOT):
                errors.append(f"{page.relative_to(ROOT)}: link leaves repository: {target}")
            elif not resolved.exists():
                errors.append(f"{page.relative_to(ROOT)}: missing link target: {target}")

    manifest = json.loads((ROOT / "Docs/Reference/modules.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        errors.append("modules.json: unsupported schema_version")
    modules = manifest.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append("modules.json: modules must be a non-empty array")
        modules = []
    interfaces = (ROOT / "Docs/Interfaces.md").read_text(encoding="utf-8")
    known_ids: set[str] = set()
    for module in modules:
        module_id = module.get("id", "")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", module_id) or module_id in known_ids:
            errors.append(f"modules.json: invalid or duplicate module id: {module_id!r}")
        known_ids.add(module_id)
        for key in ("name", "document", "sources", "interface_ids", "asset_roots", "validation"):
            if key not in module:
                errors.append(f"{module_id}: missing {key}")
        for relative in [module.get("document", ""), *module.get("sources", []), *module.get("validation", [])]:
            resolved = (ROOT / relative).resolve()
            if not relative or not resolved.is_relative_to(ROOT) or not resolved.is_file():
                errors.append(f"{module_id}: missing or invalid repository file: {relative}")
        for interface_id in module.get("interface_ids", []):
            if not re.search(r"(?<![A-Z0-9-])" + re.escape(interface_id) + r"(?![A-Z0-9-])", interfaces):
                errors.append(f"{module_id}: undocumented interface id: {interface_id}")
        for asset in module.get("asset_roots", []):
            if not asset.startswith("/Game/"):
                errors.append(f"{module_id}: unexpected asset path: {asset}")

    snapshot = json.loads((ROOT / "Docs/Reference/editor-observations.json").read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != 1 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", snapshot.get("observed_on", "")):
        errors.append("editor-observations.json: invalid schema or observation date")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    print(f"PASS: {len(pages)} Markdown files, {checked_links} local links, {len(modules)} modules, and editor snapshot JSON.")
    print("Scope: file targets and manifest references only; no heading, C++ ABI, gameplay, or asset validation.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
