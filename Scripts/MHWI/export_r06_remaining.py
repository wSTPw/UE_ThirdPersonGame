"""B10 source-sampled source-owner/custom-entry assets; authoring only, no tests."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_animation_source as native

W03 = [10, 11, 12, 13, 61, 62, 63, 113, 115, 116, 126, 130, 151, 221,
       332, 333, 334, *range(338, 350)]
COMMON = [70, 71, 72]


def run():
    import bpy
    out = native.BASE/'R06Remaining-20261025'
    out.mkdir(parents=True, exist_ok=True)
    manifest = out/'export-manifest.json'
    record = json.loads(manifest.read_text()) if manifest.exists() else dict(
        schema=1, tests_executed=False, clips=[], blocked=[],
        source_blend=native.evidence(native.BLEND), status='authoring')
    # Ancillary mirrored walk/sit reactions belong to R24. Canonical source
    # owners here request the constructor-proven standing 70/71/72 only.
    record['required_common_motions'] = COMMON
    record['ancillary_boundary'] = 'Mirrored walk/sit reaction variants are not requested by B10 source owners; keep prior blocked authoring evidence.'
    def save(): manifest.write_text(json.dumps(record, indent=2)+'\n')
    save()
    bpy.ops.wm.open_mainfile(filepath=str(native.BLEND))
    arm = bpy.data.objects['Armature']
    mesh = native.create_bind_reference_mesh(arm)
    bpy.context.scene.render.fps = 60
    for bank_name, numbers in (('w03_00', W03), ('co00_00', COMMON)):
        for motion in numbers:
            name = f'{bank_name}_{motion:03}'
            if any(row['clip']==name for row in record['clips']): continue
            path = out/(name+'.fbx')
            bank, source = native.load_action(name)
            try: evaluation = native.compiled_action(arm, name)
            except ValueError as error:
                record['blocked'].append(dict(clip=name, reason=str(error)))
                save()
                continue
            native.reset_pose(arm)
            action = native.build_action(arm, name, evaluation)
            arm.animation_data.action = action
            end = source.header.frame_count-1
            bpy.context.scene.frame_start, bpy.context.scene.frame_end = 0, max(1, end)
            bpy.context.scene.frame_set(0)
            bpy.ops.object.select_all(action='DESELECT')
            arm.hide_set(False)
            arm.select_set(True)
            mesh.select_set(True)
            bpy.context.view_layer.objects.active = arm
            bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
                object_types={'ARMATURE','MESH'}, add_leaf_bones=False,
                axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                bake_anim_step=1., bake_anim_simplify_factor=0.)
            record['clips'].append(dict(clip=name, bank=bank_name, motion=motion,
                frame_count=source.header.frame_count, loop_frame=source.header.loop_frame,
                source=native.evidence(native.SOURCES[bank_name]), fbx=native.evidence(path)))
            save()
            print('B10_AUTHORED', name, flush=True)
            arm.animation_data.action = None
            bpy.data.actions.remove(action)
    record['status'] = 'authored_not_tested'
    save()
    print('B10_AUTHORING_COMPLETE', len(record['clips']), 'blocked',len(record['blocked']), flush=True)


if __name__ == '__main__': run()
