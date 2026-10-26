"""Temporary PIE montage fixture; never saves assets or alters authored move data."""
import json
import time
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / 'MHWIImport'
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def start():
    if editor.get_game_world():
        return {'running': True}
    assert level.load_level('/Game/MHWI/Maps/L_MHWI_Training')
    level.editor_request_begin_play()
    return {'requested': True}


def pose(move='SpiritII', frame=24):
    world = editor.get_game_world()
    assert world, 'Start PIE first'
    unreal.GameplayStatics.set_game_paused(world, False)
    p = unreal.GameplayStatics.get_player_character(world, 0)
    assert isinstance(p, unreal.MHWICharacter)
    p.set_actor_tick_enabled(True)
    settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
    throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
    for target in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget):
        target.set_editor_property('enable_attacks', False)
    p.disable_input(unreal.GameplayStatics.get_player_controller(world, 0))
    p.interrupt_move()
    p.character_movement.stop_movement_immediately()
    p.set_actor_location(unreal.Vector(0, 0, 94.15), False, True)
    p.set_actor_rotation(unreal.Rotator(), False)
    original = p.get_editor_property('moveset')
    data = unreal.new_object(unreal.MHWIMovesetData)
    # Isolated zero-cost pose fixture, not normal-input gameplay validation.
    # Unreal Map is a live property view. Copy its entries before inserting a fixture move.
    moves = {str(key): value.copy() for key, value in original.get_editor_property('moves').items()}
    definition = moves[move].copy()
    definition.set_editor_property('spirit_cost', 0)
    definition.set_editor_property('require_spirit_level', False)
    definition.set_editor_property('require_nonzero_gauge', False)
    definition.set_editor_property('source_play_rates', {})
    moves[move] = definition
    data.set_editor_property('moves', moves)
    p.set_editor_property('moveset', data)
    assert p.start_move(move)
    anim = p.mesh.get_anim_instance()
    montage = anim.get_current_active_montage()
    state = {'at': time.monotonic(), 'settle': 0}

    def tick(dt):
        if time.monotonic() - state['at'] < .25:
            return
        p.set_actor_tick_enabled(False)
        if state['settle'] < 4:
            anim.montage_pause(montage)
            anim.montage_set_position(montage, frame / 60.0)
            state['settle'] += 1
            return
        unreal.GameplayStatics.set_game_paused(world, True)
        report = {'move': str(p.get_current_move()), 'montage': montage.get_path_name(),
                  'seconds': anim.montage_get_position(montage), 'actor': str(p.get_actor_transform()),
                  'bones': {n: str(p.mesh.get_socket_transform(n)) for n in
                            ['bone_root', 'bone_000', 'bone_002', 'bone_008', 'bone_012']}}
        (OUT / 'animation-pose-preview.json').write_text(json.dumps(report, indent=2), encoding='utf8')
        settings.set_editor_property('bThrottleCPUWhenNotForeground', throttle)
        # Retain fixture data through the pawn, restore its original data on end/next invocation.
        unreal.unregister_slate_post_tick_callback(state['handle'])
        unreal.log('MHWI_PREVIEW_READY ' + move)
    state['handle'] = unreal.register_slate_post_tick_callback(tick)
    return {'move': move, 'frame': frame, 'fixture_only': True}


def gait(index=89):
    world = editor.get_game_world()
    assert world, 'Start PIE first'
    unreal.GameplayStatics.set_game_paused(world, False)
    p = unreal.GameplayStatics.get_player_character(world, 0)
    p.disable_input(unreal.GameplayStatics.get_player_controller(world, 0))
    p.set_actor_tick_enabled(False)
    p.character_movement.stop_movement_immediately()
    p.character_movement.disable_movement()
    p.set_actor_location(unreal.Vector(0, 0, 94.15), False, True)
    p.set_actor_rotation(unreal.Rotator(), False)
    for target in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget):
        target.set_editor_property('enable_attacks', False)
    settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
    throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
    seq = unreal.load_asset(f'/Game/MHWI/Animations/Common/A_co00_00_{index:03}')
    seq.set_editor_property('enable_root_motion', False)
    seq.set_editor_property('force_root_lock', True)
    seq.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
    p.mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    p.mesh.play_animation(seq, True)
    p.mesh.stop()
    p.mesh.set_position(seq.get_play_length()*.2, False)
    state = {'count': 0}
    def tick(dt):
        state['count'] += 1
        if state['count'] < 5: return
        unreal.GameplayStatics.set_game_paused(world, True)
        settings.set_editor_property('bThrottleCPUWhenNotForeground', throttle)
        unreal.unregister_slate_post_tick_callback(state['handle'])
    state['handle'] = unreal.register_slate_post_tick_callback(tick)
    return {'clip': seq.get_path_name(), 'fixture_only': True}
