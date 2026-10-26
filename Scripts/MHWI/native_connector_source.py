"""B04 MBD21 source reader and per-connector evidence. No guessed exit times.

Layout follows the pinned FreeHK struct/mbd.py, read as data, never imported.
Field labels are reverse-engineering metadata, not decoded native consumers.
"""
import hashlib
import json
from pathlib import Path
import struct

from read_source_fsm import XfsReader
from audit_native_timing import parse_lmt, names, listify

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIRestoration/B04-20261024'
PIN = ROOT / 'Tools/MHW/native-connector-sources.json'


def sources():
    result = json.loads(PIN.read_text(encoding='utf8'))
    for row in result.values():
        if hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Connector source changed: ' + row['path'])
    return result


def parse_mbd(blob):
    pos = 0
    def read(fmt):
        nonlocal pos
        size = struct.calcsize('<' + fmt)
        if pos + size > len(blob): raise ValueError('Truncated MBD at ' + hex(pos))
        value = struct.unpack_from('<' + fmt, blob, pos)
        pos += size
        return value
    header = read('4i')
    if header[:2] != (0x18091001, 21) or not 0 <= header[2] <= len(blob)//24:
        raise ValueError('Expected bounded MBD21')
    entries = []
    for _ in range(header[2]):
        start = pos
        index, count, zero = read('3i')
        if not 0 <= count <= len(blob)//33: raise ValueError('Invalid MBD block count')
        blocks = []
        for _ in range(count):
            offset = pos
            animation = read('i')[0]
            end = blob.find(b'\0', pos)
            if end < 0: raise ValueError('Unterminated MBD declaration')
            declaration = blob[pos:end].decode('utf8')
            pos = end + 1
            field_offset = pos
            raw = read('fiiifii')
            blocks.append(dict(offset=offset, fields_offset=field_offset, animation_id=animation,
                               declaration=declaration, unknown4=raw[0], start_frame=raw[1],
                               interpolation_point=raw[2], overlap_blending=raw[3],
                               unknown8=raw[4], one0=raw[5], min1=raw[6]))
        tail = read('3i')
        entries.append(dict(offset=start, index=index, zero=zero, blocks=blocks, tail=tail))
    if pos != len(blob): raise ValueError('Unconsumed MBD bytes')
    if len({r['index'] for r in entries}) != len(entries): raise ValueError('Duplicate MBD destination')
    return dict(header=header, entries=entries)


def encode_mbd(parsed):
    result = bytearray(struct.pack('<4i', *parsed['header']))
    for row in parsed['entries']:
        result.extend(struct.pack('<3i', row['index'], len(row['blocks']), row['zero']))
        for b in row['blocks']:
            result.extend(struct.pack('<i', b['animation_id']))
            result.extend(b['declaration'].encode('utf8') + b'\0')
            result.extend(struct.pack('<fiiifii', b['unknown4'], b['start_frame'], b['interpolation_point'],
                                      b['overlap_blending'], b['unknown8'], b['one0'], b['min1']))
        result.extend(struct.pack('<3i', *row['tail']))
    return bytes(result)


def entry_record(destination, previous, parsed=None):
    if parsed is None:
        pin = sources()
        parsed = parse_mbd((ROOT / pin['mbd']['path']).read_bytes())
    rows = [b for r in parsed['entries'] if r['index'] == destination for b in r['blocks']
            if b['animation_id'] == previous and b['declaration'] == 'w03_00']
    # Reject threshold/phase-dependent duplicates; never pick first silently.
    if len(rows) != 1 or rows[0]['unknown4'] != 0.:
        raise ValueError('Unqualified/ambiguous MBD pair: %s -> %s' % (previous, destination))
    return rows[0]


def entry_frame(destination, previous):
    return float(entry_record(destination, previous)['start_frame'])


