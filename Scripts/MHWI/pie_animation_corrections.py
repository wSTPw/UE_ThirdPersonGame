"""CHG-004: real locomotion and input chains, source pose identity and hit timing."""
import json
import time
import traceback
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir())/'MHWIImport/PIE-animation-corrections.json'
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = {'phase': 'load', 'wall': time.monotonic(), 'at': time.monotonic(),
         'throttle': settings.get_editor_property('bThrottleCPUWhenNotForeground')}
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = {'passed': False, 'checks': [], 'normal_chain': [], 'spirit_chain': [], 'poses': [], 'movement': {}}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def check(ok, label):
    report['checks'].append({'check': label, 'passed': bool(ok)})
    if not ok: raise AssertionError(label)


def phase(name):
    state.update(phase=name, at=time.monotonic(), samples=[])


def inject(name, xyz=(1, 0, 0)):
    state['sub'].inject_input_vector_for_action(state['actions'][name], unreal.Vector(*xyz), [], [])


def current(): return str(state['pawn'].get_current_move())


def position():
    m = state['anim'].get_current_active_montage()
    return state['anim'].montage_get_position(m) if m else 0


def align():
    p = state['pawn']; loc = p.get_actor_location()
    state['target'].set_actor_location(loc + p.get_actor_forward_vector()*150 + unreal.Vector(0, 0, -4), False, False)


def pose_check(name, clip):
    p = state['pawn']; t = position()
    seq = unreal.load_asset('/Game/MHWI/Animations/LongSword/A_' + clip)
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t,
        unreal.AnimPoseEvaluationOptions(extract_root_motion=True, incorporate_root_motion_into_pose=False))
    errors = {}
    for bone in ['bone_003', 'bone_008', 'bone_012']:
        expected = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)
        actual = p.mesh.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)
        errors[bone] = (actual.translation-expected.translation).length()
    report['poses'].append({'move': name, 'clip': clip, 'seconds': t, 'error_cm': errors})
    check(max(errors.values()) < 2, name + ' evaluated body pose matches corrected source clip')


