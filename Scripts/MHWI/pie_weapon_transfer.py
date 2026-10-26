"""Actual PIE contract checks for whole-weapon contact and continuous transfer.

Uses the existing source weapon runner: real Enhanced Input, formal data/costs,
draw/sheathe/special/Iai/interrupt/death. No production asset is edited or saved.
Import is inert. ``run(max_fps=None)`` controls PIE, so coordinate its execution.
Nominal reference points are fitting markers inside source function-1/2 skin;
their animation is measured from the actual runtime bones, not the component
origin. This does not prove every skinned vertex has no body penetration.
"""
from __future__ import annotations

from pathlib import Path
import time
import traceback

import pie_native_weapon as native
import pie_behavior_corrections as behavior

try:
    import unreal
except ImportError:
    unreal = None

_ACTIVE = None


def smooth(position, start, end):
    alpha = max(0., min(1., (position-start)/max(end-start, .000001)))
    return alpha*alpha*(3.-2.*alpha)


def grip_weight(reference_y):
    # Source mesh weights from twelve nearest grip vertices, not an assumed
    # rigid parent. Values are independently recorded in source-grip-skin.json.
    knots = [(-66.485203, .520039097), (-63., .520039097),
             (-60., .449657857), (-55., .449657857),
             (-40., .330400785), (-12., .149560119)]
    value = knots[0][1]
    for a, b in zip(knots, knots[1:]):
        if reference_y < b[0]:
            alpha = max(0., min(1., (reference_y-a[0])/(b[0]-a[0])))
            return a[1]+(b[1]-a[1])*alpha
        value = b[1]
    return value


