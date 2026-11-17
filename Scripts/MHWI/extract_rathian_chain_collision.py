"""Qualify em001 BITE collision fields and preserve remaining native dependencies.

Only reads hash-pinned game resources and a qualified non-executable text copy.
Produces a contact adapter profile, never a guessed damage or re-hit rule.
The default engineering profile keeps unqualified action/clock/basis gates false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from audit_native_timing import parse_lmt
from read_monster_collision import load_fields, read_col, verify_bytes
from trace_outstanding_evidence import Evidence

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'ArtSource/ThirdParty/MHWRathalos'
NATIVE = BASE / 'nativePC'
COL_REL = 'em/em001/00/collision/em001.col'
LMT_REL = 'em/em001/00/mot/em001_02/em001_02.lmt'
MOD_REL = 'em/em001/00/mod/em001_00.mod3'
DEFAULT_OUT = ROOT / 'Tools/MHW/rathian-first-chain-collision.json'
FULL_OUT = ROOT / 'Saved/MHWI-Rathian-FirstChain-20261031/collision-native-proof.json'
NODE0 = 0xB296CA66
FLAG0 = 150806694
GROUP = 956269290


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256=sha(raw))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def original(path, rows):
    item = next(x for x in rows if x['path'] == path)
    raw = (NATIVE / path).read_bytes()
    verify_bytes(raw, item)
    return raw


def decode_geometry(raw, offset, count):
    # Current native writer 0x1419c14a0, current reflected fields 0x1419c0460.
    # Offsets here belong to the 72-byte *serialized* record, not the runtime object.
    fields = [
        ('is_use_data', 'B', 0, 0x60), ('shape', 'B', 1, 0x08),
        ('radius', 'f', 2, 0x18), ('extent', '3f', 6, 0x50),
        ('joint0', 'h', 18, 0x10), ('joint1', 'h', 20, 0x12),
        ('offset0', '3f', 22, 0x30), ('offset1', '3f', 34, 0x40),
        ('option', 'B', 46, 0x09), ('scale_option', 'B', 47, 0x0A),
        ('priority', 'B', 48, 0x0B), ('region_no', 'H', 49, 0x14),
        ('layer', 'B', 51, 0x0C), ('range_check_base_joint', 'h', 52, 0x16),
        ('angle0', '2f', 54, 0x20), ('angle1', '2f', 62, 0x28),
        ('inner_index', 'H', 70, 0x0E),
    ]
    result = []
    for index in range(count):
        begin = offset + 16 + index * 72
        part = raw[begin:begin + 72]
        if len(part) != 72:
            raise ValueError('Truncated native geometry record')
        rebuilt = bytearray(72)
        values = {}
        locations = {}
        for name, kind, relative, object_offset in fields:
            unpacked = struct.unpack_from('<' + kind, part, relative)
            if any(isinstance(v, float) and not math.isfinite(v) for v in unpacked):
                raise ValueError('Nonfinite native geometry field')
            struct.pack_into('<' + kind, rebuilt, relative, *unpacked)
            values[name] = list(unpacked) if len(unpacked) > 1 else unpacked[0]
            locations[name] = dict(file_offset=begin + relative, object_offset=hex(object_offset))
        if bytes(rebuilt) != part:
            raise ValueError('72-byte semantic geometry roundtrip failed')
        result.append(dict(index=index, file_offset=begin, raw_sha256=sha(part),
                           fields=values, locations=locations, byte_roundtrip=True))
    return result


def bone_lookup(raw):
    if raw[:4] != b'MOD\0' or struct.unpack_from('<H', raw, 4)[0] != 237:
        raise ValueError('Requires MOD3 v237')
    count = struct.unpack_from('<H', raw, 6)[0]
    start = struct.unpack_from('<Q', raw, 48)[0]
    remap_offset = start + count * (24 + 64 + 64)
    remap = raw[remap_offset:remap_offset + 512]
    if count != 140 or len(remap) != 512:
        raise ValueError('Unexpected native skeleton/remap extent')
    names = {}
    for function, index in enumerate(remap):
        if index == 255:
            continue
        if index >= count:
            raise ValueError('Invalid native remap index')
        names[function] = dict(source_index=index, ue_imported_name=f'bone_{function:03}')
    return count, remap_offset, names


def native_proof():
    e = Evidence()  # Revalidates EXE and non-executable analysis text SHA256.
    addresses = [0x1401ECE10, 0x1419C0460, 0x1419C1080, 0x1419C14A0,
                 0x1412E0060, 0x1405A3650, 0x1424A8820, 0x1424A7440]
    functions = {hex(a): e.function(a) for a in addresses}
    instruction_map = {r['va']: r for f in functions.values() for r in f['instructions']}
    anchors = {
        0x1419C14E2: ('movzx', 'esi, byte ptr [rdi + 8]'),
        0x1419C150A: ('movss', 'xmm1, dword ptr [rdi + 0x18]'),
        0x1419C1546: ('movzx', 'edx, word ptr [rdi + 0x10]'),
        0x1419C1553: ('movzx', 'edx, word ptr [rdi + 0x12]'),
        0x1412E069C: ('call', '0x1405a3650'),
        0x1412E06A1: ('lea', 'rsi, [rdi + 0x30]'),
        0x1412E06B9: ('call', '0x14024ba60'),
        0x1412E07A7: ('call', '0x1405a3650'),
        0x1412E07B5: ('lea', 'rcx, [rdi + 0x40]'),
        0x1412E08B4: ('movzx', 'ecx, byte ptr [rdi + 8]'),
        0x1412E08C3: ('je', '0x1412e0f55'),
        0x1412E110D: ('mulss', 'xmm13, dword ptr [rdi + 0x18]'),
        0x1412E1126: ('movss', 'dword ptr [rax + 0x20], xmm7'),
        0x1412E113D: ('movss', 'dword ptr [rax + 0x30], xmm9'),
        0x1412E1156: ('movss', 'dword ptr [rax + 0x40], xmm13'),
        0x1405A365B: ('and', 'edx, 0x1ff'),
        0x1405A3661: ('movzx', 'r8d, byte ptr [rdx + rax]'),
        0x1405A3670: ('lea', 'rax, [rax + rax*2]'),
        0x1405A3674: ('shl', 'rax, 6'),
    }
    checked = []
    for address, expected in anchors.items():
        row = instruction_map.get(hex(address))
        if row is None or (row['mnemonic'], row['operands']) != expected:
            raise ValueError(('Native collision anchor changed', hex(address), expected, row))
        checked.append(row)
    # Rebind names to actual offsets from the current EXE; old DTI offsets are not trusted.
    reflected = {}
    rows = functions['0x1419c0460']['instructions']
    for i, row in enumerate(rows):
        if row['mnemonic'] != 'lea' or '[rip' not in row['operands']:
            continue
        try:
            name = e.string(e.rip(row))
        except (ValueError, UnicodeDecodeError):
            continue
        if not name.startswith('m'):
            continue
        targets = [x for x in rows[i + 1:i + 8] if x['mnemonic'] == 'lea'
                   and (x['operands'].startswith('rax, [rdi + ') or x['operands'].startswith('rax, [rcx + '))]
        if len(targets) == 1:
            offset = int(targets[0]['operands'].split('+ ')[1].rstrip(']'), 0)
            reflected[name] = dict(object_offset=hex(offset), name_reference=row['va'],
                                   field_reference=targets[0]['va'])
    expected_offsets = dict(mShape=8, mRadius=0x18, mJnt0=0x10, mJnt1=0x12,
                            mOffset0=0x30, mOffset1=0x40, mExtent=0x50,
                            mOption=9, mScaleOption=10, mIsUseData=0x60)
    for key, expected in expected_offsets.items():
        if int(reflected.get(key, {}).get('object_offset', '-1'), 16) != expected:
            raise ValueError(('Current reflected field mismatch', key))
    type5 = json.loads((ROOT/'Tools/MHW/foresight-timl-semantics-20261030.json').read_text(encoding='utf-8'))
    if type5['sources']['exe']['sha256'] != e.tr.pin['exe']['sha256']:
        raise ValueError('TIML mask semantics proof belongs to another EXE')
    summaries = {}
    for address, function in functions.items():
        raw = b''.join(bytes.fromhex(x['bytes']) for x in function['instructions'])
        summaries[address] = dict(instructions=len(function['instructions']),
                                  reachable_instruction_bytes_sha256=sha(raw),
                                  spans=function['spans'], gaps=function['gaps'])
    compact = dict(source=e.tr.pin, checked_anchors=checked, current_reflection=reflected,
                   functions=summaries,
                   geometry_semantics=dict(shape_0='sphere', shape_1='capsule', shape_2='box',
                       capsule_endpoints='bone_world_matrix(jointN).transform_point(offsetN)',
                       joint_selector='(joint & 0x1ff) -> 512-byte remap -> native bone array, stride 0xc0',
                       scale_scope='Runtime adapter admits uniform nonzero scale only; native nonuniform scale modes not implemented'),
                   timl_mask=dict(expression=type5['native_semantics']['expression'],
                       endpoint=type5['native_semantics']['endpoint_evidence'],
                       source=identity(ROOT/'Tools/MHW/foresight-timl-semantics-20261030.json')))
    return compact, dict(**compact, full_functions=functions)


def build(output):
    manifest = json.loads((BASE/'extraction-manifest.json').read_text(encoding='utf-8'))
    originals = {rel: original(rel, manifest['files']) for rel in (COL_REL, LMT_REL, MOD_REL)}
    pins_path = ROOT/'Tools/MHW/rathalos-collision-sources.json'
    pins = json.loads(pins_path.read_text(encoding='utf-8'))
    parsed = read_col(originals[COL_REL], load_fields(pins))
    reference = [n for n in parsed['names'] if n['timeline_uid'] == 32]
    if len(reference) != 1 or reference[0]['geometry_index'] != 14 or reference[0]['attack_index'] != 7:
        raise ValueError('BITE candidate UID32 mapping changed')
    geometry = parsed['geometry'][14]
    shapes = decode_geometry(originals[COL_REL], geometry['offset'], geometry['inner_count'])
    if len(shapes) != 5 or any(x['fields']['shape'] != 1 or x['fields']['option'] != 0
                              or x['fields']['scale_option'] != 0 for x in shapes):
        raise ValueError('BITE geometry is outside qualified plain-capsule subset')
    count, remap_offset, names = bone_lookup(originals[MOD_REL])
    lmt = parse_lmt((NATIVE/LMT_REL).resolve(), {}, {})
    entry = next(e for e in lmt['entries'] if e['index'] == 1)
    groups = [g for g in entry['groups'] if g['hash'] == GROUP]
    if len(groups) != 1:
        raise ValueError('Ambiguous collision timeline group')
    group = groups[0]
    nodes = [t for t in group['tracks'] if t['hash'] == NODE0]
    flags = [t for t in group['tracks'] if t['hash'] == FLAG0]
    if len(nodes) != 1 or len(flags) != 1 or [(k['frame'], k['value']) for k in nodes[0]['keys']] != [(0.0, 32)]:
        raise ValueError('Expected static NodeID[0]=32 binding is absent')
    keys = flags[0]['keys']
    if [(k['frame'], k['value'], k['control_l'], k['transition']) for k in keys] != [(0.0,7,7,5),(23.0,0,7,5)]:
        raise ValueError('BITE raw mFlag mask keys changed')
    state, intervals = 0, []
    for index, key in enumerate(keys):
        state = (state & (~int(key['control_l']) & 0xffffffff)) | int(key['value'])
        stop = keys[index+1]['frame'] if index+1 < len(keys) else entry['source_frame_count']-1
        if state & 1:
            intervals.append([key['frame'], stop])
    if intervals != [[0.0,23.0]]:
        raise ValueError('Native type5 bit0 candidate window mismatch')
    proof, full = native_proof()
    runtime_capsules = []
    for shape in shapes:
        values = shape['fields']
        for endpoint in (0,1):
            function = values[f'joint{endpoint}']
            if function < 0 or function not in names:
                raise ValueError('Geometry native function is not mapped in MOD3')
            shape[f'bone{endpoint}'] = dict(native_joint=function, **names[function])
        # Pipeline candidate D=diag(1,-1,1). Kept explicitly unqualified until
        # this monster's actual UE skeleton/bone-local basis is read back.
        convert = lambda v: [v[0],-v[1],v[2]]
        runtime_capsules.append(dict(shape=1, inner_index=shape['index'],
            bone0=shape['bone0']['ue_imported_name'], bone1=shape['bone1']['ue_imported_name'],
            offset0_ue_local=convert(values['offset0']), offset1_ue_local=convert(values['offset1']),
            radius_ue_units=values['radius']))
    qualification = dict(action_binding=False, timeline_flags_uid=False,
                         geometry_remap=True, native_clock=False, ue_local_basis=False,
                         native_rehit=False, native_damage=False)
    runtime = dict(native_action_id=83, time_unit='NativeFrames', units_per_second=0.0,
        window_start=0.0, window_end=23.0, timeline_uid=32, attack_index=7, geometry_index=14,
        coordinate_basis='EngineeringCandidate: D=(x,-y,z), unit1; monster UE readback pending',
        qualification=qualification, capsules=runtime_capsules)
    result = dict(schema=1, status='native_geometry_fields_and_joint_remap_qualified_contact_profile_incomplete',
        original_game_executed=False, original_sources_modified=False,
        sources=dict(manifest=identity(BASE/'extraction-manifest.json'),
                     col=identity(NATIVE/COL_REL), lmt=identity(NATIVE/LMT_REL),
                     mod3=identity(NATIVE/MOD_REL), field_layout=identity(pins_path)),
        native_proof=proof, native_skeleton=dict(bone_count=count,remap_offset=remap_offset),
        action_candidate=dict(native_action_id=83, encoded_motion=0x2001, bank_index=2, motion_index=1,
            boundary='Current action registration/bank-file chain is supplied by the independent THK evidence work package; not inferred from Japanese labels'),
        collision_reference=reference[0], source_motion=dict(index=1, frame_count=entry['source_frame_count']),
        collision_timeline=group,
        candidate_bit0_intervals=dict(values=intervals, endpoint='left-inclusive/right-exclusive',
            boundary='Generic native type5 mask and key equality are qualified; CollisionTimeline bit-to-node activation consumer is still required'),
        geometry_records=shapes, runtime_profile=runtime,
        validation=dict(source_fingerprints_passed=True,semantic_geometry_roundtrip_count=len(shapes),
                        native_instruction_anchor_count=len(proof['checked_anchors']),
                        current_reflected_field_count=len(proof['current_reflection'])),
        unknowns=[
            'THK Action83 current registration and bank2 actual file binding must be joined from independent evidence',
            'CollisionTimeline mFlag bit0 to NodeID[0] activation consumer; trigger/other flags',
            'Native wall-clock-to-source-frame rate and modifiers; zero units_per_second is intentional',
            'This monster actual UE bone-local basis and source-length conversion readback',
            'Native re-hit authorization, cooldown and shared link grouping',
            'Final monster-to-hunter damage formula, quest/rank/defense/status modifiers',
            'Rotating capsule continuous sweep is a conservative candidate, never exact native damage',
        ],
        boundary='Original radius/joint/offset values are decoded, not guessed. Engineering mode uses explicit source frames and an unqualified converter basis; strict mode must reject remaining dependencies. Contacts never authorize native damage or re-hit.')
    for rel, before in originals.items():
        if (NATIVE/rel).read_bytes() != before:
            raise ValueError('Original source changed during extraction')
    write_json(FULL_OUT, full)
    write_json(output, result)
    print(json.dumps(dict(output=str(output), geometry_records=len(shapes),
                         anchors=len(proof['checked_anchors']), native_bones=count,
                         strict_ready=all(qualification[k] for k in
                             ('action_binding','timeline_flags_uid','geometry_remap','native_clock','ue_local_basis')))))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.output)