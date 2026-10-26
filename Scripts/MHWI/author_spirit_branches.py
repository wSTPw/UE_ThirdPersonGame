"""B02 copied-structure import; no guessed timings or broad asset rebuild."""
import copy
import datetime
import json
import shutil

import native_spirit_branches as native
from author_reference_basics import snapshot, _input

ROOT, OUT = native.ROOT, native.OUT
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'


def apply_to_copies(original, plan=None):
    import unreal
    plan = plan or native.run()
    moves = {k: v.copy() for k,v in original.items()}
    names = {str(k): k for k in moves}
    before = snapshot(original)
    step = moves[names['SpiritStepSlash']]
    values = plan['spirit_step']
    if float(step.get_editor_property('spirit_cost')) != values['cost']:
        raise RuntimeError('Qualify/import original SpiritStepSlash cost before B02')
    if float(moves[names['SpiritIII']].get_editor_property('spirit_cost')) != plan['required_spirit_iii_cost']:
        raise RuntimeError('Preserving modified SpiritIII cost; source qualification required')
    # Also qualify the fallback I from its original records. Its current values
    # already match, but base authoring must not reset it to an unaffordable I.
    for name, source in [('SpiritStepSlash', values), ('SpiritI', plan['spirit_i'])]:
        definition = moves[names[name]]
        if float(definition.get_editor_property('spirit_cost')) != source['cost']:
            raise RuntimeError('Qualify original cost before B02: '+name)
        definition.set_editor_property('allow_weak_spirit_attack', True)
        definition.set_editor_property('weak_damage_multiplier', source['weak_multiplier'])
        definition.set_editor_property('weak_spirit_gain', source['gain'])
        windows = [w.copy() for w in definition.get_editor_property('damage_windows')]
        if len(windows) != 1 or windows[0].get_editor_property('spirit_level_damage'):
            raise RuntimeError('Expected single, non-color source hit: '+name)
        windows[0].set_editor_property('damage', source['strong_damage'])
        windows[0].set_editor_property('spirit_gain', source['gain'])
        definition.set_editor_property('damage_windows', windows)

    # A and B share one source condition. Reuse the pre-existing project A window.
    routes = [r.copy() for r in step.get_editor_property('routes')]
    light = [r for r in routes if _input(r.get_editor_property('input')) == 'LIGHT']
    other = [r for r in routes if _input(r.get_editor_property('input')) == 'THRUST']
    if len(light) != 1 or len(other) > 1:
        raise RuntimeError('Unexpected step insertion route shape')
    if str(light[0].get_editor_property('next_move')) not in ['Thrust', 'SpiritComboRisingSlash']:
        raise RuntimeError('Preserving unknown step Light target')
    light[0].set_editor_property('next_move', 'SpiritComboRisingSlash')
    secondary = light[0].copy()
    secondary.set_editor_property('input', unreal.MHWIInput.THRUST)
    if other and snapshot(other[0]) != snapshot(secondary):
        raise RuntimeError('Preserving a custom step B route/window')
    result = []
    for route in routes:
        command = _input(route.get_editor_property('input'))
        if command == 'THRUST':
            continue
        result.append(route)
        if command == 'LIGHT':
            result.append(secondary)
    step.set_editor_property('routes', result)

    thrust = moves[names['SpiritComboThrust']]
    routes = []
    for route in thrust.get_editor_property('routes'):
        if _input(route.get_editor_property('input')) == 'THRUST':
            if str(route.get_editor_property('next_move')) != 'RisingSlash':
                raise RuntimeError('Preserving unknown insertion Thrust B target')
            continue
        routes.append(route.copy())
    thrust.set_editor_property('routes', routes)

    rising = moves[names['SpiritComboRisingSlash']]
    routes = [r.copy() for r in rising.get_editor_property('routes')]
    spirit = [r for r in routes if _input(r.get_editor_property('input')) == 'SPIRIT']
    primary = [r for r in spirit if str(r.get_editor_property('next_move')) == 'SpiritIII']
    fallback = [r for r in spirit if str(r.get_editor_property('next_move')) == 'SpiritI']
    if len(primary) != 1 or len(fallback) > 1 or len(spirit) != 1 + len(fallback):
        raise RuntimeError('Preserving unrecognised insertion Spirit routes')
    primary[0].set_editor_property('require_full_spirit_cost', True)
    second = primary[0].copy()
    second.set_editor_property('next_move', 'SpiritI')
    second.set_editor_property('require_full_spirit_cost', False)
    if fallback and snapshot(fallback[0]) != snapshot(second):
        raise RuntimeError('Preserving custom fallback window/prerequisites')
    result = []
    for route in routes:
        if _input(route.get_editor_property('input')) == 'SPIRIT' and str(route.get_editor_property('next_move')) == 'SpiritI':
            continue
        result.append(route)
        if _input(route.get_editor_property('input')) == 'SPIRIT':
            result.append(second)
    rising.set_editor_property('routes', result)
    after = snapshot(moves)

    # Check all unrelated UPROPERTY values and all existing timing/prerequisites.
    a, b = copy.deepcopy(before), copy.deepcopy(after)
    for data in [a,b]:
        for name in ['SpiritStepSlash','SpiritI']:
            for key in ['allow_weak_spirit_attack','weak_damage_multiplier','weak_spirit_gain']:
                data[name].pop(key)
            data[name]['damage_windows'][0].pop('damage')
            data[name]['damage_windows'][0].pop('spirit_gain')
    expected = copy.deepcopy(before['SpiritStepSlash']['routes'])
    old_a = next(r for r in expected if _input(r['input']) == 'LIGHT')
    old_a['next_move'] = 'SpiritComboRisingSlash'
    expected = [r for r in expected if _input(r['input']) != 'THRUST']
    clone = copy.deepcopy(old_a)
    clone['input'] = str(unreal.MHWIInput.THRUST)
    expected.insert(expected.index(old_a)+1,clone)
    if expected != after['SpiritStepSlash']['routes']:
        raise RuntimeError('Unexpected step timing/prerequisite change')
    expected = [r for r in before['SpiritComboThrust']['routes'] if _input(r['input']) != 'THRUST']
    if expected != after['SpiritComboThrust']['routes']:
        raise RuntimeError('Unexpected insertion Thrust change')
    expected = [copy.deepcopy(r) for r in before['SpiritComboRisingSlash']['routes']
                if not (_input(r['input']) == 'SPIRIT' and r['next_move'] == 'SpiritI')]
    row = next(r for r in expected if _input(r['input']) == 'SPIRIT')
    row['require_full_spirit_cost'] = True
    clone = copy.deepcopy(row)
    clone.update(next_move='SpiritI',require_full_spirit_cost=False)
    expected.insert(expected.index(row)+1,clone)
    if expected != after['SpiritComboRisingSlash']['routes']:
        raise RuntimeError('Unexpected ordered resource route change')
    for name in ['SpiritStepSlash','SpiritComboThrust','SpiritComboRisingSlash']:
        a[name].pop('routes');b[name].pop('routes')
    if a != b:
        raise RuntimeError('B02 changed an unrelated field')
    return moves, dict(before=before,after=after,protected_fields_unchanged=True)


