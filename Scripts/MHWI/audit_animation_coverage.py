"""Build a complete R06/R28/R30 animation disposition ledger.

Static coverage is not runtime verification. Optional decisions only record what
was actually implemented or inspected; runtime status must come from PIE reports.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIRestoration/B19-20261026'
DECISIONS_PATH = ROOT / 'Tools/MHW/animation-coverage-decisions.json'


def load_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    policy = load_json(ROOT / 'Tools/MHW/native-link-motion-policy.json')
    decisions = load_json(DECISIONS_PATH, {})
    weapon_report = load_json(OUT / 'weapon-motion-coverage.json', {})
    rows = []

    def add(group, item, asset, status, note):
        row = {'group': group, 'id': item, 'asset': asset, 'status': status, 'note': note}
        decision = decisions.get(item)
        if decision:
            row.update({key: value for key, value in decision.items() if key in {'status', 'note', 'verification'}})
        rows.append(row)

    for ref in policy['references']:
        item = ref['id']
        connector = int(ref['connector_motion'])
        asset = f"Content/MHWI/Animations/R06Staging/A_w03_00_{connector:03d}.uasset"
        if item == 'R06-N86-P0':
            status, note = 'preserved_unreachable', 'Original graph has zero incoming edges/records; do not fabricate an entry.'
        elif item in {'R06-N53-P0', 'R06-N60-P0', 'R06-N60-P1'}:
            status, note = 'partial_source_coverage', 'Blend/A01 code repaired; full node0/node26 source-owner coverage and runtime remain open.'
        else:
            status, note = 'code_repaired_pending_runtime', 'Weapon mode0 project blend fallback added; native mode0 semantics and per-reference PIE remain open.'
        add('R06', item, asset, status, note)

    remaining = ROOT / 'Content/MHWI/Animations/R06Remaining'
    for asset in sorted(remaining.glob('*.uasset')):
        motion = int(asset.stem.rsplit('_', 1)[1])
        item = f'R06-EXTRA-{asset.stem.removeprefix("A_").upper()}'
        if motion in {332, 333, 334}:
            status, note = 'blocked_missing_source', 'Action78/node51 source owner is absent; do not alias another move.'
        else:
            status, note = 'code_repaired_pending_runtime', 'Asset exists; blend/source path repaired, but exact runtime identity and PIE coverage are not complete.'
        add('R06', item, str(asset.relative_to(ROOT)), status, note)

    for motion in (181, 182):
        add('R06', f'R06-COMMON-{motion:03d}', f'native common motion {motion}',
            'unprocessed_missing_source', 'No qualified source context/entry; not in the 32 new assets and must not be silently dropped.')

    base_cycles = {
        'R28-BASE-IDLE-DRAWN': 'Content/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_001.uasset',
        'R28-BASE-MOVE-DRAWN': 'Content/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_004.uasset',
        'R28-BASE-IDLE-SHEATHED': 'Content/MHWI/Animations/NativeFidelity/Common/A_co00_00_001.uasset',
        'R28-BASE-WALK-SHEATHED': 'Content/MHWI/Animations/NativeFidelity/Common/A_co00_00_203.uasset',
        'R28-BASE-RUN-SHEATHED': 'Content/MHWI/Animations/NativeFidelity/Common/A_co00_00_090.uasset',
    }
    for item, asset in base_cycles.items():
        add('R28', item, asset, 'existing_pending_regression', 'Existing qualified loop/BlendSpace path; regression evidence is separate from new transitions.')

    for motion in (5, 6, 7, 8, 14, 15):
        item = f'R28-CANDIDATE-{motion:03d}'
        asset = f'Content/MHWI/Animations/LongSword/A_w03_00_{motion:03d}.uasset'
        add('R28', item, asset, 'asset_present_semantics_unconfirmed',
            'Old Sequence exists; NativeFidelity source/LMT qualification and visible state semantics are not closed.')

    selected = set(weapon_report.get('selected_values', []))
    for motion in range(6):
        item = f'R30-WG03-{motion:03d}'
        asset = f'Content/MHWI/Animations/Weapons/A_wg03_00_{motion:03d}.uasset'
        if motion in selected:
            status, note = 'selection_path_found_pending_runtime', 'DA event/default selection exists; actual SingleNode playback still requires PIE evidence.'
        else:
            status, note = 'no_selection_evidence', 'No DA event/default selection found; do not invent a native trigger merely to play the asset.'
        add('R30', item, asset, status, note)

    ik_chains = {
        'LARM': ('larm.ik', 'bone_006/007/008'),
        'RARM': ('rarm.ik', 'bone_010/011/012'),
        'LFOOT': ('lfoot.ik', 'bone_014/015/016'),
        'RFOOT': ('rfoot.ik', 'bone_018/019/020'),
    }
    for label, (filename, bones) in ik_chains.items():
        add('R30', 'R30-IK-' + label,
            'ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/common/ik/' + filename,
            'blocked_no_runtime_consumer', f'Chain {bones} is mapped; native solver spaces/parameters are unresolved and no project IK consumer is active.')

    missing_assets = [row['id'] for row in rows
                      if row['asset'].endswith('.uasset') and not (ROOT / row['asset']).exists()]
    for row in rows:
        row['asset_exists'] = not (row['asset'].endswith('.uasset') and not (ROOT / row['asset']).exists())

    report = {
        'scope': 'Static disposition ledger; statuses are not automatic runtime proof.',
        'counts_by_group': dict(Counter(row['group'] for row in rows)),
        'counts_by_status': dict(Counter(row['status'] for row in rows)),
        'missing_assets': missing_assets,
        'rows': rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'animation-coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# R06 / R28 / R30 动画覆盖台账', '',
             '静态处置清单；不是运行通过证明。', '',
             '| 对象 | ID | 状态 | 资产 | 说明 |', '| --- | --- | --- | --- | --- |']
    for row in rows:
        lines.append('| {group} | {id} | {status} | `{asset}` | {note} |'.format(**row))
    lines += ['', '缺资产：' + (', '.join(missing_assets) if missing_assets else '无'),
              '', '计数：' + json.dumps(report['counts_by_group'], ensure_ascii=False)]
    (OUT / 'animation-coverage.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'rows': len(rows), 'counts_by_group': report['counts_by_group'],
                      'counts_by_status': report['counts_by_status'], 'missing_assets': missing_assets,
                      'output': str(OUT / 'animation-coverage.json')}, ensure_ascii=False, indent=2))
    if missing_assets:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
