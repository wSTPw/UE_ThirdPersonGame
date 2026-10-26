"""Targeted MHWI behaviour data corrections for the seven requested actions.

This module is intentionally separate from ``author_assets.moveset()``: it only
copies and updates the affected ``FMHWIMoveDefinition`` structs in the formal
DA, so unrelated manual tuning is preserved. Import has no side effects and
``run()`` can be executed repeatedly.

Prerequisites performed by Codex through MCP (not by this script):

* ``M_SpiritThrust`` slot segment replaced with ``A_w03_00_170``.
* ``M_ForesightSlash`` slot segment replaced with ``A_w03_00_140``.
* ``M_FadeSlashLeft`` / ``M_FadeSlashRight`` slot segments replaced with
  ``A_w03_00_128`` / ``A_w03_00_127`` (UE displacement basis correction).
* ``M_RollStepSlash`` created from ``A_w03_00_129`` and a second segment
  appended for ``A_w03_00_101`` with ``startPos=0.8`` / ``endPos=2.5``.
  The exact tool calls are emitted by ``write_segment_config()``.

The script refuses to run in PIE, refuses to write when the new shared
reflection fields are absent, and raises (instead of pretending success) when a
required montage length does not match the expected source segment.
"""
import json
from pathlib import Path

try:
    import unreal
except ImportError:  # Allows the read-only audit script to reuse the constants.
    unreal = None

ROOT = Path(__file__).resolve().parents[2]
if unreal is not None:
    ROOT = Path(unreal.Paths.project_dir()).resolve()

ASSET_ROOT = '/Game/MHWI'
REPORT_DIR = ROOT / 'Saved/MHWIImport/DSH-20261022'
MAPPING_PATH = ROOT / 'Scripts/MHWI/moveset_mapping.json'

FRAME = 60.0
from native_connector_source import entry_frame
# Original MBD destination 101 / previous motion 129, not endpoint fitting.
# This qualifies the table field only; connector exit/consumer remains separate.
ROLL_STEP_ENTRY_FRAME = entry_frame(101, 129)
ROLL_STEP_END_FRAME = 150.0
ROLL_STEP_FIRST_SEGMENT_END = 29.0 / FRAME
ROLL_STEP_HIT_START_FRAME = 55.0
ROLL_STEP_HIT_END_FRAME = 66.0

MOVE_FIELDS = [
    'turn_start_time', 'turn_end_time', 'turn_max_angle', 'turn_speed',
    'return_turn_start_time', 'return_turn_end_time', 'return_turn_max_angle',
]
DATA_FIELDS = [
    'helm_air_vertical_speed', 'helm_air_forward_speed', 'helm_air_gravity',
    'helm_strike_speed', 'helm_strike_start_time',
]


# ---------------------------------------------------------------------------
# Pure helpers (usable without Unreal)
# ---------------------------------------------------------------------------

def roll_step_timing(entry_frame=ROLL_STEP_ENTRY_FRAME):
    """Return composite-relative timing for the 129 -> 101 roll step slash."""
    entry = float(entry_frame)
    if not 0.0 <= entry < ROLL_STEP_END_FRAME:
        raise ValueError('roll step entry frame out of range: %r' % (entry,))
    first = ROLL_STEP_FIRST_SEGMENT_END
    offset = first + (ROLL_STEP_HIT_START_FRAME - entry) / FRAME
    end = first + (ROLL_STEP_HIT_END_FRAME - entry) / FRAME
    total = first + (ROLL_STEP_END_FRAME - entry) / FRAME
    cancel_start = min(total - 0.08, end + 2.0 / FRAME)
    return dict(
        entry_frame=entry,
        entry_seconds=entry / FRAME,
        first_segment_start=0.0,
        first_segment_end=first,
        second_segment_end=ROLL_STEP_END_FRAME / FRAME,
        total_seconds=total,
        hit_start=offset,
        hit_end=end,
        cancel_start=cancel_start,
        cancel_end=max(0.0, total - 0.03),
    )


