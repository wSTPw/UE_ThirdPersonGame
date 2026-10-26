"""Static source collation, not a native executor or a test suite.

Predecessor TIML stays distinct from shared body poses and connector timelines.
Exit and Phase1 selection remain unset until an instruction-level chain exists.
"""
import json
from pathlib import Path
from audit_native_timing import parse_lmt, names, listify
from read_source_fsm import XfsReader
import native_connector_source as source

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Saved/MHWIRestoration/B06-20261025'


def run():
    pin = source.sources()
    base = source.build()
    labels = ROOT / 'Saved/MHWIImport/SourceFidelity-20261023/timing-FreeHK-upstream/MHW-Free-HyperKinetics-main/struct'
    lmt = parse_lmt(ROOT/pin['lmt']['path'], names(labels/'TIMLTimelineParam.txt'), names(labels/'TIMLDatatypes.txt', True))
    tracks = [dict(motion=m['index'], group=g['name'], track=t)
              for m in lmt['entries'] for g in m['groups'] for t in g['tracks']
              if t['name']=='mLinkMotionPhase']
    fsm = XfsReader((ROOT/pin['fsm']['path']).read_bytes()).parse()['root']
    nodes = {n['mId']:n for n in fsm['mpRootCluster']['mpNodeList']}
    mapping = json.loads((ROOT/pin['mapping']['path']).read_text(encoding='utf8'))
    control_path = ROOT/'Tools/MHW/native-connector-control-evidence.json'
    control = json.loads(control_path.read_text(encoding='utf8'))
    if control['scope'] != 'generic_VM_and_parameter_metadata_only':
        raise ValueError('Native control evidence scope requires explicit review')
    if control['weapon_exit_rule'] is not None or control['phase_selection_rule'] is not None:
        raise ValueError('Generic VM facts cannot silently qualify weapon rules')
    bindings = {}
    for name, move in mapping['moves'].items():
        bindings.setdefault(move['fsm_node_id'], []).append(dict(move=name, clip=move['clip']))
    phase_nodes = []
    for ident in (60,76):
        incoming = sorted({n['mId'] for n in nodes.values() for e in listify(n['mpLinkList'])
                           if e['mDestinationNodeId']==ident})
        predecessors = []
        for predecessor in incoming:
            clips = bindings.get(predecessor, [])
            predecessors.append(dict(node_id=predecessor, raw_name=nodes[predecessor]['mName'],
                action=nodes[predecessor]['mpProcessList']['mpParameter'], project_bindings=clips,
                native_phase_tracks=[t for t in tracks if t['motion'] in
                                     [int(c['clip'].rsplit('_',1)[1]) for c in clips]],
                missing_track_does_not_prove_default_zero=True))
        phase_nodes.append(dict(node_id=ident, raw_parameters=nodes[ident]['mpProcessList']['mpParameter'],
            predecessors=predecessors, phase_selection_rule=None, phase_reset_rule=None,
            fallback_rule=None, local_parameter_field_evidence='local_phase_parameter_field',
            local_parameter_zeroing_evidence='local_phase_parameter_zeroing',
            status='local_field_and_initialization_identified_selection_consumer_unresolved'))
    for c in base['connections']:
        c['native_exit_status']='instruction_dataflow_unresolved_no_exit_frame_authored'
        c['generic_vm_gate_evidence']='generic_transition_gate'
        c['generic_vm_release_evidence']='generic_gate_release'
        c['generic_vm_reset_evidence']='generic_gate_reset'
        c['native_exit_next_step']='Resolve the LinkMotion-specific gate writer and prove its release path: generic subtraction, explicit clear, or another path. Identify actual callback and value units; generic VM release alone cannot enable a connector.'
        c['next_acceptance']='Prove completion/stage choice/commit clock before enabling; then check body/root/hit/cancel timing.'
        if c['node_id'] in (80,81):
            c['status']='source_binding_corrected_B05_pending_next_stage_tests'
    result = dict(schema=1, status='development_pending_tests', sources=pin,
        generic_control_evidence=control, generic_control_path=control_path.relative_to(ROOT).as_posix(),
        tests_executed=False, phase_nodes=phase_nodes, all_source_phase_tracks=tracks,
        connections=base['connections'], new_connections_enabled=0,
        native_exit_consumer_confirmed=False, native_phase_consumer_confirmed=False)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'source-logic-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return result


if __name__=='__main__':
    r=run()
    print(json.dumps(dict(status=r['status'],connections=len(r['connections']),tests_executed=False)))
