#!/usr/bin/env python3
"""Read-only join of Long Sword collision TIML tracks and wp03.col references.

The report preserves raw collision flag keys and does not claim that the
collision geometry has been mapped to a particular bone or world-space shape.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Scripts/MHWI"))
sys.path.insert(0, str(ROOT / "Tools/MHW"))

import extract_moveset_mapping as moveset  # noqa: E402
import native_reference_basics as basics  # noqa: E402

LMT = ROOT / "ArtSource/ThirdParty/MHWLongSword/nativePC/hm/wp/wp03/mot/w03_00/w03_00.lmt"
ORIGINAL_COL = ROOT / "ArtSource/ThirdParty/MHWLongSword/nativePC/hm/wp/wp03/collision/wp03.col"
PROJECT_OVERLAY_COL = ROOT / "ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp/wp03/collision/wp03.col"
B17_CAPTURED_COL = ROOT / "Saved/MHWIRestoration/B17-20261026/active-nativePC/hm/wp/wp03/collision/wp03.col"
EXPECTED_LMT_SHA256 = "2406ee8f61fe7ba21008f200881be6d339c93af07a9ff7ada9260f0c58a8c42b"
# 输出到已跟踪的 Tools/MHW/：Saved/ 被 .gitignore 整目录排除，写在那里会静默丢失版本记录。
DEFAULT_OUTPUT = ROOT / "Tools/MHW/weapon-hit-volume-evidence.json"
DEFAULT_GAME_ROOT = Path(r"F:\PCprogram\Steam\steamapps\common\Monster Hunter World")
GEOMETRY_INNER_FORMAT = "<BBffffhhffffffHIhffffH"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_collision_at(path: Path) -> dict:
    """Use the pinned parser while making its displayed path relative to path.parent."""
    old_root = basics.ROOT
    try:
        basics.ROOT = path.parent
        return basics.read_collision(path)
    finally:
        basics.ROOT = old_root


def normalized_references(parsed: dict) -> list[list[dict]]:
    return [[{"name": ref["name"], "geometry": ref["geometry"], "move": ref["move"],
              "timeline_uid": ref["timeline_uid"]} for ref in row["names"]]
            for row in parsed["records"]]


def normalized_fields(parsed: dict) -> list[dict]:
    return [{name: item["value"] for name, item in row["fields"].items()}
            for row in parsed["records"]]


def parse_geometry_table(path: Path) -> dict:
    """Read CLND/CLGM block boundaries from the pinned community .col template."""
    import struct

    raw = path.read_bytes()
    node_tag = raw.find(b"CLND")
    attack_tag = raw.find(b"ATK\0")
    if node_tag < 0 or attack_tag < 0:
        raise ValueError("Qualified CLND/ATK tags not found")
    param_count = struct.unpack_from("<I", raw, node_tag + 8)[0]
    param_type = struct.unpack_from("<I", raw, node_tag + 12)[0]
    unk1 = raw[node_tag + 16]
    cursor = node_tag + 17
    records = []
    for geometry_index in range(param_count):
        if raw[cursor + 4:cursor + 8] != b"CLGM":
            raise ValueError(f"Expected CLGM at geometry index {geometry_index}")
        inner_count = struct.unpack_from("<I", raw, cursor + 12)[0]
        inner_start = cursor + 16
        inner_rows = []
        for inner_index in range(inner_count):
            values = struct.unpack_from(GEOMETRY_INNER_FORMAT, raw,
                                         inner_start + inner_index * struct.calcsize(GEOMETRY_INNER_FORMAT))
            inner_rows.append({
                "index": inner_index,
                "flags_raw": [values[0], values[1]],
                "attack_range_template_field": values[2],
                "float_fields_4_to_6_raw": list(values[3:6]),
                "short_fields_7_to_8_raw": list(values[6:8]),
                "float_fields_9_to_14_raw": list(values[8:14]),
                "integer_fields_15_to_17_raw": list(values[14:17]),
                "float_fields_18_to_21_raw": list(values[17:21]),
                "field_22_raw": values[21],
            })
        trailer_start = inner_start + inner_count * struct.calcsize(GEOMETRY_INNER_FORMAT)
        trailer_length = 27 + (28 if param_type == 2 else 0)
        records.append({
            "geometry_index": geometry_index,
            "inner_param_count": inner_count,
            "inner_params": inner_rows,
            "trailing_unknown_bytes_hex": raw[trailer_start:trailer_start + trailer_length].hex(),
        })
        cursor = trailer_start + trailer_length
    if cursor + 7 != attack_tag:
        raise ValueError("CLND/CLGM geometry table does not end at ATK tag")
    return {
        "clnd_geometry_param_count": param_count,
        "clnd_geometry_param_type_raw": param_type,
        "clnd_unk1_raw": unk1,
        "geometry_records": records,
        "trailing_clnd_bytes_hex": raw[cursor:cursor + 3].hex(),
        "blocks_end_at_attack_table": True,
    }


def overlay_comparison(original: dict, overlay_path: Path) -> dict:
    overlay = parse_collision_at(overlay_path)
    original_values = normalized_fields(original)
    overlay_values = normalized_fields(overlay)
    changed_fields: Counter[str] = Counter()
    changed_byte_ranges: set[int] = set()

    layout = json.loads(basics.LAYOUT.read_text(encoding="utf-8"))
    widths = {field["name"]: __import__("struct").calcsize(
        "<" + basics.FORMATS[field["type"]]) for field in layout["fields"]}
    for index, (before, after) in enumerate(zip(original["records"], overlay["records"])):
        for field_name, original_item in before["fields"].items():
            if original_item["value"] != after["fields"][field_name]["value"]:
                changed_fields[field_name] += 1
                offset = original_item["offset"]
                changed_byte_ranges.update(range(offset, offset + widths[field_name]))

    original_bytes = ORIGINAL_COL.read_bytes()
    overlay_bytes = overlay_path.read_bytes()
    differing_offsets = [index for index, pair in enumerate(zip(original_bytes, overlay_bytes))
                         if pair[0] != pair[1]]
    return {
        "path": str(overlay_path),
        "bytes": len(overlay_bytes),
        "sha256": sha256(overlay_path),
        "matches_pinned_archive": sha256(overlay_path) == original["sha256"],
        "matches_repository_NativeParameters_source_copy": sha256(overlay_path) == sha256(PROJECT_OVERLAY_COL),
        "matches_B17_captured_install_override": (
            sha256(overlay_path) == sha256(B17_CAPTURED_COL) if B17_CAPTURED_COL.is_file() else None
        ),
        "same_geometry_and_timeline_references": normalized_references(original) == normalized_references(overlay),
        "changed_attack_fields_record_counts": dict(sorted(changed_fields.items())),
        "all_changed_bytes_belong_to_changed_attack_fields": (
            len(original_bytes) == len(overlay_bytes)
            and all(offset in changed_byte_ranges for offset in differing_offsets)
        ),
        "differing_byte_count": len(differing_offsets),
    }


def build_report(game_root: Path | None) -> dict:
    pin = basics.load_sources()
    pinned_col = pin["files"]["hm/wp/wp03/collision/wp03.col"]
    lmt_hash = sha256(LMT)
    if lmt_hash != EXPECTED_LMT_SHA256:
        raise ValueError("Pinned w03_00.lmt source fingerprint changed")

    collision = basics.read_collision(ORIGINAL_COL)
    if collision["sha256"] != pinned_col["sha256"]:
        raise ValueError("wp03.col does not match native-reference-sources.json")

    refs_by_uid: dict[int, list[dict]] = defaultdict(list)
    all_refs = []
    for row in collision["records"]:
        for ref in row["names"]:
            item = {
                "attack_record": row["index"],
                "geometry": ref["geometry"],
                "move": ref["move"],
                "timeline_uid": ref["timeline_uid"],
                "motion_value": row["fields"]["Motion_Value"]["value"],
            }
            refs_by_uid[ref["timeline_uid"]].append(item)
            all_refs.append(item)

    parsed_events = moveset.lmt_events(LMT)
    geometry_table = parse_geometry_table(ORIGINAL_COL)
    source_moves = json.loads((ROOT / "Scripts/MHWI/moveset_mapping.json").read_text(encoding="utf-8"))
    project_labels = {definition["clip"]: name for name, definition in source_moves["moves"].items()}
    joined_tracks = []
    for motion_name, entry in sorted(parsed_events.items()):
        for group in entry["groups"]:
            if group["hash"] != 956269290:  # CollisionTimelineObject
                continue
            tracks = {track["name"]: track["frames"] for track in group["tracks"]}
            node_keys = tracks.get("NodeID[0]", [])
            flag_keys = tracks.get("mFlag", [])
            bank_keys = tracks.get("Bank[0]", [])
            node_ids = sorted({int(value) for _, value in node_keys})
            spans = moveset.intervals(flag_keys, entry["source_frame_count"]) if flag_keys else []
            matches = [ref for node_id in node_ids for ref in refs_by_uid.get(node_id, [])]
            joined_tracks.append({
                "lmt_motion": motion_name,
                "project_move_label": project_labels.get(motion_name),
                "project_label_status": source_moves["moves"].get(project_labels.get(motion_name), {}).get("mapping_status"),
                "source_frame_count": entry["source_frame_count"],
                "bank_raw_keys": bank_keys,
                "node_id_raw_keys": node_keys,
                "mFlag_raw_keys": flag_keys,
                "mFlag_bit0_set_spans": spans,
                "matched_wp03_col_rows": matches,
            })

    matched_count = sum(bool(track["matched_wp03_col_rows"]) for track in joined_tracks)
    result = {
        "status": "read_only_source_file_join_not_runtime_collision_validation",
        "sources": {
            "wp03_col_archive_copy": {"path": ORIGINAL_COL.relative_to(ROOT).as_posix(),
                                      "bytes": collision["bytes"] if "bytes" in collision else ORIGINAL_COL.stat().st_size,
                                      "sha256": collision["sha256"], "attack_records": collision["count"]},
            "w03_00_lmt": {"path": LMT.relative_to(ROOT).as_posix(), "bytes": LMT.stat().st_size,
                           "sha256": lmt_hash, "motion_entries": len(parsed_events)},
            "repository_NativeParameters_source_copy": {
                "path": PROJECT_OVERLAY_COL.relative_to(ROOT).as_posix(),
                "bytes": PROJECT_OVERLAY_COL.stat().st_size,
                "sha256": sha256(PROJECT_OVERLAY_COL),
            },
        },
        "join_summary": {
            "collision_timeline_motion_tracks": len(joined_tracks),
            "tracks_matching_wp03_col_timeline_uid": matched_count,
            "all_tracks_match": matched_count == len(joined_tracks),
            "mapped_geometry_ids": sorted({ref["geometry"] for ref in all_refs if ref["geometry"] >= 0}),
            "geometry_record_count": len(geometry_table["geometry_records"]),
            "mapped_header_references": len(all_refs),
            "mapped_attack_records": len({ref["attack_record"] for ref in all_refs}),
        },
        "example": next((track for track in joined_tracks if track["lmt_motion"] == "w03_00_101"), None),
        "geometry_table": geometry_table,
        "tracks": joined_tracks,
        "interpretation_limits": [
            "TIML group/field names and raw keys establish a source collision timeline track; the game runtime consumer is not dynamically observed.",
            "wp03.col geometry indices and UIDs join to those tracks, but CLND/CLGM geometry records are not decoded to exact primitives, bone parents, or local/world transforms.",
            "A geometry index does not establish triangle-mesh collision or exact visible blade contact.",
            "Monster part/hitzone selection and the full downstream damage consumer remain unresolved.",
        ],
    }

    if game_root is not None:
        game_col = game_root / "nativePC/hm/wp/wp03/collision/wp03.col"
        if game_col.is_file():
            result["installed_game_override"] = overlay_comparison(collision, game_col)
        else:
            result["installed_game_override"] = {"path": str(game_col), "present": False}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT,
                        help="Optional MHW install to read its nativePC wp03.col override")
    parser.add_argument("--no-game-root", action="store_true",
                        help="Do not inspect an installed nativePC override")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(None if args.no_game_root else args.game_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output.relative_to(ROOT).as_posix(), **report["join_summary"],
                      "installed_override": report.get("installed_game_override", {}).get("sha256")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
