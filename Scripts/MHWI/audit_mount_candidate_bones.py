"""Read-only test: which hunter bone is the weapon really rigid against?

For a candidate parent bone B, the right palm expressed in B's space must describe
one fixed point whenever the hand is on the weapon. Sampling two different clips
(002 draw, 003 sheathe) therefore gives a bone-agnostic test: the bone whose palm
trajectories come closest to intersecting is the bone the weapon is rigid against.
No mount offset is assumed and nothing is authored.

Run headless:
  UnrealEditor-Cmd <project>.uproject -run=pythonscript -script=<this> -unattended -nullrhi -nosound
Writes Saved/MHWIRestoration/B21-20261028/mount-candidate-bones.json only.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import unreal

CANDIDATES = [
    'bone_000', 'bone_001', 'bone_002', 'bone_003', 'bone_004',
    'bone_005', 'bone_006', 'bone_007', 'bone_008',
    'bone_009', 'bone_010', 'bone_011', 'bone_012',
    'bone_249', 'bone_251', 'bone_507',
]
RIGHT_PALM = (-7.0, 2.0, 0.0)
GRIP_LOCAL = (0.0, -12.0, 0.0)
CLIPS = {2: '/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_002',
         3: '/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_003',
         110: '/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_110'}
# Only the frames in which the weapon is still/again on the back. The drawn-idle
# tail of 002 and the drawn-idle head of 003 are the same pose, so an unrestricted
# search matches them trivially (0.00 cm) for every bone and proves nothing.
WINDOWS = {2: (0, 28), 3: (40, 66), 110: (95, 116)}


def quat_matrix(q) -> list[list[float]]:
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def local_point(bone, point) -> list[float]:
    """point (world) expressed in the bone's local frame; bone is a sampled dict."""
    rot = quat_matrix(bone['quat'])
    loc = bone['loc']
    d = [point[0] - loc[0], point[1] - loc[1], point[2] - loc[2]]
    return [sum(rot[k][i] * d[k] for k in range(3)) for i in range(3)]  # R^T d


def dist(a, b) -> float:
    return math.dist(a, b)


def sample(sequence, bones, lib, options, stride=1):
    end = int(round(sequence.get_play_length() * 60))
    rows = []
    for frame in range(0, end + 1, stride):
        pose = lib.get_anim_pose_at_time(sequence, frame / 60.0, options)
        world = {b: lib.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD) for b in bones}
        palm = world['bone_012'].transform_location(unreal.Vector(*RIGHT_PALM))
        row = {'frame': frame, 'palm': list(palm.to_tuple()), 'bones': {}}
        for b in bones:
            t = world[b]
            row['bones'][b] = {'loc': list(t.translation.to_tuple()),
                               'quat': [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w]}
        rows.append(row)
    return rows


def main() -> int:
    root = Path(unreal.Paths.project_dir())
    lib = unreal.AnimPoseExtensions
    options = unreal.AnimPoseEvaluationOptions(
        extract_root_motion=True, incorporate_root_motion_into_pose=False)
    fit = json.loads((root / 'Scripts/MHWI/attachment_fit.json').read_text(encoding='utf-8'))
    out = root / 'Saved/MHWIRestoration/B21-20261028'
    out.mkdir(parents=True, exist_ok=True)

    samples = {}
    for index, path in CLIPS.items():
        seq = unreal.load_asset(path)
        assert isinstance(seq, unreal.AnimSequence), path
        samples[index] = sample(seq, CANDIDATES, lib, options)
        unreal.log(f'[mount] sampled {seq.get_name()} frames={len(samples[index])}')

    def tracks(index, bone):
        lo, hi = WINDOWS[index]
        rows = [r for r in samples[index] if lo <= r['frame'] <= hi]
        return [(r['frame'], local_point(r['bones'][bone], r['palm'])) for r in rows]

    rows_out = []
    for bone in CANDIDATES:
        a = tracks(2, bone)
        b = tracks(3, bone)
        best = None
        for fa, pa in a:
            for fb, pb in b:
                d = dist(pa, pb)
                if best is None or d < best['distance_cm']:
                    best = {'distance_cm': d, 'frame_002': fa, 'frame_003': fb,
                            'point_002': pa, 'point_003': pb}
        rows_out.append({'bone': bone, 'best_match': best})
    rows_out.sort(key=lambda r: r['best_match']['distance_cm'])

    # Where the current fit puts the grip, in each of the top bones' space.
    fit_t = fit['transforms']['scabbard_relative_transform']
    handed = []
    for entry in rows_out[:5]:
        bone = entry['bone']
        rq = unreal.Rotator(pitch=fit_t['rotation'][0], yaw=fit_t['rotation'][1],
                            roll=fit_t['rotation'][2]).quaternion()
        rot = quat_matrix([rq.x, rq.y, rq.z, rq.w])
        grip = [GRIP_LOCAL[i] * fit_t['scale'][i] for i in range(3)]
        grip_world_local = [fit_t['location'][i] + sum(rot[i][k] * grip[k] for k in range(3))
                            for i in range(3)]
        handed.append({'bone': bone, 'fitted_grip_in_bone': grip_world_local,
                       'fit_vs_best_cm': dist(grip_world_local, entry['best_match']['point_002'])})

    report = {
        'schema_version': 1,
        'status': 'read_only_pose_sampling',
        'question': 'which bone is the weapon rigid against; no offset assumed',
        'right_palm_reference': RIGHT_PALM,
        'grip_local': GRIP_LOCAL,
        'method': 'minimise |palm_in_bone_space(002,f1) - palm_in_bone_space(003,f2)|',
        'clips': {str(k): {'sequence': CLIPS[k], 'frames': len(v)} for k, v in samples.items()},
        'ranking': rows_out,
        'fitted_mount_vs_best': handed,
    }
    (out / 'mount-raw-samples.json').write_text(
        json.dumps({str(k): v for k, v in samples.items()}), encoding='utf-8')
    (out / 'mount-candidate-bones.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    for entry in rows_out:
        b = entry['best_match']
        unreal.log(f"[mount] {entry['bone']:<10} best {b['distance_cm']:7.2f} cm "
                   f"at 002@{b['frame_002']} / 003@{b['frame_003']}")
    return 0


if __name__ == '__main__':
    main()
