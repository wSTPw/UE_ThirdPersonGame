"""Sample source Blender actions for moveset identification; no UE execution."""
import bpy
import json
from pathlib import Path

base = Path(__file__).resolve().parents[2]
arm = bpy.data.objects['Armature']
names = ['bone_root', 'bone_000', 'bone_001', 'bone_002', 'bone_003', 'bone_004',
         'bone_005', 'bone_006', 'bone_007', 'bone_008', 'bone_009', 'bone_010',
         'bone_011', 'bone_012', 'bone_013', 'bone_014', 'bone_015', 'bone_016',
         'bone_017', 'bone_018', 'bone_019', 'bone_020', 'bone_021',
         'bone_247', 'bone_248', 'bone_249', 'bone_250', 'bone_251', 'bone_252', 'bone_253', 'bone_254']
result = {'bones': {}, 'actions': {}}
for bone in arm.data.bones:
    if bone.name in names:
        result['bones'][bone.name] = bone.parent.name if bone.parent else None
for action in bpy.data.actions:
    if not (action.name.startswith('w03_00_') or action.name.startswith('co00_00_')):
        continue
    arm.animation_data.action = action
    frames = [int(action.frame_range[1] * f) for f in [0, .12, .25, .4, .6, .8, 1]]
    entries = []
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        entries.append({'frame': frame, 'bones': {name: list(arm.matrix_world @ arm.pose.bones[name].head) for name in result['bones']}})
    result['actions'][action.name] = entries
out = base / 'Saved/MHWI/source-poses.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result), encoding='utf8')
print(out)
