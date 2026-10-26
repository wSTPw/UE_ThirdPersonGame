"""Extract B07 native control data. No test runner, editor writes or game execution.

Produces destination-owned records in source node/link order, retaining FSM IDs
only for diagnostics. Native identities come from fixed-version PE data tables.
B10 consumers and qualification are recorded separately from the ordered table.
"""
import json
from pathlib import Path
import struct

from trace_native_connections import NativeTrace
from read_source_fsm import XfsReader
from audit_native_timing import parse_lmt, names, listify
from native_connector_source import sources, parse_mbd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIRestoration/B10-20261025'
DEST = ROOT / 'Tools/MHW/native-link-motion-policy.json'


def build():
    tr = NativeTrace()  # Fixed original executable/text hashes, read-only.
    im = tr.image
    def unpack(va, fmt):
        return struct.unpack_from('<' + fmt, im.blob, im.offset(va))
    def table(address, count):
        result = {}
        for i in range(count):
            action, pointer, size = unpack(address + i * 24, 'I4xQQ')
            if size > 1024:
                raise ValueError('Unqualified native identity array')
            result[action] = dict(address=hex(address + i * 24), pointer=pointer,
                pairs=[list(unpack(pointer + k * 8, 'ii')) for k in range(size)])
        return result

    # RIP operands of loader 14118a9e2/a9ef, weapon accessor 142165600.
    common = table(0x1434da930, unpack(0x1434d9f34, 'I')[0])
    weapon_record = 0x143fd5590 + 3 * 0x130
    weapon_ptr, weapon_count = unpack(weapon_record + 0x20, 'QI')
    weapon = table(weapon_ptr, weapon_count)
    default_pointer = unpack(weapon_record + 0x30, 'Q')[0]
    broadcast_count = unpack(0x1433aaa44, 'I')[0]
    if broadcast_count > 1024:
        raise ValueError('Unqualified native broadcast array')
    broadcast = [[1, unpack(0x1433aaa50 + i * 40, 'I')[0]] for i in range(broadcast_count)]

    pin = sources()
    fsm = XfsReader((ROOT / pin['fsm']['path']).read_bytes()).parse()['root']
    ordered_nodes = fsm['mpRootCluster']['mpNodeList']
    nodes = {n['mId']: n for n in ordered_nodes}
    def identities(node):
        params = node['mpProcessList']['mpParameter']
        action = params['ActionNo']['EnumValue']
        row = weapon.get(action) or common.get(action)
        return (row['pairs'] if row else [[3, action]], row)

    labels = ROOT / 'Saved/MHWIImport/SourceFidelity-20261023/timing-FreeHK-upstream/MHW-Free-HyperKinetics-main/struct'
    lmt = parse_lmt(ROOT / pin['lmt']['path'], names(labels/'TIMLTimelineParam.txt'), names(labels/'TIMLDatatypes.txt', True))
    motions = {m['index']: m for m in lmt['entries']}
    phase_tracks = [dict(motion=m['index'], group=g['name'], track=t)
        for m in lmt['entries'] for g in m['groups'] for t in g['tracks']
        if t['name'] == 'mLinkMotionPhase']
    mbd = parse_mbd((ROOT / pin['mbd']['path']).read_bytes())
    mapping = json.loads((ROOT / pin['mapping']['path']).read_text(encoding='utf8'))
    body_map = {v['fsm_node_id']: int(v['clip'].rsplit('_', 1)[1]) for v in mapping['moves'].values()}
    # B05 corrected mapping is in the pinned mapping file, never the B04 snapshot.
    body_map.update({23: 105, 38: 107})
    binding_path = ROOT/'Tools/MHW/native-main-motion-bindings.json'
    native_bindings = {}
    authored = json.loads((ROOT/'Saved/MHWIRestoration/B07-20261025/r06-import-journal.json').read_text(encoding='utf8'))
    authored_motions = {r['motion'] for r in authored['imports']}
    if binding_path.exists():
        native_bindings = {r['node']: r for r in json.loads(binding_path.read_text(encoding='utf8'))['bindings']}
        body_map.update({node: r['main_motion'] for node, r in native_bindings.items()})
    references = []
    by_node = {}
    for node in ordered_nodes:
        process = node['mpProcessList']
        if not process['mContainerName'].startswith('LinkMotion'):
            continue
        exits = listify(node['mpLinkList'])
        if len(exits) != 1:
            raise ValueError('Multiple LinkMotion destinations need new native review')
        target = exits[0]['mDestinationNodeId']
        target_ids, _ = identities(nodes[target])
        incoming = [dict(source_node=n['mId'], order=i, condition_id=e['mConditionId'])
            for n in ordered_nodes for i, e in enumerate(listify(n['mpLinkList']))
            if e['mDestinationNodeId'] == node['mId']]
        for phase, key in enumerate(('MotionNo', 'MotionNo_Phase1')):
            motion = process['mpParameter'][key]
            if motion < 0:
                continue  # Native signed check 14118da09/14118dabc.
            main = body_map[target]
            candidates = [dict(target_motion=e['index'], **b) for e in mbd['entries']
                if e['index'] == main for b in e['blocks']
                if b['animation_id'] == motion and b['declaration'] == 'w03_00']
            row = dict(id=f"R06-N{node['mId']}-P{phase}", node=node['mId'], phase=phase,
                connector_motion=motion, target_node=target, target_native_identity=target_ids[0],
                incoming=incoming, source_frame_count=motions[motion]['source_frame_count'],
                exit_rule='animation_layer_end_predicate_not_fixed_timer',
                project_main_motion=main,
                project_main_binding_status=('native_entry_or_update_confirmed' if target in native_bindings
                    else 'adapter_mapping_not_native_constructor_proof'),
                mbd_main_candidates=candidates, serialized_parameters=process['mpParameter'],
                runtime_record_count=0, asset_deployed=motion in authored_motions,
                asset_evidence='B07 authoring journal only; not a new readback',
                runtime_verified=False, tests_executed=False)
            references.append(row)
            by_node.setdefault(node['mId'], []).append(row)

    records = []
    # Loader visits source ActionSet nodes and their outgoing links in source order.
    for source in ordered_nodes:
        if 'ActionNo' not in source['mpProcessList']['mpParameter']:
            continue
        previous_ids, source_row = identities(source)
        for edge_index, edge in enumerate(listify(source['mpLinkList'])):
            link_rows = by_node.get(edge['mDestinationNodeId'], [])
            for previous in previous_ids:
                for row in link_rows:
                    records.append(dict(target=row['target_native_identity'], previous=previous,
                        motion=row['connector_motion'], phase=row['phase'], node=row['node'],
                        source_node=source['mId'], edge_order=edge_index, reference=row['id']))
                    row['runtime_record_count'] += 1
            # 14118da47..a9f follows the identity/phase loops; Phase0 broadcast only.
            if source_row and source_row['pointer'] == default_pointer:
                for row in link_rows:
                    if row['phase'] != 0:
                        continue
                    for previous in broadcast:
                        records.append(dict(target=row['target_native_identity'], previous=previous,
                            motion=row['connector_motion'], phase=0, node=row['node'],
                            source_node=source['mId'], edge_order=edge_index, reference=row['id']))
                        row['runtime_record_count'] += 1

    return dict(schema=3, status='r06_development_complete_uncompiled_untested',
        tests_executed=False, new_connections_enabled=0,
        new_connections_field_scope='Generator enables no playback; this is not total character runtime coverage.',
        runtime_connections_verified=0,
        code_dispatch_implemented=True, sources=pin,
        code_sources=tr.pin, weapon_identity_overrides=weapon,
        common_identity_overrides=common, default_source_broadcast=broadcast,
        selection='first exact destination/previous group+action/phase match; no phase fallback',
        reset='motion TIML rebind -> parameter virtual +0x28 -> PlMotionCommon +0x10c = 0',
        exit='uPlayer virtual +0x2b0 -> layer flags &5, optional player additional-end path',
        main_entry='MBD target + previous motion + bank + source-frame threshold; preserve order; serialized row zero fallback',
        native_main_bindings='Tools/MHW/native-main-motion-bindings.json',
        completion_evidence='Tools/MHW/native-r06-completion-evidence.json',
        remaining_evidence='Tools/MHW/native-r06-remaining-evidence.json',
        source_owners='Tools/MHW/native-r06-source-owners.json',
        actor_consumer='Source/IntroCpp/MHWI/MHWICharacterLinkMotion.cpp',
        references=references, records=records, phase_tracks=phase_tracks,
        mbd_entries=mbd['entries'],
        r06_development_complete=True,
        unresolved=[],
        structural_boundary='Source node86 has no incoming edge and generates zero records; no reachability is invented.',
        validation_status='Not compiled or tested, as requested; generated data is not runtime evidence.',
        adjacent_scope=['R07 exact input masks/cancel windows', 'R24 full reaction family selection',
                        'R25 full slinger ammunition/parts', 'R28 original locomotion start/turn/end'])


