"""B01 real PIE: independent original-value expectations, production DA/CPP.

Fixtures move a passive target into reach; this checks scalar/route consumers,
not original blade geometry, shell timing, native cancel frames or full damage.
No asset saves or production debug setters. Import is inert.
"""
from pathlib import Path
import time

import unreal
import native_reference_basics as native
import pie_behavior_corrections as base

_ACTIVE = None
# Independent golden expectations, cross-checked against the original binary
# parser before PIE starts; never generated from the DataAsset under test.
GOLDEN = {
    'StepSlash': ([24.], [26.]), 'DrawSlash': ([24.], [26.]),
    'RollStepSlash': ([24.], [26.]), 'OverheadSlash': ([21.], [23.]),
    'Thrust': ([12.], [12.]), 'SpiritComboThrust': ([12.], [12.]),
    'RisingSlash': ([18.], [12.]), 'SpiritComboRisingSlash': ([18.], [12.]),
    'FadeSlash': ([22.], [26.]), 'FadeSlashLeft': ([22.], [26.]),
    'FadeSlashRight': ([22.], [26.]), 'SpiritIII': ([14., 19., 34.], [0., 0., 0.]),
    'IaiSlash': ([18., 13.], [0., 0.]), 'SpiritThrust': ([26.], [10.]),
}


