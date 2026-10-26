"""One-pass native parameter/control database. No animation pose comparison.

Combines original weapon parameters, full TIML/FSM and IK structures. Unknown
bit consumption/operators remain explicit, so extraction is never confused
with a qualified original-game executor.
"""
from collections import Counter
import contextlib
import hashlib
import io
import json
from pathlib import Path

import audit_native_timing
import extract_native_equipment_params
import extract_native_longsword_params

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'Saved/MHWIImport/NativeParameterResearch-20261024'


def condition_ast(node):
    if not isinstance(node, dict):
        return {'kind': 'literal_or_null', 'raw': node}
    children = node.get('mpChildList', [])
    if isinstance(children, dict):
        children = [children]
    result = {'kind': 'native_operator' if 'mOperator' in node else 'property',
              'children': [condition_ast(child) for child in children]}
    if 'mOperator' in node:
        result['operator_raw'] = node['mOperator']
        result['operator_semantics'] = 'not_assumed_from_numeric_code'
    if 'mVariable' in node:
        result['property'] = node['mVariable']
        result['index_metadata'] = {k: v for k, v in node.items()
            if k not in ('mVariable', 'mpChildList', '_class_id', '_variable_id')}
    result['raw_class_id'] = node.get('_class_id')
    result['raw'] = node  # Preserve constants/index/enum metadata not yet interpreted.
    return result


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        parameters = extract_native_longsword_params.run()
        equipment = extract_native_equipment_params.run()
        audit = audit_native_timing.audit(OUTPUT / 'ActionsRaw')
    conditions = {key: condition_ast(node) for key, node in audit['all_conditions'].items()}
    motions = []
    lane_stats = Counter()
    for entry in audit['source']['entries']:
        lanes = []
        for group in entry['groups']:
            if group['name'] != 'nTimelineParam::PlMotionInput':
                continue
            for track in group['tracks']:
                keys = track['keys']
                integer_keys = [k for k in keys if isinstance(k['value'], int)]
                subset = len(integer_keys) == len(keys) and all(
                    int(k['value']) & ~int(k['control_l']) == 0 for k in keys)
                masks = sorted({int(k['control_l']) for k in keys})
                lanes.append(dict(name=track['name'], hash=track['hash'], kind=track['kind'],
                    keys=keys, constant_mask=len(masks) == 1, control_masks=masks,
                    value_subset_of_mask=subset,
                    evaluator_status='raw_source_keys_only; transition5 consumer/input-lane mapping unresolved'))
                lane_stats['tracks'] += 1
                lane_stats['keys'] += len(keys)
                lane_stats['subset_tracks'] += int(subset)
        motions.append(dict(motion_id=entry['index'], source_frame_count=entry['source_frame_count'],
            loop_frame=entry['source_loop_frame'], timl=entry.get('timl'), timelines=entry['groups'], input_lanes=lanes))
    nodes = []
    for node in audit['fsm_nodes']:
        edges = [dict(order=index, target_node_id=edge['mDestinationNodeId'],
                      condition_id=edge['mConditionId'], exists_condition=edge['mExistCondition'],
                      condition_ast=conditions.get(edge['mConditionId'], conditions.get(str(edge['mConditionId']))),
                      raw=edge) for index, edge in enumerate(node['links'])]
        nodes.append(dict(node_id=node['node_id'], native_name=node['name'], process=node['process'], ordered_edges=edges))
    mapping = json.loads((ROOT / 'Scripts/MHWI/moveset_mapping.json').read_text(encoding='utf8'))
    bindings = {key: {'source_clip': value.get('clip'), 'mapping_status': value.get('mapping_status'),
                      'boundary': 'Existing project/user-corrected identity; not an inferred native ActionNo=MotionNo relation.'}
                for key, value in mapping['moves'].items()}
    result = dict(schema=1, passed=True, mode='native_parameters_first_no_per_animation_comparison',
        counts=dict(weapon_fields=len(parameters['fields']), named_weapon_fields=sum(r['known_label'] for r in parameters['fields']),
                    motions=len(motions), fsm_nodes=len(nodes), fsm_links=sum(len(n['ordered_edges']) for n in nodes),
                    conditions=len(conditions), input=lane_stats, ik_chains=len(equipment['ik']),
                    extracted_resources=len(equipment['resources'])),
        weapon_parameters=parameters, motions=motions, fsm=nodes, conditions=conditions,
        equipment=equipment, project_bindings=bindings,
        pipeline_scripts_sha256={name: hashlib.sha256((ROOT/'Scripts/MHWI'/name).read_bytes()).hexdigest()
            for name in ('build_native_action_database.py','extract_native_longsword_params.py',
                         'extract_native_equipment_params.py','audit_native_timing.py','read_source_fsm.py')},
        source_fingerprints={'lmt': audit['source']['sha256'], 'fsm': audit['fsm_sha256']},
        application_policy={'allow': ['named parameters with explicit unit conversion', 'source speed and weapon events with known adapters'],
                            'deny': ['guess input acceptance from first nonzero flag', 'treat CMS as attachment data',
                                     'assign anonymous ActionParam blocks to Helm physics without a consumer mapping']})
    target = OUTPUT / 'native-action-database.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf8')
    summary = {'passed': True, 'database': str(target.relative_to(ROOT)),
               'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'counts': result['counts']}
    (OUTPUT/'native-action-database-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print(json.dumps(summary))
    return result


if __name__ == '__main__':
    run()
