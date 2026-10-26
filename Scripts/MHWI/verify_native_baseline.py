"""Independent source baseline for the ledger sweep (R33).

This is a static expected-value checker, not a gameplay test. It re-reads the
pinned COL/W03P/FSM bytes, then checks a saved DataAsset snapshot against
values derived from those bytes. It never launches the editor and never writes
an asset.

Usage:
  python Scripts/MHWI/verify_native_baseline.py
  python Scripts/MHWI/verify_native_baseline.py --da Saved/MHWIRestoration/B12-20261026/authored.json
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import extract_native_longsword_params as w03p_module
import native_reference_basics as basics
from read_source_fsm import XfsReader

ROOT = basics.ROOT
DEFAULT_DA = ROOT / 'Saved/MHWIRestoration/B12-20261026/authored.json'
TOL = 1e-4


def _shell_records(path):
    layout = json.loads(basics.LAYOUT.read_text(encoding='utf-8'))
    raw = Path(path).read_bytes()
    marker = raw.index(b'ATK\0', 24)
    magic, tag, version, count, kind = struct_unpack(raw, marker - 4)
    if version != 111 or kind != layout['attack_type']:
        raise ValueError('Shell ATK header mismatch')
    cursor, records = marker + 16, []
    for index in range(count):
        fields = {}
        for field in layout['fields']:
            value = struct.unpack_from('<' + basics.FORMATS[field['type']], raw, cursor)[0]
            fields[field['name']] = value
            cursor += struct.calcsize('<' + basics.FORMATS[field['type']])
        records.append(fields)
    return records


def struct_unpack(raw, offset):
    return struct.unpack_from('<I4sIII', raw, offset)


def _num(value, expected, label, errors):
    if abs(float(value) - float(expected)) > TOL:
        errors.append(f'{label}: got {value}, expected {expected}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--da', type=Path, default=DEFAULT_DA)
    args = parser.parse_args()

    pin = basics.load_sources()
    src = {name: ROOT / value['project_path'] for name, value in pin['files'].items()}
    melee = basics.read_collision(src['hm/wp/wp03/collision/wp03.col'])
    shell = _shell_records(src['hm/wp/wp03/shell/collision/object.col'])
    w03p = {row['path']: row['value'] for row in w03p_module.run()['fields']}
    raw_fsm = src['hm/wp/wp03/wp03_action.fsm'].read_bytes()
    tree = XfsReader(raw_fsm).parse()['root']
    nodes = {node['mId']: node for node in tree['mpRootCluster']['mpNodeList']}
    conditions = {(entry.get('mName') or {}).get('mId'): entry.get('mpRootNode')
                  for entry in tree['mpConditionTree']['mpTreeList']}

    errors, checks = [], []

    def check(label, value, expected):
        _num(value, expected, label, errors)
        checks.append(label)

    # --- source values -----------------------------------------------------
    check('COL#28 aerial MV', melee['records'][28]['fields']['Motion_Value']['value'], 126.0)
    check('COL#25 foresight base', melee['records'][25]['fields']['Motion_Value']['value'], 12.0)
    check('COL#25 conditional', melee['records'][25]['fields']['Conditional_Motion_value_change_replace']['value'], 26.0)
    check('COL#6 step base', melee['records'][6]['fields']['Motion_Value']['value'], 18.0)
    check('COL#6 conditional', melee['records'][6]['fields']['Conditional_Motion_value_change_replace']['value'], 28.0)
    check('COL#15 spirit I base', melee['records'][15]['fields']['Motion_Value']['value'], 14.0)
    check('COL#15 conditional', melee['records'][15]['fields']['Conditional_Motion_value_change_replace']['value'], 26.0)
    check('COL#17 spirit II', melee['records'][17]['fields']['Motion_Value']['value'], 30.0)
    check('COL#19 roundslash', melee['records'][19]['fields']['Motion_Value']['value'], 38.0)
    for index, expected in ((18, 14.0), (23, 19.0), (24, 34.0)):
        check(f'COL#{index} spirit III', melee['records'][index]['fields']['Motion_Value']['value'], expected)
    for index, expected in ((43, 18.0), (44, 13.0)):
        check(f'COL#{index} iai', melee['records'][index]['fields']['Motion_Value']['value'], expected)
    for index, expected in ((46, 17.0), (47, 19.0), (48, 31.0), (49, 39.0)):
        check(f'COL#{index} iai spirit first', melee['records'][index]['fields']['Motion_Value']['value'], expected)

    # Shell order: 0/1/2 red, 4/5/6 yellow, 8/9/10 white, 12/13/14 iai.
    for index in (0, 1, 2):
        check(f'shell#{index} red', shell[index]['Motion_Value'], 25.0)
    for index in (4, 5, 6):
        check(f'shell#{index} yellow', shell[index]['Motion_Value'], 15.0)
    for index in (8, 9, 10):
        check(f'shell#{index} white', shell[index]['Motion_Value'], 10.0)
    for index, expected in ((12, 86.0), (13, 72.0), (14, 55.0)):
        check(f'shell#{index} iai second', shell[index]['Motion_Value'], expected)

    check('W03P decay', w03p['Spirit_Gauge_Decay'], 0.05)
    check('W03P no-decay', w03p['Gauge_No_Decay_Time_after_Spirit_Gauge_Upgrade'], 10.0)
    check('W03P helm first delay', w03p['Helmbreaker_Hit_Delay_of_First_Hit'], 0.4)
    check('W03P helm interval', w03p['Helmbreaker_Hit_Delay_of_Hits_Between_First_Last'], 0.05)
    check('W03P helm limit', w03p['Helmbreaker_Hit_Limit'], 7)
    check('W03P iai second delay', w03p['Iai_Spirit_Slash_Second_Hit_Time_Delay'], 0.5)
    check('W03P white duration', w03p['Gauge_Duration_White'], 195.0)
    check('W03P yellow duration', w03p['Gauge_Duration_Yellow'], 135.0)
    check('W03P red duration', w03p['Gauge_Duration_Red'], 60.0)
    check('W03P iai regen', w03p['Spirit_Regeneration_After_Iai_Slash_Duration_in_Seconds_'], 15.0)
    check('W03P timed iai regen', w03p['Spirit_Regeneration_After_Timed_Iai_Slash_Duration_in_Seconds_'], 30.0)
    check('W03P foresight multiplier', w03p['Foresight_Slash_Damage_Multiplier_on_Successful_Evasion'], 1.3)
    check('W03P iai sheathed time', w03p['Iai_Sheathed_Time'], 3.5)

    # FSM: node65 has exactly one edge, R+triangle -> node76.
    node65 = nodes[65]
    links = node65.get('mpLinkList')
    links = links if isinstance(links, list) else ([links] if isinstance(links, dict) else [])
    if len(links) != 1 or links[0].get('mDestinationNodeId') != 76:
        errors.append('FSM node65 must have exactly one edge to node76')
    checks.append('FSM node65 single edge')
    cond = conditions.get(links[0].get('mConditionId')) if links else None
    if not cond or cond.get('mOperator') != 0:
        errors.append('FSM node65 condition is not the single R+triangle leaf')
    checks.append('FSM node65 R+triangle')

    # --- saved DataAsset ---------------------------------------------------
    if not args.da.exists():
        errors.append(f'DA snapshot missing: {args.da}')
    else:
        snapshot = json.loads(args.da.read_text(encoding='utf-8'))
        moves = snapshot.get('after', snapshot)
        helm = moves.get('SpiritHelmBreaker', {})
        windows = helm.get('damage_windows', [])
        if len(windows) != 1:
            errors.append(f'SpiritHelmBreaker windows: got {len(windows)}, expected 1')
        else:
            window = windows[0]
            check('DA helm start', window['start_time'], 25.0 / 60.0)
            check('DA helm end', window['end_time'], 112.0 / 60.0)
            check('DA helm MV', window['damage'], 126.0)
            if window.get('col_record_index') != 28:
                errors.append('DA helm ColRecordIndex is not 28')
            check('DA helm hit lag', window.get('hit_lag_seconds', 0.0), 0.4)
        checks.append('DA helm window')

        iai = moves.get('IaiSpiritSlash', {}).get('routes', [])
        adaptations = {(r['input'].split('.')[-1].split(':')[0], r['next_move']): r.get('project_adaptation')
                       for r in iai}
        for pair in (('SPIRIT', 'SpiritIII'), ('SPECIAL_SHEATHE', 'SpecialSheathe')):
            if adaptations.get(pair) is not True:
                errors.append(f'Iai adaptation missing: {pair}')
        for pair in (('HELM_BREAKER', 'SpiritThrust'), ('EVADE', 'Roll')):
            if adaptations.get(pair) is True:
                errors.append(f'Iai source exit wrongly marked adaptation: {pair}')
        checks.append('DA Iai adaptation bits')
        if len(iai) != 6:
            errors.append(f'Iai route count: got {len(iai)}, expected 6')

    print(f'checks: {len(checks)}')
    if errors:
        print('RESULT: FAIL')
        for error in errors:
            print(' - ' + error)
        return 1
    print('RESULT: PASS (static source/DataAsset expectations; no PIE)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
