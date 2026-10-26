"""B12 apply: source-backed ledger sweep on the formal long-sword DataAsset.

Two changes only:
1. SpiritHelmBreaker receives the missing aerial hit from COL record 28
   (MV 126, source collision frames 25..112, Hit_Lag_a 0.4 s). The seven
   landing windows stay untouched; this is not the delayed-shell redesign.
2. The two Iai Spirit Slash exits with no source FSM edge (Spirit->SpiritIII,
   SpecialSheathe->SpecialSheathe) are marked as project adaptations so the
   original-input preset can skip them without deleting the shortcut preset.

Everything else is protected by a full-structure before/after guard. Preview
never writes; save backs up and reads back. No PIE, no invented timing values.
"""
import copy
import datetime
import json
import shutil

from author_reference_basics import snapshot, _input

ROOT = None
OUT = None
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'
HELM = 'SpiritHelmBreaker'
IAI = 'IaiSpiritSlash'
STEP = 'StepSlash'

# COL record 28, 必殺(空中); collision active 25..112 at 60 fps.
HELM_WINDOW = {
    'start_time': 25.0 / 60.0,
    'end_time': 112.0 / 60.0,
    'damage': 126.0,
    'spirit_gain': 0.0,
    'radius': 35.0,
    'forward_reach': 200.0,
    'side_extent': 65.0,
    'col_record_index': 28,
    'hit_lag_seconds': 0.4,
}
# No source node65 edge; both remain available in the shortcut preset.
ADAPT_ROUTES = {('SPIRIT', 'SpiritIII'), ('SPECIAL_SHEATHE', 'SpecialSheathe')}


def _roots():
    global ROOT, OUT
    if ROOT is None:
        import native_reference_basics as basics
        ROOT = basics.ROOT
        OUT = ROOT / 'Saved/MHWIRestoration/B12-20261026'
    return ROOT, OUT


def _norm(value):
    if isinstance(value, float):
        return round(value, 5)
    if isinstance(value, dict):
        return {str(k): _norm(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_norm(v) for v in value]
    return value


def _window_matches(window):
    return all(abs(float(window.get_editor_property(key)) - value) < 1e-4
               for key, value in HELM_WINDOW.items() if key != 'col_record_index'
               and key != 'hit_lag_seconds') \
        and int(window.get_editor_property('col_record_index')) == HELM_WINDOW['col_record_index'] \
        and abs(float(window.get_editor_property('hit_lag_seconds')) - HELM_WINDOW['hit_lag_seconds']) < 1e-4 \
        and not dict(window.get_editor_property('spirit_level_damage'))


def apply_to_copies(original):
    import unreal
    moves = {key: value.copy() for key, value in original.items()}
    names = {str(key): key for key in moves}
    if HELM not in names or IAI not in names or STEP not in names:
        raise RuntimeError('Formal moveset lost a required move: ' + HELM + '/' + IAI + '/' + STEP)
    before = snapshot(original)

    helm = moves[names[HELM]]
    windows = [w.copy() for w in helm.get_editor_property('damage_windows')]
    if len(windows) == 0:
        template = moves[names[STEP]].get_editor_property('damage_windows')[0].copy()
        for key, value in HELM_WINDOW.items():
            template.set_editor_property(key, value)
        template.set_editor_property('spirit_level_damage', {})
        windows = [template]
    elif len(windows) == 1 and _window_matches(windows[0]):
        pass
    else:
        raise RuntimeError('SpiritHelmBreaker already has unexpected windows; re-qualify before applying')
    helm.set_editor_property('damage_windows', windows)

    iai = moves[names[IAI]]
    routes = [r.copy() for r in iai.get_editor_property('routes')]
    marked = 0
    for route in routes:
        pair = (_input(route.get_editor_property('input')), str(route.get_editor_property('next_move')))
        if pair in ADAPT_ROUTES:
            route.set_editor_property('project_adaptation', True)
            marked += 1
    if marked != len(ADAPT_ROUTES):
        raise RuntimeError('Iai adaptation exits missing; current routes: '
                           + json.dumps([(_input(r.get_editor_property('input')),
                                          str(r.get_editor_property('next_move'))) for r in routes]))
    iai.set_editor_property('routes', routes)
    after = snapshot(moves)

    # Full-structure guard: only the helm windows and the adaptation bits may differ.
    def protected(data):
        data = copy.deepcopy(data)
        data[HELM].pop('damage_windows', None)
        for route in data[IAI]['routes']:
            route.pop('project_adaptation', None)
        return data
    if protected(before) != protected(after):
        raise RuntimeError('B12 changed a field outside the two declared areas')

    expected = copy.deepcopy(before[HELM]['damage_windows'])
    if not expected:
        template = copy.deepcopy(before[STEP]['damage_windows'][0])
        for key, value in HELM_WINDOW.items():
            template[key] = value
        template['spirit_level_damage'] = {}
        expected = [template]
    if [_norm(w) for w in after[HELM]['damage_windows']] != [_norm(w) for w in expected]:
        raise RuntimeError('SpiritHelmBreaker window differs from the source-derived value')
    for route in after[IAI]['routes']:
        pair = (_input(route['input']), route['next_move'])
        if pair in ADAPT_ROUTES and not route['project_adaptation']:
            raise RuntimeError('Adaptation bit was not written for ' + str(pair))
    return moves, dict(before=before, after=after, protected_fields_unchanged=True,
                       helm_window_added=not bool(before[HELM]['damage_windows']),
                       iai_adaptation_routes=marked)


def run(save=False):
    import unreal
    root, out = _roots()
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before writing the formal moveset')
    unreal.MHWIHitWindow()
    data = unreal.load_asset(DATA)
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Wrong formal DataAsset type')
    path = root / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    import native_reference_basics as basics
    before_sha = basics.sha(path)
    moves, report = apply_to_copies(data.get_editor_property('moves'))
    again, second = apply_to_copies(moves)
    if report['after'] != second['after']:
        raise RuntimeError('B12 authoring is not idempotent')
    report.update(saved=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  disk_sha256_before=before_sha, idempotent=True,
                  source_record=dict(file='wp03.col', index=28, motion_value=126.0,
                                     collision_frames=[25.0, 112.0], hit_lag=0.4))
    if save:
        backup = out / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        data.set_editor_property('moves', moves)
        if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
            raise RuntimeError('Formal DataAsset save failed')
        if snapshot(data.get_editor_property('moves')) != report['after']:
            raise RuntimeError('Formal DataAsset readback differs from preview')
        report['saved'] = True
    elif basics.sha(path) != before_sha:
        raise RuntimeError('Preview wrote a disk asset')
    report['disk_sha256_after'] = basics.sha(path)
    out.mkdir(parents=True, exist_ok=True)
    (out / ('authored.json' if save else 'preview.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return dict(saved=save, idempotent=True, protected_fields_unchanged=True,
                helm_window_added=report['helm_window_added'],
                iai_adaptation_routes=report['iai_adaptation_routes'])


if __name__ == '__main__':
    print(json.dumps(dict(mode='import-unreal-required'), ensure_ascii=False))
