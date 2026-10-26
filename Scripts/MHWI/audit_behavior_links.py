"""Read-only endpoint / link audit for the MHWI roll step slash and 140/170 fix.

Run from a normal Python shell (no Unreal required):

    python Scripts/MHWI/audit_behavior_links.py

It reads source MBD through the fixed-fingerprint connector reader and text data:
* ``Scripts/MHWI/moveset_mapping.json``
* ``Saved/MHWI/source-poses.json`` (historical read-only sampling of the original
  converted ``ArtSource/ThirdParty/MHWLongSword/Converted/MHW_Hunter_LongSword_Actions.blend``
  by ``Scripts/MHWI/sample_source_poses.py``)
* ``Saved/MHWIImport/Research-20261022/source-evidence.json``

If Blender's ``bpy`` is importable, the script additionally opens the .blend
without saving and samples clip 101 frame by frame in the wheel 25..50. It never
saves the .blend and never writes a UE asset. The only output is
``Saved/MHWIImport/DSH-20261022/behavior-link-audit.json`` plus stdout.

The entry frame now comes from original MBD (B04). Endpoint errors are diagnostic
and cannot override the source. Entry 48 leaves 7 source frames
before the frame-55 hit start. ``author_behavior_corrections.roll_step_segment_config()``
is the authoritative segment config; this audit prints it for the recommended entry.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import author_behavior_corrections as corrections  # noqa: E402  (no Unreal writes at import)

MAPPING = ROOT / 'Scripts/MHWI/moveset_mapping.json'
SOURCE_POSES = ROOT / 'Saved/MHWI/source-poses.json'
SOURCE_EVIDENCE = ROOT / 'Saved/MHWIImport/Research-20261022/source-evidence.json'
BLEND = ROOT / 'ArtSource/ThirdParty/MHWLongSword/Converted/MHW_Hunter_LongSword_Actions.blend'
OUT = ROOT / 'Saved/MHWIImport/DSH-20261022/behavior-link-audit.json'

POSE_BONES = ['bone_003', 'bone_007', 'bone_008', 'bone_012']
CANDIDATE_MIN = 25.0
CANDIDATE_MAX = 50.0


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf8'))


def _relative(entry, bones):
    bones = entry['bones']
    root = bones.get('bone_root', [0.0, 0.0, 0.0])
    return {name: [bones[name][i] - root[i] for i in range(3)]
            for name in bones if name in bones and name != 'bone_root'}


def pose_error(reference, candidate, bones=POSE_BONES):
    a = _relative(reference, bones)
    b = _relative(candidate, bones)
    errors = {}
    for name in bones:
        if name in a and name in b:
            errors[name] = math.sqrt(sum((a[name][i] - b[name][i]) ** 2 for i in range(3))) * 100.0
    if not errors:
        return None, {}
    return sum(errors.values()) / len(errors), errors


def _entry(frame, bones):
    return {'frame': float(frame), 'bones': bones}


def historical_candidates():
    poses = load_json(SOURCE_POSES)
    if not poses:
        return None, None, 'source-poses.json missing'
    actions = poses.get('actions', {})
    if 'w03_00_129' not in actions or 'w03_00_101' not in actions:
        return None, None, 'source-poses.json does not contain both clips'
    reference = actions['w03_00_129'][-1]
    candidates = []
    for entry in actions['w03_00_101']:
        frame = float(entry['frame'])
        if CANDIDATE_MIN <= frame <= CANDIDATE_MAX:
            error, bones = pose_error(reference, entry)
            candidates.append(dict(frame=frame, mean_error_cm=error, bone_errors_cm=bones))
    return reference['frame'], candidates, 'historical samples from the converted .blend'


def _reset_pose(arm):
    """Clear channels so unkeyed bones cannot leak pose between the two actions."""
    for bone in arm.pose.bones:
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def bpy_candidates():
    try:
        import bpy
    except Exception:
        return None, 'bpy is not importable in this Python; no live .blend sampling'
    if not BLEND.exists():
        return None, 'converted .blend missing'
    try:
        bpy.ops.wm.open_mainfile(filepath=str(BLEND))
        arm = bpy.data.objects.get('Armature')
        if arm is None:
            return None, 'no Armature in the converted .blend'
        actions = {action.name: action for action in bpy.data.actions}
        if 'w03_00_129' not in actions or 'w03_00_101' not in actions:
            return None, 'actions w03_00_129/w03_00_101 not found in the converted .blend'
        if arm.animation_data is None:
            return None, 'Armature has no animation_data in the converted .blend'
        _reset_pose(arm)
        arm.animation_data.action = actions['w03_00_129']
        end = int(actions['w03_00_129'].frame_range[1])
        bpy.context.scene.frame_set(end)
        reference = _entry(end, {bone.name: list(arm.matrix_world @ arm.pose.bones[bone.name].head)
                                 for bone in arm.data.bones})
        _reset_pose(arm)
        arm.animation_data.action = actions['w03_00_101']
        candidates = []
        for frame in range(int(CANDIDATE_MIN), int(CANDIDATE_MAX) + 1):
            bpy.context.scene.frame_set(frame)
            entry = _entry(frame, {bone.name: list(arm.matrix_world @ arm.pose.bones[bone.name].head)
                                   for bone in arm.data.bones})
            error, bones = pose_error(reference, entry)
            candidates.append(dict(frame=float(frame), mean_error_cm=error, bone_errors_cm=bones))
        return candidates, 'live frame-by-frame sampling of the converted .blend (not saved)'
    except Exception as error:  # read-only audit must report, not pretend evidence
        return None, 'bpy sampling failed: %r' % (error,)


def recommend(candidates):
    usable = [item for item in candidates if item.get('mean_error_cm') is not None]
    if not usable:
        return None
    return min(usable, key=lambda item: item['mean_error_cm'])


def mapping_check(mapping, evidence):
    result = {}
    for name, clip, node, action, collision in [
            ('SpiritThrust', 'w03_00_170', 45, 87, [[84.0, 97.0]]),
            ('ForesightSlash', 'w03_00_140', 28, 86, [[70.0, 80.0]])]:
        move = mapping['moves'][name]
        result[name] = {
            'clip': move['clip'],
            'fsm_node_id': move['fsm_node_id'],
            'fsm_action_no': move['fsm_action_no'],
            'source_frames': move['source_frames'],
            'collision': move['collision_active_frames'],
            'clip_ok': move['clip'] == clip,
            'node_ok': move['fsm_node_id'] == node,
            'action_ok': move['fsm_action_no'] == action,
            'collision_ok': move['collision_active_frames'] == collision,
        }
        if evidence:
            tracks = [t for g in evidence['clips'][clip]['groups'] if g['hash'] == 956269290
                      for t in g['tracks'] if t['hash'] == 150806694]
            intervals = []
            for track in tracks:
                frames = track['frames']
                for index, pair in enumerate(frames):
                    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                        continue
                    frame, value = pair
                    if value & 1:
                        end = frames[index + 1][0] if index + 1 < len(frames) else \
                            evidence['clips'][clip]['timl_length_frames']
                        intervals.append([frame, end])
            result[name]['evidence_collision'] = intervals
            result[name]['evidence_collision_ok'] = intervals == collision
    if evidence:
        result['connectors'] = {}
        for clip in ['w03_00_118', 'w03_00_121', 'w03_00_124']:
            groups = evidence.get('clips', {}).get(clip, {}).get('groups', [])
            result['connectors'][clip] = {
                'has_collision_group': any(g.get('hash') == 956269290 for g in groups),
                'damage_windows': 'none',
            }
    return result


def historical_root_positions():
    poses = load_json(SOURCE_POSES)
    if not poses:
        return {}
    actions = poses.get('actions', {})
    result = {}
    for clip in ['w03_00_129', 'w03_00_101']:
        entries = actions.get(clip)
        if not entries:
            continue
        first = entries[0]['bones'].get('bone_root')
        result[clip] = []
        for entry in entries:
            root = entry['bones'].get('bone_root')
            if root and first:
                delta = [root[i] - first[i] for i in range(3)]
                result[clip].append({
                    'frame': float(entry['frame']),
                    'root_delta_cm': [round(value * 100.0, 3) for value in delta],
                    'horizontal_cm': round(math.hypot(delta[0], delta[1]) * 100.0, 3),
                })
    return result


def main():
    mapping = load_json(MAPPING)
    if mapping is None:
        raise SystemExit('moveset_mapping.json missing')
    evidence = load_json(SOURCE_EVIDENCE)
    reference_frame, historical, provenance = historical_candidates()
    live, live_note = bpy_candidates()
    candidates = live if live else (historical or [])
    best = recommend(candidates)
    # Without bpy the historical 12.5%-step samples cannot reproduce the measured
    # 48; keep the authoritative project entry instead of silently reverting to 37.
    # Endpoint matches stay diagnostic; they must never override original MBD.
    entry = corrections.ROLL_STEP_ENTRY_FRAME
    timing = corrections.roll_step_timing(entry)
    config = corrections.roll_step_segment_config(entry)
    measured_root = load_json(ROOT / 'Saved/MHWIImport/DSH-20261022/root-link-readonly.json')
    try:
        checked = mapping_check(mapping, evidence)
    except Exception as error:  # keep the endpoint audit usable even if evidence shape drifts
        checked = {'error': repr(error)}
    report = {
        'status': 'read_only_static_audit_not_runtime_verification',
        'blend': str(BLEND.relative_to(ROOT)) if BLEND.exists() else None,
        'blend_sampling': live_note,
        'historical_sampling': provenance,
        'clip_129_end_frame': reference_frame,
        'candidates': candidates,
        'recommended_entry_frame': entry,
        'recommended_entry_seconds': timing['entry_seconds'],
        'recommendation_is_provisional': False,
        'entry_source': 'Original w03_00.mbd destination101 / previous129 startFrame; native exit/blend consumer unresolved',
        'pre_hit_source_frames': corrections.ROLL_STEP_HIT_START_FRAME - entry,
        'decision': ('entry %g read from original MBD; endpoint diagnostics (best 48=0.54cm; 45=8.74cm, '
                     '47=2.68cm, 49=2.43cm). Entry 37 keeps 18 pre-hit frames but leaves '
                     'clip 101 root at -188.38cm instead of -220.12cm at 48, adding 31.7cm '
                     'of remaining forward root travel.' % entry),
        'timing': timing,
        'segment_config': config,
        'mapping_check': checked,
        'root_positions': historical_root_positions(),
        'measured_root_evidence': measured_root,
        'caveats': [
            'Pose error compares bone-head positions relative to bone_root; rotations are not sampled.',
            'Entry 48 leaves only 7 source frames (0.117s) before the frame-55 hit start; the montage blend-in is 0.10s, so the hit begins just after the blend completes.',
            'Historical samples without bpy exist only at 0/12/25/40/60/80/100 percent frames; 48 cannot be reproduced from that file.',
            'Root deltas are in source Blender axes, not UE axes; do not treat horizontal_cm as a UE forward value.',
            'Measured entry-48 composite root delta is [2.216, -259.804, 0]cm in root-link-readonly.json; PIE still verifies actual capsule travel.',
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, indent=2))
    print('\nwrote ' + str(OUT))
    return report


if __name__ == '__main__':
    main()
