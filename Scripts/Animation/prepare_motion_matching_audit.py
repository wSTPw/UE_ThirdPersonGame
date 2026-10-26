"""Prepare read-only UE-MCP requests; never opens Unreal or executes requests.

The first pass deliberately requires no guessed skeleton or bone names. After
reading that result, supply the verified skeleton and bones for the second pass.
File existence is an inventory fact, never proof of skeleton/data compatibility.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANIMATION_FOLDER = "/Game/MyStuff/Model/Robot/SwordAnim"
BASELINE_NAMES = (
    "Idle_Seq_YBot",
    "Walk_Loop_F_0_Seq_YBot",
    "Run_Loop_F_0_Seq_YBot",
    "Run_Start_F_0_Seq_YBot",
    "Run_Stop_F_0_Seq_YBot",
    "Turn_180_R_Seq_YBot",
)


def read_request(method: str, **args: object) -> dict:
    return {"action": "call", "category": "animation", "method": method, "args": args}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skeleton-path", help="Verified /Game/... USkeleton path")
    parser.add_argument("--root-bone", help="Verified root bone; no default guessed")
    parser.add_argument("--foot-bones", nargs=2, metavar=("LEFT", "RIGHT"))
    parser.add_argument("--output", type=Path, help="Optional local JSON output")
    args = parser.parse_args()
    if args.skeleton_path and not args.skeleton_path.startswith("/Game/"):
        parser.error("--skeleton-path must be the verified /Game/... asset path")
    if (args.root_bone or args.foot_bones) and not args.skeleton_path:
        parser.error("Verify and supply --skeleton-path before requesting bone samples")

    folder = PROJECT_ROOT / "Content/MyStuff/Model/Robot/SwordAnim"
    file_names = sorted(path.stem for path in folder.glob("*.uasset"))
    baseline = [f"{ANIMATION_FOLDER}/{name}" for name in BASELINE_NAMES]
    missing = [name for name in BASELINE_NAMES if name not in file_names]
    requests = [
        read_request("read_sequence", assetPaths=baseline, fields=[
            "skeleton", "sequenceLength", "numFrames", "rootMotionEnabled", "notifies",
        ]),
        read_request("read_anim_blueprint", assetPath="/Game/MyStuff/Model/Robot/ABP_Move"),
        read_request("read_anim_graph", assetPath="/Game/MyStuff/Model/Robot/ABP_Move", graphName="AnimGraph"),
    ]
    if args.skeleton_path:
        requests.append(read_request("get_bone_transforms", skeletonPath=args.skeleton_path))
    if args.root_bone:
        requests.extend(read_request("read_bone_track", assetPath=path, boneName=args.root_bone)
                        for path in baseline)
    if args.foot_bones:
        requests.extend(read_request("measure_natural_speed", assetPath=path,
                                     footBones=args.foot_bones)
                        for path in baseline)

    result = {
        "status": "prepared_only_no_editor_queries_executed",
        "assetFolder": ANIMATION_FOLDER,
        "baselineMissingFiles": missing,
        "localLocomotionCandidateNames": [name for name in file_names
            if name.startswith(("Idle_", "Walk_", "Run_", "Turn_"))],
        "readOnlyRequests": requests,
        "gates": [
            "Read metadata skeleton first; get_bone_transforms must confirm names before track sampling.",
            "read_bone_track lacks a bone-existence check; identity samples for an unknown bone prove nothing.",
            "Three default root samples are triage only; inspect dense samples before classifying a trajectory.",
            "Root-motion disabled does not prove the source track lacks translation or rotation.",
            "PoseSearch default Pose channel uses foot_l/foot_r; explicitly author actual YBot bone channels.",
            "The bridge channel adders retain constructor defaults; read back and replace SampledBones/Samples arrays before indexing.",
            "Do not use add_motion_matching_node connectToOutput=true on the production AnimGraph: it replaces the final chain.",
            "No attack, Fireball or UseItemComplete gameplay notify may enter the locomotion database.",
        ],
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
