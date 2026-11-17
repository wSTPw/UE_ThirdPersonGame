"""Add missing em001 FBX animations, never replacing existing assets."""
import json,hashlib
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.get_project_file_path()).resolve().parent
BATCH=ROOT/'Saved/RathianAnimationCompletion-20261030'
DEST='/Game/MHWI/Rathalos/Animations'
SKEL='/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton'
def run(limit=12):
    src=json.loads((BATCH/'export.json').read_text())
    path=BATCH/'import.json'
    report=json.loads(path.read_text()) if path.exists() else dict(imported=[],errors=[])
    sk=unreal.load_asset(SKEL)
    assert sk and sk.get_class().get_name()=='Skeleton'
    done={r['name'] for r in report['imported']}
    pending=[r for r in src['exported'] if r['name'] not in done]
    for row in pending[:limit]:
        name=row['name'];assetpath=DEST+'/'+name
        assert hashlib.sha256(Path(row['fbx']).read_bytes()).hexdigest()==row['sha256']
        if unreal.EditorAssetLibrary.does_asset_exist(assetpath):
            raise RuntimeError('Unjournaled existing asset; refusing overwrite: '+assetpath)
        opts=unreal.FbxImportUI()
        for k,v in dict(automated_import_should_detect_type=False,import_mesh=False,import_animations=True,import_materials=False,import_textures=False,mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION,skeleton=sk).items():opts.set_editor_property(k,v)
        data=opts.get_editor_property('anim_sequence_import_data')
        for k,v in dict(use_default_sample_rate=False,custom_sample_rate=60,remove_redundant_keys=False,import_bone_tracks=True).items():data.set_editor_property(k,v)
        task=unreal.AssetImportTask();task.filename=row['fbx'];task.destination_path=DEST;task.destination_name=name;task.automated=True;task.replace_existing=False;task.save=True;task.options=opts
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        seq=unreal.load_asset(assetpath)
        assert seq and seq.get_class().get_name()=='AnimSequence',name
        length=seq.get_editor_property('sequence_length')
        assert seq.get_editor_property('skeleton')==sk,name
        assert abs(length-row['expected_seconds'])<0.018,(name,length,row['expected_seconds'])
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq,only_if_is_dirty=False),name
        report['imported'].append(dict(name=name,path=seq.get_path_name(),seconds=length,expected_seconds=row['expected_seconds'],skeleton=sk.get_path_name()))
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return dict(imported=len(report['imported']),pending=len(pending)-min(limit,len(pending)),export_status=src['status'])
