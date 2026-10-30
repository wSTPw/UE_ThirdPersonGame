"""B20 targeted, source-qualified locomotion assets and CDO configuration.

Motion014/015 are bound by native actions65/66, not guessed landing clips.
Graph wiring is recorded separately in Tools/MHW/b20-animation-graph.json.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Scripts/MHWI'))
OUT = ROOT / 'Saved/MHWIRestoration/B20-20261027'


def import_locomotion():
    import unreal
    import author_native_fidelity as author
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before importing locomotion')
    manifest = json.loads((ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json').read_text(encoding='utf-8'))
    rows = {r['clip']: r for r in manifest['clips']}
    skeleton = unreal.load_asset('/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton')
    result = []
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    for motion in (5, 6, 7, 8, 14, 15):
        row = rows[f'w03_00_{motion:03}']
        path = ROOT / row['fbx']
        if row.get('passed') is not True or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('Unqualified or changed source FBX: ' + str(path))
        sequence = author._import(path, '/Game/MHWI/Animations/NativeFidelity/LongSword', skeleton, True)
        # Transitions decorate the existing CharacterMovement/BlendSpace path;
        # preserve its physical movement and do not extract extra displacement.
        sequence.set_editor_property('force_root_lock', True)
        unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False)
        result.append(dict(motion=motion, path=sequence.get_path_name(),
                           skeleton=str(sequence.get_editor_property('skeleton')),
                           seconds=sequence.get_play_length(), source_seconds=row['duration'],
                           root_lock=str(sequence.get_editor_property('root_motion_root_lock')),
                           force_root_lock=sequence.get_editor_property('force_root_lock'),
                           source_fbx_sha256=row['sha256'],
                           consumer_confirmed=True))
        if abs(sequence.get_play_length() - row['duration']) > 1e-4:
            raise RuntimeError('Imported duration differs from qualified source')
    report = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), passed=True, clips=result)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'locomotion-assets.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def bind_locomotion():
    import unreal
    cls = unreal.load_class(None, '/Game/MHWI/Blueprints/ABP_MHWI_Hunter.ABP_MHWI_Hunter_C')
    cdo = unreal.get_default_object(cls)
    clips = {i: unreal.load_asset('/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_%03d' % i)
             for i in (5, 6, 7, 8, 14, 15)}
    if any(not value for value in clips.values()):
        raise RuntimeError('Qualified locomotion assets missing')
    cdo.set_editor_property('locomotion_transition_clips', clips)
    cdo.set_editor_property('locomotion_turn_threshold_degrees', 70.0)
    blueprint = unreal.load_asset('/Game/MHWI/Blueprints/ABP_MHWI_Hunter')
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    if not unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False):
        raise RuntimeError('ABP configuration save failed')
    actual = dict(cdo.get_editor_property('locomotion_transition_clips'))
    if set(actual) != set(clips) or any(actual[k] != clips[k] for k in clips):
        raise RuntimeError('ABP locomotion CDO readback mismatch')
    report = dict(passed=True, clips={str(k):v.get_path_name() for k,v in actual.items()},
                  threshold_degrees=cdo.get_editor_property('locomotion_turn_threshold_degrees'),
                  source_actions={'14':65, '15':66})
    (OUT / 'locomotion-cdo.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def verify_assets():
    """Read actual delivered assets; does not import, configure, or save them."""
    import unreal
    bp = unreal.load_asset('/Game/MHWI/Blueprints/ABP_MHWI_Hunter')
    cls = unreal.load_class(None, '/Game/MHWI/Blueprints/ABP_MHWI_Hunter.ABP_MHWI_Hunter_C')
    cdo = unreal.get_default_object(cls)
    profile = cdo.get_editor_property('equipment_ik_profile')
    if not profile or profile.get_path_name() != '/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile.DA_MHWI_EquipmentIK_Profile':
        raise AssertionError('Missing actual Profile binding')
    out = dict(passed=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               inherits_mhwi_anim_instance=isinstance(cdo, unreal.MHWIAnimInstance), profile=profile.get_path_name(), clips=[], ik_nodes=[])
    skeleton = unreal.load_asset('/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton')
    clips = dict(cdo.get_editor_property('locomotion_transition_clips'))
    if set(clips) != {5, 6, 7, 8, 14, 15} or cdo.get_editor_property('locomotion_turn_threshold_degrees') != 70.0:
        raise AssertionError('Locomotion map/gate differs from source-qualified configuration')
    manifest = json.loads((ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json').read_text(encoding='utf-8'))
    rows = {r['clip']: r for r in manifest['clips']}
    for motion, clip in sorted(clips.items()):
        source = rows[f'w03_00_{motion:03}']
        if (clip.get_editor_property('skeleton') != skeleton
                or abs(clip.get_play_length() - source['duration']) > 1e-4
                or not clip.get_editor_property('force_root_lock')
                or not source['passed']):
            raise AssertionError('Actual clip qualification differs: ' + str(motion))
        out['clips'].append(dict(motion=motion, path=clip.get_path_name(), seconds=clip.get_play_length(),
                                 skeleton=skeleton.get_path_name(), force_root_lock=True,
                                 root_motion=clip.get_editor_property('enable_root_motion')))
    graph = bp.get_animation_graphs()[0]
    nodes = graph.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
    out['animation_node_count'] = len(nodes)
    for node in nodes:
        if isinstance(node, unreal.AnimGraphNode_SequenceEvaluator):
            data = node.get_editor_property('node')
            out['transition_evaluator'] = dict(should_loop=bool(data.get_editor_property('should_loop')),
                                               teleport_to_explicit_time=bool(data.get_editor_property('teleport_to_explicit_time')))
            if out['transition_evaluator']['should_loop'] or not out['transition_evaluator']['teleport_to_explicit_time']:
                raise AssertionError('Transition evaluator must teleport without looping/notifies/root extraction')
        if isinstance(node, unreal.AnimGraphNode_TwoBoneIK):
            data = node.get_editor_property('node')
            row = dict(name=node.get_name())
            for key in ('ik_bone', 'effector_location_space', 'effector_target', 'joint_target_location_space',
                        'joint_target', 'allow_stretching', 'maintain_effector_rel_rot'):
                row[key] = str(data.get_editor_property(key))
            row['ik_bone'] = str(data.get_editor_property('ik_bone').get_editor_property('bone_name'))
            for key in ('effector_target', 'joint_target'):
                row[key] = str(data.get_editor_property(key).get_editor_property('bone_reference').get_editor_property('bone_name'))
            if (data.get_editor_property('effector_location_space') != unreal.BoneControlSpace.BCS_BONE_SPACE
                    or data.get_editor_property('joint_target_location_space') != unreal.BoneControlSpace.BCS_BONE_SPACE
                    or data.get_editor_property('allow_stretching')
                    or not data.get_editor_property('maintain_effector_rel_rot')):
                raise AssertionError('Actual IK node space/rotation configuration differs')
            expected_mid = {'bone_008':'bone_007', 'bone_012':'bone_011', 'bone_016':'bone_015', 'bone_020':'bone_019'}
            if row['effector_target'] != row['ik_bone'] or expected_mid.get(row['ik_bone']) != row['joint_target']:
                raise AssertionError('IK target bone differs from qualified chain')
            out['ik_nodes'].append(row)
    if len(out['ik_nodes']) != 4:
        raise AssertionError('Actual graph must contain four IK solvers')
    if {row['ik_bone'] for row in out['ik_nodes']} != {'bone_008', 'bone_012', 'bone_016', 'bone_020'}:
        raise AssertionError('Actual graph does not cover each of the four chains exactly once')
    if 'transition_evaluator' not in out:
        raise AssertionError('Actual graph has no transition evaluator')
    if not out['inherits_mhwi_anim_instance']:
        raise AssertionError('Actual AnimInstance parent contract differs')
    out['passed'] = True
    (OUT / 'assets-final-readback.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    return out


def finalize():
    import unreal
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before compiling/saving the delivered graph')
    bp = unreal.load_asset('/Game/MHWI/Blueprints/ABP_MHWI_Hunter')
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError('Final graph save failed')
    return verify_assets()


def verify_weapon_selections():
    """Actual formal DA enumeration; selection does not prove clip playback."""
    import unreal
    data = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
    motions = dict(data.get_editor_property('weapon_motions'))
    moves = dict(data.get_editor_property('moves'))
    rows = []
    selected = {0, 1}  # Existing C++ sheathed/drawn defaults, separately labeled.
    for name, definition in sorted(moves.items(), key=lambda pair: str(pair[0])):
        events = [dict(time=float(event.get_editor_property('time')), motion=int(event.get_editor_property('motion_no')))
                  for event in definition.get_editor_property('weapon_motion_events')]
        selected.update(row['motion'] for row in events if row['motion'] >= 0)
        rows.append(dict(move=str(name), events=events))
    if len(moves) != 32 or set(motions) != set(range(6)):
        raise AssertionError('Formal moveset/weapon map differs from delivered contract')
    out = dict(passed=True, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               asset=data.get_path_name(), move_count=len(moves), cpp_default_values=[0, 1],
               selected_values=sorted(selected), no_formal_selection=sorted(set(motions)-selected),
               weapon_motions={str(key): value.get_path_name() for key, value in motions.items()}, moves=rows,
               scope='Actual DA event enumeration plus labeled C++ defaults; no original-game entry or runtime selection is invented')
    (OUT / 'weapon-motion-coverage.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    return out
