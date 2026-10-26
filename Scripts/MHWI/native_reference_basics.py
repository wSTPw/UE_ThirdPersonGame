"""B01 source values: parse pinned original COL/W03P/FSM, never editable exports.

This module has no Unreal dependency. Unknown timing/geometry/conditional attack
consumers remain unmodified. Source numbers carry their original byte offsets.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct

import extract_native_longsword_params as w03p
from read_source_fsm import XfsReader

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / 'Tools/MHW/native-reference-sources.json'
LAYOUT = ROOT / 'Tools/MHW/native-combat-layout.json'
OUT = ROOT / 'Saved/MHWIRestoration/B01-20261024'
FORMATS = {'UInt32': 'I', 'UInt16': 'H', 'Byte': 'B', 'SByte': 'b', 'Single': 'f'}

# Semantic record bindings, not replacement values. The original records are
# checked by names/UIDs below; all MV/gain/cost numbers come from the binaries.
MELEE_BINDINGS = {
    'StepSlash': [8], 'DrawSlash': [8], 'RollStepSlash': [8],
    'OverheadSlash': [9], 'Thrust': [10], 'SpiritComboThrust': [11],
    'RisingSlash': [12], 'SpiritComboRisingSlash': [12],
    'FadeSlash': [13], 'FadeSlashLeft': [14], 'FadeSlashRight': [14],
    'SpiritIII': [18, 23, 24], 'IaiSlash': [43, 44], 'SpiritThrust': [27],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def percent(value):
    return float(format(value * 100., '.7g'))


def load_sources():
    pin = json.loads(PIN.read_text(encoding='utf-8'))
    if sha(LAYOUT) != pin['layout_sha256']:
        raise ValueError('Combat layout changed; qualify the new layout before applying')
    for name, source in pin['files'].items():
        path = ROOT / source['project_path']
        if path.stat().st_size != source['bytes'] or sha(path) != source['sha256']:
            raise ValueError('Original source fingerprint mismatch: ' + name)
    return pin


def read_collision(path):
    layout = json.loads(LAYOUT.read_text(encoding='utf-8'))
    raw = Path(path).read_bytes()
    if raw[4:8] != b'COL\0':
        raise ValueError('Not a qualified COL file')
    count = struct.unpack_from('<I', raw, 20)[0]
    cursor, names = 24, []
    for _ in range(count):
        end = raw.index(0, cursor)
        name = raw[cursor:end].decode('utf-8')
        cursor = end + 1
        geometry, move, unknown, u2, u3, uid = struct.unpack_from('<iiiHBI', raw, cursor)
        names.append(dict(name=name, geometry=geometry, move=move, timeline_uid=uid))
        cursor += 19
    marker = raw.index(b'ATK\0', cursor)
    magic, tag, version, count, kind = struct.unpack_from('<I4sIII', raw, marker - 4)
    if version != 111 or kind != layout['attack_type']:
        raise ValueError('Unqualified ATK version/type')
    size = sum(struct.calcsize('<' + FORMATS[f['type']]) for f in layout['fields'])
    if size != layout['record_size']:
        raise ValueError('Attack record width mismatch')
    cursor, records = marker + 16, []
    for index in range(count):
        start, fields = cursor, {}
        for field in layout['fields']:
            fmt = '<' + FORMATS[field['type']]
            value = struct.unpack_from(fmt, raw, cursor)[0]
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError('Nonfinite original attack field')
            fields[field['name']] = dict(value=value, offset=cursor)
            cursor += struct.calcsize(fmt)
        if fields['Index']['value'] != index or cursor - start != size:
            raise ValueError('Attack index/width mismatch')
        records.append(dict(index=index, offset=start, fields=fields,
                            names=[n for n in names if n['move'] == index]))
    return dict(path=Path(path).relative_to(ROOT).as_posix(), sha256=sha(path),
                kind=kind, count=count, record_size=size, records=records,
                consumed_attack_end=cursor, trailing_bytes=len(raw) - cursor)


def properties(value):
    if isinstance(value, dict):
        if value.get('mPropertyName'):
            return [value['mPropertyName']]
        return sum((properties(v) for v in value.values()), [])
    if isinstance(value, list):
        return sum((properties(v) for v in value), [])
    return []


def source_routes(path):
    source = XfsReader(Path(path).read_bytes()).parse()['root']
    nodes = {n['mId']: n for n in source['mpRootCluster']['mpNodeList']}
    conditions = {c['mName']['mId']: c['mpRootNode']
                  for c in source['mpConditionTree']['mpTreeList']}
    rows = []
    for number in [4, 7, 8, 9, 28]:
        edges = nodes[number]['mpLinkList']
        edges = edges if isinstance(edges, list) else [edges]
        for order, edge in enumerate(edges):
            condition = conditions[edge['mConditionId']]
            rows.append(dict(source=number, destination=edge['mDestinationNodeId'],
                             order=order, condition_id=edge['mConditionId'],
                             operator_raw=condition['mOperator'], properties=properties(condition),
                             condition=condition))
    if any(r['source'] == 4 and r['properties'] == ['○'] for r in rows):
        raise ValueError('Native ordinary thrust B rule changed; review required')
    for node in [7, 8, 9]:
        if not any(r['source'] == node and r['destination'] == 4
                   and set(r['properties']) == {'△', '○'} for r in rows):
            raise ValueError('Native Fade Slash continuation changed')
    if not any(r['source'] == 28 and r['destination'] == 11
               and r['properties'] == ['△'] for r in rows):
        raise ValueError('Native Foresight Light continuation changed')
    return rows


def build_plan():
    pin = load_sources()
    source_path = lambda name: ROOT / pin['files'][name]['project_path']
    melee = read_collision(source_path('hm/wp/wp03/collision/wp03.col'))
    shell = read_collision(source_path('hm/wp/wp03/shell/collision/object.col'))
    if melee['count'] != 59 or shell['count'] != 16:
        raise ValueError('Attack table count changed')
    params = w03p.run(source=source_path('hm/wp/wp03/wp03_param.w03p'))
    fields = {row['path']: row for row in params['fields']}
    routes = source_routes(source_path('hm/wp/wp03/wp03_action.fsm'))

    def attack(row, kind):
        return dict(source=kind, record=row['index'], offset=row['offset'],
                    damage=row['fields']['Motion_Value']['value'],
                    spirit_gain=percent(row['fields']['Energy_Gen']['value']),
                    damage_offset=row['fields']['Motion_Value']['offset'],
                    spirit_gain_offset=row['fields']['Energy_Gen']['offset'])

    attacks = {move: [attack(melee['records'][i], 'melee') for i in ids]
               for move, ids in MELEE_BINDINGS.items()}
    iai = {level: attack(melee['records'][46 + level], 'melee') for level in range(4)}
    helm = {level: attack(shell['records'][record], 'shell')
            for level, record in [(1, 8), (2, 4), (3, 0)]}
    cost = fields['Spirit_Jumping_Slash_Cost']
    costs = {move: dict(value=percent(fields[field]['value']), raw=fields[field])
             for move, field in [('SpiritI', 'Spirit_Blade_1_Cost'),
                                 ('SpiritII', 'Spirit_Blade_2_Cost'),
                                 ('SpiritIII', 'Spirit_Blade_3_Cost'),
                                 ('SpiritRoundslash', 'Spirit_Round_Slash_Cost'),
                                 ('SpiritStepSlash', 'Spirit_Jumping_Slash_Cost')]}
    return dict(schema=1, batch='B01', sources=pin, melee=melee, shell=shell,
                attacks=attacks, gain_only={'SpiritStepSlash': attack(melee['records'][6], 'melee')},
                iai_first_hit=iai, helm_hit=helm,
                spirit_step_cost=dict(value=percent(cost['value']), raw=cost), spirit_costs=costs,
                native_routes=routes,
                route_changes=[dict(move='Thrust', input='THRUST', operation='remove'),
                               *[dict(move=m, input='LIGHT', operation='retarget',
                                      old='RisingSlash', target='Thrust')
                                 for m in ['FadeSlash', 'FadeSlashLeft', 'FadeSlashRight']],
                               dict(move='ForesightSlash', input='LIGHT', operation='retarget',
                                    old='OverheadSlash', target='StepSlash')],
                untouched=['all timing, collision geometry, Montage/sequence references',
                           'SpiritStepSlash conditional 18/28 consumer',
                           'Iai additional shell, Helm shell origin/geometry/lifetime',
                           'Q decay period, ten-second consumer, roundslash clear commit',
                           'input combinations, native buffering, connectors, turn tuning'])


def run():
    plan = build_plan()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'native-reference-plan.json').write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return plan


if __name__ == '__main__':
    p = run()
    print(json.dumps(dict(attacks=len(p['attacks']), routes=len(p['route_changes']),
                          step_cost=p['spirit_step_cost']['value'], output=str(OUT)), ensure_ascii=False))
