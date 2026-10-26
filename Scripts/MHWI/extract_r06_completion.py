"""B09 fixed-source development extraction; never executes game code or tests."""
import json
from pathlib import Path
import struct
from trace_native_connections import NativeTrace

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIRestoration/B09-20261025'


def run():
    trace = NativeTrace()
    functions = {}
    for name, va in dict(tree_update=0x142254aa0, blend_advance=0x1422564f0,
                         previous_weight=0x142253450, current_weight=0x142253250,
                         curve_setup=0x1422530b0, layer_setup=0x142253720).items():
        functions[name] = trace.function(va)
    # The B08 "vtable" field names a DTI vtable (4 slots), NOT an action instance
    # vtable. Resolve factory -> instance vtable before reading enter/update slots.
    registrations = {
        11: 0x1401b7f50, 67: 0x1401b7fa0, 68: 0x1401b7ff0,
        71: 0x1401b8090, 79: 0x1401b84a0, 80: 0x1401b84f0,
        81: 0x1401b8540, 82: 0x1401b8180, 83: 0x1401b81d0,
        84: 0x1401b8270, 85: 0x1401b8450, 87: 0x1401b75a0,
    }
    def qword(va):
        return struct.unpack_from('<Q', trace.image.blob, trace.image.offset(va))[0]
    def rip(row):
        return int(row['va'], 16) + row['size'] + struct.unpack('<i', bytes.fromhex(row['bytes'])[-4:])[0]
    vtables = []
    for action, registration in registrations.items():
        reg = trace.function(registration)
        functions[f'action_{action}_registration'] = reg
        dti = next(rip(r) for r in reg['instructions'] if r['mnemonic']=='lea' and r['operands'].startswith('rcx, [rip'))
        declared = qword(0x142ef5c30 + action * 32 + 8)
        if dti != declared:
            raise ValueError('Native action registry changed')
        dti_vtable = next(rip(r) for r in reg['instructions'] if r['mnemonic']=='lea' and r['operands'].startswith('rax, [rip'))
        factory = qword(dti_vtable + 8)
        build = trace.function(factory)
        functions[f'action_{action}_factory'] = build
        instance_vtable = next(rip(r) for r in build['instructions']
            if r['mnemonic']=='lea' and r['operands'].startswith('rax, [rip') and 0x143000000 < rip(r) < 0x144000000)
        slots = [qword(instance_vtable + k*8) for k in range(10)]
        vtables.append(dict(action=action, dti=hex(dti), registration=hex(registration),
            factory=hex(factory), dti_vtable=hex(dti_vtable), instance_vtable=hex(instance_vtable),
            slots=[hex(v) for v in slots]))
        for index in (6, 7):
            functions[f'action_{action}_slot_{index}'] = trace.function(slots[index])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'completion-native-functions.json').write_text(json.dumps(dict(
        tests_executed=False, sources=trace.pin, functions=functions, vtables=vtables), indent=2)+'\n')
    # Each terminal main comes from a qualified store/request, never ActionNo.
    # Action11/85 have extra native custom-entry branches; terminal proof alone
    # must not be reported as implementation of those branches.
    stores = {
        11: (1, 'action_11_slot_7', 0x1417ffea1),
        67: (12, 'action_67_slot_6', 0x1417fe8b1),
        68: (2, 'action_68_slot_6', 0x1417fe911),
        71: (23, 'action_71_slot_6', 0x1417fe9f1),
        79: (4, 'action_79_factory', 0x1417fb781),
        80: (3, 'action_80_slot_7', 0x141800249),
        81: (10, 'action_81_factory', 0x1417f5cb1),
        82: (8, 'action_82_factory', 0x1417fbb11),
        83: (9, 'action_83_factory', 0x1417fb9e1),
        84: (7, 'action_84_factory', 0x1417f5b81),
        85: (11, 'action_85_slot_6', 0x1417fed2a),
        87: (45, 'action_87_factory', 0x1417f6071),
    }
    binding_path = ROOT/'Tools/MHW/native-main-motion-bindings.json'
    bindings = json.loads(binding_path.read_text(encoding='utf8'))
    by_node = {r['node']: r for r in bindings['bindings']}
    for action, (node, function, address) in stores.items():
        instruction = next(r for r in functions[function]['instructions'] if int(r['va'], 16)==address)
        encoded = int(instruction['operands'].rsplit(', ', 1)[1], 16)
        if encoded & ~0x1ff != 0xc000:
            raise ValueError('Native store is not a qualified weapon-bank request')
        row = by_node.setdefault(node, dict(node=node, native_action=[3, action]))
        row.update(main_motion=encoded & 0x1ff, main_store=hex(address),
            main_binding_status='native_terminal_main_confirmed_static_not_tested',
            evidence_function=function, evidence='Saved/MHWIRestoration/B09-20261025/completion-native-functions.json')
        if action in (11, 85):
            row['custom_entry_boundary'] = 'Additional source/state-dependent entry branches are not implemented by terminal main proof.'
    bindings['bindings'] = list(by_node.values())
    bindings['b09_sources'] = trace.pin
    bindings['b09_evidence'] = 'Scripts/MHWI/extract_r06_completion.py'
    binding_path.write_text(json.dumps(bindings, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    facts = dict(schema=1, status='static_evidence_and_partial_adapter_implementation',
        tests_executed=False, sources=trace.pin, main_binding_nodes=sorted(by_node),
        functions='Saved/MHWIRestoration/B09-20261025/completion-native-functions.json',
        blend_facts=[
            dict(address='0x142255b8e', finding='Request +0xc populates interpolation duration at tree+4c0; +14 is a separate tail fade duration at +4c8.'),
            dict(address='0x142256594', finding='Blend elapsed advances separately from source motion position, using the native step supplied to blend advance.'),
            dict(address='0x14225332d', finding='When the native node/request enables this path, overlap waits for forward source frame beyond endpoint-overlap; then clears elapsed and enables tail fade. The MotionTree/request flags must be proven before enabling this branch in UE.'),
            dict(address='0x14225338b', finding='Tail weight decreases using elapsed/duration, then removes the current layer; curve selectors are separate from duration.'),
            dict(address='0x1417fed51', finding='StepSlash custom entry checks actual prior group/action and player state; selected group1 103/110/115 takes explicit151 before main101.'),
            dict(address='0x1417fe610', finding='SpiritI custom entry includes state/source-dependent 113/116/126/130/132/152, then generic entry; the LinkMotion table alone is not its full policy.')],
        remaining_development=[
            'MotionTree/request flags gating interpolation and tail envelopes, curve selection and native owner+6c blend-clock scaling still need migration. No guessed automatic tail fade was enabled. UE offers a pre-root-extraction Montage_UpdateWeight hook for the eventual qualified adapter.',
            'Native Creep/Step/KijinComboShot source gameplay owners must bind their actual identity and live montage instance; the new binding API has no such production callers yet.',
            'StepSlash and SpiritI custom native entry branches still need full state/identity consumer migration; do not enable guessed branches.'])
    (ROOT/'Tools/MHW/native-r06-completion-evidence.json').write_text(json.dumps(facts, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(source_extracted=True, tests_executed=False,
                          functions=len(functions), target_actions=len(vtables))))


if __name__ == '__main__':
    run()
