"""Real PIE verification for the MHWI long-sword behavior corrections.

Import is inert. Call ``run('ground'|'direction'|'air'|'lifecycle'|'all')`` from
the editor Python environment to install a single Slate post-tick state machine.
No gameplay asset is saved or edited, no cost is zeroed, and no preview copy of
the DataAsset is used. The report is written to
``Saved/MHWIImport/PIE-behavior-<suite>.json`` even when a phase fails.

The script only relies on the shared contract: existing getters
(GetCurrentMove / spirit gauge / level / sheathed), actor location, velocity,
movement mode, montage position, and the formal DA fields. It does not expect a
public helm-phase getter; phases are inferred from CurrentMove plus physics.
"""
from pathlib import Path
import json
import math
import time
import traceback

try:
    import unreal
except Exception:  # Allows a plain import/syntax check outside the editor.
    unreal = None

MAP_PATH = '/Game/MHWI/Maps/L_MHWI_Training'
FORMAL_DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'
SUITES = ('ground', 'direction', 'air', 'lifecycle')
SUITE_TIMEOUT = {'ground': 240.0, 'direction': 150.0, 'air': 240.0, 'lifecycle': 150.0}
COMMAND = {'light': 0, 'thrust': 1, 'spirit': 2, 'foresight': 3, 'helm': 4,
           'special': 5, 'evade': 6, 'toggle': 7, 'fade': 8}
INPUT_ENUM = {'light': 'LIGHT', 'thrust': 'THRUST', 'spirit': 'SPIRIT',
              'foresight': 'FORESIGHT', 'helm': 'HELM_BREAKER',
              'special': 'SPECIAL_SHEATHE', 'evade': 'EVADE',
              'toggle': 'TOGGLE_SHEATHE', 'fade': 'FADE_SLASH'}
SOURCE_CLIP = {'ForesightSlash': 'A_w03_00_140', 'SpiritThrust': 'A_w03_00_170'}
POSE_BONES = ('bone_003', 'bone_008', 'bone_012')
HELM_MOVES = ('SpiritThrust', 'HelmRise', 'HelmAir', 'SpiritHelmBreaker', 'HelmLand')
_ACTIVE = None


class BehaviorFailure(RuntimeError):
    """A check failed; the runner records it and cleans up instead of crashing."""


def _yaw_of(forward):
    return math.degrees(math.atan2(float(forward.y), float(forward.x)))


def _yaw_delta(before, after):
    return (float(after) - float(before) + 180.0) % 360.0 - 180.0


def _dot_xy(a, b):
    return float(a.x) * float(b.x) + float(a.y) * float(b.y)


def _len_xy(v):
    return math.hypot(float(v.x), float(v.y))


