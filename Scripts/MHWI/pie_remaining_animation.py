"""B20 real PIE movement/roll-recovery and four-chain IK consumer regression.

Uses production pawn/AnimGraph/assets. Movement is supplied through AddMovementInput;
the visibility-only terrain probe and damage are transient test-world fixtures.
No formal asset, source identity, private move state or timing window is replaced.
"""
import datetime
import json
import math
import time
import traceback
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir(), globals().get('MHWI_REPORT_PATH', 'MHWIRestoration/B20-20261027/PIE-animation-consumers.json'))
FOOT_BONE = globals().get('MHWI_FOOT_BONE', 'bone_016')
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
state = dict(phase='load', at=time.monotonic(), started=time.monotonic(), move=None,
             throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'), samples=[])
report = dict(passed=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), checks=[],
              scope='Production PIE consumers, not execution of the original game or all native source identities')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
state['max_fps'] = unreal.SystemLibrary.get_console_variable_float_value('t.MaxFPS')
if globals().get('MHWI_MAX_FPS'):
    unreal.SystemLibrary.execute_console_command(None, 't.MaxFPS %g' % MHWI_MAX_FPS)
report['requested_max_fps'] = globals().get('MHWI_MAX_FPS')
report['terrain_test_bone'] = FOOT_BONE
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def prop(obj, name):
    if name == 'in_air':
        return obj.get_editor_property('bInAir')
    try:
        return obj.get_editor_property(name)
    except Exception:
        return obj.get_editor_property('b_' + name)


def check(value, label, **data):
    report['checks'].append(dict(check=label, passed=bool(value), **data))
    if not value:
        raise AssertionError(label + ': ' + str(data))


def phase(name, move=None):
    state.update(phase=name, at=time.monotonic(), move=move, seen=set())
    if state.get('world'):
        state['game_at'] = unreal.GameplayStatics.get_time_seconds(state['world'])


def set_profile(value):
    # Transient AnimInstance fixture only; formal asset/CDO remains untouched.
    unreal.get_default_object(unreal.SystemLibrary).call_method('SetObjectPropertyByName',
        args=(state['anim'], unreal.Name('EquipmentIKProfile'), value))
    if prop(state['anim'], 'equipment_ik_profile') != value:
        raise AssertionError('Transient Profile fixture assignment failed')


def alphas():
    a = state['anim']
    return [float(prop(a, name + '_ik_alpha')) for name in ('left_arm', 'right_arm', 'left_foot', 'right_foot')]


def playback():
    text = state['player'].get_native_playback_diagnostic()
    return dict(token.split('=', 1) for token in text.split()) if text != 'none' else {}


def sample():
    a = state['anim']
    active = bool(prop(a, 'locomotion_transition_active'))
    motion = int(prop(a, 'locomotion_transition_motion'))
    if active:
        state['seen'].add(motion)
    p = state['player']
    v = p.get_velocity()
    row = dict(phase=state['phase'], seconds=unreal.GameplayStatics.get_time_seconds(state['world']), motion=motion,
               active=active, clip_seconds=float(prop(a, 'locomotion_transition_time')),
               speed=(v.x*v.x+v.y*v.y)**0.5, paused=unreal.GameplayStatics.is_game_paused(state['world']), dilation=prop(p, 'custom_time_dilation'), alphas=alphas(), move=str(p.get_current_move()))
    state['samples'].append(row)
    return row


def finish(error=None):
    report.update(passed=error is None, error=error, samples=state['samples'])
    try:
        if state.get('fixture'):
            state['fixture'].destroy_actor()
        if state.get('player'):
            state['player'].set_input_blocked(False)
        if state.get('profile'):
            set_profile(state['profile'])
        if state.get('capture_original'):
            player = state['player']
            player.set_editor_property('custom_time_dilation', state['capture_original']['dilation'])
            state['pc'].set_control_rotation(state['capture_original']['rotation'])
            for key, value in state['capture_original']['arm'].items():
                prop(player, 'spring_arm').set_editor_property(key, value)
        if state.get('capture_camera'):
            state['pc'].set_view_target_with_blend(state['player'], 0.0)
            state['capture_camera'].destroy_actor()
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
        settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
        unreal.SystemLibrary.execute_console_command(None, 't.MaxFPS %g' % state['max_fps'])
        unreal.unregister_slate_post_tick_callback(state['handle'])
        level.editor_request_end_play()
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    if error:
        unreal.log_error(error)


