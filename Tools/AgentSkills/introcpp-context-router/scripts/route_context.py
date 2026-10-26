#!/usr/bin/env python3
"""Select a small IntroCpp context slice from Docs/Reference/modules.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ALIASES = {
    "entry": "entry", "入口": "entry", "关卡": "entry", "gamemode": "entry",
    "item": "item-data", "物品": "item-data", "dataasset": "item-data",
    "inventory": "inventory", "背包": "inventory", "快捷栏": "inventory", "quickslot": "inventory",
    "attribute": "attributes", "属性": "attributes", "生命": "attributes", "mana": "attributes",
    "player": "player-combat", "玩家": "player-combat", "combat": "player-combat",
    "攻击": "player-combat", "连击": "player-combat",
    "enemy": "enemy-ai", "敌人": "enemy-ai", "statetree": "enemy-ai", "ai": "enemy-ai",
    "ui": "ui-input", "umg": "ui-input", "界面": "ui-input", "输入": "ui-input", "input": "ui-input",
    "event": "event-bus", "事件": "event-bus", "delegate": "event-bus",
    "模板": "template-variants", "shooter": "template-variants",
    "build": "editor-tooling", "编译": "editor-tooling", "构建": "editor-tooling",
    "plugin": "editor-tooling", "插件": "editor-tooling", "mcp": "editor-tooling",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_+-]+|[\u4e00-\u9fff]+", text)}


def main() -> int:
    if len(sys.argv) < 2 or not " ".join(sys.argv[1:]).strip():
        print("Usage: route_context.py <task description>", file=sys.stderr)
        return 2

    query = " ".join(sys.argv[1:]).strip()
    manifest_path = project_root() / "Docs" / "Reference" / "modules.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    modules = data.get("modules", [])
    query_lower = query.lower()
    query_tokens = tokens(query)
    alias_ids = {module_id for alias, module_id in ALIASES.items() if alias in query_lower}

    ranked = []
    for module in modules:
        searchable = " ".join(
            str(value)
            for key in ("id", "name", "document", "sources", "interface_ids", "asset_roots")
            for value in (module.get(key, []) if isinstance(module.get(key), list) else [module.get(key, "")])
        ).lower()
        score = 12 if module.get("id") in alias_ids else 0
        score += sum(1 for token in query_tokens if len(token) > 1 and token in searchable)
        if score:
            ranked.append((score, module))

    ranked.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    selected = [module for _, module in ranked[:3]]
    if not selected:
        selected = [module for module in modules if module.get("id") in {"entry", "editor-tooling"}]

    output = {
        "task": query,
        "manifest": "Docs/Reference/modules.json",
        "read_first": [
            {
                "id": module.get("id"),
                "document": module.get("document"),
                "sources": module.get("sources", []),
                "interface_ids": module.get("interface_ids", []),
                "asset_roots": module.get("asset_roots", []),
            }
            for module in selected
        ],
        "rule": "Read only routed documents first; expand when evidence crosses a module boundary.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
