"""Read pinned monster COL type-2 attacks offline; geometry/OAP semantics stay unknown.

Source: Synthlight/MHW-Editor col.bt, commit and hash in
Tools/MHW/rathalos-collision-sources.json. This is a project adapter, not execution
of the template. It follows name/geometry counts to ATK; no signature scanning.
The original file fingerprint is mandatory. OAP/CRC data is preserved opaque,
so successful structural reading is not a claim of full-file semantic decoding.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
MAGIC = 0x18091001
TYPES = {'uint': 'I', 'int': 'i', 'ushort': 'H', 'short': 'h',
         'ubyte': 'B', 'byte': 'b', 'float': 'f'}
DEFAULT_BASE = ROOT/'ArtSource/ThirdParty/MHWRathalos/nativePC'
PINS = ROOT/'Tools/MHW/rathalos-collision-sources.json'
KEYS = ('Motion_Value', 'Knock_back_Type', 'Knock_back_Lvl',
        'Guard_Stamina_Cost', 'Guard_Req', 'Element_Id', 'Element_Dmg', 'Stun')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_bytes(data, expected):
    if len(data) != expected['size'] or sha(data) != expected['sha256']:
        raise ValueError('Original source size/hash mismatch')


def load_fields(pins):
    source = pins['template']
    path = ROOT/source['cache']
    data = path.read_bytes()
    verify_bytes(data, {'size': source['bytes'], 'sha256': source['sha256']})
    text = data.decode('utf-8-sig')
    body = text[text.index('// Atk2'):text.index('// Atk3')]
    fields = re.findall(r'^\s*(uint|int|ushort|short|byte|ubyte|float)\s+(\w+)<',
                        body, re.M)
    if len(fields) != 47 or struct.calcsize('<'+''.join(TYPES[t] for t, _ in fields)) != 171:
        raise ValueError('Unqualified Atk2 layout')
    return fields


class Reader:
    def __init__(self, data):
        self.data, self.pos, self.pieces = data, 0, []

    def take(self, count):
        if count < 0 or count > len(self.data)-self.pos:
            raise ValueError('Truncated COL region at '+str(self.pos))
        value = self.data[self.pos:self.pos+count]
        self.pos += count
        self.pieces.append(value)
        return value

    def unpack(self, fmt):
        return struct.unpack('<'+fmt, self.take(struct.calcsize('<'+fmt)))

    def header(self, tag, fmt):
        value = self.unpack(fmt)
        if value[0] != MAGIC or value[1] != tag or value[2] != 111:
            raise ValueError('Unqualified COL block '+repr(tag))
        return value

    def count(self, count, minimum_width):
        if count > (len(self.data)-self.pos)//minimum_width:
            raise ValueError('Impossible COL count')

    def name(self):
        end = self.data.find(b'\0', self.pos)
        if end < 0:
            raise ValueError('Unterminated COL name')
        return self.take(end-self.pos+1)[:-1].decode('utf-8')


def read_col(data, fields):
    r = Reader(data)
    header = r.header(b'COL\0', 'I4s4I')
    r.count(header[5], 20)
    names = []
    for index in range(header[5]):
        start = r.pos
        name = r.name()
        geometry, move, unknown, unknown2, unknown3, uid = r.unpack('iiiHBI')
        names.append(dict(index=index, offset=start, name=name,
                          geometry_index=geometry, attack_index=move,
                          timeline_uid=uid,
                          unknown=[unknown, unknown2, unknown3]))
    node_offset = r.pos
    node = r.header(b'CLND', 'I4sIIIB')
    if node[4] not in (0, 1, 2):
        raise ValueError('Unknown geometry node type')
    r.count(node[3], 16)
    geometry = []
    for index in range(node[3]):
        start = r.pos
        geom = r.header(b'CLGM', 'I4sII')
        r.count(geom[3], 72)
        # col.bt defines a 72-byte inner record, followed by 27/59 bytes.
        # Preserve raw bytes: these fields are not qualified shape/bone data.
        r.take(geom[3]*72)
        r.take(27+(32 if node[4] == 2 else 0))
        geometry.append(dict(index=index, offset=start, bytes=r.pos-start,
                             inner_count=geom[3], raw_hex=data[start:r.pos].hex()))
    r.take(3)
    attack_header_offset = r.pos
    attack_header = r.header(b'ATK\0', 'I4sIII')
    count, kind = attack_header[3:]
    if kind != 2 and not (kind == 0 and count == 0):
        raise ValueError('Unsupported monster attack type/count')
    fmt = ''.join(TYPES[t] for t, _ in fields)
    width = struct.calcsize('<'+fmt)
    r.count(count, width)
    attacks = []
    for index in range(count):
        start = r.pos
        values = r.unpack(fmt)
        if values[0] != index:
            raise ValueError('Attack index mismatch')
        field_rows, offset = {}, start
        for (typ, name), value in zip(fields, values):
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError('Nonfinite attack field')
            field_rows[name] = dict(value=value, offset=offset)
            offset += struct.calcsize('<'+TYPES[typ])
        attacks.append(dict(index=index, offset=start, bytes=width,
                            fields=field_rows,
                            names=[n for n in names if n['attack_index'] == index]))
    attack_end = r.pos
    tail = r.take(len(data)-r.pos)
    # Upstream OAP tail layout is incomplete. Check the documented header only;
    # retain the rest and rely on mandatory original-file fingerprint, not padding.
    if len(tail) < 17 or struct.unpack_from('<I4sI', tail, 4) != (MAGIC, b'OAP\0', 111):
        raise ValueError('Unqualified OAP/CRC tail header')
    if b''.join(r.pieces) != data:
        raise ValueError('Byte-accounting roundtrip mismatch')
    return dict(bytes=len(data), names=names, node_offset=node_offset,
                node_type=node[4], geometry=geometry, attack_type=kind,
                attack_header_offset=attack_header_offset,
                attack_count=count, attack_record_size=width,
                attack_start=attack_header_offset+20, attack_end=attack_end,
                attacks=attacks, opaque_tail=dict(offset=attack_end, bytes=len(tail),
                    raw_hex=tail.hex(), sha256=sha(tail),
                    status='Preserved raw; OAP/CRC fields not fully decoded.'),
                accounted_bytes=r.pos, byte_roundtrip=True,
                fully_semantically_decoded=False)


def check_boundaries(data, fields, row, expected):
    checks = []
    def rejected(name, operation):
        try:
            operation()
        except (ValueError, UnicodeDecodeError, struct.error):
            checks.append(name)
        else:
            raise AssertionError('Corruption accepted: '+name)
    rejected('truncated_attack_region',
             lambda: read_col(data[:row['attack_end']-1], fields))
    damaged = bytearray(data)
    struct.pack_into('<I', damaged, row['attack_header_offset']+16, 99)
    rejected('unknown_attack_type', lambda: read_col(bytes(damaged), fields))
    damaged = bytearray(data)
    struct.pack_into('<I', damaged, 20, 0xffffffff)
    rejected('impossible_name_count', lambda: read_col(bytes(damaged), fields))
    damaged = bytearray(data)
    struct.pack_into('<I', damaged, row['node_offset']+12, 0xffffffff)
    rejected('impossible_geometry_count', lambda: read_col(bytes(damaged), fields))
    damaged = bytearray(data)
    damaged[row['attack_end']+8] ^= 1
    rejected('bad_oap_header', lambda: read_col(bytes(damaged), fields))
    rejected('appended_bytes_fingerprint', lambda: verify_bytes(data+b'\0', expected))
    rejected('truncated_source_fingerprint', lambda: verify_bytes(data[:-1], expected))
    damaged = bytearray(data)
    damaged[-1] ^= 1
    rejected('changed_opaque_tail_fingerprint', lambda: verify_bytes(bytes(damaged), expected))
    return dict(passed=True, checks=checks,
                scope='In-memory copies; no original resource was changed.')


def write_new_or_identical(path, value):
    data = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8')
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError('Refusing to replace different report: '+str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def run(base, manifest_path, output, evidence_path):
    pins = json.loads(PINS.read_text(encoding='utf-8'))
    fields = load_fields(pins)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    selected = [x for x in manifest['files'] if x['path'].endswith('.col')]
    actual = {p.relative_to(base).as_posix() for p in base.rglob('*.col')}
    if actual != {x['path'] for x in selected} or len(selected) != 42:
        raise ValueError('COL file set differs from qualified 42-file batch')
    rows, source_bytes = [], {}
    for entry in sorted(selected, key=lambda x: x['path']):
        rel = PurePosixPath(entry['path'])
        path = (base/rel).resolve()
        if rel.is_absolute() or '..' in rel.parts or not path.is_relative_to(base.resolve()):
            raise ValueError('Unsafe source path')
        data = path.read_bytes()
        verify_bytes(data, entry)
        row = dict(path=entry['path'], sha256=sha(data), **read_col(data, fields))
        rows.append(row)
        source_bytes[entry['path']] = data
    primary = next(x for x in rows if x['path'].endswith('/collision/em001.col'))
    expected = next(x for x in selected if x['path'] == primary['path'])
    validation = check_boundaries(source_bytes[primary['path']], fields, primary, expected)
    for row in rows:
        if (base/row['path']).read_bytes() != source_bytes[row['path']]:
            raise ValueError('Original source changed during read')
    counts = dict(files=len(rows), attack_files=sum(x['attack_count'] > 0 for x in rows),
                  empty_attack_files=sum(x['attack_count'] == 0 for x in rows),
                  attacks=sum(x['attack_count'] for x in rows),
                  type_counts=dict(Counter(str(x['attack_type']) for x in rows)))
    compact = []
    for row in rows:
        item = {k: row[k] for k in ('path','sha256','bytes','attack_type',
                'attack_count','attack_start','attack_end','fully_semantically_decoded')}
        item['name_count'] = len(row['names'])
        item['geometry_count'] = len(row['geometry'])
        item['opaque_tail_bytes'] = row['opaque_tail']['bytes']
        # All primary source records are retained; shell files each contain <=1.
        item['attacks'] = [dict(index=a['index'], offset=a['offset'],
            fields={k:a['fields'][k] for k in KEYS},
            names=[{k:n[k] for k in ('name','index','timeline_uid','geometry_index')}
                   for n in a['names']]) for a in row['attacks']]
        compact.append(item)
    boundary = ('Named Atk2 source fields, not final damage to a player. Native Japanese '
                'COL labels are retained, not verified action-ID bindings or translations. '
                'The shared 00 resource contains G-rank-labelled entries too; no LR-only '
                'eligibility is inferred. Geometry payload and OAP/CRC semantics remain unknown.')
    common = dict(schema=1, source_manifest=manifest_path.relative_to(ROOT).as_posix(),
                  source_manifest_sha256=sha(manifest_path.read_bytes()),
                  pins_path=PINS.relative_to(ROOT).as_posix(),
                  pins_sha256=sha(PINS.read_bytes()), counts=counts,
                  validation=validation, protected_sources_unchanged=True, boundary=boundary)
    write_new_or_identical(output, dict(**common, files=rows))
    write_new_or_identical(evidence_path, dict(**common, files=compact))
    print(json.dumps(dict(**counts, validation_checks=len(validation['checks']),
                          output=str(output), evidence=str(evidence_path))))
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_BASE.parent/'extraction-manifest.json')
    parser.add_argument('--output', type=Path, default=ROOT/'Saved/MHWRathalos-20261030-Format/collision.json')
    parser.add_argument('--evidence', type=Path, default=ROOT/'Tools/MHW/em001-collision-evidence.json')
    args = parser.parse_args()
    run(args.base.resolve(), args.manifest.resolve(), args.output.resolve(), args.evidence.resolve())
