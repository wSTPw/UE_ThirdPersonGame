"""B03: promote qualified native loops without inventing locomotion parameters."""
import hashlib
import json
from pathlib import Path
import shutil
import unreal
import author_reference_basics as basics

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / 'Saved/MHWIRestoration/B03-20261024'
MANIFEST = ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json'
MANIFEST_SHA = '2e51719e351ff27a5fed03bc871834212d5df836ae58703ec92656b12e5f913e'
CLIPS = dict(idle='w03_00_001', walk='w03_00_004', run='w03_00_004',
             sheathed_idle='co00_00_001', sheathed_walk='co00_00_203', sheathed_run='co00_00_090')
SETTINGS = ('enable_root_motion', 'force_root_lock', 'root_motion_root_lock', 'rate_scale')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preferred(legacy):
    """Shared by base authoring: qualified loop, otherwise retain legacy clip."""
    if '/NativeFidelity/' in legacy.get_path_name() or legacy.get_name()[2:] not in CLIPS.values():
        return legacy
    path = legacy.get_path_name().split('.')[0]
    path = path.replace('/Animations/', '/Animations/NativeFidelity/', 1)
    result = unreal.load_asset(path)
    if not isinstance(result, unreal.AnimSequence):
        raise RuntimeError('Import qualified native loop first: ' + path)
    return result


def _samples(blend):
    return [dict(animation=s.get_editor_property('animation').get_path_name(),
                 settings=s.export_text().replace(s.get_editor_property('animation').get_path_name(), '<animation>'))
            for s in blend.get_editor_property('sample_data')]


def run(save=False, report_name=None):
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before loop promotion')
    assert digest(MANIFEST) == MANIFEST_SHA, 'Qualification manifest changed; requalify explicitly'
    manifest = json.loads(MANIFEST.read_text(encoding='utf8'))
    for item in manifest['source_dependencies']:
        assert digest(ROOT / item['path']) == item['sha256'], 'Source dependency changed: ' + item['path']
    qualified = {r['clip']: r for r in manifest['clips']}
    data = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
    assert isinstance(data, unreal.MHWIMovesetData)
    skeleton = unreal.load_asset('/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton')
    moves_before = basics.snapshot(data.get_editor_property('moves'))
    targets, fields, sequences = {}, {}, {}
    for field, clip in CLIPS.items():
        row = qualified[clip]
        assert row['eligible_for_runtime'] and row['passed'] and row['bone_count'] == 225
        assert row['source_verification']['passed'] and row['fbx_verification']['passed']
        assert digest(ROOT / row['fbx']) == row['sha256'], 'Qualified FBX changed'
        bank = 'Common' if clip.startswith('co00') else 'LongSword'
        legacy = unreal.load_asset('/Game/MHWI/Animations/' + bank + '/A_' + clip)
        native = preferred(legacy)
        current = data.get_editor_property(field)
        assert current in (legacy, native), 'Unexpected custom reference: ' + field
        assert native.get_editor_property('skeleton') == skeleton == legacy.get_editor_property('skeleton')
        assert abs(native.get_play_length() - row['duration']) < .0001
        assert abs(native.get_play_length() - legacy.get_play_length()) < .0001
        filename = native.get_editor_property('asset_import_data').get_first_filename()
        assert Path(filename).resolve() == (ROOT / row['fbx']).resolve(), 'Unexpected import provenance'
        expected = dict(zip(SETTINGS, (False, True, unreal.RootMotionRootLock.REF_POSE,
                                      legacy.get_editor_property('rate_scale'))))
        before = {p: str(native.get_editor_property(p)) for p in SETTINGS}
        sequences[native.get_path_name()] = (native, expected)
        fields[field] = dict(old=current.get_path_name(), new=native.get_path_name(),
                             duration=native.get_play_length(), settings_before=before,
                             settings_expected={p: str(v) for p, v in expected.items()})
        targets[legacy.get_path_name()] = native
        targets[native.get_path_name()] = native
    blends = []
    for name in ('Drawn', 'Sheathed'):
        blend = unreal.load_asset('/Game/MHWI/Animations/BS_MHWI_' + name)
        assert isinstance(blend, unreal.BlendSpace)
        samples = [s.copy() for s in blend.get_editor_property('sample_data')]
        expected_fields = ('idle', 'walk', 'run') if name == 'Drawn' else ('sheathed_idle', 'sheathed_walk', 'sheathed_run')
        assert len(samples) == len(expected_fields)
        for sample, field in zip(samples, expected_fields):
            old = sample.get_editor_property('animation')
            assert old.get_name() == 'A_' + CLIPS[field] and old.get_path_name() in targets
            sample.set_editor_property('animation', targets[old.get_path_name()])
        blends.append((blend, samples, _samples(blend)))
    changed = []
    def backup(obj):
        path = ROOT / ('Content/' + obj.get_path_name().split('.')[0][6:] + '.uasset')
        dest = OUT / 'Backup' / path.relative_to(ROOT)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        changed.append(obj.get_path_name())
    if save:
        # All qualification checks above finish before the first asset mutation.
        for native, expected in sequences.values():
            if any(native.get_editor_property(p) != v for p, v in expected.items()):
                backup(native)
                for p, v in expected.items(): native.set_editor_property(p, v)
                assert unreal.EditorAssetLibrary.save_loaded_asset(native)
            assert all(native.get_editor_property(p) == v for p, v in expected.items())
        if any(data.get_editor_property(p).get_path_name() != r['new'] for p, r in fields.items()):
            backup(data)
            for p, r in fields.items(): data.set_editor_property(p, unreal.load_asset(r['new']))
            assert unreal.EditorAssetLibrary.save_loaded_asset(data)
        for blend, samples, before in blends:
            if [s.get_editor_property('animation').get_path_name() for s in samples] != [r['animation'] for r in before]:
                backup(blend)
                blend.set_editor_property('sample_data', samples)
                assert unreal.EditorAssetLibrary.save_loaded_asset(blend)
            after = _samples(blend)
            assert [r['settings'] for r in before] == [r['settings'] for r in after], 'Sample configuration changed'
            assert [r['animation'] for r in after] == [s.get_editor_property('animation').get_path_name() for s in samples]
        assert all(data.get_editor_property(p).get_path_name() == r['new'] for p, r in fields.items())
    assert moves_before == basics.snapshot(data.get_editor_property('moves')), 'Action data changed'
    report = dict(saved=save, changed=changed, fields=fields,
                  blends={b.get_path_name(): _samples(b) for b, _, _ in blends},
                  manifest_sha256=MANIFEST_SHA, action_data_unchanged=True,
                  boundary='Loop sampling/reference correction only; existing speed, rates and blending remain project tuning.')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (report_name or ('authored.json' if save else 'preview.json'))).write_text(json.dumps(report, indent=2), encoding='utf8')
    return dict(saved=save, changed=changed, fields=len(fields), clips=len(sequences))
