"""Export source-accurate internal weapon motion, without changing the weapon rig.

Offline evidence: portable Blender's Python (bundled NumPy), this file --audit
FBX export: Blender --background <existing .blend> --python-exit-code 1
    --python Scripts/MHWI/native_weapon_export.py -- --export

The EVWP mMotNo selects the motion family. Hunter mWeaponMotionNo selects an
entry within that family. Neither value is treated as a whole-weapon mount.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
import datetime
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_animation_source as sampling

BASE = ROOT / 'ArtSource/ThirdParty/MHWLongSword'
NATIVE = BASE / 'nativePC'
OUTPUT = BASE / 'NativeFidelity/Weapons'
REPORT = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024'
TEMPLATE_URL = 'https://raw.githubusercontent.com/zStatykz/MHW_EVWP_Template/master/EVWP_Template.bt'
WIKI_URL = 'https://github.com/AniBullet/MonsterHunterWorldModding/wiki/Editing-EVWP-Files'


def save(name, value):
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def read_evwp(path):
    """145-byte Iceborne v13 layout; field labels from the original template."""
    data = path.read_bytes()
    if len(data) != 145 or data[4:8] != b'EVWP' or struct.unpack_from('<I', data, 8)[0] != 13:
        raise ValueError(f'Unsupported EVWP layout: {path}')
    transforms = {}
    for name, offset in [('showcase', 12), ('smith', 40), ('sheathed', 68), ('charm', 112)]:
        values = struct.unpack_from('<7f', data, offset)
        transforms[name] = {'source_offset': offset, 'position': values[:3],
                            'rotation': values[3:6], 'scale': values[6]}
    return {'source': sampling.evidence(path), 'version': 13,
            'preset_id_off_shake': struct.unpack_from('<I', data, 96)[0],
            'mMotNo': struct.unpack_from('<I', data, 100)[0],
            'mWpTypeGeneralValue': struct.unpack_from('<I', data, 104)[0],
            'mEpvNo': struct.unpack_from('<I', data, 108)[0],
            'transforms': transforms, 'flags': list(data[140:145]),
            'layout_reference': TEMPLATE_URL,
            'sheathed_boundary': 'EVWP sheathed transform is an offset after an initial placement; initial placement remains unknown.'}


def extract_comparison_evwp():
    """Read only latest archive entries. Output stays in this audit directory."""
    module_path = ROOT / 'Tools/MHW/extract_resources.py'
    spec = importlib.util.spec_from_file_location('_mhwi_native_weapon_archive', module_path)
    archive_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(archive_module)
    index = json.loads((BASE / 'archive-index.json').read_text(encoding='utf-8'))
    game = Path(index['source'])
    oodle = ctypes.CDLL(str(Path('E:/UE/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/runtimes/win-x64/native/oo2core.dll')))
    selected = {name: row for name, row in index['files'].items()
                if name.startswith('/wp/swo/') and name.endswith('.evwp')}
    if sum(row['size'] for row in selected.values()) > 256 * 1024:
        raise ValueError('Weapon EVWP selection unexpectedly exceeds 256 KiB')
    opened = {}
    results = []
    try:
        for name, row in sorted(selected.items()):
            if row['archive'] not in opened:
                opened[row['archive']] = archive_module.Archive(game / 'chunk' / row['archive'], oodle)
            target = REPORT / 'weapon-source' / name.lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            data = opened[row['archive']].read(row['offset'], row['size'])
            if target.exists() and target.read_bytes() != data:
                raise FileExistsError(target)
            target.write_bytes(data)
            results.append({'archive_entry': name, 'archive_location': row, **read_evwp(target)})
    finally:
        for archive in opened.values():
            archive.close()
    return results


def verify_comparison_models(comparisons, families):
    """Cross-check every nonzero EVWP selector against the matching model rig."""
    module_path = ROOT / 'Tools/MHW/extract_resources.py'
    spec = importlib.util.spec_from_file_location('_mhwi_native_weapon_archive_models', module_path)
    archive_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(archive_module)
    spec = importlib.util.spec_from_file_location('_mhwi_native_weapon_mod3', sampling.LEGACY / 'mod3/mod3_parser.py')
    mod3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod3)
    index = json.loads((BASE / 'archive-index.json').read_text(encoding='utf-8'))
    oodle = ctypes.CDLL('E:/UE/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/runtimes/win-x64/native/oo2core.dll')
    rows, opened = [], {}
    selected = [row for row in comparisons if row['mMotNo'] != 0]
    names = [row['archive_entry'].replace('.evwp', '.mod3') for row in selected]
    if sum(index['files'][name]['size'] for name in names) > 8 * 1024 * 1024:
        raise ValueError('Comparison weapon models exceed 8 MiB')
    try:
        for row, name in zip(selected, names):
            entry = index['files'][name]
            if entry['archive'] not in opened:
                opened[entry['archive']] = archive_module.Archive(Path(index['source']) / 'chunk' / entry['archive'], oodle)
            target = REPORT / 'weapon-source' / name.lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            data = opened[entry['archive']].read(entry['offset'], entry['size'])
            if target.exists() and target.read_bytes() != data:
                raise FileExistsError(target)
            target.write_bytes(data)
            bones, _meshes = mod3.Mod3Parser(str(target)).read()
            functions = sorted({bone['remap'] for bone in bones})
            family = f"wg03_{row['mMotNo']:02}"
            required = sorted({function for action in families[family]['actions'] for function in action['functions']})
            rows.append({'source': sampling.evidence(target), 'evwp_mMotNo': row['mMotNo'],
                         'family': family, 'model_functions': functions,
                         'required_functions': required, 'compatible': set(required).issubset(functions)})
    finally:
        for archive in opened.values():
            archive.close()
    return rows


def audit():
    REPORT.mkdir(parents=True, exist_ok=True)
    reader, pose = sampling.native_modules()
    families = {}
    for path in sorted((NATIVE / 'wp/swo/mot').glob('wg03_*/wg03_*.lmt')):
        bank = reader.read_lmt_file(path)
        families[path.stem] = {'source': sampling.evidence(path), 'actions': [
            {'motion_no': action.id, 'frame_count': action.header.frame_count,
             'duration_seconds': (action.header.frame_count - 1) / 60,
             'loop_frame': action.header.loop_frame, 'flags2': action.header.flags2,
             'functions': sorted({track.header.bone_id for track in action.tracks}),
             'track_count': len(action.tracks)} for action in bank.actions]}
    primary = {name: read_evwp(NATIVE / f'wp/swo/swo001/mod/{name}.evwp')
               for name in ('swo001', 'saya001')}
    comparisons = extract_comparison_evwp()
    comparison_models = verify_comparison_models(comparisons, families)
    groups = {}
    for row in comparisons:
        groups.setdefault(str(row['mMotNo']), []).append(row['archive_entry'])
    # The mMotNo selector and the rig's supported functions agree on family 00.
    # All other supplied families require functions absent from swo001.
    weapon_bones = {'bone_root', 'bone_000', 'bone_001', 'bone_002', 'bone_100', 'bone_101', 'bone_200'}
    matched = f"wg03_{primary['swo001']['mMotNo']:02}"
    incompatible = {name: sorted({f for a in row['actions'] for f in a['functions']
                                 if f'bone_{f:03}' not in weapon_bones})
                    for name, row in families.items() if row['actions']}
    source_summary = json.loads((ROOT / 'Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json').read_text(encoding='utf-8'))
    event_rows = []
    for entry in source_summary['source']['entries']:
        for group in entry['groups']:
            for track in group['tracks']:
                if track['name'] != 'mWeaponMotionNo':
                    continue
                for key in track['keys']:
                    event_rows.append({'hunter_clip': f"w03_00_{entry['index']:03}",
                                       'frame': key['frame'], 'motion_no': key['value'],
                                       'raw_transition': key['transition'], 'raw_kind': key['key_kind']})
    result = {'schema_version': 1, 'status': 'native_internal_weapon_motion_family_matched',
              'utc_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'primary_evwp': primary, 'families': families, 'comparison_count': len(comparisons),
              'comparison_mot_no_counts': dict(Counter(row['mMotNo'] for row in comparisons)),
              'comparison_examples': {key: values[:5] for key, values in groups.items()},
              'comparison_model_checks': comparison_models,
              'selected_family': matched, 'missing_rig_functions_by_family': incompatible,
              'family_evidence': [
                  'swo001.evwp v13 mMotNo uint32 at offset 100 equals 0.',
                  'Same source field is named mMotNo in the original EVWP binary template.',
                  'wg03_00 is the only nonempty supplied family whose animated function set is wholly present on swo001.',
                  'The other families require function 3 and/or 4; swo001 has neither.',
                  'Independent archive EVWP comparisons preserve family selector distribution.',
                  'All four nonzero-selector weapon model rigs support their selected family function set: swo009/018=01, swo015=02, swo027=03.'],
              'hunter_motion_events': event_rows, 'decoder': pose.RULE_VERSION,
              'reference_urls': [TEMPLATE_URL, WIKI_URL],
              'limits': [
                  'Family match is supported by source EVWP selector and skeleton compatibility, not original-game execution.',
                  'mWeaponMotionNo is an internal motion entry, not a whole-weapon socket event.',
                  'bone_002 is partially weighted to the handle; whole blade is primarily bone_001.',
                  'saya001 lacks function 2 and has no supported motion in family 00.',
                  'EVWP sheathed offsets are zero/identity; initial equipment placement, runtime socket transfer and scale remain unqualified.']}
    save('weapon-family-evidence.json', result)
    save('weapon-evwp-comparisons.json', comparisons)
    print(json.dumps({'selected_family': matched, 'comparison_count': len(comparisons),
                      'groups': result['comparison_mot_no_counts'], 'events': len(event_rows)}))
    return result


def export():
    import bpy
    family_audit = json.loads((REPORT / 'weapon-family-evidence.json').read_text(encoding='utf-8'))
    family = family_audit['selected_family']
    source_path = NATIVE / f'wp/swo/mot/{family}/{family}.lmt'
    reader, pose = sampling.native_modules()
    bank = reader.read_lmt_file(source_path)
    arm = bpy.data.objects['Armature_swo001']
    # Include the existing skinned weapon mesh to carry its unchanged bind pose.
    # A skeleton-only FBX's default node transforms become the animated first
    # pose in Blender's round-trip importer. UE still imports animations only.
    meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH' and any(
        modifier.type == 'ARMATURE' and modifier.object == arm for modifier in obj.modifiers)]
    original = sampling.inspect_rig(arm)
    protected_before = {p.as_posix(): sampling.evidence(p) for p in
                        (sampling.BLEND, source_path, NATIVE / 'wp/swo/swo001/mod/swo001.mod3')}
    arm.hide_set(False)
    sampling.reset_pose(arm)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.fps = 60
    rows = []
    for source in bank.actions:
        if source.header.flags2 & 1:
            raise ValueError('Weapon source unexpectedly requires a layered parent')
        name = f'{family}_{source.id:03}'
        evaluation = pose.compile_pose_evaluation(source, sampling.function_map(arm), version=bank.header.version)
        if not evaluation.supported:
            raise ValueError(str(evaluation.diagnostics))
        sampling.reset_pose(arm)
        action = sampling.build_action(arm, name, evaluation=evaluation)
        arm.animation_data.action = action
        end = source.header.frame_count - 1
        # FBX/UE require positive duration even for a one-frame held state.
        export_end = max(1, end)
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = 0, export_end
        bpy.context.scene.frame_set(0)
        bpy.ops.object.select_all(action='DESELECT')
        arm.select_set(True)
        for mesh in meshes:
            mesh.hide_set(False)
            mesh.select_set(True)
        bpy.context.view_layer.objects.active = arm
        path = OUTPUT / f'{name}.fbx'
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
            object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
            axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
            bake_anim=True, bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False, bake_anim_step=1,
            bake_anim_simplify_factor=0.0, path_mode='AUTO', embed_textures=False)
        samples = []
        for frame in sorted({0, end // 2, end}):
            bpy.context.scene.frame_set(frame)
            bone = arm.pose.bones['bone_002']
            samples.append({'frame': frame, 'bone002_armature_position': list(bone.matrix.translation),
                            'bone002_basis_translation': list(bone.location)})
        rows.append({'motion_no': source.id, 'clip': name, 'source_frame_count': source.header.frame_count,
                     'source_duration_seconds': end / 60, 'exported_duration_seconds': export_end / 60,
                     'source_loop_frame': source.header.loop_frame,
                     'hold_static': all(len(pose.compile_pose_curve(track).frames) == 1 for track in source.tracks),
                     'looping': source.header.loop_frame >= 0,
                     'animation_path': f'/Game/MHWI/Animations/Weapons/A_{name}',
                     'fbx': sampling.evidence(path), 'preview_samples': samples})
        print('EXPORTED_NATIVE_WEAPON', name, flush=True)
    sampling.reset_pose(arm)
    unchanged_rig = original == sampling.inspect_rig(arm)
    protected_after = {p.as_posix(): sampling.evidence(p) for p in
                       (sampling.BLEND, source_path, NATIVE / 'wp/swo/swo001/mod/swo001.mod3')}
    result = {'schema_version': 1, 'status': 'exported_not_ue_imported',
              'family': family, 'family_evidence': 'Saved/MHWIImport/NativeFidelity-20261024/weapon-family-evidence.json',
              'source': sampling.evidence(source_path), 'source_blend': sampling.evidence(sampling.BLEND),
              'fps': 60, 'target_skeleton': '/Game/MHWI/Weapons/SK_MHWI_LongSword_Skeleton',
              'rig_unchanged': unchanged_rig, 'protected_sources_unchanged': protected_before == protected_after,
              'original_rig': original, 'clips': rows,
              'hunter_motion_events': family_audit['hunter_motion_events'],
              'recommended_runtime': 'Set the internal weapon sequence at exact hunter source frame. Hold static states and final dynamic pose. Do not use these entries to switch whole-weapon attachment bones.',
              'limits': family_audit['limits']}
    save('weapon-animation-manifest.json', result)
    if not unchanged_rig or protected_before != protected_after:
        raise AssertionError('Protected source or static rig changed')
    print('NATIVE_WEAPON_COMPLETE ' + json.dumps({'clips': len(rows), 'rig_unchanged': unchanged_rig}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', action='store_true')
    parser.add_argument('--export', action='store_true')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.audit:
        audit()
    if args.export:
        export()
    if not args.audit and not args.export:
        parser.error('Choose --audit and/or --export')


if __name__ == '__main__':
    main()
