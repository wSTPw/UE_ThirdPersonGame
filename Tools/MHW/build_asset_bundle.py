"""Create a common hunter rig and source actions; optionally export LS actions.

Run with the project-local portable Blender, --background --factory-startup.
Uses the unmodified Feuleur MHW tool suite 1.3.9 (MIT).
"""
import argparse
import importlib
import json
import logging
from pathlib import Path
import sys
import types

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
ADDON = ROOT / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main'
BASE = ROOT / 'ArtSource/ThirdParty/MHWLongSword'
NATIVE = BASE / 'nativePC'
OUT = BASE / 'Converted'
OUT.mkdir(exist_ok=True)
package = types.ModuleType('mhw_suite')
package.__path__ = [str(ADDON)]
sys.modules['mhw_suite'] = package
load_mod3 = importlib.import_module('mhw_suite.mod3.mod3_loader').load_mod3
load_lmt = importlib.import_module('mhw_suite.lmt.lmt_loader').load_lmt
load_mrl3 = importlib.import_module('mhw_suite.mrl3.mrl3_loader').load_mrl3
logging.basicConfig(level=logging.WARNING)
parser = argparse.ArgumentParser()
parser.add_argument('--export-longsword', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps = 60
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0
report = dict(source_game='Monster Hunter World: Iceborne (local installation)',
              status='conversion_only_not_ue_validated', fps=60, parts=[], actions=[],
              material_errors=[], rest_pose_differences=[], rig_adjustments=[], exports=[])
inventory = json.loads((BASE / 'source-inventory.json').read_text(encoding='utf-8'))
animated_bones = {'bone_' + str(i).zfill(3) for item in inventory['animations']
                  for i in item['bone_ids'] if i >= 0}
with bpy.data.libraries.load(str(ADDON / 'mrl3/materials_groups.blend'), link=False) as (src, dst):
    dst.node_groups = src.node_groups
parts = []
for path in sorted((NATIVE / 'pl').rglob('*.mod3')):
    objects = load_mod3(str(path), LOD=0, fix_rotation=True, fix_scale=True,
                        rename_bones=False, connect_bones=False)
    armature = next(obj for obj in objects if obj.type == 'ARMATURE')
    parts.append((path, armature, [obj for obj in objects if obj.type == 'MESH']))
    report['parts'].append(dict(source=str(path.relative_to(NATIVE)), bones=len(armature.data.bones)))
    try:
        load_mrl3(str(NATIVE), str(path.with_suffix('.mrl3')), use_loaded_tex=True, use_png_cache=True)
    except Exception as error:
        report['material_errors'].append(dict(source=str(path), error=str(error)))

master = next(armature for path, armature, meshes in parts if '/body/' in path.as_posix())
master.name = 'Armature'
master.data.name = 'MHW_Hunter_Skeleton'
for path, armature, meshes in parts:
    if armature == master:
        continue
    # Face MOD3 is centred on the head; armour MOD3s use the body origin.
    # Move both bind matrices and vertices into the body coordinate system.
    anchor = next((name for name in ('bone_000', 'bone_003', 'bone_002', 'bone_013', 'bone_017')
                   if name in armature.data.bones and name in master.data.bones), None)
    if anchor:
        alignment = master.data.bones[anchor].matrix_local @ armature.data.bones[anchor].matrix_local.inverted()
        if max(abs(alignment[r][c] - Matrix.Identity(4)[r][c])
               for r in range(4) for c in range(4)) > 0.01:
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='EDIT')
            for edit_bone in armature.data.edit_bones:
                edit_bone.transform(alignment)
            bpy.ops.object.mode_set(mode='OBJECT')
            for mesh in meshes:
                mesh.data.transform(alignment)
            report['rig_adjustments'].append(dict(part=path.stem, anchor=anchor,
                operation='align_part_bind_origin', translation=list(alignment.to_translation())))
    # Cloth/attachment IDs are local to each equipment piece, unlike motion IDs.
    for bone in list(armature.data.bones):
        if bone.name not in master.data.bones or bone.name in animated_bones or bone.name == 'bone_root':
            continue
        delta = max(abs(master.data.bones[bone.name].matrix_local[r][c] - bone.matrix_local[r][c])
                    for r in range(4) for c in range(4))
        if delta > 0.01:
            old_name = bone.name
            bone.name = path.stem + '_' + old_name
            for mesh in meshes:
                if old_name in mesh.vertex_groups:
                    mesh.vertex_groups[old_name].name = bone.name
            report['rig_adjustments'].append(dict(part=path.stem, operation='namespace_attachment_bone',
                                                 original=old_name, renamed=bone.name))
    bpy.context.view_layer.objects.active = master
    bpy.ops.object.mode_set(mode='EDIT')
    added = set()
    for bone in armature.data.bones:
        if bone.name in master.data.edit_bones:
            existing = master.data.edit_bones[bone.name]
            delta = max(abs(existing.matrix[r][c] - bone.matrix_local[r][c])
                        for r in range(4) for c in range(4))
            if delta > 0.01:
                report['rest_pose_differences'].append(dict(part=path.stem, bone=bone.name, max_delta=delta))
            continue
        new = master.data.edit_bones.new(bone.name)
        new.matrix = bone.matrix_local
        new.length = bone.length
        new.inherit_scale = bone.inherit_scale
        added.add(bone.name)
    for bone in armature.data.bones:
        if bone.name in added and bone.parent:
            master.data.edit_bones[bone.name].parent = master.data.edit_bones[bone.parent.name]
    bpy.ops.object.mode_set(mode='OBJECT')
