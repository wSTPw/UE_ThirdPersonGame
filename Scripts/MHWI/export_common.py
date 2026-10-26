"""Export the minimal source common locomotion/roll clips for the MHWI pawn."""
import bpy
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/Converted'
bpy.ops.wm.open_mainfile(filepath=str(BASE / 'MHW_Hunter_LongSword_Actions.blend'))
master = bpy.data.objects['Armature']
output = BASE / 'Common'
output.mkdir(exist_ok=True)
# Explicit clip arguments export only the requested additions, without rewriting old FBXs.
clips = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [
    'co00_00_001', 'co00_00_203', 'co00_00_090', 'co00_00_130']
for name in clips:
    action = bpy.data.actions.get(name)
    if not action:
        raise RuntimeError('Required common clip missing: ' + name)
    master.animation_data.action = None
    for bone in master.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
    master.animation_data.action = action
    bpy.context.scene.render.fps = 60
    bpy.context.scene.frame_start = int(action.frame_range[0])
    bpy.context.scene.frame_end = int(action.frame_range[1])
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    bpy.ops.object.select_all(action='DESELECT')
    master.hide_set(False)
    master.select_set(True)
    bpy.context.view_layer.objects.active = master
    bpy.ops.export_scene.fbx(filepath=str(output / (name + '.fbx')), use_selection=True,
        object_types={'ARMATURE'}, add_leaf_bones=False, axis_forward='-Y', axis_up='Z',
        apply_unit_scale=True, bake_anim=True, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False, bake_anim_step=1, bake_anim_simplify_factor=0.0)
    print('COMMON_EXPORTED', name, flush=True)
