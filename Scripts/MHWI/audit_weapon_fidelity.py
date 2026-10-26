"""Offline, read-only MHWI weapon/source-decoder audit.

Normal run uses the project-local portable Blender Python (NumPy is bundled):
  Tools/MHW/Runtime/blender-4.5.0-windows-x64/4.5/python/bin/python.exe \
    Scripts/MHWI/audit_weapon_fidelity.py

Optional saved-rig audit (no .blend or UE asset writes):
  Tools/MHW/Runtime/blender-4.5.0-windows-x64/blender.exe --background \
    ArtSource/ThirdParty/MHWLongSword/Converted/MHW_Hunter_LongSword_Actions.blend \
    --python Scripts/MHWI/audit_weapon_fidelity.py -- --blender-phase

The upstream MIT native-instruction sampler is imported as a synthetic package;
its add-on __init__, installation, updater and registration are never executed.
Its reported native parity is third-party evidence, not a game execution test.
All output goes to Saved/MHWIImport/SourceFidelity-20261024 by default.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import types

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/nativePC'
OLD = ROOT / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main'
CACHE = ROOT / 'Saved/MHWIImport/SourceFidelity-20261023'
UPSTREAM = CACHE / 'timing-mhw-anim-tools/mhw-anim-tools-main'
BLEND = ROOT / 'ArtSource/ThirdParty/MHWLongSword/Converted/MHW_Hunter_LongSword_Actions.blend'
DEFAULT_OUT = ROOT / 'Saved/MHWIImport/SourceFidelity-20261024'
FOCUS_BONES = {2, 4, 8, 12, 16, 20, *range(247, 255)}


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def evidence(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'path': relative(path), 'bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def serializable(value):
    if hasattr(value, 'tolist'):
        return value.tolist()
    raise TypeError(type(value).__name__)


def save(out, name, value):
    (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                     default=serializable), encoding='utf-8')


def module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_native_modules():
    # A namespace shell avoids importing the add-on's top-level __init__.py.
    package = types.ModuleType('_mhwi_audit_native')
    package.__path__ = [str(UPSTREAM)]
    sys.modules[package.__name__] = package
    reader = importlib.import_module(package.__name__ + '.core.formats.lmt.reader')
    pose = importlib.import_module(package.__name__ + '.core.formats.lmt.pose_evaluation')
    return reader, pose


def scalar_stats(values):
    values = sorted(values)
    if not values:
        return {'count': 0, 'max': None, 'mean': None, 'p95': None}
    return {'count': len(values), 'max': values[-1],
            'mean': sum(values) / len(values),
            'p95': values[min(len(values) - 1, int(len(values) * .95))]}


def distance(left, right, quaternion):
    if not quaternion:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(left[:3], right[:3])))
    nl = math.sqrt(sum(a * a for a in left))
    nr = math.sqrt(sum(a * a for a in right))
    if nl <= 1e-12 or nr <= 1e-12:
        return None
    dot = abs(sum(a * b for a, b in zip(left, right)) / (nl * nr))
    return math.degrees(2 * math.acos(min(1.0, dot)))


def summarize_track(track):
    result = {key: value for key, value in track.items() if key.endswith('_referencial')}
    for kind in ('pos', 'rot', 'scl'):
        if kind not in track:
            continue
        keys = track[kind]
        times = sorted(keys)
        values = [keys[t] for t in times]
        selected = sorted(set(times[::max(1, len(times) // 4)] + times[-1:]))
        result[kind] = {'key_count': len(keys), 'first_frame': times[0] if times else None,
                        'last_frame': times[-1] if times else None,
                        'range': [max(v[i] for v in values) - min(v[i] for v in values)
                                  for i in range(len(values[0]))] if values else [],
                        'samples': [[t, keys[t]] for t in selected]}
    return result


def cms_audit(path):
    data = path.read_bytes()
    signature, version, unknown8, count = struct.unpack_from('<4sIII', data)
    # A repeatable layout hypothesis. Field names intentionally stay unknown.
    # It fits this one file; it is not a qualified general CMS reader.
    rows = []
    if signature == b'CMS\0' and version == 4 and count == 19:
        for index in range(count):
            offset = 16 + index * 36
            values = struct.unpack_from('<2i3f4i', data, offset)
            rows.append({'offset': offset, 'unknown_ints_0': values[:2],
                         'unknown_floats': values[2:5], 'unknown_ints_1': values[5:]})
    tail = 16 + len(rows) * 36
    return {'source': evidence(path), 'signature_hex': signature.hex(),
            'version': version, 'unknown_offset8': unknown8, 'candidate_count_offset12': count,
            'candidate_rows36': rows, 'sequential_first_fields':
            [row['unknown_ints_0'][0] for row in rows] == list(range(count)),
            'tail_offset': tail, 'tail_words': [
                {'offset': off, 'u32': struct.unpack_from('<I', data, off)[0],
                 'f32': struct.unpack_from('<f', data, off)[0]}
                for off in range(tail, len(data) - 3, 4)],
            'classification': 'unknown_semantics_layout_hypothesis_only',
            'not_established': ['attachment bone', 'weapon/scabbard transform', 'weapon scale',
                                'camera interpretation', 'timing interpretation']}


def compare_decoders(path, old_animations, native_reader, pose):
    parsed = native_reader.read_lmt_file(path)
    old_by_id = {int(row['name'].rsplit('_', 1)[1]): row for row in old_animations}
    result = {'source': evidence(path), 'version': parsed.header.version,
              'slots': parsed.header.entry_count, 'actions': [], 'unsupported': []}
    aggregate = defaultdict(list)
    for action in parsed.actions:
        old = old_by_id[action.id]['bone_action']
        rows = []
        identities = Counter((t.header.bone_id, t.header.usage) for t in action.tracks)
        for index, track in enumerate(action.tracks):
            h = track.header
            if h.usage not in range(6):
                result['unsupported'].append({'action': action.id, 'track': index,
                                               'reason': 'unknown usage', 'usage': h.usage})
                continue
            kind = ('rot', 'pos', 'scl')[h.usage % 3]
            try:
                curve = pose.compile_pose_curve(track)
            except ValueError as error:
                result['unsupported'].append({'action': action.id, 'track': index,
                                               'reason': str(error)})
                continue
            old_keys = old.get(h.bone_id, {}).get(kind, {})
            errors = []
            worst = None
            for frame, value in old_keys.items():
                if not 0 <= frame <= action.header.frame_count - 1:
                    continue
                sampled = curve.sample(frame)
                legacy = (value[3], *value[:3]) if kind == 'rot' else value[:3]
                error = distance(legacy, sampled, kind == 'rot')
                if error is None:
                    continue
                errors.append(error)
                aggregate[kind].append(error)
                if worst is None or error > worst['error']:
                    worst = {'frame': frame, 'error': error, 'old': list(legacy),
                             'native_instruction_sampler': list(sampled)}
            row = {'record_index': index, 'bone': h.bone_id, 'usage': h.usage,
                   'kind': kind, 'codec': h.buffer_type, 'joint_type': h.joint_type,
                   'weight': h.weight, 'basis': h.basis,
                   'legacy_key_count': len(old_keys), 'native_key_count': len(curve.frames),
                   'native_frame_range': [curve.frames[0], curve.frames[-1]],
                   'stats': scalar_stats(errors), 'worst': worst}
            rows.append(row)
        result['actions'].append({'action_id': action.id,
                                  'native_frame_count': action.header.frame_count,
                                  'flags2': action.header.flags2,
                                  'duplicate_bone_usage': [list(key) for key, num in identities.items()
                                                           if num > 1],
                                  'tracks': rows})
    result['aggregate_error'] = {kind: scalar_stats(values) for kind, values in aggregate.items()}
    result['units'] = {'rot': 'degrees; normalized quaternion shortest rotation angle',
                       'pos': 'source rig units; centimeter convention used by conversion',
                       'scl': 'dimensionless Euclidean difference'}
    result['comparison_boundary'] = (
        'Raw source-track samples at legacy key times only. Native sampler is upstream '
        'CPU reproduction, not execution in the original game. This does not measure '
        'delivered UE skin error, layer/IK, constraints, root-tail semantics or attachment fit.')
    return result


def run_offline(out):
    legacy = module_from_path('_mhwi_audit_legacy_lmt', OLD / 'lmt/lmt_parser.py')
    native_reader, pose = load_native_modules()
    mappings = json.loads((ROOT / 'Scripts/MHWI/moveset_mapping.json').read_text(encoding='utf-8'))
    motion_roles = defaultdict(list)
    for name, definition in mappings['moves'].items():
        if definition.get('clip'):
            motion_roles[definition['clip']].append(name)
    sources = sorted((NATIVE / 'wp/swo/mot').rglob('*.lmt')) + [
        NATIVE / 'hm/wp/wp03/mot/w03_00/w03_00.lmt',
        NATIVE / 'hm/common/mot/co00_00/co00_00.lmt']
    hunter_models = sorted((NATIVE / 'pl').rglob('*.mod3'))
    protected = sources + hunter_models + list((UPSTREAM / 'core').rglob('*.py')) + [
                            Path(__file__).resolve(),
                            NATIVE / 'hm/wp/wp03/wp03_setting.cms',
                            NATIVE / 'wp/swo/swo001/mod/swo001.mod3',
                            NATIVE / 'wp/swo/swo001/mod/saya001.mod3', BLEND,
                            ROOT / 'Scripts/MHWI/attachment_fit.json',
                            OLD / 'lmt/lmt_parser.py', OLD / 'lmt/lmt_loader.py',
                            OLD / 'common/bone_rename.py',
                            UPSTREAM / 'core/formats/lmt/pose_evaluation.py',
                            UPSTREAM / 'LICENSE']
    before = {relative(path): evidence(path) for path in protected}
    summary = {'schema_version': 1, 'status': 'offline_source_audit_no_ue_asset_writes',
               'utc_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'sampler_rule': pose.RULE_VERSION, 'files': {}, 'mapped_moves': {},
               'helper_bones': {}, 'source_evidence_before': before,
               'limits': ['CMS field semantics unknown.',
                          'Native sampler is third-party reverse engineering; original game not run.',
                          'Existing fixed attachment scale/offsets are project fit values.',
                          'A source decoder difference is not yet a measured UE render defect.']}
    for path in sources:
        animations = legacy.LmtParser(str(path)).read()
        comparison = compare_decoders(path, animations, native_reader, pose)
        save(out, 'weapon-decoder-' + path.stem + '.json', comparison)
        parsed = native_reader.read_lmt_file(path)
        summary['files'][path.stem] = {
            'source': evidence(path), 'slots': parsed.header.entry_count,
            'valid_actions': parsed.action_count, 'tracks': parsed.track_count,
            'bone_ids': sorted({t.header.bone_id for a in parsed.actions for t in a.tracks}),
            'usages': dict(Counter(t.header.usage for a in parsed.actions for t in a.tracks)),
            'codecs': dict(Counter(t.header.buffer_type for a in parsed.actions for t in a.tracks)),
            'duplicate_bone_usage_actions': [a['action_id'] for a in comparison['actions']
                                            if a['duplicate_bone_usage']],
            'aggregate_error': comparison['aggregate_error'],
            'unsupported_count': len(comparison['unsupported'])}
        if path.stem.startswith('wg'):
            save(out, 'weapon-source-' + path.stem + '.json', {
                'source': evidence(path), 'actions': [
                    {**a, 'bone_action': {str(b): summarize_track(t)
                                          for b, t in a['bone_action'].items()}}
                    for a in animations]})
        if path.stem == 'w03_00':
            for action in comparison['actions']:
                name = f"w03_00_{action['action_id']:03}"
                focus = [track for track in action['tracks'] if track['bone'] in FOCUS_BONES]
                summary['helper_bones'][name] = [
                    track for track in focus if track['bone'] >= 247]
                if name in motion_roles:
                    summary['mapped_moves'][name] = {
                        'project_move_names': motion_roles[name], 'focus_tracks': focus,
                        'max_errors_by_kind': {
                            kind: max((t['stats']['max'] or 0 for t in action['tracks']
                                       if t['kind'] == kind), default=0)
                            for kind in ('pos', 'rot', 'scl')}}
    model = module_from_path('_mhwi_audit_mod3', OLD / 'mod3/mod3_parser.py')
    summary['weapon_models'] = {}
    for name in ('swo001', 'saya001'):
        path = NATIVE / f'wp/swo/swo001/mod/{name}.mod3'
        bones, meshes = model.Mod3Parser(str(path)).read()
        summary['weapon_models'][name] = {
            'source': evidence(path), 'bones': [
                {key: value for key, value in bone.items()
                 if key not in ('local_matrix', 'global_matrix')} for bone in bones]}
    summary['hunter_model_function_evidence'] = {}
    for path in hunter_models:
        bones, meshes = model.Mod3Parser(str(path)).read()
        rows = []
        for bone in bones:
            if bone.get('remap') not in FOCUS_BONES | {30, 48, 61}:
                continue
            chain = []
            parent_id = bone['parent']
            while 0 <= parent_id < len(bones):
                parent = bones[parent_id]
                chain.append({'array_id': parent_id, 'function': parent['function'],
                              'remap': parent.get('remap')})
                parent_id = parent['parent']
            rows.append({**{key: value for key, value in bone.items()
                            if key not in ('local_matrix', 'global_matrix')},
                         'parent_chain': chain})
        summary['hunter_model_function_evidence'][path.stem] = {'source': evidence(path),
                                                                'focus_bones': rows}
    extractor = module_from_path('_mhwi_audit_event_extractor',
                                 ROOT / 'Scripts/MHWI/extract_moveset_mapping.py')
    summary['hunter_weapon_motion_events'] = {}
    for name, event in extractor.lmt_events(NATIVE / 'hm/wp/wp03/mot/w03_00/w03_00.lmt').items():
        tracks = [{'group': group['name'], **track}
                  for group in event['groups'] for track in group['tracks']
                  if track['name'] == 'mWeaponMotionNo']
        if tracks:
            summary['hunter_weapon_motion_events'][name] = tracks
    summary['decoder_diagnosis'] = {
        'quantization': 'Legacy raw/(2**bits-1) differs from upstream native-instruction '
                        '(raw-8)/(2**bits-16); native arithmetic rounds float32.',
        'partial_quaternion': 'Legacy codecs 11/12/13 force absent XYZ components to zero; '
                              'upstream sampler retains interpolation-basis add components.',
        'large_rotation_examples': [
            {'clip': 'w03_00_129', 'bone': 48, 'codec': 12, 'max_degrees': 18.79975587345464,
             'meaning': 'function/remap 48; anatomical assignment requires model hierarchy; '
                        'source for RollStepSlash prefix'},
            {'clip': 'w03_00_173', 'bone': 30, 'codec': 11, 'max_degrees': 175.80528410668822,
             'meaning': 'function/remap 30; anatomical assignment requires model hierarchy'}],
        'applicability': 'Measured numeric differences justify a narrowly scoped conversion '
                        'patch investigation. They do not establish the source of large '
                        'whole-weapon attachment displacement or validate a replacement exporter.'}
    save(out, 'weapon-cms.json', cms_audit(NATIVE / 'hm/wp/wp03/wp03_setting.cms'))
    summary['source_evidence_after'] = {relative(path): evidence(path) for path in protected}
    summary['protected_sources_unchanged'] = before == summary['source_evidence_after']
    save(out, 'weapon-fidelity-summary.json', summary)
    print(json.dumps({'status': summary['status'], 'output': str(out),
                      'protected_sources_unchanged': summary['protected_sources_unchanged'],
                      'files': {name: {key: value for key, value in item.items()
                                       if key in ('valid_actions', 'aggregate_error', 'unsupported_count')}
                                for name, item in summary['files'].items()}}))
    if not summary['protected_sources_unchanged']:
        raise RuntimeError('A protected source changed during the audit')


def run_blender(out):
    import bpy
    arm = bpy.data.objects['Armature']
    initial = evidence(BLEND)
    result = {'source_blend': initial, 'hunter_bone_count': len(arm.data.bones),
              'hunter_helpers': {}, 'weapons': {}, 'poses': {},
              'matrix_note': 'armature space; distances in source rig centimeters'}
    result['hunter_focus_hierarchy'] = {}
    for index in sorted(FOCUS_BONES | {30, 48, 61}):
        name = f'bone_{index:03}'
        bone = arm.data.bones.get(name)
        if bone is None:
            continue
        chain = []
        parent = bone.parent
        while parent:
            chain.append(parent.name)
            parent = parent.parent
        result['hunter_focus_hierarchy'][name] = {
            'parent_chain': chain, 'head_local': list(bone.head_local),
            'tail_local': list(bone.tail_local)}
    for index in range(247, 255):
        bone = arm.data.bones.get(f'bone_{index:03}')
        result['hunter_helpers'][f'bone_{index:03}'] = {
            'present': bone is not None, 'parent': bone.parent.name if bone and bone.parent else None}
    for name in ('Armature_swo001', 'Armature_saya001'):
        weapon = bpy.data.objects[name]
        row = {'bones': {}, 'skin_groups': {}}
        for bone in weapon.data.bones:
            local = bone.parent.matrix_local.inverted() @ bone.matrix_local if bone.parent else bone.matrix_local
            row['bones'][bone.name] = {'parent': bone.parent.name if bone.parent else None,
                                       'local_position': list(local.translation)}
        for obj in bpy.data.objects:
            if obj.type != 'MESH' or not any(mod.type == 'ARMATURE' and mod.object == weapon
                                            for mod in obj.modifiers):
                continue
            for group in obj.vertex_groups:
                vertices = [v for v in obj.data.vertices
                            if any(g.group == group.index and g.weight > .001 for g in v.groups)]
                if vertices:
                    row['skin_groups'][obj.name + ':' + group.name] = {
                        'vertex_count': len(vertices),
                        'bounds_min': [min(v.co[i] for v in vertices) for i in range(3)],
                        'bounds_max': [max(v.co[i] for v in vertices) for i in range(3)]}
        result['weapons'][name] = row
    for index in (1, 2, 3, 101, 102, 104, 105, 106, 107, 108, 109, 127, 128, 129,
                  140, 170, 171, 172, 173, 174, 175, 176, 177, 178):
        name = f'w03_00_{index:03}'
        action = bpy.data.actions.get(name)
        if action is None:
            continue
        arm.animation_data.action = action
        rows = []
        for frame in sorted({int(action.frame_range[1] * f) for f in (0, .12, .25, .4, .6, .8, 1)}):
            bpy.context.scene.frame_set(frame)
            row = {'frame': frame, 'aux_vs_body': {}}
            for aux, body in ((247, 12), (248, 8), (249, 20), (250, 16), (252, 4)):
                a = arm.pose.bones[f'bone_{aux:03}'].matrix
                b = arm.pose.bones[f'bone_{body:03}'].matrix
                row['aux_vs_body'][f'{aux}-{body}'] = {
                    'position_distance': (a.translation - b.translation).length,
                    'rotation_distance_degrees': math.degrees(a.to_quaternion().rotation_difference(
                        b.to_quaternion()).angle)}
            rows.append(row)
        curve_bones = sorted({f.data_path.split('"')[1] for f in action.fcurves
                              if f.data_path.startswith('pose.bones[')})
        result['poses'][name] = {'frames': rows,
                                'curve_helpers': [b for b in curve_bones if b in result['hunter_helpers']],
                                'curves_for_missing_bones': [b for b in curve_bones if b not in arm.data.bones]}
    result['source_blend_after'] = evidence(BLEND)
    result['protected_blend_unchanged'] = initial == result['source_blend_after']
    save(out, 'weapon-blender-audit.json', result)
    print('WEAPON_BLENDER_AUDIT ' + json.dumps({'actions': len(result['poses']),
                                              'protected_blend_unchanged': result['protected_blend_unchanged']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--blender-phase', action='store_true')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if not out.is_relative_to((ROOT / 'Saved/MHWIImport').resolve()):
        raise ValueError('Audit output must stay below project Saved/MHWIImport')
    out.mkdir(parents=True, exist_ok=True)
    if args.blender_phase:
        run_blender(out)
    else:
        run_offline(out)


if __name__ == '__main__':
    main()