def roll_step_segment_config(entry_frame=ROLL_STEP_ENTRY_FRAME):
    """Explicit MCP segment configuration. Codex must apply this before run()."""
    timing = roll_step_timing(entry_frame)
    return {
        'schema': 1,
        'status': 'explicit_mcp_anim_segment_config',
        'note': ('The 129 dash is played once (29 source frames, 0.4833s; its segment '
                 'must end at the existing project 29/60), then clip 101 enters at source '
                 'frame 48 from original MBD destination101/previous129. The connector exit '
                 'and blend consumer remain unqualified. Its collision frames '
                 '55..66 are preserved without playing the whole 101 approach on top of '
                 'the 233.95cm 129 dash. Entry 48 leaves 7 source frames before the hit '
                 'and the measured composite root delta is -259.8cm; entry 37 keeps 18 '
                 'frames but leaves 31.7cm more forward travel, so it was rejected. '
                 'Apply through MCP before running author_behavior_corrections.run().'),
        'idempotency': ('First call animation.list_montage_segments. If it already matches '
                        '"expect", stop. If absent, create from 129. If the 129 segment endPos '
                        'is not 29/60 (some imports expose a 30-frame range), insert a trimmed '
                        '129 segment (startPos 0, endPos 0.48333333333333334) at insertIndex 1, '
                        'then remove segment 0. If no 101 segment exists, append it at insertIndex '
                        '1 with startPos 0.8 / endPos 2.5. If a 101 segment exists with a '
                        'different trim, remove it and re-add. Never run moveset() to create it.'),
        'assetPath': ASSET_ROOT + '/Montages/M_RollStepSlash',
        'skeleton': ASSET_ROOT + '/Character/SK_MHWI_Hunter_Skeleton',
        'slotName': 'DefaultSlot',
        'steps': [
            {
                'tool': 'animation.list_montage_segments',
                'params': {'assetPath': ASSET_ROOT + '/Montages/M_RollStepSlash'},
                'purpose': 'precheck; a missing asset error means run the creation step',
            },
            {
                'tool': 'animation.author_montages_batch',
                'params': {
                    'items': [{
                        'name': 'M_RollStepSlash',
                        'packagePath': ASSET_ROOT + '/Montages',
                        'animSequencePath': ASSET_ROOT + '/Animations/LongSword/A_w03_00_129',
                        'onConflict': 'skip',
                        'slotName': 'DefaultSlot',
                        'blendIn': 0.10,
                        'blendOut': 0.12,
                    }],
                },
                'purpose': 'create the montage from clip 129 when absent; skip leaves it untouched',
            },
            {
                'tool': 'animation.add_montage_segment',
                'params': {
                    'assetPath': ASSET_ROOT + '/Montages/M_RollStepSlash',
                    'animSequencePath': ASSET_ROOT + '/Animations/LongSword/A_w03_00_129',
                    'slotName': 'DefaultSlot',
                    'startPos': 0.0,
                    'endPos': timing['first_segment_end'],
                    'playRate': 1.0,
                    'loopCount': 1,
                    'insertIndex': 1,
                },
                'condition': 'only when the existing 129 segment endPos is not 29/60 (e.g. 0.5)',
                'purpose': 'normalize the 129 trim; follow with remove_montage_segment index 0',
            },
            {
                'tool': 'animation.remove_montage_segment',
                'params': {
                    'assetPath': ASSET_ROOT + '/Montages/M_RollStepSlash',
                    'slotName': 'DefaultSlot',
                    'segmentIndex': 0,
                },
                'condition': 'only after the trimmed 129 was inserted at index 1',
                'purpose': 'drop the old full-length 129 segment',
            },
            {
                'tool': 'animation.add_montage_segment',
                'params': {
                    'assetPath': ASSET_ROOT + '/Montages/M_RollStepSlash',
                    'animSequencePath': ASSET_ROOT + '/Animations/LongSword/A_w03_00_101',
                    'slotName': 'DefaultSlot',
                    'startPos': timing['entry_seconds'],
                    'endPos': ROLL_STEP_END_FRAME / FRAME,
                    'playRate': 1.0,
                    'loopCount': 1,
                    'insertIndex': 1,
                },
                'condition': 'only when no 101 segment exists, or after removing a 101 with another trim',
                'purpose': 'append the trimmed 101 swing',
            },
            {
                'tool': 'animation.list_montage_segments',
                'params': {'assetPath': ASSET_ROOT + '/Montages/M_RollStepSlash'},
                'expect': {
                    'montageLength': timing['total_seconds'],
                    'segmentCount': 2,
                    'segments': [
                        {'animation': ASSET_ROOT + '/Animations/LongSword/A_w03_00_129',
                         'startPos': 0.0, 'endPos': timing['first_segment_end'],
                         'trackStartPos': 0.0, 'playRate': 1.0},
                        {'animation': ASSET_ROOT + '/Animations/LongSword/A_w03_00_101',
                         'startPos': timing['entry_seconds'],
                         'endPos': ROLL_STEP_END_FRAME / FRAME,
                         'trackStartPos': timing['first_segment_end'],
                         'playRate': 1.0},
                    ],
                },
            },
        ],
        'expected_data': {
            'move': 'RollStepSlash',
            'damage_windows': [[timing['hit_start'], timing['hit_end']]],
            'cancel_start': timing['cancel_start'],
            'cancel_end': timing['cancel_end'],
            'damage': 26.0,
            'spirit_gain': 9.0,
            'light_route': 'OverheadSlash',
        },
    }


