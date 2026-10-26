"""Real MHWI PIE smoke: possession/input, capsule movement and montage effects."""
import json
from pathlib import Path
import time
import traceback
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / 'MHWIImport/PIE-smoke.json'
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report = dict(passed=False, checks=[], snapshots=[])
state = dict(phase='load', wall=time.monotonic(), at=time.monotonic())
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def check(value, label):
    report['checks'].append(dict(check=label, passed=bool(value)))
    if not value:
        raise AssertionError(label)


def phase(value):
    state.update(phase=value, at=time.monotonic())


def finish(error=None):
    report['passed'] = error is None
    if error:
        report['error'] = error
        unreal.log_error('MHWI_SMOKE_FAILED ' + error)
    else:
        unreal.log('MHWI_SMOKE_PASSED')
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(handle)
    if level.is_in_play_in_editor():
        level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick(delta):
    try:
        elapsed = time.monotonic() - state['at']
        if time.monotonic() - state['wall'] > 80:
            raise TimeoutError('PIE phase ' + state['phase'])
        current = state['phase']
        if current == 'load':
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads')
            phase('start')
        elif current == 'start':
            level.editor_request_begin_play()
            phase('wait')
        elif current == 'wait':
            world = editor.get_game_world()
            if not world:
                return
            player = unreal.GameplayStatics.get_player_character(world, 0)
            if not player:
                return
            check(isinstance(player, unreal.MHWICharacter), 'training GameMode possesses MHWI character')
            check(isinstance(player.mesh.get_anim_instance(), unreal.MHWIAnimInstance), 'native MHWI animation instance active')
            state.update(world=world, player=player, start=player.get_actor_location(),
                         attributes=player.get_editor_property('attributes'))
            targets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget)
            check(len(targets) == 3, 'three training targets present')
            for target in targets:
                target.set_editor_property('enable_attacks', False)
            state['target'] = targets[0]
            check(not player.request_input(unreal.MHWIInput.FORESIGHT), 'neutral foresight rejects')
            check(not player.start_move('SpiritI'), 'zero-gauge spirit attack rejects')
            phase('move')
        elif current == 'move':
            state['player'].add_movement_input(unreal.Vector(1, 0, 0), 1.0, False)
            if elapsed >= 1.0:
                player = state['player']
                travel = (player.get_actor_location() - state['start']).length()
                report['capsule_move_cm'] = travel
                check(travel > 60, 'movement input displaces capsule')
                check(player.mesh.get_anim_instance().get_editor_property('speed') > 70, 'locomotion graph receives actual speed')
                player.character_movement.stop_movement_immediately()
                state['root_start'] = player.get_actor_location()
                target = state['target']
                target.set_actor_location(state['root_start'] + unreal.Vector(170, 0, -2), False, False)
                player.set_actor_rotation(unreal.Rotator(), False)
                state['health_before'] = target.get_editor_property('attributes').get_current_health()
                check(player.start_move('DrawSlash'), 'draw slash montage starts')
                phase('attack')
        elif current == 'attack':
            player = state['player']
            report['snapshots'].append(dict(t=elapsed, move=str(player.get_current_move()),
                location=list(player.get_actor_location().to_tuple()), gauge=player.get_spirit_gauge(),
                target_hp=state['target'].get_editor_property('attributes').get_current_health()))
            if elapsed > 5.0:
                damage = state['health_before'] - state['target'].get_editor_property('attributes').get_current_health()
                report['attack_damage'] = damage
                report['attack_root_cm'] = (player.get_actor_location() - state['root_start']).length()
                check(damage > 0, 'source attack window applies attribute damage')
                check(player.get_spirit_gauge() > 0, 'normal attack hit builds spirit gauge')
                check(player.get_current_move().is_none(), 'montage completion releases foreground action')
                check(report['attack_root_cm'] > 5, 'montage root motion displaces capsule')
                finish()
    except Exception:
        finish(traceback.format_exc())


handle = unreal.register_slate_post_tick_callback(tick)
