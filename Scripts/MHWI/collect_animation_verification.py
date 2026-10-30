"""Retain bounded B20 runtime evidence outside ignored Saved directories.

This collects existing actual reports and fingerprints; it never runs tests or
turns missing/failed reports into success. Per-tick samples remain in Saved.
"""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'Saved/MHWIRestoration/B20-20261027'
OUT = ROOT / 'Tools/MHW/b20-animation-runtime-evidence.json'


def fingerprint(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size)


def main():
    build = BATCH / 'build-playback-diagnostic.log'
    reports = []
    for name in ('PIE-r06-repairs.json', 'PIE-r06-impact-matrix.json', 'PIE-animation-consumers.json',
                 'PIE-animation-15fps.json', 'PIE-animation-capture.json', 'PIE-weapon-transfer-30fps.json',
                 'PIE-r06-connections.json', 'PIE-r06-prefix-lifecycle.json', 'PIE-r06-weak-adoption.json'):
        path = BATCH / name
        if path.stat().st_mtime < build.stat().st_mtime:
            raise AssertionError('Report predates the final C++ build: ' + name)
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('passed') is not True or any(row.get('passed') is not True for row in data['checks']):
            raise AssertionError('Unsuccessful actual report: ' + name)
        row = dict(source=fingerprint(path), passed=True, checks=data['checks'], check_count=len(data['checks']),
                   source_modified_utc=datetime.datetime.fromtimestamp(path.stat().st_mtime, datetime.timezone.utc).isoformat())
        row.update({key: data[key] for key in ('utc', 'scope', 'requested_max_fps', 'terrain_test_bone', 'cases') if key in data})
        if name in {'PIE-weapon-transfer-30fps.json', 'PIE-r06-prefix-lifecycle.json'}:
            # Preserve every distinct assertion and repetition count, without
            # copying thousands of identical per-frame assertions into Git.
            unique = {}
            for check in data['checks']:
                key = check['check']
                if key not in unique:
                    unique[key] = dict(check, repetitions=0)
                unique[key]['repetitions'] += 1
            row['checks'] = list(unique.values())
            row['unique_assertions'] = len(unique)
        if name == 'PIE-weapon-transfer-30fps.json':
            row.update(max_fps=data['max_fps'], elapsed_seconds=data['elapsed_seconds'],
                       strict_source_hold=data['strict_source_hold'], notes=data['notes'],
                       observed_weapon_motions=sorted({r['motion_no'] for r in data['samples']['weapon_frames']}),
                       action_samples=data['samples']['weapon_actions'])
        reports.append(row)
    if 'Result: Succeeded' not in build.read_text(encoding='utf-8', errors='replace'):
        raise AssertionError('Final reflected C++ build not successful')
    readback = json.loads((BATCH / 'assets-final-readback.json').read_text(encoding='utf-8'))
    if readback.get('passed') is not True:
        raise AssertionError('Actual asset readback failed')
    protected = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    before = json.loads((BATCH / 'before.json').read_text(encoding='utf-8'))
    original = next(row['sha256'] for row in before['files'] if row['path'] == protected.relative_to(ROOT).as_posix())
    if fingerprint(protected)['sha256'] != original:
        raise AssertionError('Protected formal moveset changed')
    capture = json.loads((BATCH / 'PIE-animation-capture.json').read_text(encoding='utf-8'))
    screenshots = [fingerprint(Path(row['path'])) for row in capture['checks'] if 'path' in row]
    if len(screenshots) != 3:
        raise AssertionError('Three actual multi-view files required')
    sources = [ROOT / 'Source/IntroCpp/MHWI' / name for name in
               ('MHWICharacter.h', 'MHWICharacter.cpp', 'MHWICharacterLinkMotion.cpp', 'MHWIAnimInstance.h', 'MHWIAnimInstance.cpp')]
    if any(path.stat().st_mtime > build.stat().st_mtime for path in sources):
        raise AssertionError('C++ was edited after the recorded build; rebuild and rerun affected verification')
    coverage_path = ROOT / 'Tools/MHW/b20-r06-runtime-coverage.json'
    coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
    if not coverage.get('passed') or coverage['runtime_references'] != 31 or coverage['static_negative_references'] != 1:
        raise AssertionError('Actual per-reference adjudication missing')
    out = dict(schema=1, batch='B20-20261027', collected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               scope='Actual UE project consumers; 31 representative R06 pipelines plus orphan negative, not complete incoming identities or original-game certification',
               build=dict(**fingerprint(build), target='IntroCppEditor Win64 Development UE5.8', result='Succeeded'),
               sources=[fingerprint(path) for path in sources], protected_moveset=dict(**fingerprint(protected), unchanged=True),
               asset_readback=readback, reports=reports, screenshots=screenshots, r06_coverage=fingerprint(coverage_path),
               visual_review='Three unique files inspected: same held SpecialSheathe pose at independent camera angles. Frozen capture does not verify timing or every skin vertex.',
               excluded_visual_run='PIE-animation-capture-superseded-visualqa.json: stale files/incorrect views; not used as visual evidence',
               remaining=['native mode0 MotionTree/request', 'full N53/N60 source identities and phase boundaries; forward-roll18/19 ownership remains ambiguous',
                          'real Action78/node51 owner for332/333/334', 'full native locomotion FSM/physics/landing',
                          'native IK solver spaces/limits/manager/CTM'])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(reports=len(reports), checks=sum(row['check_count'] for row in reports),
                          protected_moveset_unchanged=True, output=OUT.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
