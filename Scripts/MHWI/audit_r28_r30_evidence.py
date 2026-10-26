"""Read-only source audit for the remaining R28/R30 locomotion and IK evidence.

Reads the pinned local MHWI source extracts, prior archive fingerprint report,
and source rig bind. It never starts the game/editor or writes source assets.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import native_animation_source as animation_source


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved/MHWIRestoration/B18-20261026/r28-r30-evidence.json"
LOCOMOTION_IDS = (5, 6, 7, 8, 14, 15)
IK_CHAINS = {
    "larm": (6, 7, 8),
    "rarm": (10, 11, 12),
    "lfoot": (14, 15, 16),
    "rfoot": (18, 19, 20),
}
IK_FILES = (
    "hm.arm_mgr",
    "hm.leg_mgr",
    "hm.ikctrl",
    "hm_common.ctm",
    "larm.ik",
    "rarm.ik",
    "lfoot.ik",
    "rfoot.ik",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> dict:
    reader, _ = animation_source.native_modules()
    lmt_path = animation_source.SOURCES["w03_00"]
    bank = reader.read_lmt_file(lmt_path)
    actions = {action.header.id: action for action in bank.actions}
    lmt_digest = sha256(lmt_path)
    candidates = []
    for action_id in LOCOMOTION_IDS:
        action = actions[action_id]
        header = action.header
        candidates.append(
            {
                "motion": f"w03_00_{action_id:03}",
                "frame_count": header.frame_count,
                "duration_seconds_at_60fps": header.frame_count / 60.0,
                "loop_frame": header.loop_frame,
                "track_count": header.fcurve_count,
                "source_header_translation": list(header.translation[:3]),
                "source_joint_ids": sorted({track.header.bone_id for track in action.tracks}),
            }
        )

    manifest_path = ROOT / "ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json"
    animation_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    qualified = {row["clip"]: row for row in animation_manifest["clips"]}
    base_loops = (
        "w03_00_001",
        "w03_00_004",
        "co00_00_001",
        "co00_00_203",
        "co00_00_090",
    )
    existing_loops = []
    for clip in base_loops:
        row = qualified[clip]
        existing_loops.append(
            {
                "clip": clip,
                "frame_count": row["frame_count"],
                "duration_seconds": row["duration"],
                "loop_frame": row["loop_frame"],
                "eligible_for_runtime": row["eligible_for_runtime"],
                "source_and_fbx_checks_passed": bool(
                    row["source_verification"]["passed"]
                    and row["fbx_verification"]["passed"]
                    and row["bone_count"] == 225
                ),
            }
        )

    rig_path = ROOT / "ArtSource/ThirdParty/MHWLongSword/NativeFidelity/rig-bind.json"
    rig = json.loads(rig_path.read_text(encoding="utf-8"))
    rig_bones = rig["bones"]
    chain_rows = []
    for name, joint_ids in IK_CHAINS.items():
        bones = [f"bone_{joint_id:03}" for joint_id in joint_ids]
        chain_rows.append(
            {
                "resource": f"{name}.ik",
                "source_joint_indices": list(joint_ids),
                "rig_bones": [
                    {
                        "name": bone,
                        "parent": rig_bones[bone]["parent"],
                    }
                    for bone in bones
                ],
                "contiguous_parent_chain": all(
                    rig_bones[bones[index]]["parent"] == bones[index - 1]
                    for index in range(1, len(bones))
                ),
            }
        )

    ik_root = ROOT / "ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/common/ik"
    pin_path = ROOT / "Saved/MHWIRestoration/B17-20261026/native-parameter-fingerprint-verification.json"
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    verified = {row["path"]: row for row in pin["files"]}
    ik_files = []
    for filename in IK_FILES:
        path = ik_root / filename
        relative = f"hm/common/ik/{filename}"
        row = verified[relative]
        digest = sha256(path)
        ik_files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "matches_pinned_archive": bool(
                    row["manifest_match"]
                    and row["archive_sha256"] == digest
                    and row["bytes"] == path.stat().st_size
                ),
                "nativePC_override_sha256": row["nativePC_override_sha256"],
            }
        )

    result = {
        "schema_version": 1,
        "scope": "read-only R28/R30 source evidence; no original-game, UE, or PIE runtime observation",
        "r28": {
            "source_lmt": {
                "path": lmt_path.relative_to(ROOT).as_posix(),
                "bytes": lmt_path.stat().st_size,
                "sha256": lmt_digest,
            },
            "candidate_motion_headers": candidates,
            "already_qualified_base_loops": existing_loops,
            "candidate_role_mapping_confirmed": False,
        },
        "r30": {
            "archive_verification": {
                "exe_sha256": pin["exe_sha256"],
                "verified_archive_resources": pin["matched"],
                "resource_count": pin["count"],
            },
            "resources": ik_files,
            "chains_mapped_to_rig_bind": chain_rows,
            "solver_coordinate_and_ctm_semantics_decoded": False,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": OUT.relative_to(ROOT).as_posix(),
        "r28_candidates": len(candidates),
        "r30_resources": len(ik_files),
        "all_r30_resources_match_archive": all(row["matches_pinned_archive"] for row in ik_files),
        "all_r30_chains_map_to_contiguous_rig_bones": all(row["contiguous_parent_chain"] for row in chain_rows),
    }, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
