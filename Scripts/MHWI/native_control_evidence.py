"""Read-only PE source evidence. Never launches or modifies the game.

Uses local Capstone/pefile wheels in Saved, and records exact RVA/hash evidence.
It is a static analysis helper, not an in-game hook or a native-semantics claim.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024'
sys.path.insert(0, str(OUT / 'python-deps'))
import capstone
import pefile


class Image:
    def __init__(self, path):
        self.path = Path(path)
        self.blob = self.path.read_bytes()
        self.pe = pefile.PE(data=self.blob, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = self.pe.sections
        self.has_bind_section = any(s.Name.startswith(b'.bind') for s in self.sections)
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        pdata = next(s for s in self.sections if s.Name.startswith(b'.pdata'))
        self.functions = [x for x in struct.iter_unpack('<III', self.blob[pdata.PointerToRawData:pdata.PointerToRawData + pdata.Misc_VirtualSize]) if x[0] and x[1] > x[0]]
        self.starts = [x[0] for x in self.functions]

    def offset(self, va):
        rva = va - self.base
        for s in self.sections:
            if s.VirtualAddress <= rva < s.VirtualAddress + s.SizeOfRawData:
                return s.PointerToRawData + rva - s.VirtualAddress
        raise ValueError(hex(va))

    def va(self, offset):
        for s in self.sections:
            if s.PointerToRawData <= offset < s.PointerToRawData + s.SizeOfRawData:
                return self.base + s.VirtualAddress + offset - s.PointerToRawData
        raise ValueError(offset)

    def function(self, va):
        """Return the containing unwind span, not a complete chained function."""
        rva = va-self.base
        i = bisect.bisect_right(self.starts, rva)-1
        if i < 0:
            raise ValueError('No unwind metadata at ' + hex(va))
        f = self.functions[i]
        if not f[0] <= rva < f[1]:
            raise ValueError('No unwind metadata at ' + hex(va))
        return (self.base + f[0], self.base + f[1])

    def disasm(self, begin, end=None):
        if self.has_bind_section:
            raise ValueError('Protected on-disk .bind image: random bytes are not native execution evidence. Supply a qualified analysis image.')
        if end is None:
            begin, end = self.function(begin)
        offset = self.offset(begin)
        return [dict(va=hex(i.address), size=i.size, bytes=i.bytes.hex(), mnemonic=i.mnemonic, operands=i.op_str)
                for i in self.md.disasm(self.blob[offset:offset + end-begin], begin)]

    def string_xrefs(self, text):
        matches = list(re.finditer(re.escape(text.encode() + b'\0'), self.blob))
        strings = [self.va(m.start()) for m in matches]
        result=[]
        code = next(s for s in self.sections if s.Name.startswith(b'.text'))
        raw = self.blob[code.PointerToRawData:code.PointerToRawData+code.SizeOfRawData]
        # RIP-relative LEA only. Each hit is decoded/length-checked before use.
        for m in re.finditer(b'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]', raw):
            off=m.start()
            va=self.base+code.VirtualAddress+off
            target=va+7+struct.unpack_from('<i',raw,off+3)[0]
            if target in strings:
                ins=list(self.md.disasm(raw[off:off+7],va))
                if ins and ins[0].size==7:
                    try:
                        begin,end=self.function(va)
                    except ValueError:
                        result.append(dict(va=hex(va),target=hex(target),function_begin=None,
                                           function_end=None,boundary_status='missing_unwind_metadata'))
                    else:
                        result.append(dict(va=hex(va), target=hex(target), function_begin=hex(begin),
                                           function_end=hex(end),boundary_status='single_unwind_span_not_complete_function'))
        return dict(strings=[hex(x) for x in strings],refs=result)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',default='F:/PCprogram/Steam/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe')
    p.add_argument('--string',action='append',default=[])
    p.add_argument('--function',action='append',default=[])
    p.add_argument('--out',default=str(OUT/'native-control-static.json'))
    args=p.parse_args()
    image=Image(args.exe)
    code=next(s for s in image.sections if s.Name.startswith(b'.text'))
    counts=Counter(image.blob[code.PointerToRawData:code.PointerToRawData+code.SizeOfRawData])
    entropy=-sum((v/code.SizeOfRawData)*math.log2(v/code.SizeOfRawData) for v in counts.values())
    result=dict(status='read_only_static_analysis',exe_path=str(image.path),exe_sha256=hashlib.sha256(image.blob).hexdigest(),image_base=hex(image.base),capstone_version=capstone.__version__,pefile_version=pefile.__version__,has_bind_section=image.has_bind_section,text_entropy_bits_per_byte=entropy,native_code_qualified=False if image.has_bind_section else None,sections=[dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=hex(s.VirtualAddress),raw_size=s.SizeOfRawData) for s in image.sections],strings={},functions={})
    strings=args.string or ['mMotionSpeed','PlMotionInput','cFSMPl_W03','mAttackAdjustAngleIndex','mTurnSpeed','mWeaponMotionNo']
    for text in strings:
        result['strings'][text]=image.string_xrefs(text)
    functions={int(x,0) for x in args.function}
    functions.update(int(r['function_begin'],16) for v in result['strings'].values() for r in v['refs'] if r['function_begin'] is not None)
    for va in sorted(functions):
        result['functions'][hex(va)]=image.disasm(va)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(out),exe_sha256=result['exe_sha256'],strings=result['strings'],function_count=len(functions)),indent=2))


if __name__=='__main__':
    main()