def write_segment_config(path=None):
    config = roll_step_segment_config()
    target = Path(path) if path else REPORT_DIR / 'rollstepslash-segments.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + '\n', encoding='utf8')
    return config


# ---------------------------------------------------------------------------
# Unreal helpers
# ---------------------------------------------------------------------------

def _plain(value):
    """Recursively convert Unreal maps/names/structs into JSON-safe Python values."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if hasattr(value, 'items'):
        return {str(key): _plain(item) for key, item in value.items()}
    return str(value)


def _require_unreal():
    if unreal is None:
        raise RuntimeError('author_behavior_corrections requires Unreal Python')


def _asset(path):
    obj = unreal.load_asset(path)
    if not obj:
        raise RuntimeError('Required asset missing: ' + path)
    return obj


def _assert_not_pie():
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level.is_in_play_in_editor():
        raise RuntimeError('Stop PIE before running behaviour corrections')


def _moves(data):
    # Unreal TMap -> plain dict so later struct copies cannot alias preview state.
    return {str(key): value for key, value in data.get_editor_property('moves').items()}


def _missing_property(obj, name):
    try:
        obj.get_editor_property(name)
    except Exception:
        return True
    return False


def _check_reflection_contract(data):
    missing = []
    moves = _moves(data)
    sample_move = next(iter(moves.values()), None)
    if sample_move is None:
        raise RuntimeError('DA has no move definitions to validate')
    for name in MOVE_FIELDS:
        if _missing_property(sample_move, name):
            missing.append('FMHWIMoveDefinition.' + name)
    for name in DATA_FIELDS:
        if _missing_property(data, name):
            missing.append('UMHWIMovesetData.' + name)
    probe = unreal.MHWIRoute()
    if _missing_property(probe, 'require_drawn'):
        missing.append('FMHWIRoute.require_drawn')
    if missing:
        raise RuntimeError('New shared reflection fields are missing (compile the A contract first): '
                           + ', '.join(missing))


def _route(command, next_move, hit=False, counter=False, drawn=False):
    value = unreal.MHWIRoute()
    value.set_editor_property('input', getattr(unreal.MHWIInput, command))
    value.set_editor_property('next_move', next_move)
    value.set_editor_property('require_hit', hit)
    value.set_editor_property('require_counter', counter)
    value.set_editor_property('require_drawn', drawn)
    return value


def _set_route(definition, command, next_move, require_drawn=None):
    wanted = getattr(unreal.MHWIInput, command)
    routes = definition.get_editor_property('routes')
    result = []
    found = False
    for link in routes:
        item = link.copy()
        if item.get_editor_property('input') == wanted:
            item.set_editor_property('next_move', next_move)
            if require_drawn is not None:
                item.set_editor_property('require_drawn', require_drawn)
            found = True
        result.append(item)
    if not found:
        result.append(_route(command, next_move, drawn=bool(require_drawn)))
    definition.set_editor_property('routes', result)
    return result


def _replace_input_routes(definition, command, next_move, drawn=False):
    """Drop existing routes for one input, then append a single explicit route."""
    wanted = getattr(unreal.MHWIInput, command)
    result = [link.copy() for link in definition.get_editor_property('routes')
              if link.get_editor_property('input') != wanted]
    result.append(_route(command, next_move, drawn=drawn))
    definition.set_editor_property('routes', result)
    return result


def _set_light_primary_and_fallback(definition, primary, fallback):
    """High-priority drawn Light route, then a non-drawn fallback for active sheathed Roll."""
    wanted = getattr(unreal.MHWIInput, 'LIGHT')
    result = [_route('LIGHT', primary, drawn=True), _route('LIGHT', fallback, drawn=False)]
    result.extend(link.copy() for link in definition.get_editor_property('routes')
                  if link.get_editor_property('input') != wanted)
    definition.set_editor_property('routes', result)
    return result


def _apply_hit_windows(definition, source, fallback_damage, fallback_gain):
    old = definition.get_editor_property('damage_windows')
    windows = []
    for index, (start, end) in enumerate(source['collision_active_frames']):
        window = old[min(index, len(old) - 1)].copy() if old else unreal.MHWIHitWindow()
        window.set_editor_property('start_time', start / FRAME)
        window.set_editor_property('end_time', end / FRAME)
        if not old:
            window.set_editor_property('damage', float(fallback_damage))
            window.set_editor_property('spirit_gain', float(fallback_gain))
        windows.append(window)
    definition.set_editor_property('damage_windows', windows)
    return windows


def _apply_montage_timing(definition, montage, source):
    final_hit = max((pair[1] / FRAME for pair in source['collision_active_frames']),
                    default=montage.get_play_length() * 0.45)
    definition.set_editor_property('cancel_start', min(montage.get_play_length() - 0.08,
                                                       final_hit + 2.0 / FRAME))
    definition.set_editor_property('cancel_end', max(0.0, montage.get_play_length() - 0.03))
    speeds = source.get('source_motion_speed', [])
    definition.set_editor_property('source_play_rates',
                                   {frame / FRAME: rate for frame, rate in speeds[0]} if speeds else {})


def _montage_length(definition):
    return definition.get_editor_property('montage').get_play_length()


def _verify_montage(name, definition, expected_clip, expected_frames):
    montage = definition.get_editor_property('montage')
    expected = expected_frames / FRAME
    actual = montage.get_play_length()
    if abs(actual - expected) > 0.001:
        raise RuntimeError(
            '%s montage must be re-segmented to clip %s (expected %.4fs, current %.4fs) '
            'through MCP before this correction' % (name, expected_clip, expected, actual))
    return montage


def _apply_fade_direction_timing(definitions, mapping, report):
    """Refresh source timing while preserving each semantic move's tuning/routes."""
    corrected = []
    for name, clip, node, action, collision in [
            ('FadeSlashLeft', 'w03_00_128', 8, 82, [[27.0, 42.0]]),
            ('FadeSlashRight', 'w03_00_127', 9, 83, [[27.0, 43.0]])]:
        source = mapping['moves'][name]
        if (source['clip'] != clip or source['fsm_node_id'] != node
                or source['fsm_action_no'] != action
                or source['collision_active_frames'] != collision):
            raise RuntimeError('moveset_mapping.json has a stale lateral fade record: ' + name)
        montage = _verify_montage(name, definitions[name], clip, source['source_frames'])
        corrected.append((name, source, montage))
    for name, source, montage in corrected:
        definition = definitions[name].copy()
        _apply_hit_windows(definition, source, 24.0, 9.0)
        _apply_montage_timing(definition, montage, source)
        definition.set_editor_property('turn_start_time', 0.0)
        definition.set_editor_property('turn_end_time', 0.0)
        definition.set_editor_property('turn_max_angle', 0.0)
        definition.set_editor_property('turn_speed', 360.0)
        definitions[name] = definition
        report['moves'][name] = {
            'clip': source['clip'],
            'fsm_node_id': source['fsm_node_id'],
            'fsm_action_no': source['fsm_action_no'],
            'collision_frames': source['collision_active_frames'],
            'montage_length': montage.get_play_length(),
            'cancel': [definition.get_editor_property('cancel_start'),
                       definition.get_editor_property('cancel_end')],
            'play_rates': {float(key): float(value) for key, value in
                           definition.get_editor_property('source_play_rates').items()},
            'preserved': ['damage', 'spirit_gain', 'routes', 'other_move_tuning'],
            'turn_max_angle': 0.0,
        }


