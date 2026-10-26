"""Read original W03P using a pinned public layout, without launching the game.

The source archive remains untouched. Node's local OpenSSL legacy provider is
used solely for the game's published Blowfish resource format; no npm install,
process injection, savegame access or game-directory write occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'Saved/MHWIImport/NativeParameterResearch-20261024/MHW-Editor'
SOURCE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp/wp03/wp03_param.w03p'
OUTPUT = ROOT / 'Saved/MHWIImport/NativeParameterResearch-20261024'
PIN = ROOT / 'Tools/MHW/native-parameter-sources.json'
FORMATS = {'float': 'f', 'uint': 'I', 'int': 'i', 'ushort': 'H', 'ubyte': 'B'}
DECLARATION = re.compile(r'^(\w+)\s+(\w+)(?:\[(\d+)\])?(?:<.*>)?;$')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned_sources():
    manifest = json.loads(PIN.read_text(encoding='utf8'))
    for row in manifest['files']:
        if sha(CACHE / row['path']) != row['sha256']:
            raise ValueError('Upstream schema/decryption source changed: ' + row['path'])
    return manifest


def fetch_layout():
    """Explicit opt-in cache restore; pinned hashes, no execution or overwrite."""
    import urllib.request
    manifest = json.loads(PIN.read_text(encoding='utf8'))
    for row in manifest['files']:
        target = CACHE / row['path']
        if target.exists():
            if sha(target) != row['sha256']:
                raise ValueError('Preserving modified local schema: ' + str(target))
            continue
        with urllib.request.urlopen(row['url'], timeout=30) as response:
            data = response.read(4 * 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Downloaded schema hash mismatch: ' + row['path'])
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    return pinned_sources()


def decrypt_resource(source, key_name='PL_PARAM_KEY'):
    """Mirror the pinned BSwap -> Blowfish ECB -> BSwap read path exactly."""
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js with OpenSSL Blowfish support is required')
    code = r'''
const fs = require('fs'), crypto = require('crypto');
const [sourceFile, keyFile, keyName] = process.argv.slice(1);
const keySource = fs.readFileSync(keyFile, 'utf8');
const match = keySource.match(new RegExp(keyName + '\\s*=\\s*"([^"]+)"'));
if (!match) throw new Error('Published resource key missing');
const key = Buffer.from(match[1], 'utf8'), input = fs.readFileSync(sourceFile);
function swap4(bytes) {
  if (bytes.length % 4) throw new Error('Invalid word alignment');
  const output = Buffer.alloc(bytes.length);
  for (let i = 0; i < bytes.length; i += 4) output.writeUInt32BE(bytes.readUInt32LE(i), i);
  return output;
}
if (input.length % 8) throw new Error('Invalid Blowfish block alignment');
const decipher = crypto.createDecipheriv('bf-ecb', key, null); decipher.setAutoPadding(false);
const plain = swap4(Buffer.concat([decipher.update(swap4(input)), decipher.final()]));
const cipher = crypto.createCipheriv('bf-ecb', key, null); cipher.setAutoPadding(false);
const roundtrip = swap4(Buffer.concat([cipher.update(swap4(plain)), cipher.final()]));
process.stdout.write(JSON.stringify({plain_hex: plain.toString('hex'), roundtrip: input.equals(roundtrip)}));
'''
    result = subprocess.run([node, '--openssl-legacy-provider', '-e', code, str(source),
        str(CACHE / 'MHW-Template/EncryptionKeys.cs'), key_name], capture_output=True, check=True)
    decoded = json.loads(result.stdout)
    if not decoded['roundtrip']:
        raise ValueError('Published resource decryption/encryption roundtrip failed')
    return bytes.fromhex(decoded['plain_hex'])


def read_layout(path):
    """Interpret only this template's declarative, fixed-size field grammar.

    No template code is executed; unsupported constructs fail closed. Source
    line numbers and labels remain attached to every expanded scalar field.
    """
    types, roots, pending = {}, [], None
    section = ''
    for line_no, original in enumerate(path.read_text(encoding='utf8').splitlines(), 1):
        line = original.strip()
        if line.startswith('//'):
            section = line[2:].strip()
            continue
        if not line:
            continue
        if line == 'typedef struct {':
            if pending is not None:
                raise ValueError('Unexpected nested typedef')
            pending = []
            continue
        close = re.fullmatch(r'}\s+(\w+);', line)
        if close:
            if pending is None:
                raise ValueError('Unexpected struct end')
            types[close[1]] = pending
            pending = None
            continue
        match = DECLARATION.fullmatch(line)
        if not match:
            raise ValueError('Unsupported template line %d: %s' % (line_no, line))
        dtype, name, count = match.groups()
        if dtype not in FORMATS and dtype not in types and dtype != 'char':
            raise ValueError('Unknown field type ' + dtype)
        label = re.search(r'name="([^"]+)"', line)
        row = dict(type=dtype, name=name, count=int(count or 1), is_array=count is not None,
                   label=label[1] if label else name, template_line=line_no, section=section)
        (pending if pending is not None else roots).append(row)
    if pending is not None:
        raise ValueError('Unclosed template struct')
    return types, roots


def decode_layout(payload, types, roots):
    fields, cursor = [], 0

    def visit(declarations, prefix=''):
        nonlocal cursor
        for row in declarations:
            name = prefix + row['name']
            if row['type'] == 'char':
                raw = payload[cursor:cursor + row['count']]
                fields.append(dict(path=name, label=row['label'], offset=cursor, size=len(raw),
                    type='ascii', value=raw.decode('ascii'), section=row['section'],
                    template_line=row['template_line'], known_label=True))
                cursor += row['count']
                continue
            for index in range(row['count']):
                path = name + ('[%d]' % index if row['is_array'] else '')
                if row['type'] in types:
                    visit(types[row['type']], path + '.')
                    continue
                fmt = '<' + FORMATS[row['type']]
                size = struct.calcsize(fmt)
                if cursor + size > len(payload):
                    raise ValueError('Layout exceeds payload at ' + path)
                value = struct.unpack_from(fmt, payload, cursor)[0]
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError('Nonfinite value at ' + path)
                fields.append(dict(path=path, label=row['label'], offset=cursor,
                    offset_hex=hex(cursor), size=size, type=row['type'], value=value,
                    section=row['section'], template_line=row['template_line'],
                    known_label=not row['name'].lower().startswith('unk')))
                cursor += size
    visit(roots)
    padding = payload[cursor:]
    # The pinned layout consumes 1572 bytes of the local 1584-byte resource.
    # Preserve its 12 trailing zeros explicitly; their native meaning is not
    # part of the public template, so do not invent additional named fields.
    if len(padding) >= 16 or any(padding):
        raise ValueError('Unexpected trailing data: consumed%d of%d' % (cursor, len(payload)))
    return fields, cursor, len(padding)


def run(source=SOURCE, output=OUTPUT):
    upstream = pinned_sources()
    digest = sha(source)
    payload = decrypt_resource(source)
    if payload[:4].lower() != b'w03\0':
        raise ValueError('Unexpected decoded W03P signature: ' + repr(payload[:4]))
    template = CACHE / '010 Templates/w03p.bt'
    types, roots = read_layout(template)
    fields, consumed, padding = decode_layout(payload, types, roots)
    report = dict(schema=1, passed=True, source=str(source.relative_to(ROOT)), source_sha256=digest,
        decoded_sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload), consumed_bytes=consumed,
        unmapped_zero_tail_bytes=padding, encryption_roundtrip_passed=True, source_unchanged=sha(source) == digest,
        upstream=upstream, fields=fields,
        boundary='Labels come from the pinned original editor schema. Unknown fields remain unnamed. ActionParam blocks do not identify their gameplay action or unit conversion by themselves.')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'longsword-native-parameters.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (output / 'wp03_param.decrypted.bin').write_bytes(payload)
    print(json.dumps(dict(passed=True, fields=len(fields), known_labels=sum(r['known_label'] for r in fields),
                          consumed_bytes=consumed, unmapped_zero_tail_bytes=padding, source_unchanged=report['source_unchanged'])))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--fetch-layout', action='store_true', help='Restore missing pinned public schema files only')
    args = parser.parse_args()
    if args.fetch_layout:
        fetch_layout()
    run(args.source.resolve(), args.output.resolve())
