"""Blender: complete pinned em001 motion banks, preserving existing UE animations."""
import sys,json,struct,hashlib,types,importlib
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'ArtSource/ThirdParty/MHWRathalos'
OUT=ROOT/'Saved/RathianLegacyRepair-20261031'
OUT.mkdir(parents=True,exist_ok=True)
pkg=types.ModuleType('rathian_suite');pkg.__path__=[str(ROOT/'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main')];sys.modules[pkg.__name__]=pkg
load_mod3=importlib.import_module(pkg.__name__+'.mod3.mod3_loader').load_mod3
load_lmt=importlib.import_module(pkg.__name__+'.lmt.lmt_loader').load_lmt
manifest=json.loads((BASE/'extraction-manifest.json').read_text(encoding='utf-8'))
records={r['path']:r for r in manifest['files']}
existing=json.loads((ROOT/'Saved/rathian-inventory.json').read_text(encoding='utf-8'))
old={r['path'].split('/')[-1].split('.')[0] for r in existing['assets']}
report=dict(banks=[],exported=[],existing=sorted(old),errors=[],empty=[],status='running')
def save():
    temp=OUT/'export.tmp.json'
    temp.write_text(json.dumps(report,indent=2),encoding='utf-8')
    temp.replace(OUT/'export.json')
mod=BASE/'nativePC/em/em001/00/mod/em001_00.mod3'
for path in sorted((BASE/'nativePC/em/em001/00/mot').rglob('em001_00.lmt')):
    raw=path.read_bytes();rel=path.relative_to(BASE/'nativePC').as_posix()
    assert hashlib.sha256(raw).hexdigest()==records[rel]['sha256']
    count=struct.unpack_from('<H',raw,6)[0]
    offsets=struct.unpack_from('<'+'Q'*count,raw,16) if count else []
    frames={f'{path.stem}_{i:03}':struct.unpack_from('<I',raw,o+12)[0] for i,o in enumerate(offsets) if o}
    bank=dict(path=rel,sha256=records[rel]['sha256'],slots=count,valid=len(frames),frames=frames)
    report['banks'].append(bank)
    if not frames:
        report['empty'].append(rel);save();continue
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for a in list(bpy.data.actions):bpy.data.actions.remove(a)
    objects=load_mod3(str(mod),LOD=0,fix_rotation=True,fix_scale=True,rename_bones=False,connect_bones=False)
    arm=next(o for o in objects if o.type=='ARMATURE');arm.animation_data_create()
    load_lmt(str(path),arm.data,set_fake_user=True)
    actions={a.name:a for a in bpy.data.actions}
    assert set(frames)==set(actions),(path,set(frames)-set(actions))
    for name,source_frames in frames.items():
        if 'A_'+name not in old:continue
        action=actions[name]
        try:
            arm.animation_data.action=None
            for p in arm.pose.bones:
                p.location=(0,0,0);p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
            arm.animation_data.action=action
            scene=bpy.context.scene;scene.render.fps=60;scene.frame_start=0;scene.frame_end=max(1,source_frames-1);scene.frame_set(0)
            bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm
            target=OUT/'FBX'/f'{name}.fbx';target.parent.mkdir(exist_ok=True)
            bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_step=1,bake_anim_simplify_factor=0.0)
            row=dict(name='A_'+name,bank=rel,source_frames=source_frames,expected_seconds=scene.frame_end/60,fbx=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bones=len(arm.data.bones))
            report['exported'].append(row)
            print('EXPORTED',name,source_frames,flush=True)
        except Exception as e:
            report['errors'].append(dict(name=name,error=str(e)))
        save()
    print('BANK_DONE',path.stem,len(frames),flush=True)
report['status']='done';save()
print('COMPLETE',len(report['exported']),'errors',len(report['errors']),flush=True)
