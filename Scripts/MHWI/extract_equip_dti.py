"""Structured extract of the reflection (DTI) corpus for weapon/equipment classes.

The corpus itself is plain in .rdata of the shipped build, so class sizes, field
offsets and vtable addresses are readable without touching encrypted code. This
script converts the flat dump into JSON + CSV so field offsets can be used
directly (e.g. uModel::mParentNo at +0x150).

Usage: python Scripts/MHWI/extract_equip_dti.py [--filter REGEX]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024/public/dti_prop_dump.h'
OUT = ROOT / 'Saved/MHWIRestoration/B21-20261028/dti-weapon-equip.json'
CSV_OUT = ROOT / 'Saved/MHWIRestoration/B21-20261028/dti-weapon-equip-fields.csv'
DEFAULT_FILTER = r'weapon|equip|\bwp\b|nwp|umodel|umhmodel|joint|dummyweapon'

HEAD = re.compile(r'^// (?P<cls>\S+) vftable:(?P<vt>0x[0-9A-F]+), Size:(?P<size>0x[0-9A-F]+), CRC32:(?P<crc>0x[0-9A-F]+)')
DECL = re.compile(r'^class (?P<cls>\S+) /\*:(?P<bases>.*?)\*/')
FIELD = re.compile(r"^\s*(?P<type>[\w:]+) '(?P<name>[^']+)'(?P<arr>\[\*\])?\s*; // Offset:(?P<off>\S+),(?P<rest>.*)$")


def parse(text: str) -> list[dict]:
    classes: list[dict] = []
    current = None
    for line in text.split('\n'):
        m = HEAD.match(line)
        if m:
            current = {'class': m['cls'], 'vtable': m['vt'], 'size': m['size'], 'crc32': m['crc'],
                       'bases': [], 'fields': []}
            classes.append(current)
            continue
        if current is None:
            continue
        d = DECL.match(line)
        if d:
            current['bases'] = [b.strip() for b in d['bases'].split(',') if b.strip()]
            continue
        f = FIELD.match(line)
        if f:
            rest = f['rest']
            off = f['off']
            current['fields'].append({
                'type': f['type'].strip(), 'name': f['name'],
                'array': bool(f['arr']),
                'offset': off if off.startswith('0x') and int(off, 16) < 0x1000000 else None,
                'pseudo': off == '0x7FFFFFFFFFFFFFFF',
                'getter': (re.search(r'Getter:(0x[0-9A-F]+)', rest) or [None, None])[1],
                'setter': (re.search(r'Setter:(0x[0-9A-F]+)', rest) or [None, None])[1],
            })
    return classes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--filter', default=DEFAULT_FILTER)
    args = ap.parse_args()
    rx = re.compile(args.filter, re.I)
    classes = [c for c in parse(SRC.read_text(encoding='utf-8', errors='ignore'))
               if rx.search(c['class'])]
    for c in classes:
        c['field_count'] = len(c['fields'])
        c['real_fields'] = sum(1 for f in c['fields'] if f['offset'])
    classes.sort(key=lambda c: c['class'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'schema_version': 1, 'source': str(SRC.relative_to(ROOT)),
                               'filter': args.filter, 'class_count': len(classes),
                               'classes': classes}, ensure_ascii=False, indent=1), encoding='utf-8')
    with CSV_OUT.open('w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['class', 'vtable', 'size', 'field', 'type', 'offset', 'getter', 'setter'])
        for c in classes:
            for f in c['fields']:
                w.writerow([c['class'], c['vtable'], c['size'], f['name'], f['type'],
                            f['offset'] or ('pseudo' if f['pseudo'] else ''), f['getter'] or '', f['setter'] or ''])
    print(f'classes {len(classes)}  fields {sum(c["field_count"] for c in classes)}')
    for c in classes[:40]:
        print(f"  {c['class']:<38} {c['size']:>7} fields {c['field_count']:>3} real {c['real_fields']:>3}")
    print('json', OUT)
    print('csv ', CSV_OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
