"""Decode fixed-size player table using a local declarative C# schema.

Schema is read as text, never executed. Unmapped regions stay uninterpreted.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from extract_native_longsword_params import decrypt_resource, pinned_sources

FORMATS = {'Single':'f','Double':'d','UInt32':'I','Int32':'i','UInt64':'Q',
           'Int64':'q','UInt16':'H','Int16':'h','Byte':'B','SByte':'b','Boolean':'B'}
SCHEMA_SHA256 = '7decb332b4ede0ebb71e511bf08afca84d2ff3e619c3e02d2f4255a87304c97a'


def decode(source, schema, output):
    pinned_sources()
    if hashlib.sha256(schema.read_bytes()).hexdigest() != SCHEMA_SHA256:
        raise ValueError('Player schema fingerprint changed; review its layout first')
    src = schema.read_text(encoding='utf-8-sig')
    data = decrypt_resource(source)
    if data[:8] != b'PLP\x00\x1f\x00\x00\x00' or len(data) != 20688:
        raise ValueError('Unsupported player parameter version or size')
    classes = list(dict.fromkeys(re.findall(r'new MhwStructDataContainer<(\w+)>',
                         src[src.index('using var reader = new BinaryReader'):])))
    rows, pos = [], 0
    for cl in classes:
        text = src.split('public partial class '+cl+' :', 1)[1]
        count = int(re.search(r'FixedSizeCount = (\d+)', text)[1])
        if cl.startswith('Skipping_Ahead_') or cl == 'The_Rest':
            size = int(re.search(r'const ulong count = (\d+)UL;', text)[1]) if cl != 'The_Rest' else len(data)-pos
            if size < 0 or pos+size > len(data): raise ValueError('Invalid unknown region')
            rows.append(dict(section=cl,index=0,field='uninterpreted',offset=pos,size=size))
            pos += size
            continue
        body = re.search(r'public static '+re.escape(cl)+r' LoadData\(BinaryReader reader, ulong i[^)]*\) \{(.*?)return data;', text, re.S)[1]
        fields = re.findall(r'data\.(\w+)_raw = reader.Read(\w+)\(([^)]*)\);', body)
        if not fields: raise ValueError('Empty schema '+cl)
        for index in range(count):
            for field, typ, arg in fields:
                size = int(arg) if typ in ('Chars','Bytes') else struct.calcsize(FORMATS[typ])
                if pos+size > len(data): raise ValueError('Schema exceeds resource')
                value = data[pos:pos+size].hex() if typ in ('Chars','Bytes') else struct.unpack_from('<'+FORMATS[typ],data,pos)[0]
                rows.append(dict(section=cl,index=index,field=field,offset=pos,size=size,type=typ,value=value))
                pos += size
    if pos != len(data):
        raise ValueError('Player schema did not consume the complete resource')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = dict(schema=str(schema),schema_sha256=sha(schema),source=str(source),source_sha256=sha(source),
                  decoded_sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),consumed=pos,rows=rows,
                  boundary='Schema labels alone are not proof of native consumers. Unknown byte regions are preserved in decoded binary.')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    output.with_suffix('.bin').write_bytes(data)
    print(json.dumps(dict(bytes=len(data),consumed=pos,fields=len(rows),unknown_regions=sum(r['field']=='uninterpreted' for r in rows))))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--schema',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    decode(args.source,args.schema,args.output)