def _maintain_roll_step_blends(montage):
    """Set only blend times; the existing 129+101 segment array remains intact."""
    result = {}
    for property_name, seconds in [('blend_in', 0.10), ('blend_out', 0.12)]:
        blend = montage.get_editor_property(property_name)
        blend.set_editor_property('blend_time', seconds)
        montage.set_editor_property(property_name, blend)
        result[property_name] = float(blend.get_editor_property('blend_time'))
    unreal.EditorAssetLibrary.save_loaded_asset(montage, only_if_is_dirty=False)
    return result


def fade_direction_corrections():
    """Only refresh left/right fade DA timings and existing roll montage blends."""
    _require_unreal()
    _assert_not_pie()
    mapping = json.loads(MAPPING_PATH.read_text(encoding='utf8'))
    data = _asset(ASSET_ROOT + '/Data/DA_MHWI_LongSword')
    definitions = _moves(data)
    report = {'moves': {}, 'montages': {}, 'saved': False}
    _apply_fade_direction_timing(definitions, mapping, report)
    roll = _asset(ASSET_ROOT + '/Montages/M_RollStepSlash')
    expected_length = roll_step_timing()['total_seconds']
    if abs(roll.get_play_length() - expected_length) > 0.001:
        raise RuntimeError('M_RollStepSlash must retain the 129+101 composite before correction')
    report['montages']['RollStepSlash'] = _maintain_roll_step_blends(roll)
    data.set_editor_property('moves', definitions)
    unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False)
    report['saved'] = True
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / 'fade-direction-corrections.json').write_text(
        json.dumps(_plain(report), indent=2) + '\n', encoding='utf8')
    return report


