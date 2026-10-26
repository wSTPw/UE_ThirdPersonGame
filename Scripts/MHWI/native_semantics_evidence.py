"""Collate source/raw-control evidence without guessing native runtime semantics.

Reads the prior complete source audit and locally cached public implementations.
Does not author Unreal assets or change game files. The mask statistics are data
observations, never accepted as decoded input/cancel windows.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/MHWIImport/NativeFidelity-20261024'
AUDIT=ROOT/'Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=json.loads(AUDIT.read_text(encoding='utf8'))
    public=OUT/'public'
    dti_path=public/'dti_prop_dump.h'
    dti=dti_path.read_text(encoding='utf8')
    classes={}
    for name in ['cFSMPl_W03','nTimelineParam::PlMotionInput','nTimelineParam::PlMotionCommon','nPlFSM::LinkMotion_W03']:
        match=re.search(r'^// '+re.escape(name)+r' vftable:.*?^};',dti,re.S|re.M)
        assert match,name
        block=match.group()
        classes[name]=dict(line_start=dti.count('\n',0,match.start())+1,text=block)
        (OUT/('native-'+name.replace('::','-')+'.txt')).write_text(block+'\n',encoding='utf8')
    inputs=source['input_bit_intervals']
    masks=[]
    for row in inputs:
        track=row['track']; keys=track['keys']
        masks.append(dict(motion=row['motion'],track=track['name'],key_count=len(keys),transition_codes=sorted({k['transition'] for k in keys}),control_l_unique=sorted({k['control_l'] for k in keys}),control_r_unique=sorted({k['control_r'] for k in keys}),value_has_bits_outside_control_l=any(int(k['value']) & ~int(k['control_l']) for k in keys),semantics='raw_values_only: control_l_mask_candidate_not_native_confirmed'))
    speeds=[]
    for row in source['motion_speed']:
        keys=row['track']['keys']
        if len({k['value'] for k in keys})>1:
            samples=[]
            for a,b in zip(keys,keys[1:]):
                samples.append(dict(frame=(a['frame']+b['frame'])/2,linear_value=(a['value']+b['value'])/2,quadratic_ease_in_value=a['value']+(b['value']-a['value'])*.25))
            speeds.append(dict(motion=row['motion'],keys=keys,diagnostic_midpoints=samples,disposition='Keep existing linear runtime; newer public EFX tool labels source code 2 LINEAR. This conflicts with old FreeHK QUAD label. Local native instruction/active-game confirmation remains unavailable.'))
    nodes={n['node_id']:n for n in source['fsm_nodes']}
    motions={m['index']:m for m in source['source']['entries']}
    links=[]
    for node in source['connectors']:
        p=node['process']['mpParameter']
        motion_ids=[p['MotionNo']]+([p['MotionNo_Phase1']] if p['MotionNo_Phase1']>=0 else [])
        links.append(dict(node_id=node['node_id'],name=node['name'],raw_process=node['process'],source_motions=[dict(index=x,frame_count=motions[x]['source_frame_count'],loop_frame=motions[x]['source_loop_frame'],control_tracks=[dict(group=g['name'],track=t) for g in motions[x]['groups'] for t in g['tracks'] if t['name'] in ['mActionPhase','mActionPhaseSub','mLinkMotionPhase','mPosInterpolationProgress','mAngleInterpolationProgress','mMotionSpeed','mWeaponMotionNo']]) for x in motion_ids],ordered_exits=[dict(order=i,destination_node_id=e['mDestinationNodeId'],destination_name=nodes[e['mDestinationNodeId']]['name'],destination_process=nodes[e['mDestinationNodeId']]['process'],condition_id=e['mConditionId'],condition_tree=e['condition_tree']) for i,e in enumerate(node['links'])],main_motion_entry_frame=None,entry_frame_status='Not serialized by nPlFSM::LinkMotion_W03; must recover from ActionNo native implementation or original-game observation. Never infer as full connector plus full main action.'))
    (OUT/'native-connector-evidence.json').write_text(json.dumps(dict(status='source_table_evidence_not_native_evaluator',source_audit_sha256=sha(AUDIT),connectors=links),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    public_files=[]
    for path in sorted(public.iterdir()):
        if path.is_file():
            public_files.append(dict(path=path.relative_to(ROOT).as_posix(),size=path.stat().st_size,sha256=sha(path)))
    getter_count=Counter(re.findall(r'Getter:(0x[0-9A-Fa-f]+)',classes['cFSMPl_W03']['text']))
    report=dict(status='static_data_and_public_tool_evidence_native_execution_unresolved',source_audit_sha256=sha(AUDIT),native_lmt_sha256=source['source']['sha256'],native_fsm_sha256=source['fsm_sha256'],dti_dump_sha256=sha(dti_path),dti_source_commit='4a124e4073519eaf19e3a446cb62d375d8da3209',dti_version_boundary='Public reflection dump from 2023 is not automatically ABI-identical to local exe. Offsets and getter VAs are reference metadata only.',classes=classes,pseudo_getter_histogram=getter_count,input_tracks=masks,changing_speed_curves=speeds,source_link_order_status='Preserved. Public original FSM author guide describes top-first priority, but local executable evaluator is not decoded.',public_sources=[dict(url='https://github.com/Dimcirui/MHW-EFX-Editor/blob/v0.7.7/efx_format/sim/resolve.py',cache='public/efx-resolve.py',version='v0.7.7',archive='public/efx-v0.7.7.zip'),dict(url='https://github.com/Andoryuuta/MHW-DTI-Dumps/blob/4a124e4073519eaf19e3a446cb62d375d8da3209/dti_prop_dump.h',cache='public/dti_prop_dump.h'),dict(url='https://github.com/Ezekial711/MonsterHunterWorldModding/wiki/Moveset-Editing-via-wp-.fsm',cache='public/fsm-guide.md'),dict(url='https://github.com/wowo-dot/mhw-anim-tools/blob/main/blender_adapter/timl_sampling.py',status='previously_cached',scope='TIML writeback sampling supports CONSTANT/LINEAR; no native TIML executor evidence found.')],public_files=public_files,findings=[dict(item='mMotionSpeed transition 2',confidence='public_implementation_only',result='Current linear speed interpolation matches newer EFX tool; do not change to t squared from old Blender label.'),dict(item='PlMotionInput bit meanings',confidence='unresolved',result='Reflection confirms 8 u32 flags + 8 u32 triggers. Per-bit semantics and transition 5 evaluator are not exposed.'),dict(item='cFSMPl_W03 input conditions',confidence='reflection_metadata_only',result='Public dump exposes named pseudo-properties sharing one transitionDummy getter; cannot derive actual input-history or timing from this getter address.'),dict(item='LinkMotion main entry',confidence='unresolved',result='Serialized class contains MotionNo[0/1] only, no main start frame. Existing source endpoint fit is not native confirmation.'),dict(item='Turn/weapon properties',confidence='reflection_and_source_keys_only',result='Exact field names/values/timestamps are available; angle index tables, weapon family/attachment switches and reset/trigger consumption are unresolved.')],local_game_process_observation=dict(status='not_running',observation_date='2026-10-24',method='Host Get-Process MonsterHunterWorld (read-only)',status_origin='Recorded by agent in this investigation; this collator does not query processes again.',not_launched_during_this_subtask=True),limitations=['No game injection, process writes, keyboard input, installation modifications, or native code execution.', 'Protected on-disk exe .text cannot qualify native evaluator; string/reflection presence does not prove execution semantics.', 'Public EFX simulation deliberately excludes BIG_FLAGS. Never use its float fallback for PlMotionInput transition 5.'])
    destination=OUT/'native-control-summary.json'
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(destination),connectors=len(links),motion_references=sum(len(x['source_motions']) for x in links),input_tracks=len(masks),input_keys=sum(x['key_count'] for x in masks),changing_speed_curves=len(speeds),pseudo_getter_histogram=getter_count),indent=2))


if __name__=='__main__':
    main()
