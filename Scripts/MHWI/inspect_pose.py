import unreal,json
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_character(w,0)
r={'actor':str(p.get_actor_transform()),'mesh':str(p.mesh.get_socket_transform(unreal.Name())),'bones':{n:str(p.mesh.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT)) for n in ['bone_root','bone_000','bone_003','bone_013','bone_017','bone_012','bone_008']}}
r['materials']=[str(p.mesh.get_material(i)) for i in range(p.mesh.get_num_materials())]
Path(unreal.Paths.project_saved_dir(),'MHWIImport/pose-inspect.json').write_text(json.dumps(r,indent=2),encoding='utf8')
p.mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
p.mesh.play_animation(unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_001'),True)


