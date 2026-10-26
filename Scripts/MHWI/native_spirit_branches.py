"""B02: source-qualified Spirit Jumping Slash and ordered FSM continuations."""
from pathlib import Path
import json

import native_reference_basics as basics
from read_source_fsm import XfsReader

ROOT = basics.ROOT
OUT = ROOT / 'Saved/MHWIRestoration/B02-20261024'


def build_plan():
    baseline = basics.build_plan()
    pin = baseline['sources']
    evidence_path = ROOT / pin['spirit_branch_evidence']['path']
    if basics.sha(evidence_path) != pin['spirit_branch_evidence']['sha256']:
        raise ValueError('Spirit branch semantic evidence changed')
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    cost = baseline['spirit_costs']['SpiritStepSlash']['value']
    if ('Attempts to consume %g%% spirit' % cost) not in evidence['consumption_note']:
        raise ValueError('Source semantic evidence no longer agrees with original cost')
    normal, weak = [baseline['melee']['records'][i] for i in [6, 7]]
    if not any('ゲージ無し' in n['name'] for n in weak['names']):
        raise ValueError('Expected original no-gauge attack identity missing')
    weak_mv = weak['fields']['Motion_Value']
    strong_mv = normal['fields']['Conditional_Motion_value_change_replace']
    if normal['fields']['Motion_Value']['value'] != weak_mv['value'] or strong_mv['value'] <= 0:
        raise ValueError('Conditional attack structure changed')
    gain = weak['fields']['Energy_Gen']
    if gain['value'] != normal['fields']['Energy_Gen']['value']:
        raise ValueError('Source weak/strong spirit gains need separate consumers')
    first, first_weak = [baseline['melee']['records'][i] for i in [15, 16]]
    if not any('ゲージ無し' in n['name'] for n in first_weak['names']):
        raise ValueError('Original weak Spirit I identity missing')
    first_strong = first['fields']['Conditional_Motion_value_change_replace']['value']
    if first_strong <= 0 or first['fields']['Motion_Value']['value'] != first_weak['fields']['Motion_Value']['value']:
        raise ValueError('Original Spirit I conditional attack structure changed')

    source = ROOT / pin['files']['hm/wp/wp03/wp03_action.fsm']['project_path']
    tree = XfsReader(source.read_bytes()).parse()['root']
    nodes = {n['mId']: n for n in tree['mpRootCluster']['mpNodeList']}
    conditions = {c['mName']['mId']: c['mpRootNode'] for c in tree['mpConditionTree']['mpTreeList']}

    def rows(node):
        edges = nodes[node]['mpLinkList']
        edges = edges if isinstance(edges, list) else [edges]
        return [dict(source=node, order=i, destination=e['mDestinationNodeId'],
                     condition_id=e['mConditionId'], condition=conditions[e['mConditionId']],
                     properties=basics.properties(conditions[e['mConditionId']]))
                for i, e in enumerate(edges)]

    step, thrust, rising = rows(6), rows(23), rows(38)
    step_insert = next(r for r in step if r['destination'] == 38 and set(r['properties']) == {'△', '○'})
    if step_insert['condition']['mOperator'] != 17:
        raise ValueError('Step A/B condition structure changed')
    thrust_light = next(r for r in thrust if r['destination'] == 3 and r['properties'] == ['△'])
    if any(r['properties'] == ['○'] for r in thrust):
        raise ValueError('Original insertion Thrust B condition changed; review required')
    primary = next(r for r in rising if r['properties'] == ['R', '練気ゲージ判定(気刃斬りIII'])
    fallback = next(r for r in rising if r['properties'] == ['R'] and r['destination'] == 1)
    if primary['condition']['mOperator'] != 16 or primary['order'] >= fallback['order']:
        raise ValueError('Original Spirit III/I order changed')
    link = nodes[primary['destination']]
    process = link['mpProcessList']
    parameter = process['mpParameter']
    exits = link['mpLinkList']
    exits = exits if isinstance(exits, list) else [exits]
    if parameter.get('MotionNo') is None or len(exits) != 1 or exits[0]['mDestinationNodeId'] != 2:
        raise ValueError('Expected source LinkMotion into Spirit III missing')
    return dict(schema=1, batch='B02', source_fingerprints=pin,
                spirit_step=dict(cost=cost, strong_damage=strong_mv['value'], weak_damage=weak_mv['value'],
                                 weak_multiplier=weak_mv['value'] / strong_mv['value'],
                                 gain=basics.percent(gain['value']), allow_weak=True,
                                 source_normal=normal, source_weak=weak,
                                 cost_field=baseline['spirit_costs']['SpiritStepSlash']['raw'],
                                 semantic_evidence=evidence),
                required_spirit_iii_cost=baseline['spirit_costs']['SpiritIII']['value'],
                spirit_i=dict(cost=baseline['spirit_costs']['SpiritI']['value'],
                              strong_damage=first_strong,
                              weak_damage=first_weak['fields']['Motion_Value']['value'],
                              weak_multiplier=first_weak['fields']['Motion_Value']['value']/first_strong,
                              gain=basics.percent(first['fields']['Energy_Gen']['value']),
                              source_normal=first,source_weak=first_weak),
                fsm_evidence=dict(step_insert=step_insert, insertion_thrust_light=thrust_light,
                                  rising_priority=primary, rising_fallback=fallback,
                                  link_process=process, link_exits=exits),
                boundaries=['existing timing values retained; not original cancel-frame proof',
                            'new same-condition routes copy existing matching input windows',
                            'no connectors, input buffer, shell, Q decay or full damage changes'])


def run():
    plan = build_plan()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'native-spirit-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return plan


if __name__ == '__main__':
    p = run()
    print(json.dumps(dict(batch=p['batch'], strong=p['spirit_step']['strong_damage'],
                          weak=p['spirit_step']['weak_damage'], cost=p['spirit_step']['cost'])))
