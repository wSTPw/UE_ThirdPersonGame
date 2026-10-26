"""Real PIE regressions for the MHWI local action authority and imported montages.

Does not rewrite gameplay assets. The inert training target is repositioned in
this disposable PIE world for deterministic counters and independent blade hits.
"""
import json
from pathlib import Path
import time
import traceback
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / 'MHWIImport/PIE-moveset.json'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
report = dict(passed=False, checks=[], events=[], helm_samples=[])
state = dict(phase='load', wall=time.monotonic(), at=time.monotonic(), level_cycle=0)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state['throttle'] = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def check(value, label):
    report['checks'].append(dict(check=label, passed=bool(value)))
    if not value:
        raise AssertionError(label)


def phase(value):
    state.update(phase=value, at=time.monotonic())
    report['events'].append(dict(phase=value, wall=time.monotonic() - state['wall']))
    unreal.log('MHWI_PIE_PHASE ' + value)


def finish(error=None):
    report['passed'] = error is None
    if error:
        report['error'] = error
        unreal.log_error('MHWI_PIE_FAILED ' + error)
    else:
        unreal.log('MHWI_PIE_PASSED')
    settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(handle)
    if level.is_in_play_in_editor():
        level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def current():
    return str(state['player'].get_current_move())


def position():
    montage = state['anim'].get_current_active_montage()
    return state['anim'].montage_get_position(montage) if montage else 0.0


def idle():
    return state['player'].get_current_move().is_none()


def start(name):
    check(state['player'].start_move(name), name + ' starts')


def hp():
    return state['attrs'].get_current_health()


def align():
    player = state['player']
    if idle():
        player.set_actor_location(unreal.Vector(0, 0, 92.2), False, True)
        player.character_movement.stop_movement_immediately()
    player.set_actor_rotation(unreal.Rotator(), False)
    loc = player.get_actor_location()
    state['target'].set_actor_location(unreal.Vector(loc.x + 150, loc.y, 90), False, False)


