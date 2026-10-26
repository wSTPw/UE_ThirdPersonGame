"""Short B02 production-actor smoke; no long suites or asset writes."""
import time
import unreal
import native_spirit_branches as native
import pie_behavior_corrections as base

_ACTIVE = None


class BranchSmoke(base.BehaviorRunner):
    def __init__(self):
        super().__init__('ground')
        self.suites = ['b02']
        self.requested = 'B02-short-smoke'
        self.report_file = native.OUT / 'PIE-short-smoke.json'
        self.report['suite'] = self.requested
        self.report['notes'] = ['Only original weak/strong values and semantic route identities.',
                                'No original cancel-frame, connector or complex terrain claims.']
        self.cases = [
            dict(move='SpiritStepSlash', gauge=0., cost=0., damage=18., end=10.),
            dict(move='SpiritStepSlash', gauge=10., cost=0., damage=18., end=20.),
            dict(move='SpiritStepSlash', gauge=20., cost=20., damage=28., end=10.),
            dict(move='SpiritStepSlash', command='light', target='SpiritComboRisingSlash', far=True),
            dict(move='SpiritStepSlash', command='thrust', target='SpiritComboRisingSlash', far=True),
            dict(move='SpiritComboThrust', command='thrust', negative=True, far=True),
            dict(move='SpiritComboRisingSlash', command='spirit', target='SpiritI', clear=True, far=True, target_cost=0.),
            dict(move='SpiritStepSlash', gauge=0., cost=0., damage=18., end=10.),
            dict(move='SpiritStepSlash', gauge=10., cost=0., damage=18., end=20.),
            dict(move='SpiritComboRisingSlash', command='spirit', target='SpiritIII', gauge=20., far=True, target_cost=20.),
        ]
        self.index = 0

    def _begin_suite(self, name):
        self.current_suite = name
        self.suite_started = time.monotonic()
        self._require_drawn('b02_start')

    def _phase_b02_start(self, elapsed):
        if not self._idle():return
        if self.index == len(self.cases):
            self._suite_done()
            return
        case = self.cases[self.index]
        self._reset_fixture(3000. if case.get('far') else 150.)
        if case.get('clear'):
            self._check(self.pawn.start_move('ForesightSlash'), 'production action clears resource fixture')
            self.pawn.interrupt_move()
        gauge = self._gauge()
        if 'gauge' in case:self._check(abs(gauge-case['gauge'])<.01, 'source resource boundary '+str(case['gauge']))
        self.target_attrs.set_health(self.target_attrs.get_max_health())
        self.observe = dict(hp=self._hp(),gauge=gauge,pressed=False)
        self._check(self.pawn.start_move(case['move']), 'production move starts '+case['move'])
        if 'cost' in case:self._check(abs(gauge-self._gauge()-case['cost'])<.01,'source weak/strong spend')
        self._phase('b02_watch',8.)

    def _done_case(self, **extra):
        case = self.cases[self.index]
        self._record('cases',index=self.index,move=case['move'],target=case.get('target'),**extra)
        self.index += 1
        self._phase('b02_start',8.)

    def _phase_b02_watch(self, elapsed):
        case, state = self.cases[self.index], self.observe
        self._place_target(3000. if case.get('far') else 150.)
        name = self._current()
        if case.get('target') and name == case['target']:
            self._check(state['pressed'],'route command was delivered')
            if 'target_cost' in case:
                self._check(abs(state['route_gauge']-self._gauge()-case['target_cost'])<.01,'ordered branch spends the selected target cost')
            self.pawn.interrupt_move()
            self._done_case(selected=name)
            return
        self._check(name in ['None',case['move']], 'no unrequested/invented continuation')
        if name != 'None':
            if case.get('command') and not state['pressed']:
                # The removed B route has no window: use its retained A window
                # only as an injection location for the negative input test.
                query = 'light' if case.get('negative') else case['command']
                if self._cancel_ready(self._def(name),query):
                    state['route_gauge'] = self._gauge()
                    self._press(case['command'])
                    state['pressed'] = True
            return
        if case.get('target'):
            self._check(False,'required continuation did not start')
        if case.get('negative'):
            self._check(state['pressed'],'removed B route was actually attempted')
        if 'damage' in case:
            self._check(abs(state['hp']-self._hp()-case['damage'])<.02,'actual original weak/strong hit value')
            self._check(abs(self._gauge()-case['end'])<.01,'actual source gain/cost result')
        self._done_case(damage=state['hp']-self._hp(),gauge=self._gauge())


def run():
    global _ACTIVE
    if _ACTIVE is not None and not _ACTIVE.done:raise RuntimeError('B02 smoke already running')
    _ACTIVE = BranchSmoke()
    _ACTIVE.prepare_editor()
    _ACTIVE.handle = unreal.register_slate_post_tick_callback(_ACTIVE.tick)
    return str(_ACTIVE.report_file)
