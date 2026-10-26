"""Targeted, auditable route-window authoring for the formal MHWI moveset.

The profile contains project tuning anchored to source TIML phase boundaries.
It does not decode input flag semantics or claim original-game cancel frames.
Import is inert. ``run(save=False)`` previews; the coordinator explicitly calls
``run(save=True)`` after loading the new FMHWIRoute reflection fields.

Only Routes is written, using copies of existing definitions/routes. Montage,
damage, defence, resource, weapon event and source speed properties are retained.
No animation sequence, montage, skeleton, Blueprint, map or source file is saved.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil

try:
    import unreal
except ImportError:
    unreal = None

ROOT = Path(__file__).resolve().parents[2]
if unreal is not None:
    ROOT = Path(unreal.Paths.project_dir()).resolve()
PROFILE_PATH = ROOT / 'Scripts/MHWI/transition_calibration.json'
OUTPUT = ROOT / 'Saved/MHWIImport/TransitionCalibration-20261024'
DATA_PATH = '/Game/MHWI/Data/DA_MHWI_LongSword'
FRAME_RATE = 60.0
DISABLED_SECONDS = 9999.0
GENERIC_TARGETS = {'EVADE': 'Roll', 'SPECIAL_SHEATHE': 'SpecialSheathe',
                   'FORESIGHT': 'ForesightSlash', 'FADE_SLASH': 'FadeSlash'}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_profile(path=PROFILE_PATH, verify_sources=True):
    """Validate the checked-in profile without requiring Unreal or mutation."""
    profile = json.loads(Path(path).read_text(encoding='utf8'))
    if profile.get('schema') != 1 or profile.get('frame_rate') != FRAME_RATE:
        raise ValueError('Unsupported transition profile schema/frame rate')
    if profile.get('original_game_exact_frames') is not False:
        raise ValueError('This profile must state its project-tuning boundary')
    if verify_sources:
        for source in profile['source_files']:
            if _sha256(ROOT / source['path']) != source['sha256']:
                raise ValueError('Source hash mismatch: ' + source['path'])
    for name, move in profile['moves'].items():
        seen = set()
        for rule in move['rules']:
            identity = (rule['input'], rule.get('target', '*'))
            if identity in seen:
                raise ValueError('Duplicate rule: %s %r' % (name, identity))
            seen.add(identity)
            if not rule.get('rationale') or not rule.get('confidence'):
                raise ValueError('Missing evidence boundary: ' + name)
            if rule.get('scope') == 'generic_cancel':
                if rule.get('target') != GENERIC_TARGETS.get(rule['input']):
                    raise ValueError('Unexpected generic cancel target: ' + name)
            if rule.get('disabled'):
                continue
            start, end = rule['frames']
            if not all(math.isfinite(x) for x in (start, end)) or not 0 <= start <= end:
                raise ValueError('Invalid route window: ' + name)
            if end > move['expected_montage_frames'] + 0.01:
                raise ValueError('Window exceeds montage: ' + name)
    return profile


def profile_summary(profile=None):
    profile = profile or load_profile()
    return {'profile': str(PROFILE_PATH.relative_to(ROOT)),
            'profile_sha256': _sha256(PROFILE_PATH),
            'moves': len(profile['moves']),
            'rules': sum(len(m['rules']) for m in profile['moves'].values()),
            'original_game_exact_frames': False,
            'validation': 'profile_schema_and_original_source_hashes_only'}


def _input_name(value):
    # Unreal exposes ``<MHWIInput.LIGHT: 0>``; name is provided on some builds.
    name = getattr(value, 'name', None)
    if isinstance(name, str):
        return name
    return str(value).split('MHWIInput.')[-1].split(':')[0].split('>')[0]


def _route_snapshot(route):
    return {'input': _input_name(route.get_editor_property('input')),
            'next_move': str(route.get_editor_property('next_move')),
            'require_hit': bool(route.get_editor_property('require_hit')),
            'require_counter': bool(route.get_editor_property('require_counter')),
            'require_drawn': bool(route.get_editor_property('require_drawn')),
            'require_full_spirit_cost': bool(route.get_editor_property('require_full_spirit_cost')),
            'cancel_start': float(route.get_editor_property('cancel_start')),
            'cancel_end': float(route.get_editor_property('cancel_end'))}


def _window(rule):
    if rule.get('disabled'):
        return DISABLED_SECONDS, DISABLED_SECONDS
    return tuple(float(x) / FRAME_RATE for x in rule['frames'])


def _guard_reflection():
    if unreal is None:
        raise RuntimeError('run() requires the project Unreal Python environment')
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before route-window authoring')
    probe = unreal.MHWIRoute()
    try:
        probe.get_editor_property('cancel_start')
        probe.get_editor_property('cancel_end')
        probe.get_editor_property('require_full_spirit_cost')
    except Exception as exc:
        raise RuntimeError('Rebuild/restart with FMHWIRoute.CancelStart/CancelEnd first') from exc


def _patched_routes(name, definition, move, definitions):
    routes = [route.copy() for route in definition.get_editor_property('routes')]
    before = [_route_snapshot(route) for route in routes]
    for rule in move['rules']:
        command = rule['input']
        target = rule.get('target')
        matches = [route for route in routes
                   if _input_name(route.get_editor_property('input')) == command
                   and (target is None or str(route.get_editor_property('next_move')) == target)]
        if not matches:
            if rule.get('scope') != 'generic_cancel' or target != GENERIC_TARGETS.get(command):
                raise RuntimeError('%s: expected existing route %s -> %s' % (name, command, target))
            if any(_input_name(route.get_editor_property('input')) == command for route in routes):
                raise RuntimeError('%s: existing custom %s target conflicts with generic profile; preserve and review it'
                                   % (name, command))
            if target not in definitions:
                raise RuntimeError('%s: missing generic target %s' % (name, target))
            route = unreal.MHWIRoute()
            route.set_editor_property('input', getattr(unreal.MHWIInput, command))
            route.set_editor_property('next_move', target)
            route.set_editor_property('require_drawn', command != 'EVADE')
            routes.append(route)
            matches.append(route)
        start, end = _window(rule)
        for route in matches:
            route.set_editor_property('cancel_start', start)
            route.set_editor_property('cancel_end', end)
    return routes, {'before': before, 'after': [_route_snapshot(route) for route in routes]}


def run(save=False):
    """Preview all changes, or explicitly save the formal DA after full preflight.

    A first-write disk snapshot is retained. All rules are validated before any
    UObject property is changed. Repeating the call does not duplicate routes.
    """
    _guard_reflection()
    profile = load_profile()
    data = unreal.load_asset(DATA_PATH)
    if not data or data.get_class().get_name() != 'MHWIMovesetData':
        raise RuntimeError('Expected formal UMHWIMovesetData: ' + DATA_PATH)
    original = {str(key): value for key, value in data.get_editor_property('moves').items()}
    definitions = dict(original)
    changes = {}
    for name, move in profile['moves'].items():
        if name not in original:
            raise RuntimeError('Missing formal move: ' + name)
        definition = original[name].copy()
        montage = definition.get_editor_property('montage')
        expected = move['expected_montage_frames'] / FRAME_RATE
        if not montage or abs(montage.get_play_length() - expected) > .001:
            raise RuntimeError('%s: unexpected formal montage length; refusing stale timing' % name)
        expected_path = '/Game/MHWI/Montages/M_' + move.get('montage_name', name)
        if montage.get_path_name().split('.')[0] != expected_path:
            raise RuntimeError('%s: unexpected formal montage %s' % (name, montage.get_path_name()))
        routes, change = _patched_routes(name, definition, move, original)
        definition.set_editor_property('routes', routes)
        definitions[name] = definition
        changes[name] = change
    report = {**profile_summary(profile), 'data': data.get_path_name(), 'saved': False,
              'status': 'preview', 'moves': changes,
              'preserved': ['montage references/segments/notifies', 'move shared cancel window',
                            'damage windows', 'source speed keys', 'weapon motion events',
                            'defence/counter windows', 'spirit/resource rules', 'all other move fields'],
              'runtime_verification': 'not_executed_by_authoring_script'}
    # Serialization must succeed before touching the formal UObject.
    json.dumps(report, indent=2)
    if not save:
        return report
    package = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    backup = OUTPUT / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(package, backup)
    report['backup'] = str(backup.relative_to(ROOT))
    report['backup_sha256'] = _sha256(backup)
    data.set_editor_property('moves', definitions)
    if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
        data.set_editor_property('moves', original)
        raise RuntimeError('Formal moveset save failed; restored in-memory definitions')
    report['saved'] = True
    report['status'] = 'saved_route_windows_runtime_verification_pending'
    report['readback'] = {name: [_route_snapshot(route) for route in definition.get_editor_property('routes')]
                          for name, definition in data.get_editor_property('moves').items()
                          if str(name) in changes}
    report['readback'] = {str(name): rows for name, rows in report['readback'].items()}
    report['saved_asset_sha256'] = _sha256(package)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'author-transition-calibration.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true', help='Read-only profile/source check')
    options = parser.parse_args()
    if options.validate:
        print(json.dumps(profile_summary(), indent=2))
    else:
        parser.error('Use --validate outside Unreal; coordinator calls run(save=True) inside UE')
