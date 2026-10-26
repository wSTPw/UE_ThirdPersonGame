import unreal,json
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_character(w,0)
p.mesh.set_editor_property('global_anim_rate_scale',0.0)
r=dict(path=p.get_path_name(),xyz=list(p.get_actor_location().to_tuple()),bones={n:str(p.mesh.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_WORLD)) for n in ['bone_003','bone_012','bone_008']})
Path(unreal.Paths.project_saved_dir(),'MHWIImport/visual-pawn.json').write_text(json.dumps(r,indent=2),encoding='utf8')
