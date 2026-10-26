"""Export independently validated source-sampled hunter FBXs in NativeFidelity.

Usage (portable Blender, source blend is read only):
  blender --background --python Scripts/MHWI/export_native_animation.py -- --clips w03_00_129
  ... -- --focus
  ... -- --all
Output is confined to ArtSource/ThirdParty/MHWLongSword/NativeFidelity.
NeedsParent entries are explicitly blocked pending original parent-context proof.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_animation_source as native
import verify_native_animation as verify


def main():
    import bpy
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clips', nargs='+')
    parser.add_argument('--focus', action='store_true')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--fbx-step', type=float, default=1.)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    native.OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest_path = native.OUTPUT / 'export-manifest.json'
    deps_before = native.dependency_evidence()
    manifest = json.loads(manifest_path.read_text(encoding='utf8')) if args.resume and manifest_path.exists() else {
        'schema_version': 1, 'clips': [], 'blocked': []}
    manifest.update(utc_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_dependencies=deps_before, sampler_rule=native.native_modules()[1].RULE_VERSION,
        source_space='Feuleur centimeter Y-up bind hierarchy; object +90X/.01; raw root/action convention retained',
        target_space='Existing 225 bones, bone_root identity bind; FBX -Y forward Z up, unit scale applied',
        partial_base_policy='NeedsParent blocked; otherwise explicit copied skeleton REST in absent components',
        qualification_boundary='Native-instruction CPU sampler, not execution in original game; no IK/layers/attachment/parent logic',
        fbx_sample_step=args.fbx_step, contains_bind_reference_mesh=True,
        bind_reference_mesh='Disposable 675-vertex/225-triangle skin, all original bind matrices; ignore geometry on UE animation import')
    tool_evidence = [native.evidence(native.ROOT/'Scripts/MHWI'/name) for name in
                    ('native_animation_source.py', 'export_native_animation.py', 'verify_native_animation.py')]
    manifest['exporter_tool_evidence'] = tool_evidence
    manifest['root_qualification'] = ('Native root samples projected using the existing production raw action-space '
        'convention. This preserves REF_POSE basis compatibility; original game equipment/world placement is separate.')
    bpy.ops.wm.open_mainfile(filepath=str(native.BLEND))
    arm = bpy.data.objects['Armature']
    bind_mesh = native.create_bind_reference_mesh(arm)
    if len(arm.data.bones) != 225:
        raise ValueError('Expected unchanged production 225-bone rig')
    rig = native.inspect_rig(arm)
    (native.OUTPUT / 'rig-bind.json').write_text(json.dumps(rig, indent=2), encoding='utf8')
    bpy.context.scene.render.fps = 60
    names = args.clips or native.FOCUS
    if args.all:
        reader, _ = native.native_modules()
        names = [f'w03_00_{a.id:03}' for a in reader.read_lmt_file(native.SOURCES['w03_00']).actions]
        names += sorted(p.stem for p in (native.BASE/'Converted/Common').glob('*.fbx'))
        mapping = json.loads((native.ROOT/'Scripts/MHWI/moveset_mapping.json').read_text(encoding='utf8'))
        used = sorted({row['clip'] for row in mapping['moves'].values() if row.get('clip')})
        priority = native.FOCUS + [name for name in names if name.startswith('co00_00_')] + used
        names = list(dict.fromkeys([*priority, *names]))
    completed = {item['clip'] for item in manifest['clips'] if item.get('passed')
        and (native.ROOT/item['fbx']).is_file()
        and native.evidence(native.ROOT/item['fbx'])['sha256'] == item['sha256']}
    for name in names:
        started = time.perf_counter()
        if args.resume and name in completed:
            continue
        bank, source = native.load_action(name)
        family, index = name.rsplit('_', 1)
        try:
            evaluation = native.compiled_action(arm, name)
        except ValueError as error:
            mapping = native.function_map(arm)
            raw_evaluation = native.native_modules()[1].compile_pose_evaluation(source, mapping, version=bank.header.version)
            selected = {(b.target or 'bone_root', b.usage % 3) for b in raw_evaluation.bindings}
            missing = [(b.name, kind) for b in arm.data.bones for kind in range(3)
                       if (b.name, kind) not in selected]
            blocked = dict(clip=name, bank=family, index=int(index), flags2=source.header.flags2,
                reason=str(error), eligible_for_runtime=False, missing_components=missing,
                frame_count=source.header.frame_count, duration=(source.header.frame_count-1)/60)
            blocked['missing_components_sha256'] = hashlib.sha256(
                json.dumps(missing, separators=(',', ':')).encode()).hexdigest()
            manifest['blocked'] = [b for b in manifest['blocked'] if b['clip'] != name] + [blocked]
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
            print('NATIVE_BLOCKED', name, str(error), flush=True)
            continue
        native.reset_pose(arm)
        legacy = bpy.data.actions.get(name)
        action = native.build_action(arm, name, evaluation)
        arm.animation_data.action = action
        result = verify.verify_action(arm, evaluation, action, legacy,
                                     quarter_frames=not args.all or name in native.FOCUS)
        if not result['passed']:
            (native.OUTPUT / (name+'-failed.json')).write_text(json.dumps(result, indent=2), encoding='utf8')
            raise RuntimeError(f'Native source matrix check failed: {name}: {result}')
        end = source.header.frame_count-1
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = 0, max(1, end)
        bpy.context.scene.frame_set(0)
        bpy.ops.object.select_all(action='DESELECT')
        arm.hide_set(False)
        arm.select_set(True)
        bind_mesh.select_set(True)
        bpy.context.view_layer.objects.active = arm
        folder = native.OUTPUT / ('Common' if family == 'co00_00' else 'Animations')
        folder.mkdir(exist_ok=True)
        path = folder/(name+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
            object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
            axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
            bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
            bake_anim_step=args.fbx_step, bake_anim_simplify_factor=0.0)
        roundtrip = verify.verify_fbx(path, arm, source.header.frame_count)
        row = dict(clip=name, bank=family, index=int(index),
            fbx=str(path.relative_to(native.ROOT).as_posix()),
            frame_count=source.header.frame_count, duration=end/60,
            loop_frame=source.header.loop_frame, flags2=source.header.flags2,
            sha256=native.evidence(path)['sha256'], bone_count=len(arm.data.bones),
            source_verification=result, fbx_verification=roundtrip,
            passed=result['passed'] and roundtrip['passed'],
            eligible_for_runtime=result['passed'] and roundtrip['passed'])
        row['tool_evidence'] = tool_evidence
        row['elapsed_seconds'] = time.perf_counter()-started
        manifest['clips'] = [r for r in manifest['clips'] if r['clip'] != name] + [row]
        manifest['source_dependencies_after'] = native.dependency_evidence()
        manifest['protected_sources_unchanged'] = deps_before == manifest['source_dependencies_after']
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
        print('NATIVE_EXPORTED', name, 'passed='+str(row['passed']), 'source_max_cm='+str(result['position_cm']['max']),
              'fbx_max_cm='+str(roundtrip['position_cm']['max']), flush=True)
        if not row['passed'] or not manifest['protected_sources_unchanged']:
            raise RuntimeError('Export or protected-source verification failed: '+name)
        arm.animation_data.action = None
        bpy.data.actions.remove(action)
    manifest['passed'] = all(c.get('passed') for c in manifest['clips']) and manifest.get('protected_sources_unchanged', False)
    manifest['blocked_count'] = len(manifest['blocked'])
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print('NATIVE_COMPLETE', len(manifest['clips']), 'blocked', len(manifest['blocked']), flush=True)


if __name__ == '__main__':
    main()
