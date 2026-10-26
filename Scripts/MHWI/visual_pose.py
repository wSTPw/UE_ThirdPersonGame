import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_character(w,0)
p.request_input(unreal.MHWIInput.TOGGLE_SHEATHE)
unreal.GameplayStatics.get_player_controller(w,0).set_control_rotation(unreal.Rotator(pitch=-10,yaw=140))
