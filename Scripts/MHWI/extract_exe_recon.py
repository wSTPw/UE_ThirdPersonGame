"""Read-only extraction of what IS readable in the shipped game executable.

Produces a machine-readable record: PE layout, per-section entropy and x86-64
decodability, keyword string hits with file offsets and owning section, and
vtable resolution for the reflection corpus. No decryption, no memory dump,
no patching, no execution.

Usage:
  python Scripts/MHWI/extract_exe_recon.py [--exe <path>] [--out <json>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = r'F:\PCprogram\Steam\steamapps\common\Monster Hunter World\MonsterHunterWorld.exe'
DTI = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024/public/dti_prop_dump.h'
OUT = ROOT / 'Saved/MHWIRestoration/B21-20261028/exe-recon.json'
KEYWORDS = [b'wp03', b'swo', b'saya', b'sheathe', b'attach', b'equip', b'weapon',
            b'joint', b'MOD3', b'evwp', b'w03_00']
VTABLES = ['nHmTransition::cWeaponOn', 'nHmTransition::cWeaponOnPrev',
           'uModel', 'uMhModel', 'uDummyWeaponModel', 'cWeaponData', 'PlayerEquipList']


def parse_sections(data: bytes):
    e = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, e + 6)[0]
    optsize = struct.unpack_from('<H', data, e + 20)[0]
    entry = struct.unpack_from('<I', data, e + 24 + 16)[0]
    base = e + 24 + optsize
    rows = []
    for i in range(nsec):
        o = base + i * 40
        name = data[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsize, va, rsize, raw = struct.unpack_from('<IIII', data, o + 8)
        rows.append({'name': name, 'va': va, 'vsize': vsize, 'raw': raw, 'rawsize': rsize})
    return entry, rows


def entropy(blob: bytes) -> float:
    counts = Counter(blob)
    n = len(blob)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def decodable(blob: bytes, va: int, samples: int = 4000) -> float:
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    stride = max(1, len(blob) // samples)
    ok = tried = 0
    for off in range(0, len(blob) - 32, stride):
        tried += 1
        ins = list(md.disasm(blob[off:off + 32], va + off, count=4))
        if len(ins) == 4 and sum(i.size for i in ins) >= 16:
            ok += 1
    return ok / max(tried, 1)


def section_of(rows, off):
    for r in rows:
        if r['raw'] <= off < r['raw'] + r['rawsize']:
            return r['name'], r['va'] + (off - r['raw'])
    return '?', None


def string_hits(data: bytes, rows):
    out = {}
    for kw in KEYWORDS:
        hits = []
        i = data.find(kw)
        while i != -1 and len(hits) < 40:
            name, rva = section_of(rows, i)
            lo, hi = max(0, i - 48), min(len(data), i + 48)
            ctx = ''.join(chr(c) if 32 <= c < 127 else '.' for c in data[lo:hi])
            hits.append({'file_offset': i, 'section': name, 'rva': rva, 'context': ctx})
            i = data.find(kw, i + 1)
        out[kw.decode()] = {'count_capped_at': 40 if len(hits) == 40 else len(hits), 'hits': hits}
    return out


def vtable_rows(data: bytes, rows):
    text = DTI.read_text(encoding='utf-8', errors='ignore') if DTI.exists() else ''
    out = []
    for want in VTABLES:
        import re
        m = re.search(r'^// ' + re.escape(want) + r' vftable:(0x[0-9A-F]+), Size:(0x[0-9A-F]+)',
                      text, re.M)
        if not m:
            out.append({'class': want, 'found': False})
            continue
        va = int(m.group(1), 16)
        rva = va - 0x140000000
        name, _ = section_of(rows, 0)
        host = next((r for r in rows if r['va'] <= rva < r['va'] + max(r['vsize'], r['rawsize'])), None)
        entry = {'class': want, 'found': True, 'vtable_va': hex(va), 'size': m.group(2), 'section': host['name'] if host else '?'}
        if host:
            off = host['raw'] + (rva - host['va'])
            if off + 16 <= len(data):
                first, second = struct.unpack_from('<QQ', data, off)
                entry['first_slot'] = hex(first)
                entry['second_slot'] = hex(second)
                slot_section = next((r['name'] for r in rows
                                     if r['va'] <= first - 0x140000000 < r['va'] + max(r['vsize'], r['rawsize'])), '?')
                entry['first_slot_section'] = slot_section
        out.append(entry)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', default=DEFAULT_EXE)
    ap.add_argument('--out', default=str(OUT))
    args = ap.parse_args()
    path = Path(args.exe)
    data = path.read_bytes()
    entry, rows = parse_sections(data)
    sections = []
    for r in rows:
        blob = data[r['raw']:r['raw'] + r['vsize']]
        if not blob:
            continue
        row = {'name': r['name'], 'va': hex(r['va']), 'vsize': r['vsize'],
               'rawsize': r['rawsize'], 'entropy': round(entropy(blob[:1 << 20]), 3),
               'entry_section': r['va'] <= entry < r['va'] + max(r['vsize'], r['rawsize'])}
        if r['name'] == '.text':
            row['decodable_ratio'] = round(decodable(blob, 0x140000000 + r['va']), 4)
        sections.append(row)
    report = {
        'schema_version': 1,
        'status': 'read_only_static_extraction',
        'exe': {'path': str(path), 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(),
                'image_base': '0x140000000', 'entry_rva': hex(entry)},
        'sections': sections,
        'verdict': 'code section encrypted; reflection/data sections plain',
        'strings': string_hits(data, rows),
        'vtable_resolution': vtable_rows(data, rows),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print('sections:')
    for s in sections:
        print(f"  {s['name']:<10} {s['va']:>12} entropy {s['entropy']:.3f}"
              + (f" decodable {s['decodable_ratio']:.1%}" if 'decodable_ratio' in s else '')
              + ('  <-- entry' if s['entry_section'] else ''))
    print('strings:', {k: v['count_capped_at'] for k, v in report['strings'].items()})
    print('vtables:', [(v['class'], v.get('first_slot'), v.get('first_slot_section')) for v in report['vtable_resolution']])
    print('report', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
