"""Start a persistent, inert PIE view for manual visual inspection via MCP screenshots."""
import unreal
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def setup(delta):
    world=editor.get_game_world()
    player=unreal.GameplayStatics.get_player_character(world,0) if world else None
    if not player: return
    for target in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MHWITrainingTarget):
        target.set_editor_property('enable_attacks',False)
    pc=unreal.GameplayStatics.get_player_controller(world,0)
    pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=0))
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.log('MHWI_VISUAL_READY')

if not level.is_in_play_in_editor():
    level.load_level('/Game/MHWI/Maps/L_MHWI_Training')
    level.editor_request_begin_play()
handle=unreal.register_slate_post_tick_callback(setup)
