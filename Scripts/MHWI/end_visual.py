import unreal,json
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_character(w,0)
unreal.log('REF_BASIS_HEAD '+str(p.mesh.get_socket_transform('bone_003',unreal.RelativeTransformSpace.RTS_COMPONENT)))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
