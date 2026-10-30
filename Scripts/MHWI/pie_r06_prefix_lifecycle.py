"""Real impact-prefix interruption/replacement and death regression, B20."""
import datetime
import json
import time
import traceback
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir(), 'MHWIRestoration/B20-20261027/PIE-r06-prefix-lifecycle.json')
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = dict(phase='load', at=time.monotonic(), started=time.monotonic(), throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'))
report = dict(passed=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), checks=[])
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def phase(name):
    state.update(phase=name, at=time.monotonic())
    if state.get('world'):
        state['game_at'] = unreal.GameplayStatics.get_time_seconds(state['world'])


def check(value, label, **data):
    report['checks'].append(dict(check=label, passed=bool(value), **data))
    if not value:
        raise AssertionError(label + str(data))


def live():
    text = state['player'].get_native_playback_diagnostic()
    return dict(token.split('=', 1) for token in text.split()) if text != 'none' else {}


def finish(error=None):
    report.update(passed=error is None, error=error)
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
        if elapsed > 9 or time.monotonic()-state['started'] > 60:
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
            player.disable_input(unreal.GameplayStatics.get_player_controller(world, 0))
            state.update(player=player, world=world, target=targets[0], attrs=player.get_editor_property('attributes'), anim=player.mesh.get_anim_instance())
            check(player.request_input(unreal.MHWIInput.TOGGLE_SHEATHE), 'real draw input accepted')
            phase('draw')
            return
        player = state['player']
        if p == 'draw' and player.get_current_move().is_none():
            state['target'].set_editor_property('impact_size', unreal.MHWIImpactSize.LARGE)
            state['attrs'].apply_damage(1, state['target'])
            phase('impact')
        elif p == 'impact' and str(player.get_current_move()) == 'HitReaction':
            check(player.request_input(unreal.MHWIInput.LIGHT), 'actual large-impact source buffers Light')
            phase('prefix')
        elif p == 'prefix' and str(player.get_current_move()) == 'StepSlash':
            previous = live()
            check(previous.get('connector') == '1' and previous.get('body') == '131', 'actual131 prefix is live before interruption', playback=previous)
            state['old_length'] = state['anim'].get_current_active_montage().get_play_length()
            player.interrupt_move()
            check(player.get_current_move().is_none() and not live(), 'interrupt releases both prefix ownership and action')
            check(player.request_input(unreal.MHWIInput.LIGHT), 'replacement action accepts real input')
            replacement = live()
            check(replacement.get('body') == '102' and replacement.get('serial') != previous['serial'], 'replacement owns a new actual OverheadSlash instance', playback=replacement)
            state['replacement'] = replacement
            phase('late')
        elif p == 'late':
            current = live()
            check(current.get('serial') == state['replacement']['serial'] and current.get('body') == '102',
                  'retired prefix callback cannot commit or terminate the replacement action')
            if unreal.GameplayStatics.get_time_seconds(state['world'])-state['game_at'] > state['old_length']+0.2:
                player.interrupt_move()
                state['target'].set_editor_property('impact_size', unreal.MHWIImpactSize.SMALL)
                state['attrs'].apply_damage(1, state['target'])
                phase('impact_death')
        elif p == 'impact_death' and str(player.get_current_move()) == 'HitReaction':
            check(player.request_input(unreal.MHWIInput.SPIRIT), 'actual small-impact source buffers Spirit')
            phase('prefix_death')
        elif p == 'prefix_death' and str(player.get_current_move()) == 'SpiritI':
            previous = live()
            # At zero Q, weak-I may adopt the existing impact61 carrier. The
            # native entry explicitly allows continuing that owned source;
            # do not pretend every recovery must request a new132 clip.
            entry = player.get_last_native_entry_diagnostic()
            check(previous.get('connector') == '1' and previous.get('body') in {'61', '132'}
                  and ('first='+previous['body']+' ') in entry,
                  'actual owned recovery prefix is live before lethal damage, including native source adoption', playback=previous, entry=entry)
            state['attrs'].apply_damage(10000, state['target'])
            check(state['attrs'].get_current_health() == 0 and player.get_current_move().is_none() and not live(), 'death releases the actual prefix before its main commit')
            phase('dead')
        elif p == 'dead':
            check(player.get_current_move().is_none() and not live() and not player.request_input(unreal.MHWIInput.LIGHT),
                  'dead actor rejects input and old prefix cannot create a main instance')
            if unreal.GameplayStatics.get_time_seconds(state['world'])-state['game_at'] > 4.0:
                finish()
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
