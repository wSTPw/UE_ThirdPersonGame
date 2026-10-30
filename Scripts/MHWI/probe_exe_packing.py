"""Read-only packing probe for a shipped game executable.

Reports PE section table, entry-point section, per-section Shannon entropy and
the portion of a section that decodes as plausible x86-64. Used to decide
whether a static instruction-level audit is possible at all.

Does not patch, decrypt, dump or execute the target. Path is a command-line
argument so the report can be reproduced on any installation.
"""
from __future__ import annotations

import argparse
import math
import struct
from collections import Counter
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64

IMAGE_BASE_DEFAULT = 0x140000000


def sections(data: bytes) -> tuple[int, list[dict]]:
    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    optsize = struct.unpack_from('<H', data, e_lfanew + 20)[0]
    entry_rva = struct.unpack_from('<I', data, e_lfanew + 24 + 16)[0]
    base = e_lfanew + 24 + optsize
    rows = []
    for i in range(nsec):
        o = base + i * 40
        name = data[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsize, va, rsize, raw = struct.unpack_from('<IIII', data, o + 8)
        rows.append({'name': name, 'va': va, 'vsize': vsize, 'raw': raw,
                     'rawsize': rsize, 'entry': va <= entry_rva < va + max(vsize, rsize)})
    return entry_rva, rows


def entropy(blob: bytes) -> float:
    counts = Counter(blob)
    n = len(blob)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def decodable_ratio(blob: bytes, start_va: int, samples: int = 4000) -> float:
    """Share of evenly spaced windows that decode without an invalid opcode."""
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    stride = max(1, len(blob) // samples)
    ok = 0
    tried = 0
    for off in range(0, len(blob) - 32, stride):
        tried += 1
        chunk = blob[off:off + 32]
        ins = list(md.disasm(chunk, start_va + off, count=4))
        if len(ins) == 4 and sum(i.size for i in ins) >= 16:
            ok += 1
    return ok / max(tried, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('--base', type=lambda s: int(s, 0), default=IMAGE_BASE_DEFAULT)
    args = ap.parse_args()
    path = Path(args.exe)
    data = path.read_bytes()
    entry, rows = sections(data)
    print(f'{path.name}  {len(data):,} bytes  entry RVA {entry:#x}')
    for row in rows:
        blob = data[row['raw']:row['raw'] + row['rawsize']]
        if not blob:
            continue
        h = entropy(blob[:1 << 20])
        ratio = decodable_ratio(blob, args.base + row['va']) if row['name'] in ('.text',) else None
        tail = f'  decodable {ratio:.1%}' if ratio is not None else ''
        print(f"  {row['name']:<10} VA {row['va']:#010x} size {row['rawsize']:>10,}  "
              f"entropy {h:.3f}{tail}{'   <-- entry' if row['entry'] else ''}")
    text = next((r for r in rows if r['name'] == '.text'), None)
    if text:
        h = entropy(data[text['raw']:text['raw'] + min(text['rawsize'], 1 << 20)])
        ratio = decodable_ratio(data[text['raw']:text['raw'] + text['rawsize']], args.base + text['va'])
        packed = h > 7.9 or ratio < 0.2
        print(f"verdict: .text entropy {h:.3f}, decodable {ratio:.1%} -> "
              f"{'packed/encrypted, static instruction audit not possible' if packed else 'plain code, static audit possible'}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