def _maintain_aerial_montage_tails():
    """Keep the air/strike tail pose until the character's real landing transition."""
    montages = [_asset(ASSET_ROOT + '/Montages/M_' + name)
                for name in ['HelmAir', 'SpiritHelmBreaker']]
    report = {}
    for montage in montages:
        montage.set_editor_property('enable_auto_blend_out', False)
        unreal.EditorAssetLibrary.save_loaded_asset(montage, only_if_is_dirty=False)
        report[montage.get_path_name()] = {
            'enable_auto_blend_out': bool(montage.get_editor_property('enable_auto_blend_out')),
            'length': float(montage.get_play_length()),
            'segments': 'unchanged',
        }
    return report


def aerial_montage_corrections():
    """Only disable auto blend-out on existing Air/Strike montages; preserve segments."""
    _require_unreal()
    _assert_not_pie()
    report = {'montages': _maintain_aerial_montage_tails(), 'saved': True}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / 'aerial-montage-corrections.json').write_text(
        json.dumps(_plain(report), indent=2) + '\n', encoding='utf8')
    return report


def create_roll_step_montage():
    """Create only M_RollStepSlash from clip 129. Safe to repeat; never resets segments."""
    _require_unreal()
    _assert_not_pie()
    path = ASSET_ROOT + '/Montages/M_RollStepSlash'
    existing = unreal.load_asset(path)
    if existing:
        return dict(montage=path, already_exists=True, length=existing.get_play_length(),
                    blends=_maintain_roll_step_blends(existing))
    sequence = _asset(ASSET_ROOT + '/Animations/LongSword/A_w03_00_129')
    factory = unreal.AnimMontageFactory()
    factory.set_editor_property('target_skeleton', sequence.get_editor_property('skeleton'))
    factory.set_editor_property('source_animation', sequence)
    montage = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'M_RollStepSlash', ASSET_ROOT + '/Montages', unreal.AnimMontage, factory)
    if not montage:
        raise RuntimeError('Could not create ' + path)
    return dict(montage=path, already_exists=False, length=montage.get_play_length(),
                blends=_maintain_roll_step_blends(montage))


