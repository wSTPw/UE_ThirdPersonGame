"""Rebuild/verify B13 byte evidence from the pinned offline native sources.

This verifies provenance and selected instructions, not gameplay interpretations.
No native bytes are executed. --write updates only the reviewable JSON manifest.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from extract_native_longsword_params import decrypt_resource
from trace_outstanding_evidence import Evidence, ROOT, OUT

MANIFEST = ROOT / 'Tools/MHW/native-outstanding-evidence.json'
# Requested functions plus selected ranges; complete reachable-CFG hashes and
# unresolved branches accompany the excerpts. Direct calls are not traversed.
WINDOWS = [
    ('parameter_loader', 0x141379680, [(0x141379680, 0x14137a200)]),
    ('gauge_change', 0x142122410, [(0x142122410, 0x142122530)]),
    ('roundslash_commit', 0x142122570, [(0x142122570, 0x1421225e0)]),
    ('roundslash_contact', 0x142123510, [(0x142123650, 0x142123760)]),
    ('weapon_tick', 0x1421237b0, [(0x142123870, 0x142123a90)]),
    ('shell_contact', 0x142124b20, [(0x142124b20, 0x142124e30)]),
    ('helm_schedule', 0x1421225e0, [(0x1421225e0, 0x142122880)]),
    ('helm_emit', 0x142125150, [(0x142125150, 0x142125330)]),
    ('iai_emit', 0x142125860, [(0x142125860, 0x142125a50)]),
    ('dodge_entry', 0x141784e90, [(0x141784e90, 0x141784f20)]),
    ('dodge_common', 0x141783470, [(0x141783470, 0x141783720)]),
    ('dodge_protection_table', 0x141f752d0, [(0x141f752d0, 0x141f75518)]),
    ('protection_countdown', 0x141f6bd80, [(0x141f6c2e0, 0x141f6c340)]),
    ('protection_flags', 0x141f6f560, [(0x141f70020, 0x141f70150)]),
    ('player_resource_loader', 0x141a0e640, [(0x141a0e640, 0x141a0e790)]),
    ('player_table_loader', 0x141240740, [(0x1412413b0, 0x141241430)]),
    ('dodge_row_loader', 0x1405f4290, [(0x1405f4290, 0x1405f4310)]),
    ('actor_clocks', 0x142228f50, [(0x142228f50, 0x142229020)]),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build():
    e = Evidence()  # rejects EXE / analysis-text hash changes
    functions = []
    for label, va, windows in WINDOWS:
        fn = e.function(va)
        rows = fn['instructions']
        excerpt = [r for r in rows if any(a <= int(r['va'], 16) < b for a, b in windows)]
        if not excerpt:
            raise ValueError('No reachable instructions for '+label)
        canonical = json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()
        functions.append(dict(label=label, entry=fn['entry'], spans=fn['spans'],
                              cfg_sha256=digest(canonical), instructions=excerpt,
                              gaps=fn['gaps'], switches=fn['switches']))
    actions = e.actions()
    selected = [r for r in actions if r['action'] in (18,19,20,21,22,69,91,92,98,99,102)]
    if len(actions) != 113 or any('slots' not in r for r in actions):
        raise ValueError('Action registration coverage changed')
    action_rows = [dict(action=r['action'], name=r['name'], vtable=r['vtable'],
                        constructor=r['constructor']['entry'], slots=r['slots'][6:9],
                        callbacks={k:r[k] for k in ('entry','update','exit')}) for r in selected]
    extraction = json.loads((OUT/'resources/extraction-manifest.json').read_text(encoding='utf-8'))
    for row in extraction['files']:
        file = OUT/'resources/nativePC'/row['path']
        if file.stat().st_size != row['size'] or digest(file.read_bytes()) != row['sha256']:
            raise ValueError('Extracted resource changed: '+str(file))
    w03 = ROOT/'ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp/wp03/wp03_param.w03p'
    plp = OUT/'resources/nativePC/common/pl/pl_param.plp'
    values = []
    for name, path, specs in [
        ('W03P', w03, [(0x499,'f'),(0x49d,'f'),(0x4f1,'f'),(0x4f5,'f'),(0x4f9,'f'),
                       (0x51d,'f'),(0x540,'f'),(0x548,'f'),(0x54c,'f'),(0x5f8,'f'),
                       (0x5fc,'f'),(0x600,'f'),(0x604,'I'),(0x608,'I'),(0x60c,'f')]),
        ('PLP', plp, [(0x1e4,'f'),(0x1e8,'f')]+[(0x485+4*i,'f') for i in range(7)])]:
        raw = path.read_bytes()
        decoded = decrypt_resource(path)
        values.append(dict(name=name, path=path.relative_to(ROOT).as_posix(),
                           source_sha256=digest(raw), decoded_sha256=digest(decoded),
                           fields=[dict(offset=hex(off), format=fmt,
                                        bytes=decoded[off:off+struct.calcsize(fmt)].hex(),
                                        value=struct.unpack_from('<'+fmt,decoded,off)[0]) for off,fmt in specs]))
    motion = ROOT/'ArtSource/ThirdParty/MHWLongSword/nativePC/hm/wp/wp03/mot/w03_00/w03_00.lmt'
    data = motion.read_bytes()
    # Header first fields: curve pointer, curve count, frame count, loop frame.
    pointer, curves, frames, loop = struct.unpack_from('<QIIi', data, 0x3290)
    return dict(schema=1, batch='B13-20261026', scope='offline_static_evidence_only',
                boundary='Bytes/CFG verified, not runtime or complete consumer coverage. Unresolved indirect jumps remain gaps.',
                exe=e.tr.pin['exe'], analysis_text=e.tr.pin['text'],
                action_count=len(actions), actions=action_rows, functions=functions,
                parameters=values, extracted_resources=extraction['files'],
                motion306=dict(path=motion.relative_to(ROOT).as_posix(), sha256=digest(data),
                               header_offset='0x3290', curve_pointer=hex(pointer),
                               curve_count=curves, frame_count=frames, loop_frame=loop))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    current=build()
    if args.write:
        MANIFEST.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    elif json.loads(MANIFEST.read_text(encoding='utf-8')) != current:
        raise ValueError('B13 evidence differs; inspect source changes before regenerating')
    print(json.dumps(dict(mode='write' if args.write else 'verify', passed=True,
                          functions=len(current['functions']), actions=current['action_count'],
                          resources=len(current['extracted_resources']),
                          manifest=MANIFEST.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
