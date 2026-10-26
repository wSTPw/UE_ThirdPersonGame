"""B10 pinned source extraction for source owners/custom entries/blending. No tests."""
import json
import hashlib
from pathlib import Path
import re
import struct
from trace_native_connections import NativeTrace

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'Saved/MHWIRestoration/B10-20261025'


def run():
    tr = NativeTrace()
    def u(va, fmt='Q'):
        return struct.unpack_from('<'+fmt, tr.image.blob, tr.image.offset(va))[0]
    def rip(row):
        return int(row['va'], 16)+row['size']+struct.unpack('<i', bytes.fromhex(row['bytes'])[-4:])[0]
    def function(va):
        result = tr.function(va)
        if result['instructions']: return result
        upper = min((tr.image.base+r[0] for r in tr.records if tr.image.base+r[0]>va), default=tr.end)
        pending, instructions = [va], {}
        while pending:
            pc = pending.pop()
            while va <= pc < upper and pc not in instructions:
                decoded = list(tr.image.md.disasm(tr.code[pc-tr.begin:pc-tr.begin+15], pc, count=1))
                if not decoded: raise ValueError('Undecodable reached leaf instruction')
                ins = decoded[0]
                if ins.mnemonic in ('int3','ud2'): raise ValueError('Reached padding/trap in leaf')
                instructions[pc] = dict(va=hex(pc), size=ins.size, bytes=ins.bytes.hex(),
                                        mnemonic=ins.mnemonic, operands=ins.op_str)
                if ins.mnemonic.startswith('ret'): break
                if ins.mnemonic.startswith('j'):
                    if ins.op_str.startswith('0x'):
                        target = int(ins.op_str,16)
                        if va <= target < upper: pending.append(target)
                    if ins.mnemonic=='jmp': break
                pc += ins.size
        return dict(requested_va=hex(va), owner_va=hex(va),
                    status='static_reachable_leaf_cfg_not_tested',
                    boundary='Known call/vtable entry; direct reachable CFG only; ret/tail-jump terminates; next pdata bounds address space, not a guessed byte count.',
                    instructions=[instructions[k] for k in sorted(instructions)])
    actions = {}
    for action in (7, 18, 19, 20, 21, 22, 30, 31, 32, 34, 55, 56, 57, 58, 59, 60, 61, 62, 63, *range(104, 113)):
        actions[(3, action)] = u(0x142ef5c30+action*32+8)
    for action in (103, 104, 105, 106, 107, 110, 111, 112, 115, 116, 117):
        actions[(1, action)] = u(0x142edc760+action*32+8)
    by_dti = {}
    for identity, dti in actions.items(): by_dti.setdefault(dti, []).append(identity)
    found = {}
    # Registration init functions use RIP-relative rcx/rax. Only owned function
    # instructions are accepted, never the raw search hit by itself.
    for match in re.finditer(rb'\x48\x8d\x0d', tr.code):
        offset = match.start()
        va = tr.begin+offset
        target = va+7+struct.unpack_from('<i', tr.code, offset+3)[0]
        if target not in by_dti: continue
        reg = tr.function(va)
        if not any(int(r['va'],16)==va and r['mnemonic']=='lea' for r in reg['instructions']): continue
        vtables = [rip(r) for r in reg['instructions'] if r['mnemonic']=='lea' and r['operands'].startswith('rax, [rip')]
        if len(vtables)!=1: continue
        vt = vtables[0]
        try: factory = u(vt+8)
        except ValueError: continue
        if not tr.begin <= factory < tr.end: continue
        build = function(factory)
        constructor = build
        if not any(r['mnemonic']=='lea' and '[rip' in r['operands']
                   and 0x143000000 < rip(r) < 0x144000000 for r in constructor['instructions']):
            jumps = [r for r in build['instructions'] if r['mnemonic']=='jmp' and r['operands'].startswith('0x')]
            if jumps: constructor = function(int(jumps[-1]['operands'],16))
        ivts = [rip(r) for r in constructor['instructions'] if r['mnemonic']=='lea'
                and '[rip' in r['operands'] and 0x143000000 < rip(r) < 0x144000000]
        if not ivts: continue
        instance = ivts[-1]
        slots = [u(instance+i*8) for i in range(10)]
        found[target] = dict(registration=reg, factory=build, constructor=constructor, instance_vtable=hex(instance),
            slots=[hex(v) for v in slots], dti_getter=function(slots[4]),
            entry=function(slots[6]), update=function(slots[7]))
    records = []
    for identity, dti in actions.items():
        table = 0x142ef5c30 if identity[0]==3 else 0x142edc760
        name_pointer = u(table+identity[1]*32+24)
        name_offset = tr.image.offset(name_pointer)
        name_end = tr.image.blob.index(b'\0', name_offset)
        record = dict(identity=list(identity), dti=hex(dti), registry_name_pointer=hex(name_pointer),
                      registry_name=tr.image.blob[name_offset:name_end].decode('utf8'),
                      **found.get(dti, {}))
        records.append(record)
    functions = {hex(va):function(va) for va in (0x1417fe610, 0x1417fed20,
        0x141f776d0, 0x1417845e0, 0x142255820, 0x1422564f0,
        0x142253250, 0x142253450, 0x142253640, 0x141c014f0,
        0x14187cb80, 0x14187a7c0, 0x141719db0, 0x1417468c0,
        0x141f77700, 0x141bffc70, 0x142228f50, 0x14221ace0,
        0x14225be20, 0x14225f9f0, 0x14236a300, 0x142368a90,
        0x142256fd0, 0x142256650, 0x142254aa0,
        0x14177f950, 0x141787950, 0x1417896e0, 0x1417ffe50)}
    # Pdata also covers the embedded jump tables. Keep their bytes as DATA;
    # do not publish Capstone's accidental decoding as source instructions.
    spirit_entry = functions['0x1417fe610']
    spirit_entry['embedded_data_ranges'] = [dict(begin='0x1417fe824', end='0x1417fe89d',
        meaning='5 destination RVAs followed by 101 byte selectors; not executable instructions')]
    spirit_entry['instructions'] = [r for r in spirit_entry['instructions']
        if not 0x1417fe824 <= int(r['va'],16) < 0x1417fe89d]
    # Four adjacent identity getters have a ret followed by int3 padding, not a
    # speculative 256-byte function. The switch byte table is DATA, not code.
    getters = {hex(begin):tr._decode(begin, begin+0x12) for begin in
               (0x141bffa20, 0x141bffa40, 0x141bff740, 0x141bff760)}
    destinations = struct.unpack_from('<5I', tr.code, 0x1417fe824-tr.begin)
    selectors = tr.code[0x1417fe838-tr.begin:0x1417fe838-tr.begin+101]
    switches = [dict(destination=hex(tr.image.base+va),
                     previous_actions=[i+1 for i, v in enumerate(selectors) if v==index])
                for index, va in enumerate(destinations)]
    out = dict(schema=1, tests_executed=False, source_pins=tr.pin,
        source_actions=records, functions=functions, identity_getters=getters,
        spirit_i_switch=switches, spirit_i_post_override=[57,60,63])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'remaining-native-functions.json').write_text(json.dumps(out,indent=2)+'\n')
    tree_path = ROOT/'ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp/wp03/mot/wp03_tree/wp03_tree.at'
    tree_blob = tree_path.read_bytes()
    magic, version, count = struct.unpack_from('<3I', tree_blob)
    # v7 header has three u32 values; each serialized node is 0x20 bytes.
    if magic != 0x18091001 or version != 7 or len(tree_blob) != 12+count*32:
        raise ValueError('MotionTree layout requires new source qualification')
    tree_rows = [struct.unpack_from('<8I', tree_blob, 12+i*32) for i in range(count)]
    if any((r[0] >> 12) == 12 for r in tree_rows):
        raise ValueError('Bank12 MotionTree nodes require new blend gate qualification')
    evidence = dict(schema=1, status='r06_development_complete_uncompiled_untested',
        tests_executed=False, runtime_verified=False, source_pins=tr.pin,
        function_ranges='Saved/MHWIRestoration/B10-20261025/remaining-native-functions.json',
        registry=dict(weapon='0x142ef5c30', common='0x142edc760', stride=32,
                      name_pointer_offset=24, dti_getter_slot=4, entry_slot=6, update_slot=7),
        source_owners='Tools/MHW/native-r06-source-owners.json',
        custom_entry=dict(spirit_i='0x1417fe610', step_slash='0x1417fed20',
            prior_draw_snapshot='0x141f77722 -> 0x141f7772c, +76a8 -> +76aa',
            prior_identity=['0x141bffa20','0x141bffa40'], current_identity=['0x141bff740','0x141bff760'],
            rule='Explicit request before generic Phase sampling; ordered generic lookup; post override last; preserve intermediate MBD predecessor.',
            post_override=out['spirit_i_post_override']),
        motion_tree=dict(path=tree_path.relative_to(ROOT).as_posix(),
            sha256=hashlib.sha256(tree_blob).hexdigest(), magic=hex(magic), version=version,
            count=count, rows=[list(r) for r in tree_rows],
            direct_weapon_request_bank=12, node_lookup='0x142255856..0x14225594b',
            interpretation='Bank12 direct leaves have no node; no request100/200 injection. Source .at nodes belong to bank1.'),
        blend=dict(request_builder='0x141c014f0', mode_consumer='0x141c01624..0x141c01667',
            weapon_mbd_mode=1, request_flags=2, curve_selectors=[0,0], curve='linear',
            initial_envelope_enabled=False, tail_envelope_enabled=False,
            raw_overlap='Preserved as source data; disabled without request200; never used as a UE Stop duration.',
            capture=['0x142255e6d','0x142255ee3','0x14236a300'],
            first_evaluation_gate=['0x142256586','0x142368a90'],
            common_mode0=['0x142255b98','0x142254e6b','0x142255022'],
            consumer='UMHWIAnimInstance proxy: full destination root carrier, displayed-pose capture, linear interpolation before pose output.'),
        clock=dict(global_owner_pointer='0x1451c4148', constructor='0x14225be20',
            rate_constant='0x14225c472: +58 = 60', frame_delta='0x14225f9f0 -> +94',
            unit_manager='0x14221ada1: global+94 * group+9c -> +a0; +a4 = +a0 / global+58',
            unit_copy='0x142228f90: manager+a0 -> owner+6c',
            player_consumer='0x141bffd26: owner+6c -> tree virtual+78 / 0x1422564f0',
            blend_step='0x142256594', ue_consumer='UMHWIAnimInstance::Montage_UpdateWeight(DeltaSeconds) * 60',
            motion_play_rate_affects_blend_clock=False),
        structural_boundary='node86 retains no inbound edge and zero runtime records',
        adapter_boundaries=['Existing project cancel windows and new source cancel properties remain R07.',
            'Canonical standing hit-reaction owners complete R06 sources; full environmental/mirrored reactions remain R24.',
            'Slinger burst trigger is native frame36; ammunition type/parts/damage model remain R25.',
            'Project neutral IDLE/WALK owners and directional drawn rolls supply sources; complete locomotion remains R28.'])
    (ROOT/'Tools/MHW/native-r06-remaining-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(extracted=True, tests_executed=False,
                         source_actions=len(records), registered=sum('entry' in r for r in records))))
    return tr, function


if __name__ == '__main__': run()
