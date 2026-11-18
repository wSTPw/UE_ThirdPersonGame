"""Real PIE check for the presentation layer: blade trail (both styles) and hit numbers.

Runs the same swing twice: the default TipOnly filament, then FullBlade. Verifies that
a switch drops the stored samples, that both styles record a ribbon inside the source
hit window, that a real hit produces one number, and that the number expires.
Presentation only: it does not re-test damage rules.

A background editor runs PIE at 2-3 FPS, so a 0.4 s swing would be invisible. The
script slows the game clock instead of pretending the sampling succeeded; game-time
positions are reported so the timing stays auditable.
Writes Saved/MHWIPresentation/PIE-presentation.json.
"""
import json
import time
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / 'MHWIPresentation/PIE-presentation.json'
OUT.parent.mkdir(parents=True, exist_ok=True)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

report = dict(done=False, passed=False, checks=[], snapshots=[], screenshots=[])
state = dict(phase='load', wall=time.monotonic(), at=time.monotonic(), shot=set(), align_frames=0)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def check(value, label):
    report['checks'].append(dict(check=label, passed=bool(value)))
    if not value:
        raise AssertionError(label)


def phase(value):
    state.update(phase=value, at=time.monotonic())
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')


def reset_run():
    state['run'] = dict(samples=0, numbers=0, hp_min=None, bucket=-1)


def snapshot(tag, **extra):
    report['snapshots'].append(dict(tag=tag, t=round(time.monotonic() - state['wall'], 3), **extra))


def shoot(name):
    if name in state['shot']:
        return
    state['shot'].add(name)
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, name)
        report['screenshots'].append(name)
    except BaseException as error:  # noqa: BLE001 - a missing screenshot must not hide the functional result
        unreal.log_error('MHWI_PIE screenshot failed %s: %r' % (name, error))
        report['screenshots'].append(dict(name=name, error=repr(error)))


def finish(error=None):
    report['done'] = True
    report['passed'] = error is None
    if error:
        report['error'] = error
        unreal.log_error('MHWI_PRESENTATION_FAILED ' + error)
    else:
        unreal.log('MHWI_PRESENTATION_PASSED')
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(handle)
    if level.is_in_play_in_editor():
        level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def gap(player, target):
    delta = player.get_actor_location() - target.get_actor_location()
    return (delta.x ** 2 + delta.y ** 2 + delta.z ** 2) ** 0.5


def blade_probe(player):
    try:
        mesh = player.get_editor_property('weapon_mesh')
        base = mesh.get_socket_location('bone_100')
        tip = mesh.get_socket_location('bone_101')
        delta = tip - base
        length = (delta.x ** 2 + delta.y ** 2 + delta.z ** 2) ** 0.5
        return dict(length=round(length, 1))
    except BaseException as error:  # noqa: BLE001 - diagnostics must not fail the run
        return repr(error)


def place(player, target):
    player.set_actor_location(unreal.Vector(0, 0, 92.2), False, True)
    player.character_movement.stop_movement_immediately()
    player.set_actor_rotation(unreal.Rotator(), False)
    loc = player.get_actor_location()
    target.set_actor_location(unreal.Vector(loc.x + 150.0, loc.y, 90.0), False, False)
    return loc


def start_swing(move_names):
    started = []
    for name in move_names:
        if state['player'].start_move(unreal.Name(name)):
            started.append(name)
            break
    check(started, 'a drawn attack starts (' + '/'.join(move_names) + ')')
    return started[-1] if started else None


def observe(tag, shot_tag):
    """One frame of swing evidence; returns the per-run counters."""
    player = state['player']
    run = state['run']
    # Root motion turns the character; keep the inert target in front of the blade so
    # the hit is decided by the damage window, not by placement luck.
    if run['numbers'] == 0:
        ahead = player.get_actor_location() + player.get_actor_forward_vector() * 80.0
        state['target'].set_actor_location(unreal.Vector(ahead.x, ahead.y, 90.0), False, False)
    samples = player.get_weapon_trail_sample_count()
    run['samples'] = max(run['samples'], samples)
    numbers = player.get_active_damage_number_count()
    run['numbers'] = max(run['numbers'], numbers)
    hp_now = state['attrs'].get_current_health()
    run['hp_min'] = hp_now if run['hp_min'] is None else min(run['hp_min'], hp_now)
    if samples >= (10 if 'tip' in shot_tag else 3):
        shoot(shot_tag)
    if numbers > 0:
        shoot('MHWI_03_hit')
    elapsed = time.monotonic() - state['at']
    if elapsed > 0.2 and int(elapsed * 3) != run['bucket']:
        run['bucket'] = int(elapsed * 3)
        snapshot(tag, t_game=round(player.get_move_position(), 3), samples=samples, numbers=numbers,
                 hp=hp_now, gap=round(gap(player, state['target']), 1), blade=blade_probe(player),
                 debug=player.get_presentation_debug())
    return run


