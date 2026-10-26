"""Source-pose contact evidence for MHWI whole-weapon transfers.

``audit_source_contacts()`` is read-only for the editor and production assets.
It never starts/stops PIE, changes defaults, or saves an Unreal package. The
only output is Saved/MHWIImport/WeaponTransfer-20261024/source-contacts.json.
Fixed mount and palm points are project fitting, not decoded game transforms.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path


def audit_source_skin():
    """Run in background Blender with the original .blend open; never saves it."""
    import bpy
    root = Path(__file__).resolve().parents[2]
    source = Path(bpy.data.filepath)

    def source_hash():
        digest = hashlib.sha256()
        with source.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                digest.update(block)
        return digest.hexdigest()

    before = source_hash()
    arm = bpy.data.objects['Armature_swo001']
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and any(
        m.type == 'ARMATURE' and m.object == arm for m in o.modifiers))
    groups = {g.index: g.name for g in mesh.vertex_groups}
    rows = []
    for reference_y in (-12., -40., -55., -60., -63., -66.485203):
        vertices = sorted(mesh.data.vertices,
            key=lambda v: v.co.x*v.co.x + v.co.y*v.co.y + (v.co.z-reference_y)**2)[:12]
        weights = []
        for v in vertices:
            total = sum(g.weight for g in v.groups)
            weight = sum(g.weight for g in v.groups if groups[g.group] == 'bone_002') / total
            normalized = {groups[g.group]: g.weight/total for g in v.groups}
            assert not any(w > .00001 and name not in ('bone_001', 'bone_002')
                           for name, w in normalized.items()), normalized
            weights.append(dict(index=v.index, xyz=list(v.co), bone002_weight=weight,
                                skin_weights=normalized))
        rows.append(dict(reference_y=reference_y, vertices=weights,
                         bone002_mean_weight=sum(v['bone002_weight'] for v in weights)/len(weights)))
    output = root / 'Saved/MHWIImport/WeaponTransfer-20261024'
    output.mkdir(parents=True, exist_ok=True)
    (output/'source-grip-skin.json').write_text(json.dumps(rows, indent=2), encoding='utf8')
    after = source_hash()
    (output/'source-grip-skin-provenance.json').write_text(json.dumps(dict(
        source=source.relative_to(root).as_posix(), source_sha256_before=before,
        source_sha256_after=after, protected_source_unchanged=before == after,
        mesh=mesh.name, vertex_count=len(mesh.data.vertices),
        method='12 nearest source surface vertices; normalized bone001/002 weights',
        reference_axis='UE component Y maps to source mesh Z'), indent=2), encoding='utf8')
    assert before == after, 'Protected original blend changed during read-only grip audit'
    print('MHWI_GRIP_SKIN '+json.dumps([{k:v for k,v in r.items() if k!='vertices'} for r in rows]))


def audit_source_contacts():
    import unreal

    root = Path(unreal.Paths.project_dir())
    fit = json.loads((root / 'Scripts/MHWI/attachment_fit.json').read_text(encoding='utf8'))
    library = unreal.AnimPoseExtensions
    options = unreal.AnimPoseEvaluationOptions(
        extract_root_motion=True, incorporate_root_motion_into_pose=False)
    output = root / 'Saved/MHWIImport/WeaponTransfer-20261024'
    output.mkdir(parents=True, exist_ok=True)

    def transform(value):
        return unreal.Transform(location=unreal.Vector(*value['location']),
            rotation=unreal.Rotator(pitch=value['rotation'][0], yaw=value['rotation'][1],
                                    roll=value['rotation'][2]),
            scale=unreal.Vector(*value['scale']))

    def serial(t):
        return dict(location=list(t.translation.to_tuple()),
                    quaternion=[t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w],
                    scale=list(t.scale3d.to_tuple()))

    report = dict(schema_version=1, assets_read_only=True, notes=[
        'Pose sampling reads exact production skeleton and qualified native sequences.',
        'Right palm(-7,2,0), left palm(+7,2,0), sword grip(0,-12,0), sheath mouth(0,21,0) are project reference points.',
        'Hand bind evidence confirms opposite X directions; the old shared left/right marker was outside the left hand.',
        'No native runtime attachment event or original initial placement is inferred.'], clips={})
    for index in (2, 3, 306, 307, 308, 309, 310, 311, 110):
        qualified = index not in (309, 310, 311)
        prefix = '/Game/MHWI/Animations/NativeFidelity/LongSword' if qualified else '/Game/MHWI/Animations/LongSword'
        path = f'{prefix}/A_w03_00_{index:03}'
        sequence = unreal.load_asset(path)
        assert isinstance(sequence, unreal.AnimSequence), path
        end = int(round(sequence.get_play_length() * 60))
        frames = range(0, min(end, 100) + 1)
        rows = []
        for frame in frames:
            pose = library.get_anim_pose_at_time(sequence, frame / 60., options)
            bones = {name: library.get_bone_pose(pose, name, unreal.AnimPoseSpaces.WORLD)
                     for name in ('bone_002', 'bone_008', 'bone_012')}
            left = bones['bone_008'].transform_location(unreal.Vector(7, 2, 0))
            right = bones['bone_012'].transform_location(unreal.Vector(-7, 2, 0))
            back = unreal.MathLibrary.compose_transforms(
                transform(fit['transforms']['scabbard_relative_transform']), bones['bone_002'])
            drawn = unreal.MathLibrary.compose_transforms(
                transform(fit['transforms']['weapon_relative_transform']), bones['bone_012'])
            special = unreal.MathLibrary.compose_transforms(
                transform(fit['transforms']['special_scabbard_relative_transform']), bones['bone_008'])
            row = dict(frame=frame, bones={name: serial(t) for name, t in bones.items()},
                       palms=dict(left=list(left.to_tuple()), right=list(right.to_tuple())),
                       back=serial(back), drawn=serial(drawn), special=serial(special),
                       errors_cm={
                'back_grip_right': (back.transform_location(unreal.Vector(0, -12, 0))-right).length(),
                'back_mouth_left': (back.transform_location(unreal.Vector(0, 21, 0))-left).length(),
                'special_mouth_left': (special.transform_location(unreal.Vector(0, 21, 0))-left).length(),
                'special_hilt_right': (special.transform_location(unreal.Vector(
                    0, fit['special_fit']['hilt_grip_source_y'], 0))-right).length(),
                'drawn_grip_right': (drawn.transform_location(unreal.Vector(0, -12, 0))-right).length()})
            rows.append(row)
        minimum = {key: min(rows, key=lambda r: r['errors_cm'][key])['frame']
                   for key in rows[0]['errors_cm']}
        report['clips'][str(index)] = dict(asset=path, qualified_sampler=qualified,
                                          duration=sequence.get_play_length(), frames=rows,
                                          minimum_error_frames=minimum)
    # Preserve the historical 845-frame report that used the incorrect shared marker.
    (output / 'source-contacts-mirrored-palms.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    summary = {k: dict(frames=len(v['frames']), minimum_error_frames=v['minimum_error_frames'],
                      last_errors_cm=v['frames'][-1]['errors_cm']) for k, v in report['clips'].items()}
    unreal.log('MHWI_WEAPON_TRANSFER_CONTACTS '+json.dumps(summary))
    return summary


if __name__ == '__main__':
    audit_source_skin()
