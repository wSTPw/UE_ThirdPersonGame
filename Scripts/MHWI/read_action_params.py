"""Read pinned MHWI v2 ActionData properties without executing game/upstream code.

Layout: Fexty12573/MHW-010-Templates actp2.bt + UnitProperty.bt, MIT.
See Tools/MHW/rathalos-actp2-sources.json for hashes and the Property-wrapper
adaptation. Reject unobserved tags/versions; do not infer attack damage from
ActionData array indexes or type-name candidates. Game inputs remain read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/data/em001.actp2'
SOURCE_SHA = '96dcdc5b6b7ae5853cbd917f6f2cf122749b25a190e5e018d7e22f07ebc1ce7e'
PINS = ROOT / 'Tools/MHW/rathalos-actp2-sources.json'
DTI = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024/public/dti_prop_dump.h'
OUTPUT = ROOT / 'Saved/MHWRathalos-20261030-Format/actp2.json'
SUMMARY = ROOT / 'Tools/MHW/em001-actp2-evidence.json'
FORMATS = {0x04B747F9: '<f', 0x12491816: '<B', 0x189831BA: '<i', 0x4F9357BC: '<4f'}
TAGS = {0x04B747F9: 'Float', 0x12491816: 'Bool', 0x189831BA: 'Int32',
        0x4F9357BC: 'Vector4', 0x65EA28E0: 'PageEnd'}
PAGE_END = 0x65EA28E0
TIME_FIELDS = {'mLoopTime', 'mStruggleSec', 'mTrapEndSec', 'mDefLoopMotPlayCount', 'mSwitchLoopMotCount'}


class FormatError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {'path': path.resolve().as_posix(), 'bytes': len(data), 'sha256': sha(data)}


class Reader:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def read(self, fmt: str):
        size = struct.calcsize(fmt)
        if self.pos + size > len(self.data):
            raise FormatError(f'Truncated {fmt} at {self.pos:#x}')
        values = struct.unpack_from(fmt, self.data, self.pos)
        self.pos += size
        return values[0] if len(values) == 1 else list(values)

    def string(self) -> str:
        end = self.data.find(b'\0', self.pos)
        if end < 0:
            raise FormatError(f'Unterminated string at {self.pos:#x}')
        try:
            value = self.data[self.pos:end].decode('utf-8')
        except UnicodeDecodeError as exc:
            raise FormatError(f'Invalid UTF-8 at {self.pos:#x}') from exc
        self.pos = end + 1
        return value


def decode(data: bytes) -> dict:
    r = Reader(data)
    header = r.read('<5I')
    if header[:3] != [0x18091001, 0x00327061, 2]:
        raise FormatError('Unsupported ACTP2 header/version')
    count = header[4]
    if count > (len(data) - 20) // 9:
        raise FormatError('ActionData count exceeds minimum record budget')
    actions = []
    for index in range(count):
        start = r.pos
        dti, used, crc = r.read('<IBI')
        if dti != 0x11E2D786 or used not in (0, 1):
            raise FormatError(f'Unsupported ActionData DTI/use at {start:#x}')
        count_offset = r.pos if used else None
        prop_count = r.read('<I') if used else 0
        if prop_count > (len(data) - r.pos) // 4:
            raise FormatError(f'Property count exceeds minimum budget at {r.pos:#x}')
        properties = []
        for prop_index in range(prop_count):
            offset = r.pos
            tag = r.read('<I')
            if tag not in TAGS:
                raise FormatError(f'Unsupported Property tag {tag:#x} at {offset:#x}')
            row = {'index': prop_index, 'offset': offset, 'tag': tag, 'tag_name': TAGS[tag]}
            if tag != PAGE_END:
                row['value'] = r.read(FORMATS[tag])
                row['name'] = r.string()
                row['property_type'] = r.read('<I')
                row['type_name'] = r.string()
                row['attribute'], row['property_index'], row['property_count'] = r.read('<3I')
                row['user'] = r.read('<B')
                if tag == 0x12491816 and row['value'] not in (0, 1):
                    raise FormatError(f'Non-boolean Bool Property at {offset:#x}')
            row['end'] = r.pos
            properties.append(row)
        actions.append({'index': index, 'offset': start, 'end': r.pos, 'dti': dti,
                        'used': used, 'name_crc': crc, 'property_count_offset': count_offset,
                        'properties': properties})
    if r.pos != len(data):
        raise FormatError(f'Unexpected tail: {len(data)-r.pos} bytes at {r.pos:#x}')
    return {'header': header, 'consumed': r.pos, 'actions': actions}


def encode(parsed: dict) -> bytes:
    data = bytearray(struct.pack('<5I', *parsed['header']))
    for action in parsed['actions']:
        data += struct.pack('<IBI', action['dti'], action['used'], action['name_crc'])
        if action['used']:
            data += struct.pack('<I', len(action['properties']))
        for row in action['properties']:
            tag = row['tag']
            data += struct.pack('<I', tag)
            if tag == PAGE_END:
                continue
            value = row['value']
            data += struct.pack(FORMATS[tag], *(value if isinstance(value, list) else [value]))
            data += row['name'].encode('utf-8') + b'\0'
            data += struct.pack('<I', row['property_type'])
            data += row['type_name'].encode('utf-8') + b'\0'
            data += struct.pack('<3IB', row['attribute'], row['property_index'], row['property_count'], row['user'])
    return bytes(data)


def verify_pins(path: Path) -> dict:
    pins = json.loads(path.read_text(encoding='utf-8'))
    for row in pins['files']:
        target = (ROOT / row['path']).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file():
            raise FormatError('Missing/outside pinned cache: ' + row['path'])
        data = target.read_bytes()
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise FormatError('Modified pinned source: ' + row['path'])
    return pins


def name_candidates(path: Path | None) -> tuple[dict, dict]:
    if path is None or not path.exists():
        return {}, {'available': False, 'boundary': 'No DTI candidate mapping attempted'}
    data = path.read_bytes()
    text = data.decode('utf-8-sig')
    names = sorted(set(re.findall(r'^class (nActEm\w+::([A-Za-z0-9_]+))\b', text, re.M)))
    result = defaultdict(list)
    for full, tail in names:
        snake = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', tail)
        snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', snake).upper()
        candidate = 'ACTION::' + snake
        crc = (~zlib.crc32(candidate.encode('ascii'))) & 0xFFFFFFFF
        result[crc].append({'candidate': candidate, 'derived_from_dti_class': full})
    info = identity(path)
    info.update(available=True, source_header=text.splitlines()[0],
                candidate_classes=len(names),
                derivation='nActEm* class basename CamelCase -> ACTION::UPPER_SNAKE; complement CRC32, no high-bit mask',
                boundary='Derived candidate names only; dump header is 2021-03-23. Exact hash equality does not establish current-game registration, motion binding, clock units or runtime duration.')
    return dict(result), info


def self_check(data: bytes, parsed: dict) -> dict:
    results = {'roundtrip_exact': encode(parsed) == data}
    first = next(a for a in parsed['actions'] if a['properties'])
    fixtures = {'truncated': data[:-1], 'unexpected_tail': data + b'\0'}
    for name, offset, value in [('unknown_property_tag', first['properties'][0]['offset'], 0xDEADBEEF),
                                ('action_count_overflow', 16, 0xFFFFFFFF),
                                ('property_count_overflow', first['property_count_offset'], 0xFFFFFFFF)]:
        damaged = bytearray(data)
        struct.pack_into('<I', damaged, offset, value)
        fixtures[name] = bytes(damaged)
    damaged = bytearray(data)
    struct.pack_into('<I', damaged, 8, 3)
    fixtures['unsupported_version'] = bytes(damaged)
    for name, fixture in fixtures.items():
        try:
            decode(fixture)
        except FormatError:
            results[name + '_rejected'] = True
        else:
            results[name + '_rejected'] = False
    if not all(results.values()):
        raise FormatError('Self-check failed: ' + str(results))
    return results


def run(args) -> dict:
    pins = verify_pins(args.pins)
    data = args.source.read_bytes()
    if sha(data) != SOURCE_SHA:
        raise FormatError('Source fingerprint differs from pinned em001 source')
    parsed = decode(data)
    if encode(parsed) != data:
        raise FormatError('Decode/encode byte roundtrip mismatch')
    candidates, candidate_info = name_candidates(args.dti)
    tag_counts, names = Counter(), Counter()
    timing = []
    for action in parsed['actions']:
        action['name_crc_hex'] = f'0x{action["name_crc"]:08x}'
        action['name_candidates'] = candidates.get(action['name_crc'], [])
        for prop in action['properties']:
            tag_counts[prop['tag_name']] += 1
            if 'name' in prop:
                names[prop['name']] += 1
            if prop.get('name') in TIME_FIELDS:
                timing.append({'action_index': action['index'], 'name_crc': action['name_crc_hex'],
                               'candidate_names': sorted(set(x['candidate'] for x in action['name_candidates'])),
                               'offset': prop['offset'], 'field': prop['name'], 'value': prop['value'],
                               'type_name': prop['type_name'],
                               'status': 'raw_source_parameter; candidate_action_name_only; runtime_clock_unverified'})
    counts = {'actions': len(parsed['actions']), 'enabled_actions': sum(a['used'] for a in parsed['actions']),
              'property_items': sum(tag_counts.values()), 'named_properties': sum(names.values()),
              'distinct_property_names': len(names), 'tag_counts': dict(tag_counts),
              'actions_with_candidate_name': sum(bool(a['name_candidates']) for a in parsed['actions']),
              'actions_with_no_candidate_name': sum(not a['name_candidates'] for a in parsed['actions']),
              'actions_with_distinct_candidate_name_collision': sum(len(set(x['candidate'] for x in a['name_candidates'])) > 1 for a in parsed['actions'])}
    summary = {'schema': 1, 'mode': 'offline_source_layout_only', 'passed': True,
               'source': identity(args.source), 'script': identity(Path(__file__)),
               'layout_pins': identity(args.pins), 'layout_commit': pins['commit'],
               'adaptation': pins['adaptation'], 'counts': counts, 'consumed': parsed['consumed'],
               'tail_bytes': len(data)-parsed['consumed'], 'roundtrip_exact': True,
               'name_candidates_source': candidate_info, 'property_name_counts': dict(sorted(names.items())),
               'direct_damage_fields': [],
               'damage_boundary': 'All 111 names reviewed: no direct attack damage/knockback/stun numeric field in this file. mbRideSuccessDamage and mbDisableFriendHitS are booleans; do not use as damage values. Does not establish which other resource supplies damage.',
               'timing_parameters': timing,
               'runtime_boundary': 'No original-game/UE execution. ACTP2 array index is not a proved action ID, motion ID, attack ID or clagger/knockdown duration.'}
    if args.self_check:
        summary['self_checks'] = self_check(data, parsed)
    parsed.update(summary=summary)
    targets = [args.output.resolve(), args.summary.resolve()]
    protected = [args.source.resolve(), args.pins.resolve(), *( (ROOT/row['path']).resolve() for row in pins['files'])]
    if args.dti is not None and args.dti.exists():
        protected.append(args.dti.resolve())
    if len(set(targets)) != len(targets) or any(t in protected for t in targets):
        raise FormatError('Outputs must be distinct from each other and all source inputs')
    for target, value in [(args.output, parsed), (args.summary, summary)]:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'consumed': len(data), 'counts': counts,
                      'self_checks': summary.get('self_checks'), 'output': str(args.output),
                      'summary': str(args.summary)}, ensure_ascii=False))
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=SOURCE)
    ap.add_argument('--pins', type=Path, default=PINS)
    ap.add_argument('--dti', type=Path, default=DTI)
    ap.add_argument('--output', type=Path, default=OUTPUT)
    ap.add_argument('--summary', type=Path, default=SUMMARY)
    ap.add_argument('--self-check', action='store_true')
    args = ap.parse_args()
    try:
        run(args)
    except (OSError, ValueError, KeyError, struct.error) as exc:
        ap.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