class WeaponTransferRunner(native.NativeWeaponRunner):
    def __init__(self, max_fps, capture_holds=False):
        super().__init__(False, max_fps)
        self.report_file = Path(unreal.Paths.project_saved_dir()) / 'MHWIImport/WeaponTransfer-20261024/PIE-transfer.json'
        if capture_holds:
            self.report_file = self.report_file.with_name('PIE-transfer-capture.json')
        if max_fps is not None:
            suffix = '-capture' if capture_holds else ''
            self.report_file = self.report_file.with_name('PIE-transfer%s-%gfps.json' % (suffix, max_fps))
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        self.report['suite'] = self.requested = 'weapon_transfer'
        self.report['notes'].append(
            'Contact checks measure source function-2 animated grip and sheath mouth; '
            'sword/sheath component origins need not coincide while the hilt retracts.')
        self.last_move = None
        self.move_started = time.monotonic()
        self.capture_holds = bool(capture_holds)
        self.capture_state = None
        self.capture_done = False
        self.capture_run = str(time.time_ns())
        self.report['capture_holds'] = self.capture_holds
        if self.capture_holds:
            self.report['notes'].append(
                'Visual-only capture freezes this temporary pawn with CustomTimeDilation=0 '
                'after the source pose has settled; this segment cannot validate original '
                'game rhythm, action timing, or the 3.5s hold duration. Dilation and camera '
                'are restored before the remaining functional cases continue.')
        # Ordinary poses also retain the real weighted grip, beyond the
        # draw/hold/Iai lifecycle inherited from the weapon-event regression.
        self.jobs[3:3] = [('ordinary_overhead', 'light', 'OverheadSlash', 'idle'),
                          ('ordinary_thrust', 'thrust', 'Thrust', 'idle'),
                          ('drawn_roll', 'evade', 'Roll', 'idle')]

    def _begin_suite(self, name):
        # Native runner invokes _sample while creating its initial state.
        sequence = unreal.load_asset('/Game/MHWI/Animations/Weapons/A_wg03_00_001')
        pose = unreal.AnimPoseExtensions.get_reference_pose(sequence.get_editor_property('skeleton'))
        self.grip_bind = {name: unreal.AnimPoseExtensions.get_bone_pose(
            pose, name, unreal.AnimPoseSpaces.WORLD) for name in ('bone_001', 'bone_002')}
        super()._begin_suite(name)
        self.report['suite'] = 'weapon_transfer'

    def _sample(self, label):
        result = super()._sample(label)
        move = self._current()
        if move != self.last_move:
            self.entry_grip_reference_y = getattr(self, 'last_grip_reference_y', -12.)
            self.last_move = move
            self.move_started = time.monotonic()
        position = self._position()
        if self.anim.get_current_active_montage() is None and move != 'None':
            position = getattr(self, 'last_contact_position', position)
        self.last_contact_position = position
        held = self.pawn.is_special_sheath_holding()
        inserted = 1. if held else smooth(position, 60./60., 73./60.)
        reference_y = -12. + (-66.485203 + 12.)*inserted if move == 'SpecialSheathe' else -12.
        if move.startswith('Iai'):
            amount = smooth(position, 0., 8./60.)
            reference_y = self.entry_grip_reference_y + (-12.-self.entry_grip_reference_y)*amount
        self.last_grip_reference_y = reference_y
        skinned = {}
        for name, bind in self.grip_bind.items():
            bone_point = unreal.MathLibrary.inverse_transform_location(bind, unreal.Vector(0, reference_y, 0))
            skinned[name] = self.weapon.get_socket_transform(name).transform_location(bone_point)
        weight = grip_weight(reference_y)
        actual_grip = skinned['bone_001']*(1.-weight)+skinned['bone_002']*weight
        right = self.pawn.mesh.get_socket_transform('bone_012').transform_location(unreal.Vector(-7, 2, 0))
        left = self.pawn.mesh.get_socket_transform('bone_008').transform_location(unreal.Vector(7, 2, 0))
        sheath = self.pawn.get_editor_property('scabbard_mesh')
        sheath_world = sheath.get_socket_transform(unreal.Name())
        sword_world = self.weapon.get_socket_transform(unreal.Name())
        mouth = sheath_world.transform_location(unreal.Vector(0, 21, 0))
        contact = dict(label=label, move=move, position=position, held=held,
            source_motion=int(result[0]), weapon_position=float(result[1]),
            grip_reference_y=reference_y, grip_error_cm=(right-actual_grip).length(),
            mouth_error_cm=(left-mouth).length(),
            sword_socket=str(self.weapon.get_attach_socket_name()),
            scabbard_socket=str(sheath.get_attach_socket_name()))
        settled = time.monotonic()-self.move_started > .20
        should_grip = move == 'SpecialSheathe' or (move == 'Draw' and position >= 25./60.) \
            or (move == 'Sheathe' and position < 40./60.) \
            or (move.startswith('Iai') and position >= 8./60. and settled) \
            or (move in ('OverheadSlash', 'Thrust', 'Roll') and settled)
        if should_grip:
            self._check(contact['grip_error_cm'] < .5, label+': animated grip stays within .5cm of right palm')
        if (move == 'SpecialSheathe' or move.startswith('Iai')) and settled:
            self._check(contact['mouth_error_cm'] < .5, label+': sheath mouth stays within .5cm of left palm')
        if held:
            sword_axis = (sword_world.transform_location(unreal.Vector(0, 1, 0))-sword_world.translation).normal()
            sheath_axis = (sheath_world.transform_location(unreal.Vector(0, 1, 0))-sheath_world.translation).normal()
            separation = sword_world.translation-sheath_world.translation
            contact['axes_dot'] = sword_axis.dot(sheath_axis)
            contact['axis_separation_cm'] = separation.cross(sheath_axis).length()
            self._check(contact['axes_dot'] > .9999, 'held blade and sheath point along the same axis')
            self._check(contact['axis_separation_cm'] < .5, 'held blade lies on the sheath mouth line')
        self._record('contact_frames', **contact)
        return result

    def _restore_capture_camera(self):
        if not self.capture_state:
            return
        state = self.capture_state
        self.capture_state = None
        errors = []
        try:
            self.pawn.set_editor_property('custom_time_dilation', state['dilation'])
            self._record('capture_freeze', action='restored', custom_time_dilation=state['dilation'],
                         frozen_wall_seconds=time.monotonic()-state['frozen_at'])
        except Exception as exc:
            errors.append('pawn dilation: '+str(exc))
        try:
            self.pc.set_control_rotation(state['rotation'])
        except Exception as exc:
            errors.append('controller rotation: '+str(exc))
        arm = state['arm']
        for key, value in state['properties'].items():
            try:
                arm.set_editor_property(key, value)
            except Exception as exc:
                errors.append(key+': '+str(exc))
        if errors:
            raise RuntimeError('Capture cleanup: '+'; '.join(errors))

    def _phase(self, name, budget=30.):
        if self.capture_holds and name == 'weapon_hold_settle' \
                and getattr(self, 'watch', {}).get('label') == 'special_for_iai':
            budget = 45.
        return super()._phase(name, budget)

    def _phase_weapon_hold_settle(self, elapsed):
        if not self.capture_holds or self.capture_done or self.watch['label'] != 'special_for_iai':
            return super()._phase_weapon_hold_settle(elapsed)
        self._sample('special hold camera capture')
        self._check(self.pawn.is_special_sheath_holding(), 'multi-view capture retains the settled special pose')
        if elapsed < .35:
            return
        if self.capture_state is None:
            arm = self.pawn.get_editor_property('spring_arm')
            self.capture_state = dict(arm=arm, rotation=self.pc.get_control_rotation(),
                dilation=self.pawn.get_editor_property('custom_time_dilation'), frozen_at=time.monotonic(),
                properties={key: arm.get_editor_property(key) for key in (
                    'target_arm_length', 'socket_offset', 'do_collision_test')},
                index=0, stage='view', at=0., task=None)
            self.pawn.set_editor_property('custom_time_dilation', 0.)
            self._record('capture_freeze', action='frozen_for_visual_only', custom_time_dilation=0.,
                         original_dilation=self.capture_state['dilation'], timing_validation=False)
            arm.set_editor_property('target_arm_length', 300.)
            arm.set_editor_property('socket_offset', unreal.Vector(0, 0, 25))
            arm.set_editor_property('do_collision_test', False)
        state = self.capture_state
        views = [('front-three-quarter', 145.), ('side', 90.), ('opposite-three-quarter', 215.)]
        name, relative_yaw = views[state['index']]
        if state['stage'] == 'view':
            self.pc.set_control_rotation(unreal.Rotator(pitch=-8., yaw=self._actor_yaw()+relative_yaw, roll=0.))
            state.update(stage='settle', at=time.monotonic())
            return
        if state['stage'] == 'settle':
            if time.monotonic()-state['at'] < .18:
                return
            path = self.report_file.parent / ('special-hold-frozen-'+self.capture_run+'-'+name+'.png')
            state['path'] = path
            state['task'] = unreal.AutomationLibrary.take_high_res_screenshot(1280, 960, str(path))
            self._check(state['task'] is not None and state['task'].is_valid_task(), 'PIE screenshot task accepted '+name)
            self._record('capture_views', view=name, file=str(path), move=self._current(),
                held=self.pawn.is_special_sheath_holding(), internal_motion=int(self.pawn.get_weapon_motion_no()),
                visual_freeze=True, custom_time_dilation=self.pawn.get_editor_property('custom_time_dilation'),
                hunter_transform=str(self.pawn.get_actor_transform()),
                control_rotation=str(self.pc.get_control_rotation()),
                weapon_transform=str(self.weapon.get_socket_transform(unreal.Name())),
                scabbard_transform=str(self.pawn.get_editor_property('scabbard_mesh').get_socket_transform(unreal.Name())))
            state.update(stage='capture', at=time.monotonic())
            return
        if not state['task'].is_task_done() or not state['path'].exists():
            return
        self._check(state['path'].stat().st_size > 10000, 'captured PNG exists '+name)
        state['index'] += 1
        if state['index'] < len(views):
            state['stage'] = 'view'
            return
        self.capture_done = True
        self._restore_capture_camera()
        return super()._phase_weapon_hold_settle(elapsed)

    def _finish(self, error=None):
        global _ACTIVE
        try:
            self._restore_capture_camera()
        except Exception as exc:
            self.report.setdefault('notes', []).append('Camera restore failed: '+str(exc))
        super()._finish(error)
        _ACTIVE = None


def run(max_fps=None, capture_holds=False):
    global _ACTIVE
    if unreal is None:
        raise RuntimeError('Run in Unreal Editor Python')
    if behavior._ACTIVE is not None and not behavior._ACTIVE.done:
        raise RuntimeError('Wait for the existing PIE runner')
    runner = WeaponTransferRunner(max_fps, capture_holds)
    _ACTIVE = native._ACTIVE = behavior._ACTIVE = runner
    try:
        runner.prepare_editor()
        runner.handle = unreal.register_slate_post_tick_callback(runner.tick)
    except Exception:
        runner._finish(traceback.format_exc())
        raise
    return dict(started=True, report=str(runner.report_file))
