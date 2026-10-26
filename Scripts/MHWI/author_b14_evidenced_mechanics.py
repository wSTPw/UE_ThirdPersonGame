"""B14 source-backed migration for evidenced MHWI mechanics; import is inert.

Only DA globals, SpiritHelmBreaker.HitLagSeconds and HelmLand.DamageWindows are
written. Preview does not mutate the formal asset. Save creates a byte backup,
checks idempotence/full move protection, then saves and reads back the asset.
"""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import shutil
import struct
import sys

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import native_reference_basics as native
from author_reference_basics import snapshot
from verify_native_baseline import _shell_records

ROOT = native.ROOT
OUT = ROOT / 'Saved/MHWIImport/EvidencedMechanics-20261026'
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'
MANIFEST = ROOT / 'Tools/MHW/native-outstanding-evidence.json'
HELM = 'SpiritHelmBreaker'
LAND = 'HelmLand'
EXTERNAL_SOURCES = [
    'https://mhworld.kiranico.com/en/guide/long-sword',
    'https://monsterhunterworld.wiki.fextralife.com/index.php?diff=cur&oldid=16586',
    'https://www.nexusmods.com/monsterhunterworld/mods/5262',
]
GLOBAL_DEFAULTS = {
    'spirit_decay_pause_on_raise_seconds': 10.0,
    'spirit_gauge_decay_time_scale': 120.0,
    'spirit_gauge_decay_fraction': 0.05,
    'helm_shell_first_delay': 0.4,
    'helm_shell_interval': 0.05,
    'helm_shell_hit_limit': 7,
    'iai_shell_delay': 0.5,
    'evasion_mantle_protection_frames': 30.0,
    'special_sheath_hold_seconds': 3.5,
}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_values():
    """Re-read retained resources; use the reviewed manifest for missing PLP/CFG."""
    pin = native.load_sources()
    sources = {name: ROOT / row['project_path'] for name, row in pin['files'].items()}
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    parameters = {row['name']: row for row in manifest['parameters']}
    w03_path = sources['hm/wp/wp03/wp03_param.w03p']
    w03_info = parameters['W03P']
    if _sha(w03_path) != w03_info['source_sha256']:
        raise RuntimeError('Retained W03P no longer matches the reviewed B13 manifest')
    decoded = w03_path.read_bytes()
    # The pinned extractor is used even though the retained file is already decoded.
    import extract_native_longsword_params as w03p
    decoded = w03p.decrypt_resource(w03_path)
    if hashlib.sha256(decoded).hexdigest() != w03_info['decoded_sha256']:
        raise RuntimeError('W03P decoded bytes differ from the reviewed B13 manifest')
    w03 = {}
    for row in w03_info['fields']:
        fmt = '<' + row['format']
        value = struct.unpack_from(fmt, decoded, int(row['offset'], 16))[0]
        if value != row['value']:
            raise RuntimeError('W03P value changed at ' + row['offset'])
        w03[int(row['offset'], 16)] = float(value)

    shell = _shell_records(sources['hm/wp/wp03/shell/collision/object.col'])
    expected_shell = {0: 25., 4: 15., 8: 10., 12: 86., 13: 72., 14: 55.}
    for index, expected in expected_shell.items():
        if abs(shell[index]['Motion_Value'] - expected) > 1e-4:
            raise RuntimeError('Shell MV differs from source at record %d' % index)
    plp = {int(row['offset'], 16): float(row['value']) for row in parameters['PLP']['fields']}
    globals_out = dict(GLOBAL_DEFAULTS)
    globals_out.update({
        'spirit_decay_pause_on_raise_seconds': w03[0x51d],
        'spirit_gauge_decay_time_scale': w03[0x499],
        'spirit_gauge_decay_fraction': w03[0x49d],
        'helm_shell_first_delay': w03[0x5f8],
        'helm_shell_interval': w03[0x5fc],
        'helm_shell_hit_limit': int(w03[0x604]),
        'iai_shell_delay': w03[0x54c],
        'special_sheath_hold_seconds': w03[0x540],
        'evasion_mantle_protection_frames': plp[0x49d],
    })
    globals_out['helm_shell_damage_by_level'] = [0., shell[8]['Motion_Value'],
        shell[4]['Motion_Value'], shell[0]['Motion_Value']]
    globals_out['iai_shell_damage_by_level'] = [0., shell[14]['Motion_Value'],
        shell[13]['Motion_Value'], shell[12]['Motion_Value']]
    globals_out['evasion_protection_frames'] = [plp[0x485 + 4 * i] for i in range(6)]
    evidence = {
        'manifest': MANIFEST.relative_to(ROOT).as_posix(),
        'manifest_boundary': manifest['boundary'],
        'w03p': w03_info,
        'plp': parameters['PLP'],
        'plp_availability': 'reviewed manifest only; original PLP binary is not present in this workspace',
        'shell_records': expected_shell,
        'external_cross_sources': EXTERNAL_SOURCES,
        'not_reexecuted': ['original game', 'native disassembly extraction'],
    }
    return globals_out, evidence