def write_cpp(data):
    # Header-only table consumed by the compiled control policy, no runtime JSON loading/cook guesses.
    lines = ['// Generated by build_native_link_policy.py; native frames; NOT a test result.',
        '#pragma once', '#include "MHWINativeLinkMotion.h"', 'namespace MHWI::Native', '{',
        '    inline const FLinkEntry LinkEntries[] = {']
    for r in data['records']:
        t, p = r['target'], r['previous']
        lines.append('        {{%d, %d}, {%d, %d}, %d, %d, %d}, // %s source %d edge %d' %
            (*t, *p, r['motion'], r['phase'], r['node'], r['reference'], r['source_node'], r['edge_order']))
    lines += ['    };', '    inline const FBlendEntry BlendEntries[] = {']
    def f(value):
        value = format(float(value), '.9g')
        return value + ('.0' if '.' not in value and 'e' not in value.lower() else '') + 'f'
    for entry in data['mbd_entries']:
        for b in entry['blocks']:
            declaration = b['declaration'].replace('\\', '\\\\').replace('"', '\\"')
            lines.append('        {%d, %d, FName(TEXT("%s")), %s, %d, %d, %d, %s, %d, %d},' %
                (entry['index'], b['animation_id'], declaration, f(b['unknown4']), b['start_frame'],
                 b['interpolation_point'], b['overlap_blending'], f(b['unknown8']), b['one0'], b['min1']))
    lines += ['    };', '}']
    (ROOT/'Source/IntroCpp/MHWI/MHWINativeLinkMotionData.inl').write_text('\n'.join(lines)+'\n', encoding='utf8')


if __name__ == '__main__':
    result = build()
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'native-link-policy.json').write_text(DEST.read_text(encoding='utf8'), encoding='utf8')
    write_cpp(result)
    print(json.dumps(dict(references=len(result['references']), records=len(result['records']),
        tests_executed=False, assets_written=False, character_adapter='development_complete_unverified')))
