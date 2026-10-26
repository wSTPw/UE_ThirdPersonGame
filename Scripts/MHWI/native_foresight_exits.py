"""B05 source evidence: Foresight Slash (node 28) missing exits, read-only.

Parses the pinned original FSM every run and records node 28's complete edge
list. The two exits this batch implements are qualified here:

  * circle (B)      -> node 4  (Thrust)          review R04 "B->thrust"
  * R + triangle    -> node 45 (SpiritThrust)    review R04 "R+A->helm thrust"

Node identities are cross-checked against Scripts/MHWI/moveset_mapping.json.
No timing, geometry or consumer values are invented; the batch reuses existing
adapter cancel windows, per the shared-ledger rule for same-condition routes.
"""
from __future__ import annotations

import json
from pathlib import Path

import native_reference_basics as basics
from read_source_fsm import XfsReader

ROOT = basics.ROOT
OUT = ROOT / 'Saved/MHWIRestoration/B11-20261025'

# FSM node ids of the moves involved, from the project's source mapping.
NODE_FORESIGHT = 28
NODE_THRUST = 4
NODE_SPIRIT_THRUST = 45
NODE_STEP_SLASH = 11


def _edges(source_path, number):
    tree = XfsReader(Path(source_path).read_bytes()).parse()['root']
    nodes = {n['mId']: n for n in tree['mpRootCluster']['mpNodeList']}
    conditions = {c['mName']['mId']: c['mpRootNode']
                  for c in tree['mpConditionTree']['mpTreeList']}
    edges = nodes[number]['mpLinkList']
    edges = edges if isinstance(edges, list) else [edges]
    rows = []
    for order, edge in enumerate(edges):
        condition = conditions[edge['mConditionId']]
        rows.append(dict(source=number, order=order,
                         destination=edge['mDestinationNodeId'],
                         condition_id=edge['mConditionId'],
                         operator=condition['mOperator'],
                         properties=basics.properties(condition)))
    return rows


def build_plan():
    pin = basics.load_sources()  # raises on any source fingerprint change
    fsm = ROOT / pin['files']['hm/wp/wp03/wp03_action.fsm']['project_path']
    edges = _edges(fsm, NODE_FORESIGHT)
    thrust_edge = next((r for r in edges if r['destination'] == NODE_THRUST
                        and r['properties'] == ['○']), None)
    helm_edge = next((r for r in edges if r['destination'] == NODE_SPIRIT_THRUST
                      and r['properties'] == ['R+△']), None)
    light_edge = next((r for r in edges if r['destination'] == NODE_STEP_SLASH
                       and r['properties'] == ['△']), None)
    if not thrust_edge or not helm_edge or not light_edge:
        raise ValueError('Node 28 no longer carries the qualified B / R+triangle / triangle exits')
    if any(r['properties'] == ['○'] and r['destination'] == NODE_THRUST
           and r['operator'] != thrust_edge['operator'] for r in edges):
        raise ValueError('Foresight B exit operator changed')
    # The already-imported A exit must stay the same edge B01 retargeted.
    if light_edge['operator'] != 0:
        raise ValueError('Foresight triangle exit operator changed; review before reusing its window')
    mapping = json.loads((ROOT / 'Scripts/MHWI/moveset_mapping.json').read_text(encoding='utf-8'))
    identities = {name: dict(node=mapping['moves'][name]['fsm_node_id'],
                             action=mapping['moves'][name]['fsm_action_no'],
                             clip=mapping['moves'][name]['clip'])
                  for name in ['ForesightSlash', 'Thrust', 'SpiritThrust', 'StepSlash']}
    if (identities['Thrust']['node'] != NODE_THRUST
            or identities['SpiritThrust']['node'] != NODE_SPIRIT_THRUST
            or identities['ForesightSlash']['node'] != NODE_FORESIGHT
            or identities['StepSlash']['node'] != NODE_STEP_SLASH):
        raise ValueError('Move-to-node mapping changed; re-qualify before applying routes')
    return dict(schema=1, batch='B05', sources=pin,
                foresight_edges=edges,
                exits=[dict(input='THRUST', target='Thrust', edge=thrust_edge,
                            note='original circle edge to node 4'),
                       dict(input='HELM_BREAKER', target='SpiritThrust', edge=helm_edge,
                            note='original R+triangle edge to node 45')],
                identities=identities,
                boundaries=['cancel windows reuse the existing ForesightSlash Light adapter window;'
                            ' no original accept/execute frames are claimed (R07 stays open)',
                            'connector/LinkMotion processes stay with R06/B04; no montage edits',
                            'no damage, cost, gain or geometry values change in this batch'])


def run():
    plan = build_plan()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'native-foresight-plan.json').write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return plan


if __name__ == '__main__':
    p = run()
    print(json.dumps(dict(edges=len(p['foresight_edges']),
                          exits=[(e['input'], e['target']) for e in p['exits']]),
                     ensure_ascii=False))
