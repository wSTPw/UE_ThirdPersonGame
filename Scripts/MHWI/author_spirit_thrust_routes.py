"""Append three routes; preserve all other fields. Editor authoring, never PIE."""
import hashlib
import json
from pathlib import Path
import shutil
import unreal

NAMES = ('SpiritI', 'SpiritII', 'SpiritIII')
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'


def editor_state():
    """Read user work before a compile; never saves or ends PIE."""
    return dict(pie=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(),
                dirty_content=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
                dirty_maps=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()])


def run(save=False):
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('User owns game testing: stop PIE before asset authoring')
    root = Path(unreal.Paths.project_dir()).resolve()
    out = root / 'Saved/MHWIRestoration/B24-20261030'
    out.mkdir(parents=True, exist_ok=True)
    data = unreal.load_asset(DATA)
    assert isinstance(data, unreal.MHWIMovesetData)
    original = dict(data.get_editor_property('moves'))
    names = {str(k): k for k in original}
    assert 'SpiritThrust' in names
    profile = json.loads((root / 'Scripts/MHWI/transition_calibration.json').read_text(encoding='utf-8'))
    before = {k: v.export_text() for k, v in original.items()}
    patched = {k: v.copy() for k, v in original.items()}
    report = dict(asset=data.get_path_name(), saved=False, rows=[], exact_native_frames=False)
    for name in NAMES:
        definition = patched[names[name]]
        routes = list(definition.get_editor_property('routes'))
        existing = [r for r in routes if r.get_editor_property('input') == unreal.MHWIInput.HELM_BREAKER]
        assert len(existing) <= 1, name + ': ambiguous route priority'
        window = next(r['frames'] for r in profile['moves'][name]['rules'] if r['input'] == 'HELM_BREAKER')
        if existing:
            route = existing[0]
            assert str(route.get_editor_property('next_move')) == 'SpiritThrust'
        else:
            route = unreal.MHWIRoute()
            route.set_editor_property('input', unreal.MHWIInput.HELM_BREAKER)
            route.set_editor_property('next_move', 'SpiritThrust')
            route.set_editor_property('require_drawn', True)
            route.set_editor_property('cancel_start', window[0] / 60.)
            route.set_editor_property('cancel_end', window[1] / 60.)
            routes.append(route)
            definition.set_editor_property('routes', routes)
        assert not route.get_editor_property('require_hit')
        assert not route.get_editor_property('require_counter')
        assert not route.get_editor_property('project_adaptation')
        assert abs(float(route.get_editor_property('cancel_start')) - window[0] / 60.) < 1e-5
        assert abs(float(route.get_editor_property('cancel_end')) - window[1] / 60.) < 1e-5
        guard = definition.copy()
        guard.set_editor_property('routes', original[names[name]].get_editor_property('routes'))
        assert guard.export_text() == before[names[name]], name + ': unrelated field changed'
        report['rows'].append(dict(move=name, target='SpiritThrust', frames=window,
                                   route_count_before=len(original[names[name]].get_editor_property('routes')),
                                   route_count_after=len(routes)))
    changed = any(patched[k].export_text() != before[k] for k in original)
    for k in original:
        if str(k) not in NAMES:
            assert patched[k].export_text() == before[k]
    if save and changed:
        disk = root / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup = out / 'Backup/DA_MHWI_LongSword.uasset'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(disk, backup)
        report['before_sha256'] = hashlib.sha256(disk.read_bytes()).hexdigest()
        data.set_editor_property('moves', patched)
        assert unreal.EditorAssetLibrary.save_loaded_asset(data, False)
        report['saved'] = True
        report['after_sha256'] = hashlib.sha256(disk.read_bytes()).hexdigest()
    actual = dict(data.get_editor_property('moves'))
    if save:
        assert all(actual[k].export_text() == patched[k].export_text() for k in patched)
    report['changed'] = changed
    report['readback'] = bool(save)
    (out / ('routes-saved.json' if save else 'routes-preview.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report
