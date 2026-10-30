"""Parse the per-weapon-type setting tables (hm/wp/wpNN/wpNN_setting.cms).

Layout established on all 14 shipped files (identical rule, different counts):

  header   24 B : u32 magic 'CMS', u32 version(4), u32 14, u32 entry_count, u32 0, u32 0
  records  count x 36 B : f32[3] + u32[6]
  trailer  rest : sub-block with (float, index) pairs, then a shared tail

The trailer's last 8 floats are identical in every file (40, 90, 110, 170, 200,
250, 800, 800), so that part is a shared distance table, not weapon data.
The meaning of the 3 floats per record is NOT decoded. Evidence against reading
them as per-weapon belt placement: the second component is -380 in every weapon
type from great sword to bow.

Usage: python Scripts/MHWI/dump_weapon_settings.py
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp'
OUT = ROOT / 'Saved/MHWIRestoration/B21-20261028/weapon-setting-tables.json'
HEADER = 24
RECORD = 36


def parse(path: Path) -> dict:
    data = path.read_bytes()
    magic, version, const, count, z0, z1 = struct.unpack_from('<6I', data, 0)
    records = []
    for i in range(count):
        off = HEADER + i * RECORD
        xyz = struct.unpack_from('<3f', data, off)
        ints = struct.unpack_from('<6I', data, off + 12)
        records.append({'index': i, 'offset': off,
                        'triple': [round(v, 3) for v in xyz],
                        'words': [f'0x{w:08X}' for w in ints],
                        'ints': list(ints)})
    trailer_off = HEADER + count * RECORD
    trailer = data[trailer_off:]
    t_words = list(struct.unpack_from('<%dI' % (len(trailer) // 4), trailer))
    t_floats = list(struct.unpack_from('<%df' % (len(trailer) // 4), trailer))
    return {
        'file': str(path.relative_to(ROOT)),
        'bytes': len(data),
        'header': {'magic': hex(magic), 'version': version, 'constant': const,
                   'entry_count': count, 'reserved': [z0, z1]},
        'layout_ok': len(data) == trailer_off + len(trailer) and len(trailer) > 0,
        'records': records,
        'trailer': {'offset': trailer_off, 'bytes': len(trailer),
                    'ints': t_words, 'floats': [round(v, 3) for v in t_floats],
                    'tail8': [round(v, 1) for v in t_floats[-8:]] if len(t_floats) >= 8 else []},
    }


def main() -> int:
    rows = [parse(p) for p in sorted(SRC.glob('wp*/*_setting.cms'))]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'schema_version': 1, 'layout': {
        'header_bytes': HEADER, 'record_bytes': RECORD, 'record_fields': 'f32[3] + u32[6]'},
        'file_count': len(rows), 'tables': rows}, ensure_ascii=False, indent=1), encoding='utf-8')
    ok = sum(1 for r in rows if r['layout_ok'])
    tails = {tuple(r['trailer']['tail8']) for r in rows}
    print(f'files {len(rows)}  layout_ok {ok}/{len(rows)}  distinct tail8 {len(tails)}')
    print('shared tail8:', tails)
    ls = next(r for r in rows if 'wp03' in r['file'])
    print(f"\nwp03 records ({len(ls['records'])}), trailer {ls['trailer']['bytes']} B at {ls['trailer']['offset']}")
    for rec in ls['records']:
        print(f"  #{rec['index']:>2} off {rec['offset']:>4}  {str(rec['triple']):<26} ints {rec['ints']}")
    print('report', OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