class ReferenceRunner(base.BehaviorRunner):
    def __init__(self, scope='full'):
        super().__init__('ground')
        self.requested = 'B01-reference-basics'
        self.suites = ['native']
        self.report_file = native.OUT / 'PIE-reference-basics.json'
        self.report['suite'] = self.requested
        self.report['suites_run'] = self.suites
        self.report['notes'] += ['B01 golden values come from original COL/W03P/FSM, not the DA.',
                                 'Target-follow fixture isolates scalar/route consumers; geometry/timing fidelity remains open.']
        self.source = native.build_plan()
        self.report['source_fingerprints'] = self.source['sources']
        for name, (damage, gain) in GOLDEN.items():
            rows = self.source['attacks'][name]
            if [r['damage'] for r in rows] != damage or [r['spirit_gain'] for r in rows] != gain:
                raise RuntimeError('Golden fixture disagrees with original binary: ' + name)
        self.cases = [dict(move=name, damage=sum(GOLDEN[name][0]), gain=sum(GOLDEN[name][1]))
                      for name in ['StepSlash', 'OverheadSlash', 'Thrust', 'RisingSlash',
                                   'SpiritComboThrust', 'SpiritComboRisingSlash', 'SpiritIII',
                                   'FadeSlash', 'FadeSlashLeft', 'FadeSlashRight', 'RollStepSlash']]
        self.cases += [dict(move='Thrust', damage=12., gain=12., negative=True),
                       dict(move='Thrust', route='RisingSlash', damage=30., gain=24.),
                       *[dict(move=m, route='Thrust', damage=34., gain=38.)
                         for m in ['FadeSlash', 'FadeSlashLeft', 'FadeSlashRight']],
                       dict(move='ForesightSlash', route='StepSlash', damage=50., gain=36.),
                       dict(move='IaiSpiritSlash', damage=17., gain=None, counter=True),
                       dict(move='IaiSlash', damage=31., gain=None)]
        self.case_index = 0
        self.color = 1
        self.scope = scope
        if scope == 'step':
            self.cases = [dict(move='SpiritStepSlash', damage=28., gain=10.)]
            self.report_file = native.OUT / 'PIE-reference-basics-step.json'

    def _begin_suite(self, name):
        self.current_suite = name
        self.suite_started = time.monotonic()
        self._suite_entry(name)['started'] = round(self.suite_started - self.started, 3)
        self._reset_fixture(150.)
        self._phase('native_assets', 30.)

    def _phase_native_assets(self, elapsed):
        for name, (damages, gains) in GOLDEN.items():
            windows = list(self._def(name).get_editor_property('damage_windows'))
            self._check([float(w.get_editor_property('damage')) for w in windows] == damages,
                        name + ' saved per-hit bases equal independent original COL')
            self._check([float(w.get_editor_property('spirit_gain')) for w in windows] == gains,
                        name + ' saved gains equal independent original COL')
        self._check(abs(self._cost('SpiritStepSlash') - 20.) < 1e-5,
                    'SpiritStepSlash original 0.20 cost is twenty gauge')
        self._check(self._find_route(self._def('Thrust'), 'thrust') is None,
                    'ordinary Thrust has no invented B continuation')
        self._require_drawn('native_border_zero' if self.scope == 'step' else 'native_start')

    def _phase_native_border_zero(self, elapsed):
        if not self._idle():
            return
        # Reach exact resource boundaries through production actions, without
        # a private-field setter or changing any cost/gain in the DataAsset.
        self._check(self.pawn.start_move('ForesightSlash'), 'production Foresight can clear the boundary fixture gauge')
        self.pawn.interrupt_move()
        self._check(abs(self._gauge()) < .001, 'boundary fixture begins at zero gauge')
        self._place_target(150.)
        self._check(self.pawn.start_move('OverheadSlash'), 'boundary fixture builds original twenty-three gauge')
        self._phase('native_border_overhead', 10.)

    def _phase_native_border_overhead(self, elapsed):
        self._place_target(150.)
        if not self._idle():
            return
        self._check(abs(self._gauge() - 23.) < .001, 'original Overhead gain is exactly twenty-three')
        self._check(self.pawn.start_move('SpiritI'), 'boundary fixture spends original fifteen gauge')
        self.pawn.interrupt_move()
        self._check(abs(self._gauge() - 8.) < .001, 'interrupted pre-hit SpiritI leaves exactly eight gauge')
        self._check(self.pawn.start_move('SpiritStepSlash'), 'SpiritStepSlash permits the original low-gauge weak branch')
        self._check(abs(self._gauge() - 8.) < .001, 'weak SpiritStepSlash spends no unavailable gauge')
        self.pawn.interrupt_move()
        self._check(self.pawn.start_move('Thrust'), 'original Thrust builds the exact cost boundary')
        self._phase('native_border_thrust', 10.)

    def _phase_native_border_thrust(self, elapsed):
        self._place_target(150.)
        if not self._idle():
            return
        self._check(abs(self._gauge() - 20.) < .001, 'original Thrust reaches exactly twenty gauge')
        self._phase('native_start', 10.)

    def _phase_native_start(self, elapsed):
        if not self._idle():
            return
        if self.case_index >= len(self.cases):
            if self.scope == 'step':
                self._suite_done()
            else:
                self._phase('native_color_prepare', 120.)
            return
        case = self.cases[self.case_index]
        if self._gauge() < self._cost(case['move']):
            self._start_gauge(self._cost(case['move']), 'native_start')
            return
        self._reset_fixture(150.)
        self.target_attrs.set_health(self.target_attrs.get_max_health())
        self.observe = dict(case=case, hp=self._hp(), seen=[case['move']], pressed=False,
                            start_gauge=self._gauge(), input_rejected=False)
        self._check(self.pawn.start_move(case['move']), 'real Montage starts ' + case['move'])
        self.observe['gauge_after_start'] = self._gauge()
        if case['move'] == 'SpiritStepSlash':
            self._check(abs(self.observe['start_gauge'] - self._gauge() - 20.) < .001,
                        'SpiritStepSlash actually spends twenty gauge at startup')
        if case.get('counter'):
            self.pawn.get_editor_property('attributes').apply_damage(1., self.target)
            self._check(self.pawn.has_counter_confirmed(), 'Iai first-hit fixture confirms counter without losing color')
        self._phase('native_watch', 30.)

    def _phase_native_watch(self, elapsed):
        self._place_target(150.)
        state = self.observe
        case, name = state['case'], self._current()
        if name != 'None' and name != state['seen'][-1]:
            state['seen'].append(name)
        if name == case['move'] and not state['pressed'] and (case.get('route') or case.get('negative')):
            if self._cancel_ready(self._def(name), 'light'):
                self._press('thrust' if case.get('negative') else 'light')
                state['pressed'] = True
        if name != 'None':
            return
        expected_moves = [case['move']] + ([case['route']] if case.get('route') else [])
        self._check(state['seen'] == expected_moves,
                    'original route identities ' + str(expected_moves))
        if case.get('route') or case.get('negative'):
            self._check(state['pressed'], 'route positive/negative input was actually delivered')
        damage = state['hp'] - self._hp()
        if case['damage'] is not None:
            self._check(abs(damage - case['damage']) < .1,
                        '%s actual damage %.3f equals independent base %.3f' % (case['move'], damage, case['damage']))
        else:
            self._check(damage > 0., 'gain-only fixture actually hits; conditional MV remains unqualified')
        if case['gain'] is not None:
            expected_gauge = min(100., state['gauge_after_start'] + case['gain'])
            self._check(abs(self._gauge() - expected_gauge) < .1,
                        case['move'] + ' actual gauge follows original per-hit gains')
        self._record('native_cases', move=case['move'], route=case.get('route'), negative=case.get('negative', False),
                     damage=damage, expected=case['damage'], seen=state['seen'])
        self.case_index += 1
        self._phase('native_start', 30.)

    def _phase_native_color_prepare(self, elapsed):
        if self.color > 3:
            self._suite_done()
            return
        if not self._idle():
            return
        if self.pawn.is_sheathed():
            self._require_drawn('native_color_prepare', 120.)
            return
        if self._level() < self.color:
            stock = self._spirit_chain_stock()
            if self._gauge() < stock:
                self._start_gauge(stock, 'native_color_prepare', 120.)
            else:
                self._start_spirit_plan('native_color_prepare', 120.)
            return
        self._check(self._level() == self.color, 'color fixture reached requested color through real spirit combo')
        self._reset_fixture(150.)
        self.target_attrs.set_health(self.target_attrs.get_max_health())
        self.color_hp = self._hp()
        self._check(self.pawn.start_move('IaiSpiritSlash'), 'colored Iai first-hit Montage starts')
        self.pawn.get_editor_property('attributes').apply_damage(1., self.target)
        self._check(self.pawn.has_counter_confirmed(), 'colored Iai counter preserves fixture level')
        self._phase('native_color_iai', 15.)

    def _phase_native_color_iai(self, elapsed):
        self._place_target(150.)
        if not self._idle():
            return
        multiplier = [1., 1.05, 1.1, 1.2][self.color]
        expected = [17., 19., 31., 39.][self.color] * multiplier
        damage = self.color_hp - self._hp()
        self._check(abs(damage - expected) < .1, 'colored Iai actually consumes captured original first-hit base')
        self._check(self._level() == self.color, 'successful Iai preserves current World color')
        self._record('native_iai_color', color=self.color, damage=damage, expected=expected)
        self._reset_fixture(150.)
        self.target_attrs.set_health(self.target_attrs.get_max_health())
        self.helm_observe = dict(hp=self._hp(), seen=['SpiritThrust'], pressed=False)
        self._check(self.pawn.start_move('SpiritThrust'), 'colored helm begins from real hit-confirmed thrust')
        self._phase('native_color_helm', 25.)

    def _phase_native_color_helm(self, elapsed):
        self._place_target(150.)
        state, name = self.helm_observe, self._current()
        if name != 'None' and name != state['seen'][-1]:
            state['seen'].append(name)
        if name == 'HelmAir' and not state['pressed']:
            self._press('light')
            state['pressed'] = True
        if name != 'None':
            return
        self._check(state['pressed'], 'actual aerial input committed helm strike')
        self._check(all(m in state['seen'] for m in base.HELM_MOVES), 'colored helm traversed all real physical stages')
        multiplier = [1., 1.05, 1.1, 1.2][self.color]
        expected = (26. + 7. * [0., 10., 15., 25.][self.color]) * multiplier
        damage = state['hp'] - self._hp()
        self._check(abs(damage - expected) < .2, 'real thrust plus seven colored helm hits match independent source bases')
        self._check(self._level() == self.color - 1, 'committed helm consumes exactly one aura level')
        self._record('native_helm_color', color=self.color, damage=damage, expected=expected, seen=state['seen'])
        self.color += 1
        self._phase('native_color_prepare', 120.)


def run(scope='full'):
    global _ACTIVE
    if _ACTIVE is not None and not _ACTIVE.done:
        raise RuntimeError('B01 PIE already running')
    _ACTIVE = ReferenceRunner(scope)
    _ACTIVE.prepare_editor()
    _ACTIVE.handle = unreal.register_slate_post_tick_callback(_ACTIVE.tick)
    return str(_ACTIVE.report_file)
