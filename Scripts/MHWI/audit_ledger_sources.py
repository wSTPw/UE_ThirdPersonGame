"""B12 ledger sweep: read-only dump of every pinned native source.

Purpose
-------
One deterministic evidence base for processing the whole MHWI ledger. It does
not write any project asset and does not evaluate gameplay. Every number keeps
its source file, record index and byte offset so later batches can re-check it.

Run: python Scripts/MHWI/audit_ledger_sources.py
Out: Saved/MHWIRestoration/B12-20261026/evidence/ledger-source-dump.json
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import native_reference_basics as basics
from read_source_fsm import XfsReader

ROOT = basics.ROOT
OUT = ROOT / 'Saved/MHWIRestoration/B12-20261026/evidence/ledger-source-dump.json'

# Ledger items whose FSM node is examined by this sweep. Documented in the
# 2026-10-24 review and in the per-item ledger rows.
FSM_FOCUS = {
    2: 'SpiritIII',
    4: 'Thrust',
    5: 'SpiritRoundslash',
    6: 'SpiritStepSlash',
    7: 'FadeSlashLeft',
    8: 'FadeSlashLeftVariant',
    9: 'FadeSlashRight',
    10: 'OverheadSlash',
    11: 'StepSlash',
    18: 'Aerial neutral (drawn)',
    28: 'ForesightSlash',
    38: 'SpiritComboRisingSlash',
    45: 'SpiritThrust',
    60: 'SpecialSheathe/Iai phase select',
    63: 'Slinger',
    65: 'IaiSpiritSlash',
    66: 'Slinger 66',
    67: 'Slinger 67',
    68: 'Slinger 68',
    69: 'Slinger 69',
    70: 'Slinger 70',
    71: 'Slinger 71',
    72: 'Slinger 72',
    73: 'Slinger 73',
    74: 'Slinger 74',
    75: 'Slinger 75',
    76: 'Iai phase select',
    86: 'Unreachable connector',
}


def record_summary(rec):
    """Keep every layout field and its byte offset; callers decide what matters."""
    return {
        'index': rec['index'],
        'offset': rec.get('offset'),
        'names': [n['name'] for n in rec.get('names', [])],
        'fields': rec['fields'],
    }


def condition_expr(node):
    """Render an FSM condition tree as a neutral nested expression.

    The tree mixes single nodes and child arrays, so both shapes are accepted;
    no interpretation of operator ids is invented here.
    """
    if isinstance(node, list):
        return {'operator': 'list', 'children': [condition_expr(c) for c in node if c]}
    if not isinstance(node, dict):
        return None
    out = {'operator': node.get('mOperator')}
    variable = node.get('mVariable') or {}
    if variable.get('mPropertyName'):
        out.update({
            'variable': variable.get('mPropertyName'),
            'owner': variable.get('mOwnerName'),
            'bit': node.get('mIsBitNo'),
            'index': node.get('mIndex'),
        })
    child_wrap = node.get('mpChildList')
    if isinstance(child_wrap, dict):
        # A single condition is encoded as a wrapper that is itself the leaf
        # (it carries mVariable) rather than as an array of children.
        if child_wrap.get('mVariable') or 'mOperator' in child_wrap:
            children = [child_wrap]
        else:
            children = child_wrap.get('mpChildList') or []
    elif isinstance(child_wrap, list):
        children = child_wrap
    else:
        children = []
    if children:
        out['children'] = [condition_expr(c) for c in children if c]
    return out


def process_summary(process):
    if not isinstance(process, dict):
        return None
    parameter = process.get('mpParameter') or {}
    out = {'container': process.get('mContainerName'), 'category': process.get('mCategoryName')}
    action = parameter.get('ActionNo') or {}
    if isinstance(action, dict) and 'EnumValue' in action:
        out['action_no'] = action['EnumValue']
    for key in ('MotionNo', 'MotionNo_Phase', 'MotionNo_Phase2'):
        if key in parameter:
            out[key] = parameter[key]
    return out


def read_shell(path, layout):
    raw = Path(path).read_bytes()
    if raw[4:8] != b'COL\0':
        raise ValueError('Not a qualified shell COL')
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
        raise ValueError('Unqualified shell ATK version/type')
    size = sum(struct.calcsize('<' + basics.FORMATS[f['type']]) for f in layout['fields'])
    if size != layout['record_size']:
        raise ValueError('Shell record width mismatch')
    cursor, records = marker + 16, []
    for index in range(count):
        start, fields = cursor, {}
        for field in layout['fields']:
            value = struct.unpack_from('<' + basics.FORMATS[field['type']], raw, cursor)[0]
            fields[field['name']] = {'value': value, 'offset': cursor - start}
            cursor += struct.calcsize('<' + basics.FORMATS[field['type']])
        records.append({'index': index, 'offset': start, 'fields': fields})
    return {'count': count, 'names': names, 'records': records}


def main():
    pin = basics.load_sources()
    layout = json.loads(basics.LAYOUT.read_text(encoding='utf-8'))
    src = {name: ROOT / value['project_path'] for name, value in pin['files'].items()}

    melee = basics.read_collision(src['hm/wp/wp03/collision/wp03.col'])
    shell = read_shell(src['hm/wp/wp03/shell/collision/object.col'], layout)

    fsm_raw = src['hm/wp/wp03/wp03_action.fsm'].read_bytes()
    tree = XfsReader(fsm_raw).parse()['root']
    nodes = {node['mId']: node for node in tree['mpRootCluster']['mpNodeList']}
    conditions = {
        (entry.get('mName') or {}).get('mId'): condition_expr(entry.get('mpRootNode'))
        for entry in tree['mpConditionTree']['mpTreeList']
    }
    focus = {}
    for node_id, label in FSM_FOCUS.items():
        node = nodes.get(node_id)
        if node is None:
            continue
        raw_links = node.get('mpLinkList')
        if isinstance(raw_links, dict):
            raw_links = [raw_links] if 'mDestinationNodeId' in raw_links else []
        edges = []
        for order, link in enumerate(raw_links or []):
            condition_id = link.get('mConditionId')
            edges.append({
                'order': order,
                'name': link.get('mName'),
                'destination': link.get('mDestinationNodeId'),
                'condition_id': condition_id,
                'condition': conditions.get(condition_id),
            })
        focus[node_id] = {
            'label': label,
            'name': node.get('mName'),
            'process': process_summary(node.get('mpProcessList')),
            'edges': edges,
            'subcluster': node.get('mpSubCluster'),
        }

    out = {
        'schema': 1,
        'sources': {
            name: {'bytes': value['bytes'], 'sha256': value['sha256']}
            for name, value in pin['files'].items()
        },
        'melee': {
            'count': melee['count'],
            'records': [record_summary(rec) for rec in melee['records']],
        },
        'shell': {
            'count': shell['count'],
            'names': shell['names'],
            'records': [record_summary(rec) for rec in shell['records']],
        },
        'fsm': {'node_count': len(nodes), 'focus': focus},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('wrote', OUT)
    print('melee', melee['count'], 'shell', shell['count'], 'fsm nodes', len(nodes))


if __name__ == '__main__':
    main()
