"""Continue B23-03 from pinned native bytes; never executes original game code."""
import json
from pathlib import Path
from trace_outstanding_evidence import Evidence

ROOT = Path(__file__).resolve().parents[2]

def run():
    e = Evidence()
    table = 0x140b32414
    targets = [e.tr.image.base + e.u(table+i*4, 'I') for i in range(14)]
    assert targets[3] == 0x140b30dae
    assert e.u(0x143f33da0+630*16, 'I') == 630
    assert e.u(0x143f33da0+630*16+8) == 0x144f7c6c8
    assert e.u(0x1431c68b0+7*8) == 0x1417c3e50
    assert e.u(0x143eeabf0+24*4, 'i') == 15
    report = dict(schema=1, status='special_sheathe_command_bound_timing_not_yet_final',
        original_game_executed=False, gameplay_modified=False, sources=e.tr.pin,
        special_sheathe=dict(property_name='居合斬り',property_id=630,
            name_resolver='0x140b306a0',weapon_case=3,case_target=hex(targets[3]),
            name_ref='0x140b3104d',return_va='0x140b31068',
            transition_factory_table='0x143f33da0',transition_id=630,dti='0x144f7c6c8',
            type_name='nHmTransition::cWp03Iaigiri',registration='0x140130f60',
            constructor='0x140ef8bc0',command_store='0x140ef8c1f',command_offset='0x28',command_id=24,
            instance_vtable='0x1431c68b0',eval_slot=6,evaluate_thunk='0x140f0ebb0',evaluate='0x1417be130',commit_slot=7,commit='0x1417c3e50',
            execute_bit=15,buffer_bit=14,
            conclusion='The constructor binds Iai entry to command24. Exact end-to-end legal windows require evaluation and TIML semantics, not just candidate bit spans.'),
        weapon_name_resolver_case=e.tr._decode(targets[3],targets[4]),
        functions={hex(a):e.function(a) for a in [0x140130f60,0x140ef8bc0,0x140f0ebb0,0x1417be130,0x1417bd120,0x1419a30d0,0x14122fe60,0x14122fdb0,0x141230000,0x1417c3e50,0x141230070,0x141230100]},
        unresolved=['Iai evaluator extra gates/command use','R+triangle property52 actual consumers','transition5/endpoint/bit-mask semantics'])
    out=ROOT/'Tools/MHW/foresight-consumers-20261030.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(out),status=report['status'],Iai_command=24)))

if __name__=='__main__':
    run()