def _global_snapshot(data):
    result = {}
    for key in list(GLOBAL_DEFAULTS) + ['helm_shell_damage_by_level',
            'iai_shell_damage_by_level', 'evasion_protection_frames']:
        value = data.get_editor_property(key)
        result[key] = [float(v) for v in value] if isinstance(value, (list, tuple)) or type(value).__name__.endswith('Array') else value
    return result


def apply_to_copies(original, globals_expected):
    moves = {key: value.copy() for key, value in original.items()}
    names = {str(key): key for key in moves}
    if HELM not in names or LAND not in names:
        raise RuntimeError('Formal moveset lost SpiritHelmBreaker or HelmLand')
    before = snapshot(original)
    helm = moves[names[HELM]]
    windows = [window.copy() for window in helm.get_editor_property('damage_windows')]
    if len(windows) != 1 or int(windows[0].get_editor_property('col_record_index')) != 28:
        raise RuntimeError('Expected the single sourced COL#28 aerial hit before B14')
    windows[0].set_editor_property('hit_lag_seconds', 0.0)
    helm.set_editor_property('damage_windows', windows)
    land = moves[names[LAND]]
    old_land_count = len(land.get_editor_property('damage_windows'))
    if old_land_count not in (0, 7):
        raise RuntimeError('HelmLand has unexpected custom windows; requalify before B14')
    land.set_editor_property('damage_windows', [])
    after = snapshot(moves)

    protected_before, protected_after = copy.deepcopy(before), copy.deepcopy(after)
    protected_before[HELM]['damage_windows'][0].pop('hit_lag_seconds', None)
    protected_after[HELM]['damage_windows'][0].pop('hit_lag_seconds', None)
    protected_before[LAND].pop('damage_windows', None)
    protected_after[LAND].pop('damage_windows', None)
    if protected_before != protected_after:
        raise RuntimeError('B14 changed a move field outside the two declared areas')
    return moves, {
        'before': before,
        'after': after,
        'protected_fields_unchanged': True,
        'old_land_window_count': old_land_count,
        'globals_before': None,
        'globals_after': globals_expected,
    }


def run(save=False):
    import unreal
    commandlet = '-run=pythonscript' in unreal.SystemLibrary.get_command_line().lower()
    if not commandlet and unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before writing the formal moveset')
    for key in ('spirit_gauge_decay_time_scale', 'helm_shell_damage_by_level',
                'iai_shell_damage_by_level', 'evasion_protection_frames'):
        unreal.MHWIMovesetData().get_editor_property(key)
    globals_expected, evidence = source_values()
    data = unreal.load_asset(DATA)
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Wrong formal DataAsset type')
    path = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    before_sha = _sha(path)
    moves, report = apply_to_copies(data.get_editor_property('moves'), globals_expected)
    again, second = apply_to_copies(moves, globals_expected)
    if report['after'] != second['after']:
        raise RuntimeError('B14 authoring is not idempotent')
    report['globals_before'] = _global_snapshot(data)
    report.update(saved=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  idempotent=True, source_evidence=evidence, disk_sha256_before=before_sha)
    if save:
        backup = OUT / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        data.set_editor_property('moves', moves)
        for key, value in globals_expected.items():
            data.set_editor_property(key, value)
        if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
            raise RuntimeError('B14 formal DataAsset save failed')
        if snapshot(data.get_editor_property('moves')) != report['after']:
            raise RuntimeError('B14 move readback differs from preview')
        actual_globals = _global_snapshot(data)
        for key, expected in globals_expected.items():
            actual = actual_globals[key]
            if isinstance(expected, list):
                if len(actual) != len(expected) or any(abs(float(a) - float(b)) > 1e-4 for a, b in zip(actual, expected)):
                    raise RuntimeError('B14 global readback mismatch: ' + key)
            elif abs(float(actual) - float(expected)) > 1e-4:
                raise RuntimeError('B14 global readback mismatch: ' + key)
        report['saved'] = True
    elif _sha(path) != before_sha:
        raise RuntimeError('Preview wrote a disk asset')
    report['disk_sha256_after'] = _sha(path)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('authored.json' if save else 'preview.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'saved': save, 'idempotent': True, 'report': str(OUT),
            'old_land_window_count': report['old_land_window_count']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    print(run(save=args.save))
