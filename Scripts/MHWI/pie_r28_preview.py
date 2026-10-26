"""Read-only visual preview of the six R28 candidate AnimSequences.

Runs through MCP run_python_file. No asset property is edited and no authored
move data is changed. Screenshots are project visual-review evidence only.
"""
import json
import time
import traceback
from pathlib import Path

import unreal

OUT = Path(unreal.Paths.project_saved_dir(), 'MHWIRestoration/B19-20261026/R28Preview')
OUT.mkdir(parents=True, exist_ok=True)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
state = {'phase': 'load', 'at': time.monotonic(), 'index': 0, 'sample': 0,
         'motion_ids': [5, 6, 7, 8, 14, 15], 'samples': [0.0, 0.35, 0.7],
         'report': {'passed': False, 'clips': []}}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def finish(error=None):
    try:
        if 'player' in state:
            player = state['player']
            player.set_actor_tick_enabled(True)
            player.mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT)
            player.set_input_blocked(False)
        if 'world' in state:
            unreal.GameplayStatics.set_game_paused(state['world'], False)
        if 'arm' in state:
            state['arm'].set_editor_property('target_arm_length', state['arm_length'])
            state['arm'].set_editor_property('socket_offset', state['socket_offset'])
            state['arm'].set_editor_property('do_collision_test', state['collision_test'])
    except Exception:
        pass
    state['report']['passed'] = error is None
    if error:
        state['report']['error'] = error
        unreal.log_error(error)
    (OUT / 'report.json').write_text(json.dumps(state['report'], indent=2), encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(state['handle'])
    level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def next_sample():
    state['sample'] += 1
    if state['sample'] >= len(state['samples']):
        state['sample'] = 0
        state['index'] += 1
    state['phase'] = 'load_clip'


def tick(delta):
    try:
        if state['phase'] == 'load':
            if not level.load_level('/Game/MHWI/Maps/L_MHWI_Training'):
                raise RuntimeError('training map load failed')
            state['phase'] = 'start'
            return
        if state['phase'] == 'start':
            level.editor_request_begin_play()
            state['phase'] = 'wait'
            return
        if state['phase'] == 'wait':
            world = editor.get_game_world()
            player = unreal.GameplayStatics.get_player_character(world, 0) if world else None
            if not player:
                return
            for target in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget):
                target.set_editor_property('enable_attacks', False)
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            player.disable_input(pc)
            player.set_input_blocked(True)
            player.character_movement.stop_movement_immediately()
            player.character_movement.disable_movement()
            player.set_actor_location(unreal.Vector(0, 0, 94.15), False, True)
            player.set_actor_rotation(unreal.Rotator(), False)
            player.set_actor_tick_enabled(False)
            arm = player.get_editor_property('spring_arm')
            state.update(world=world, player=player, pc=pc, arm=arm,
                         arm_length=arm.get_editor_property('target_arm_length'),
                         socket_offset=arm.get_editor_property('socket_offset'),
                         collision_test=arm.get_editor_property('do_collision_test'))
            arm.set_editor_property('target_arm_length', 320.0)
            arm.set_editor_property('socket_offset', unreal.Vector(0, 0, 25))
            arm.set_editor_property('do_collision_test', False)
            pc.set_control_rotation(unreal.Rotator(pitch=-8.0, yaw=55.0, roll=0.0))
            state['phase'] = 'load_clip'
            return
        if state['index'] >= len(state['motion_ids']):
            finish()
            return
        motion = state['motion_ids'][state['index']]
        if state['phase'] == 'load_clip':
            unreal.GameplayStatics.set_game_paused(state['world'], False)
            sequence = unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_%03d' % motion)
            if not sequence:
                raise RuntimeError('missing candidate ' + str(motion))
            state['sequence'] = sequence
            state['player'].mesh.stop()
            state['player'].mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            state['player'].mesh.play_animation(sequence, False)
            state['clip_started'] = time.monotonic()
            state['phase'] = 'wait_sample'
            return
        if state['phase'] == 'wait_sample':
            fraction = state['samples'][state['sample']]
            sequence = state['sequence']
            if time.monotonic() - state['clip_started'] < sequence.get_play_length() * fraction:
                return
            path = OUT / ('w03_00_%03d-%02d.png' % (motion, round(fraction * 100)))
            if path.exists():
                path.unlink()
            task = unreal.AutomationLibrary.take_high_res_screenshot(1100, 825, str(path))
            if not task or not task.is_valid_task():
                raise RuntimeError('screenshot task rejected ' + str(path))
            state.update(task=task, path=path, phase='wait_capture')
            return
        if state['phase'] == 'wait_capture':
            if not state['task'].is_task_done() or not state['path'].exists():
                return
            state['report']['clips'].append({'motion': motion, 'fraction': state['samples'][state['sample']],
                                              'image': str(state['path']),
                                              'play_length': state['sequence'].get_play_length()})
            next_sample()
    except Exception:
        finish(traceback.format_exc())


state['handle'] = unreal.register_slate_post_tick_callback(tick)
