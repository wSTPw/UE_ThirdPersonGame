"""Persist constructor/clock/TIML source evidence; extraction only, no tests."""
import dataclasses
import json
from pathlib import Path
import struct

from trace_native_connections import NativeTrace
from native_connector_source import sources, parse_mbd
from native_animation_source import native_modules, SOURCES, shared_curve_owner

ROOT = Path(__file__).resolve().parents[2]


def run():
    tr = NativeTrace()
    out = ROOT/'Saved/MHWIRestoration/B08-20261025'
    out.mkdir(parents=True, exist_ok=True)
    functions = {name: tr.function(address) for name, address in dict(
        insertion_stab_entry=0x1417fe9e0, insertion_upper_entry=0x1417feae0,
        upper_entry=0x1417fee10, upper_update=0x141800200,
        spirit_one_entry=0x1417fe610, spirit_one_update=0x1417ffe50,
        step_slash_entry=0x1417fed20,
        phase_key_selection=0x1424a7440, phase_interpolation=0x1424a8580,
        phase_copy=0x1424a8770, motion_request_settings=0x141c007f0,
        animation_tree_constructor=0x142251b40, animation_tree_request=0x142255820,
        animation_layer_clock=0x14224d530,
        motion_setup=0x14224c200).items()}
    (out/'runtime-native-functions.json').write_text(json.dumps(functions, indent=2)+'\n', encoding='utf8')
    reader, _ = native_modules()
    bank = reader.read_lmt_file(SOURCES['w03_00'])
    aliases = []
    for source in bank.actions:
        owner = shared_curve_owner(bank, source)
        if owner is None:
            continue
        def header(h):
            r = dataclasses.asdict(h)
            r['null2'] = r['null2'].hex()
            return r
        aliases.append(dict(motion=source.id, owner=owner.id,
            source_header=header(source.header), owner_header=header(owner.header),
            basis='same nonzero curve-table address/count and identical pose header; independent TIML'))
    pin = sources()
    mbd = parse_mbd((ROOT/pin['mbd']['path']).read_bytes())
    binding = dict(schema=1, tests_executed=False, sources=tr.pin,
        status='native_static_evidence_not_runtime_verified',
        bindings=[dict(node=23, native_action=[3, 71], native_type='nHmAction::Wp03::cKijinStab',
            weapon_record='0x143fd5920', factory_table='0x142ef5c30', row_stride=32,
            row='0x142ef6510', dti='0x144fefb48', dti_registration='from_weapon_action_factory_table',
            factory='0x1417faa10', instance_vtable='0x143384780', entry_slot=6,
            entry='0x1417fe9e0', main_store='0x1417fe9f1', main_motion=112,
            generic_enter='0x1417845e0', connector=118,
            mbd=[b for e in mbd['entries'] if e['index']==112 for b in e['blocks'] if b['animation_id']==118]),
            dict(node=38, native_action=[3,72], entry='0x1417feae0', main_store='0x1417feaf1', main_motion=107),
            dict(node=3, native_action=[3,80], entry='0x1417fee10',
                explicit_connector_store='0x1417fee20', explicit_connector=119,
                main_update='0x141800200', main_store='0x141800249', main_motion=107)],
        shared_curve_aliases=aliases,
        facts=[
            dict(id='MBD_ROW_ZERO', va='0x141c00ab9', finding='No source-specific row: read serialized row zero. Preserve its values; no fabricated default.'),
            dict(id='PHASE_STEP', va='0x1424a85b8', finding='Transition 1 branches to current-key copy 1424a8770; next-key selection uses >= frame.'),
            dict(id='FORWARD_END', va='0x14224e340', finding='Truncate current and next source frame with epsilon 0.0005; flag1 predicts boundary, flag4 marks reached boundary. Forward one-shot scope.'),
            dict(id='UPPER_CUSTOM', va='0x1417fee10', finding='Upper action does not call generic LinkMotion entry: explicitly plays 119 then waits and submits 107.'),
            dict(id='SOURCE_34', finding='Native weapon action34 is cActCreepSingleMotion; project Draw(002) must not be bound to source node43.'),
            dict(id='SOURCE_1002_1003', finding='These expand native StepS/M/L and WpOnStep actions; do not label them climbing or bind project sheathed Roll to node27.')],
        unresolved=['native overlap/curve equivalence in UE blending',
                    'unimplemented predecessor gameplay contexts remain separately tracked',
                    'non-LinkMotion custom entry branches beyond the implemented cUpper case'])
    (ROOT/'Tools/MHW/native-main-motion-bindings.json').write_text(json.dumps(binding, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    (out/'native-main-motion-bindings.json').write_text(json.dumps(binding, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(source_extracted=True, tests_executed=False, explicit_aliases=len(aliases))))


if __name__ == '__main__':
    run()
