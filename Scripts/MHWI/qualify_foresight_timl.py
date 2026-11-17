"""Qualify TIML type-5 mask writes and source-frame interval boundaries offline."""
import hashlib
import json
from pathlib import Path
from audit_native_timing import parse_lmt
from trace_outstanding_evidence import Evidence

ROOT=Path(__file__).resolve().parents[2]

def bit_spans(keys, bit, end):
    state=0
    spans=[]
    for i,key in enumerate(keys):
        assert key['transition']==5
        state=(state & (~int(key['control_l']) & 0xffffffff)) | int(key['value'])
        stop=keys[i+1]['frame'] if i+1<len(keys) else end
        if state & (1<<bit) and stop>key['frame']:
            if spans and spans[-1][1]==key['frame']:
                spans[-1][1]=stop
            else:
                spans.append([key['frame'],stop])
    return spans

def run():
    e=Evidence()
    first=json.loads((ROOT/'Tools/MHW/foresight-window-evidence-20261030.json').read_text(encoding='utf8'))
    path=ROOT/first['sources']['lmt']['path']
    lmt=parse_lmt(path,{1875693838:'PlMotionInput'},{150806694:'mFlag',4150962813:'mFlag2'})
    assert lmt['sha256']==first['sources']['lmt']['sha256']
    m=next(x for x in lmt['entries'] if x['index']==140)
    tracks={t['name']:t for g in m['groups'] if g['hash']==1875693838 for t in g['tracks']}
    anchors={
        0x1424a8586:('mov','r8, qword ptr [rcx]'),
        0x1424a8747:('mov','rdx, rcx'),
        0x1424a8752:('jmp','0x1424a8820'),
        0x1424a8840:('not','edx'),
        0x1424a8842:('and','edx, eax'),
        0x1424a8844:('or','edx, dword ptr [rbx]'),
        0x1424a7b67:('comiss','xmm6, dword ptr [r10 + rcx*4 + 0xc]'),
        0x1424a7b6d:('jb','0x1424a7b80'),
        0x1424a7584:('comiss','xmm7, dword ptr [r9 + rcx*4 + 0xc]'),
        0x1424a758a:('jb','0x1424a75b4'),
        0x1424a785f:('jmp','0x1424a8580'),
    }
    functions={hex(a):e.function(a) for a in [0x1424a7b20,0x1424a7440,0x1424a8580,0x1424a8820,0x14218eb20,0x142190730,0x141230990,0x141230230]}
    rows={int(r['va'],16):r for f in functions.values() for r in f['instructions']}
    for va,pair in anchors.items():
        assert (rows[va]['mnemonic'],rows[va]['operands'])==pair,(hex(va),rows.get(va))
    spans=[]
    for cmd,track_name,local_exec_bit in [(24,'mFlag',15),(53,'mFlag2',9)]:
        flag=e.u(0x143eeabf0+cmd*4,'i')
        assert flag==local_exec_bit+(0 if cmd==24 else 64)
        keys=tracks[track_name]['keys']
        execute=bit_spans(keys,local_exec_bit,m['timl']['length'])
        buffer=bit_spans(keys,local_exec_bit-1,m['timl']['length'])
        assert execute==[[40.,47.],[90.,160.]]
        assert buffer==[[25.,47.],[70.,160.]]
        spans.append(dict(command=cmd,track=track_name,execute_bit=flag,buffer_bit=flag-1,
            execute_frame_intervals=execute,buffer_frame_intervals=buffer,endpoint='left_inclusive_right_exclusive'))
    result=dict(schema=1,status='native_timl_type5_bit_intervals_qualified_not_complete_action_acceptance',
        original_game_executed=False,gameplay_modified=False,sources=dict(exe=e.tr.pin['exe'],text=e.tr.pin['text'],lmt={k:lmt[k] for k in ['path','sha256','size']}),
        native_semantics=dict(dispatch='0x1424a8580',type5_target='0x1424a8820',key_stride=20,frame_offset=12,transition_offset=16,
            expression='new_u32 = (old_u32 & ~key.control_l) | key.value',
            property_get='0x14218eb20',property_set='0x142190730',
            seek='0x1424a7b20',normal_advance='0x1424a7440',
            endpoint_evidence='COMISS currentFrame,nextKey.frame followed by JB; equality advances to new key. Normal advance ends with tail JMP 0x1424a8580.',
            property_adapter_boundary='Generic reflected property get/set has virtual getter/setter branches; PlMotionInput local object field binding is supported by earlier input registration evidence, not native game execution.'),
        commands=spans,raw_source_tracks=[tracks['mFlag'],tracks['mFlag2']],
        instruction_anchors=[rows[a] for a in anchors],functions=functions,
        command_pipeline=dict(eval='0x1417be130 -> 0x1417bd120 -> 0x1419a30d0',
            command24='cWp03Iaigiri ctor 0x140ef8bc0 writes +0x28=24; eval thunk 0x140f0ebb0 -> 0x1417be130',
            execute='0x14122fdb0 calls 0x141230070; command field chooses odd permission bit',
            buffering='0x141230990 reads even bit, writes +0x800/+0x840; odd bit writes +0x7e0',
            invalidation='0x141230230 clears saved flags when main/secondary even bits and global202 are absent; unrelated controller reset/special handling also exists',
            caveat='0x1419a30d0 chooses 0x14122fdb0 or 0x14122fe60 depending transition flag +8; normal predicate may use current command bits directly. This report does not collapse all contexts to one odd-bit-only rule.'),
        implementation_boundary='The two exact native TIML permission-bit windows are proven. An implementation using only these windows must disclose remaining command-state/secondary/global overrides and project input buffering rather than claiming full native input parity.',
        open_boundaries=['Full current/saved input selection and per-context transition flag configuration','All secondary-channel and global202/203 overrides','Original-game input timing and view observed by user'])
    out=ROOT/'Tools/MHW/foresight-timl-semantics-20261030.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(out),status=result['status'],anchors=len(anchors),commands=spans)))

if __name__=='__main__':
    run()