def tick(delta):
    # A high-res capture pumps Slate and re-enters this callback: one step per frame only.
    if state.get('busy'):
        return
    state['busy'] = True
    try:
        if time.monotonic() - state['wall'] > 240:
            raise TimeoutError('PIE phase ' + state['phase'])
        elapsed = time.monotonic() - state['at']
        current = state['phase']
        state['ticks'] = state.get('ticks', 0) + 1
        trace = report.setdefault('trace', [])
        if not trace or trace[-1] != current:
            trace.append(current)
            unreal.log('MHWI_PIE phase=%s tick=%d' % (current, state['ticks']))
        if current == 'load':
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads')
            phase('start')
        elif current == 'start':
            level.editor_request_begin_play()
            phase('wait')
        elif current == 'wait':
            world = editor.get_game_world()
            player = unreal.GameplayStatics.get_player_character(world, 0) if world else None
            if not player:
                return
            check(isinstance(player, unreal.MHWICharacter), 'training GameMode possesses MHWI character')
            trail = player.get_editor_property('weapon_trail')
            check(trail is not None, 'character owns a weapon trail component')
            targets = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
                       if 'TrainingTarget' in actor.get_class().get_name()]
            check(len(targets) > 0, 'training target exists')
            for actor in targets:
                actor.set_editor_property('enable_attacks', False)
            state.update(world=world, player=player, trail=trail, target=targets[0],
                         attrs=targets[0].get_editor_property('attributes'))
            check(player.get_weapon_trail_style() == unreal.MHWIWeaponTrailStyle.TIP_ONLY,
                  'trail starts on the tip-only style')
            phase('align')
        elif current == 'align':
            # RestartPlayer can still run after the first possession frame, so the
            # placement is re-applied for a few frames before the swing starts.
            state['align_frames'] += 1
            loc = place(state['player'], state['target'])
            state['hp_before'] = state['attrs'].get_current_health()
            if state['align_frames'] >= 3:
                check(abs(loc.x) < 1.0 and abs(loc.y) < 1.0, 'player stands on the aligned mark')
                report['align'] = dict(player=loc.to_tuple(),
                                       target=state['target'].get_actor_location().to_tuple())
                # 2-3 FPS background editor: 0.04 keeps the swing observable per frame
                # and still yields a ribbon with enough segments to judge the look.
                unreal.GameplayStatics.set_global_time_dilation(state['world'], 0.04)
                reset_run()
                report['tip_move'] = start_swing(('DrawSlash', 'OverheadSlash', 'StepSlash'))
                phase('swing')
        elif current == 'swing':
            run = observe('tip_probe', 'MHWI_02_tip_trail')
            if elapsed > 30.0:
                check(run['samples'] >= 2, 'tip-only trail recorded samples inside the swing window')
                check(run['hp_min'] < state['hp_before'], 'the swing damaged the target')
                check(run['numbers'] >= 1, 'a hit number appeared for the resolved hit')
                check(state['player'].get_weapon_trail_style() == unreal.MHWIWeaponTrailStyle.TIP_ONLY,
                      'tip-only look stays active through its swing')
                phase('check')
        elif current == 'check':
            # 0.75 s of game time at 0.05 dilation is ~15 s of wall clock.
            if elapsed > 16.0:
                player = state['player']
                check(player.get_active_damage_number_count() == 0, 'hit numbers expire after their lifetime')
                check(player.get_weapon_trail_sample_count() < 2, 'trail clears once the window closes')
                # Switch look: old samples describe a different band and must be dropped.
                before = player.get_weapon_trail_sample_count()
                player.set_weapon_trail_style(unreal.MHWIWeaponTrailStyle.FULL_BLADE)
                check(player.get_weapon_trail_style() == unreal.MHWIWeaponTrailStyle.FULL_BLADE,
                      'style switch reaches the trail component')
                check(player.get_weapon_trail_sample_count() == 0 and before < 2,
                      'style switch drops the stored samples')
                state['align_frames'] = 0
                phase('full_align')
        elif current == 'full_align':
            if not state['player'].get_current_move().is_none():
                return
            state['align_frames'] += 1
            loc = place(state['player'], state['target'])
            if state['align_frames'] >= 3:
                reset_run()
                state['hp_before'] = state['attrs'].get_current_health()
                report['full_blade_move'] = start_swing(('OverheadSlash', 'StepSlash', 'DrawSlash'))
                phase('full_swing')
        elif current == 'full_swing':
            run = observe('full_probe', 'MHWI_04_full_trail')
            if elapsed > 30.0:
                check(run['samples'] >= 2, 'full-blade trail recorded samples inside the swing window')
                check(run['hp_min'] < state['hp_before'], 'the full-blade swing damaged the target')
                check(run['numbers'] >= 1, 'the full-blade swing produced a hit number')
                snapshot('final', numbers=state['player'].get_active_damage_number_count(),
                         samples=state['player'].get_weapon_trail_sample_count())
                finish()
    except BaseException as error:  # noqa: BLE001 - report every failure, never raise into Slate
        import traceback
        finish(repr(error) + '\n' + traceback.format_exc())
    finally:
        state['busy'] = False


handle = unreal.register_slate_post_tick_callback(tick)
