"""Author isolated R06 source-sampled FBXs without running any verification.

Does not import the verification module, alter production exports, or save the
source blend. NeedsParent clips remain blocked until their original base is known.
Run with portable Blender --background --python <this file>.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_animation_source as native


def main(directory='R06Staging-20261025', motion_numbers=None):
    import bpy
    out = native.BASE/directory
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out/'export-manifest.json'
    if manifest_path.exists():
        raise RuntimeError('Preserve existing staging manifest; choose a new batch before re-export')
    policy = json.loads((native.ROOT/'Tools/MHW/native-link-motion-policy.json').read_text(encoding='utf8'))
    clips = sorted({r['connector_motion'] for r in policy['references']}) if motion_numbers is None else motion_numbers
    manifest = dict(schema=1, status='authored_pending_next_stage_tests', tests_executed=False,
        source_blend=native.evidence(native.BLEND), source_lmt=native.evidence(native.SOURCES['w03_00']),
        clips=[], blocked=[], production_assets_written=False)
    def save():
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    save()
    bpy.ops.wm.open_mainfile(filepath=str(native.BLEND))
    arm = bpy.data.objects['Armature']
    bind_mesh = native.create_bind_reference_mesh(arm)
    bpy.context.scene.render.fps = 60
    for number in clips:
        name = f'w03_00_{number:03}'
        path = out/(name+'.fbx')
        if path.exists():
            raise RuntimeError('Refusing to overwrite staging FBX: '+str(path))
        bank, source = native.load_action(name)
        try:
            evaluation = native.compiled_action(arm, name)
        except ValueError as error:
            manifest['blocked'].append(dict(clip=name, reason=str(error), tests_executed=False))
            save()
            print('R06_SOURCE_BLOCKED', name, str(error), flush=True)
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
        bind_mesh.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
            object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
            axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
            bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
            bake_anim_step=1., bake_anim_simplify_factor=0.)
        manifest['clips'].append(dict(clip=name, motion=number,
            frame_count=source.header.frame_count, last_source_frame=end,
            loop_frame=source.header.loop_frame, flags2=source.header.flags2,
            shared_curve_owner=(native.shared_curve_owner(bank, source).id
                if native.shared_curve_owner(bank, source) is not None else None),
            native_curve_table_offset=source.header.fcurve_offset,
            fbx=native.evidence(path), tests_executed=False,
            status='fbx_authored_not_imported_not_verified'))
        save()
        print('R06_AUTHORED', name, 'tests_executed=False', flush=True)
        arm.animation_data.action = None
        bpy.data.actions.remove(action)
    save()
    print('R06_EXPORT_COMPLETE', len(manifest['clips']), 'blocked', len(manifest['blocked']), flush=True)


if __name__ == '__main__':
    main()
