"""Rebuild fixed-version, offline PBC serialization evidence.

Uses only NativeTrace hash-qualified analysis bytes and owned pdata ranges.
No game launch, process attach, reflection call, or guessed leaf range occurs.
The result maps file payload positions to unnamed object offsets, not durability.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from trace_native_connections import NativeTrace

ROOT = Path(__file__).resolve().parents[2]
FUNCTIONS = {
    'resource_load': 0x1419d86e0,
    'parts_info_array_read': 0x1419d7c20,
    'parts_state_array_read': 0x1419d7de0,
    'parts_detail_array_read': 0x1419d7a20,
    'parts_info_array_write': 0x1419d7f80,
    'resource_save': 0x1419d8780,
}
# Exact instruction checks keep descriptions attached to this pinned build.
KEY_INSTRUCTIONS = {
    0x1419d8703: ('cmp', 'eax, 0x18091001'),
    0x1419d8714: ('cmp', 'eax, 9'),
    0x1419d8723: ('cmp', 'eax, 0x434250'),
    0x1419d8746: ('call', '0x1419d7c20'),
    0x1419d7d3d: ('call', '0x1419d7de0'),
    0x1419d7f1f: ('call', '0x1419d7a20'),
    0x1419d7b67: ('mov', 'dword ptr [rsi + 0x10], eax'),
    0x1419d7b73: ('mov', 'dword ptr [rsi + 0x20], eax'),
    0x1419d7bc1: ('mov', 'dword ptr [rsi + 0x28], eax'),
    0x1419d7f2d: ('mov', 'dword ptr [rsi + 0x10], eax'),
    0x1419d7d4b: ('mov', 'dword ptr [rsi + 0x28], eax'),
    0x1419d7d57: ('mov', 'dword ptr [rsi + 0x2c], eax'),
    0x1419d7d63: ('mov', 'dword ptr [rsi + 0x30], eax'),
    0x1419d8079: ('mov', 'edx, dword ptr [r14 + 0x10]'),
    0x1419d8086: ('mov', 'edx, dword ptr [r14 + 0x20]'),
    0x1419d808d: ('mov', 'edx, dword ptr [r14 + 0x28]'),
    0x1419d80ab: ('mov', 'edx, dword ptr [rsi + 0x10]'),
    0x1419d80d0: ('mov', 'edx, dword ptr [r15 + 0x28]'),
    0x1419d80dd: ('mov', 'edx, dword ptr [r15 + 0x2c]'),
    0x1419d80ea: ('mov', 'edx, dword ptr [r15 + 0x30]'),
    0x1419d879f: ('mov', 'edx, 0x18091001'),
    0x1419d87ae: ('mov', 'edx, 9'),
    0x1419d87bd: ('mov', 'edx, 0x434250'),
    0x1419d87e8: ('call', '0x1419d7f80'),
}
FIELD_MAP = [
    (20,'PartsDetailInfo',0x10,0x1419d7b67,0x1419d8079),
    (24,'PartsDetailInfo',0x20,0x1419d7b73,0x1419d8086),
    (28,'PartsDetailInfo',0x28,0x1419d7bc1,0x1419d808d),
    (32,'PartsStateInfo',0x10,0x1419d7f2d,0x1419d80ab),
    (36,'PartsInfo',0x28,0x1419d7d4b,0x1419d80d0),
    (40,'PartsInfo',0x2c,0x1419d7d57,0x1419d80dd),
    (44,'PartsInfo',0x30,0x1419d7d63,0x1419d80ea),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    native = NativeTrace()
    functions=[]
    instructions={}
    for name,va in FUNCTIONS.items():
        result=native.function(va)
        if result['status']!='chained_unwind_ranges_collected_not_runtime_verified':
            raise ValueError('No owned pdata ranges for '+name)
        if int(result['owner_va'],16)!=va:
            raise ValueError('Unexpected owner for '+name)
        ranges=[]
        for r in result['ranges']:
            begin,end=int(r['begin'],16),int(r['end'],16)
            decoded=[x for x in result['instructions'] if begin<=int(x['va'],16)<end]
            if r['decoded_bytes']!=r['expected_bytes'] or sum(x['size'] for x in decoded)!=end-begin:
                raise ValueError('Incomplete decode for '+name)
            ranges.append(dict(r,sha256=sha(native.code[begin-native.begin:end-native.begin])))
        for ins in result['instructions']:
            instructions[int(ins['va'],16)]=ins
        relevant=[x for x in result['instructions'] if int(x['va'],16) in KEY_INSTRUCTIONS]
        functions.append(dict(name=name,address=hex(va),status=result['status'],ranges=ranges,
                              instruction_count=len(result['instructions']),key_instructions=relevant))
    for va,(mnemonic,operands) in KEY_INSTRUCTIONS.items():
        actual=instructions.get(va)
        if actual is None or (actual['mnemonic'],actual['operands'])!=(mnemonic,operands):
            raise ValueError('Pinned instruction changed at '+hex(va))
    fields=[dict(sample_record_relative_offset=offset,
                 object_class='rEmPartsBreakCtrl::'+cls,object_memory_offset=hex(mem),
                 read_store_instruction=hex(read),write_load_instruction=hex(write),
                 semantic_name=None)
            for offset,cls,mem,read,write in FIELD_MAP]
    return dict(schema=1,passed=True,mode='fixed_version_offline_static_serialization_evidence',
        sources=dict(exe=native.pin['exe'],text=native.pin['text'],
                     native_pin_path='Tools/MHW/native-connector-code-sources.json',
                     native_pin_sha256=sha((ROOT/'Tools/MHW/native-connector-code-sources.json').read_bytes()),
                     trace_script_sha256=sha((ROOT/'Scripts/MHWI/trace_native_connections.py').read_bytes()),
                     inspector_script_sha256=sha(Path(__file__).read_bytes())),
        class_identity_source=dict(url='https://github.com/Andoryuuta/MHW-DTI-Dumps/blob/4a124e4073519eaf19e3a446cb62d375d8da3209/dti_prop_dump.h',
            use='Class names and CRCs only. Historical dump vtable addresses are not used as current-build addresses.'),
        functions=functions,key_instruction_checks=len(KEY_INSTRUCTIONS),
        nesting=dict(resource_array_offset='0xa8',root_count_read='0x1419d7c8e',
                     info_state_array_offset='0x8',state_count_read='0x1419d7e4e',
                     state_detail_array_offset='0x18',detail_count_read='0x1419d7a8e',
                     sample_state_count_relative_offset=4,sample_detail_count_relative_offset=12,
                     sample_counts=[1,1],
                     limitation='48 bytes is the flattened size of the four qualified samples with both nested counts equal to one, not a generic fixed record stride.'),
        field_memory_mapping=fields,
        unresolved=['Business semantics of all seven payload integers remain unknown.',
                    '2006/2007 at sample +24 maps to PartsDetailInfo+0x20; no durability/ID semantics are inferred.',
                    'The loaded object field consumers, original-game part damage and break conditions are not observed.'],
        game_launched=False,game_code_executed=False,game_or_asset_modified=False,
        qualification='NativeTrace validated the pinned EXE and qualified analysis-text SHA256; all six functions are fully decoded within owned pdata/CHAININFO ranges. This is shell/Capstone evidence, not a REA decompilation result or runtime observation.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'Tools/MHW/em001-pbc-native-layout-evidence.json')
    args=parser.parse_args()
    result=build()
    target=args.out.resolve()
    protected={Path(__file__).resolve(), Path(result['sources']['exe']['path']).resolve(),
               (ROOT/result['sources']['text']['path']).resolve(),
               (ROOT/result['sources']['native_pin_path']).resolve()}
    if target.suffix.lower()!='.json' or not target.is_relative_to(ROOT) or target in protected:
        raise ValueError('Output must be a workspace JSON separate from all source inputs')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=result['passed'],functions=len(result['functions']),
                         key_instruction_checks=result['key_instruction_checks'],fields=len(result['field_memory_mapping']),
                         output=str(args.out))))


if __name__=='__main__':
    main()
