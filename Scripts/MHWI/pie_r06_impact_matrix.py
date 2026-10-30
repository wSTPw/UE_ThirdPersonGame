"""B20 S/M/L impact sources in both stances, through real damage and input."""
import datetime
import json
import time
import traceback
import sys
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Scripts/MHWI'))
import native_connector_source as native_source
SOURCE_PINS = native_source.sources()
SOURCE_MBD = native_source.parse_mbd((ROOT / SOURCE_PINS['mbd']['path']).read_bytes())

OUT = Path(unreal.Paths.project_saved_dir(), globals().get('MHWI_REPORT_PATH', 'MHWIRestoration/B20-20261027/PIE-r06-impact-matrix.json'))
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = dict(phase='load', at=time.monotonic(), start=time.monotonic(), index=0,
             throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'))
report = dict(passed=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), checks=[], cases=[],
              observations=[], scope='12 real impact-to-Light/Spirit cases; not all 32 references or missing posture/item owners')
cases = globals().get('MHWI_CASES') or [(s, size, key) for s in (True, False) for size in ('SMALL', 'MEDIUM', 'LARGE') for key in ('LIGHT', 'SPIRIT')]
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def phase(name):
    state.update(phase=name, at=time.monotonic())


def check(value, label, **data):
    report['checks'].append(dict(check=label, passed=bool(value), case=state['index'], **data))
    if not value:
        raise AssertionError(label + str(data))


def playback():
    text = state['player'].get_native_playback_diagnostic()
    if text == 'none':
        return {}
    return dict(field.split('=', 1) for field in text.split())


def finish(error=None):
    report.update(passed=error is None, error=error)
    if state.get('player'):
        report['last_diagnostic'] = dict(gauge=state['player'].get_spirit_gauge(), failure=state['player'].get_last_move_start_failure(), current=str(state['player'].get_current_move()))
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
        elapsed = time.monotonic() - state['at']
        if time.monotonic() - state['start'] > 140 or elapsed > 8:
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
            player.disable_input(unreal.GameplayStatics.get_player_controller(world, 0))
            state.update(player=player, world=world, target=targets[0], anim=player.mesh.get_anim_instance(),
                         attrs=player.get_editor_property('attributes'), anchor=player.get_actor_location(), rotation=player.get_actor_rotation())
            phase('setup')
            return
        player, anim = state['player'], state['anim']
        report['observations'].append(dict(case=state['index'], phase=p, time=unreal.GameplayStatics.get_time_seconds(state['world']), move=str(player.get_current_move()), gauge=player.get_spirit_gauge(), failure=player.get_last_move_start_failure(), falling=player.character_movement.is_falling(), location=str(player.get_actor_location())))
        sheathed, size, key = cases[state['index']]
        if p == 'setup':
            player.interrupt_move()
            # Isolate ground cases: accumulated root motion otherwise leaves
            # this finite training platform. Keep actual falling/landing physics.
            player.character_movement.stop_movement_immediately()
            player.set_actor_location(state['anchor'], False, True)
            player.set_actor_rotation(state['rotation'], False)
            phase('ground')
        elif p == 'ground' and elapsed > 0.15 and player.character_movement.is_moving_on_ground():
            check(True, 'ground fixture really landed before the impact')
            if player.is_sheathed() != sheathed:
                check(player.request_input(unreal.MHWIInput.TOGGLE_SHEATHE), 'production stance change accepted')
                phase('stance')
            else:
                phase('damage')
        elif p == 'stance' and player.get_current_move().is_none():
            check(player.is_sheathed() == sheathed, 'stance completed before damage')
            phase('damage')
        elif p == 'damage':
            state['target'].set_editor_property('impact_size', getattr(unreal.MHWIImpactSize, size))
            state['attrs'].apply_damage(1.0, state['target'])
            phase('impact')
        elif p == 'impact' and str(player.get_current_move()) == 'HitReaction':
            check(size.lower() in str(player.get_control_state()).lower(), 'real damage retains the requested impact control class', control=str(player.get_control_state()))
            montage = anim.get_current_active_montage()
            check(montage is not None and montage.get_play_length() > 0, 'actual source carrier has a positive duration', seconds=montage.get_play_length() if montage else None)
            check(not player.request_input(unreal.MHWIInput.EVADE), 'impact rejects unauthored Evade recovery')
            check(player.request_input(getattr(unreal.MHWIInput, key)), 'authored recovery request accepted', input=key, sheathed=sheathed, size=size)
            phase('recover')
        elif p == 'recover':
            expected = 'StepSlash' if key == 'LIGHT' else 'SpiritI'
            if str(player.get_current_move()) == expected:
                check(anim.get_current_active_montage() is not None, 'real impact source commits the requested main montage', move=expected)
                index = ('SMALL', 'MEDIUM', 'LARGE').index(size)
                group = 1 if sheathed else 3
                action = (103, 110, 115)[index] if sheathed else 30 + index
                motion = 70 + index if sheathed else 61 + index
                diagnostic = player.get_last_native_entry_diagnostic()
                check(f'previous={group}/{action} ' in diagnostic and f'motion={motion} ' in diagnostic,
                      'accepted plan retains the real impact identity and source motion', diagnostic=diagnostic)
                live = playback()
                check(live.get('connector') == '1', 'actual bound carrier is the connector, distinct from the main action name', playback=live)
                main_motion = 101 if key == 'LIGHT' else 104
                block = next(row for row in SOURCE_MBD['entries'] if row['index'] == main_motion)
                matches = [row for row in block['blocks'] if row['declaration'] == live['bank'] and row['animation_id'] == int(live['body'])]
                selection = 'specific'
                if not matches:
                    matches = [row for row in block['blocks'] if row['declaration'] == 'Default']
                    selection = 'serialized_default'
                check(len(matches) == 1, 'independent original MBD identifies this actual prefix-to-main pair or its serialized default', selection=selection)
                state.update(prefix=live, main_motion=main_motion, mbd=matches[0], entry=diagnostic)
                phase('main')
            elif player.get_current_move().is_none():
                raise AssertionError('source ended without recovery ' + str(cases[state['index']]))
        elif p == 'main':
            live = playback()
            if live.get('connector') == '0' and int(live.get('body', -1)) == state['main_motion']:
                check(live['serial'] == state['prefix']['serial'] and live['instance'] != state['prefix']['instance'],
                      'connector commits a new main carrier without starting a second action execution', prefix=state['prefix'], main=live)
                frame = float(live['frame'])
                start = state['mbd']['start_frame']
                check(start <= frame < start+6, 'first observed actual main frame follows the original MBD entry', expected_frame=start, actual_frame=frame, tolerance='under 6 source frames for 60 FPS Slate sampling')
                check(live['gauge_start'] == state['prefix']['gauge_start'], 'main commit retains the original captured resource transaction')
                report['cases'].append(dict(sheathed=sheathed, size=size, input=key, main='StepSlash' if key == 'LIGHT' else 'SpiritI',
                    source_entry=state['entry'], prefix=state['prefix'], first_main=live, mbd=state['mbd'], passed=True))
                phase('complete')
            elif player.get_current_move().is_none():
                raise AssertionError('connector ended without an actual main carrier')
        elif p == 'complete' and player.get_current_move().is_none():
            state['index'] += 1
            if state['index'] == len(cases):
                finish()
            else:
                phase('setup')
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