def finish(error=None):
    report['passed'] = error is None
    if error: report['error'] = error; unreal.log_error(error)
    settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
    OUT.write_text(json.dumps(report, indent=2), encoding='utf8')
    unreal.unregister_slate_post_tick_callback(handle)
    if level.is_in_play_in_editor(): level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick(dt):
    try:
        if time.monotonic()-state['wall'] > 85: raise TimeoutError(state['phase'])
        elapsed = time.monotonic()-state['at']; stage = state['phase']
        if stage == 'load':
            check(not level.is_in_play_in_editor(), 'fresh PIE fixture starts without old preview world')
            check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads'); phase('start')
        elif stage == 'start': level.editor_request_begin_play(); phase('wait')
        elif stage == 'wait':
            world = editor.get_game_world()
            pawn = unreal.GameplayStatics.get_player_character(world, 0) if world else None
            if not pawn: return
            check(isinstance(pawn, unreal.MHWICharacter), 'saved Blueprint spawns MHWI pawn')
            check(pawn.is_sheathed(), 'fresh pawn starts sheathed')
            targets = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MHWITrainingTarget)
            for target in targets: target.set_editor_property('enable_attacks', False)
            contexts = [o for o in unreal.ObjectIterator(unreal.InputMappingContext) if o.get_outer() == pawn]
            subs = []
            for sub in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem):
                present = sub.has_mapping_context(contexts[0])
                if present[0] if isinstance(present, tuple) else present: subs.append(sub)
            state.update(pawn=pawn, anim=pawn.mesh.get_anim_instance(), world=world, sub=subs[0],
                actions={o.get_name(): o for o in unreal.ObjectIterator(unreal.InputAction) if o.get_outer() == pawn},
                target=targets[0], target_attrs=targets[0].get_editor_property('attributes'))
            data = pawn.get_editor_property('moveset')
            check(data.get_editor_property('sheathed_walk').get_name() == 'A_co00_00_203', 'saved sheathed walk uses standing forward loop')
            check(data.get_editor_property('sheathed_run').get_name() == 'A_co00_00_090', 'saved sheathed run uses standing forward loop')
            pawn.set_actor_location(unreal.Vector(0, -1200, 94.15), False, True)
            pawn.set_actor_rotation(unreal.Rotator(), False)
            unreal.GameplayStatics.get_player_controller(world, 0).set_control_rotation(unreal.Rotator())
            state['origin'] = pawn.get_actor_location(); phase('walk')
        elif stage in ['walk', 'sprint']:
            p = state['pawn']; inject('MHWI_Move', (0, 1, 0))
            if stage == 'sprint': inject('MHWI_Sprint')
            if elapsed > .3:
                root = p.mesh.get_socket_location('bone_root')
                state['samples'].append({n: (p.mesh.get_socket_location(n)-root).z for n in ['bone_003', 'bone_008', 'bone_012']})
            if elapsed > 1.1:
                travel = (p.get_actor_location()-state['origin']).length()
                report['movement'][stage] = {'travel_cm': travel, 'speed': p.mesh.get_anim_instance().get_editor_property('speed'), 'samples': state['samples']}
                check(travel > (145 if stage == 'walk' else 330), stage + ' Enhanced Input advances capsule at expected speed')
                check(p.is_sheathed(), stage + ' retains sheathed stance')
                check(min(s['bone_003'] for s in state['samples']) > 120, stage + ' keeps standing head height')
                check(max(max(s['bone_008'], s['bone_012']) for s in state['samples']) < 125, stage + ' avoids raised ladder-climbing arms')
                check(str(p.get_editor_property('weapon_mesh').get_attach_socket_name()) == 'bone_002', stage + ' retains fitted back weapon mount')
                state['origin'] = p.get_actor_location()
                if stage == 'walk': phase('sprint')
                else:
                    inject('MHWI_Move', (0, 0, 0)); inject('MHWI_Sprint', (0, 0, 0)); phase('release')
        elif stage == 'release' and elapsed > .35:
            p = state['pawn']; p.character_movement.stop_movement_immediately()
            p.set_actor_location(unreal.Vector(0, 0, 94.15), False, True)
            p.set_actor_rotation(unreal.Rotator(), False); align()
            state.update(hp_before=state['target_attrs'].get_current_health(), normal_index=0, queued=set(), pose_checked=set())
            inject('MHWI_Command_0'); phase('normal')
        elif stage == 'normal':
            align(); name = current()
            expected = ['DrawSlash', 'OverheadSlash', 'Thrust', 'RisingSlash', 'OverheadSlash', 'Thrust']
            order = report['normal_chain']
            if name != 'None' and (not order or order[-1] != name):
                check(name == expected[len(order)], 'left-click stage ' + str(len(order)+1) + ' is ' + expected[len(order)])
                order.append(name)
            if name == 'RisingSlash' and position() > .22 and name not in state['pose_checked']:
                pose_check(name, 'w03_00_107'); state['pose_checked'].add(name)
            if len(order) < len(expected) and name != 'None':
                key = len(order)
                definition = state['pawn'].get_editor_property('moveset').get_editor_property('moves')[name]
                if position() >= definition.get_editor_property('cancel_start')-.04 and key not in state['queued']:
                    inject('MHWI_Command_0'); state['queued'].add(key)
            if name == 'None' and order:
                check(order == expected, 'six left-click actions complete in corrected order')
                damage = state['hp_before']-state['target_attrs'].get_current_health()
                report['normal_damage'] = damage
                check(abs(damage-124) < .1, 'normal chain produces exactly six correctly timed hits')
                check(abs(state['pawn'].get_spirit_gauge()-54) < .1, 'normal chain earns gauge once per hit')
                state.update(hp_before=state['target_attrs'].get_current_health(), queued=set())
                inject('MHWI_Command_2'); phase('spirit')
        elif stage == 'spirit':
            align(); name = current(); expected = ['SpiritI', 'SpiritII', 'SpiritIII', 'SpiritRoundslash']; order = report['spirit_chain']
            if name != 'None' and (not order or order[-1] != name):
                check(name == expected[len(order)], 'spirit stage ' + str(len(order)+1) + ' is ' + expected[len(order)])
                order.append(name)
                report.setdefault('spirit_gauge_samples', []).append({'move': name, 'gauge': state['pawn'].get_spirit_gauge()})
            if name == 'SpiritII' and position() > .22 and name not in state['pose_checked']:
                pose_check(name, 'w03_00_106'); state['pose_checked'].add(name)
            if len(order) < len(expected) and name != 'None':
                definition = state['pawn'].get_editor_property('moveset').get_editor_property('moves')[name]
                if position() >= definition.get_editor_property('cancel_start')-.04 and name not in state['queued']:
                    inject('MHWI_Command_2'); state['queued'].add(name)
            if name == 'None' and order:
                check(order == expected, 'full spirit chain completes with corrected second animation')
                damage = state['hp_before']-state['target_attrs'].get_current_health(); report['spirit_damage'] = damage
                report['final_gauge'] = state['pawn'].get_spirit_gauge()
                check(abs(damage-132) < .1, 'spirit chain produces exactly six correctly timed hits')
                check(abs(state['pawn'].get_spirit_gauge()-6) < .1, 'four spirit costs consume gauge exactly once each')
                check(state['pawn'].get_spirit_level() == 1, 'roundslash hit raises white spirit level')
                check(state['pawn'].is_sheathed(), 'roundslash restores sheathed stance')
                check(state['pose_checked'] == {'RisingSlash', 'SpiritII'}, 'both swapped actions have runtime source-pose evidence')
                check(state['pawn'].request_input(unreal.MHWIInput.LIGHT), 'input remains usable after complete chain')
                state['pawn'].interrupt_move()
                check(state['pawn'].get_current_move().is_none(), 'interrupt clears corrected foreground action')
                finish()
    except Exception: finish(traceback.format_exc())


handle = unreal.register_slate_post_tick_callback(tick)
