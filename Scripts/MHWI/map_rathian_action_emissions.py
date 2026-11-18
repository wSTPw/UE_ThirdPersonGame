"""M2 first pass: inventory every THK action emission in em001 and map to names.

Reads the frozen thk-all-raw.json (offline source extraction, not game execution)
and Leviathon's ActionDump for em001. Produces:
  - all action-emitting segments (actionID != 0) grouped by behavior context
  - the 7 is_rank (0xB8) gates with their case values
  - a name-mapped action inventory

CFG-level rank pruning (which actions are LR-exclusive) is NOT done here: segment
flow semantics (flowControl/branchingControl) require Leviathon decompiler output.
This file is the evidence JSON the milestone record points to.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'Saved/DevFlow/Rathian-Condition-Audit-20261104/source-baseline/EvidenceInput/thk-all-raw.json'
DUMP = ROOT / 'Tools/MHW/ActionDumps/em001-actiondump.txt'
OUT = ROOT / 'Tools/MHW/rathian-action-emission-inventory-20261117.json'

raw = json.loads(RAW.read_text(encoding='utf-8'))

names = {}
for line in DUMP.read_text(encoding='utf-8').splitlines():
    m = re.match(r'\[[^\]]+\]Group:(\d+),ID:(\d+),Name:(.+)', line.strip())
    if m:
        names[int(m.group(2))] = m.group(3).strip()

contexts = {}
for entry in raw['thklst']['entries']:
    contexts[entry['index']] = entry['path'].split('\\')[-1]

emissions = []
rank_gates = []
for table in raw['tables']:
    src_path = table['source'].get('path', '?')
    context = Path(src_path).stem
    for node in table['nodes']:
        for seg in node['segments']:
            f = seg['fields']
            if f.get('functionType') == 184:
                rank_gates.append({
                    'table': context, 'node': node['id'], 'segment': seg['index'],
                    'case_rank': f.get('parameter1'),
                    'rank_name': {0: 'LR', 1: 'HR', 2: 'MR', 3: 'AT'}.get(f.get('parameter1'), '?'),
                })
            aid = f.get('actionID', 0)
            if aid:
                emissions.append({
                    'action_id': aid, 'table': context, 'node': node['id'],
                    'segment': seg['index'], 'function_type': hex(f.get('functionType', 0)),
                    'name': names.get(aid),
                })

by_id = defaultdict(lambda: {'count': 0, 'contexts': set(), 'name': None})
for e in emissions:
    k = e['action_id']
    by_id[k]['count'] += 1
    by_id[k]['contexts'].add(e['table'])
    by_id[k]['name'] = e['name'] or by_id[k]['name']

inventory = [
    {'action_id': k, 'name': v['name'], 'emissions': v['count'],
     'contexts': sorted(v['contexts']),
     'named': v['name'] is not None}
    for k, v in sorted(by_id.items())
]

out = {
    'schema': 1,
    'date': '2026-11-17',
    'mode': 'offline_source_extraction_not_original_game_execution',
    'source': str(RAW.relative_to(ROOT)),
    'action_dump': 'Tools/MHW/ActionDumps/em001-actiondump.txt (Leviathon ActionDumps, 285 entries)',
    'counts': {
        'segments_total': sum(len(n['segments']) for t in raw['tables'] for n in t['nodes']),
        'emitting_segments': len(emissions),
        'distinct_action_ids': len(inventory),
        'named': sum(1 for i in inventory if i['named']),
        'rank_gates': len(rank_gates),
    },
    'rank_gates': rank_gates,
    'inventory': inventory,
}
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
print('M2 emitted=%d distinct=%d named=%d rank_gates=%d -> %s' % (
    len(emissions), len(inventory), sum(1 for i in inventory if i['named']),
    len(rank_gates), OUT.name))
