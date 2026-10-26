"""Independent FBX round-trip checks against the delivered static weapon skeleton.

Run with portable Blender --background --factory-startup --python-exit-code 1.
All reads are local. Writes one Saved report; no source or UE asset writes.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_animation_source as sampling

BASE = ROOT / 'ArtSource/ThirdParty/MHWLongSword'
REPORT = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024'


def delete_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def import_fbx(path):
    previous = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=True,
                             ignore_leaf_bones=False, automatic_bone_orientation=False)
    return next(obj for obj in bpy.data.objects if obj not in previous and obj.type == 'ARMATURE')


def run():
    manifest = json.loads((REPORT / 'weapon-animation-manifest.json').read_text(encoding='utf-8'))
    delete_scene()
    static = import_fbx(BASE / 'Converted/swo001.fbx')
    static_rig = sampling.inspect_rig(static)
    rows = []
    reader, pose = sampling.native_modules()
    bank = reader.read_lmt_file(BASE / 'nativePC/wp/swo/mot/wg03_00/wg03_00.lmt')
    for clip in manifest['clips']:
        path = ROOT / clip['fbx']['path']
        arm = import_fbx(path)
        rig = sampling.inspect_rig(arm)
        same_names = set(rig['bones']) == set(static_rig['bones'])
        same_parent = all(bone['parent'] == static_rig['bones'][name]['parent']
                          for name, bone in rig['bones'].items())
        bind_max = max(abs(v - static_rig['bones'][name]['local_matrix'][r][c])
                       for name, bone in rig['bones'].items()
                       for r, row in enumerate(bone['local_matrix']) for c, v in enumerate(row))
        # Independently compile fresh native curves. Compare the source's bone 2
        # absolute local matrix with imported FBX parent-local bone transforms.
        source = next(action for action in bank.actions if action.id == clip['motion_no'])
        curves = {track.header.usage: pose.compile_pose_curve(track) for track in source.tracks}
        from mathutils import Matrix, Quaternion, Vector
        samples = []
        for frame in range(source.header.frame_count):
            # FBX importer uses its normal one-based Blender action convention.
            bpy.context.scene.frame_set(frame + 1)
            bone = arm.pose.bones['bone_002']
            local = bone.parent.matrix.inverted() @ bone.matrix
            translation = Vector(curves[1].sample(frame))
            rotation = Quaternion(curves[0].sample(frame))
            scale = Vector(curves[2].sample(frame))
            expected = Matrix.LocRotScale(translation, rotation, scale)
            # FBX importer may place a fixed reorientation on each bone. Compare
            # rest-relative changes in its own axes against the source-rig rest.
            source_rest = manifest['original_rig']['bones']['bone_002']['local_matrix']
            source_rest = Matrix(source_rest)
            source_delta = source_rest.inverted() @ expected
            imported_rest = Matrix(rig['bones']['bone_002']['local_matrix'])
            imported_delta = imported_rest.inverted() @ local
            translation_error = (source_delta.translation - imported_delta.translation).length
            samples.append({'source_frame': frame, 'translation_error_cm': translation_error,
                            'source_delta_translation': list(source_delta.translation),
                            'fbx_delta_translation': list(imported_delta.translation)})
        max_translation = max(row['translation_error_cm'] for row in samples)
        passed = same_names and same_parent and bind_max < 0.001 and max_translation < 0.001
        rows.append({'clip': clip['clip'], 'same_bone_names': same_names,
                     'same_parents': same_parent, 'rest_local_matrix_max_error': bind_max,
                     'frame_count': len(samples), 'bone002_translation_max_error_cm': max_translation,
                     'samples': samples[::max(1, len(samples) // 4)], 'passed': passed})
    result = {'status': 'offline_fbx_roundtrip_not_ue_validation',
              'passed': all(row['passed'] for row in rows), 'clips': rows,
              'static_weapon_fbx': sampling.evidence(BASE / 'Converted/swo001.fbx'),
              'limits': ['Verifies static skeleton match and internal translated function2 only.',
                         'Does not establish source equipment parent placement or UE imported sampling.']}
    (REPORT / 'weapon-fbx-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('NATIVE_WEAPON_FBX_VERIFY ' + json.dumps({'passed': result['passed'], 'clips': len(rows)}))
    if not result['passed']:
        raise AssertionError('Native weapon roundtrip failed; inspect report')


if __name__ == '__main__':
    run()
