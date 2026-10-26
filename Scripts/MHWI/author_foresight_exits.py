"""B11 apply: Foresight Slash missing source-qualified exits (routes only).

Adds the two exits the original FSM node 28 carries and the project lacked:
THRUST (circle) -> Thrust and HELM_BREAKER (R+triangle) -> SpiritThrust.
Both copy the existing ForesightSlash Light route (same no-prerequisite
condition class), reusing its adapter cancel window per the shared-ledger rule
for same-condition routes; no timing value is invented. Nothing else changes.
"""
import copy
import datetime
import json
import shutil

import native_foresight_exits as native
from author_reference_basics import snapshot, _input

ROOT, OUT = native.ROOT, native.OUT
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'
MOVE = 'ForesightSlash'
# Expected current routes before this batch: input -> target.
EXPECTED_ROUTES = [('SPIRIT', 'SpiritRoundslash'), ('LIGHT', 'StepSlash'),
                   ('FORESIGHT', 'ForesightSlash'), ('SPECIAL_SHEATHE', 'SpecialSheathe'),
                   ('EVADE', 'Roll'), ('FADE_SLASH', 'FadeSlash')]
NEW_EXITS = [('THRUST', 'Thrust'), ('HELM_BREAKER', 'SpiritThrust')]


def apply_to_copies(original, plan=None):
    import unreal
    plan = plan or native.run()
    moves = {key: value.copy() for key, value in original.items()}
    names = {str(key): key for key in moves}
    if MOVE not in names:
        raise RuntimeError('Formal moveset no longer defines ' + MOVE)
    before = snapshot(original)
    definition = moves[names[MOVE]]
    routes = [r.copy() for r in definition.get_editor_property('routes')]
    current = [(_input(r.get_editor_property('input')), str(r.get_editor_property('next_move')))
               for r in routes]
    light_index = next((i for i, (command, target) in enumerate(current)
                        if command == 'LIGHT' and target == 'StepSlash'), None)
    if light_index is None:
        raise RuntimeError('Light route no longer targets StepSlash (B01 retarget); review required')
    light = routes[light_index]
    for key in ('require_hit', 'require_counter', 'require_drawn', 'require_full_spirit_cost'):
        if light.get_editor_property(key):
            raise RuntimeError('Light route carries prerequisites; same-condition reuse no longer applies')
    if light.get_editor_property('cancel_start') < 0 or light.get_editor_property('cancel_end') < 0:
        raise RuntimeError('Light route has no explicit adapter window to reuse')
    additions = []
    for command, target in NEW_EXITS:
        route = light.copy()
        route.set_editor_property('input', getattr(unreal.MHWIInput, command))
        route.set_editor_property('next_move', target)
        additions.append(route)
    post_inputs = (EXPECTED_ROUTES[:light_index + 1]
                   + [(command, target) for command, target in NEW_EXITS]
                   + EXPECTED_ROUTES[light_index + 1:])
    if current == EXPECTED_ROUTES:
        result = routes[:light_index + 1] + additions + routes[light_index + 1:]
        applied_now = True
    elif current == post_inputs:
        # Idempotent repeat: the two derived routes must still equal the
        # derivation from the current Light route; nothing is rewritten.
        derived = [snapshot(route) for route in additions]
        existing = [snapshot(route) for route in routes[light_index + 1:light_index + 1 + len(NEW_EXITS)]]
        if existing != derived:
            raise RuntimeError('Applied exits no longer match the reused Light route; re-qualify')
        result = routes
        applied_now = False
    else:
        raise RuntimeError('Unexpected current ' + MOVE + ' routes; re-qualify before applying: '
                           + json.dumps(current))
    definition.set_editor_property('routes', result)
    after = snapshot(moves)

    # Full-structure guard: only ForesightSlash.routes may differ, and only by
    # the two derived routes inserted after the reused Light route.
    protected_before, protected_after = copy.deepcopy(before), copy.deepcopy(after)
    for data in (protected_before, protected_after):
        data[MOVE].pop('routes', None)
    if protected_before != protected_after:
        raise RuntimeError('B11 changed a field outside ' + MOVE + '.routes')
    expected_routes = copy.deepcopy(before[MOVE]['routes'])
    if applied_now:
        light_row = next(r for r in expected_routes if r['input'].endswith('LIGHT: 0>'))
        clones = []
        for command, target in NEW_EXITS:
            clone = copy.deepcopy(light_row)
            clone['input'] = str(getattr(unreal.MHWIInput, command))
            clone['next_move'] = target
            clones.append(clone)
        expected_routes = (expected_routes[:expected_routes.index(light_row) + 1]
                           + clones + expected_routes[expected_routes.index(light_row) + 1:])
    if after[MOVE]['routes'] != expected_routes:
        raise RuntimeError('B11 route derivation differs from the reused Light route')
    return moves, dict(before=before, after=after, protected_fields_unchanged=True)


def run(save=False):
    import unreal
    commandlet = '-run=pythonscript' in unreal.SystemLibrary.get_command_line().lower()
    if not commandlet and unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before writing the formal moveset')
    unreal.MHWIRoute().get_editor_property('cancel_start')
    plan = native.run()
    data = unreal.load_asset(DATA)
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Wrong formal DataAsset type')
    path = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    before_sha = native.basics.sha(path)
    moves, report = apply_to_copies(data.get_editor_property('moves'), plan)
    again, second = apply_to_copies(moves, plan)
    if report['after'] != second['after']:
        raise RuntimeError('B11 source import is not idempotent')
    report.update(saved=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_fingerprints=plan['sources'], disk_sha256_before=before_sha,
                  idempotent=True, exits=plan['exits'], boundaries=plan['boundaries'])
    if save:
        backup = OUT / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        data.set_editor_property('moves', moves)
        if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
            raise RuntimeError('Formal DataAsset save failed')
        if snapshot(data.get_editor_property('moves')) != report['after']:
            raise RuntimeError('Formal DataAsset readback differs from preview')
        report['saved'] = True
    elif native.basics.sha(path) != before_sha:
        raise RuntimeError('Preview wrote a disk asset')
    report['disk_sha256_after'] = native.basics.sha(path)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('authored.json' if save else 'preview.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return dict(saved=save, idempotent=True, protected_fields_unchanged=True,
                added_routes=len(NEW_EXITS))


if __name__ == '__main__':
    print(json.dumps(dict(mode='import-unreal-required'), ensure_ascii=False))
