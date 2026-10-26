"""B03 short real-input smoke; leaves full movement/pose comparison for later."""
import math
import time
import unreal
import author_locomotion_fidelity as author
import pie_behavior_corrections as base

_ACTIVE = None


class LoopSmoke(base.BehaviorRunner):
    def __init__(self):
        super().__init__('ground')
        self.suites = ['b03']
        self.report_file = author.OUT / 'PIE-short-smoke.json'
        self.report['notes'] = ['Runtime movement/finite-pose smoke only; original velocity, foot sliding and transition timing not qualified.']
        self.index = 0
        self.cases = [(True, 'idle'), (True, 'walk'), (True, 'run'), (False, 'idle'), (False, 'walk')]

    def _begin_suite(self, name):
        self.current_suite = name
        self.suite_started = time.monotonic()
        self._phase('loop_prepare', 10.)

    def _phase_loop_prepare(self, elapsed):
        self._stop_inputs()
        if self.index == len(self.cases):
            self._suite_done()
            return
        sheathed, kind = self.cases[self.index]
        if sheathed: self._require_sheathed('loop_start')
        else: self._require_drawn('loop_start')

    def _phase_loop_start(self, elapsed):
        sheathed, kind = self.cases[self.index]
        self._reset_fixture(3000.)
        self.begin_location = self.pawn.get_actor_location()
        self._move(0., 0. if kind == 'idle' else 1.)
        self.held_sprint = (1., 0., 0.) if kind == 'run' else (0., 0., 0.)
        self.sprint_release_pending = kind != 'run'
        self._phase('loop_watch', 5.)

    def _phase_loop_watch(self, elapsed):
        if elapsed < 1.2: return
        sheathed, kind = self.cases[self.index]
        self._check(self._idle(), 'no unexpected action during '+kind)
        self._check(self.pawn.is_sheathed() == sheathed, 'stance preserved during '+kind)
        velocity = self.pawn.get_velocity()
        speed = math.hypot(velocity.x, velocity.y)
        expected = 0. if kind == 'idle' else self.data.get_editor_property('run_speed' if kind == 'run' else 'walk_speed')
        self._check(abs(speed-expected) < 2., 'existing CharacterMovement speed preserved '+kind)
        self._check(abs(self.pawn.get_actor_location().z-self.begin_location.z) < 2., 'locked loop causes no vertical root drift')
        for bone in ('bone_003', 'bone_008', 'bone_012'):
            p = self.pawn.mesh.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT).translation
            self._check(all(math.isfinite(v) for v in (p.x,p.y,p.z)), 'finite evaluated pose '+bone)
        self._record('movement', sheathed=sheathed, kind=kind, speed=speed, expected=expected)
        self._stop_inputs()
        self.index += 1
        self._phase('loop_prepare', 10.)


def run():
    global _ACTIVE
    if _ACTIVE and not _ACTIVE.done: raise RuntimeError('B03 smoke already running')
    _ACTIVE = LoopSmoke()
    _ACTIVE.prepare_editor()
    _ACTIVE.handle = unreal.register_slate_post_tick_callback(_ACTIVE.tick)
    return str(_ACTIVE.report_file)
