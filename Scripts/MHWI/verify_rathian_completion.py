"""Editor readback of missing-animation completion; no original-game fidelity claim."""
import json,hashlib
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.get_project_file_path()).resolve().parent
BATCH=ROOT/'Saved/RathianAnimationCompletion-20261030'
def run():
    exp=json.loads((BATCH/'export.json').read_text())
    imp=json.loads((BATCH/'import.json').read_text())
    base=json.loads((BATCH/'baseline.json').read_text())
    assert exp['status']=='done' and not exp['errors']
    allnames={'A_'+n for bank in exp['banks'] for n in bank['frames']}
    old=set(exp['existing']);new={r['name'] for r in exp['exported']}
    assert not old&new and old|new==allnames
    assert {r['name'] for r in imp['imported']}==new
    sk=unreal.load_asset('/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton')
    paths=unreal.EditorAssetLibrary.list_assets('/Game/MHWI/Rathalos/Animations',recursive=True,include_folder=False)
    actual={p.split('/')[-1].split('.')[0] for p in paths}
    assert actual==allnames,(len(actual),len(allnames))
    for row in imp['imported']:
        seq=unreal.load_asset(row['path'])
        assert seq.get_class().get_name()=='AnimSequence' and seq.get_editor_property('skeleton')==sk
        assert abs(seq.get_editor_property('sequence_length')-row['expected_seconds'])<0.018
        p=ROOT/'Content/MHWI/Rathalos/Animations'/(row['name']+'.uasset')
        assert p.is_file()
    for row in base['old']:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    poses=[]
    for bank in exp['banks']:
        candidates=[r for r in exp['exported'] if r['bank']==bank['path'] and r['source_frames']>2]
        if not candidates:continue
        row=max(candidates,key=lambda r:r['source_frames'])
        seq=unreal.load_asset('/Game/MHWI/Rathalos/Animations/'+row['name'])
        tracks=unreal.AnimationLibrary.get_animation_track_names(seq)
        changed=[]
        for bone in tracks:
            a=unreal.AnimationLibrary.get_bone_pose_for_time(seq,bone,0,False)
            b=unreal.AnimationLibrary.get_bone_pose_for_time(seq,bone,row['expected_seconds']*0.43,False)
            def values(t):
                return [t.translation.x,t.translation.y,t.translation.z,t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w,t.scale3d.x,t.scale3d.y,t.scale3d.z]
            if any(abs(x-y)>1e-5 for x,y in zip(values(a),values(b))):changed.append(str(bone))
        poses.append(dict(bank=bank['path'],asset=row['name'],tracks=len(tracks),changing_bones=len(changed)))
    result=dict(passed=True,total=len(allnames),added=len(new),preserved=len(old),banks=exp['banks'],pose_samples=poses,old_hashes_unchanged=True,source_archive_lmt_count=len(base['lmt_paths']),original_game_fidelity_verified=False)
    (BATCH/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return dict(passed=True,total=len(allnames),added=len(new),preserved=len(old),pose_samples=poses)
