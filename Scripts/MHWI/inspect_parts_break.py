"""Inspect four pinned PBC samples; identify class CRCs without guessing field semantics.

This is a bounded 16+N*48 sample inspector, not a general PBC deserializer.
The seven payload dwords stay unnamed. No game code or DTI addresses execute.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / 'Tools/MHW/rathalos-pbc-sources.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect(data, classes):
    if len(data) < 16:
        raise ValueError('Truncated PBC header')
    marker, version, magic, count = struct.unpack_from('<II4sI', data)
    if (marker, version, magic) != (0x18091001, 9, b'PBC\0'):
        raise ValueError('Unexpected sample header/version')
    if count != 5 or len(data) != 16 + count * 48:
        raise ValueError('Outside qualified four-sample shape; no fallback slicing')
    rows = []
    for index in range(count):
        offset = 16 + index * 48
        words = struct.unpack_from('<12I', data, offset)
        for field, name in ((0, 'PartsInfo'), (2, 'PartsStateInfo'), (4, 'PartsDetailInfo')):
            if words[field] != classes['rEmPartsBreakCtrl::' + name]:
                raise ValueError('Unexpected class CRC at ' + hex(offset + field * 4))
        if words[1] != 1 or words[3] != 1:
            raise ValueError('Outside qualified nested-count pattern')
        payload = struct.unpack_from('<7i', data, offset + 20)
        rows.append(dict(index=index, offset=offset, class_ids=[hex(words[x]) for x in (0,2,4)],
                         raw_plus4=words[1], raw_plus12=words[3],
                         payload=[dict(relative_offset=20+i*4, signed=value,
                                       unsigned=words[5+i], semantics=None)
                                  for i,value in enumerate(payload)]))
    return dict(size=len(data), consumed=16+48*count, shape_scope='four pinned samples only',
                header=dict(marker=hex(marker), version=version, count=count), records=rows)


def self_check(data, classes):
    mutations = {'truncated': data[:-1], 'trailing': data+b'\0'}
    for name,offset,value in [('count',12,6),('class_crc',16,0),('nested_count',20,2),('version',4,10)]:
        b=bytearray(data)
        struct.pack_into('<I',b,offset,value)
        mutations[name]=bytes(b)
    for name,invalid in mutations.items():
        try:
            inspect(invalid, classes)
        except ValueError:
            continue
        raise AssertionError('Accepted invalid sample: '+name)
    return dict(passed=True, rejected=list(mutations))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'Tools/MHW/em001-pbc-evidence.json')
    parser.add_argument('--self-check',action='store_true')
    args=parser.parse_args()
    pin=json.loads(PIN.read_text(encoding='utf-8'))
    target=args.out.resolve()
    protected={PIN.resolve(),Path(__file__).resolve(),(ROOT/pin['dti']['path']).resolve()}
    protected.update((ROOT/row[key]).resolve() for row in pin['files'] for key in ('path','manifest'))
    if target.suffix.lower()!='.json' or not target.is_relative_to(ROOT) or target in protected:
        raise ValueError('Output must be a workspace JSON separate from all source inputs')
    dti=(ROOT/pin['dti']['path']).read_bytes()
    if digest(dti)!=pin['dti']['sha256']:
        raise ValueError('Historical DTI source changed')
    text=dti.decode('utf-8-sig')
    classes={}
    for name,crc in pin['classes'].items():
        actual=(~zlib.crc32(name.encode('ascii'))) & 0x7fffffff
        if actual!=int(crc,16):
            raise ValueError('Class-name CRC mismatch')
        pattern=r'// '+re.escape(name)+r' vftable:[^\n]*CRC32:0x([0-9A-Fa-f]+)'
        matches=re.findall(pattern,text)
        if len(matches)!=1 or int(matches[0],16)!=actual:
            raise ValueError('DTI does not uniquely confirm class '+name)
        classes[name]=actual
    files=[]
    checks=[]
    for source in pin['files']:
        path=ROOT/source['path']
        data=path.read_bytes()
        if len(data)!=source['bytes'] or digest(data)!=source['sha256']:
            raise ValueError('Pinned PBC sample changed: '+str(path))
        manifest=json.loads((ROOT/source['manifest']).read_text(encoding='utf-8'))
        matches=[row for row in manifest['files'] if row['path']==source['archive_path']]
        if len(matches)!=1 or matches[0]['sha256']!=source['sha256'] or matches[0]['size']!=len(data):
            raise ValueError('Extraction manifest identity mismatch')
        files.append(dict(source=source, inspection=inspect(data,classes)))
        if args.self_check:
            checks.append(self_check(data,classes))
    result=dict(schema=1,passed=True,scope=pin['scope'],sources=pin,files=files,
                class_identity_resolved=True,durability_semantics_resolved=False,
                local_inspector_sha256=digest(Path(__file__).read_bytes()),
                corrections=['The three constants are class CRC32 values, not unidentified Murmur hashes.',
                             'Record 0 payload +24 is -1; only records 1..4 contain 2006/2007.'],
                self_checks=checks,game_or_ue_executed=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,files=len(files),records=sum(len(x['inspection']['records']) for x in files),
                         class_matches=len(classes),self_checks=len(checks),output=str(args.out))))


if __name__=='__main__':
    main()
