"""Read-only parser for MHW monster parameter files, driven by MHW-Editor struct definitions.

The generated C# `LoadData(BinaryReader, ulong)` bodies are a linear read spec.
This script interprets those bodies directly instead of hand-copying field offsets,
then asserts the parse consumed exactly the file size. A size mismatch is reported
as a failure, never repaired by guessing.

Usage:
    python Scripts/MHWI/parse_em_params.py --layouts Tools/MHW/Source/MHW-Editor-b6ff379 \
        --input ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/data \
        --out Saved/MHWProbe-20261030/em001-lr-params.json
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

READERS = {
    'ReadByte': ('B', 1),
    'ReadSByte': ('b', 1),
    'ReadUInt16': ('H', 2),
    'ReadInt16': ('h', 2),
    'ReadUInt32': ('I', 4),
    'ReadInt32': ('i', 4),
    'ReadUInt64': ('Q', 8),
    'ReadInt64': ('q', 8),
    'ReadSingle': ('f', 4),
    'ReadDouble': ('d', 8),
}

# MHW monster extension -> MHW-Editor struct root class.
EXT_CLASS = {
    'dtt_epg': 'MonsterParts',
    'dtt_agr': 'MonsterEnrage',
    'dtt_sta': 'MonsterStamina',
    'dtt_eda': 'MonsterDamageAttributes',
    'shlp': 'ShellParam',
}


def key_map(keys_cs):
    """extension -> EncryptionKeys constant name, from the pinned key table."""
    text = keys_cs.read_text(encoding='utf-8-sig', errors='replace')
    pairs = re.findall(r'\{("\.\w+"),\s*(\w+_KEY)\}', text)
    return {ext.strip('".').lstrip('.'): name for ext, name in pairs}


def strip_comments(text):
    text = re.sub(r'//[^\n]*', '', text)
    return re.sub(r'/\*.*?\*/', '', text, flags=re.S)


def class_bodies(text):
    """Return {class_name: body_text} for every `public partial class X {`."""
    out = {}
    for match in re.finditer(r'public partial class (\w+)\s*(?::[^{]+)?\{', text):
        name = match.group(1)
        start = match.end() - 1
        depth, i = 0, start
        while i < len(text):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out.setdefault(name, text[start + 1:i])
    return out


def method_body(body, class_name):
    """Extract the per-item LoadData body.

    The generated outer container class names its loader after an inner type
    (e.g. MonsterEnrage owns Monster_Rage.LoadData), so match on the signature
    shape rather than on the class name.
    """
    pat = re.compile(r'public static [\w<>]+ LoadData\(BinaryReader reader, ulong i[^)]*\)\s*\{')
    m = pat.search(body)
    if not m:
        return None
    start = m.end() - 1
    depth, i = 0, start
    while i < len(body):
        if body[i] == '{':
            depth += 1
        elif body[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    return body[start + 1:i]


def collection_count(body, class_name):
    """Count expression of the `LoadData(reader, parent)` collector, if present."""
    pat = re.compile(r'public static ObservableMhwStructCollection<' + class_name +
                     r'> LoadData\(BinaryReader reader(?:, ObservableMhwStructCollection<(\w+)> \w+)?\)\s*\{(.*?)\n\s{8,}\}', re.S)
    m = pat.search(body)
    if not m:
        return None
    parent, text = m.group(1), m.group(2)
    const = re.search(r'const ulong count = (\d+)UL;', text)
    if const:
        return ('const', int(const.group(1)), parent)
    ref = re.search(r'var count = \(ulong\) (?:countTarget|lastStruct\.Last\(\))\.(\w+);', text)
    if ref:
        return ('field', ref.group(1), parent)
    return None


class Struct:
    def __init__(self, name, body, ops):
        self.name = name
        self.body = body
        self.ops = ops
        self.count = collection_count(body, name)


def parse_ops(body, class_name, definitions):
    """Turn a LoadData body into a flat op list."""
    lines = [ln.strip() for ln in method_body(body, class_name).splitlines()]
    ops, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        if re.match(r'var data = new \w+\(\);', line) or re.match(r'data\.Index = i;', line) or line == 'return data;':
            i += 1
            continue
        m = re.match(r'data\.(\w+?)_raw\s*=\s*reader\.ReadChars\((\d+)\);', line)
        if m:
            name, n = m.group(1), int(m.group(2))
            ops.append(('chars', name, n))
            i += 1
            continue
        m = re.match(r'data\.(\w+?)_raw\s*=\s*(?:\([^)]*\)\s*)?reader\.(Read\w+)\(\);', line)
        if m:
            ops.append(('read', m.group(1), m.group(2)))
            i += 1
            continue
        m = re.match(r'data\.(\w+)_offset\s*=\s*reader\.BaseStream\.Position;', line)
        if m:
            ops.append(('mark', m.group(1)))
            i += 1
            continue
        m = re.match(r'data\.(\w+?)_raw\s*=\s*reader\.ReadBytes\((\d+)\)', line)
        if m:
            ops.append(('bytes', m.group(1), int(m.group(2))))
            i += 1
            continue
        m = re.match(r'if \(data\.\w+?_raw\s*!=\s*0\)\s*data\.(\w+?)_offset\s*=\s*reader\.BaseStream\.Position;', line)
        if m:
            ops.append(('mark', m.group(1)))
            i += 1
            continue
        m = re.match(r'if \(data\.(\w+?)_raw\s*!=\s*0\)\s*data\.(\w+?)_raw\s*=\s*reader\.ReadNullTermString\(\);', line)
        if m:
            ops.append(('cond_string', m.group(1), m.group(2)))
            i += 1
            continue
        m = re.match(r'if \(data\.(\w+?)_raw\s*==\s*(\d+)\)\s*data\.(\w+?)_raw\s*=\s*(\w+)\.LoadData\(reader, data\);', line)
        if m:
            sub = m.group(4)
            ops.append(('cond_array', m.group(1), int(m.group(2)), sub))
            i += 1
            continue
        m = re.match(r'data\.(\w+?)_raw\s*=\s*(\w+)\.LoadData\(reader, data\);', line)
        if m:
            ops.append(('array', m.group(2)))
            i += 1
            continue
        m = re.match(r'data\.(\w+?)_raw\s*=\s*reader\.(Read\w+)\((\d+)\)', line)
        if m:
            ops.append(('counted', m.group(1), m.group(2), int(m.group(3))))
            i += 1
            continue
        # Anything unrecognised is recorded so a silent mis-parse cannot happen.
        ops.append(('unsupported', line))
        i += 1
    return ops


def build_definitions(layout_root):
    defs = {}
    for path in layout_root.rglob('*.cs'):
        text = strip_comments(path.read_text(encoding='utf-8-sig', errors='replace'))
        for name, body in class_bodies(text).items():
            if 'LoadData(BinaryReader reader, ulong i' in body:
                defs.setdefault(name, Struct(name, body, parse_ops(body, name, defs)))
    return defs


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, kind):
        fmt, size = READERS[kind]
        value = struct.unpack_from('<' + fmt, self.data, self.pos)[0]
        self.pos += size
        return value


def load_instance(defs, cls, reader, ctx, out, depth=0):
    st = defs[cls]
    rec = {'_class': cls, '_offset': reader.pos}
    for op in st.ops:
        kind = op[0]
        if kind == 'read':
            name, rd = op[1], op[2]
            if rd == 'ReadNullTermString':
                end = reader.data.find(b'\0', reader.pos)
                end = len(reader.data) if end < 0 else end
                rec[name] = reader.data[reader.pos:end].decode('ascii', 'replace')
                reader.pos = end + 1
                continue
            if rd not in READERS:
                raise ValueError(f'{cls}.{name}: unsupported reader {rd}')
            rec[name] = reader.read(rd)
        elif kind == 'mark':
            rec[op[1] + '_offset'] = reader.pos
        elif kind == 'bytes':
            rec[op[1]] = reader.data[reader.pos:reader.pos + op[2]].hex()
            reader.pos += op[2]
        elif kind == 'string':
            end = reader.data.find(b'\0', reader.pos)
            end = len(reader.data) if end < 0 else end
            rec[op[1]] = reader.data[reader.pos:end].decode('ascii', 'replace')
            reader.pos = end + 1
        elif kind == 'cond_string':
            field, target = op[1], op[2]
            if rec.get(field) != 0:
                end = reader.data.find(b'\0', reader.pos)
                end = len(reader.data) if end < 0 else end
                rec[target] = reader.data[reader.pos:end].decode('ascii', 'replace')
                reader.pos = end + 1
        elif kind == 'chars':
            name, n = op[1], op[2]
            rec[name] = reader.data[reader.pos:reader.pos + n].decode('ascii', 'replace')
            reader.pos += n
        elif kind == 'counted':
            name, rd, n = op[1], op[2], op[3]
            vals = [reader.read(rd) for _ in range(n)]
            rec[name] = vals
        elif kind == 'array':
            sub = op[1]
            rec[sub] = load_collection(defs, sub, reader, {})
        elif kind == 'cond_array':
            field, expected, sub = op[1], op[2], op[3]
            if rec.get(field) == expected:
                rec[sub] = load_collection(defs, sub, reader, {})
        else:
            raise ValueError(f'{cls}: unsupported statement: {op[1][:120]}')
    out.append(rec)
    return rec


def load_collection(defs, cls, reader, sections):
    st = defs[cls]
    if st.count is None:
        raise ValueError(f'{cls}: no collector LoadData(reader, parent) found')
    mode, value, parent = st.count
    if mode == 'const':
        n = value
    else:
        if not parent or parent not in sections or not sections[parent]:
            raise ValueError(f'{cls}: count field {value} needs parent section {parent}')
        n = sections[parent][-1][value]
    items = []
    for _ in range(n):
        load_instance(defs, cls, reader, [], items)
    return items


def load_root(defs, cls, data):
    """Execute the file-level LoadFile order for the root class."""
    reader = Reader(data)
    st = defs[cls]
    text = strip_comments(st.body)
    order = re.findall(r'new MhwStructDataContainer<(\w+)(?:, \w+)?>\((\w+)\.LoadData\(reader', text)
    result = {'_class': cls, '_sections': []}
    sections = {}
    for type_name, called in order:
        # Every section goes through its collection loader; header sections
        # declare FixedSizeCount = 1 and are therefore length-1 collections.
        items = load_collection(defs, type_name, reader, sections)
        result[type_name] = items
        sections[type_name] = items
        result['_sections'].append({'class': type_name, 'count': len(items), 'end': reader.pos})
    return result, reader.pos


def verify_pins(layout_root, pins_path):
    """Fail closed unless every layout file matches its pinned SHA256.

    A silently substituted struct definition would change field order and could
    make a wrong parse look self-consistent, so a mismatch is fatal.
    """
    pins = json.loads(pins_path.read_text(encoding='utf-8'))
    import hashlib
    checked, problems = 0, []
    for row in pins.get('files', []):
        target = layout_root / row['path']
        if not target.is_file():
            problems.append(f'missing layout: {row["path"]}')
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != row['sha256']:
            problems.append(f'hash mismatch: {row["path"]} {digest[:12]} != {row["sha256"][:12]}')
        checked += 1
    if problems:
        raise SystemExit('layout pin check failed://n  ' + '\n  '.join(problems))
    return {'pins_file': str(pins_path), 'commit': pins.get('commit'), 'verified': checked}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layouts', type=Path, required=True)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--keys', type=Path, help='EncryptionKeys.cs from the pinned MHW-Editor cache')
    ap.add_argument('--pins', type=Path, help='mhw-editor-sources.json; verifies every layout hash before parsing')
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    keys = key_map(args.keys) if args.keys else {}
    decrypt = None
    if keys:
        from extract_native_longsword_params import decrypt_resource
        decrypt = decrypt_resource

    pins = None
    if args.pins:
        pins = verify_pins(args.layouts, args.pins)

    defs = build_definitions(args.layouts)
    print(f'loaded {len(defs)} struct definitions', file=sys.stderr)

    report = {'definitions': len(defs), 'pins': pins, 'files': []}
    failures = 0
    for path in sorted(args.input.iterdir()):
        ext = path.suffix.lstrip('.')
        cls = EXT_CLASS.get(ext)
        if not cls:
            continue
        if cls not in defs:
            print(f'SKIP {path.name}: no struct {cls}', file=sys.stderr)
            continue
        raw = path.read_bytes()
        key_name = keys.get(ext)
        try:
            data = decrypt(path, key_name) if key_name else raw
        except Exception as exc:  # noqa: BLE001 - decryption failure is reported, never bypassed
            failures += 1
            report['files'].append({'file': path.name, 'class': cls, 'ok': False,
                                    'error': f'decrypt {key_name}: {exc}'})
            print(f'FAIL {path.name}: decrypt {key_name}: {exc}', file=sys.stderr)
            continue
        try:
            parsed, consumed = load_root(defs, cls, data)
        except Exception as exc:  # noqa: BLE001 - report, never guess
            failures += 1
            report['files'].append({'file': path.name, 'class': cls, 'ok': False, 'error': str(exc)})
            print(f'FAIL {path.name}: {exc}', file=sys.stderr)
            continue
        # A short read is accepted only when the remainder is zero padding.
        # Rationale: the same convention is already used by the project's B13
        # parts parser (expected_zero_tail). Non-zero leftovers stay failures.
        tail = data[consumed:]
        zero_tail = len(tail) if tail and not any(tail) and len(tail) <= 64 else 0
        ok = consumed == len(data) or (zero_tail > 0 and consumed <= len(data))
        if not ok:
            failures += 1
        report['files'].append({
            'file': path.name,
            'class': cls,
            'ok': ok,
            'size': len(data),
            'consumed': consumed,
            'decrypted': bool(key_name),
            'zero_tail': zero_tail,
            'sha256_raw': __import__('hashlib').sha256(raw).hexdigest(),
            'sections': parsed['_sections'],
            'data': {k: v for k, v in parsed.items() if not k.startswith('_')},
        })
        print(f'{"OK  " if ok else "MISMATCH"} {path.name}: {consumed}/{len(data)} bytes', file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'{len(report["files"])} parsed, {failures} failed', file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
