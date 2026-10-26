"""Verify B01 original-file parsing and known bindings without launching UE."""
from pathlib import Path
import json
import struct

import native_reference_basics as native


def run():
    plan = native.run()
    layout = json.loads(native.LAYOUT.read_text(encoding='utf-8'))
    fields_checked = 0
    for table in [plan['melee'], plan['shell']]:
        raw = (native.ROOT / table['path']).read_bytes()
        for record in table['records']:
            encoded = b''
            for declaration in layout['fields']:
                value = record['fields'][declaration['name']]
                encoded += struct.pack('<' + native.FORMATS[declaration['type']], value['value'])
                fields_checked += 1
            start = record['offset']
            assert encoded == raw[start:start + table['record_size']], (table['path'], record['index'])
    # Independent, version-qualified original values, not DataAsset readback.
    golden = {'StepSlash': ([24.], [26.]), 'OverheadSlash': ([21.], [23.]),
              'Thrust': ([12.], [12.]), 'SpiritComboThrust': ([12.], [12.]),
              'RisingSlash': ([18.], [12.]), 'FadeSlash': ([22.], [26.]),
              'SpiritIII': ([14., 19., 34.], [0., 0., 0.]),
              'IaiSlash': ([18., 13.], [0., 0.]), 'SpiritThrust': ([26.], [10.])}
    for name, (damage, gain) in golden.items():
        assert [r['damage'] for r in plan['attacks'][name]] == damage, name
        assert [r['spirit_gain'] for r in plan['attacks'][name]] == gain, name
    assert [v['value'] for v in plan['spirit_costs'].values()] == [15., 15., 20., 25., 20.]
    assert [v['damage'] for v in plan['iai_first_hit'].values()] == [17., 19., 31., 39.]
    assert [v['damage'] for v in plan['helm_hit'].values()] == [10., 15., 25.]
    assert plan['gain_only']['SpiritStepSlash']['spirit_gain'] == 10.
    # Cross-check the previous independent extraction when it is available.
    previous = native.ROOT / 'Saved/MHWIReview-20261024/native-attack-reference.json'
    compared = 0
    if previous.exists():
        old = json.loads(previous.read_text(encoding='utf-8'))
        for kind in ['melee', 'shell']:
            for new, original in zip(plan[kind]['records'], old[kind], strict=True):
                assert new['offset'] == original['_offset']
                assert new['fields']['Motion_Value']['value'] == original['Motion Value']
                assert new['fields']['Energy_Gen']['value'] == original['Energy Gen']
                compared += 1
    report = dict(passed=True, original_records=75, field_roundtrips=fields_checked,
                  independent_previous_records_compared=compared, golden_move_cases=len(golden),
                  source_build=plan['sources']['source_build'], source_fingerprints=plan['sources'],
                  boundary='Raw source layout/known mapping check; not gameplay or timing verification')
    native.OUT.mkdir(parents=True, exist_ok=True)
    (native.OUT / 'source-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {k: report[k] for k in ['passed','original_records','field_roundtrips','independent_previous_records_compared']}


if __name__ == '__main__':
    print(json.dumps(run()))
