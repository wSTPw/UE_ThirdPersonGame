"""Pin property52 R+triangle and transition-command namespaces independently.

Only static source extraction; never runs original game code or changes gameplay.
Capstone official API: https://www.capstone-engine.org/lang_python.html
"""
import json
from pathlib import Path
from trace_outstanding_evidence import Evidence

ROOT = Path(__file__).resolve().parents[2]


def run():
    e = Evidence()
    expression_table = 0x143360510
    rows = []
    for row in range(777):
        record = expression_table + row * 40
        if e.u(record, 'i') == 52:
            pointer, count = e.u(record + 8), e.u(record + 16, 'I')
            terms = [list(e.u(pointer + i*24+j*4, 'i') for j in range(6)) for i in range(count)]
            rows.append(dict(row=row, record=hex(record), id=52, pointer=hex(pointer), count=count, record_stride=24, terms=terms))
    assert len(rows) == 1 and rows[0]['row'] == 47
    assert rows[0]['terms'][0] == [-10,-10,0,0,1,25]
    assert rows[0]['terms'][-1] == [1,144,1,0,1,26]
    initialization = e.function(0x1417c5de0)
    group = key = active = None
    bindings = []
    for instruction in initialization['instructions']:
        op, args = instruction['mnemonic'], instruction['operands']
        if op == 'mov' and args.startswith('dword ptr [rbp + 0x5b8], '):
            group = int(args.rsplit(', ', 1)[1], 0)
        if op == 'mov' and args.startswith('dword ptr [rbp + 0x5bc], '):
            try:
                key = int(args.rsplit(', ', 1)[1], 0)
            except ValueError:
                key = None
        if op == 'call' and args == '0x14026b550':
            active = dict(group=group, transition_id=key, lookup=instruction)
        if op == 'mov' and args.startswith('dword ptr [rax + 0x28], ') and active and active['group'] == 1 and active['transition_id'] in (25, 33, 52):
            command = int(args.rsplit(', ', 1)[1], 0)
            bindings.append(dict(**active, command=command, command_store=instruction,
                                 execute_bit=e.u(0x143eeabf0 + command*4, 'i'),
                                 preceding_bit=e.u(0x143eeabf0 + command*4, 'i')-1))
    assert [(r['transition_id'], r['command']) for r in bindings] == [(25,26),(33,34),(52,53)]
    factory_records = []
    for row in range(798):
        record = 0x143f33da0 + row*16
        identity = e.u(record, 'i')
        if identity in (0,25,33,52,290,295,395,399,490):
            factory_records.append(dict(row=row, id=identity, dti=hex(e.u(record+8))))
    assert all(r['dti'] == '0x144feab50' for r in factory_records if r['id'] in (25,33,52))
    assert e.u(0x1431c5278+6*8) == 0x1417be130
    report = dict(schema=1, status='r_triangle_command53_static_binding_closed_window_consumer_separate',
        sources=e.tr.pin, original_game_executed=False, gameplay_modified=False,
        official=dict(url='https://www.capstone-engine.org/lang_python.html',
                      conclusion='Capstone disassembles bounded bytes; it does not prove source gameplay semantics.'),
        requirement='Close Foresight node28 to SpiritThrust node45 condition108 without equating unrelated numeric namespaces.',
        property_name=dict(name='R+triangle', property_id=52, name_va='0x1430b9864',
                           resolver='0x140b2e4e0', return_va='0x140b2ed81'),
        expression=rows[0], expression_registration=dict(function='0x14118ddc0',
            lea_table='0x14118de61', register_call='0x14118de68', group=1, count=777),
        transition_factory_table=dict(address='0x143f33da0', count=798, stride=16, records=factory_records),
        command_initialization=dict(function='0x1417c5de0', lookup='0x14026b550',
            key='qword(group:int32 at rbp+5b8,transition:int32 at rbp+5bc)',
            object_command_offset='0x28', bindings=bindings),
        finding='R+triangle property52 resolves to transition factory52, whose initialized command is53. The 18 records at143f0d5c0 are downstream action-routing records of 24 bytes, not 18 boolean token pairs. They do not negate the direct condition binding.',
        routing_consumers=dict(evaluate='0x14026b830', record_stride_proof='0x14026b883/0x14026b887',
            condition_pair_offsets=[0,4], expected_return_offset=12, target_pair_offsets=[16,20],
            condition_dispatch='0x14026ba00', condition_virtual_call='0x14026ba7c', condition_slot=6,
            selected_action_setter='0x140269ce0', target_current_offsets=['0xac','0xb0'], target_pending_offsets=['0xbc','0xc0']),
        condition_gate=dict(instance_vtable='0x1431c5278',slot=6,evaluate='0x1417be130',
            command_load='0x1417be136', helper='0x1417bd120', permission_call='0x1417bd183',
            permission='0x1419a30d0', execute_query='0x14122fdb0',buffer_query='0x14122fe60',
            execute_bit=73,buffer_bit=72,
            scope='Static binding and reached call chain; current-control-state/input-buffer lifetime gates remain part of the full permission.'),
        command_commit=dict(command_evaluator='0x1417c3e50', setter='0x1411a1100',
            conclusion='The reached setter only stores edx to rcx+4ef0. This is a selected-command write, not proof of execution or buffering permission.'),
        functions={hex(a):e.function(a) for a in [0x140b2e4e0,0x14118ddc0,0x1417b01c0,0x1417be130,0x1417bd120,0x1419a30d0,0x14122fdb0,0x14122fe60,0x1417c3e50,0x1411a1100,0x14026b830,0x14026ba00,0x14026bf70,0x140269ce0,0x141230070,0x141230100]},
        unknowns=['TIML mask update and endpoint conclusions must be taken from the separately validated consumer extraction.',
                  'Full control-state gates and original runtime sampling are not claimed by this static chain.',
                  'No gameplay code or asset has been changed by this extractor.'])
    output = ROOT/'Tools/MHW/spirit-thrust-command-evidence-20261030.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(output), status=report['status'], bindings=[(r['transition_id'],r['command']) for r in bindings])))


if __name__ == '__main__':
    run()
