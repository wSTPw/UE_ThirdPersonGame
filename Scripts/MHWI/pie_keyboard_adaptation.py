"""Real Enhanced Input regression for the MHWI PC keyboard adapter.

Run inside Unreal Editor Python after compiling IntroCppEditor. This script does
not prove physical driver-level key delivery; it injects the generated actions.
"""
import json
import time
import traceback
from pathlib import Path

import unreal

editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = dict(phase='load', at=time.monotonic(), wall=time.monotonic(),
             throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'), held=[])
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = dict(passed=False, checks=[])
unreal.EditorPythonScripting.set_keep_python_script_alive(True)

KEY_ACTIONS = {
    'light': 'MHWI_KeyboardCommand_0',
    'thrust': 'MHWI_KeyboardCommand_1',
    'spirit': 'MHWI_KeyboardCommand_2',
    'evade': 'MHWI_KeyboardCommand_6',
    'toggle': 'MHWI_KeyboardCommand_7',
    'slinger': 'MHWI_KeyboardCommand_9',
    'sprint': 'MHWI_KeyboardSprint',
}
COMMAND_CASES = [
    ('LMB -> Light', ['light'], unreal.MHWIInput.LIGHT, False),
    ('RMB -> Thrust', ['thrust'], unreal.MHWIInput.THRUST, False),
    ('Ctrl -> Spirit', ['spirit'], unreal.MHWIInput.SPIRIT, False),
    ('Ctrl+LMB -> HelmBreaker only', ['spirit', 'light'], unreal.MHWIInput.HELM_BREAKER, False),
    ('Ctrl+RMB -> Foresight only', ['spirit', 'thrust'], unreal.MHWIInput.FORESIGHT, False),
    ('LMB+RMB -> FadeSlash only', ['light', 'thrust'], unreal.MHWIInput.FADE_SLASH, False),
    ('Ctrl+Space -> SpecialSheathe only', ['spirit', 'evade'], unreal.MHWIInput.SPECIAL_SHEATHE, False),
    ('Space -> Evade', ['evade'], unreal.MHWIInput.EVADE, False),
    ('V -> SlingerBurst', ['slinger'], unreal.MHWIInput.SLINGER_BURST, False),
    ('gamepad preset does not change PC Helm chord', ['spirit', 'light'], unreal.MHWIInput.HELM_BREAKER, True),
    ('gamepad preset does not change PC Fade chord', ['light', 'thrust'], unreal.MHWIInput.FADE_SLASH, True),
]


def check(value, label):
    report['checks'].append(dict(check=label, passed=bool(value)))
    if not value:
        raise AssertionError(label)


def phase(name):
    state.update(phase=name, at=time.monotonic())


def serial():
    return state['player'].get_input_request_serial()


def last_input():
    return state['player'].get_last_requested_input()


def set_original_preset(value):
    for name in ('b_original_input_preset', 'original_input_preset'):
        try:
            state['player'].set_editor_property(name, value)
            state['preset_property'] = name
            return
        except Exception:
            pass
    raise RuntimeError('Original input preset property is not accessible')


def set_keys(keys):
    state['held'] = list(keys)
    for name, action in state['actions'].items():
        value = 1.0 if name in keys else 0.0
        state['subsystem'].inject_input_vector_for_action(action, unreal.Vector(value, 0.0, 0.0), [], [])


def finish(error=None):
    try:
        if 'actions' in state:
            set_keys([])
        if 'player' in state and 'preset_property' in state:
            state['player'].set_editor_property(state['preset_property'], False)
    except Exception:
        pass
    report['passed'] = error is None
    if error:
        report['error'] = error
        unreal.log_error(error)
    output = Path(unreal.Paths.project_saved_dir(), 'MHWIImport/PIE-keyboard-adaptation.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
    unreal.unregister_slate_post_tick_callback(handle)
    level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick(delta):
    try:
        elapsed = time.monotonic() - state['at']
        current_phase = state['phase']
        if time.monotonic() - state['wall'] > 90:
            raise TimeoutError(current_phase)
        if current_phase == 'load':
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads')
            phase('start')
        elif current_phase == 'start':
            level.editor_request_begin_play()
            phase('wait')
        elif current_phase == 'wait':
            world = editor.get_game_world()
            player = unreal.GameplayStatics.get_player_character(world, 0) if world else None
            if not player:
                return
            check(isinstance(player, unreal.MHWICharacter), 'MHWI pawn possesses')
            for target in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget):
                target.set_editor_property('enable_attacks', False)
            contexts = [obj for obj in unreal.ObjectIterator(unreal.InputMappingContext) if obj.get_outer() == player]
            check(len(contexts) == 1, 'one runtime mapping context exists')
            candidates = []
            for subsystem in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem):
                present = subsystem.has_mapping_context(contexts[0])
                if present[0] if isinstance(present, tuple) else present:
                    candidates.append(subsystem)
            check(len(candidates) == 1, 'mapping context is installed once')
            objects = [obj for obj in unreal.ObjectIterator(unreal.InputAction) if obj.get_outer() == player]
            by_name = {obj.get_name(): obj for obj in objects}
            actions = {key: by_name[action_name] for key, action_name in KEY_ACTIONS.items()}
            for index in range(10):
                check('MHWI_Command_' + str(index) in by_name, 'legacy gamepad action remains: ' + str(index))
                check('MHWI_KeyboardCommand_' + str(index) in by_name, 'keyboard action exists: ' + str(index))
            state.update(world=world, player=player, subsystem=candidates[0], actions=actions,
                         case_index=0, command_results=[])
            phase('sheathed_sprint')
        elif current_phase == 'sheathed_sprint':
            state['before'] = serial()
            set_keys(['sprint'])
            phase('sheathed_sprint_check')
        elif current_phase == 'sheathed_sprint_check' and elapsed > 0.15:
            check(state['player'].is_sprinting(), 'Shift sprints while sheathed')
            check(serial() == state['before'], 'sheathed Shift emits no attack command')
            set_keys([])
            phase('sprint_release')
        elif current_phase == 'sprint_release' and elapsed > 0.15:
            check(not state['player'].is_sprinting(), 'Shift release stops sprint')
            state['before'] = serial()
            set_keys(['toggle', 'thrust'])
            phase('sheathed_filters')
        elif current_phase == 'sheathed_filters' and elapsed > 0.15:
            check(serial() == state['before'], 'sheathed E and RMB emit no draw/thrust request')
            set_keys([])
            state['before'] = serial()
            set_keys(['light'])
            phase('draw_with_light')
        elif current_phase == 'draw_with_light':
            if not state['player'].is_sheathed() and state['player'].get_current_move().is_none():
                check(serial() - state['before'] == 1 and last_input() == unreal.MHWIInput.LIGHT,
                      'sheathed LMB produces one Light request and really draws')
                set_keys([])
                state['before'] = serial()
                set_keys(['toggle'])
                phase('drawn_e')
        elif current_phase == 'drawn_e' and elapsed > 0.15:
            check(serial() - state['before'] == 1 and last_input() == unreal.MHWIInput.TOGGLE_SHEATHE,
                  'drawn E routes one Sheathe request')
            set_keys([])
            phase('wait_sheathed_for_shift')
        elif current_phase == 'wait_sheathed_for_shift':
            if state['player'].is_sheathed() and state['player'].get_current_move().is_none():
                state['before'] = serial()
                set_keys(['light'])
                phase('draw_for_shift')
        elif current_phase == 'draw_for_shift':
            if not state['player'].is_sheathed() and state['player'].get_current_move().is_none():
                check(serial() - state['before'] == 1 and last_input() == unreal.MHWIInput.LIGHT,
                      'LMB redraws before the Shift check')
                set_keys([])
                state['before'] = serial()
                set_keys(['sprint'])
                phase('drawn_shift')
        elif current_phase == 'drawn_shift' and elapsed > 0.15:
            check(serial() - state['before'] == 1 and last_input() == unreal.MHWIInput.TOGGLE_SHEATHE,
                  'drawn Shift routes one Sheathe request')
            set_keys([])
            phase('wait_sheathed_for_commands')
        elif current_phase == 'wait_sheathed_for_commands':
            if state['player'].is_sheathed() and state['player'].get_current_move().is_none():
                state['before'] = serial()
                set_keys(['light'])
                phase('draw_for_commands')
        elif current_phase == 'draw_for_commands':
            if not state['player'].is_sheathed() and state['player'].get_current_move().is_none():
                check(serial() - state['before'] == 1 and last_input() == unreal.MHWIInput.LIGHT,
                      'LMB redraws before the command matrix')
                set_keys([])
                phase('command_inject')
        elif current_phase == 'command_inject':
            case = COMMAND_CASES[state['case_index']]
            set_original_preset(case[3])
            state['before'] = serial()
            set_keys(case[1])
            phase('command_check')
        elif current_phase == 'command_check':
            case = COMMAND_CASES[state['case_index']]
            check(serial() - state['before'] == 1, case[0] + ': exactly one request')
            check(last_input() == case[2], case[0] + ': expected command')
            state['command_results'].append(case[0])
            set_keys([])
            state['case_index'] += 1
            phase('command_release' if state['case_index'] < len(COMMAND_CASES) else 'unrelated_chord')
        elif current_phase == 'command_release':
            phase('command_inject')
        elif current_phase == 'unrelated_chord':
            set_original_preset(False)
            state['before'] = serial()
            set_keys(['spirit', 'light'])
            phase('unrelated_add')
        elif current_phase == 'unrelated_add':
            check(serial() - state['before'] == 1 and last_input() == unreal.MHWIInput.HELM_BREAKER,
                  'unrelated test starts with one Helm request')
            state['before'] = serial()
            set_keys(['spirit', 'light', 'slinger'])
            phase('unrelated_check')
        elif current_phase == 'unrelated_check':
            check(serial() - state['before'] == 1, 'unrelated V adds only one request, not another Helm')
            check(last_input() == unreal.MHWIInput.SLINGER_BURST,
                  'unrelated V is the last request while Ctrl+LMB remains held')
            set_keys([])
            state['player'].interrupt_move()
            finish()
    except Exception:
        finish(traceback.format_exc())


handle = unreal.register_slate_post_tick_callback(tick)
