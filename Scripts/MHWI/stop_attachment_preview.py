import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if w: unreal.GameplayStatics.set_game_paused(w,False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
