"""Read pinned original Foresight input facts; never infer legal cancel windows."""
import hashlib
import json
from pathlib import Path
import native_reference_basics as basics
from audit_native_timing import parse_lmt, raw_bit_intervals, listify
from read_source_fsm import XfsReader
from trace_outstanding_evidence import Evidence

ROOT = Path(__file__).resolve().parents[2]

def run():
    pin = basics.load_sources()
    fsm_path = ROOT / pin['files']['hm/wp/wp03/wp03_action.fsm']['project_path']
    fsm = XfsReader(fsm_path.read_bytes()).parse()['root']
    nodes = {n['mId']: n for n in fsm['mpRootCluster']['mpNodeList']}
    conditions = {c['mName']['mId']: c['mpRootNode'] for c in fsm['mpConditionTree']['mpTreeList']}
    previous = json.loads((ROOT / 'Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json').read_text(encoding='utf8'))
    lmt_path = ROOT / previous['source']['path']
    lmt = parse_lmt(lmt_path, {1875693838: 'PlMotionInput'}, {150806694: 'mFlag', 1852046279: 'mFlag1', 4150962813: 'mFlag2'})
    assert lmt['sha256'] == previous['source']['sha256']
    motion = next(m for m in lmt['entries'] if m['index'] == 140)
    tracks = [dict(track=t, candidate_spans=raw_bit_intervals(t, motion['timl']['length'])) for g in motion['groups'] if g['hash'] == 1875693838 for t in g['tracks']]
    e = Evidence()
    commands = [dict(command=i, execute_bit=e.u(0x143eeabf0+i*4, 'i'), buffer_bit=e.u(0x143eeabf0+i*4, 'i')-1) for i in [24,53]]
    assert [(r['command'],r['execute_bit']) for r in commands] == [(24,15),(53,73)]
    result = dict(schema=1, date='2026-10-30', status='exact_foresight_cancel_windows_unresolved',
        requirement='Prove original exact windows before changing Foresight early SpecialSheathe/SpiritThrust routes.',
        original_execution=False, gameplay_modified=False,
        sources=dict(fsm=dict(path=str(fsm_path.relative_to(ROOT)),sha256=hashlib.sha256(fsm_path.read_bytes()).hexdigest()),lmt={k:lmt[k] for k in ['path','sha256','size']},exe=e.tr.pin['exe'],analysis_text=e.tr.pin['text']),
        official_ue=dict(version='5.8',url='https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine',conclusion='Synchronous Branching Points can support gameplay branching; this is no evidence of MHWI input permission.'),
        source_action=dict(node=28,action=86,motion=140,transitions=[dict(destination=l['mDestinationNodeId'],condition_id=l['mConditionId'],condition=conditions[l['mConditionId']]) for l in listify(nodes[28]['mpLinkList'])]),
        special_sheathe_shared_route=dict(source_node=62,action=1013,destination=61,destination_action=98,condition_id=232,condition=conditions[232]),
        input_tracks=tracks,command_bit_map=dict(table='0x143eeabf0',record_type='int32',rows=commands,meaning='Numeric command-to-bit facts only; command 24/53 gameplay names are not proven.'),
        native_functions=[e.function(a) for a in [0x141230070,0x141230100,0x140b2e4e0]],
        additional_finding=dict(property_name='R+\u25b3',name_va='0x1430b9864',resolver='0x140b2e4e0',name_ref='0x140b2ed33',return_va='0x140b2ed81',property_index=52,scope='Property index 52 is not command 24, and must not be equated to it.'),
        rea=dict(open_binary_sha_matched=True,native_trace='provider_unavailable',reason='Ghidra and IDA not configured; Hopper unsupported on Windows; Kuna not configured and PE unsupported.'),
        unknowns=['FSM property R+triangle / Iai-to-command mapping is not closed.','Transition-5 BIG_FLAGS evaluation and acceptance/buffering lifetime remain unresolved.','No original-game frame sampling was run; early 25/40/47 keys are candidate bit spans only.'],
        decision='Do not alter Foresight early cancel routes using guessed timing. Other four user fixes can proceed independently.')
    out = ROOT / 'Tools/MHW/foresight-window-evidence-20261030.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(out),status=result['status'],motion=140,tracks=len(tracks),commands=commands)))

if __name__ == '__main__':
    run()