def run():
    if (ROOT / 'Tools/MHW/r06-runtime-adapter.json').exists():
        raise RuntimeError('R06 runtime migration is active. This historical batch rebuilds the obsolete 129 composite; use targeted corrections.')
    """Apply the seven requested data corrections to the formal DataAsset only."""
    _require_unreal()
    _assert_not_pie()
    mapping = json.loads(MAPPING_PATH.read_text(encoding='utf8'))
    data = _asset(ASSET_ROOT + '/Data/DA_MHWI_LongSword')
    _check_reflection_contract(data)
    source_170 = mapping['moves']['SpiritThrust']
    source_140 = mapping['moves']['ForesightSlash']
    if source_170['clip'] != 'w03_00_170' or source_140['clip'] != 'w03_00_140':
        raise RuntimeError('moveset_mapping.json does not carry the corrected 140/170 clips')
    for name, source, node, action, collision in [
            ('SpiritThrust', source_170, 45, 87, [[84.0, 97.0]]),
            ('ForesightSlash', source_140, 28, 86, [[70.0, 80.0]])]:
        if (source['fsm_node_id'] != node or source['fsm_action_no'] != action
                or source['collision_active_frames'] != collision):
            raise RuntimeError('moveset_mapping.json has a stale %s node/action/collision entry' % name)

    moves = _moves(data)
    definitions = dict(moves)
    report = {'moves': {}, 'routes': {}, 'montages': {}, 'notes': []}
    _apply_fade_direction_timing(definitions, mapping, report)

    # ---- source inversion fix: montage and windows must both follow the clip ----
    for name, source in [('SpiritThrust', source_170), ('ForesightSlash', source_140)]:
        montage = _verify_montage(name, definitions[name], source['clip'], source['source_frames'])
        definition = definitions[name].copy()
        _apply_hit_windows(definition, source, 18.0 if name == 'SpiritThrust' else 26.0,
                           0.0 if name == 'SpiritThrust' else 9.0)
        _apply_montage_timing(definition, montage, source)
        definitions[name] = definition
        report['moves'][name] = {
            'clip': source['clip'],
            'fsm_node_id': source['fsm_node_id'],
            'fsm_action_no': source['fsm_action_no'],
            'collision_frames': source['collision_active_frames'],
            'montage_length': montage.get_play_length(),
            'play_rates': {float(key): float(value) for key, value in
                           definition.get_editor_property('source_play_rates').items()},
        }

    # SpiritThrust hit -> HelmRise exactly at the 170 collision end (frame 97).
    # Clear the unconditional AutoFollowUp explicitly: a stale non-None value would
    # enter Rise even on a whiff, bypassing "hit plus white aura or above".
    thrust = definitions['SpiritThrust'].copy()
    thrust.set_editor_property('require_spirit_level', True)
    thrust.set_editor_property('auto_follow_up', 'None')
    thrust.set_editor_property('auto_follow_up_on_hit', 'HelmRise')
    thrust.set_editor_property('auto_follow_up_time', 97.0 / FRAME)
    definitions['SpiritThrust'] = thrust
    report['moves']['SpiritThrust']['auto_follow_up'] = 'None'
    report['moves']['SpiritThrust']['auto_follow_up_on_hit'] = 'HelmRise'
    report['moves']['SpiritThrust']['auto_follow_up_time'] = 97.0 / FRAME

    # ---- Foresight projectile-dodge tuning (all project values) ----
    foresight = definitions['ForesightSlash'].copy()
    foresight.set_editor_property('counter', True)
    foresight.set_editor_property('require_nonzero_gauge', True)
    foresight.set_editor_property('consume_all_gauge', True)
    foresight.set_editor_property('counter_start', 8.0 / FRAME)
    foresight.set_editor_property('counter_end', 42.0 / FRAME)
    foresight.set_editor_property('turn_start_time', 0.0)
    foresight.set_editor_property('turn_end_time', 0.12)
    foresight.set_editor_property('turn_max_angle', 25.0)
    foresight.set_editor_property('turn_speed', 360.0)
    foresight.set_editor_property('return_turn_start_time', 46.0 / FRAME)
    foresight.set_editor_property('return_turn_end_time', 68.0 / FRAME)
    foresight.set_editor_property('return_turn_max_angle', 45.0)
    foresight.set_editor_property('routes', [
        _route('SPIRIT', 'SpiritRoundslash', hit=True, counter=True),
        _route('LIGHT', 'OverheadSlash')])
    definitions['ForesightSlash'] = foresight
    report['moves']['ForesightSlash'].update({
        'counter_frames': [8.0, 42.0],
        'return_turn_frames': [46.0, 68.0],
        'return_turn_max_angle': 45.0,
        'turn': [0.0, 0.12, 25.0, 360.0],
    })

    # ---- normal RMB cycle: Thrust -> RisingSlash -> Thrust ----
    for name, target in [('Thrust', 'RisingSlash'), ('RisingSlash', 'Thrust')]:
        definition = definitions[name].copy()
        _set_route(definition, 'THRUST', target)
        definitions[name] = definition
        report['routes'][name + '.Thrust'] = target

    # ---- insertion identities reusing checked 105/107 main montages ----
    for combo, base, light, thrust, spirit, clip, frames in [
            ('SpiritComboThrust', 'Thrust', 'RisingSlash', 'RisingSlash', 'SpiritII',
             'w03_00_105', 130.0),
            ('SpiritComboRisingSlash', 'RisingSlash', 'OverheadSlash', 'Thrust', 'SpiritIII',
             'w03_00_107', 136.0)]:
        base_definition = definitions[base]
        montage = base_definition.get_editor_property('montage')
        if abs(montage.get_play_length() - frames / FRAME) > 0.001:
            raise RuntimeError('%s reuses %s but its montage length does not match %s'
                               % (combo, base, clip))
        combo_definition = base_definition.copy()
        combo_definition.set_editor_property('display_name', unreal.Text(combo))
        combo_definition.set_editor_property('routes', [
            _route('LIGHT', light), _route('THRUST', thrust), _route('SPIRIT', spirit)])
        combo_definition.set_editor_property('auto_follow_up', 'None')
        combo_definition.set_editor_property('auto_follow_up_on_hit', 'None')
        combo_definition.set_editor_property('auto_follow_up_time', 0.0)
        combo_definition.set_editor_property('spirit_cost', 0.0)
        definitions[combo] = combo_definition
        report['moves'][combo] = {
            'reused_move': base,
            'reused_clip': clip,
            'reused_montage': montage.get_path_name(),
            'connection_frames': 'project blend; connector clip 118/121/124 owns no damage window',
            'routes': {'Light': light, 'Thrust': thrust, 'Spirit': spirit},
        }

    # ---- Spirit I/II Light and Thrust enter the insertion identities ----
    for name, combo in [('SpiritI', 'SpiritComboThrust'), ('SpiritII', 'SpiritComboRisingSlash')]:
        definition = definitions[name].copy()
        _set_route(definition, 'LIGHT', combo)
        _set_route(definition, 'THRUST', combo)
        definitions[name] = definition
        report['routes'][name] = {'Light': combo, 'Thrust': combo}

    # ---- drawn Roll Light -> dedicated composite RollStepSlash ----
    timing = roll_step_timing()
    roll_montage = unreal.load_asset(ASSET_ROOT + '/Montages/M_RollStepSlash')
    if not roll_montage:
        write_segment_config()
        raise RuntimeError('Create M_RollStepSlash and apply the segment config first: '
                           + str(REPORT_DIR / 'rollstepslash-segments.json'))
    if abs(roll_montage.get_play_length() - timing['total_seconds']) > 0.001:
        write_segment_config()
        raise RuntimeError('M_RollStepSlash length %.4f does not match the 129+101 composite '
                           '%.4f; apply the AnimSegments config first: %s'
                           % (roll_montage.get_play_length(), timing['total_seconds'],
                              REPORT_DIR / 'rollstepslash-segments.json'))
    report['montages']['RollStepSlash'] = _maintain_roll_step_blends(roll_montage)
    if 'RollStepSlash' in definitions:
        roll_step = definitions['RollStepSlash'].copy()
    else:
        roll_step = definitions['StepSlash'].copy()
        roll_step.set_editor_property('display_name', unreal.Text('Roll Step Slash'))
    roll_step.set_editor_property('montage', roll_montage)
    roll_hit = unreal.MHWIHitWindow()
    roll_hit.set_editor_property('start_time', timing['hit_start'])
    roll_hit.set_editor_property('end_time', timing['hit_end'])
    roll_hit.set_editor_property('damage', 26.0)
    roll_hit.set_editor_property('spirit_gain', 9.0)
    roll_step.set_editor_property('damage_windows', [roll_hit])
    roll_step.set_editor_property('cancel_start', timing['cancel_start'])
    roll_step.set_editor_property('cancel_end', timing['cancel_end'])
    roll_step.set_editor_property('source_play_rates', {})
    roll_step.set_editor_property('routes', [_route('LIGHT', 'OverheadSlash')])
    definitions['RollStepSlash'] = roll_step
    report['moves']['RollStepSlash'] = {
        'montage': roll_montage.get_path_name(),
        'montage_length': roll_montage.get_play_length(),
        'segments': '129 frames 0..29 then 101 frames %d..%d'
                    % (int(ROLL_STEP_ENTRY_FRAME), int(ROLL_STEP_END_FRAME)),
        'damage_window': [timing['hit_start'], timing['hit_end']],
        'cancel': [timing['cancel_start'], timing['cancel_end']],
        'light_route': 'OverheadSlash',
    }
    roll = definitions['Roll'].copy()
    _set_light_primary_and_fallback(roll, 'RollStepSlash', 'DrawSlash')
    roll.set_editor_property('turn_start_time', 0.0)
    roll.set_editor_property('turn_end_time', 0.0)
    roll.set_editor_property('turn_max_angle', 0.0)
    roll.set_editor_property('turn_speed', 360.0)
    definitions['Roll'] = roll
    report['routes']['Roll.Light'] = [
        {'next_move': 'RollStepSlash', 'require_drawn': True},
        {'next_move': 'DrawSlash', 'require_drawn': False}]

    # ---- fade slashes must not add a programmatic entry turn ----
    for name in ['FadeSlash', 'FadeSlashLeft', 'FadeSlashRight']:
        definition = definitions[name].copy()
        definition.set_editor_property('turn_start_time', 0.0)
        definition.set_editor_property('turn_end_time', 0.0)
        definition.set_editor_property('turn_max_angle', 0.0)
        definition.set_editor_property('turn_speed', 360.0)
        definitions[name] = definition
        report['routes'][name + '.turn'] = {'max_angle': 0.0}

    # ---- helm chain: only Rise auto-exits; Air/Strike/Land are runtime-driven ----
    rise = definitions['HelmRise'].copy()
    rise.set_editor_property('use_full_root_motion', True)
    rise.set_editor_property('auto_follow_up', 'HelmAir')
    rise.set_editor_property('auto_follow_up_time',
                             max(0.0, rise.get_editor_property('montage').get_play_length() - 0.04))
    rise.set_editor_property('cancel_start', 9999.0)
    rise.set_editor_property('cancel_end', 9999.0)
    definitions['HelmRise'] = rise
    for name in ['HelmAir', 'SpiritHelmBreaker', 'HelmLand']:
        definition = definitions[name].copy()
        definition.set_editor_property('use_full_root_motion', False)
        definition.set_editor_property('auto_follow_up', 'None')
        definition.set_editor_property('auto_follow_up_on_hit', 'None')
        definition.set_editor_property('auto_follow_up_time', 0.0)
        definition.set_editor_property('cancel_start', 9999.0)
        definition.set_editor_property('cancel_end', 9999.0)
        definitions[name] = definition
    for name in ['HelmAir', 'SpiritHelmBreaker']:
        definition = definitions[name].copy()
        definition.set_editor_property('turn_start_time', 0.0)
        definition.set_editor_property('turn_end_time', 25.0 / FRAME)
        definition.set_editor_property('turn_max_angle', 120.0)
        definition.set_editor_property('turn_speed', 720.0)
        definitions[name] = definition
        report['moves'][name + '.turn'] = {'frames': [0.0, 25.0], 'max_angle': 120.0, 'speed': 720.0}
    report['montages']['aerial_tails'] = _maintain_aerial_montage_tails()
    report['routes']['HelmRise.auto'] = 'HelmAir'
    report['routes']['HelmAir.auto'] = 'None'
    report['routes']['SpiritHelmBreaker.auto'] = 'None'

    data.set_editor_property('moves', definitions)
    report['data'] = data.get_path_name()
    # Preflight serialization BEFORE saving the DA: no Unreal container/name/struct
    # may reach json.dumps, otherwise a saved DA could be followed by a report error.
    json.dumps(_plain(report), indent=2)
    unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False)
    report['saved'] = True
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / 'behavior-corrections.json').write_text(
        json.dumps(_plain(report), indent=2) + '\n', encoding='utf8')
    return report


def emit_segment_config():
    """Entry point that only writes/prints the MCP segment JSON (no UE writes)."""
    config = write_segment_config()
    print(json.dumps(config, indent=2))
    return config