def tick(delta):
    try:
        elapsed = time.monotonic() - state['at']
        if time.monotonic() - state['wall'] > 210:
            raise TimeoutError('MHWI PIE timeout in ' + state['phase'])
        p = state['phase']
        if p == 'load':
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads')
            phase('start')
        elif p == 'start':
            level.editor_request_begin_play()
            phase('wait')
        elif p == 'wait':
            world = editor.get_game_world()
            if not world:
                return
            player = unreal.GameplayStatics.get_player_character(world, 0)
            if not player:
                return
            check(isinstance(player, unreal.MHWICharacter), 'MHWI pawn possesses')
            targets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget)
            for target in targets:
                target.set_editor_property('enable_attacks', False)
            state.update(world=world, player=player, anim=player.mesh.get_anim_instance(),
                         attrs=player.get_editor_property('attributes'), target=targets[0])
            state['target_attrs'] = targets[0].get_editor_property('attributes')
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            contexts = [obj for obj in unreal.ObjectIterator(unreal.InputMappingContext) if obj.get_outer() == player]
            check(len(contexts) == 1, 'pawn owns exactly one runtime input mapping context')
            context = contexts[0]
            candidates = []
            for obj in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem):
                present = obj.has_mapping_context(context)
                if present[0] if isinstance(present, tuple) else present:
                    candidates.append(obj)
            check(len(candidates) == 1, 'runtime input context installed on exactly one local subsystem')
            subsystem = candidates[0]
            actions = [obj for obj in unreal.ObjectIterator(unreal.InputAction) if obj.get_outer() == player]
            commands = [next(obj for obj in actions if obj.get_name() == 'MHWI_Command_' + str(i)) for i in range(9)]
            state.update(subsystem=subsystem, commands=commands)
            value = unreal.Vector(1.0, 0.0, 0.0)
            subsystem.inject_input_vector_for_action(commands[7], value, [], [])
            phase('draw_input')
        elif p == 'draw_input':
            if not state.get('draw_seen') and current() == 'Draw':
                state['draw_seen'] = True
                check(True, 'Enhanced Input Started invokes draw command')
            if elapsed > 4:
                check(state.get('draw_seen'), 'draw command observed through input system')
                check(not state['player'].is_sheathed(), 'draw completes in drawn stance')
                check(idle(), 'draw completion returns idle')
                start('Roll')
                state['hp_before'] = hp()
                phase('roll_safe')
        elif p == 'roll_safe' and 0.12 < position() < 0.38:
            state['attrs'].apply_damage(12, state['target'])
            check(abs(hp() - state['hp_before']) < 0.01, 'roll iframe intercepts incoming attribute damage')
            phase('roll_unsafe')
        elif p == 'roll_unsafe' and position() > 0.5:
            state['attrs'].apply_damage(12, state['target'])
            check(abs(hp() - (state['hp_before'] - 12)) < 0.01, 'damage outside roll iframe deducts HP')
            check(idle(), 'ordinary damage interrupts the action')
            align()
            start('OverheadSlash')
            phase('level_attack')
        elif p == 'level_attack':
            align()
            if position() >= 1.05:
                check(state['player'].get_spirit_gauge() > 0, 'normal blade hit supplies foresight resource')
                check(state['player'].request_input(unreal.MHWIInput.FORESIGHT), 'foresight buffers from attack recovery')
                phase('foresight_start')
        elif p == 'foresight_start':
            align()
            if current() == 'ForesightSlash' and 0.16 < position() < 0.6:
                before = hp()
                state['attrs'].apply_damage(12, state['target'])
                check(abs(hp() - before) < 0.01, 'foresight successful timing prevents damage')
                check(state['player'].get_spirit_gauge() >= 99.9, 'successful foresight fills spirit gauge')
                phase('foresight_return')
            elif elapsed > 3:
                raise AssertionError('foresight did not enter its counter window')
        elif p == 'foresight_return':
            align()
            if position() >= 1.68:
                check(state['player'].request_input(unreal.MHWIInput.SPIRIT), 'confirmed foresight queues roundslash')
                phase('roundslash')
        elif p == 'roundslash':
            align()
            if current() == 'SpiritRoundslash':
                state['roundslash_seen'] = True
            if idle():
                state['level_cycle'] += 1
                check(state.pop('roundslash_seen', False), 'counter route plays real roundslash montage')
                check(state['player'].get_spirit_level() == state['level_cycle'], 'roundslash raises color to ' + str(state['level_cycle']))
                check(state['player'].is_sheathed(), 'roundslash finishes sheathed')
                if state['level_cycle'] < 3:
                    start('DrawSlash')
                    phase('level_attack')
                else:
                    align()
                    start('DrawSlash')
                    phase('full_chain_prepare')
            elif elapsed > 5:
                raise AssertionError('roundslash route failed to finish')
        elif p == 'full_chain_prepare':
            align()
            if position() >= 1.18:
                check(state['player'].request_input(unreal.MHWIInput.SPIRIT), 'normal attack queues full spirit chain')
                state['full_chain_seen'] = []
                state['full_chain_queued'] = set()
                phase('full_chain')
        elif p == 'full_chain':
            align()
            name = current()
            required = ['SpiritI', 'SpiritII', 'SpiritIII', 'SpiritRoundslash']
            if name in required and name not in state['full_chain_seen']:
                state['full_chain_seen'].append(name)
                if name == 'SpiritI':
                    state['full_chain_hp'] = state['target_attrs'].get_current_health()
                    state['full_chain_gauge'] = state['player'].get_spirit_gauge()
            if name in required[:-1] and name not in state['full_chain_queued']:
                definition = state['player'].get_editor_property('moveset').get_editor_property('moves')[unreal.Name(name)]
                if position() >= definition.get_editor_property('cancel_start') - 0.08:
                    check(state['player'].request_input(unreal.MHWIInput.SPIRIT), name + ' queues next spirit stage')
                    state['full_chain_queued'].add(name)
            if idle():
                check(state['full_chain_seen'] == required, 'full spirit I > II > III > roundslash route completes')
                damage = state['full_chain_hp'] - state['target_attrs'].get_current_health()
                report['full_spirit_chain_damage'] = damage
                check(abs(damage - (28 + 30 + 3 * 12 + 38) * 1.2) < 0.15, 'full spirit chain has six independent real hits')
                check(abs(state['full_chain_gauge'] - state['player'].get_spirit_gauge() - 36) < 0.1, 'remaining spirit stages consume configured gauge once each')
                start('DrawSlash')
                phase('iai_prepare')
            elif elapsed > 14:
                raise AssertionError('full spirit chain failed to finish')
        elif p == 'iai_prepare':
            align()
            if position() >= 1.18:
                check(state['player'].request_input(unreal.MHWIInput.SPECIAL_SHEATHE), 'special sheath queues after an attack')
                phase('special_hold')
        elif p == 'special_hold':
            if state['player'].is_special_sheath_holding():
                check(current() == 'SpecialSheathe', 'special sheath keeps foreground ownership')
                check(state['player'].is_sheathed(), 'special sheath pose reaches sheathed state')
                state['before_iai_target'] = state['target_attrs'].get_current_health()
                check(state['player'].request_input(unreal.MHWIInput.LIGHT), 'special hold accepts Iai double slash')
                phase('iai_double')
            elif elapsed > 5:
                raise AssertionError('special sheath hold did not latch')
        elif p == 'iai_double':
            align()
            if idle():
                damage = state['before_iai_target'] - state['target_attrs'].get_current_health()
                check(abs(damage - 2 * 16 * 1.2) < 0.1, 'Iai double slash has two independent real hit commits')
                state['gauge_regen_before'] = state['player'].get_spirit_gauge()
                start('OverheadSlash')
                phase('iai_counter_prepare')
        elif p == 'iai_counter_prepare':
            align()
            if position() >= 1.06:
                state['player'].request_input(unreal.MHWIInput.SPECIAL_SHEATHE)
                phase('iai_counter_hold')
        elif p == 'iai_counter_hold':
            if state['player'].is_special_sheath_holding():
                state['before_iai_level'] = state['player'].get_spirit_level()
                check(state['player'].request_input(unreal.MHWIInput.SPIRIT), 'special hold accepts Iai spirit slash')
                phase('iai_counter')
        elif p == 'iai_counter':
            align()
            if 0.04 < position() < 0.20 and not state.get('iai_countered'):
                before = hp()
                state['attrs'].apply_damage(12, state['target'])
                check(abs(hp() - before) < 0.01, 'Iai counter intercepts within explicit window')
                state['iai_countered'] = True
            if idle():
                check(state.get('iai_countered'), 'Iai counter actually received incoming damage')
                check(state['player'].get_spirit_level() == state['before_iai_level'], 'successful Iceborne Iai counter preserves level')
                start('OverheadSlash')
                phase('iai_miss_prepare')
        elif p == 'iai_miss_prepare':
            align()
            if position() >= 1.06:
                state['player'].request_input(unreal.MHWIInput.SPECIAL_SHEATHE)
                phase('iai_miss_hold')
        elif p == 'iai_miss_hold':
            if state['player'].is_special_sheath_holding():
                state['before_miss_level'] = state['player'].get_spirit_level()
                state['player'].request_input(unreal.MHWIInput.SPIRIT)
                phase('iai_miss')
        elif p == 'iai_miss':
            align()
            if idle():
                check(state['player'].get_spirit_level() == state['before_miss_level'] - 1, 'uncountered Iai spirit slash consumes one color')
                align()
                state['helm_hp_before'] = state['target_attrs'].get_current_health()
                state['helm_level_before'] = state['player'].get_spirit_level()
                state['helm_states'] = []
                state['helm_ground_start'] = state['player'].get_actor_location()
                start('SpiritThrust')
                phase('helm')
        elif p == 'helm':
            name = current()
            if name not in state['helm_states']:
                state['helm_states'].append(name)
            if name == 'SpiritThrust':
                align()
            report['helm_samples'].append(dict(move=name, position=position(),
                xyz=list(state['player'].get_actor_location().to_tuple()),
                target=list(state['target'].get_actor_location().to_tuple()), hp=state['target_attrs'].get_current_health()))
            if name == 'HelmLand' and not state.get('helm_landing_hp'):
                state['helm_landing_hp'] = state['target_attrs'].get_current_health()
            if idle() and elapsed > 1:
                for required in ['SpiritThrust', 'HelmRise', 'HelmAir', 'SpiritHelmBreaker', 'HelmLand']:
                    check(required in state['helm_states'], 'helm route visits ' + required)
                count_damage = state['helm_landing_hp'] - state['target_attrs'].get_current_health()
                expected = 7 * 20 * [1, 1.05, 1.1, 1.2][state['helm_level_before']]
                report['helm_landing_damage'] = count_damage
                report['helm_landing_expected'] = expected
                check(abs(count_damage - expected) < 0.1, 'helm landing applies exactly seven independent hits')
                check(state['player'].get_spirit_level() == state['helm_level_before'] - 1, 'helm consumes exactly one spirit color')
                check(state['player'].character_movement.movement_mode != unreal.MovementMode.MOVE_FLYING, 'aerial root-motion mode restored after helm')
                start('OverheadSlash')
                state['attrs'].apply_damage(1000, state['target'])
                check(not state['attrs'].is_alive, 'lethal incoming damage kills the hunter')
                check(idle(), 'death releases action ownership')
                check(not state['player'].request_input(unreal.MHWIInput.LIGHT), 'death rejects further combat input')
                finish()
    except Exception:
        finish(traceback.format_exc())


handle = unreal.register_slate_post_tick_callback(tick)



