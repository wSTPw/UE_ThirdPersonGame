"""Apply only B01's source-qualified numeric/route fields; import is inert."""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import re
import shutil

import native_reference_basics as native

ROOT = native.ROOT
OUT = native.OUT
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'


def struct_fields():
    fields, owner = {}, None
    for line in (ROOT / 'Source/IntroCpp/MHWI/MHWIMovesetData.h').read_text(encoding='utf-8-sig').splitlines():
        match = re.search(r'(?:struct|class) INTROCPP_API ([FU]\w+)', line)
        if match:
            owner = match[1][1:]
            fields[owner] = []
        match = re.search(r'UPROPERTY\(.*\)\s+.+?\s+(\w+)\s*(?:=|;)', line)
        if match and owner:
            name = match[1]
            if name.startswith('b') and len(name) > 1 and name[1].isupper():
                name = name[1:]
            fields[owner].append(re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower())
    return fields


def snapshot(value):
    import unreal
    fields = struct_fields()

    def visit(v):
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        if isinstance(v, unreal.Object):
            return v.get_path_name()
        if type(v).__name__ in fields:
            return {p: visit(v.get_editor_property(p)) for p in fields[type(v).__name__]}
        if hasattr(v, 'items'):
            return {str(k): visit(x) for k, x in v.items()}
        if isinstance(v, (list, tuple, unreal.Array, unreal.Set)):
            return [visit(x) for x in v]
        return str(v)
    return visit(value)


def _input(value):
    return str(value).split('.', 1)[-1].split(':', 1)[0].rstrip('>')


def apply_to_copies(original, plan=None):
    """In-memory copies only; also used at the end of base authoring passes."""
    plan = plan or native.run()
    moves = {key: value.copy() for key, value in original.items()}
    names = {str(k): k for k in moves}
    before = snapshot(original)
    for name, records in plan['attacks'].items():
        obj = moves[names[name]]
        windows = [w.copy() for w in obj.get_editor_property('damage_windows')]
        if len(windows) != len(records):
            raise RuntimeError('Expected source hit-window identity missing: ' + name)
        for window, record in zip(windows, records):
            window.set_editor_property('damage', record['damage'])
            window.set_editor_property('spirit_gain', record['spirit_gain'])
        obj.set_editor_property('damage_windows', windows)
    for name, record in plan['gain_only'].items():
        obj = moves[names[name]]
        windows = [w.copy() for w in obj.get_editor_property('damage_windows')]
        if len(windows) != 1:
            raise RuntimeError('Expected single gain-only window: ' + name)
        windows[0].set_editor_property('spirit_gain', record['spirit_gain'])
        obj.set_editor_property('damage_windows', windows)
    for name, values in [('IaiSpiritSlash', plan['iai_first_hit'])]:
        obj = moves[names[name]]
        windows = [w.copy() for w in obj.get_editor_property('damage_windows')]
        if len(windows) != 1:
            raise RuntimeError('Unexpected existing hit count for ' + name)
        values = {int(k): v for k, v in values.items()}
        for window in windows:
            window.set_editor_property('damage', values[0]['damage'])
            window.set_editor_property('spirit_level_damage', {k: v['damage'] for k, v in values.items()})
        obj.set_editor_property('damage_windows', windows)
    # B14 moved shell damage out of landing montage windows. Rebuilding must not
    # reintroduce the old seven adapters; source shell values remain in native.run().
    if len(moves[names['HelmLand']].get_editor_property('damage_windows')) != 0:
        raise RuntimeError('HelmLand must use the B14 delayed-shell queue, not direct windows')
    for name, source in plan['spirit_costs'].items():
        moves[names[name]].set_editor_property('spirit_cost', source['value'])
    for change in plan['route_changes']:
        obj = moves[names[change['move']]]
        routes, matches = [], 0
        for old in obj.get_editor_property('routes'):
            route = old.copy()
            if _input(route.get_editor_property('input')) == change['input']:
                matches += 1
                if change['operation'] == 'remove':
                    continue
                target = str(route.get_editor_property('next_move'))
                if target not in [change['old'], change['target']]:
                    raise RuntimeError('Preserving unrecognised route edit: ' + change['move'])
                route.set_editor_property('next_move', change['target'])
            routes.append(route)
        if change['operation'] != 'remove' and matches != 1:
            raise RuntimeError('Expected exactly one route: ' + change['move'])
        obj.set_editor_property('routes', routes)

    after = snapshot(moves)
    # Full-structure guard: only these exact fields may differ, including every
    # otherwise unknown future UPROPERTY parsed from the current C++ declaration.
    protected_before, protected_after = copy.deepcopy(before), copy.deepcopy(after)
    for name in list(plan['attacks']) + ['IaiSpiritSlash', 'HelmLand']:
        for data in [protected_before, protected_after]:
            for window in data[name]['damage_windows']:
                for field in ['damage', 'spirit_gain', 'spirit_level_damage']:
                    window.pop(field, None)
    for data in [protected_before, protected_after]:
        for name in plan['spirit_costs']:
            data[name].pop('spirit_cost')
        for name in plan['gain_only']:
            for window in data[name]['damage_windows']:
                window.pop('spirit_gain')
    for change in plan['route_changes']:
        expected = copy.deepcopy(before[change['move']]['routes'])
        expected = [r for r in expected if not (change['operation'] == 'remove'
                    and _input(r['input']) == change['input'])]
        if change['operation'] == 'retarget':
            for route in expected:
                if _input(route['input']) == change['input']:
                    route['next_move'] = change['target']
        if expected != after[change['move']]['routes']:
            raise RuntimeError('Route prerequisites/timing changed: ' + change['move'])
        protected_before[change['move']].pop('routes', None)
        protected_after[change['move']].pop('routes', None)
    if protected_before != protected_after:
        raise RuntimeError('B01 changed a field outside its approved source-qualified scope')
    return moves, dict(before=before, after=after, protected_fields_unchanged=True)


def run(save=False):
    import unreal
    # LevelEditor UI does not exist in Python commandlets; querying its PIE
    # state there can crash in native code before Python can catch an error.
    commandlet = '-run=pythonscript' in unreal.SystemLibrary.get_command_line().lower()
    if not commandlet and unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before writing the formal moveset')
    # Reflection guard before touching any UObject property.
    unreal.MHWIHitWindow().get_editor_property('spirit_level_damage')
    plan = native.run()
    data = unreal.load_asset(DATA)
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Wrong formal DataAsset type')
    path = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    before_sha = native.sha(path)
    moves, report = apply_to_copies(data.get_editor_property('moves'), plan)
    # A second in-memory application must have exactly the same result.
    again, second = apply_to_copies(moves, plan)
    if report['after'] != second['after']:
        raise RuntimeError('B01 source import is not idempotent')
    report.update(saved=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_fingerprints=plan['sources'], disk_sha256_before=before_sha,
                  idempotent=True, unchanged_timing=True, boundaries=plan['untouched'])
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
    elif native.sha(path) != before_sha:
        raise RuntimeError('Preview wrote a disk asset')
    report['disk_sha256_after'] = native.sha(path)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('authored.json' if save else 'preview.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return dict(saved=save, idempotent=True, protected_fields_unchanged=True,
                source_attack_moves=len(plan['attacks']), color_moves=1,
                route_changes=len(plan['route_changes']), step_cost=plan['spirit_step_cost']['value'])
