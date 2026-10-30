"""B20 actual route-to-prefix-to-main checks against independent original MBD.

Source attacks are entered with the public neutral StartMove fixture. Target
transitions use real RequestInput and actual authored cancel windows. No private
identity, gauge, cost, phase or Montage position is written. This is a pipeline
matrix, not proof of every source attack's complete human-input precondition.
"""
import datetime
import json
import sys
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Scripts/MHWI'))
import native_connector_source as source
PINS = source.sources()
MBD = source.parse_mbd((ROOT / PINS['mbd']['path']).read_bytes())
OUT = ROOT / 'Saved/MHWIRestoration/B20-20261027/PIE-r06-connections.json'
CASES = [
    ('R06-N29-P0', 'StepSlash', 'FADE_SLASH', 'FadeSlash', 111, 103),
    ('R06-N30-P0', 'SpiritI', 'FADE_SLASH', 'FadeSlash', 117, 103),
    ('R06-N31-P0', 'Thrust', 'LIGHT', 'RisingSlash', 119, 107),
    ('R06-N32-P0', 'Thrust', 'FADE_SLASH', 'FadeSlash', 120, 103),
    ('R06-N33-P0', 'SpiritComboThrust', 'SPIRIT', 'SpiritII', 121, 106),
    ('R06-N34-P0', 'SpiritII', 'FADE_SLASH', 'FadeSlash', 122, 103),
    ('R06-N35-P0', 'SpiritComboRisingSlash', 'FADE_SLASH', 'FadeSlash', 123, 103),
    ('R06-N36-P0', 'SpiritComboRisingSlash', 'SPIRIT', 'SpiritIII', 124, 108),
    ('R06-N37-P0', 'SpiritComboRisingSlash', 'LIGHT', 'OverheadSlash', 125, 102),
    ('R06-N39-P0', 'RisingSlash', 'LIGHT', 'OverheadSlash', 125, 102),
    ('R06-N40-P0', 'SpiritI', 'LIGHT', 'SpiritComboThrust', 118, 112),
    ('R06-N42-P0', 'RisingSlash', 'FADE_SLASH', 'FadeSlash', 123, 103),
    ('R06-N52-P0', 'Roll', 'LIGHT', 'RollStepSlash', 129, 101),
    ('R06-N77-P0', 'IaiSlash', 'LIGHT', 'OverheadSlash', 358, 102),
    ('R06-N78-P0', 'IaiSlash', 'THRUST', 'Thrust', 359, 105),
    ('R06-N79-P0', 'IaiSlash', 'FADE_SLASH', 'FadeSlash', 360, 103),
    ('R06-N82-P0', 'IaiSlash', 'SPIRIT', 'SpiritI', 363, 104),
    ('R06-N44-P0', 'OverheadSlash', 'LIGHT', 'StepSlash', 114, 101, {'recoil': True}),
    ('R06-N84-P0', 'SpiritI', 'SPIRIT', 'SpiritII', 365, 106, {'slinger': 0}),
    ('R06-N85-P0', 'SpiritI', 'SPIRIT', 'SpiritII', 365, 106, {'slinger': -1}),
    ('R06-N85-P0', 'SpiritI', 'SPIRIT', 'SpiritII', 365, 106, {'slinger': 1}),
    ('R06-N88-P0', 'SpiritII', 'SPIRIT', 'SpiritIII', 366, 108, {'slinger': 0}),
    ('R06-N89-P0', 'SpiritII', 'SPIRIT', 'SpiritIII', 366, 108, {'slinger': -1}),
    ('R06-N87-P0', 'SpiritII', 'SPIRIT', 'SpiritIII', 366, 108, {'slinger': 1}),
    ('R06-N80-P0', 'IaiSlash', 'FADE_SLASH', 'FadeSlashRight', 361, 127, {'direction': 1}),
    ('R06-N81-P0', 'IaiSlash', 'FADE_SLASH', 'FadeSlashLeft', 362, 128, {'direction': -1}),
    ('R06-N76-P0', 'IaiSpiritSlash', 'HELM_BREAKER', 'SpiritThrust', 357, 170, {'level': 1}),
    ('R06-N83-P0', 'IaiSlash', 'HELM_BREAKER', 'SpiritThrust', 364, 170, {'level': 1}),
    ('R06-N76-P1', 'IaiSpiritSlash', 'HELM_BREAKER', 'SpiritThrust', 367, 170, {'level': 3}),
    ('R06-N29-P0', 'WalkOnSlash', 'FADE_SLASH', 'FadeSlash', 111, 103),
    ('R06-N32-P0', 'SpiritComboThrust', 'FADE_SLASH', 'FadeSlash', 120, 103),
    ('R06-N52-P0', 'RollLeft', 'LIGHT', 'RollStepSlash', 129, 101),
    ('R06-N52-P0', 'RollRight', 'LIGHT', 'RollStepSlash', 129, 101),
    ('R06-N52-P0', 'RollBack', 'LIGHT', 'RollStepSlash', 129, 101),
    ('R06-N34-P0', 'SpiritI', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': 0}),
    ('R06-N34-P0', 'SpiritI', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': -1}),
    ('R06-N34-P0', 'SpiritI', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': 1}),
    ('R06-N34-P0', 'SpiritII', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': 0}),
    ('R06-N34-P0', 'SpiritII', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': -1}),
    ('R06-N34-P0', 'SpiritII', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': 1}),
    ('R06-N34-P0', 'SpiritIII', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': 0}),
    ('R06-N34-P0', 'SpiritIII', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': -1}),
    ('R06-N34-P0', 'SpiritIII', 'FADE_SLASH', 'FadeSlash', 122, 103, {'slinger': 1}),
    ('R06-N30-P0', 'SpiritI', 'FADE_SLASH', 'FadeSlash', 117, 103, {'weak_source': True}),
    ('R06-N40-P0', 'SpiritI', 'LIGHT', 'SpiritComboThrust', 118, 112, {'weak_source': True}),
]
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = dict(phase='load', at=time.monotonic(), started=time.monotonic(), index=0,
             throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'))
report = dict(passed=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), checks=[], cases=[],
              scope=__doc__, source_mbd=PINS['mbd'])
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def phase(name):
    state.update(phase=name, at=time.monotonic())


def check(value, label, **data):
    report['checks'].append(dict(check=label, passed=bool(value), reference=CASES[state['index']][0], **data))
    if not value:
        raise AssertionError(label + ': ' + str(data))


def playback():
    text = state['player'].get_native_playback_diagnostic()
    return dict(token.split('=', 1) for token in text.split()) if text != 'none' else {}


def definition(name):
    return next(value for key, value in state['player'].get_editor_property('moveset').get_editor_property('moves').items() if str(key) == name)


def finish(error=None):
    report.update(passed=error is None, error=error)
    if state.get('player'):
        report['last_playback'] = state['player'].get_native_playback_diagnostic()
        report['last_entry'] = state['player'].get_last_native_entry_diagnostic()
        report['last_failure'] = state['player'].get_last_move_start_failure()
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
    unreal.unregister_slate_post_tick_callback(state['handle'])
    level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    if error:
        unreal.log_error(error)


def _tick(delta):
    try:
        p = state['phase']
        elapsed = time.monotonic()-state['at']
        if elapsed > 9 or time.monotonic()-state['started'] > 180:
            raise TimeoutError(p)
        if p == 'load':
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads')
            phase('start')
            return
        if p == 'start':
            level.editor_request_begin_play()
            phase('wait')
            return
        if p == 'wait':
            world = editor.get_game_world()
            player = unreal.GameplayStatics.get_player_character(world, 0) if world else None
            if not player:
                return
            targets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget)
            for target in targets:
                target.set_editor_property('enable_attacks', False)
                target.set_actor_location(unreal.Vector(10000, 10000, 75), False, True)
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            contexts = [o for o in unreal.ObjectIterator(unreal.InputMappingContext) if o.get_outer() == player]
            subs = []
            for sub in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem):
                present = sub.has_mapping_context(contexts[0])
                if present[0] if isinstance(present, tuple) else present:
                    subs.append(sub)
            actions = {o.get_name(): o for o in unreal.ObjectIterator(unreal.InputAction) if o.get_outer() == player}
            state.update(world=world, player=player, pc=pc, sub=subs[0], move_action=actions['MHWI_Move'],
                         target=targets[0], anim=player.mesh.get_anim_instance(), anchor=player.get_actor_location(), intent=0)
            phase('reset')
            return
        player = state['player']
        case = CASES[state['index']]
        ref, source_move, command, target_move, prefix_motion, main_motion = case[:6]
        options = case[6] if len(case) > 6 else {}
        state['sub'].inject_input_vector_for_action(state['move_action'], unreal.Vector(state['intent'], 0, 0), [], [])
        if p == 'reset':
            player.interrupt_move()
            player.character_movement.stop_movement_immediately()
            player.set_actor_location(state['anchor'], False, True)
            player.set_actor_rotation(unreal.Rotator(), False)
            state.update(intent=0, aimed=False)
            state['pc'].set_control_rotation(unreal.Rotator())
            state['target'].set_editor_property('deflects_melee', False)
            phase('ground')
        elif p == 'ground' and elapsed > 0.15 and player.character_movement.is_moving_on_ground():
            if player.is_sheathed():
                check(player.request_input(unreal.MHWIInput.TOGGLE_SHEATHE), 'draw input accepted for neutral source fixture')
                phase('draw')
            else:
                phase('fund')
        elif p == 'draw' and player.get_current_move().is_none():
            phase('fund')
        elif p == 'fund':
            # Obtain resources through real hits, preserving all formal costs.
            if options.get('weak_source'):
                if player.get_spirit_gauge() > 0:
                    check(player.start_move('ForesightSlash'), 'real Foresight cost clears Q for a weak-source boundary')
                    player.interrupt_move()
                    check(player.get_spirit_gauge() == 0, 'actual consume-all action established zero Q')
                    phase('reset')
                else:
                    phase('source_start')
                return
            needs_color = player.get_spirit_level() < options.get('level', 0)
            needed = (float(definition('SpiritRoundslash').get_editor_property('spirit_cost')) if needs_color else
                      float(definition(source_move).get_editor_property('spirit_cost')) + float(definition(target_move).get_editor_property('spirit_cost'))) + 5.0
            if player.get_spirit_gauge() >= needed:
                state['target'].set_actor_location(unreal.Vector(10000, 10000, 75), False, True)
                if needs_color:
                    state['old_level'] = player.get_spirit_level()
                    check(player.start_move('SpiritRoundslash'), 'color fixture starts a real paid Roundslash')
                    phase('color')
                else:
                    phase('source_start')
            else:
                state['needed'] = needed
                check(player.start_move('OverheadSlash'), 'resource fixture uses a real cost-free attack instead of overwriting gauge')
                phase('farm')
        elif p == 'farm':
            state['target'].set_actor_location(player.get_actor_location()+player.get_actor_forward_vector()*150, False, True)
            if player.get_spirit_gauge() >= state['needed']:
                check(True, 'real confirmed damage funds the unchanged source/target costs', gauge=player.get_spirit_gauge())
                player.interrupt_move()
                state['target'].set_actor_location(unreal.Vector(10000, 10000, 75), False, True)
                phase('reset')
            elif player.get_current_move().is_none():
                phase('fund')
        elif p == 'color':
            state['target'].set_actor_location(player.get_actor_location()+player.get_actor_forward_vector()*150, False, True)
            if player.get_current_move().is_none():
                check(player.get_spirit_level() > state['old_level'], 'actual Roundslash hit/end raises the required color', level=player.get_spirit_level())
                state['target'].set_actor_location(unreal.Vector(10000, 10000, 75), False, True)
                phase('reset')
        elif p == 'source_start':
            if options.get('recoil'):
                state['target'].set_editor_property('deflects_melee', True)
            check(player.start_move(source_move), 'public neutral fixture starts an actual source attack', source=source_move)
            phase('source')
        elif p == 'source':
            live = playback()
            if options.get('recoil'):
                state['target'].set_actor_location(player.get_actor_location()+player.get_actor_forward_vector()*150, False, True)
                if str(player.get_current_move()) != 'WeaponRecoil':
                    return
                state['target'].set_editor_property('deflects_melee', False)
                state['target'].set_actor_location(unreal.Vector(10000, 10000, 75), False, True)
                check(live.get('body') == '221', 'real deflection produces the exact recoil motion221')
                state['source'] = live
                check(player.request_input(getattr(unreal.MHWIInput, command)), 'real recoil accepts its recovery input')
                phase('prefix')
                return
            if not live or live.get('connector') != '0':
                return
            data = definition(source_move)
            start = float(data.get_editor_property('cancel_start'))
            stop = float(data.get_editor_property('cancel_end'))
            for route in data.get_editor_property('routes'):
                if route.get_editor_property('input') == getattr(unreal.MHWIInput, command):
                    a, b = float(route.get_editor_property('cancel_start')), float(route.get_editor_property('cancel_end'))
                    if a >= 0:
                        start = a
                    if b >= 0:
                        stop = b
                    break
            montage = state['anim'].get_current_active_montage()
            position = state['anim'].montage_get_position(montage) if montage else -1
            if position < start:
                return
            check(position <= stop, 'target request falls inside its real formal cancel window', position=position, start=start, end=stop)
            state['source'] = live
            if 'slinger' in options or 'direction' in options:
                state['intent'] = options.get('slinger', options.get('direction', 0))
                state['pc'].set_control_rotation(player.get_actor_rotation())
                state['aim_ticks'] = 0
                phase('aim')
            else:
                check(player.request_input(getattr(unreal.MHWIInput, command)), 'actual RequestInput accepts the route from the source', command=command)
                phase('prefix')
        elif p == 'aim':
            state['aim_ticks'] += 1
            if state['aim_ticks'] < 3:
                return
            if 'slinger' in options:
                state['ammo'] = player.get_editor_property('slinger_ammo')
                check(player.request_input(unreal.MHWIInput.SLINGER_BURST), 'real directional input starts a native slinger source')
                phase('slinger')
            else:
                check(player.request_input(getattr(unreal.MHWIInput, command)), 'real directional movement selects the authored Iai exit')
                phase('prefix')
        elif p == 'slinger':
            live = playback()
            if not str(player.get_current_move()).startswith('SlingerBurst'):
                return
            state['intent'] = 0
            if player.get_editor_property('slinger_ammo') != state['ammo']-1:
                return
            check(True, 'actual source fires once before its recovery request', source=live)
            state['source'] = live
            check(player.request_input(getattr(unreal.MHWIInput, command)), 'actual fired slinger source accepts its authored recovery')
            phase('prefix')
        elif p == 'prefix':
            if str(player.get_current_move()) != target_move:
                return
            live = playback()
            check(live.get('connector') == '1' and int(live.get('body', -1)) == prefix_motion,
                  'bound instance plays the reference-specific real connector', expected=prefix_motion, actual=live,
                  entry=player.get_last_native_entry_diagnostic())
            destination = next(row for row in MBD['entries'] if row['index'] == main_motion)
            matches = [row for row in destination['blocks'] if row['animation_id'] == prefix_motion and row['declaration'] == live['bank']]
            check(len(matches) == 1, 'original MBD has one exact prefix-to-main record')
            state.update(prefix=live, mbd=matches[0], entry=player.get_last_native_entry_diagnostic())
            phase('main')
        elif p == 'main':
            live = playback()
            if not live or live.get('connector') != '0' or int(live.get('timeline', -1)) != main_motion:
                if player.get_current_move().is_none():
                    raise AssertionError('connector failed to commit the actual main carrier')
                return
            check(live['serial'] == state['prefix']['serial'] and live['instance'] != state['prefix']['instance'],
                  'main replacement retains one execution but has a new real instance', prefix=state['prefix'], main=live)
            start = state['mbd']['start_frame']
            check(start <= float(live['frame']) < start+6, 'actual main enters at original MBD frame', expected=start, actual=live['frame'])
            check(live['gauge_start'] == state['prefix']['gauge_start'], 'main replacement retains the original captured resource transaction')
            report['cases'].append(dict(reference=ref, source=state['source'], entry=state['entry'], prefix=state['prefix'],
                                        first_main=live, mbd=state['mbd'], passed=True))
            phase('end')
        elif p == 'end':
            # This case proved the actual commit; isolate the next source fixture.
            if state['index']+1 == len(CASES):
                finish()
            else:
                state['index'] += 1
                phase('reset')
    except Exception:
        finish(traceback.format_exc())


def tick(delta):
    if state.get('inside_tick'):
        return
    state['inside_tick'] = True
    try:
        _tick(delta)
    finally:
        state['inside_tick'] = False


state['handle'] = unreal.register_slate_post_tick_callback(tick)