for path, armature, meshes in parts:
    for mesh in meshes:
        mesh.parent = master
        for modifier in mesh.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.object = master
    if armature != master:
        bpy.data.objects.remove(armature, do_unlink=True)
for bone in master.pose.bones:
    bone.rotation_mode = 'QUATERNION'
master.animation_data_create()

metadata = {item['name']: item for item in inventory['animations']}
for relative in ['hm/wp/wp03/mot/w03_00/w03_00.lmt', 'hm/common/mot/co00_00/co00_00.lmt']:
    load_lmt(str(NATIVE / relative), master.data, set_fake_user=True)
for action in bpy.data.actions:
    if action.name in metadata:
        action['source_lmt'] = metadata[action.name]['source']
        action['source_has_root_track'] = metadata[action.name]['root_track']
        action['source_fps'] = 60
        report['actions'].append(dict(name=action.name, frames=list(action.frame_range),
                                     source_has_root_track=metadata[action.name]['root_track']))

def reset_pose():
    master.animation_data.action = None
    for bone in master.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def export(path, objects, animation=False):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
        object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
        axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
        bake_anim=animation, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_step=1, bake_anim_simplify_factor=0.0,
        path_mode='COPY', embed_textures=False)
    report['exports'].append(str(path.relative_to(BASE)))


reset_pose()
hunter_objects = [master] + [obj for _, _, meshes in parts for obj in meshes]
export(OUT / 'SK_MHW_Hunter_pl001.fbx', hunter_objects)
weapon_objects = []
for path in sorted((NATIVE / 'wp/swo/swo001/mod').glob('*.mod3')):
    objects = load_mod3(str(path), LOD=0, fix_rotation=True, fix_scale=True,
                        rename_bones=False, connect_bones=False)
    weapon_objects.extend(objects)
    try:
        load_mrl3(str(NATIVE), str(path.with_suffix('.mrl3')), use_loaded_tex=True, use_png_cache=True)
    except Exception as error:
        report['material_errors'].append(dict(source=str(path), error=str(error)))
    export(OUT / (path.stem + '.fbx'), objects)

for obj in weapon_objects:
    obj.hide_set(True)
    obj.hide_render = True
reset_pose()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'MHW_Hunter_LongSword_Actions.blend'))
if args.export_longsword:
    animations_out = OUT / 'Animations'
    animations_out.mkdir(exist_ok=True)
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        if not action.name.startswith('w03_00_'):
            continue
        reset_pose()
        master.animation_data.action = action
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        export(animations_out / (action.name + '.fbx'), [master], animation=True)
        print('EXPORTED_ACTION', action.name, flush=True)
report['bones'] = len(master.data.bones)
report['armature_name'] = master.name
report['root_bone'] = 'bone_root'
(BASE / 'conversion-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('BUNDLE_CREATED', len(report['actions']), 'actions', report['bones'], 'bones', flush=True)
