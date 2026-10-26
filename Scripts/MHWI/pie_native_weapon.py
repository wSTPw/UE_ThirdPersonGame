"""Focused real-PIE tests for native internal weapon clips/events.

Import is inert. run(strict_source_hold=False) starts an async Slate state machine.
Uses the formal moveset, actual Enhanced Input, real costs and native getters.
No assets are saved. The inherited runner restores input/throttle and ends PIE.

Strict hold additionally requires source306's 80->0 event after SpecialSheathe
settles. A hold at source73 that prevents this event is deliberately reported.
This compares UE poses to imported source clips, not to a running original game.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
import traceback

try:
    import unreal
except ImportError:
    unreal = None

import pie_behavior_corrections as behavior

_ACTIVE = None


class NativeWeaponRunner(behavior.BehaviorRunner):
    def __init__(self, strict_source_hold, max_fps=None):
        super().__init__('ground')
        self.strict_hold = bool(strict_source_hold)
        self.max_fps = max_fps
        self.previous_max_fps = None
        self.requested = 'native_weapon'
        self.report_file = Path(unreal.Paths.project_saved_dir()) / 'MHWIImport/NativeFidelity-20261024/weapon-pie-verification.json'
        self.report.update(suite='native_weapon', suites_run=['native_weapon'],
                           strict_source_hold=self.strict_hold)
        if max_fps is not None:
            self.report_file = self.report_file.with_name('weapon-pie-%gfps.json' % max_fps)
            self.report['max_fps'] = max_fps
        self.report['notes'] = [
            'Actual formal DA, actual Enhanced Input; no costs/gauge/level fields overwritten.',
            'Pose comparison proves imported source-clip sampling; original-game execution is not compared.',
            'Interrupt/death tests wait beyond the old draw event and original montage tail.',
            'Whole-equipment attachment matrices remain prior project fitting. Internal hilt motion may change measured grip distances.']
        self.jobs = [('draw', 'toggle', 'Draw', 'idle'),
                     ('sheathe', 'toggle', 'Sheathe', 'idle'),
                     ('draw_again', 'toggle', 'Draw', 'idle'),
                     ('special_for_iai', 'special', 'SpecialSheathe', 'hold'),
                     ('iai_slash', 'light', 'IaiSlash', 'idle'),
                     ('special_for_spirit', 'special', 'SpecialSheathe', 'hold'),
                     ('iai_spirit_zero_level', 'spirit', 'IaiSpiritSlash', 'idle'),
                     ('sheathe_for_interrupt', 'toggle', 'Sheathe', 'idle'),
                     ('interrupted_draw', 'toggle', 'Draw', 'interrupt'),
                     ('sheathe_for_death', 'toggle', 'Sheathe', 'idle'),
                     ('death_during_draw', 'toggle', 'Draw', 'death')]
        self.job_index = 0

    def prepare_editor(self):
        super().prepare_editor()
        if self.max_fps is not None:
            self.previous_max_fps = unreal.SystemLibrary.get_console_variable_float_value('t.MaxFPS')
            unreal.SystemLibrary.execute_console_command(None, 't.MaxFPS %g' % self.max_fps)

    def _begin_suite(self, name):
        self.current_suite = 'native_weapon'
        self.suite_started = time.monotonic()
        self._suite_entry()
        self._reset_fixture(3000.)
        self.weapon = self.pawn.get_editor_property('weapon_mesh')
        self.weapon_motions = self.data.get_editor_property('weapon_motions')
        self._check(len(self.weapon_motions) == 6, 'formal DA contains all six source weapon entries')
        self._check(self.pawn.get_weapon_motion_no() == 0, 'fresh sheathed pawn uses source internal motion0')
        self._sample('initial')
        self.report['data']['weapon_motions'] = {str(key): seq.get_path_name() for key, seq in self.weapon_motions.items()}
        self._phase('weapon_next', 10.)

    def _sample(self, label):
        number = int(self.pawn.get_weapon_motion_no())
        position = float(self.pawn.get_weapon_motion_position())
        self._check(number in self.weapon_motions, label + ': weapon clip number is formal')
        sequence = self.weapon_motions[number]
        self._check(-.0001 <= position <= sequence.get_play_length() + .0001,
                    label + ': source weapon clock stays within clip bounds')
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(sequence, position,
            unreal.AnimPoseEvaluationOptions(extract_root_motion=False,
                incorporate_root_motion_into_pose=False))
        errors = {}
        for bone in ('bone_001', 'bone_002'):
            expected = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)
            actual = self.weapon.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)
            errors[bone] = float((actual.translation - expected.translation).length())
        self._check(max(errors.values()) < .05, label + ': evaluated weapon bones match formal source sequence within .05cm')
        self._record('weapon_frames', label=label, move=self._current(), montage_position=self._position(),
                     motion_no=number, position=position, errors_cm=errors)
        return number, position

    def _phase_weapon_next(self, elapsed):
        if self.job_index >= len(self.jobs):
            self._finish()
            return
        label, semantic, move, ending = self.jobs[self.job_index]
        if semantic != 'special' and not (self._idle() or self.pawn.is_special_sheath_holding()):
            return
        self.watch = {'label': label, 'move': move, 'ending': ending,
                      'initial_motion': int(self.pawn.get_weapon_motion_no()), 'seen': False,
                      'seen_motion_numbers': [], 'event_before': {}, 'event_after': {}}
        if semantic == 'special':
            self._press('light')
            self._phase('weapon_prepare_special', 12.)
        else:
            self._press(semantic)
            self._phase('weapon_observe', 12.)

    def _phase_weapon_prepare_special(self, elapsed):
        if self._idle():
            if elapsed > .8:
                raise behavior.BehaviorFailure('normal attack failed to start special-sheathe preparation')
            return
        if self._cancel_ready(self._def(self._current()), 'special'):
            self.watch['initial_motion'] = int(self.pawn.get_weapon_motion_no())
            self._press('special')
            self._phase('weapon_observe', 12.)

    def _phase_weapon_observe(self, elapsed):
        watch = self.watch
        current = self._current()
        if current != watch['move']:
            if not watch['seen']:
                if elapsed > 3.:
                    raise behavior.BehaviorFailure('input did not reach ' + watch['move'] + ', actual=' + current)
                return
            self._check(current == 'None', watch['label'] + ': no unrequested follow-up')
            self._default_pose(watch['label'] + ' finished')
            self.job_index += 1
            self._phase('weapon_next', 10.)
            return
        watch['seen'] = True
        position = self._position()
        # GetCurrentActiveMontage returns None during blend-out, while the action
        # still owns its ending delegate. Its helper then returns 0, not a rewind.
        if self.anim.get_current_active_montage() is None and position == 0:
            position = watch.get('last_source_position', 0.)
        watch['last_source_position'] = position
        number, _ = self._sample(watch['label'])
        if not watch['seen_motion_numbers'] or watch['seen_motion_numbers'][-1] != number:
            watch['seen_motion_numbers'].append(number)
        events = self._def(watch['move']).get_editor_property('weapon_motion_events')
        expected = watch['initial_motion']
        for event in events:
            at, motion = float(event.get_editor_property('time')), int(event.get_editor_property('motion_no'))
            if motion < 0:
                continue
            if at <= position + .0001:
                expected = motion
                watch['event_after'][str(at)] = True
            else:
                watch['event_before'][str(at)] = True
        # The hold settlement check below deliberately goes beyond the frozen
        # hunter montage position; it verifies that source event80 is resolved.
        if not self.pawn.is_special_sheath_holding():
            self._check(number == expected, watch['label'] + ': source event threshold selects the correct internal clip')
        if watch['ending'] in ('interrupt', 'death') and .04 < position < .25:
            if watch['ending'] == 'death':
                self.pawn.get_editor_property('attributes').apply_damage(1000., self.target)
                self._check(not self.pawn.get_editor_property('attributes').is_alive, 'lethal incoming damage applied')
                self._check(not self.pawn.request_input(unreal.MHWIInput.LIGHT), 'dead pawn rejects combat input')
            else:
                self.pawn.interrupt_move()
            self._check(self._idle(), watch['label'] + ': releases action immediately')
            self._default_pose(watch['label'] + ' immediate')
            watch['reset_motion'] = int(self.pawn.get_weapon_motion_no())
            self._phase('weapon_late_callback', 4.)
        elif watch['ending'] == 'hold' and self.pawn.is_special_sheath_holding():
            watch['hold_at'] = float(position)
            self._phase('weapon_hold_settle', 5.)

    def _phase_weapon_hold_settle(self, elapsed):
        number, _ = self._sample('special hold settling')
        self._check(self.pawn.is_special_sheath_holding(), 'source weapon update does not release SpecialSheathe hold')
        if elapsed < .35:
            return
        if self.strict_hold:
            self._check(number == 0, 'settled SpecialSheathe consumes source306 event80 -> internal static0')
        else:
            self._check(number == 3, 'project hold73 retains motion3; later hunter event80 is not consumed')
            self._note('Non-strict hold: actual motion%d, hunter froze at %.6fs; source event80 may remain unconsumed.'
                       % (number, self.watch['hold_at']))
        self._record('weapon_actions', **self.watch)
        self.job_index += 1
        self._phase('weapon_next', 10.)

    def _default_pose(self, label):
        number, _ = self._sample(label)
        expected = 0 if self.pawn.is_sheathed() else 1
        self._check(number == expected, label + ': restores stance default internal0/1')

    def _phase_weapon_late_callback(self, elapsed):
        number, _ = self._sample(self.watch['label'] + ' late guard')
        self._check(self._idle(), 'old draw montage never regains action ownership')
        self._check(number == self.watch['reset_motion'], 'old event/delegate never overwrites restored weapon motion')
        if elapsed < 1.6:
            return
        self._record('weapon_actions', **self.watch)
        self.job_index += 1
        self._phase('weapon_next', 10.)

    def _finish(self, error=None):
        global _ACTIVE
        if self.previous_max_fps is not None:
            unreal.SystemLibrary.execute_console_command(None, 't.MaxFPS %g' % self.previous_max_fps)
            self.report['max_fps_restored'] = self.previous_max_fps
            self.previous_max_fps = None
        super()._finish(error)
        _ACTIVE = None


def run(strict_source_hold=False, max_fps=None):
    """Run asynchronously; read weapon-pie-verification.json for actual results."""
    global _ACTIVE
    if unreal is None:
        raise RuntimeError('Run inside the Unreal editor Python environment')
    if _ACTIVE is not None and not _ACTIVE.done:
        raise RuntimeError('A native weapon test is already running')
    if behavior._ACTIVE is not None and not behavior._ACTIVE.done:
        raise RuntimeError('Wait for the active behavior suite before this test')
    if max_fps is not None and not (0 < float(max_fps) <= 240):
        raise ValueError('max_fps must be greater than 0 and at most 240')
    runner = NativeWeaponRunner(strict_source_hold, max_fps)
    _ACTIVE = runner
    behavior._ACTIVE = runner
    try:
        runner.prepare_editor()
        runner.handle = unreal.register_slate_post_tick_callback(runner.tick)
    except Exception:
        runner._finish(traceback.format_exc())
        raise
    return {'started': True, 'report': str(runner.report_file), 'strict_source_hold': bool(strict_source_hold)}