def build():
    pin = sources()
    raw = (ROOT / pin['mbd']['path']).read_bytes()
    mbd = parse_mbd(raw)
    assert encode_mbd(mbd) == raw, 'MBD roundtrip mismatch'
    fsm = XfsReader((ROOT / pin['fsm']['path']).read_bytes()).parse()['root']
    nodes = {n['mId']: n for n in fsm['mpRootCluster']['mpNodeList']}
    conditions = {c['mName']['mId']: c['mpRootNode'] for c in fsm['mpConditionTree']['mpTreeList']}
    labels = ROOT / 'Saved/MHWIImport/SourceFidelity-20261023/timing-FreeHK-upstream/MHW-Free-HyperKinetics-main/struct'
    lmt = parse_lmt(ROOT / pin['lmt']['path'], names(labels/'TIMLTimelineParam.txt'), names(labels/'TIMLDatatypes.txt', True))
    motions = {m['index']: m for m in lmt['entries']}
    mapping = json.loads((ROOT / pin['mapping']['path']).read_text(encoding='utf8'))
    target_nodes = {e['mDestinationNodeId'] for n in nodes.values()
                    if n['mpProcessList']['mContainerName'].startswith('LinkMotion')
                    for e in listify(n['mpLinkList'])}
    target_clips = {}
    for move in mapping['moves'].values():
        node, clip = move.get('fsm_node_id'), move.get('clip')
        if node in target_nodes and clip:
            value = int(clip.rsplit('_', 1)[1])
            if node in target_clips and target_clips[node] != value: raise ValueError('Ambiguous project mapping')
            target_clips[node] = value
    # Native inserted identities share the existing 105/107 body motions.
    target_clips.update({23: 105, 38: 107})
    rows = []
    for ident, node in nodes.items():
        process = node['mpProcessList']
        if not process['mContainerName'].startswith('LinkMotion'): continue
        params = process['mpParameter']
        exits = listify(node['mpLinkList'])
        if len(exits) != 1: raise ValueError('Connector now has multiple exits')
        edge = exits[0]
        target = edge['mDestinationNodeId']
        main = target_clips[target]
        incoming = [dict(node_id=n['mId'], name=n['mName'], order=i, condition_id=e['mConditionId'])
                    for n in nodes.values() for i,e in enumerate(listify(n['mpLinkList'])) if e['mDestinationNodeId']==ident]
        for phase, key in enumerate(('MotionNo', 'MotionNo_Phase1')):
            motion = params[key]
            if motion < 0: continue
            pairs = [(r['index'], b) for r in mbd['entries'] for b in r['blocks']
                     if b['animation_id']==motion and b['declaration']=='w03_00']
            matches = [p for p in pairs if p[0]==main]
            selected = matches if matches else pairs
            if len(selected)!=1: raise ValueError('Connector MBD target not unique: '+str(motion))
            mbd_main, record = selected[0]
            record = entry_record(mbd_main, motion, mbd)
            mapping_matches = main == mbd_main
            source = motions[motion]
            assert 0 <= record['start_frame'] < motions[mbd_main]['source_frame_count']
            rows.append(dict(id='R06-N%02d-P%d' % (ident, phase), node_id=ident, phase=phase,
                             name=node['mName'], connector_motion=motion, target_node=target,
                             target_name=nodes[target]['mName'], main_motion=main,
                             incoming=incoming, serialized_parameters=params, exit_edge=edge,
                             exit_condition=conditions[edge['mConditionId']],
                             source_frame_count=source['source_frame_count'],
                             last_source_sample=source['source_frame_count']-1,
                             timl=source['timl'], all_timeline_groups=source['groups'],
                             exit_phase_keys=[t for g in source['groups'] for t in g['tracks']
                                              if t['name'] in ('mActionPhase','mActionPhaseSub','mLinkMotionPhase')],
                             mbd=record, mbd_main_motion=mbd_main, mapping_matches=mapping_matches,
                             mbd_candidates=[dict(destination=p[0], record=p[1]) for p in pairs],
                             main_start_frame=record['start_frame'],
                             connector_exit_frame=None, phase_selection_confirmed=False,
                             status='main_entry_table_decoded_exit_consumer_unresolved' if mapping_matches else 'target_mapping_conflict_exit_unresolved',
                             runtime='existing_project_composite_exit_unqualified' if ident==52 else 'not_implemented',
                             mapping_boundary='Target motion uses pinned project/user-corrected ActionNo mapping, not ActionNo=MotionNo.',
                             next_step='Recover LinkMotion process completion and optional phase selection; do not use frame count or empty condition as exit time.'))
    assert len({r['node_id'] for r in rows})==30 and len(rows)==32
    return dict(schema=1, sources=pin, mbd_entries=len(mbd['entries']),
                mbd_blocks=sum(len(r['blocks']) for r in mbd['entries']), roundtrip_passed=True,
                connector_nodes=30, motion_references=32, implemented_new_connections=0, connections=rows)


def run():
    report = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'connector-evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    (OUT/'mbd-decoded.json').write_text(json.dumps(parse_mbd((ROOT/report['sources']['mbd']['path']).read_bytes()),indent=2)+'\n',encoding='utf8')
    return report


if __name__ == '__main__':
    result = run()
    print(json.dumps({k:result[k] for k in ('mbd_entries','mbd_blocks','connector_nodes','motion_references','implemented_new_connections')}))
