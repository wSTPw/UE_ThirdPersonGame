"""Focused PIE checks for the R06 mode0/A01/A04 repairs."""
import json
import time
import traceback
from pathlib import Path

import unreal

editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = dict(phase='load', at=time.monotonic(), wall=time.monotonic(),
             throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = dict(passed=False, checks=[])
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def check(value, label):
    report['checks'].append(dict(check=label, passed=bool(value)))
    if not value:
        raise AssertionError(label)


def phase(name):
    state.update(phase=name, at=time.monotonic())


def current():
    return str(state['player'].get_current_move())


def idle():
    return state['player'].get_current_move().is_none()


def finish(error=None):
    try:
        if 'player' in state:
            state['player'].set_input_blocked(False)
            state['player'].interrupt_move()
    except Exception:
        pass
    report['passed'] = error is None
    if error:
        report['error'] = error
        unreal.log_error(error)
    output = Path(unreal.Paths.project_saved_dir(), 'MHWIRestoration/B19-20261026/PIE-r06-repairs.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
    unreal.unregister_slate_post_tick_callback(handle)
    level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick(delta):
    try:
        elapsed = time.monotonic() - state['at']
        p = state['phase']
        if time.monotonic() - state['wall'] > 75:
            raise TimeoutError(p)
        if p == 'load':
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads')
            phase('start')
        elif p == 'start':
            level.editor_request_begin_play()
            phase('wait')
        elif p == 'wait':
            world = editor.get_game_world()
            player = unreal.GameplayStatics.get_player_character(world, 0) if world else None
            if not player:
                return
            targets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget)
            for target in targets:
                target.set_editor_property('enable_attacks', False)
            state.update(world=world, player=player, target=targets[0],
                         attrs=player.get_editor_property('attributes'))
            phase('draw')
        elif p == 'draw':
            check(state['player'].request_input(unreal.MHWIInput.LIGHT), 'weapon Light request accepted')
            phase('draw_wait')
        elif p == 'draw_wait':
            if current() == 'DrawSlash' and not state.get('draw_seen'):
                state['draw_seen'] = True
                check(state['player'].mesh.get_anim_instance().get_current_active_montage() is not None,
                      'mode0 fallback permits the weapon montage to play')
            if idle():
                check(state.pop('draw_seen', False), 'DrawSlash started and completed')
                check(not state['player'].is_sheathed(), 'DrawSlash reaches drawn stance')
                check(state['player'].request_input(unreal.MHWIInput.SPIRIT), 'SpiritI request accepted')
                phase('spirit')
        elif p == 'spirit':
            if current() == 'SpiritI' and not state.get('spirit_seen'):
                state['spirit_seen'] = True
                check(state['player'].mesh.get_anim_instance().get_current_active_montage() is not None,
                      'special SpiritI entry also plays through mode0 fallback')
            if idle() or elapsed > 3:
                check(state.pop('spirit_seen', False), 'SpiritI was observed before impact setup')
                state['player'].interrupt_move()
                state['attrs'].apply_damage(12, state['target'])
                phase('impact')
        elif p == 'impact':
            if current() == 'HitReaction':
                check(not state['player'].request_input(unreal.MHWIInput.EVADE),
                      'impact rejects an input with no authored recovery route')
                check(state['player'].request_input(unreal.MHWIInput.LIGHT),
                      'impact accepts its authored Light recovery route')
                phase('recovery')
        elif p == 'recovery':
            if current() == 'StepSlash':
                check(True, 'real impact source commits StepSlash through its native link')
                state['player'].interrupt_move()
                state['attrs'].apply_damage(12, state['target'])
                phase('menu_buffer')
            elif idle() or elapsed > 3:
                raise AssertionError('impact recovery did not reach StepSlash')
        elif p == 'menu_buffer':
            if current() == 'HitReaction':
                check(state['player'].request_input(unreal.MHWIInput.LIGHT),
                      'second impact buffers Light before menu block')
                state['player'].set_input_blocked(True)
                phase('menu_wait')
        elif p == 'menu_wait' and elapsed > 1.5:
            check(current() != 'StepSlash', 'menu block clears source input and prevents internal commit')
            state['player'].set_input_blocked(False)
            state['player'].interrupt_move()
            check(state['player'].request_input(unreal.MHWIInput.LIGHT),
                  'input works again after menu unblock')
            finish()
    except Exception:
        finish(traceback.format_exc())


handle = unreal.register_slate_post_tick_callback(tick)
