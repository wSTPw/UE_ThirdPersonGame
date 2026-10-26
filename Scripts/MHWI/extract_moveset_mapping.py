"""Read source FSM and LMT95 TIML into explicit, provenance-labelled metadata.

Binary layout research references (no game/editor is launched):
https://github.com/Strackeror/MHW-Fsm/blob/main/fsm_handling.py
https://github.com/AsteriskAmpersand/MHW-Free-HyperKinetics/blob/main/struct/Lmt.py
https://github.com/AsteriskAmpersand/MHW-Free-HyperKinetics/blob/main/struct/TIML.py
"""
from __future__ import annotations
import json
import struct
from pathlib import Path
from read_source_fsm import XfsReader

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/nativePC'
GROUPS = {956269290: 'CollisionTimelineObject', 1221988687: 'PlMotionCommon',
          1875693838: 'PlMotionInput', 1550093923: 'ShellCreate', 2124266392: 'ShellMultiCreate'}
FIELDS = {150806694: 'mFlag', 1852046279: 'mFlag1', 4150962813: 'mFlag2',
          503910216: 'mFlag4', 4027018852: 'mFlag6', 2575924291: 'mTrigger',
          2222217367: 'mActionPhase', 1113117094: 'mActionPhaseSub',
          2241509828: 'mLinkMotionPhase', 2996226662: 'NodeID[0]',
          3213885619: 'Bank[0]', 2724604139: 'mWeaponGaugeIndex',
          717816547: 'mMotionSpeed', 1737628254: 'mWeaponMotionNo'}


def lmt_events(path):
    data = path.read_bytes()
    def read(fmt, off): return struct.unpack_from('<' + fmt, data, off)
    entries = {}
    for index in range(read('H', 6)[0]):
        offset = read('Q', 16 + index * 8)[0]
        if not offset: continue
        timl = read('Q', offset + 88)[0]
        entry = {'source_frame_count': read('I', offset + 12)[0],
                 'source_loop_frame': read('i', offset + 16)[0], 'groups': []}
        if timl:
            group_offset, count, ix0, ix1, length, loopstart, loopcontrol, label = read('QQiiffiI', timl)
            entry.update(timl_length_frames=length, timl_label_hash=label)
            for g in range(count):
                track_offset, track_count, group_hash, _ = read('QQIi', group_offset + g * 24)
                if group_hash not in GROUPS: continue
                tracks = []
                for t in range(track_count):
                    frame_offset, frame_count, field_hash, kind = read('QQIi', track_offset + t * 24)
                    frames = []
                    for k in range(frame_count):
                        pos = frame_offset + k * 20
                        value = read('f' if kind == 2 else 'i' if kind == 0 else 'I', pos)[0]
                        frames.append([read('f', pos + 12)[0], value])
                    tracks.append({'hash': field_hash, 'name': FIELDS.get(field_hash), 'frames': frames})
                entry['groups'].append({'hash': group_hash, 'name': GROUPS[group_hash], 'tracks': tracks})
        entries[f'{path.stem}_{index:03}'] = entry
    return entries


def intervals(frames, last):
    result = []
    for i, (at, value) in enumerate(frames):
        if value & 1:
            end = frames[i + 1][0] if i + 1 < len(frames) else last
            result.append([at, end])
    return result


def track(entry, group, field):
    return [t['frames'] for g in entry['groups'] if g['hash'] == group
            for t in g['tracks'] if t['hash'] == field]


def listify(value): return value if isinstance(value, list) else [value] if value is not None else []


def properties(value):
    if isinstance(value, dict):
        if value.get('mPropertyName'): yield value['mPropertyName']
        for child in value.values(): yield from properties(child)
    elif isinstance(value, list):
        for child in value: yield from properties(child)


