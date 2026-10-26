"""Read-only trace of the pinned MHWI collision-node loader path.

This inspects a qualified on-disk .text copy and PE data; it never launches the
game or executes native code. Output is local under Saved/.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from trace_outstanding_evidence import Evidence

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'Saved/MHWIRestoration/B19-20261026/weapon-collision-loader-chain.json'


def rip_target(ins: dict) -> int:
    raw = bytes.fromhex(ins['bytes'])
    return int(ins['va'], 16) + ins['size'] + struct.unpack('<i', raw[-4:])[0]


def text_at(e: Evidence, address: int) -> str:
    offset = e.tr.image.offset(address)
    end = e.tr.image.blob.index(b'\0', offset)
    return e.tr.image.blob[offset:end].decode('ascii', errors='replace')


def find_target(e: Evidence, function: dict, reg: str) -> int:
    for ins in function['instructions']:
        if ins['mnemonic'] == 'lea' and ins['operands'].startswith(reg + ', [rip'):
            return rip_target(ins)
    raise ValueError(f'No RIP-relative LEA into {reg} in {function.get("entry")}')


def direct_calls(function: dict) -> set[int]:
    return {
        int(ins['operands'], 16)
        for ins in function['instructions']
        if ins['mnemonic'] == 'call' and ins['operands'].startswith('0x')
    }


def main() -> None:
    e = Evidence()
    image = e.tr.image

    # CLND.type == 1 indexes this fixed-version function table.
    table = 0x143F94A18
    factory_object = e.u(table + 8)
    section = next(
        s for s in image.sections
        if image.base + s.VirtualAddress <= factory_object < image.base + s.VirtualAddress + s.Misc_VirtualSize
    )
    section_start = image.base + section.VirtualAddress
    raw_end = section_start + section.SizeOfRawData
    storage_is_zero_fill = factory_object >= raw_end

    initializer_va = 0x140009890
    initializer = e.function(initializer_va)
    initializer_object = find_target(e, initializer, 'rcx')
    node_class_name_va = find_target(e, initializer, 'rdx')
    vtable_va = find_target(e, initializer, 'rax')
    if initializer_object != factory_object:
        raise ValueError('Type-1 factory object does not match its initializer')
    if text_at(e, node_class_name_va) != 'cCollNodePl':
        raise ValueError('Unexpected type-1 factory class name')
    if 0x14216ED60 not in direct_calls(initializer):
        raise ValueError('Expected factory-object initializer call is absent')

    factory_function = e.u(vtable_va + 8)
    node_creator = e.function(factory_function)
    if 0x1419C2680 not in direct_calls(node_creator):
        raise ValueError('Type-1 node creator no longer calls the expected constructor')
    instance_vtable_va = find_target(e, node_creator, 'rax')
    node_reader_wrapper_va = e.u(instance_vtable_va + 0x28)
    if node_reader_wrapper_va != 0x140294530:
        raise ValueError('Type-1 node reader vtable slot changed')
    node_reader_wrapper = e.function(node_reader_wrapper_va)
    node_reader_va = next(iter(direct_calls(node_reader_wrapper)))

    clnd_reader_va = 0x1419C30B0
    clnd_reader = e.function(clnd_reader_va)
    if 0x14191A5C0 not in direct_calls(clnd_reader):
        raise ValueError('CLND reader no longer calls the indexed factory')
    if 0x1419C2FE0 not in direct_calls(node_reader_wrapper):
        raise ValueError('Type-1 node reader path changed')

    writer = e.function(0x1419C13D0)
    record_writer = e.function(0x1419C14A0)
    geometry_type_name = text_at(e, 0x14352D428)

    result = {
        'status': 'read_only_static_trace',
        'source': e.tr.pin,
        'native_code_executed': False,
        'clnd_type_1': {
            'factory_table': hex(table),
            'factory_object': hex(factory_object),
            'storage_section': section.Name.rstrip(b'\0').decode('ascii'),
            'storage_is_pe_zero_fill': storage_is_zero_fill,
            'static_initializer': hex(initializer_va),
            'class_name': text_at(e, node_class_name_va),
            'class_size_bytes': 0x58,
            'vtable': hex(vtable_va),
            'vtable_slot_plus_8_creator': hex(factory_function),
            'instance_constructor': '0x1419c2680',
            'instance_vtable': hex(instance_vtable_va),
            'instance_reader_slot_plus_0x28': hex(node_reader_wrapper_va),
            'instance_reader_wrapper': hex(node_reader_wrapper_va),
            'instance_reader': hex(node_reader_va),
            'clnd_reader': hex(clnd_reader_va),
        },
        'clgm_static_evidence': {
            'writer': '0x1419c13d0',
            'record_writer': '0x1419c14a0',
            'record_size_bytes': 72,
            'record_field_semantics_decoded': False,
        },
        'geometry_candidate': {
            'type_name': geometry_type_name,
            'constructor': '0x142466d70',
            'mapped_from_wp03_clgm': False,
            'bone_binding_or_transform_proven': False,
        },
        'decision': {
            'original_geometry_reusable_as_project_implementation': False,
            'reason': 'The trace resolves CLND type 1 to a collision-node factory, but does not map the 13 wp03.col CLGM groups or their 72-byte fields to a concrete geometry object or bone-space transform.',
            'project_owned_collision_path_needed_for_current_implementation': True,
        },
        'scope': 'Pinned offline static evidence only; no game process, debugger, plugin, or runtime observation was used.',
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'output': str(OUTPUT), 'class_name': result['clnd_type_1']['class_name'],
                      'reader': result['clnd_type_1']['instance_reader'],
                      'geometry_mapping_proven': False, 'runtime_observation': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