def _tick(delta):
    try:
        p = state['phase']
        elapsed = time.monotonic()-state['at']
        if time.monotonic()-state['started'] > 160:
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
            state.update(world=world, player=player, target=targets[0], anim=player.mesh.get_anim_instance())
            check(prop(state['anim'], 'equipment_ik_profile') is not None, 'real AnimInstance has the saved IK Profile')
            check(player.request_input(unreal.MHWIInput.LIGHT), 'draw request accepted')
            phase('draw')
            return

        player, anim = state['player'], state['anim']
        if state['move']:
            player.add_movement_input(unreal.Vector(*state['move']), 1.0, False)
        row = sample()
        if elapsed > (25.0 if p == 'capture' else 6.0):
            raise TimeoutError('Phase stalled: '+p)
        if p == 'draw' and player.get_current_move().is_none() and not player.is_sheathed():
            player.set_actor_rotation(unreal.Rotator(), False)
            phase('walk', (1, 0, 0))
        elif p == 'walk' and elapsed > 1.4:
            check(5 in state['seen'], 'source-qualified WALK entry005 is selected by real movement')
            check(row['speed'] > 50, 'CharacterMovement actually moves during transition')
            check(not row['active'], 'start transition completes and returns to base BlendSpace')
            phase('stop')
        elif p == 'stop' and elapsed > 1.3:
            check(8 in state['seen'], 'WALK_END008 is consumed on movement release')
            check(row['speed'] < 1 and not row['active'], 'stop completes without a stuck pose state')
            player.set_actor_rotation(unreal.Rotator(), False)
            phase('left', (-1, -1, 0))
        elif p == 'left' and elapsed > 0.45:
            check(6 in state['seen'], 'left-directed WALK entry consumes006')
            phase('left_stop')
        elif p == 'left_stop' and elapsed > 1.2:
            player.set_actor_rotation(unreal.Rotator(), False)
            phase('right', (-1, 1, 0))
        elif p == 'right' and elapsed > 0.45:
            check(7 in state['seen'], 'right-directed WALK entry consumes007')
            phase('right_stop')
        elif p == 'right_stop' and elapsed > 1.2:
            state['roll_serial'] = player.get_natural_roll_completion_serial()
            player.set_actor_rotation(unreal.Rotator(), False)
            accepted = player.request_input(unreal.MHWIInput.EVADE)
            if not accepted:
                moveset = player.get_editor_property('moveset')
                moves = moveset.get_editor_property('moves')
                definition = next(v for k,v in moves.items() if str(k)=='Roll')
                state['samples'].append({'start_failure':player.get_last_move_start_failure(),'roll_diagnostic':{key:str(definition.get_editor_property(key)) for key in ['montage','sheathed_montage','play_rate','spirit_cost','require_spirit_level','require_nonzero_gauge']},'alive':str(player.get_editor_property('attributes').get_current_health()),'control':str(player.get_control_state()),'blocked':player.is_input_blocked(),'actual_montage':str(anim.get_current_active_montage())})
                template = definition.get_editor_property('montage')
                diagnostic = {'template_seconds':template.get_play_length()}
                if hasattr(unreal,'duplicate_object'):
                    copied = unreal.duplicate_object(template, player)
                    diagnostic['duplicate_seconds'] = copied.get_play_length()
                copied = unreal.find_object(player, template.get_name())
                diagnostic['actor_copy'] = str(copied)
                if copied:
                    diagnostic['actor_copy_seconds'] = copied.get_play_length()
                diagnostic['direct_template_play_seconds'] = anim.montage_play(template, 1.0)
                state['samples'].append({'duplicate_probe':diagnostic})
            check(accepted, 'real drawn roll starts')
            phase('roll_forward', (1, 0, 0))
        elif p == 'roll_forward' and 14 in state['seen']:
            check(player.get_natural_roll_completion_serial() != state['roll_serial'], '014 is gated by a real natural roll completion')
            check(True, 'DODGE_TO_MOVE014 is consumed after the roll')
            check(player.request_input(unreal.MHWIInput.LIGHT), 'real Light starts from the visible014 exit')
            diagnostic = player.get_last_native_entry_diagnostic()
            check('previous=3/65 ' in diagnostic and 'motion=14 ' in diagnostic,
                  '014 actual owner overrides the cached completed roll in R06', diagnostic=diagnostic)
            state['forward_main_seen'] = False
            phase('forward_attack')
        elif p == 'forward_attack':
            live = playback()
            if not state['forward_main_seen'] and live.get('connector') == '0' and live.get('body') == '101':
                check(48 <= float(live['frame']) < 60, '014 recovery actually commits101 at original MBD131-to101 frame48', playback=live)
                state['forward_main_seen'] = True
            if player.get_current_move().is_none():
                check(state['forward_main_seen'], '014 recovery main was observed before completion')
                phase('after_forward')
        elif p == 'after_forward' and elapsed > 1.3:
            player.set_actor_rotation(unreal.Rotator(), False)
            state['roll_serial'] = player.get_natural_roll_completion_serial()
            check(player.request_input(unreal.MHWIInput.EVADE), 'second real drawn roll starts')
            phase('roll_reverse', (-1, 0, 0))
        elif p == 'roll_reverse' and 15 in state['seen']:
            check(player.get_natural_roll_completion_serial() != state['roll_serial'], '015 retains the real completed-roll owner')
            check(True, 'DODGE_TO_TURN015 is consumed for reverse recovery')
            check(player.request_input(unreal.MHWIInput.LIGHT), 'real Light starts from the visible015 exit')
            diagnostic = player.get_last_native_entry_diagnostic()
            check('previous=3/66 ' in diagnostic and 'motion=15 ' in diagnostic,
                  '015 actual owner overrides the cached completed roll in R06', diagnostic=diagnostic)
            state['reverse_main_seen'] = False
            phase('reverse_attack')
        elif p == 'reverse_attack':
            live = playback()
            if not state['reverse_main_seen'] and live.get('connector') == '0' and live.get('body') == '101':
                check(48 <= float(live['frame']) < 60, '015 recovery actually commits101 at original MBD131-to101 frame48', playback=live)
                state['reverse_main_seen'] = True
            if player.get_current_move().is_none():
                check(state['reverse_main_seen'], '015 recovery main was observed before completion')
                phase('after_reverse')
        elif p == 'after_reverse' and elapsed > 1.3:
            check(player.request_input(unreal.MHWIInput.LIGHT), 'combat can interrupt the locomotion layer')
            phase('attack')
        elif p == 'attack' and not player.get_current_move().is_none():
            check(not row['active'] and row['alphas'][1] > 0.0
                  and row['alphas'][0] == row['alphas'][2] == row['alphas'][3] == 0.0,
                  'combat Slot keeps the drawn weapon in the right hand while suppressing other IK chains',
                  alphas=row['alphas'])
            phase('attack_end')
        elif p == 'attack_end' and player.get_current_move().is_none():
            phase('ik_idle')
        elif p == 'ik_idle' and elapsed > 0.4:
            check(row['alphas'][1] > 0 and row['alphas'][2] > 0 and row['alphas'][3] > 0,
                  'drawn idle feeds right hand and both foot solvers', alphas=row['alphas'])
            mesh = player.mesh
            foot = mesh.get_socket_location(FOOT_BONE)
            state['foot_before'] = [foot.x, foot.y, foot.z]
            transform = unreal.Transform()
            transform.translation = unreal.Vector(foot.x, foot.y, 5.0)
            statics = unreal.get_default_object(unreal.GameplayStatics)
            fixture = statics.call_method('BeginDeferredActorSpawnFromClass', args=(state['world'], unreal.StaticMeshActor.static_class(), transform, unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN, None))
            statics.call_method('FinishSpawningActor', args=(fixture, transform))
            fixture.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            check(fixture.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube')), 'terrain fixture mesh is assigned successfully')
            fixture.set_actor_scale3d(unreal.Vector(0.10, 0.10, 0.02))
            fixture.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            fixture.static_mesh_component.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            fixture.static_mesh_component.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_BLOCK)
            state['fixture'] = fixture
            phase('ik_terrain')
        elif p == 'ik_terrain' and elapsed > 0.4:
            foot = player.mesh.get_socket_location(FOOT_BONE)
            rise = foot.z-state['foot_before'][2]
            check(rise > 2.0, 'actual evaluated foot bone reacts to a visibility terrain step', rise_cm=rise,
                  before=state['foot_before'], after=[foot.x, foot.y, foot.z])
            state['fixture'].destroy_actor()
            state['fixture'] = None
            phase('ik_restore')
        elif p == 'ik_restore' and elapsed > 0.5:
            foot = player.mesh.get_socket_location(FOOT_BONE)
            check(abs(foot.z-state['foot_before'][2]) < 2.0, 'foot returns without accumulating previous IK displacement')
            state['profile'] = prop(anim, 'equipment_ik_profile')
            fixture = unreal.new_object(unreal.MHWIEquipmentIKProfile)
            for key in ('left_arm', 'right_arm', 'left_foot', 'right_foot', 'arm_alpha', 'foot_alpha', 'foot_trace_up', 'foot_trace_down', 'foot_sole_offset_z'):
                fixture.set_editor_property(key, prop(state['profile'], key))
            chain = prop(fixture, 'right_arm')
            chain.set_editor_property('joint_target_offset', unreal.Vector(0, 0, 15))
            fixture.set_editor_property('right_arm', chain)
            state['elbow_before'] = player.mesh.get_socket_location('bone_011')
            state['wrist_before'] = player.mesh.get_socket_location('bone_012')
            state['profile_fixture'] = fixture
            set_profile(fixture)
            phase('ik_arm')
        elif p == 'ik_arm' and elapsed > 0.3:
            elbow = player.mesh.get_socket_location('bone_011')
            wrist = player.mesh.get_socket_location('bone_012')
            change = (elbow-state['elbow_before']).length()
            drift = (wrist-state['wrist_before']).length()
            check(change > 0.5 and drift < 2.0, 'evaluated right arm responds to a transient pole target while retaining the wrist goal', elbow_change_cm=change, wrist_drift_cm=drift)
            set_profile(state['profile'])
            check(player.request_input(unreal.MHWIInput.LIGHT), 'attack starts for real special-sheath entry')
            phase('special_queue')
        elif p == 'special_queue':
            montage = anim.get_current_active_montage()
            moves = prop(prop(player, 'moveset'), 'moves')
            definition = next(v for k,v in moves.items() if str(k)==str(player.get_current_move()))
            start = float(prop(definition, 'cancel_start'))
            if montage and anim.montage_get_position(montage) >= start:
                check(player.request_input(unreal.MHWIInput.SPECIAL_SHEATHE), 'special sheath is requested through the production cancel window')
                phase('special_hold')
        elif p == 'special_hold' and player.is_special_sheath_holding():
            phase('special_settle')
        elif p == 'special_settle' and elapsed > 0.35:
            check(min(row['alphas'][:2]) > 0, 'special-sheath hold feeds both real arm solvers', alphas=row['alphas'])
            state['left_before'] = player.mesh.get_socket_location('bone_007')
            fixture = state['profile_fixture']
            chain = prop(fixture, 'left_arm')
            chain.set_editor_property('joint_target_offset', unreal.Vector(0, 0, 15))
            fixture.set_editor_property('left_arm', chain)
            set_profile(fixture)
            phase('special_left')
        elif p == 'special_left' and elapsed > 0.3:
            change = (player.mesh.get_socket_location('bone_007')-state['left_before']).length()
            check(change > 0.5, 'evaluated left arm responds during the actual special-sheath hold', elbow_change_cm=change)
            set_profile(state['profile'])
            phase('special_restored')
        elif p == 'special_restored' and elapsed > 0.3:
            if globals().get('MHWI_CAPTURE'):
                pc = unreal.GameplayStatics.get_player_controller(state['world'], 0)
                arm = prop(player, 'spring_arm')
                state['capture_original'] = dict(dilation=prop(player, 'custom_time_dilation'), rotation=pc.get_control_rotation(),
                    arm={key: prop(arm, key) for key in ('target_arm_length', 'socket_offset', 'do_collision_test')})
                state.update(pc=pc, capture_index=0, capture_stage='view', capture_task=None)
                state['capture_run'] = str(time.time_ns())
                transform = unreal.Transform()
                statics = unreal.get_default_object(unreal.GameplayStatics)
                camera = statics.call_method('BeginDeferredActorSpawnFromClass', args=(state['world'], unreal.CameraActor.static_class(), transform, unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN, None))
                statics.call_method('FinishSpawningActor', args=(camera, transform))
                state['capture_camera'] = camera
                pc.set_view_target_with_blend(camera, 0.0)
                player.set_editor_property('custom_time_dilation', 0.0)
                arm.set_editor_property('target_arm_length', 260.0)
                arm.set_editor_property('socket_offset', unreal.Vector(0, 0, 25))
                arm.set_editor_property('do_collision_test', False)
                phase('capture')
            else:
                player.interrupt_move()
                player.set_input_blocked(True)
                phase('blocked')
        elif p == 'capture':
            views = [('front', 20.0), ('side', 90.0), ('opposite', 200.0)]
            name, yaw = views[state['capture_index']]
            if state['capture_stage'] == 'view':
                focus = player.get_actor_location()
                angle = math.radians(player.get_actor_rotation().yaw+yaw)
                location = focus+unreal.Vector(450*math.cos(angle), 450*math.sin(angle), 65)
                state['capture_camera'].set_actor_location(location, False, True)
                state['capture_camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, focus), False)
                state.update(capture_stage='settle', capture_at=time.monotonic())
            elif state['capture_stage'] == 'settle' and time.monotonic()-state['capture_at'] > 0.25:
                path = (OUT.parent / ('IK-special-'+state['capture_run']+'-'+name+'.png')).resolve()
                state['capture_path'] = path
                # FinishLoadingBeforeScreenshot pumps Slate. Mark waiting before
                # the call, and the outer tick guard rejects nested callbacks.
                state['capture_stage'] = 'wait'
                state['capture_task'] = unreal.AutomationLibrary.take_high_res_screenshot(1280, 960, str(path))
                check(state['capture_task'] is not None and state['capture_task'].is_valid_task(), 'unique screenshot task is valid')
            elif state['capture_stage'] == 'wait' and state['capture_task'].is_task_done() and state['capture_path'].exists():
                check(player.is_special_sheath_holding() and state['capture_path'].stat().st_size > 10000,
                      'multi-view screenshot retains the real special hold', path=str(state['capture_path']), visual_freeze=True)
                state['capture_index'] += 1
                if state['capture_index'] < len(views):
                    state['capture_stage'] = 'view'
                    return
                player.set_editor_property('custom_time_dilation', state['capture_original']['dilation'])
                state['pc'].set_control_rotation(state['capture_original']['rotation'])
                for key, value in state['capture_original']['arm'].items():
                    prop(player, 'spring_arm').set_editor_property(key, value)
                state['capture_original'] = None
                state['pc'].set_view_target_with_blend(player, 0.0)
                state['capture_camera'].destroy_actor()
                state['capture_camera'] = None
                player.interrupt_move()
                player.set_input_blocked(True)
                phase('blocked')
        elif p == 'blocked' and row['seconds']-state['game_at'] > 0.2:
            check(max(row['alphas']) == 0 and not row['active'], 'menu gate clears IK and locomotion consumers')
            player.set_input_blocked(False)
            player.set_actor_location(player.get_actor_location()+unreal.Vector(0,0,120), False, True)
            player.character_movement.set_movement_mode(unreal.MovementMode.MOVE_FALLING, 0)
            phase('air')
        elif p == 'air' and prop(anim, 'in_air'):
            check(max(row['alphas']) == 0 and not row['active'], 'airborne state disables all ground IK/transition consumers')
            phase('land')
        elif p == 'land' and not prop(anim, 'in_air'):
            state['player'].get_editor_property('attributes').apply_damage(10000.0, state['target'])
            phase('dead')
        elif p == 'dead' and elapsed > 0.2:
            check(prop(anim, 'dead') and max(row['alphas']) == 0 and not row['active'], 'death invalidates all animation consumer goals')
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
