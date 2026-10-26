"""Real PIE defence/resource/route regression for public-frame-table calibration.

Import is inert. ``run('defense'|'resources'|'routes'|'all')`` is asynchronous.
The parent orchestrator must run this alone: it owns PIE while active. No asset
is saved. Every tested definition is read from the formal DA. Only preparation
uses a transient DA: Draw.SpiritGainOnStart seeds an exact gauge, and an ordinary
OverheadSlash hit may raise a colour. These are explicitly labelled fixtures,
never presented as normal gameplay progression or written into private state.

Exact defence endpoints are tested on paused real montages via ApplyDamage in
one callback. Actor clocks/regen/armour are tested using actual world time.
These tests verify the published-table adapter, not a running original game.
"""
from pathlib import Path
import time
import traceback

try:
    import unreal
except ImportError:
    unreal = None

import pie_behavior_corrections as behavior

_ACTIVE = None
SUITES = ('defense', 'resources', 'routes')
FRAME = 1.0 / 60.0
EPS = .00002
KEYS = {str(getattr(unreal.MHWIInput, enum)): semantic
        for semantic, enum in behavior.INPUT_ENUM.items()} if unreal else {}


class CombatFidelityRunner(behavior.BehaviorRunner):
    def __init__(self, suite, route_limit=None):
        super().__init__('ground')
        self.requested = suite
        self.suites = list(SUITES) if suite == 'all' else [suite]
        self.route_limit = route_limit
        self.report_file = Path(unreal.Paths.project_saved_dir()) / (
            'MHWIImport/PIE-combat-fidelity-' + suite + '.json')
        self.report.update(suite=suite, suites_run=self.suites,
                           route_limit=route_limit)
        self.report['notes'] = [
            'Runtime-only fixtures; no asset saves or private-field writes.',
            'Transient Draw SpiritGainOnStart prepares exact gauge. Temporary '
            'OverheadSlash RaiseSpiritOnHit prepares colour through a real hit; '
            'the formal DA is restored before each tested move.',
            'Actual Enhanced Input enters defence moves. Endpoint probes use '
            'paused real Montage position plus UAttributeComponent.ApplyDamage.',
            'Defence windows are half-open. Route cancel windows remain inclusive.',
            'Published table values are tested as the project adapter contract; '
            'no original-game execution or universal cancel-frame fidelity is claimed.',
        ]
        self.task = None
        self.fixture_data = None
        self.deadline = 0.0

    def _begin_suite(self, name):
        self.current_suite = name
        self.suite_started = time.monotonic()
        self._suite_entry()
        self.task = getattr(self, '_suite_' + name)()
        self._phase('scenario', 900.0)

    def _phase_scenario(self, elapsed):
        try:
            next(self.task)
        except StopIteration:
            self._suite_done()

    def _tick_impl(self, delta):
        # Do not inherit the short behaviour suite deadlines: enumerating every
        # authored input route legitimately takes longer than a direction test.
        if self.done:
            return
        if time.monotonic() - self.started > 1800.0:
            self._finish('combat fidelity overall timeout')
            return
        try:
            handler = getattr(self, '_phase_' + self.phase)
            handler(time.monotonic() - self.phase_started)
            if not self.done:
                self._pump_held_inputs()
        except Exception:
            self._finish(traceback.format_exc())

    def _wait(self, predicate, label, seconds=8.0):
        end = time.monotonic() + seconds
        while not predicate():
            if time.monotonic() > end:
                raise behavior.BehaviorFailure('timeout: ' + label)
            yield

    def _wait_world(self, seconds):
        end = self._seconds() + float(seconds)
        yield from self._wait(lambda: self._seconds() >= end,
                              'world seconds %.3f' % seconds, seconds * 4 + 10)

    def _seconds(self):
        return float(unreal.GameplayStatics.get_time_seconds(self.world))

    def _player_hp(self):
        return float(self.pawn.get_editor_property('attributes').get_current_health())

    def _seek(self, seconds):
        montage = self.anim.get_current_active_montage()
        self._check(montage is not None, 'active montage exists for endpoint probe')
        self.anim.montage_pause(montage)
        self.anim.montage_set_position(montage, float(seconds))
        actual = float(self.anim.montage_get_position(montage))
        self._check(abs(actual - seconds) < .00001,
                    'real montage reached source second %.7f' % seconds)
        return montage

    def _fresh(self, gauge=50.0, level=0):
        old = self.pawn
        old.interrupt_move()
        self._flush_zero_inputs()
        old.set_actor_enable_collision(False)
        transform = unreal.Transform(location=unreal.Vector(0., 0., 94.15))
        # The deferred GameplayStatics spawn wrappers are BlueprintInternalUseOnly
        # and are not in this UE Python surface. The live GameMode's public native
        # event spawns its configured DefaultPawnClass in the actual PIE world.
        game_mode = unreal.GameplayStatics.get_game_mode(self.world)
        self._check(game_mode is not None, 'runtime training GameMode exists')
        pawn = game_mode.spawn_default_pawn_at_transform(self.pc, transform)
        self._check(pawn is not None, 'fresh runtime pawn can be spawned')
        self.pc.possess(pawn)
        old.destroy_actor()
        yield
        yield from self._wait(self._setup_world, 'fresh pawn input setup', 8.0)
        self._reset_fixture(3000.)
        for target in unreal.GameplayStatics.get_all_actors_of_class(
                self.world, unreal.MHWITrainingTarget):
            target.set_actor_location(unreal.Vector(3000., 3000., 90.), False, True)
        for _ in range(int(level)):
            yield from self._prepare_colour()
        self._seed_gauge(gauge)
        self._check(self.data.get_path_name().split('.')[0] == behavior.FORMAL_DATA,
                    'formal DA restored before tested actions')
        self._check(abs(self._gauge() - gauge) < .002,
                    'fixture prepared exact gauge %.4f' % gauge)
        self._check(self._level() == level, 'fixture prepared colour %d' % level)

    def _temporary(self, name, **properties):
        # PythonScriptPlugin exposes new_object, not a generic UObject duplicate
        # helper. Copy public fields into a transient class instance explicitly.
        data = unreal.new_object(unreal.MHWIMovesetData)
        for key in ('weapon_motions', 'idle', 'walk', 'run', 'sheathed_idle',
                    'sheathed_walk', 'sheathed_run', 'special_sheathed_idle',
                    'walk_speed', 'run_speed', 'base_damage_multiplier',
                    'input_buffer_seconds', 'special_sheath_hold_seconds',
                    'gauge_regen_per_second', 'spirit_decay_pause_on_raise_seconds',
                    'counter_armor_damage_multiplier', 'helm_air_vertical_speed',
                    'helm_air_forward_speed', 'helm_air_gravity', 'helm_strike_speed',
                    'helm_strike_start_time', 'spirit_level_durations'):
            data.set_editor_property(key, self.data.get_editor_property(key))
        # Do not mutate the live formal Map view or nested USTRUCT references.
        moves = {key: value.copy() for key, value in
                 self.data.get_editor_property('moves').items()}
        definition = moves[unreal.Name(name)].copy()
        for key, value in properties.items():
            definition.set_editor_property(key, value)
        moves[unreal.Name(name)] = definition
        data.set_editor_property('moves', moves)
        self.fixture_data = data  # Strong reference until the preparation ends.
        self.pawn.set_editor_property('moveset', data)

    def _restore_formal(self):
        self.pawn.set_editor_property('moveset', self.data)
        self.fixture_data = None

    def _seed_gauge(self, desired):
        self.pawn.interrupt_move()
        # Draw always has zero authored cost. It immediately applies its public
        # gain-on-start, so no tick/pose or target hit is required to seed state.
        self._temporary('Draw', spirit_gain_on_start=float(desired) - self._gauge())
        try:
            self._check(self.pawn.start_move('Draw'), 'transient gauge preparation Draw starts')
            self.pawn.interrupt_move()
        finally:
            self._restore_formal()
        self._record('fixtures', action='Draw.SpiritGainOnStart', gauge=self._gauge())

    def _prepare_colour(self):
        before = self._level()
        self._temporary('OverheadSlash', raise_spirit_on_hit=True)
        try:
            self._place_target(150.)
            self.target.reset_target()
            self._check(self.pawn.start_move('OverheadSlash'),
                        'transient colour preparation real OverheadSlash starts')
            end = time.monotonic() + 8.
            while self._level() == before:
                self._place_target(150.)
                if time.monotonic() > end:
                    raise behavior.BehaviorFailure('colour preparation did not hit')
                yield
            self._check(self._hp() < self.target_attrs.get_max_health(),
                        'colour preparation was a real target hit')
            self.pawn.interrupt_move()
        finally:
            self._restore_formal()
            self._place_target(3000.)
        self._record('fixtures', action='OverheadSlash.RaiseSpiritOnHit', level=self._level())

    def _enter_defense(self, move):
        # Enter through runtime Enhanced Input and the formal route window.
        self._press('light')
        yield from self._wait(lambda: self._current() == 'OverheadSlash',
                              'LMB starts OverheadSlash')
        definition = self._def('OverheadSlash')
        semantic = 'foresight' if move == 'ForesightSlash' else 'special'
        route = self._find_route(definition, semantic)
        start = float(definition.get_editor_property('cancel_start'))
        if route is not None:
            override = float(route.get_editor_property('cancel_start'))
            if override >= 0:
                start = override
        self._seek(start + .02)
        yield
        self._press(semantic)
        next_move = 'ForesightSlash' if move == 'ForesightSlash' else 'SpecialSheathe'
        yield from self._wait(lambda: self._current() == next_move, next_move + ' input')
        if next_move == 'SpecialSheathe':
            special = self._def('SpecialSheathe')
            self._seek(float(special.get_editor_property('special_sheath_hold_time')))
            yield
            self._press('light' if move == 'IaiSlash' else 'spirit')
            yield from self._wait(lambda: self._current() == move, move + ' input')
        self._check(self._current() == move, 'real Enhanced Input entered ' + move)

    def _probe_damage(self, label, position, immune, counter, damage=10.):
        self._seek(position)
        before = self._player_hp()
        move = self._current()
        self.pawn.get_editor_property('attributes').apply_damage(damage, self.target)
        actual = before - self._player_hp()
        self._check(abs(actual - (0. if immune else damage)) < .001,
                    '%s HP loss %.3f' % (label, actual))
        self._check(bool(self.pawn.has_counter_confirmed()) == counter,
                    label + ': counter confirmation matches independent window')
        self._check(self._current() == move if immune else self._idle(),
                    label + ': action survives iff avoidance consumed the damage')
        self._record('damage_probes', label=label, seconds=position,
                     loss=actual, counter=bool(self.pawn.has_counter_confirmed()),
                     armor=float(self.pawn.get_counter_armor_remaining()))

    def _suite_defense(self):
        cases = [
            ('ForesightSlash', 50., 0, 0., True, True),
            ('ForesightSlash', 50., 0, 33*FRAME-EPS, True, True),
            ('ForesightSlash', 50., 0, 33*FRAME, True, False),
            ('ForesightSlash', 50., 0, 45*FRAME-EPS, True, False),
            ('ForesightSlash', 50., 0, 45*FRAME, False, False),
            ('ForesightSlash', 9.99, 0, 0., True, False),
            ('ForesightSlash', 10., 0, 0., True, True),
            ('ForesightSlash', 0., 0, 13*FRAME-EPS, True, False),
            ('ForesightSlash', 0., 0, 13*FRAME, False, False),
            ('IaiSlash', 50., 0, 5*FRAME-EPS, True, True),
            ('IaiSlash', 50., 0, 5*FRAME, False, False),
            ('IaiSpiritSlash', 50., 0, 12*FRAME-EPS, True, True),
            ('IaiSpiritSlash', 50., 0, 12*FRAME, False, False),
            ('IaiSpiritSlash', 50., 1, 12*FRAME-EPS, True, True),
            ('IaiSpiritSlash', 50., 1, 12*FRAME, True, False),
            ('IaiSpiritSlash', 50., 1, 14*FRAME-EPS, True, False),
            ('IaiSpiritSlash', 50., 1, 14*FRAME, False, False),
        ]
        for move, gauge, level, position, immune, counter in cases:
            yield from self._fresh(gauge, level)
            yield from self._enter_defense(move)
            self._check(abs(self.pawn.get_spirit_gauge_at_move_start()-gauge) < .003,
                        'move-start gauge snapshot is captured before consuming gauge')
            label = '%s gauge%.2f level%d frame%.5f' % (move, gauge, level, position/FRAME)
            self._probe_damage(label, position, immune, counter)
        for move, duration in [('ForesightSlash', 1.), ('IaiSlash', 2.),
                               ('IaiSpiritSlash', 2.)]:
            yield from self._fresh(50., 1 if move == 'IaiSpiritSlash' else 0)
            yield from self._enter_defense(move)
            self._probe_damage(move + ' successful counter', 0., True, True)
            self._check(abs(self.pawn.get_counter_armor_remaining()-duration) < .005,
                        move + ': source-table armour duration installed')
            montage = self._seek(min(self._length()-.15, .9))
            before = self._player_hp()
            self.pawn.get_editor_property('attributes').apply_damage(10., self.target)
            self._check(abs(before-self._player_hp()-5.) < .001,
                        move + ': armour takes half damage outside iframe')
            self._check(self._current() == move, move + ': armour suppresses interruption')
            yield from self._wait_world(duration+.05)
            self._check(self.pawn.get_counter_armor_remaining() <= .0001,
                        move + ': armour expires using actor world time')
            before = self._player_hp()
            self.pawn.get_editor_property('attributes').apply_damage(10., self.target)
            self._check(abs(before-self._player_hp()-10.) < .001 and self._idle(),
                        move + ': expired armour allows full damage and interruption')
        yield from self._fresh(50.)
        yield from self._enter_defense('IaiSlash')
        self._probe_damage('explicit interrupt armour setup', 0., True, True)
        self.pawn.interrupt_move()
        self._check(self._idle() and self.pawn.get_counter_armor_remaining() == 0.,
                    'explicit InterruptMove clears granted armour immediately')
        yield from self._fresh(50.)
        yield from self._enter_defense('ForesightSlash')
        self._probe_damage('normal derivative armour setup', 0., True, True)
        self._place_target(150.)
        windows = list(self._def('ForesightSlash').get_editor_property('damage_windows'))
        self._seek(float(windows[-1].get_editor_property('end_time')))
        yield
        route = self._find_route(self._def('ForesightSlash'), 'spirit', 'SpiritRoundslash')
        self._check(route is not None, 'formal counter-hit Roundslash route exists')
        start = float(route.get_editor_property('cancel_start'))
        if start < 0:
            start = float(self._def('ForesightSlash').get_editor_property('cancel_start'))
        self._seek(start+.01)
        yield
        self._press('spirit')
        yield from self._wait(lambda: self._current() == 'SpiritRoundslash',
                              'counter-hit R derives Roundslash')
        self._check(self.pawn.get_counter_armor_remaining() > 0.,
                    'unexpired counter armour survives a normal legal derivation')
        before = self._player_hp()
        self.pawn.get_editor_property('attributes').apply_damage(10., self.target)
        self._check(abs(before-self._player_hp()-5.) < .001
                    and self._current() == 'SpiritRoundslash',
                    'derived move keeps half-damage armour and resists interruption')
        yield from self._fresh(50.)
        yield from self._enter_defense('IaiSlash')
        self._probe_damage('armour death setup', 0., True, True)
        self._seek(.9)
        self.pawn.get_editor_property('attributes').apply_damage(1000., self.target)
        self._check(not bool(self.pawn.get_editor_property('attributes').is_alive),
                    'lethal incoming damage kills even under counter armour')
        self._check(self._idle() and self.pawn.get_counter_armor_remaining() == 0,
                    'death clears action and counter armour')

    def _suite_resources(self):
        durations = [float(v) for v in self.data.get_editor_property('spirit_level_durations')]
        self._check(durations == [0., 195., 135., 60.],
                    'formal white/yellow/red durations are 195/135/60 seconds')
        for level in (1, 2, 3):
            yield from self._fresh(50., level)
            remaining = float(self.pawn.get_spirit_time_remaining())
            self._check(abs(remaining-durations[level]) < .01,
                        'real level-%d raise installs its formal colour timer' % level)
        for move, cost in [('SpiritI', 15.), ('SpiritII', 15.),
                           ('SpiritIII', 20.), ('SpiritRoundslash', 25.)]:
            self._check(abs(self._cost(move)-cost) < .001, move + ': formal cost')
            for gauge in (cost-.01, cost):
                yield from self._fresh(gauge)
                started = bool(self.pawn.start_move(move))
                weak = move == 'SpiritI' and gauge < cost
                self._check(started == (weak or gauge >= cost),
                            '%s gauge%.2f start eligibility' % (move, gauge))
                expected = gauge if weak or not started else gauge-cost
                self._check(abs(self._gauge()-expected) < .003,
                            '%s gauge%.2f exact single spend/weak no-spend' % (move, gauge))
                self._record('cost', move=move, before=gauge, after=self._gauge(),
                             started=started, weak=weak)
        # Countering alone must not fill the Foresight gauge. Its return slash
        # must actually damage a target; an empty sweep grants nothing.
        for hit in (False, True):
            yield from self._fresh(50.)
            yield from self._enter_defense('ForesightSlash')
            self._probe_damage('Foresight return ' + ('hit' if hit else 'whiff'),
                               0., True, True)
            self._check(self._gauge() < .01, 'successful dodge alone does not fill gauge')
            self._place_target(150. if hit else 3000.)
            baseline = self._hp()
            montage = self.anim.get_current_active_montage()
            self.anim.montage_resume(montage)
            end = time.monotonic()+8.
            while not self._idle():
                self._place_target(150. if hit else 3000.)
                if time.monotonic() > end:
                    raise behavior.BehaviorFailure('Foresight return did not finish')
                yield
            self._check(self._hp() < baseline if hit else abs(self._hp()-baseline)<.001,
                        'Foresight return has the requested real hit/whiff result')
            self._check(self._gauge() > 99.99 if hit else self._gauge() < .01,
                        'only a successful real Foresight return fills gauge')
        for counter in (False, True):
            yield from self._fresh(50., 1)
            yield from self._enter_defense('IaiSpiritSlash')
            if counter:
                self._probe_damage('Iai spirit preserve-level setup', 0., True, True)
            montage = self.anim.get_current_active_montage()
            self.anim.montage_resume(montage)
            yield from self._wait(self._idle, 'Iai Spirit completes')
            self._check(self._level() == (1 if counter else 0),
                        'Iai Spirit preserves colour only when counter confirmed')
        for counter, expected in [(False, 15.), (True, 30.)]:
            yield from self._fresh(0.)
            yield from self._enter_defense('IaiSlash')
            if counter:
                self._probe_damage('Iai regen counter setup', 0., True, True)
            self._place_target(150.)
            montage = self.anim.get_current_active_montage()
            self.anim.montage_resume(montage)
            end = time.monotonic()+8.
            while self.pawn.get_gauge_regen_time_remaining() <= 0:
                self._place_target(150.)
                if time.monotonic() > end:
                    raise behavior.BehaviorFailure('Iai did not hit and activate regen')
                yield
            self._check(expected-.25 <= self.pawn.get_gauge_regen_time_remaining() <= expected,
                        'Iai real hit grants %.0fs regen' % expected)
            # Let the move finish, then pause its actor clock at 99% gauge for a
            # short observation; the measured delta, not wall time, is decisive.
            yield from self._wait(self._idle, 'Iai completes before regen measurement')
            self._place_target(3000.)
            before, remaining, clock = (self._gauge(),
                self.pawn.get_gauge_regen_time_remaining(), self._seconds())
            yield from self._wait_world(.5)
            dt = self._seconds()-clock
            expected_gain = min(100.-before, min(dt, remaining)*100./15.)
            self._check(abs(self._gauge()-before-expected_gain) < .025,
                        'regen adds exactly 100/15 per actor second, capped at 100')
            self._record('regen', counter=counter, seconds=dt, before=before,
                         after=self._gauge(), expected_gain=expected_gain)
            # Accelerate only this runtime Actor to approach the final interval,
            # then deliberately cross expiry in a large Tick. Gauge preparation
            # uses the public gain-on-start and does not reset the regen timer.
            self.pawn.set_editor_property('custom_time_dilation', 20.)
            try:
                yield from self._wait(
                    lambda: self.pawn.get_gauge_regen_time_remaining() < 2.,
                    'regen approaches expiry', 8.)
                self._seed_gauge(0.)
                tail = float(self.pawn.get_gauge_regen_time_remaining())
                self._check(tail > 0., 'regen tail remains before large-tick probe')
                self.pawn.set_editor_property('custom_time_dilation', 100.)
                yield from self._wait(
                    lambda: self.pawn.get_gauge_regen_time_remaining() <= 0.,
                    'large actor Tick crosses regen expiry', 4.)
                self._check(abs(self._gauge()-tail*100./15.) < .03,
                            'regen expiration grants only remaining source seconds')
                self._record('regen_expiry', counter=counter, remaining=tail,
                             gauge=self._gauge(), expected=tail*100./15.)
            finally:
                self.pawn.set_editor_property('custom_time_dilation', 1.)
        yield from self._fresh(100.)
        self._place_target(150.)
        self._check(self.pawn.start_move('SpiritRoundslash'), 'formal Roundslash starts')
        end = time.monotonic()+8.
        while self._level() == 0:
            self._place_target(150.)
            if time.monotonic() > end:
                raise behavior.BehaviorFailure('formal Roundslash did not raise colour')
            yield
        self._check(9.7 <= self.pawn.get_spirit_decay_pause_remaining() <= 10.,
                    'formal Roundslash hit starts ten-second colour-decay pause')
        before = float(self.pawn.get_spirit_time_remaining())
        yield from self._wait_world(.5)
        self._check(abs(self.pawn.get_spirit_time_remaining()-before)<.001,
                    'colour timer stays fixed while decay is paused')

    def _suite_routes(self):
        # Enumerate every authored input route. Generic defensive fallback is
        # not a route record and is covered by the defence suite instead.
        jobs = []
        blocked = {'HelmRise', 'HelmAir', 'SpiritHelmBreaker', 'HelmLand'}
        for move in sorted(self._move_names()):
            if move in blocked:
                continue  # Cannot legally start an isolated airborne stage.
            definition = self._def(move)
            for index, route in enumerate(self._routes(definition)):
                command = KEYS.get(str(route.get_editor_property('input')))
                if command is None:
                    raise behavior.BehaviorFailure('unknown authored route input')
                start = float(route.get_editor_property('cancel_start'))
                stop = float(route.get_editor_property('cancel_end'))
                if start < 0: start = float(definition.get_editor_property('cancel_start'))
                if stop < 0: stop = float(definition.get_editor_property('cancel_end'))
                jobs.append((move, index, route, command, start, stop))
        if self.route_limit is not None:
            jobs = jobs[:int(self.route_limit)]
        self.report['route_count'] = len(jobs)
        self._check(bool(jobs), 'formal DA contains per-input route windows')
        for move, index, route, command, start, stop in jobs:
            for case in ('early_expired', 'inside', 'late'):
                yield from self._fresh(100., 1)
                self._check(self.pawn.start_move(move), 'route source starts: ' + move)
                montage = self.anim.get_current_active_montage()
                length = float(montage.get_play_length())
                # Qualify only reachable windows. Unreachable source entries are
                # recorded explicitly, never silently treated as passed input.
                if start >= length or stop < start:
                    self._record('route_skips', move=move, index=index,
                                 reason='unreachable authored window', start=start,
                                 stop=stop, length=length)
                    break
                if bool(route.get_editor_property('require_hit')):
                    self._place_target(150.)
                    windows = list(self._def(move).get_editor_property('damage_windows'))
                    if windows:
                        self._seek(float(windows[-1].get_editor_property('end_time')))
                        yield
                    self._place_target(3000.)
                if bool(route.get_editor_property('require_counter')):
                    self._seek(0.)
                    self.pawn.get_editor_property('attributes').apply_damage(10., self.target)
                    self._check(self.pawn.has_counter_confirmed(),
                                move + ': route counter prerequisite is real')
                if case == 'early_expired':
                    position = max(0., start-.4)
                    if start-position <= .31:
                        self._record('route_skips', move=move, index=index,
                                     case=case, reason='window opens before buffer expiry')
                        continue
                    self._seek(position)
                    self._press(command)
                    yield
                    yield from self._wait_world(.36)
                    self._seek(min(stop, start+.01))
                    yield
                    self._check(self._current() == move,
                                '%s route%d expired early input cannot connect' % (move,index))
                elif case == 'inside':
                    self._seek(min(stop, start+.01))
                    yield
                    self._press(command)
                    yield from self._wait(lambda: self._current() != move,
                                          move + ' inside route transition', 1.5)
                    expected = str(route.get_editor_property('next_move'))
                    # Priority duplicates are data-defined. Require the first
                    # currently matching route for this input, not every branch.
                    earlier = [r for r in self._routes(self._def(move))[:index]
                               if r.get_editor_property('input') == route.get_editor_property('input')]
                    allowed = {expected} | {str(r.get_editor_property('next_move')) for r in earlier}
                    self._check(self._current() in allowed,
                                '%s route%d connects an eligible priority branch' % (move,index))
                else:
                    position = stop+.02
                    if bool(self._def(move).get_editor_property('holds_special_sheath')):
                        hold = float(self._def(move).get_editor_property('special_sheath_hold_time'))
                        if hold >= 0 and position >= hold:
                            self._record('route_skips', move=move, index=index, case=case,
                                         reason='special-hold phase owns later input')
                            continue
                    if position >= length-.01:
                        self._record('route_skips', move=move, index=index, case=case,
                                     reason='no live montage time after close')
                        continue
                    self._seek(position)
                    yield
                    self._press(command)
                    yield
                    yield
                    self._check(self._current() == move,
                                '%s route%d late input cannot reopen historical window' % (move,index))
                self._record('routes', move=move, index=index, case=case,
                             input=command, start=start, end=stop,
                             result=self._current())
        self.report['unverified_route_contexts'] = [
            'Airborne stage input is covered by pie_behavior_corrections air suite.',
            'Skipped cases are explicit in route_skips and are not counted as passed probes.']

    def _finish(self, error=None):
        global _ACTIVE
        if self.task is not None:
            try:
                self.task.close()
            except Exception:
                pass
            self.task = None
        if self.pawn is not None and self.data is not None:
            try:
                self.pawn.set_editor_property('custom_time_dilation', 1.)
                self._restore_formal()
            except Exception:
                pass
        super()._finish(error)
        _ACTIVE = None


def run(suite='all', route_limit=None):
    """Start a serial disposable PIE run; inspect its report's passed field."""
    global _ACTIVE
    if unreal is None:
        raise RuntimeError('run requires Unreal Editor Python')
    if suite not in ('all',) + SUITES:
        raise ValueError('suite must be all/defense/resources/routes')
    if _ACTIVE is not None and not _ACTIVE.done:
        raise RuntimeError('a combat fidelity runner is already active')
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level.is_in_play_in_editor():
        raise RuntimeError('end existing PIE before starting this serial suite')
    runner = CombatFidelityRunner(suite, route_limit)
    _ACTIVE = runner
    try:
        runner.prepare_editor()
        runner.handle = unreal.register_slate_post_tick_callback(runner.tick)
    except Exception:
        runner._finish(traceback.format_exc())
        raise
    return {'started': True, 'suite': suite, 'report': str(runner.report_file)}
