import unreal,json
from pathlib import Path
root=Path(unreal.Paths.project_dir());p=unreal.GameplayStatics.get_player_character(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),0)
file=root/'Scripts/MHWI/attachment_fit.json';data=json.loads(file.read_text(encoding='utf8'))
# Back mount follows the chest's own back plane through stance changes.
for key in ['scabbard_relative_transform','sheathed_weapon_relative_transform']:
 data['transforms'][key]={'location':[-12,-25,-15],'rotation':[0,-40,0],'scale':[.7,.7,.7]}
# The fixed hold pose has two real grip points: left hand at the sheath mouth,
# right hand along the long hilt. Solve its axis in world space then store left-wrist local.
left=p.mesh.get_socket_transform('bone_008');right=p.mesh.get_socket_transform('bone_012')
l=left.transform_location(unreal.Vector(-7,2,0));r=right.transform_location(unreal.Vector(-7,2,0))
axis=(l-r).normal();normal=unreal.Vector(0,0,1).cross(axis).normal()
rot=unreal.MathLibrary.make_rot_from_yz(axis,normal)
origin=l-axis*(21*.7)
rel=unreal.MathLibrary.make_relative_transform(unreal.Transform(location=origin,rotation=rot,scale=unreal.Vector(.7,.7,.7)),left)
e=rel.rotation.rotator()
for key in ['special_scabbard_relative_transform','special_weapon_relative_transform']:
 data['transforms'][key]={'location':list(rel.translation.to_tuple()),'rotation':[e.pitch,e.yaw,e.roll],'scale':[.7,.7,.7]}
data['special_fit']={'left_grip':list(l.to_tuple()),'right_grip':list(r.to_tuple()),'mouth_source_y':21,'hilt_grip_source_y':21-(l-r).length()/.7,'method':'two measured hold-pose palm points; fixed wrist-local transform'}
file.write_text(json.dumps(data,indent=2),encoding='utf8')
