"""B13 offline, pinned native evidence. Never executes or changes game code.

Direct reachable CFG only; unresolved indirect branches are explicitly recorded.
Data inside pdata is never silently promoted to instructions. Output stays local.
"""
import argparse
import hashlib
import json
import re
import struct
from functools import lru_cache
from pathlib import Path
from trace_native_connections import NativeTrace

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIRestoration/B13-20261026'


class Evidence:
    def __init__(self):
        self.tr = NativeTrace()

    def u(self, va, fmt='Q'):
        if self.tr.begin <= va < self.tr.end:
            return struct.unpack_from('<'+fmt, self.tr.code, va-self.tr.begin)[0]
        return struct.unpack_from('<'+fmt, self.tr.image.blob, self.tr.image.offset(va))[0]

    def string(self, va):
        off = self.tr.image.offset(va)
        end = self.tr.image.blob.index(b'\0', off)
        return self.tr.image.blob[off:end].decode('utf8')

    @staticmethod
    def rip(row):
        # Only the LEA forms used by this registration walker.
        return int(row['va'], 16)+row['size']+struct.unpack('<i', bytes.fromhex(row['bytes'])[-4:])[0]

    @lru_cache(None)
    def function(self, va):
        tr = self.tr
        owned = tr.function(va)
        spans = [(int(r['begin'], 16), int(r['end'], 16)) for r in owned.get('ranges', [])]
        entry = int(owned.get('owner_va', hex(va)), 16)
        if not spans:
            upper = min((tr.image.base+r[0] for r in tr.records if tr.image.base+r[0] > va), default=tr.end)
            spans = [(va, upper)]
        inside = lambda x: any(a <= x < b for a, b in spans)
        pending, rows, gaps = [entry], {}, []
        switches = []
        while pending:
            pc = pending.pop()
            while inside(pc) and pc not in rows:
                ins = next(tr.image.md.disasm(tr.code[pc-tr.begin:pc-tr.begin+15], pc, count=1), None)
                if ins is None or ins.mnemonic in ('int3', 'ud2'):
                    gaps.append(dict(va=hex(pc), reason='undecodable_or_trap')); break
                row = dict(va=hex(pc), size=ins.size, bytes=ins.bytes.hex(), mnemonic=ins.mnemonic, operands=ins.op_str)
                rows[pc] = row
                if ins.mnemonic.startswith('ret'): break
                if ins.mnemonic.startswith('j'):
                    if ins.op_str.startswith('0x'):
                        target = int(ins.op_str, 16)
                        if inside(target): pending.append(target)
                    elif pc == 0x141f75488:
                        # Verified cmp edi,5 / ja plus image-relative uint32 table.
                        # Pin applies to this exact EXE; never generalize to other jumps.
                        targets = [tr.image.base+self.u(0x141f75518+i*4, 'I') for i in range(6)]
                        if not all(inside(t) for t in targets):
                            raise ValueError('Evasion switch escaped owner spans')
                        pending.extend(targets)
                        switches.append(dict(branch=hex(pc), table='0x141f75518',
                                             targets=[hex(t) for t in targets]))
                    else:
                        gaps.append(dict(va=hex(pc), reason='indirect_branch_requires_table_resolution'))
                    if ins.mnemonic == 'jmp': break
                pc += ins.size
        return dict(entry=hex(entry), requested=hex(va), spans=[[hex(a),hex(b)] for a,b in spans],
                    instructions=[rows[k] for k in sorted(rows)], gaps=gaps, switches=switches,
                    scope='static_direct_reachable_cfg_no_runtime_validation')

    def lea_refs(self, targets):
        tr = self.tr
        result = []
        for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]', tr.code):
            off = m.start(); va = tr.begin+off
            target = va+7+struct.unpack_from('<i', tr.code, off+3)[0]
            if target not in targets: continue
            f = self.function(va)
            if any(int(r['va'],16)==va and r['mnemonic']=='lea' for r in f['instructions']):
                result.append(dict(target=hex(target), va=hex(va), function=f))
        return result

    def actions(self, bank=3, table=0x142ef5c30, indices=None):
        records = []
        for action in range(113) if indices is None else indices:
            records.append(dict(bank=bank, action=action, dti=hex(self.u(table+32*action+8)),
                                name=self.string(self.u(table+32*action+24))))
        targets = {int(r['dti'],16) for r in records}
        registrations = {}
        for ref in self.lea_refs(targets):
            f = ref['function']
            vts = [self.rip(r) for r in f['instructions'] if r['mnemonic']=='lea' and r['operands'].startswith('rax, [rip')]
            if len(vts)!=1: continue
            if not 0x143000000 < vts[0] < 0x144000000: continue
            factory = self.u(vts[0]+8)
            if not self.tr.begin <= factory < self.tr.end: continue
            build = self.function(factory)
            ctor = build
            ivts = lambda fn: [self.rip(r) for r in fn['instructions'] if r['mnemonic']=='lea' and '[rip' in r['operands'] and 0x143000000 < self.rip(r) < 0x144000000]
            if not ivts(ctor):
                jumps = [r for r in build['instructions'] if r['mnemonic']=='jmp' and r['operands'].startswith('0x')]
                if jumps: ctor = self.function(int(jumps[-1]['operands'],16))
            if not ivts(ctor): continue
            vt = ivts(ctor)[-1]
            slots = [self.u(vt+i*8) for i in range(10)]
            registrations[ref['target']] = dict(registration=f, factory=build, constructor=ctor,
                vtable=hex(vt), slots=[hex(v) for v in slots],
                entry=self.function(slots[6]), update=self.function(slots[7]), exit=self.function(slots[8]))
        return [dict(**r, **registrations.get(r['dti'], {})) for r in records]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--actions', action='store_true')
    p.add_argument('--function', action='append', default=[])
    p.add_argument('--string', action='append', default=[])
    p.add_argument('--disp', action='append', default=[])
    p.add_argument('--call', action='append', default=[])
    args = p.parse_args()
    e = Evidence(); OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'source-pins.json').write_text(json.dumps(e.tr.pin, indent=2)+'\n')
    if args.actions:
        rows=e.actions()
        (OUT/'actions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps([dict(action=r['action'],name=r['name'],entry=r.get('slots',[])[6:9]) for r in rows],ensure_ascii=False))
    for target_arg in args.call:
        target = int(target_arg, 0); refs = []
        for m in re.finditer(rb'[\xe8\xe9]', e.tr.code):
            off=m.start(); va=e.tr.begin+off
            if off+5>len(e.tr.code): continue
            if va+5+struct.unpack_from('<i',e.tr.code,off+1)[0] != target: continue
            f=e.function(va)
            if any(r['va']==hex(va) and r['mnemonic'] in ('call','jmp') and r['operands']==hex(target) for r in f['instructions']):
                refs.append(dict(va=hex(va),function=f))
        (OUT/f'call-{target_arg}.json').write_text(json.dumps(refs,indent=2)+'\n')
        print(target_arg,[(r['va'],r['function']['entry']) for r in refs])
    for va in args.function:
        f=e.function(int(va,0))
        (OUT/f'fn-{va}.json').write_text(json.dumps(f,indent=2)+'\n')
        for r in f['instructions']: print(r['va'],r['mnemonic'],r['operands'])
        print('GAPS',f['gaps'])
    for s in args.string:
        matches=list(re.finditer(re.escape(s.encode()+b'\0'),e.tr.image.blob))
        targets={e.tr.image.va(m.start()) for m in matches}
        refs=e.lea_refs(targets)
        safe=re.sub(r'[^A-Za-z0-9_-]','_',s)
        (OUT/f'string-{safe}.json').write_text(json.dumps(dict(string=s,targets=[hex(v) for v in targets],refs=refs),indent=2)+'\n')
        print(s,[(r['va'],r['function']['entry']) for r in refs])
    for disp in args.disp:
        value=int(disp,0); candidates={}
        for match in re.finditer(re.escape(struct.pack('<I',value)),e.tr.code):
            va=e.tr.begin+match.start(); rec=e.tr.record_at(va)
            if rec: candidates[e.tr.image.base+e.tr._owner(rec)[0]]=True
        found=[]
        for va in sorted(candidates):
            f=e.function(va)
            hits=[r for r in f['instructions'] if re.search(r'\+ '+hex(value)+r'\]',r['operands'])]
            if hits: found.append(dict(function=f,hits=hits))
        (OUT/f'disp-{disp}.json').write_text(json.dumps(found,indent=2)+'\n')
        print(disp,[(r['function']['entry'],[(i['va'],i['mnemonic'],i['operands']) for i in r['hits']]) for r in found])


if __name__ == '__main__': main()