def run(save=False):
    import unreal
    commandlet = '-run=pythonscript' in unreal.SystemLibrary.get_command_line().lower()
    if not commandlet and unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before B02 migration')
    unreal.MHWIRoute().get_editor_property('require_full_spirit_cost')
    plan = native.run()
    data = unreal.load_asset(DATA)
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Wrong formal data asset')
    path = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    digest = native.basics.sha(path)
    moves,report = apply_to_copies(data.get_editor_property('moves'),plan)
    again,second = apply_to_copies(moves,plan)
    if report['after'] != second['after']:
        raise RuntimeError('B02 is not idempotent')
    report.update(saved=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  disk_sha256_before=digest,idempotent=True,source_plan=plan,boundaries=plan['boundaries'])
    if save:
        backup = OUT / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(path,backup)
        data.set_editor_property('moves',moves)
        if not unreal.EditorAssetLibrary.save_loaded_asset(data,only_if_is_dirty=False):
            raise RuntimeError('B02 data asset save failed')
        if snapshot(data.get_editor_property('moves')) != report['after']:
            raise RuntimeError('B02 readback failed')
        report['saved'] = True
    elif native.basics.sha(path) != digest:
        raise RuntimeError('B02 preview wrote an asset')
    report['disk_sha256_after'] = native.basics.sha(path)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/('authored.json' if save else 'preview.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dict(saved=save,idempotent=True,protected_fields_unchanged=True,
                weak=plan['spirit_step']['weak_damage'],strong=plan['spirit_step']['strong_damage'],
                routes=sum(len(v['routes']) for v in report['after'].values()))