def main():
    wp = NATIVE / 'hm/wp/wp03'
    fsm = XfsReader((wp / 'wp03_action.fsm').read_bytes()).parse()['root']
    nodes = fsm['mpRootCluster']['mpNodeList']
    conditions = {c['mName']['mId']: list(properties(c['mpRootNode']))
                  for c in fsm['mpConditionTree']['mpTreeList']}
    evidence_nodes = []
    for n in nodes:
        param = n['mpProcessList']['mpParameter']
        evidence_nodes.append({'node_id': n['mId'], 'name_ja': n['mName'],
            'process': n['mpProcessList']['mContainerName'],
            'action_no': param.get('ActionNo', {}).get('EnumValue'),
            'motion_no': param.get('MotionNo'), 'motion_no_phase1': param.get('MotionNo_Phase1'),
            'transitions': [{'destination_node_id': link['mDestinationNodeId'],
                             'conditions': conditions.get(link['mConditionId'], [])}
                            for link in listify(n['mpLinkList'])]})
    events = lmt_events(wp / 'mot/w03_00/w03_00.lmt')
    definitions = [
        ('StepSlash', 101, 11), ('OverheadSlash', 102, 10), ('FadeSlash', 103, 7),
        ('SpiritI', 104, 1), ('Thrust', 105, 4), ('RisingSlash', 107, 3),
        ('SpiritII', 106, 12), ('SpiritIII', 108, 2), ('SpiritRoundslash', 109, 5),
        # UE displacement verification (2026-10-23): the imported basis makes
        # 128 actor-left and 127 actor-right; keep the original node/clip pairs.
        ('SpiritStepSlash', 110, 6), ('FadeSlashLeft', 128, 8), ('FadeSlashRight', 127, 9),
        # 2026-10-22 correction: 170/node45 is the helm-breaker opener (SpiritThrust),
        # 140/node28 is ForesightSlash. The earlier table had these two reversed.
        ('SpiritThrust', 170, 45), ('ForesightSlash', 140, 28), ('HelmRise', 171, 55),
        ('HelmAir', 172, 56), ('SpiritHelmBreaker', 173, 58), ('HelmLand', 174, 57),
        ('SpecialSheathe', 306, 61), ('IaiSlash', 307, 64), ('IaiSpiritSlash', 308, 65),
        ('IaiSpiritSlashWhite', 309, 65), ('IaiSpiritSlashYellow', 310, 65),
        ('IaiSpiritSlashRed', 311, 65)]
    moves = {}
    for move, index, node_id in definitions:
        clip = f'w03_00_{index:03}'
        event = events[clip]
        collision = [i for frames in track(event, 956269290, 150806694)
                     for i in intervals(frames, event['timl_length_frames'])]
        input_tracks = [t for g in event['groups'] if g['hash'] == 1875693838 for t in g['tracks']]
        # 256/512 and larger bitfields distinguish buffer/accept/cancel controls.
        # Preserve all values; first nonzero is NOT automatically a legal chain frame.
        changes = sorted({frame for t in input_tracks for frame, value in t['frames'] if value and frame > 0})
        moves[move] = {'clip': clip, 'fsm_node_id': node_id,
            'fsm_action_no': evidence_nodes[node_id]['action_no'],
            'mapping_status': 'inferred_from_source_pose_and_motion_events',
            'source_frames': event['timl_length_frames'],
            'converted_duration_seconds_at_60fps': event['timl_length_frames'] / 60,
            'collision_active_frames': collision,
            'collision_status': 'source_timl_collision_enable_bit0; not a swept weapon trace verification',
            'input_flag_change_frames': changes,
            'input_flags': input_tracks,
            'cancel_status': 'unknown_per_button; raw source bitfields retained; do not use first change as universal cancel',
            'source_common_events': [t for g in event['groups'] if g['hash'] == 1221988687 for t in g['tracks']],
            'source_motion_speed': [t['frames'] for g in event['groups'] if g['hash'] == 1221988687
                                    for t in g['tracks'] if t['hash'] == 717816547],
            'delayed_hit_status': 'shell/effect-generated extra damage is not represented by collision_active_frames'}
        if move in ['SpiritII', 'RisingSlash']:
            moves[move]['mapping_status'] = 'source_pose_and_user_identified_correction_2026_10_22'
            moves[move]['mapping_note'] = '106 is SpiritII; 107 is RisingSlash. Previous labels were reversed; corrected after user comparison and UE source-pose review.'
        if move in ['FadeSlashLeft', 'FadeSlashRight']:
            moves[move]['mapping_status'] = 'ue_runtime_displacement_correction_2026_10_23'
            moves[move]['fsm_binding_status'] = 'original_fsm_name_input_and_mbd_agree_B05_pending_tests'
            moves[move]['mapping_note'] = ('UE camera-relative movement tests proved imported clip 128 moves actor-left and 127 moves actor-right. B05 source binding is left128/node8/Action82 and right127/node9/Action83, confirmed by original FSM names/arrow inputs and MBD362/361. Body clip, collision, length, flags and speed remain unchanged; source root X alone does not define UE lateral semantics. Evidence: Saved/MHWIImport/PIE-behavior-direction.json (92 checks passed after montage swap).')
    output = {'schema_version': 1, 'date': '2026-10-22',
        'status': 'source_static_research_no_ue_runtime_verification',
        'fps': 60, 'fps_status': 'conversion pipeline explicitly uses 60fps; TIML values are source frame units; no source runtime speed modifiers decoded',
        'evidence': {'fsm': 'ArtSource/ThirdParty/MHWLongSword/nativePC/hm/wp/wp03/wp03_action.fsm',
                     'lmt': 'ArtSource/ThirdParty/MHWLongSword/nativePC/hm/wp/wp03/mot/w03_00/w03_00.lmt',
                     'inventory': 'ArtSource/ThirdParty/MHWLongSword/source-inventory.json',
                     'pose_sampling': 'Scripts/MHWI/sample_source_poses.py',
                     'layout_references': __doc__.splitlines()[3:6]},
        'important': ['FSM ActionNo and LMT MotionNo are different namespaces.',
                      'Clip labels are inferred from source pose and event shape, not claimed as original text labels.',
                      'No exact parry/invincibility/cancel timings claimed until flag meanings are decoded.',
                      'Iceborne Iai Spirit Slash counter preserves a spirit level rather than the Rise/Wilds level-up behavior.'],
        'moves': moves,
        'drawn_locomotion': {'status': 'source_pose_inference_and_source_loop_frame', 'idle': 'w03_00_001',
                             'draw': 'w03_00_002', 'sheathe': 'w03_00_003',
                             'walk_loop_candidate': 'w03_00_004',
                             'walk_start_candidate': 'w03_00_005',
                             'turn_start_candidates': ['w03_00_006', 'w03_00_007'],
                             'walk_stop_candidate': 'w03_00_008',
                             'moving_sheathe_candidate': 'w03_00_009',
                             'roll_back': 'w03_00_010', 'roll_forward': 'w03_00_011',
                             'roll_right': 'w03_00_012', 'roll_left': 'w03_00_013',
                             'run_loop': None, 'run_note': '014/015 have directional start/turn poses, not yet identified as loops'},
        'sheathed_locomotion': {'status': 'source_pose_inference_and_source_loop_frame',
                               'idle': 'co00_00_001', 'idle_variants': ['co00_00_002', 'co00_00_003'],
                               'walk': 'co00_00_203', 'sprint_candidate': 'co00_00_090', 'roll': 'co00_00_130',
                               'rejected': {'co00_00_034': 'ladder ascent, root +171.58cm vertical',
                                            'co00_00_035': 'ladder descent, root -173.53cm vertical',
                                            'co00_00_010': 'low crouched gait', 'co00_00_037': 'low crouched gait'},
                               'source_speed_cm_s': {'walk': 135.04176, 'run': 365.51273},
                               'note': '203/090 are standing forward loops, inspected in UE; labels remain pose inference. Rates match project speeds 180/420cm/s.'},
        'locomotion_source_headers': {key: {k: value for k, value in events[key].items() if k != 'groups'}
                                      for key in [f'w03_00_{i:03}' for i in range(1,16)]},
        'fsm_nodes': evidence_nodes}
    path = ROOT / 'Scripts/MHWI/moveset_mapping.json'
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(path)


if __name__ == '__main__': main()