class BehaviorRunner:
    def __init__(self, suite):
        self.requested = suite
        self.suites = list(SUITES) if suite == 'all' else [suite]
        self.suite_index = 0
        self.current_suite = 'boot'
        self.suite_started = time.monotonic()
        self.started = time.monotonic()
        self.phase = 'idle'
        self.phase_started = time.monotonic()
        self.phase_budget = 30.0
        self.done = False
        self.handle = None
        self.settings = None
        self.throttle = True
        self.level = None
        self.editor = None
        self.world = None
        self.pawn = None
        self.pc = None
        self.anim = None
        self.sub = None
        self.actions = {}
        self.data = None
        self.moves = None
        self.montage_segment_errors = []
        self.target = None
        self.target_attrs = None
        self.after_stance = None
        self.level_then = None
        self.held_move = (0.0, 0.0)
        self.move_release_pending = False
        self.held_sprint = (0.0, 0.0, 0.0)
        self.sprint_release_pending = False
        self.report_file = Path(unreal.Paths.project_saved_dir()) / 'MHWIImport' / (
            'PIE-behavior-' + suite + '.json')
        self.report = {
            'suite': suite,
            'passed': False,
            'started_wall': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'checks': [],
            'phases': [],
            'suites': {},
            'samples': {},
            'notes': [
                'Uses the formal DA and real Enhanced Input injection; no cost, '
                'damage window, montage or asset is modified by this script.',
                'Input-route windows are current project authoring; defence and '
                'resource values use the public-table adapter. Neither is a '
                'running-original-game fidelity comparison.',
                'Helm phase names are inferred from GetCurrentMove plus velocity, '
                'Z, MovementMode and montage position; no private phase getter is used.',
                'Pose checks reuse the existing component-vs-source-pose convention '
                'from pie_animation_corrections.py; they prove asset identity, not '
                'original-game animation fidelity.',
            ],
            'segment_read_errors': self.montage_segment_errors,
        }
        self.report['suites_run'] = list(self.suites)

    # ------------------------------------------------------------------ logging

    def _suite_entry(self, name=None):
        """Single contract for every suite record, including boot and failures."""
        target = self.current_suite if name is None else name
        suites = self.report.setdefault('suites', {})
        entry = suites.setdefault(target, {})
        entry.setdefault('checks', [])
        if 'started' not in entry:
            entry['started'] = round(time.monotonic() - self.started, 3)
        return entry

    def _check(self, ok, label):
        entry = {'suite': self.current_suite, 'phase': self.phase,
                 'check': label, 'passed': bool(ok)}
        self.report.setdefault('checks', []).append(entry)
        suite = self._suite_entry()
        suite['checks'].append({'check': label, 'passed': bool(ok), 'phase': self.phase})
        if not ok:
            # The tick handler catches BehaviorFailure and calls _finish(), which
            # writes the partial report before the callback is unregistered.
            raise BehaviorFailure('%s/%s: %s' % (self.current_suite, self.phase, label))

    def _note(self, text):
        self.report['notes'].append(str(text))
        unreal.log('MHWI_BEHAVIOR_NOTE ' + str(text))

    def _phase(self, name, budget=30.0):
        self.phase = name
        self.phase_started = time.monotonic()
        self.phase_budget = float(budget)
        event = {'suite': self.current_suite, 'phase': name,
                 'wall': round(self.phase_started - self.started, 3)}
        self.report['phases'].append(event)
        unreal.log('MHWI_BEHAVIOR_PHASE %s %s' % (self.current_suite, name))

    # ------------------------------------------------------------ data helpers

    def _prop(self, obj, name, where):
        try:
            return obj.get_editor_property(name)
        except Exception as exc:
            raise BehaviorFailure(
                '%s: missing editor property %r (A/B shared contract not present); %s'
                % (where, name, exc))

    def _optional_prop(self, obj, name):
        try:
            return obj.get_editor_property(name)
        except Exception:
            return None

    def _num(self, obj, name, where):
        value = self._prop(obj, name, where)
        try:
            return float(value)
        except Exception as exc:
            raise BehaviorFailure('%s.%s is not numeric: %r (%s)' % (where, name, value, exc))

    def _move_names(self):
        try:
            return [str(key) for key in self.moves.keys()]
        except Exception:
            pass
        try:
            return [str(key) for key in self.moves]
        except Exception:
            return None

    def _def(self, name):
        present = None
        membership_checked = False
        for key in (name, unreal.Name(name)):
            try:
                membership_checked = True
                if key in self.moves:
                    present = True
                    break
            except Exception:
                pass
        if present is None:
            names = self._move_names()
            if names is not None:
                if name in names:
                    present = True
            elif membership_checked:
                present = False
        if present is False:
            raise BehaviorFailure(
                'formal DA %s lacks move %r; B routing/data contract is not applied'
                % (FORMAL_DATA, name))
        try:
            definition = self.moves[unreal.Name(name)]
        except Exception as exc:
            raise BehaviorFailure('formal DA cannot read move %r: %s' % (name, exc))
        montage = self._optional_prop(definition, 'montage')
        if montage is None:
            raise BehaviorFailure(
                'formal DA move %r has no montage; B data/routing contract is not applied'
                % (name,))
        return definition

    def _mount(self, name):
        return self._prop(self._def(name), 'montage', 'move ' + name)

    def _cost(self, name):
        return self._num(self._def(name), 'spirit_cost', 'move ' + name)

    def _cancel_window(self, definition, input_key, next_move=None):
        """Read the actual requested input's route, with the native fallback.

        Never take a minimum across unrelated inputs: a SpecialSheathe opening
        cannot authorize the fixture's later Spirit or Light press.
        """
        if input_key not in INPUT_ENUM:
            raise BehaviorFailure('cancel fixture needs a semantic input: %r' % input_key)
        start = self._num(definition, 'cancel_start', 'move definition')
        end = self._num(definition, 'cancel_end', 'move definition')
        wanted = getattr(unreal.MHWIInput, INPUT_ENUM[input_key])
        for route in self._routes(definition):
            if route.get_editor_property('input') != wanted:
                continue
            if next_move is not None and str(route.get_editor_property('next_move')) != next_move:
                continue
            if bool(route.get_editor_property('require_drawn')) and self.pawn.is_sheathed():
                continue
            for key, current in (('cancel_start', start), ('cancel_end', end)):
                value = self._optional_prop(route, key)
                value = current if value is None or float(value) < 0.0 else float(value)
                if key == 'cancel_start':
                    start = value
                else:
                    end = value
            return start, end
        return start, end

    def _cancel_start(self, definition, input_key, next_move=None):
        return self._cancel_window(definition, input_key, next_move)[0]

    def _cancel_ready(self, definition, input_key, lead=0.0, next_move=None):
        start, end = self._cancel_window(definition, input_key, next_move)
        return start - float(lead) <= self._position() <= end

    def _near_cancel(self, definition, input_key, lead=0.05, next_move=None):
        return self._cancel_ready(definition, input_key, lead, next_move)

    def _spirit_chain_stock(self):
        # Conservative reserve: normal hit income is verified separately and
        # must not be needed to conceal a missing/duplicated spend in a fixture.
        return sum(self._cost(name) for name in
                   ('SpiritI', 'SpiritII', 'SpiritIII', 'SpiritRoundslash'))

    def _routes(self, definition):
        try:
            return list(definition.get_editor_property('routes'))
        except Exception as exc:
            raise BehaviorFailure('move routes are unreadable: %s' % (exc))

    def _find_route(self, definition, input_key, next_move=None):
        wanted = getattr(unreal.MHWIInput, INPUT_ENUM[input_key])
        for route in self._routes(definition):
            if route.get_editor_property('input') != wanted:
                continue
            if next_move is not None and str(route.get_editor_property('next_move')) != next_move:
                continue
            return route
        return None

    def _montage_sequence_names(self, montage):
        """Read the montage's actual segments; return (names, error)."""
        if montage is None:
            return None, 'no montage'
        try:
            tracks = montage.get_editor_property('slot_anim_tracks')
        except Exception as exc:
            return None, 'slot_anim_tracks unavailable: %s' % (exc)
        names = []
        try:
            for track in tracks:
                try:
                    segments = track.get_editor_property('anim_track').get_editor_property(
                        'anim_segments')
                except Exception as exc:
                    return None, 'anim_segments unavailable: %s' % (exc)
                for segment in segments:
                    try:
                        reference = segment.get_editor_property('anim_reference')
                    except Exception as exc:
                        return None, 'anim_reference unavailable: %s' % (exc)
                    if reference is None:
                        continue
                    if hasattr(reference, 'get') and not hasattr(reference, 'get_name'):
                        reference = reference.get()
                    if reference is None:
                        continue
                    names.append(str(reference.get_name()))
        except Exception as exc:
            return None, 'montage segment walk failed: %s' % (exc)
        return names, None

    def _clip_path(self, clip_name):
        return '/Game/MHWI/Animations/LongSword/' + clip_name

    def _pose_errors(self, clip_name, seconds):
        sequence = unreal.load_asset(self._clip_path(clip_name))
        if sequence is None:
            raise BehaviorFailure('source sequence missing: %s' % (self._clip_path(clip_name),))
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(
            sequence, float(seconds),
            unreal.AnimPoseEvaluationOptions(extract_root_motion=True,
                                             incorporate_root_motion_into_pose=False))
        errors = {}
        for bone in POSE_BONES:
            expected = unreal.AnimPoseExtensions.get_bone_pose(
                pose, bone, unreal.AnimPoseSpaces.WORLD)
            actual = self.pawn.mesh.get_socket_transform(
                bone, unreal.RelativeTransformSpace.RTS_COMPONENT)
            errors[bone] = (actual.translation - expected.translation).length()
        return errors

    def _check_pose(self, move, clip_name, seconds, tolerance=2.0):
        errors = self._pose_errors(clip_name, seconds)
        self.report.setdefault('samples', {}).setdefault('poses', []).append({
            'move': move, 'clip': clip_name, 'seconds': round(float(seconds), 3),
            'error_cm': {bone: round(float(value), 4) for bone, value in errors.items()},
        })
        worst = max(errors.values()) if errors else 999.0
        self._check(worst < float(tolerance),
                    '%s playing pose matches source %s within %.1f cm' %
                    (move, clip_name, tolerance))

    # ---------------------------------------------------------- input / state

    def _inject(self, action_name, xyz=(1.0, 0.0, 0.0)):
        action = self.actions.get(action_name)
        if action is None:
            raise BehaviorFailure('runtime input action missing: %s' % (action_name,))
        self.sub.inject_input_vector_for_action(
            action, unreal.Vector(float(xyz[0]), float(xyz[1]), float(xyz[2])), [], [])

    def _press(self, semantic):
        self._inject('MHWI_Command_' + str(COMMAND[semantic]))

    def _move(self, x=0.0, y=0.0):
        # Held intent only; the Slate tick pump injects at most once per frame
        # so a phase that waits 0.05s keeps the real Move input alive.
        self.held_move = (float(x), float(y))
        self.move_release_pending = (self.held_move == (0.0, 0.0))

    def _stop_inputs(self):
        self.held_move = (0.0, 0.0)
        self.move_release_pending = True
        self.held_sprint = (0.0, 0.0, 0.0)
        self.sprint_release_pending = True

    def _pump_held_inputs(self):
        if self.sub is None or not self.actions:
            return
        x, y = self.held_move
        if x != 0.0 or y != 0.0:
            self._inject('MHWI_Move', (x, y, 0.0))
            self.move_release_pending = False
        elif self.move_release_pending:
            self._inject('MHWI_Move', (0.0, 0.0, 0.0))
            self.move_release_pending = False
        sx, sy, sz = self.held_sprint
        if sx != 0.0 or sy != 0.0 or sz != 0.0:
            self._inject('MHWI_Sprint', (sx, sy, sz))
            self.sprint_release_pending = False
        elif self.sprint_release_pending:
            self._inject('MHWI_Sprint', (0.0, 0.0, 0.0))
            self.sprint_release_pending = False

    def _flush_zero_inputs(self, cleanup=None):
        self.held_move = (0.0, 0.0)
        self.held_sprint = (0.0, 0.0, 0.0)
        self.move_release_pending = False
        self.sprint_release_pending = False
        if self.sub is None or not self.actions:
            return
        try:
            if 'MHWI_Move' in self.actions:
                self._inject('MHWI_Move', (0.0, 0.0, 0.0))
            if 'MHWI_Sprint' in self.actions:
                self._inject('MHWI_Sprint', (0.0, 0.0, 0.0))
            if cleanup is not None:
                cleanup.append('zero Move/Sprint flushed')
        except Exception as exc:
            if cleanup is not None:
                cleanup.append('zero Move/Sprint flush failed: %s' % (exc))

    def _current(self):
        return str(self.pawn.get_current_move())

    def _idle(self):
        return self.pawn.get_current_move().is_none()

    def _position(self):
        montage = self.anim.get_current_active_montage()
        return float(self.anim.montage_get_position(montage)) if montage else 0.0

    def _montage_name(self):
        montage = self.anim.get_current_active_montage()
        return str(montage.get_name()) if montage else ''

    def _length(self):
        montage = self.anim.get_current_active_montage()
        return float(montage.get_play_length()) if montage else 0.0

    def _level(self):
        return int(self.pawn.get_spirit_level())

    def _gauge(self):
        return float(self.pawn.get_spirit_gauge())

    def _hp(self):
        return float(self.target_attrs.get_current_health())

    def _actor_yaw(self):
        return _yaw_of(self.pawn.get_actor_forward_vector())

    def _control_yaw(self):
        return float(self.pc.get_control_rotation().yaw)

    def _set_control_yaw(self, value):
        self.pc.set_control_rotation(unreal.Rotator(pitch=0.0, yaw=float(value), roll=0.0))

    def _world_intent(self, x, y):
        """Camera-yaw projection matching the character: (Y forward, X right)."""
        radians = math.radians(self._control_yaw())
        forward = (math.cos(radians), math.sin(radians))
        right = (-math.sin(radians), math.cos(radians))
        return (forward[0] * float(y) + right[0] * float(x),
                forward[1] * float(y) + right[1] * float(x))

    def _movement_mode(self):
        try:
            return self.pawn.character_movement.movement_mode
        except Exception as exc:
            raise BehaviorFailure('character movement mode is unreadable: %s' % (exc))

    def _mode_name(self):
        try:
            return str(self._movement_mode())
        except Exception:
            return 'unknown'

    def _velocity(self):
        try:
            return self.pawn.get_velocity()
        except Exception:
            try:
                return self.pawn.character_movement.velocity
            except Exception:
                return unreal.Vector(0.0, 0.0, 0.0)

    def _is_flying(self):
        try:
            return self._movement_mode() == unreal.MovementMode.MOVE_FLYING
        except Exception:
            return False

    def _place_target(self, distance=150.0, side=0.0):
        if self.target is None or self.pawn is None:
            return
        location = self.pawn.get_actor_location()
        forward = self.pawn.get_actor_forward_vector()
        right = self.pawn.get_actor_right_vector()
        position = (location + forward * float(distance) + right * float(side)
                    + unreal.Vector(0.0, 0.0, -4.0))
        self.target.set_actor_location(position, False, False)

    def _reset_fixture(self, target_distance=150.0):
        if self.pawn is None:
            return
        try:
            if not self._idle():
                self.pawn.interrupt_move()
        except Exception:
            pass
        try:
            self.pawn.character_movement.stop_movement_immediately()
        except Exception:
            pass
        self._stop_inputs()
        try:
            self.pawn.set_actor_location(unreal.Vector(0.0, 0.0, 94.15), False, True)
            self.pawn.set_actor_rotation(
                unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0), False)
            self.pc.set_control_rotation(
                unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        except Exception:
            pass
        self._place_target(target_distance)

    def _record(self, bucket, **values):
        rows = self.report.setdefault('samples', {}).setdefault(bucket, [])
        if len(rows) < 600:
            values['wall'] = round(time.monotonic() - self.started, 3)
            rows.append(values)

    # ------------------------------------------------------- stance / helpers

    def _require_drawn(self, next_phase, budget=30.0):
        self.after_stance = (next_phase, budget)
        self._phase('ensure_drawn', 10.0)

    def _require_sheathed(self, next_phase, budget=30.0):
        self.after_stance = (next_phase, budget)
        self._phase('ensure_sheathed', 10.0)

    def _advance_after_stance(self):
        if not self.after_stance:
            raise BehaviorFailure('stance helper reached without a next phase')
        next_phase, budget = self.after_stance
        self._phase(next_phase, budget)

    def _begin_stance_watch(self, expected_drawn, next_phase, label):
        self.stance_watch = {
            'expected_drawn': bool(expected_drawn), 'next': next_phase,
            'label': str(label), 'started_at': time.monotonic(), 'elapsed': 0.0,
            'observed_moves': [], 'last_stance': bool(self.pawn.is_sheathed()),
            'last_move': 'None',
        }

    def _stance_watch_tick(self):
        state = self.stance_watch
        name = self._current()
        sheathed = bool(self.pawn.is_sheathed())
        if name != 'None' and (not state['observed_moves']
                               or state['observed_moves'][-1] != name):
            state['observed_moves'].append(name)
        state['last_move'] = name
        state['last_stance'] = sheathed
        state['elapsed'] = round(time.monotonic() - state['started_at'], 3)
        observed = ('label=%s elapsed=%.3f moves=%s last_stance=%s'
                    % (state['label'], state['elapsed'],
                       state['observed_moves'], sheathed))
        target_sheathed = not state['expected_drawn']
        if name == 'None' and sheathed == target_sheathed:
            self._record('stance_observations', label=state['label'],
                         moves=list(state['observed_moves']),
                         last_stance=sheathed, elapsed=state['elapsed'])
            next_phase = state.get('next')
            if next_phase:
                self._phase(next_phase, 20.0)
            else:
                self._advance_after_stance()
            return
        if name == 'None' and state['observed_moves']:
            self._record('stance_observations', label=state['label'],
                         moves=list(state['observed_moves']),
                         last_stance=sheathed, elapsed=state['elapsed'])
            raise BehaviorFailure(
                '%s observed but ended in the wrong stance; %s'
                % (state['label'], observed))
        if name == 'None' and state['elapsed'] >= 0.5:
            self._record('stance_observations', label=state['label'],
                         moves=list(state['observed_moves']),
                         last_stance=sheathed, elapsed=state['elapsed'])
            raise BehaviorFailure(
                '%s did not start within 0.5s (input still queued?); %s'
                % (state['label'], observed))
        if state['elapsed'] > 8.0:
            self._record('stance_observations', label=state['label'],
                         moves=list(state['observed_moves']),
                         last_stance=sheathed, elapsed=state['elapsed'])
            raise BehaviorFailure(
                '%s did not reach the expected stance within 8s; %s'
                % (state['label'], observed))

    def _phase_ensure_drawn(self, elapsed):
        if not self._idle():
            return
        if not self.pawn.is_sheathed():
            self._advance_after_stance()
            return
        self._begin_stance_watch(True, None, 'E toggle -> drawn')
        self._press('toggle')
        self._phase('ensure_drawn_wait', 10.0)

    def _phase_ensure_drawn_wait(self, elapsed):
        self._stance_watch_tick()

    def _phase_ensure_sheathed(self, elapsed):
        if not self._idle():
            return
        if self.pawn.is_sheathed():
            self._advance_after_stance()
            return
        self._begin_stance_watch(False, None, 'E toggle -> sheathed')
        self._press('toggle')
        self._phase('ensure_sheathed_wait', 10.0)

    def _phase_ensure_sheathed_wait(self, elapsed):
        self._stance_watch_tick()

    # ----------------------------------------------------- gauge / spirit plan

    def _start_gauge(self, goal, then_phase, budget=90.0):
        self.gauge_task = {'goal': float(goal), 'then': then_phase, 'attempts': 0,
                           'hits': 0, 'hp': self._hp(), 'last_move': None,
                           'queued': False, 'seen_move': False}
        self._phase('gauge_idle', budget)

    def _phase_gauge_idle(self, elapsed):
        if not self._idle():
            return
        if self._gauge() + 0.5 >= self.gauge_task['goal']:
            self._phase(self.gauge_task['then'], 60.0)
            return
        if self.gauge_task['attempts'] >= 24:
            raise BehaviorFailure(
                'gauge build did not reach %.0f after %d attacks (gauge=%.1f)'
                % (self.gauge_task['goal'], self.gauge_task['attempts'], self._gauge()))
        self.gauge_task['attempts'] += 1
        self.gauge_task['hp'] = self._hp()
        self.gauge_task['last_move'] = None
        self.gauge_task['queued'] = False
        # The previous attempt's observation must not leak into this new input.
        self.gauge_task['seen_move'] = False
        self._place_target(150.0)
        self._press('light')
        # A full 100-gauge preparation can contain >8 seconds of real actions.
        # Bound the whole chain separately from the per-move progress watchdog.
        self.gauge_task['progress_at'] = time.monotonic()
        self._phase('gauge_attack', 30.0)

    def _phase_gauge_attack(self, elapsed):
        self._place_target(150.0)
        name = self._current()
        task = self.gauge_task
        evidence = ('attempt=%d seen_move=%s name=%s hp=%.2f gauge=%.2f'
                    % (task['attempts'], task.get('seen_move'), name,
                       self._hp(), self._gauge()))
        if self._idle():
            if not task.get('seen_move'):
                if elapsed < 1.0:
                    return
                raise BehaviorFailure(
                    'light input did not start a normal attack; ' + evidence)
            self._check(self._hp() < task['hp'] - 0.01,
                        'normal light attack really damages the target while '
                        'building gauge; ' + evidence)
            task['hits'] += 1
            self._phase('gauge_idle', 90.0)
            return
        if name != task['last_move']:
            task['last_move'] = name
            task['queued'] = False
            task['seen_move'] = True
            task['progress_at'] = time.monotonic()
            self._record('gauge_progress', move=name, gauge=round(self._gauge(), 2),
                         goal=task['goal'], attempt=task['attempts'])
        if time.monotonic() - task['progress_at'] > 8.0:
            raise BehaviorFailure('gauge preparation stopped advancing; ' + evidence)
        goal_reached = self._gauge() + 0.5 >= task['goal']
        if not goal_reached and not task['queued'] and self._cancel_ready(self._def(name), 'light'):
            self._press('light')
            task['queued'] = True

    def _start_spirit_plan(self, then_phase, budget=90.0):
        self.plan = {'steps': [('SpiritI', 'spirit'), ('SpiritII', 'spirit'),
                               ('SpiritIII', 'spirit')],
                     'i': 0, 'queued': False, 'last': None, 'then': then_phase,
                     'level_before': self._level(), 'gauge_before': self._gauge(),
                     'seen': False, 'round_seen': False}
        self._phase('plan_start', 20.0)

    def _phase_plan_start(self, elapsed):
        if not self._idle():
            return
        self._check(self._gauge() + 0.01 >= self._cost('SpiritI'),
                    'formal gauge covers the SpiritI cost before the level plan')
        self.plan['gauge_before'] = self._gauge()
        self.plan['level_before'] = self._level()
        self.plan['time_before'] = float(self.pawn.get_spirit_time_remaining())
        self._place_target(150.0)
        self._press('spirit')
        self._phase('plan_wait', 90.0)

    def _phase_plan_wait(self, elapsed):
        self._place_target(150.0)
        name = self._current()
        steps = self.plan['steps']
        if name == 'None':
            if not self.plan['seen']:
                return
            self._check(self.plan['round_seen'],
                        'real spirit level plan reaches SpiritRoundslash')
            expected_level = min(3, self.plan['level_before'] + 1)
            self._check(self._level() == expected_level,
                        'real roundslash raises the spirit color or refreshes the red cap')
            if self.plan['level_before'] == 3:
                self._check(self.pawn.get_spirit_time_remaining() > self.plan['time_before'],
                            'a real red roundslash refreshes its nearly expired timer')
            self._check(self._gauge() < self.plan['gauge_before'] + 0.01,
                        'real spirit level plan spent its formal gauge once per stage')
            self._phase(self.plan['then'], 60.0)
            return
        if name != self.plan['last']:
            self.plan['last'] = name
            self.plan['queued'] = False
            self.plan['seen'] = True
            if name == 'SpiritRoundslash':
                self.plan['round_seen'] = True
        valid = [step[0] for step in steps] + ['SpiritRoundslash']
        if name not in valid:
            raise BehaviorFailure(
                'spirit level plan reached unexpected move %r (expected %s)'
                % (name, valid))
        if self.plan['i'] < len(steps) and name == steps[self.plan['i']][0]:
            if not self.plan['queued'] and self._cancel_ready(
                    self._def(name), steps[self.plan['i']][1]):
                self._press(steps[self.plan['i']][1])
                self.plan['queued'] = True
                self.plan['i'] += 1

    def _start_level_prep(self, then_phase):
        self.level_then = then_phase
        self._phase('level_prep', 150.0)

    def _phase_level_prep(self, elapsed):
        # Combined suites inherit the red color earned by the ground tests.
        # Refresh it by a real chain when nearly expired; natural expiry must
        # not be mistaken for a second Helm color spend later in the suite.
        remaining = float(self.pawn.get_spirit_time_remaining())
        if self._level() >= 1 and remaining >= 45.0:
            self._require_drawn(self.level_then, 60.0)
            return
        required = self._spirit_chain_stock()
        if self._gauge() < required:
            self._start_gauge(required, 'level_prep', 120.0)
            return
        self._start_spirit_plan('level_ready', 90.0)

    def _phase_level_ready(self, elapsed):
        # Roundslash really sheathes the weapon; G is only valid while drawn.
        self._require_drawn(self.level_then, 60.0)

    # ------------------------------------------------------------- boot / runs

    def prepare_editor(self):
        self.settings = unreal.get_default_object(
            unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
        self.throttle = bool(self.settings.get_editor_property(
            'bThrottleCPUWhenNotForeground'))
        self.settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
        self.editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        self.level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        unreal.EditorPythonScripting.set_keep_python_script_alive(True)
        self._phase('boot_prepare', 30.0)

    def tick(self, delta):
        # Editor map loading/PIE startup may pump Slate recursively. Do not
        # submit another play/load request while the first callback is active.
        if self.done or getattr(self, '_inside_tick', False):
            return
        self._inside_tick = True
        try:
            self._tick_impl(delta)
        finally:
            self._inside_tick = False

    def _tick_impl(self, delta):
        if self.done:
            return
        now = time.monotonic()
        try:
            limit = SUITE_TIMEOUT.get(self.current_suite)
            if limit is not None and now - self.suite_started > limit:
                raise BehaviorFailure(
                    'wall-clock timeout in suite %s at phase %s after %.0f s'
                    % (self.current_suite, self.phase, limit))
            if now - self.started > sum(SUITE_TIMEOUT.values()) + 90.0:
                raise BehaviorFailure(
                    'overall wall-clock timeout at %s/%s' % (self.current_suite, self.phase))
            if now - self.phase_started > self.phase_budget:
                raise BehaviorFailure(
                    'phase timeout %s/%s after %.0f s'
                    % (self.current_suite, self.phase, self.phase_budget))
            handler = getattr(self, '_phase_' + self.phase, None)
            if handler is None:
                raise BehaviorFailure('no tick handler for phase %r' % (self.phase,))
            handler(now - self.phase_started)
            # Apply the phase's final held state exactly once. Injecting before
            # the handler would enqueue old-left + release-zero in one frame;
            # Enhanced Input accumulates injections rather than replacing them.
            if not self.done:
                self._pump_held_inputs()
        except BehaviorFailure as exc:
            self._finish(str(exc))
        except Exception:
            self._finish(traceback.format_exc())

    def _setup_world(self):
        self.world = self.editor.get_game_world()
        if not self.world:
            return False
        pawn = unreal.GameplayStatics.get_player_character(self.world, 0)
        if not pawn:
            return False
        character_class = getattr(unreal, 'MHWICharacter', None)
        self._check(character_class is not None and isinstance(pawn, character_class),
                    'training GameMode spawns AMHWICharacter')
        self.pawn = pawn
        self.anim = pawn.mesh.get_anim_instance()
        anim_class = getattr(unreal, 'MHWIAnimInstance', None)
        self._check(anim_class is not None and isinstance(self.anim, anim_class),
                    'native MHWI animation instance is active')
        self._check(pawn.is_sheathed(), 'fresh PIE pawn starts sheathed')
        self.pc = unreal.GameplayStatics.get_player_controller(self.world, 0)
        self._check(self.pc is not None, 'local player controller is present')
        targets = list(unreal.GameplayStatics.get_all_actors_of_class(
            self.world, unreal.MHWITrainingTarget))
        self._check(len(targets) >= 1, 'training map contains MHWI training targets')
        self.target = targets[0]
        self.target_attrs = self.target.get_editor_property('attributes')
        self._check(self.target_attrs is not None, 'training target has attribute component')
        default_attacks = [bool(t.get_editor_property('enable_attacks')) for t in targets]
        self.report['target_default_attacks'] = default_attacks
        self._check(not any(default_attacks),
                    'default training targets are passive before any fixture is applied')
        contexts = [obj for obj in unreal.ObjectIterator(unreal.InputMappingContext)
                    if obj.get_outer() == pawn]
        self._check(len(contexts) == 1,
                    'pawn owns exactly one runtime input mapping context')
        installed = []
        for subsystem in unreal.ObjectIterator(
                unreal.EnhancedInputLocalPlayerSubsystem):
            present = subsystem.has_mapping_context(contexts[0])
            if present[0] if isinstance(present, tuple) else present:
                installed.append(subsystem)
        self._check(len(installed) == 1,
                    'runtime input context is installed on exactly one local subsystem')
        self.sub = installed[0]
        self.actions = {obj.get_name(): obj for obj in unreal.ObjectIterator(
            unreal.InputAction) if obj.get_outer() == pawn}
        for semantic, index in COMMAND.items():
            key = 'MHWI_Command_' + str(index)
            self._check(key in self.actions,
                        'runtime input action %s is present (%s)' % (key, semantic))
        data = pawn.get_editor_property('moveset')
        self._check(data is not None, 'pawn references a moveset DataAsset')
        self._check(data.get_name() == 'DA_MHWI_LongSword',
                    'runtime moveset is the formal DA_MHWI_LongSword')
        self.data = data
        self.moves = data.get_editor_property('moves')
        self._check(self.moves is not None, 'formal DA exposes move definitions')
        self._capture_data_readback()
        return True

    def _capture_data_readback(self):
        snapshot = {'asset': self.data.get_path_name(), 'moves': {}}
        names = self._move_names() or []
        for name in sorted(set(names) | set(HELM_MOVES) | set(SOURCE_CLIP)):
            if names and name not in names:
                continue
            entry = {}
            try:
                definition = self._def(name)
            except Exception as exc:
                entry['missing'] = str(exc)
                snapshot['moves'][name] = entry
                continue
            for key in ('spirit_cost', 'spirit_gain_on_start', 'cancel_start',
                        'cancel_end', 'require_spirit_level', 'require_nonzero_gauge',
                        'consume_all_gauge', 'raise_spirit_on_hit',
                        'spend_spirit_level', 'use_full_root_motion',
                        'auto_follow_up', 'auto_follow_up_on_hit'):
                value = self._optional_prop(definition, key)
                if value is not None:
                    entry[key] = str(value)
            for key in ('turn_start_time', 'turn_end_time', 'turn_max_angle',
                        'turn_speed', 'return_turn_start_time', 'return_turn_end_time',
                        'return_turn_max_angle'):
                value = self._optional_prop(definition, key)
                entry[key] = 'missing' if value is None else str(value)
            entry['routes'] = [{
                'input': str(route.get_editor_property('input')),
                'next_move': str(route.get_editor_property('next_move')),
                'cancel_start': str(self._optional_prop(route, 'cancel_start')),
                'cancel_end': str(self._optional_prop(route, 'cancel_end')),
            } for route in self._routes(definition)]
            montage = self._optional_prop(definition, 'montage')
            entry['montage'] = montage.get_name() if montage else None
            if montage is not None:
                sequences, error = self._montage_sequence_names(montage)
                entry['segments'] = sequences
                if error:
                    self.montage_segment_errors.append(name + ': ' + error)
            snapshot['moves'][name] = entry
        for key in ('helm_air_vertical_speed', 'helm_air_forward_speed',
                    'helm_air_gravity', 'helm_strike_speed', 'helm_strike_start_time'):
            value = self._optional_prop(self.data, key)
            snapshot[key] = 'missing' if value is None else str(value)
        self.report['data'] = snapshot

    def _begin_suite(self, name):
        self.current_suite = name
        self.suite_started = time.monotonic()
        entry = self._suite_entry(name)
        entry['started'] = round(self.suite_started - self.started, 3)
        self._reset_fixture(150.0 if name in ('ground', 'air', 'lifecycle') else 3000.0)
        first = {
            'ground': 'ground_assets',
            'direction': 'dir_prepare',
            'air': 'air_read',
            'lifecycle': 'life_prepare',
        }[name]
        self._phase(first, 40.0)

    def _suite_done(self):
        entry = self._suite_entry()
        entry['finished'] = round(time.monotonic() - self.suite_started, 3)
        entry['passed'] = True
        self.suite_index += 1
        if self.suite_index >= len(self.suites):
            self._finish(None)
            return
        self._begin_suite(self.suites[self.suite_index])

    # --------------------------------------------------------------- cleanup

    def _finish(self, error=None):
        global _ACTIVE
        if self.done:
            return
        self.done = True
        self.report['passed'] = error is None
        self.report['finished_wall'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        self.report['elapsed_seconds'] = round(time.monotonic() - self.started, 3)
        if error:
            self.report['error'] = str(error)
            self.report['failed_suite'] = self.current_suite
            self.report['failed_phase'] = self.phase
            suite = self._suite_entry()
            suite['passed'] = False
            suite['error'] = str(error)
            unreal.log_error('MHWI_BEHAVIOR_FAILED %s/%s %s'
                             % (self.current_suite, self.phase, error))
        cleanup = []
        # Explicit release even on error, before the callback/world is torn down.
        self._flush_zero_inputs(cleanup)
        try:
            if self.handle is not None:
                unreal.unregister_slate_post_tick_callback(self.handle)
                self.handle = None
                cleanup.append('slate callback unregistered')
        except Exception as exc:
            cleanup.append('callback unregister failed: %s' % (exc))
        try:
            if self.settings is not None:
                self.settings.set_editor_property(
                    'bThrottleCPUWhenNotForeground', self.throttle)
                cleanup.append('EditorPerformanceSettings.bThrottleCPUWhenNotForeground restored')
        except Exception as exc:
            cleanup.append('EditorPerformanceSettings restore failed: %s' % (exc))
        try:
            if self.level is not None and self.level.is_in_play_in_editor():
                self.level.editor_request_end_play()
                cleanup.append('PIE end requested')
        except Exception as exc:
            cleanup.append('PIE end failed: %s' % (exc))
        self.report['cleanup'] = cleanup
        try:
            self.report_file.parent.mkdir(parents=True, exist_ok=True)
            self.report['report_path'] = str(self.report_file)
            self.report_file.write_text(json.dumps(self.report, indent=2), encoding='utf-8')
            unreal.log('MHWI_BEHAVIOR_REPORT %s' % (self.report_file,))
        except Exception as exc:
            unreal.log_error('MHWI_BEHAVIOR_REPORT_WRITE_FAILED %s' % (exc,))
        try:
            unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        except Exception as exc:
            unreal.log_error('MHWI_BEHAVIOR_KEEP_ALIVE_FAILED %s' % (exc,))
        if not error:
            unreal.log('MHWI_BEHAVIOR_PASSED %s' % (self.requested,))
        self.world = None
        self.pawn = None
        self.pc = None
        self.anim = None
        self.sub = None
        self.actions = {}
        self.moves = None
        self.data = None
        self.target = None
        self.target_attrs = None
        _ACTIVE = None

    # ---------------------------------------------------------------- phases
    # boot

    def _phase_boot_prepare(self, elapsed):
        if self.level.is_in_play_in_editor():
            self.level.editor_request_end_play()
            self._phase('boot_end_old', 20.0)
            return
        self._phase('boot_load', 40.0)

    def _phase_boot_end_old(self, elapsed):
        if not self.level.is_in_play_in_editor():
            self._phase('boot_load', 40.0)

    def _phase_boot_load(self, elapsed):
        if self.level.is_in_play_in_editor():
            self.level.editor_request_end_play()
            return
        self._check(self.level.load_level(MAP_PATH), 'MHWI training map loads')
        self._phase('boot_start', 15.0)

    def _phase_boot_start(self, elapsed):
        self.level.editor_request_begin_play()
        self._phase('boot_wait', 40.0)

    def _phase_boot_wait(self, elapsed):
        if not self._setup_world():
            return
        self._begin_suite(self.suites[0])

    # --------------------------------------------------------------- ground

    def _phase_ground_assets(self, elapsed):
        for move, cost in [('SpiritI', 15.0), ('SpiritII', 15.0),
                           ('SpiritIII', 20.0), ('SpiritRoundslash', 25.0)]:
            self._check(abs(self._cost(move) - cost) < 0.01,
                        '%s keeps the published %.0f gauge cost' % (move, cost))
        spirit_windows = self._prop(self._def('SpiritI'), 'damage_windows', 'SpiritI')
        self._check(len(spirit_windows) > 0 and all(
            abs(float(window.get_editor_property('spirit_gain'))-10.0) < .001
            for window in spirit_windows),
            'SpiritI formal damage windows each grant ten gauge on real hit')
        self._check(not bool(self._prop(self._def('ForesightSlash'),
                                    'require_nonzero_gauge', 'ForesightSlash')),
                    'ForesightSlash permits zero-gauge evasion')
        self._check(bool(self._prop(self._def('ForesightSlash'),
                                    'counter_restores_gauge_on_hit', 'ForesightSlash')),
                    'Foresight restores gauge only after a counter-confirmed return hit')
        self._check(bool(self._prop(self._def('ForesightSlash'),
                                    'consume_all_gauge', 'ForesightSlash')),
                    'ForesightSlash still consumes the remaining gauge')
        self._check(bool(self._prop(self._def('SpiritThrust'),
                                    'require_spirit_level', 'SpiritThrust')),
                    'SpiritThrust still requires white or better')
        for move, clip in SOURCE_CLIP.items():
            definition = self._def(move)
            montage = self._prop(definition, 'montage', 'move ' + move)
            self._check(str(montage.get_name()) == 'M_' + move,
                        move + ' uses the formal M_' + move + ' montage')
            self._check(unreal.load_asset(self._clip_path(clip)) is not None,
                        move + ' source sequence ' + clip + ' exists')
            names, error = self._montage_sequence_names(montage)
            if names is None:
                self._note('montage segment read unavailable for %s: %s' % (move, error))
            else:
                self._check(clip in names,
                            move + ' montage actually references ' + clip)
        expected_windows = {'ForesightSlash': (70.0, 80.0),
                            'SpiritThrust': (84.0, 97.0)}
        for move, (start_frame, end_frame) in expected_windows.items():
            windows = list(self._prop(self._def(move), 'damage_windows',
                                      'move ' + move))
            self._check(len(windows) >= 1, move + ' has a real damage window')
            start = float(windows[0].get_editor_property('start_time'))
            end = float(windows[0].get_editor_property('end_time'))
            self._check(abs(start - start_frame / 60.0) <= 1.0 / 60.0 + 1e-4 and
                        abs(end - end_frame / 60.0) <= 1.0 / 60.0 + 1e-4,
                        move + ' damage window follows source frames %d-%d'
                        % (start_frame, end_frame))
        self.insert_cycle = 0
        self.ground_rmb = []
        self._phase('ground_draw', 20.0)

    def _phase_ground_draw(self, elapsed):
        if not self._idle():
            return
        self._check(self.pawn.is_sheathed(),
                    'ground suite starts from the saved sheathed stance')
        self._begin_stance_watch(True, 'ground_foresight_start', 'ground E -> drawn')
        self._press('toggle')
        self._phase('ground_draw_wait', 12.0)

    def _phase_ground_draw_wait(self, elapsed):
        self._stance_watch_tick()

    def _phase_ground_foresight_start(self, elapsed):
        threshold = self._num(self._def('ForesightSlash'), 'counter_minimum_gauge',
                              'ForesightSlash')
        if self._gauge() < threshold:
            self._start_gauge(threshold, 'ground_foresight_begin', 90.0)
            return
        self._phase('ground_foresight_begin', 20.0)

    def _phase_ground_foresight_begin(self, elapsed):
        self._reset_fixture(150.0)
        self.foresight_pressed = False
        self._press('light')
        self._phase('ground_foresight_wait', 12.0)

    def _phase_ground_foresight_wait(self, elapsed):
        self._place_target(150.0)
        name = self._current()
        if name == 'ForesightSlash':
            self._check(self._montage_name() == 'M_ForesightSlash',
                        'ForesightSlash plays its formal montage')
            self._phase('ground_foresight_pose', 8.0)
            return
        if name == 'None':
            if elapsed < 0.25:
                return
            raise BehaviorFailure(
                'ForesightSlash did not start from a real attack; gauge=%.1f'
                % (self._gauge(),))
        if name in ('DrawSlash', 'OverheadSlash', 'StepSlash', 'Thrust', 'RisingSlash'):
            if not self.foresight_pressed and self._cancel_ready(self._def(name), 'foresight'):
                self._check(self._gauge() > 0.01,
                            'a real normal hit filled the gauge before the F input')
                self._press('foresight')
                self.foresight_pressed = True

    def _phase_ground_foresight_pose(self, elapsed):
        name = self._current()
        if name != 'ForesightSlash':
            if name == 'None':
                raise BehaviorFailure('ForesightSlash ended before its pose sample')
            return
        if self._position() < 0.5:
            return
        self._check_pose('ForesightSlash', 'A_w03_00_140', self._position())
        # A real counter confirmation is independent of the later return hit.
        # Use the public Montage carrier for an exact in-window damage fixture,
        # then resume normal playback and require actual target damage to fill.
        montage = self.anim.get_current_active_montage()
        self.anim.montage_pause(montage)
        self.anim.montage_set_position(montage, .5)
        attrs = self.pawn.get_editor_property('attributes')
        before_hp = float(attrs.get_current_health())
        attrs.apply_damage(10.0, self.target)
        self._check(abs(attrs.get_current_health()-before_hp) < .001
                    and self.pawn.has_counter_confirmed(),
                    'Foresight confirms a real incoming hit without losing HP')
        self._check(self._gauge() < .001,
                    'Foresight counter confirmation alone does not fill the gauge')
        self.foresight_return_hp = self._hp()
        self.anim.montage_resume(montage)
        self._phase('ground_foresight_return', 12.0)

    def _phase_ground_foresight_return(self, elapsed):
        self._place_target(150.0)
        if self._hp() >= self.foresight_return_hp-.001:
            if self._idle():
                raise BehaviorFailure('counter-confirmed Foresight return failed to hit')
            return
        self._check(self._gauge() > 99.99,
                    'counter-confirmed real Foresight return hit fills the gauge')
        self.pawn.interrupt_move()
        self._check(self._idle(), 'interrupt releases the ForesightSlash foreground action')
        self._phase('ground_gauge_prepare', 20.0)

    def _phase_ground_gauge_prepare(self, elapsed):
        self._start_gauge(100.0, 'ground_insert_start', 150.0)

    def _phase_ground_insert_start(self, elapsed):
        if self.insert_cycle >= 3:
            self._check(len(self.ground_rmb) >= 6,
                        'at least six real RMB insertions were observed')
            self._check(self.ground_rmb == ['SpiritComboThrust',
                                            'SpiritComboRisingSlash'] * 3,
                        'six RMB presses alternate SpiritComboThrust/RisingSlash')
            self._phase('ground_roll_prepare', 30.0)
            return
        self._check(self._gauge() + 0.01 >= self._spirit_chain_stock(),
                    'formal gauge is stocked before spirit insertion cycle %d'
                    % (self.insert_cycle + 1))
        self.ins = {
            'expect': 'SpiritI', 'next_press': None, 'queued': False,
            'last': None, 'gauge_before_press': self._gauge(),
            'rmb': [], 'costs': [], 'level_before': self._level(),
            'round_seen': False,
        }
        self._place_target(150.0)
        self._press('spirit')
        self._phase('ground_insert_wait', 90.0)

    def _phase_ground_insert_wait(self, elapsed):
        self._place_target(150.0)
        name = self._current()
        ins = self.ins
        if name == 'None':
            if not ins.get('seen'):
                return
            self._check(ins.get('round_seen'),
                        'insertion cycle reaches SpiritRoundslash')
            self._check(ins['rmb'] == ['SpiritComboThrust', 'SpiritComboRisingSlash'],
                        'insertion cycle presses RMB into thrust then rising slash')
            self._check(self._level() >= ins['level_before'],
                        'insertion cycle does not lose spirit color')
            self._phase('ground_insert_after_cycle', 10.0)
            return
        if name != ins['last']:
            ins['last'] = name
            ins['queued'] = False
            ins['seen'] = True
            if name == ins['expect']:
                ins['stage_gauge'] = self._gauge()
                ins['stage_hp'] = self._hp()
                if name == 'SpiritI':
                    observed = ins['gauge_before_press'] - self._gauge()
                    self._check(abs(observed-self._cost('SpiritI')) < .75,
                                'normal SpiritI applies its formal cost once at start')
                if name in ('SpiritComboThrust', 'SpiritComboRisingSlash'):
                    ins['rmb'].append(name)
                    self.ground_rmb.append(name)
                    configured = self._cost(name)
                    observed = ins['gauge_before_press'] - self._gauge()
                    ins['costs'].append({'move': name, 'configured': configured,
                                         'observed': round(observed, 4)})
                    self._check(abs(observed - configured) < 0.75,
                                name + ' applies its configured formal gauge cost once')
                transitions = {
                    'SpiritI': ('thrust', 'SpiritComboThrust'),
                    'SpiritComboThrust': ('spirit', 'SpiritII'),
                    'SpiritII': ('thrust', 'SpiritComboRisingSlash'),
                    'SpiritComboRisingSlash': ('spirit', 'SpiritIII'),
                    'SpiritIII': ('spirit', 'SpiritRoundslash'),
                    'SpiritRoundslash': (None, None),
                }
                if name not in transitions:
                    raise BehaviorFailure('unexpected insertion move %r' % (name,))
                press, expect = transitions[name]
                ins['next_press'] = press
                ins['expect'] = expect
                if name == 'SpiritRoundslash':
                    ins['round_seen'] = True
            elif name not in ('SpiritI', 'SpiritComboThrust', 'SpiritII',
                              'SpiritComboRisingSlash', 'SpiritIII',
                              'SpiritRoundslash'):
                raise BehaviorFailure('insertion cycle reached unexpected move %r' % (name,))
        press = ins['next_press']
        if press and not ins['queued'] and self._cancel_ready(self._def(name), press):
            if name == 'SpiritI':
                windows = list(self._prop(self._def(name), 'damage_windows', name))
                if self._position() < max(float(w.get_editor_property('end_time')) for w in windows):
                    return
                expected_gain = sum(float(w.get_editor_property('spirit_gain')) for w in windows)
                self._check(self._hp() < ins['stage_hp'],
                            'SpiritI really hits before the insertion fixture continues')
                observed_gain = self._gauge()-ins['stage_gauge']
                expected_gain = min(100.0-ins['stage_gauge'], expected_gain)
                self._check(abs(observed_gain-expected_gain) < .75,
                            'SpiritI real hit grants its formal ten gauge once per window')
            ins['gauge_before_press'] = self._gauge()
            self._press(press)
            ins['queued'] = True

    def _phase_ground_insert_after_cycle(self, elapsed):
        if not self._idle():
            return
        self.insert_cycle += 1
        self._record('insertion_cycles', cycle=self.insert_cycle,
                     rmb=list(self.ins['rmb']), costs=list(self.ins['costs']),
                     gauge=round(self._gauge(), 2), level=self._level())
        if self.insert_cycle < 3:
            self._require_drawn('ground_gauge_prepare', 150.0)
        else:
            self._check(self.ground_rmb == ['SpiritComboThrust',
                                            'SpiritComboRisingSlash'] * 3,
                        'three real spirit chains preserve all six insertion identities')
            self._require_drawn('ground_rmb_start', 30.0)

    def _phase_ground_rmb_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self.rmb_loop = {'moves': [], 'queued': False, 'hp': self._hp()}
        self._press('thrust')
        self._phase('ground_rmb_watch', 30.0)

    def _phase_ground_rmb_watch(self, elapsed):
        self._place_target(150.0)
        name = self._current()
        state = self.rmb_loop
        expected = ['Thrust', 'RisingSlash'] * 3
        if name == 'None':
            if not state['moves']:
                if elapsed < 1.0:
                    return
                raise BehaviorFailure('ordinary B/A combo never started')
            self._check(state['moves'] == expected,
                         'six ordinary B/A actions alternate thrust and rising slash')
            self._check(self._hp() < state['hp'],
                         'ordinary B/A combo really damages the target')
            self._record('ordinary_b_a_combo', moves=list(state['moves']),
                         damage=round(state['hp'] - self._hp(), 3))
            self._phase('ground_roll_prepare', 30.0)
            return
        if not state['moves'] or state['moves'][-1] != name:
            index = len(state['moves'])
            self._check(index < len(expected) and name == expected[index],
                         'ordinary B/A action %d has the expected identity' % (index + 1))
            state['moves'].append(name)
            state['queued'] = False
        command = 'light' if name == 'Thrust' else 'thrust'
        if len(state['moves']) < 6 and not state['queued'] and self._cancel_ready(self._def(name), command):
            self._press(command)
            state['queued'] = True

    def _phase_ground_roll_prepare(self, elapsed):
        self._require_drawn('ground_roll_drawn', 30.0)

    def _phase_ground_roll_drawn(self, elapsed):
        if not self._idle():
            return
        roll = self._def('Roll')
        route = self._find_route(roll, 'light', 'RollStepSlash')
        self._check(route is not None,
                    'Roll has a formal Light route to RollStepSlash')
        self._check(bool(self._prop(route, 'require_drawn', 'Roll Light route')),
                    'RollStepSlash route carries require_drawn')
        roll_slash = self._def('RollStepSlash')
        roll_slash_montage = self._prop(roll_slash, 'montage', 'RollStepSlash')
        roll_windows = list(self._prop(roll_slash, 'damage_windows', 'RollStepSlash'))
        self._check(len(roll_windows) >= 1,
                    'RollStepSlash owns real damage timing after the 129+101 composite')
        segments, segment_error = self._montage_sequence_names(roll_slash_montage)
        if segments is None:
            self._note('RollStepSlash segment read unavailable: ' + str(segment_error))
        else:
            self._check('A_w03_00_101' in segments,
                        'RollStepSlash montage actually contains the A_w03_00_101 follow-through')
        self._reset_fixture(150.0)
        self.roll = {'pressed': False}
        self._press('evade')
        self._phase('ground_roll_drawn_wait', 12.0)

    def _roll_press_at(self):
        definition = self._def('Roll')
        cancel, cancel_end = self._cancel_window(definition, 'light')
        length = max(0.1, self._length())
        return max(0.0, min(max(cancel, length - 0.28),
                            max(0.0, length - 0.05), cancel_end))

    def _phase_ground_roll_drawn_wait(self, elapsed):
        name = self._current()
        if name == 'Roll':
            self.roll['seen_roll'] = True
            if not self.roll['pressed'] and self._position() >= self._roll_press_at():
                self._press('light')
                self.roll['pressed'] = True
            return
        if name == 'RollStepSlash':
            self._check(self._montage_name() == 'M_RollStepSlash',
                        'drawn Roll + LMB plays the dedicated M_RollStepSlash montage')
            self._record('roll_light', case='drawn', move=name,
                         montage=self._montage_name(),
                         position=round(self._position(), 3))
            self.pawn.interrupt_move()
            self._phase('ground_roll_sheathed', 10.0)
            return
        if name == 'None':
            if not self.roll.get('seen_roll'):
                return
            # One retry at the first idle frame while the bounded drawn recovery
            # identity is still alive; a second miss is a real failure.
            if not self.roll.get('retry'):
                self.roll['retry'] = True
                self._press('light')
                return
            raise BehaviorFailure(
                'drawn Roll ended without RollStepSlash (pressed=%s)'
                % (self.roll['pressed'],))

    def _phase_ground_roll_sheathed(self, elapsed):
        self._require_sheathed('ground_roll_sheathed_start', 20.0)

    def _phase_ground_roll_sheathed_start(self, elapsed):
        if not self._idle():
            return
        self._check(self.pawn.is_sheathed(), 'sheathed Roll fixture is really sheathed')
        self._reset_fixture(150.0)
        self.roll = {'pressed': False}
        self._press('evade')
        self._phase('ground_roll_sheathed_wait', 12.0)

    def _phase_ground_roll_sheathed_wait(self, elapsed):
        name = self._current()
        if name == 'Roll':
            self.roll['seen_roll'] = True
            # Press in the active Roll window, not after neutral recovery. The
            # sheathed fallback must resolve this to DrawSlash.
            if not self.roll['pressed'] and self._position() >= self._roll_press_at():
                self._press('light')
                self.roll['pressed'] = True
            return
        if name == 'None':
            if not self.roll.get('seen_roll'):
                return
            raise BehaviorFailure(
                'sheathed active Roll LMB did not reach DrawSlash (pressed=%s)'
                % (self.roll['pressed'],))
        if name == 'DrawSlash':
            self._check(self._montage_name() != 'M_RollStepSlash',
                        'sheathed Roll + LMB does not use the drawn RollStepSlash route')
            self._record('roll_light', case='sheathed_active', move=name,
                         montage=self._montage_name(),
                         position=round(self._position(), 3),
                         pressed_at_roll=bool(self.roll.get('pressed')))
            self.pawn.interrupt_move()
            self._phase('ground_roll_expired_prepare', 10.0)
            return
        if name == 'RollStepSlash':
            raise BehaviorFailure('sheathed Roll incorrectly selected RollStepSlash')
        if name == 'None':
            if not self.roll.get('seen_roll'):
                return
            raise BehaviorFailure(
                'sheathed Roll ended without DrawSlash (pressed=%s)'
                % (self.roll['pressed'],))

    def _phase_ground_roll_expired_prepare(self, elapsed):
        self._require_drawn('ground_roll_expired_start', 30.0)

    def _phase_ground_roll_expired_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self.roll = {'pressed': False, 'idle_at': None}
        self._press('evade')
        self._phase('ground_roll_expired_wait', 12.0)

    def _phase_ground_roll_expired_wait(self, elapsed):
        name = self._current()
        if name == 'Roll':
            self.roll['seen_roll'] = True
            return
        if name == 'None':
            if not self.roll.get('seen_roll'):
                return
            if self.roll.get('idle_at') is None:
                self.roll['idle_at'] = time.monotonic()
            if time.monotonic() - self.roll['idle_at'] >= 0.4:
                self._press('light')
                self._phase('ground_roll_expired_check', 10.0)
            return
        raise BehaviorFailure('unexpected move %r during expired Roll context' % (name,))

    def _phase_ground_roll_expired_check(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed > 0.8:
                raise BehaviorFailure('late LMB after Roll started no neutral action')
            return
        self._check(name != 'RollStepSlash',
                    'late LMB after Roll completion does not reuse RollStepSlash')
        self._check(name in ('OverheadSlash', 'DrawSlash', 'StepSlash'),
                    'late LMB starts an ordinary neutral action (%s)' % (name,))
        self._record('roll_light', case='expired', move=name,
                     montage=self._montage_name())
        self.pawn.interrupt_move()
        self._phase('ground_done', 8.0)

    def _phase_ground_done(self, elapsed):
        if self._idle():
            self._suite_done()

    # ------------------------------------------------------------ direction

    def _phase_dir_prepare(self, elapsed):
        thrust = self._def('Thrust')
        turn_start = self._num(thrust, 'turn_start_time', 'Thrust')
        turn_end = self._num(thrust, 'turn_end_time', 'Thrust')
        turn_angle = self._num(thrust, 'turn_max_angle', 'Thrust')
        turn_speed = self._num(thrust, 'turn_speed', 'Thrust')
        return_start = self._num(thrust, 'return_turn_start_time', 'Thrust')
        return_end = self._num(thrust, 'return_turn_end_time', 'Thrust')
        return_angle = self._num(thrust, 'return_turn_max_angle', 'Thrust')
        self._check(abs(turn_start) < 0.01,
                    'normal turn_start_time keeps the project default 0')
        self._check(abs(turn_end - 0.12) < 0.02,
                    'normal turn_end_time keeps the project default 0.12 s')
        self._check(abs(turn_angle - 25.0) < 0.5,
                    'normal turn_max_angle keeps the project default 25 deg')
        self._check(abs(turn_speed - 360.0) < 1.0,
                    'normal turn_speed keeps the project default 360 deg/s')
        self._check(abs(return_start + 1.0) < 0.01 and abs(return_end + 1.0) < 0.01,
                    'return turn window stays disabled by default')
        self._check(abs(return_angle - 45.0) < 0.5,
                    'return_turn_max_angle keeps the project default 45 deg')
        for name in ('FadeSlash', 'FadeSlashLeft', 'FadeSlashRight'):
            self._check(abs(self._num(self._def(name), 'turn_max_angle', name)) < 0.01,
                        name + ' disables extra programmatic entry turn')
        self._require_drawn('dir_start', 40.0)

    def _phase_dir_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(3000.0)
        self.cases = [
            (0, 'W', (0.0, 1.0), 'FadeSlash'),
            (0, 'S', (0.0, -1.0), 'FadeSlash'),
            (0, 'A', (-1.0, 0.0), 'FadeSlashLeft'),
            (0, 'D', (1.0, 0.0), 'FadeSlashRight'),
            (0, 'none', (0.0, 0.0), 'FadeSlash'),
            (90, 'W', (0.0, 1.0), 'FadeSlashRight'),
            (90, 'S', (0.0, -1.0), 'FadeSlashLeft'),
            (90, 'none', (0.0, 0.0), 'FadeSlash'),
            (180, 'D', (1.0, 0.0), 'FadeSlashLeft'),
            (180, 'A', (-1.0, 0.0), 'FadeSlashRight'),
            (180, 'none', (0.0, 0.0), 'FadeSlash'),
            (270, 'W', (0.0, 1.0), 'FadeSlashLeft'),
            (270, 'S', (0.0, -1.0), 'FadeSlashRight'),
            (270, 'none', (0.0, 0.0), 'FadeSlash'),
            (0, 'simultaneous A+C', (-1.0, 0.0), 'FadeSlashLeft'),
            (90, 'simultaneous W+C', (0.0, 1.0), 'FadeSlashRight'),
            (0, 'release+C', (0.0, 0.0), 'FadeSlash'),
        ]
        self.case_index = 0
        self._phase('dir_case_start', 10.0)

    def _phase_dir_case_start(self, elapsed):
        if self.case_index >= len(self.cases):
            self._phase('dir_turn_setup', 15.0)
            return
        if not self._idle():
            return
        yaw, label, vector, expected = self.cases[self.case_index]
        self._reset_fixture(3000.0)
        self._set_control_yaw(yaw)
        if label == 'release+C':
            self._move(-1.0, 0.0)  # prime a stale left value before releasing
        elif not label.startswith('simultaneous'):
            self._move(vector[0], vector[1])
        self.case = {'yaw': yaw, 'label': label, 'vector': vector,
                     'expected': expected, 'seen': False}
        self._phase('dir_case_press', 6.0)

    def _phase_dir_case_press(self, elapsed):
        # Let the injected Move value reach MoveInput, but keep the idle turn
        # toward the stick short enough that the camera-relative choice stays
        # on the intended side of A's 0.2 right-axis dead zone.
        # Slate can tick more than once before a game/input frame at low FPS.
        # Wait for a world tick AFTER the first held-value injection, so Fade
        # cannot be processed ahead of the first Move event in the same frame.
        world_time = float(unreal.GameplayStatics.get_time_seconds(self.world))
        simultaneous = self.case['label'].startswith('simultaneous')
        if not simultaneous and 'primed_world_time' not in self.case:
            self.case['primed_world_time'] = world_time
            return
        if elapsed < 0.05 or (not simultaneous and
                world_time <= self.case['primed_world_time'] + 1e-5):
            return
        case = self.case
        # Drop residual locomotion velocity and re-establish the known facing
        # after the Move input has been sampled. Selection then projects the
        # camera-relative intent onto this pre-selection right axis, and only the
        # fade clip's authored root motion contributes to the displacement.
        try:
            self.pawn.character_movement.stop_movement_immediately()
            # This fixture promises a known pre-selection basis. At 10 FPS the
            # idle movement component can otherwise turn a full 90 degrees in
            # the frame between this callback and the queued Fade command.
            # StartResolvedMove also disables idle facing; FinishMove restores
            # it. Only this disposable PIE instance is changed here.
            self.pawn.character_movement.set_editor_property(
                'orient_rotation_to_movement', False)
            self.pawn.set_actor_rotation(
                unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0), False)
        except Exception:
            pass
        case['start'] = self.pawn.get_actor_location()
        case['forward'] = self.pawn.get_actor_forward_vector()
        case['right'] = self.pawn.get_actor_right_vector()
        case['selected_yaw'] = self._actor_yaw()
        intent = self._world_intent(case['vector'][0], case['vector'][1])
        side = _dot_xy(unreal.Vector(intent[0], intent[1], 0.0), case['right'])
        computed = ('FadeSlashRight' if side > 0.2 else
                    ('FadeSlashLeft' if side < -0.2 else 'FadeSlash'))
        case['intent'] = intent
        case['side'] = side
        case['computed'] = computed
        case['released'] = False
        self._check(computed == case['expected'],
                    'fixture base for yaw %s input %s yields %s (side %.3f)'
                    % (case['yaw'], case['label'], computed, side))
        if simultaneous or case['label'] == 'release+C':
            self._move(case['vector'][0], case['vector'][1])
            # The post-handler pump queues this transition with C in the SAME
            # game frame, once, without adding the previous held vector to it.
        self._press('fade')
        # Keep the real Move input held until the Fade action is actually
        # observed; releasing immediately can let Move Completed clear MoveInput
        # before Enhanced Input processes the Fade request.
        self._phase('dir_case_measure', 10.0)

    def _phase_dir_case_measure(self, elapsed):
        name = self._current()
        case = self.case
        if name == 'None':
            if elapsed < 0.2:
                return
            raise BehaviorFailure(
                'camera yaw %s input %s fade ended without %s'
                % (case['yaw'], case['label'], case['expected']))
        if not case['released']:
            case['released'] = True
            case['release_position'] = round(self._position(), 3)
            self._stop_inputs()
        expected = case['computed']
        if name != expected:
            raise BehaviorFailure(
                'camera yaw %s input %s selected %s, computed base expected %s; '
                'pre-yaw %.2f observed-yaw %.2f'
                % (case['yaw'], case['label'], name, expected,
                   case['selected_yaw'], self._actor_yaw()))
        if not case['seen']:
            case['seen'] = True
            case['montage'] = self._montage_name()
            self._record('fade_selection', camera_yaw=case['yaw'],
                         input=case['label'], move=name, montage=case['montage'],
                         control_yaw=round(self._control_yaw(), 2),
                         actor_right=[round(float(case['right'].x), 3),
                                      round(float(case['right'].y), 3)],
                         intent=[round(case['intent'][0], 3),
                                 round(case['intent'][1], 3)],
                         side=round(case['side'], 3),
                         release_position=case['release_position'])
        length = max(0.2, self._length())
        if self._position() < min(1.0, length * 0.78):
            return
        displacement = self.pawn.get_actor_location() - case['start']
        lateral = _dot_xy(displacement, case['right'])
        forward = _dot_xy(displacement, case['forward'])
        distance = _len_xy(displacement)
        self._check(distance > 20.0,
                    'fade yaw %s input %s produces real displacement (%.1f cm)'
                    % (case['yaw'], case['label'], distance))
        if case['expected'] == 'FadeSlashRight':
            self._check(lateral > 15.0,
                        'right fade displaces along the pre-selection actor right axis')
        elif case['expected'] == 'FadeSlashLeft':
            self._check(lateral < -15.0,
                        'left fade displaces against the pre-selection actor right axis')
        else:
            self._check(forward < -15.0,
                        'no-input/forward-axis fade displaces backward')
        yaw_delta = _yaw_delta(case['selected_yaw'], self._actor_yaw())
        self._check(abs(yaw_delta) < 5.0,
                    'fade selection does not add a second programmatic actor turn')
        self._record('fade_displacement', camera_yaw=case['yaw'],
                     input=case['label'], move=name, lateral=round(lateral, 2),
                     forward=round(forward, 2), distance=round(distance, 2),
                     yaw_delta=round(yaw_delta, 2))
        self.pawn.interrupt_move()
        self._phase('dir_case_next', 6.0)

    def _phase_dir_case_next(self, elapsed):
        if not self._idle():
            return
        self.case_index += 1
        self._phase('dir_case_start', 10.0)

    def _phase_dir_turn_setup(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(3000.0)
        self._set_control_yaw(90.0)
        self._move(0.0, 1.0)
        self.turn = {'before': self._actor_yaw(), 'move': 'Thrust'}
        self._press('thrust')
        self._phase('dir_turn_measure', 10.0)

    def _phase_dir_turn_measure(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed < 0.2:
                return
            raise BehaviorFailure('normal turn fixture ended before sampling')
        if name != 'Thrust':
            raise BehaviorFailure('normal turn fixture started %r instead of Thrust' % (name,))
        if self._position() < 0.3:
            return
        delta = _yaw_delta(self.turn['before'], self._actor_yaw())
        self._check(delta > 2.0,
                    'normal action turns toward the camera-relative move intent')
        self._check(delta <= 29.0,
                    'normal action respects the project max turn angle (%.1f deg)' % (delta,))
        self._record('turns', case='normal', move=name, delta=round(delta, 2),
                     control_yaw=round(self._control_yaw(), 2))
        self.pawn.interrupt_move()
        self._phase('dir_derived_setup', 12.0)

    def _phase_dir_derived_setup(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(3000.0)
        self._set_control_yaw(0.0)
        self._stop_inputs()
        self._press('thrust')
        self.derived = {'pressed': False}
        self._phase('dir_derived_wait', 15.0)

    def _phase_dir_derived_wait(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed < 0.2:
                return
            raise BehaviorFailure('derived turn fixture ended before the chain window')
        if name == 'Thrust':
            if not self.derived['pressed'] and self._cancel_ready(self._def('Thrust'), 'light'):
                self._set_control_yaw(180.0)
                self._move(0.0, 1.0)
                self.derived['before'] = self._actor_yaw()
                self.derived['pressed'] = True
                self._press('light')
                self._phase('dir_derived_measure', 12.0)

    def _phase_dir_derived_measure(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed < 0.2:
                return
            raise BehaviorFailure('derived turn ended before RisingSlash')
        if name != 'RisingSlash':
            return
        if 'start_yaw' not in self.derived:
            self.derived['start_yaw'] = self._actor_yaw()
        if self._position() < 0.3:
            return
        delta = _yaw_delta(self.derived['start_yaw'], self._actor_yaw())
        self._check(delta > 2.0,
                    'a normal derived action turns toward the camera-relative input')
        self._check(delta <= 29.0,
                    'derived normal action respects the project max turn angle (%.1f deg)'
                    % (delta,))
        self._record('turns', case='derived', move=name, delta=round(delta, 2))
        self.pawn.interrupt_move()
        self._phase('dir_camera_setup', 10.0)

    def _phase_dir_camera_setup(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(3000.0)
        self._set_control_yaw(0.0)
        self._stop_inputs()
        self.camera_only = {'before': self._actor_yaw(), 'look_sent': False}
        self._press('thrust')
        self._phase('dir_camera_measure', 12.0)

    def _phase_dir_camera_measure(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed < 0.3:
                return
            raise BehaviorFailure('camera-only fixture ended before sampling')
        if name != 'Thrust':
            return
        if not self.camera_only['look_sent'] and self._position() >= 0.05:
            self._inject('MHWI_Look', (20.0, 0.0, 0.0))
            self._set_control_yaw(120.0)
            self.camera_only['look_sent'] = True
        if self._position() < 0.5:
            return
        delta = _yaw_delta(self.camera_only['before'], self._actor_yaw())
        self._check(abs(delta) < 2.0,
                    'with no move input, changing the camera does not turn the actor')
        self._record('camera_only', move=name, yaw_delta=round(delta, 3),
                     control_yaw=round(self._control_yaw(), 2))
        self.pawn.interrupt_move()
        self._phase('dir_done', 8.0)

    def _phase_dir_done(self, elapsed):
        if self._idle():
            self._suite_done()

    # ------------------------------------------------------------------ air

    def _phase_air_read(self, elapsed):
        for name in HELM_MOVES:
            self._def(name)
        vertical = self._num(self.data, 'helm_air_vertical_speed', 'UMHWIMovesetData')
        forward = self._num(self.data, 'helm_air_forward_speed', 'UMHWIMovesetData')
        gravity = self._num(self.data, 'helm_air_gravity', 'UMHWIMovesetData')
        strike = self._num(self.data, 'helm_strike_speed', 'UMHWIMovesetData')
        strike_start = self._num(self.data, 'helm_strike_start_time', 'UMHWIMovesetData')
        self._check(vertical > 0.0 and forward > 0.0 and gravity > 0.0 and strike > 0.0,
                    'helm aerial speeds and gravity are positive project tuning')
        self._check(0.0 < strike_start < 1.5,
                    'helm strike start time is a positive montage offset')
        self._check(bool(self._prop(self._def('HelmRise'), 'use_full_root_motion',
                                    'HelmRise')),
                    'HelmRise keeps full vertical root motion')
        rise_next = str(self._optional_prop(self._def('HelmRise'), 'auto_follow_up') or '')
        self._check(rise_next == 'HelmAir', 'HelmRise auto-follows into HelmAir')
        for name in ('HelmAir', 'SpiritHelmBreaker'):
            auto = self._optional_prop(self._def(name), 'auto_follow_up')
            self._check(auto is None or str(auto) in ('None', ''),
                        name + ' has no automatic montage exit')
        windows = list(self._prop(self._def('HelmLand'), 'damage_windows', 'HelmLand'))
        self._check(len(windows) == 7, 'HelmLand keeps exactly seven delayed damage windows')
        self._check(bool(self._prop(self._def('HelmLand'), 'spend_spirit_level',
                                    'HelmLand')),
                    'HelmLand still owns the spirit-color spend')
        self.report['helm_physics'] = {
            'vertical_speed': vertical, 'forward_speed': forward, 'gravity': gravity,
            'strike_speed': strike, 'strike_start_time': strike_start,
        }
        self._require_drawn('air_level_prep', 40.0)

    def _phase_air_level_prep(self, elapsed):
        self._start_level_prep('air_miss_setup')

    def _phase_air_miss_setup(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._set_control_yaw(0.0)
        self._place_target(3000.0)
        self._stop_inputs()
        start = self.pawn.get_actor_location()
        self.air = {'level': self._level(), 'gauge': self._gauge(), 'hp': self._hp(),
                    'z': float(start.z), 'max_z': float(start.z), 'seen': [],
                    'last': None}
        self._check(self.air['level'] >= 1,
                    'white or better is available before the miss fixture')
        self._press('helm')
        self._phase('air_miss_watch', 10.0)

    def _phase_air_miss_watch(self, elapsed):
        name = self._current()
        state = self.air
        state['max_z'] = max(state['max_z'], float(self.pawn.get_actor_location().z))
        if name != state['last']:
            state['last'] = name
            if name != 'None':
                state['seen'].append(name)
                if name in HELM_MOVES[1:]:
                    raise BehaviorFailure(
                        'missed SpiritThrust still entered aerial stage ' + name)
        if name == 'None':
            if not state['seen']:
                if elapsed < 0.5:
                    return
                raise BehaviorFailure('missed G input never started SpiritThrust')
            self._check(state['seen'] == ['SpiritThrust'],
                        'missed thrust only plays SpiritThrust (saw %s)'
                        % (state['seen'],))
            self._check(self._level() == state['level'],
                        'missed thrust does not change the spirit color')
            self._check(abs(self._gauge() - state['gauge']) < 0.75,
                        'missed thrust does not consume gauge')
            self._check(abs(self._hp() - state['hp']) < 0.01,
                        'missed thrust deals no target damage')
            self._check(state['max_z'] - state['z'] < 20.0,
                        'missed thrust does not lift the actor')
            self._check(not self._is_flying(),
                        'missed thrust restores a non-flying movement mode')
            self._record('helm_miss', seen=list(state['seen']),
                         level=self._level(), gauge=round(self._gauge(), 2),
                         hp=round(self._hp(), 2))
            self._phase('air_nostrike_setup', 15.0)

    def _phase_air_nostrike_setup(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._set_control_yaw(0.0)
        self._place_target(150.0)
        self._stop_inputs()
        start = self.pawn.get_actor_location()
        self.nostrike = {
            'level': self._level(), 'gauge': self._gauge(), 'hp': self._hp(),
            'z': float(start.z), 'max_z': float(start.z), 'rise_max_z': float(start.z),
            'seen': [], 'last': None, 'rise_start': None, 'air_start': None,
            'land_start': None, 'land_hp': None, 'last_hp': self._hp(),
            'modes': [], 'idle_at': None, 'samples': 0, 'pose_sampled': False,
        }
        self._check(self.nostrike['level'] >= 1,
                    'white or better is available before the no-strike helm')
        self._press('helm')
        self._phase('air_nostrike_watch', 40.0)

    def _phase_air_nostrike_watch(self, elapsed):
        name = self._current()
        now = time.monotonic()
        state = self.nostrike
        location = self.pawn.get_actor_location()
        hp = self._hp()
        if name != state['last']:
            state['last'] = name
            if name != 'None':
                state['seen'].append(name)
                if name == 'HelmRise':
                    state['rise_start'] = now
                elif name == 'HelmAir':
                    state['air_start'] = now
                elif name == 'HelmLand':
                    state['land_start'] = now
                    # SpiritThrust's own hit already happened; use the pre-Land HP
                    # so only Land-window damage is attributed to the landing.
                    state['land_hp'] = max(hp, state['last_hp'])
                elif name == 'SpiritHelmBreaker':
                    raise BehaviorFailure(
                        'helm Air entered the strike without any attack input')
        if name == 'SpiritThrust':
            self._place_target(150.0)
            if not state['pose_sampled'] and 0.55 <= self._position() <= 0.8:
                self._check_pose('SpiritThrust', 'A_w03_00_170', self._position())
                state['pose_sampled'] = True
        if name == 'HelmRise':
            state['rise_max_z'] = max(state['rise_max_z'], float(location.z))
        if name == 'HelmAir':
            state['modes'].append(self._mode_name())
        if state['samples'] < 300:
            self._record('air_nostrike_samples', move=name,
                         position=round(self._position(), 3),
                         z=round(float(location.z), 2),
                         vz=round(float(self._velocity().z), 2),
                         mode=self._mode_name(), hp=round(self._hp(), 2))
            state['samples'] += 1
        state['last_hp'] = hp
        if name == 'None':
            if not state['seen']:
                if elapsed < 0.5:
                    return
                raise BehaviorFailure('no-strike G input never started SpiritThrust')
            if state['idle_at'] is None:
                state['idle_at'] = now
            if now - state['idle_at'] < 0.4:
                return
            for required in ('SpiritThrust', 'HelmRise', 'HelmAir', 'HelmLand'):
                self._check(required in state['seen'],
                            'no-strike helm route visits ' + required)
            self._check('SpiritHelmBreaker' not in state['seen'],
                        'no-strike helm never enters SpiritHelmBreaker')
            self._check(state['pose_sampled'],
                        'SpiritThrust 170 pose was sampled during the real playback')
            self._check(self._level() == state['level'],
                        'natural helm landing without strike input preserves the color')
            self._check(state['land_hp'] is not None,
                        'no-strike helm observed the HelmLand stage')
            self._check(abs(hp - state['land_hp']) < 0.01,
                        'HelmLand without strike authorization awards no seven hits')
            self._check(state['rise_max_z'] - state['z'] > 50.0,
                        'HelmRise really lifts the capsule with vertical root motion')
            self._check(state['modes'] and
                        all('MOVE_FLYING' not in mode for mode in state['modes']),
                        'HelmAir uses physics movement on every sampled frame')
            self._check(not self._is_flying(),
                        'natural landing leaves a non-flying movement mode')
            self._check(abs(float(self.pawn.get_actor_location().z) - state['z']) < 30.0,
                        'natural landing returns the capsule near the floor')
            air_seconds = ((state['land_start'] or now) - (state['air_start'] or now))
            self._check(0.0 < air_seconds < 6.0,
                        'HelmAir reaches a real landing instead of waiting out a montage loop')
            self._record('helm_nostrike', seen=list(state['seen']),
                         air_seconds=round(air_seconds, 3),
                         rise_cm=round(state['rise_max_z'] - state['z'], 2),
                         level=self._level(), hp=round(self._hp(), 2))
            self._phase('air_tail_setup', 15.0)

    def _phase_air_tail_setup(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._stop_inputs()
        self.tail = {'boosted': False, 'pose': None, 'pose_at': None, 'held_samples': 0,
                     'level': self._level(), 'hp': None, 'land_seen': False}
        self._press('helm')
        self._phase('air_tail_watch', 20.0)

    def _phase_air_tail_watch(self, elapsed):
        name = self._current()
        state = self.tail
        if name == 'SpiritThrust':
            self._place_target(150.0)
        if name == 'HelmAir':
            if not state['boosted']:
                point = self.pawn.get_actor_location()
                self.pawn.set_actor_location(
                    unreal.Vector(point.x, point.y, point.z + 5000.0), False, True)
                state['boosted'] = True
                state['hp'] = self._hp()
                self._record('aerial_tail', event='height_fixture', extra_height_cm=5000)
            if self._position() >= self._length() - 0.02:
                self._check(self._montage_name() == 'M_HelmAir',
                            'high-drop Air keeps its montage as the pose carrier')
                if state['pose_at'] is None:
                    state['pose_at'] = time.monotonic()
                if time.monotonic() - state['pose_at'] < 0.08:
                    return
                bones = [self.pawn.mesh.get_socket_transform(
                    bone, unreal.RelativeTransformSpace.RTS_COMPONENT).translation
                         for bone in POSE_BONES]
                if state['pose'] is None:
                    state['pose'] = bones
                else:
                    error = max((a - b).length() for a, b in zip(bones, state['pose']))
                    self._check(error < 1.0, 'Air tail keeps the final pose during a long fall')
                    state['held_samples'] += 1
        if name == 'HelmLand':
            state['land_seen'] = True
        if name == 'None' and state['boosted']:
            self._check(state['held_samples'] >= 2,
                        'high-drop fixture observed the held Air pose after its animation tail')
            self._check(state['land_seen'] and not self._is_flying(),
                        'high-drop Air still exits only through physical landing')
            self._check(abs(self._hp() - state['hp']) < 0.01 and
                        self._level() == state['level'],
                        'high-drop landing without a strike has no seven hits or color spend')
            self._record('aerial_tail', event='completed', held_samples=state['held_samples'])
            self._phase('air_early_setup', 15.0)

    def _phase_air_early_setup(self, elapsed):
        if not self._idle():
            return
        level = self._level()
        self._check(level >= 1,
                    'white or better remains before the early-landing fixture')
        self._reset_fixture(150.0)
        self._set_control_yaw(0.0)
        self._place_target(150.0)
        self._stop_inputs()
        start = self.pawn.get_actor_location()
        early = {
            'level': level, 'hp': self._hp(), 'z': float(start.z),
            'strike_start': self._num(self.data, 'helm_strike_start_time',
                                      'UMHWIMovesetData'),
            'strike_speed': self._num(self.data, 'helm_strike_speed',
                                      'UMHWIMovesetData'),
            'seen': [], 'last': None, 'pressed': False, 'forced': False,
            'strike_pos': None, 'strike_vz': None, 'land_hp': None,
            'idle_at': None, 'forced_at': None, 'last_hp': self._hp(),
        }
        self.early = early
        self._press('helm')
        self._phase('air_early_watch', 30.0)

    def _phase_air_early_watch(self, elapsed):
        name = self._current()
        state = self.early
        if name != state['last']:
            state['last'] = name
            if name != 'None':
                state['seen'].append(name)
        if name == 'SpiritThrust':
            self._place_target(150.0)
        if name == 'HelmAir' and not state['pressed']:
            self._press('light')
            state['pressed'] = True
        if name == 'SpiritHelmBreaker':
            position = self._position()
            if not state['forced'] and position < state['strike_start'] - 0.03:
                # Force an early landing before the 173 clip reaches its 25/60
                # descent point. This must not authorize the seven-hit landing.
                now = time.monotonic()
                state['strike_pos'] = round(position, 3)
                state['strike_vz'] = round(float(self._velocity().z), 2)
                self._check(float(self._velocity().z) >
                            -state['strike_speed'] * 0.8,
                            'Strike before 25/60 has not already applied the fast descent')
                location = self.pawn.get_actor_location()
                try:
                    self.pawn.set_actor_location(
                        unreal.Vector(float(location.x), float(location.y), 94.15),
                        False, True)
                    self.pawn.character_movement.stop_movement_immediately()
                except Exception as exc:
                    raise BehaviorFailure(
                        'early-landing fixture could not reposition the actor: %s'
                        % (exc,))
                try:
                    self.pawn.character_movement.set_movement_mode(
                        unreal.MovementMode.MOVE_WALKING)
                except Exception:
                    try:
                        self.pawn.character_movement.set_movement_mode(
                            unreal.MovementMode.MOVE_WALKING, 0)
                    except Exception:
                        pass
                state['forced'] = True
                state['forced_at'] = now
                self._record('helm_early_land', phase='forced', position=state['strike_pos'],
                             vz=state['strike_vz'], level=self._level(),
                             hp=round(self._hp(), 2))
                self._phase('air_early_land', 8.0)
                return
            if not state['forced'] and position >= state['strike_start'] - 0.03:
                raise BehaviorFailure(
                    'early-landing fixture could not ground before 25/60; '
                    'strike position %.3f' % (position,))
        state['last_hp'] = self._hp()
        if name == 'None' and not state['forced']:
            if not state['seen']:
                if elapsed < 0.5:
                    return
                raise BehaviorFailure('early-landing G input never started SpiritThrust')
            raise BehaviorFailure('helm chain ended before the early Strike fixture')

    def _phase_air_early_land(self, elapsed):
        name = self._current()
        state = self.early
        hp = self._hp()
        if name == 'HelmLand':
            # Use the previous tick's HP so a Land window that already resolved
            # on this frame is still counted as unauthorized damage.
            state['land_hp'] = max(hp, state['last_hp'])
            state['last_hp'] = hp
            self._record('helm_early_land', phase='land',
                         level=self._level(), hp=round(hp, 2),
                         baseline=round(state['land_hp'], 2))
            self._phase('air_early_settle', 10.0)
            return
        state['last_hp'] = hp
        if name == 'SpiritHelmBreaker' and self._position() >= state['strike_start'] - 0.02:
            raise BehaviorFailure(
                'Strike reached the 25/60 commit before the forced early landing')
        if name is None or name == 'None':
            raise BehaviorFailure(
                'forced early landing ended without HelmLand (last=%r)' % (state['last'],))

    def _phase_air_early_settle(self, elapsed):
        # Wait for the early HelmLand itself to finish before checking the color
        # spend, which A performs in FinishMove rather than at the first window.
        if not self._idle():
            return
        if elapsed < 0.5:
            return
        state = self.early
        hp = self._hp()
        self._check(state['land_hp'] is not None,
                    'early landing actually entered HelmLand')
        self._check(abs(hp - state['land_hp']) < 0.01,
                    'landing before the 25/60 commit awards no seven-hit damage')
        self._check(self._level() == state['level'],
                    'landing before the 25/60 commit does not spend a spirit color')
        self._check(not self._is_flying(),
                    'early landing restores a non-flying movement mode')
        self._record('helm_early_land', phase='settle',
                     forced_position=state['strike_pos'], forced_vz=state['strike_vz'],
                     hp=round(hp, 2), level=self._level())
        self._phase('air_strike_setup', 15.0)

    def _phase_air_strike_setup(self, elapsed):
        if not self._idle():
            return
        level = self._level()
        self._check(level >= 1, 'white or better remains before the strike helm')
        self._reset_fixture(150.0)
        self._set_control_yaw(0.0)
        self._place_target(150.0)
        self._stop_inputs()
        start = self.pawn.get_actor_location()
        strike = self._num(self.data, 'helm_strike_speed', 'UMHWIMovesetData')
        self.strike = {
            'level': level, 'hp': self._hp(), 'z': float(start.z),
            'strike_speed': strike, 'strike_start': self._num(
                self.data, 'helm_strike_start_time', 'UMHWIMovesetData'),
            'seen': [], 'last': None, 'pressed': False, 'steps': 0,
            'last_hp': self._hp(), 'min_vz': 0.0, 'pre_vz': None, 'post_vz': None,
            'idle_at': None, 'samples': 0, 'rise_max_z': float(start.z),
            'modes': [], 'land_hp': None, 'land_seen': False,
        }
        self._press('helm')
        self._phase('air_strike_watch', 40.0)

    def _phase_air_strike_watch(self, elapsed):
        name = self._current()
        now = time.monotonic()
        state = self.strike
        location = self.pawn.get_actor_location()
        velocity = self._velocity()
        hp = self._hp()
        if name != state['last']:
            state['last'] = name
            if name != 'None':
                state['seen'].append(name)
                if name == 'HelmLand':
                    # SpiritThrust's hit and the Strike wind-up are not Land damage.
                    # Baseline against the previous tick's HP so a first Window that
                    # already resolved this frame is still attributed to Land.
                    state['land_hp'] = max(hp, state['last_hp'])
                    state['land_seen'] = True
                    state['steps'] = 0
                    state['last_hp'] = state['land_hp']
        if name == 'SpiritThrust':
            self._place_target(150.0)
        if name == 'HelmAir' and not state['pressed']:
            self._press('light')
            state['pressed'] = True
            self._record('helm_strike_input', move=name,
                         position=round(self._position(), 3))
        if name == 'SpiritHelmBreaker':
            position = self._position()
            if position < state['strike_start'] - 0.03 and state['pre_vz'] is None:
                state['pre_vz'] = float(velocity.z)
                self._check(state['pre_vz'] > -state['strike_speed'] * 0.8,
                            'strike does not slam down before its project start time')
            if position >= state['strike_start'] + 0.02 and state['post_vz'] is None:
                state['post_vz'] = float(velocity.z)
                self._check(state['post_vz'] <= -state['strike_speed'] * 0.8,
                            'strike commits the configured fast downward speed after its start')
        if name == 'HelmRise':
            state['rise_max_z'] = max(state['rise_max_z'], float(location.z))
        if name in ('HelmAir', 'SpiritHelmBreaker'):
            state['modes'].append(self._mode_name())
        state['min_vz'] = min(state['min_vz'], float(velocity.z))
        if state['land_seen'] and hp < state['last_hp'] - 0.01:
            state['steps'] += 1
            state['last_hp'] = hp
        if state['samples'] < 300:
            self._record('air_strike_samples', move=name,
                         position=round(self._position(), 3),
                         z=round(float(location.z), 2),
                         vz=round(float(velocity.z), 2),
                         mode=self._mode_name(), hp=round(hp, 2))
            state['samples'] += 1
        state['last_hp'] = hp
        if name == 'None':
            if not state['seen']:
                if elapsed < 0.5:
                    return
                raise BehaviorFailure('strike G input never started SpiritThrust')
            if state['idle_at'] is None:
                state['idle_at'] = now
            if now - state['idle_at'] < 0.5:
                return
            for required in HELM_MOVES:
                self._check(required in state['seen'],
                            'strike helm route visits ' + required)
            self._check(state['pressed'],
                        'air attack input was submitted during HelmAir')
            self._check(state['post_vz'] is not None or
                        state['min_vz'] <= -state['strike_speed'] * 0.8,
                        'strike commits the configured fast downward speed')
            self._check(state['rise_max_z'] - state['z'] > 50.0,
                        'strike helm retains the HelmRise vertical lift')
            self._check(state['modes'] and
                        all('MOVE_FLYING' not in mode for mode in state['modes']),
                        'HelmAir and SpiritHelmBreaker use physics movement on every sample')
            multiplier_before = [1.0, 1.05, 1.1, 1.2][state['level']]
            # Independent original shell values; no longer the adapter's old 20.
            original_bases = {1: 10.0, 2: 15.0, 3: 25.0}
            expected = (7.0 * original_bases[state['level']] * multiplier_before,)
            self._check(state['land_hp'] is not None,
                        'strike helm observed the HelmLand stage')
            damage = state['land_hp'] - hp
            self._check(any(abs(damage - value) < 0.75 for value in expected),
                        'HelmLand damage equals seven authorized original-color base commits')
            self._check(state['steps'] >= 5,
                        'HelmLand produced at least five distinct damage commits (saw %d)'
                        % (state['steps'],))
            self._check(self._level() == state['level'] - 1,
                        'authorized strike consumes exactly one spirit color')
            self._check(not self._is_flying(),
                        'authorized strike restores a non-flying movement mode')
            self._check(abs(float(self.pawn.get_actor_location().z) - state['z']) < 30.0,
                        'authorized strike returns the capsule near the floor')
            self._record('helm_strike', seen=list(state['seen']),
                         damage=round(damage, 2), expected=list(expected),
                         steps=state['steps'], level_before=state['level'],
                         level_after=self._level(), min_vz=round(state['min_vz'], 2),
                         pre_vz=state['pre_vz'], post_vz=state['post_vz'])
            self._phase('air_strike_settle', 8.0)

    def _phase_air_strike_settle(self, elapsed):
        if elapsed < 0.5:
            return
        hp = self._hp()
        self._check(abs(hp - self.strike['last_hp']) < 0.01,
                    'no extra HelmLand damage arrives after the seven commits')
        self._check(not self._is_flying(),
                    'movement mode stays restored after the strike sequence')
        self._suite_done()

    # ------------------------------------------------------------ lifecycle

    def _phase_life_prepare(self, elapsed):
        targets = list(unreal.GameplayStatics.get_all_actors_of_class(
            self.world, unreal.MHWITrainingTarget))
        self._check(all(not bool(t.get_editor_property('enable_attacks'))
                        for t in targets),
                    'training targets remain passive by default during lifecycle checks')
        self._require_drawn('life_roll_expired_start', 30.0)

    def _phase_life_roll_expired_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._stop_inputs()
        self.life = {'seen_roll': False, 'idle_at': None}
        self._press('evade')
        self._phase('life_roll_expired_wait', 12.0)

    def _phase_life_roll_expired_wait(self, elapsed):
        name = self._current()
        if name == 'Roll':
            self.life['seen_roll'] = True
            return
        if name == 'None':
            if not self.life['seen_roll']:
                return
            if self.life['idle_at'] is None:
                self.life['idle_at'] = time.monotonic()
            if time.monotonic() - self.life['idle_at'] >= 0.4:
                self._press('light')
                self._phase('life_roll_expired_check', 10.0)
            return
        raise BehaviorFailure('unexpected move %r while waiting for Roll to expire' % (name,))

    def _phase_life_roll_expired_check(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed > 0.8:
                raise BehaviorFailure('late LMB after Roll started no neutral action')
            return
        self._check(name != 'RollStepSlash',
                    'expired Roll recovery no longer routes LMB to RollStepSlash')
        self._record('roll_lifecycle', case='expired', move=name,
                     montage=self._montage_name())
        self.pawn.interrupt_move()
        self._phase('life_roll_interrupt_start', 8.0)

    def _phase_life_roll_interrupt_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._stop_inputs()
        self.life = {'seen_roll': False}
        self._press('evade')
        self._phase('life_roll_interrupt_wait', 12.0)

    def _phase_life_roll_interrupt_wait(self, elapsed):
        name = self._current()
        if name == 'Roll':
            self.life['seen_roll'] = True
            length = max(0.2, self._length())
            if self._position() >= max(0.35, length * 0.5):
                self.pawn.interrupt_move()
                self._check(self._idle(),
                            'explicit interrupt releases the Roll foreground action')
                self._record('roll_lifecycle', case='interrupted', move='Roll',
                             position=round(self._position(), 3))
                self._phase('life_roll_interrupt_settle', 6.0)
            return
        if name == 'None' and self.life['seen_roll']:
            self._phase('life_roll_interrupt_settle', 6.0)
            return
        if name == 'None':
            return
        raise BehaviorFailure('unexpected move %r during interrupted Roll' % (name,))

    def _phase_life_roll_interrupt_settle(self, elapsed):
        if not self._idle():
            return
        if elapsed < 0.35:
            return
        self._press('light')
        self._phase('life_roll_interrupt_check', 10.0)

    def _phase_life_roll_interrupt_check(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed > 0.8:
                raise BehaviorFailure(
                    'LMB after interrupted Roll started no neutral action')
            return
        self._check(name != 'RollStepSlash',
                    'interrupted Roll does not leave a stale RollStepSlash recovery route')
        self._record('roll_lifecycle', case='interrupted_light', move=name,
                     montage=self._montage_name())
        self.pawn.interrupt_move()
        self._phase('life_air_prepare', 20.0)

    def _phase_life_air_prepare(self, elapsed):
        self._start_level_prep('life_air_start')

    def _phase_life_air_start(self, elapsed):
        if not self._idle():
            return
        self._check(self._level() >= 1,
                    'white or better is available before the interrupted helm')
        self._reset_fixture(150.0)
        self._set_control_yaw(0.0)
        self._place_target(150.0)
        self._stop_inputs()
        self.life_air = {'level': self._level(), 'hp': self._hp(),
                         'seen': [], 'last': None,
                         'interrupt_requested': False, 'z': float(
                             self.pawn.get_actor_location().z),
                         'interrupt_hp': None, 'interrupt_level': None}
        self._press('helm')
        self._phase('life_air_watch', 30.0)

    def _phase_life_air_watch(self, elapsed):
        name = self._current()
        state = self.life_air
        if name != state['last']:
            state['last'] = name
            if name != 'None':
                state['seen'].append(name)
        if name == 'SpiritThrust':
            self._place_target(150.0)
        if name == 'SpiritHelmBreaker' and not state['interrupt_requested']:
            raise BehaviorFailure('helm Air entered strike without input before interrupt')
        if name == 'HelmAir' and not state['interrupt_requested']:
            position = self._position()
            mode = self._mode_name()
            z = float(self.pawn.get_actor_location().z)
            # SpiritThrust already dealt its source attack damage before Rise; baseline the
            # post-interrupt no-further-damage assertion here, not before G.
            state['interrupt_hp'] = self._hp()
            state['interrupt_level'] = self._level()
            self._place_target(150.0)
            self.pawn.interrupt_move()
            state['interrupt_requested'] = True
            self._record('helm_interrupt', move=name,
                         position=round(position, 3), mode=mode,
                         z=round(z, 2), level=state['interrupt_level'],
                         hp=round(state['interrupt_hp'], 2))
            return
        if state['interrupt_requested'] and self._idle():
            self._phase('life_air_settle', 12.0)
            return
        if name == 'None':
            if not state['seen']:
                if elapsed < 0.5:
                    return
                raise BehaviorFailure('interrupted helm never started SpiritThrust')
            if not state['interrupt_requested']:
                raise BehaviorFailure('helm chain finished before HelmAir could be interrupted')

    def _phase_life_air_settle(self, elapsed):
        if not self._idle():
            return
        if elapsed < 0.6:
            return
        self._check(not self._is_flying(),
                    'interrupting HelmAir restores a non-flying movement mode')
        self._check(self.life_air['interrupt_hp'] is not None,
                    'the interrupted helm actually reached HelmAir')
        self._check(abs(self._hp() - self.life_air['interrupt_hp']) < 0.01,
                    'interrupted helm awards no HelmLand damage after the interrupt')
        self._check(self._level() <= self.life_air['interrupt_level'],
                    'interrupted helm does not add a spirit color')
        self._record('helm_interrupt_settle', mode=self._mode_name(),
                     z=round(float(self.pawn.get_actor_location().z), 2),
                     level=self._level(), hp=round(self._hp(), 2))
        self._phase('life_buffer_start', 10.0)

    def _phase_life_buffer_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._stop_inputs()
        self.late_buffer = {'case': 'after_window', 'submitted': False}
        self._press('thrust')
        self._phase('life_buffer_seek', 10.0)

    def _phase_life_buffer_seek(self, elapsed):
        name = self._current()
        if name == 'None' and elapsed < 1.0:
            return
        self._check(name == 'Thrust', 'buffer boundary fixture starts the formal Thrust')
        if self._position() < 0.08:
            return
        montage = self.anim.get_current_active_montage()
        definition = self._def('Thrust')
        # Seeking is a runtime-only fixture: do not alter the formal cancel window.
        if self.late_buffer['case'] == 'after_window':
            position = self._length() - 0.005
            self._check(position > self._cancel_window(definition, 'light')[1],
                        'late input fixture is genuinely after the saved cancel end')
        else:
            position = self._cancel_start(definition, 'light') + 0.005
        self.anim.montage_set_position(montage, position)
        self._check(self.pawn.request_input(unreal.MHWIInput.LIGHT),
                    'native buffering accepts the request for later route resolution')
        self._record('buffer_boundary', case=self.late_buffer['case'], position=position)
        self._phase('life_buffer_watch', 8.0)

    def _phase_life_buffer_watch(self, elapsed):
        name = self._current()
        if self.late_buffer['case'] == 'after_window':
            self._check(name in ('Thrust', 'None'),
                        'a late request cannot reopen a historical cancel window at montage end')
            if name != 'None':
                return
            self.late_buffer = {'case': 'inside_window', 'submitted': False}
            self._press('thrust')
            self._phase('life_buffer_seek', 10.0)
        elif name == 'RisingSlash':
            self._check(True, 'an input in the real cancel window still chains to RisingSlash')
            self.pawn.interrupt_move()
            self._phase('life_death_start', 10.0)
        elif name == 'None':
            raise BehaviorFailure('an inside-window buffered input failed to chain')

    def _phase_life_death_start(self, elapsed):
        if not self._idle():
            return
        self._reset_fixture(150.0)
        self._stop_inputs()
        self._press('light')
        self._phase('life_death_wait', 10.0)

    def _phase_life_death_wait(self, elapsed):
        name = self._current()
        if name == 'None':
            if elapsed < 0.3:
                return
            raise BehaviorFailure('death fixture did not start a normal attack')
        if self._position() < 0.1:
            return
        attributes = self.pawn.get_editor_property('attributes')
        attributes.apply_damage(1000.0, self.target)
        self._check(not attributes.is_alive,
                    'lethal incoming damage kills the hunter')
        self._check(self._idle(), 'death releases the foreground action')
        self._check(not self.pawn.request_input(unreal.MHWIInput.LIGHT),
                    'death rejects further combat input')
        self._check(not self._is_flying(),
                    'death restores a non-flying movement mode')
        self._record('death', move='OverheadSlash', mode=self._mode_name())
        self._phase('life_done', 6.0)

    def _phase_life_done(self, elapsed):
        self._suite_done()

    # __SUITE_PHASES__


def run(suite='all'):
    """Start one real PIE suite (or all suites) and return its report path."""
    global _ACTIVE
    if unreal is None:
        raise RuntimeError(
            'pie_behavior_corrections.run requires the Unreal Python environment')
    value = str(suite or 'all').strip().lower()
    if value not in ('all',) + SUITES:
        raise ValueError('suite must be one of all/%s' % ('/'.join(SUITES),))
    if _ACTIVE is not None and not _ACTIVE.done:
        raise RuntimeError('a behavior PIE run is already active; wait for its report')
    runner = BehaviorRunner(value)
    _ACTIVE = runner
    try:
        runner.prepare_editor()
        runner.handle = unreal.register_slate_post_tick_callback(runner.tick)
    except Exception:
        runner._finish(traceback.format_exc())
        raise
    return {'started': True, 'suite': value, 'report': str(runner.report_file)}
