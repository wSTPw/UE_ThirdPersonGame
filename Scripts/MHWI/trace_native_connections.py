"""B06 read-only, hash-pinned native FSM tracing. Never executes game code.

Unwind CHAININFO ranges are collected together. Missing unwind metadata is an
explicit gap, never permission to decode an arbitrary 256-byte pseudo-function.
The original PE remains protected/unmodified; only a qualified local text-section
copy is used as disassembler input. This is source extraction, not a test suite.
"""
import bisect
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import struct

from native_control_evidence import Image

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT/'Tools/MHW/native-connector-code-sources.json'
OUT = ROOT/'Saved/MHWIRestoration/B06-20261025'


class NativeTrace:
    def __init__(self):
        self.pin = json.loads(PIN.read_text(encoding='utf8'))
        self.image = Image(self.pin['exe']['path'])
        if hashlib.sha256(self.image.blob).hexdigest() != self.pin['exe']['sha256']:
            raise ValueError('Original executable version changed')
        self.code = (ROOT/self.pin['text']['path']).read_bytes()
        if hashlib.sha256(self.code).hexdigest() != self.pin['text']['sha256']:
            raise ValueError('Qualified local analysis section changed')
        self.section = next(s for s in self.image.sections if s.Name.startswith(b'.text'))
        if len(self.code) != self.section.SizeOfRawData:
            raise ValueError('Analysis section has the wrong size')
        self.begin = self.image.base+self.section.VirtualAddress
        self.end = self.begin+len(self.code)
        self.records = [tuple(r) for r in self.image.functions
                        if self.begin <= self.image.base+r[0] < self.image.base+r[1] <= self.end]
        self.starts = [r[0] for r in self.records]
        self.record_set = set(self.records)
        self.owners = {}
        self.unwind_issues = []
        for r in self.records:
            try:
                owner = self._owner(r)
            except ValueError as error:
                self.unwind_issues.append(dict(record=r, reason=str(error)))
                continue
            self.owners.setdefault(owner, []).append(r)

    @lru_cache(None)
    def _owner(self, record, ancestry=()):
        if record in ancestry:
            raise ValueError('Unwind chain cycle')
        a,b,u = record
        if not self.begin <= self.image.base+a < self.image.base+b <= self.end:
            raise ValueError('Unwind range outside qualified code section')
        offset = self.image.offset(self.image.base+u)
        blob = self.image.blob
        if offset+4 > len(blob): raise ValueError('Truncated unwind header')
        version_flags, prolog, count, frame = struct.unpack_from('<4B', blob, offset)
        if version_flags & 7 != 1:
            raise ValueError('Unsupported unwind version')
        flags = version_flags >> 3
        if flags & 4:
            if flags & 3: raise ValueError('Chain mixed with exception handler')
            tail = offset+4+((count+1)//2)*4
            if tail+12 > len(blob): raise ValueError('Truncated chained record')
            parent = struct.unpack_from('<3I',blob,tail)
            if parent not in self.record_set: raise ValueError('Chained parent absent from pdata')
            return self._owner(parent, ancestry+(record,))
        return record

    def record_at(self, va):
        i = bisect.bisect_right(self.starts, va-self.image.base)-1
        if i < 0: return None
        r = self.records[i]
        return r if self.image.base+r[0] <= va < self.image.base+r[1] else None

    def _decode(self, begin, end):
        if not self.begin <= begin < end <= self.end:
            raise ValueError('Decode outside qualified section')
        code = self.code[begin-self.begin:end-self.begin]
        return [dict(va=hex(i.address),size=i.size,bytes=i.bytes.hex(),
                     mnemonic=i.mnemonic,operands=i.op_str)
                for i in self.image.md.disasm(code,begin)]

    def function(self, va):
        record = self.record_at(va)
        if record is None:
            declared = [r for r in self.pin.get('explicit_leaf_ranges',[]) if int(r['begin'],16)==va]
            if len(declared)==1:
                row = declared[0]
                return dict(requested_va=hex(va),owner_va=hex(va),
                            status='explicit_fixed_version_leaf_range_pending_review',
                            ranges=[row],instructions=self._decode(va,int(row['end'],16)),
                            boundary=row['evidence'])
            return dict(requested_va=hex(va),status='missing_unwind_metadata',instructions=[])
        owner = self._owner(record)
        spans = sorted(self.owners[owner])
        instructions, ranges = [], []
        for a,b,u in spans:
            rows = self._decode(self.image.base+a,self.image.base+b)
            instructions.extend(rows)
            ranges.append(dict(begin=hex(self.image.base+a),end=hex(self.image.base+b),
                               unwind_rva=hex(u),decoded_bytes=sum(x['size'] for x in rows),
                               expected_bytes=b-a))
        return dict(requested_va=hex(va),owner_va=hex(self.image.base+owner[0]),
                    status='chained_unwind_ranges_collected_not_runtime_verified',
                    ranges=ranges,instructions=instructions,
                    boundary='Only owned pdata spans; uncovered epilogues/leaf targets are gaps, not silently decoded.')


def run():
    trace = NativeTrace()
    functions = {name:trace.function(int(va,16)) for name,va in trace.pin['addresses'].items()}
    facts = [
        dict(id='generic_transition_gate',scope='generic_FSM_VM_only',
             instruction_va='0x1423fc998',return_path_va='0x1423fc9a4',
             finding='The dword at the evaluated drive context +0x30 must be zero before conditions are evaluated; otherwise this path returns false.',
             linkmotion_writer=None,linkmotion_release_predicate=None),
        dict(id='named_callback_slots',scope='generic_process_binding_only',
             finding='Binding resolves update/state/exit and stores their function objects at container +0x20/+0x28/+0x30.',
             bindings=[dict(name='update',string_va='0x143519144',store_va='0x142458e2e'),
                       dict(name='state',string_va='0x143525448',store_va='0x142458e41'),
                       dict(name='exit',string_va='0x143525450',store_va='0x142458e54')]),
        dict(id='state_result_not_completion',scope='generic_VM_callsite_only',
             call_va='0x1423feb6a',next_va='0x1423feb6f',
             finding='The state dispatch return is not used as a completion boolean at this loop callsite; transition evaluation is a separate call at 0x1423feb85.',
             concrete_state_target=None),
        dict(id='optional_core_hook',scope='generic_VM_callsite_only',
             load_va='0x1423fea76',call_va='0x1423fea93',
             finding='This branch calls an optional function pointer from Core +0xd0 before the update slot dispatch. Its concrete target/writer is not resolved.',
             concrete_hook_target=None),
        dict(id='generic_gate_release',scope='generic_FSM_VM_only',
             nonzero_gate_va='0x1423febc9',nonnegative_check_va='0x1423febd8',
             decrement_va='0x1423febe4',store_value_va='0x1423febef',
             positive_branch_va='0x1423febf6',clear_gate_va='0x1423fec08',
             finding='On this reached VM path, a nonzero drive +0x30 and a nonnegative ordered +0x34 value enter subtraction of singleton +0x94. A positive result skips clearing; the other result clears drive +0x30 and updates owner +0x2c bits. Negative or unordered initial values skip this path. Units, all branch predecessors, and LinkMotion use remain unresolved.',
             linkmotion_writer=None,linkmotion_release_predicate=None,
             time_unit=None),
        dict(id='generic_gate_reset',scope='generic_drive_initialization_only',
             function_va='0x1423fec80',clear_gate_va='0x1423fecdb',
             reset_value_va='0x1423fecde',
             finding='This generic drive setup/reset path clears +0x30 and writes float -1 to +0x34. This is not proof of LinkMotion completion or Phase reset.',
             weapon_specific=False),
        dict(id='local_phase_parameter_field',scope='local_parameter_metadata_only',
             type_name_va='0x1433c6598',type_registration_va='0x1401e15c0',
             dti_va='0x145000fc0',vtable_va='0x1431c93d0',
             get_dti_va='0x140f0c750',property_name_va='0x1433c6708',
             property_name_load_va='0x141920387',field_address_va='0x141920399',
             field_offset='0x10c',
             finding='Local nTimelineParam::PlMotionCommon type registration, vtable DTI getter and property registration associate mLinkMotionPhase with object +0x10c. This qualifies the local layout, not a selection consumer.'),
        dict(id='local_phase_parameter_zeroing',scope='local_parameter_initialization_only',
             constructor_va='0x14191f5b0',constructor_zero_store_va='0x14191f619',
             vtable_slot5_va='0x141921cb0',slot5_zero_store_va='0x141921d99',
             finding='Constructor and vtable slot 5 each zero a qword at +0x10c, covering the Phase field. Slot 5 invocation timing and action-entry/missing-track reset are unresolved. Fresh parameter initialization is not a missing-track fallback rule.',
             action_entry_reset=None,phase1_selection=None,missing_track_fallback=None),
    ]
    report = dict(schema=1,status='static_extraction_pending_tests',sources=trace.pin,
                  original_pe_modified=False,native_code_executed=False,tests_executed=False,
                  unwind_issues=trace.unwind_issues,functions=functions,facts=facts,
                  weapon_exit_rule=None,phase_selection_rule=None,new_connections_enabled=0,
                  next_step='Resolve actual LinkMotion state/update callback target or Core gate writer/releaser; then trace Phase1 load and fallback.')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'native-call-path.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(OUT/'native-call-path.json'),functions=len(functions),
                          tests_executed=False,weapon_exit_rule=None,phase_selection_rule=None)))
    return report


if __name__=='__main__': run()
