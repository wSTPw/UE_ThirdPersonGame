"""Read persisted assets after a full editor restart; no asset writes."""
import unreal,json
from pathlib import Path
root='/Game/MHWI'
checks=[]
def check(v,label):
 checks.append(dict(check=label,passed=bool(v)))
 if not v: raise AssertionError(label)
result=dict(passed=False,checks=checks)
try:
 slots=0
 for leaf in ['Character/SK_MHWI_Hunter','Weapons/SK_MHWI_LongSword','Weapons/SK_MHWI_Scabbard']:
  mesh=unreal.load_asset(root+'/'+leaf)
  mats=mesh.get_editor_property('materials')
  check(all(s.get_editor_property('material_interface') for s in mats),leaf+' material slots persist')
  slots+=len(mats)
 result['slots']=slots
 lib=unreal.AnimPoseExtensions
 for leaf in ['LongSword/A_w03_00_001','Common/A_co00_00_001']:
  seq=unreal.load_asset(root+'/Animations/'+leaf)
  check(seq.get_editor_property('root_motion_root_lock')==unreal.RootMotionRootLock.REF_POSE,leaf+' root basis persists')
  pose=lib.get_anim_pose_at_time(seq,0,unreal.AnimPoseEvaluationOptions(extract_root_motion=True, incorporate_root_motion_into_pose=False))
  head=lib.get_bone_pose(pose,'bone_003',unreal.AnimPoseSpaces.WORLD).translation
  foot=lib.get_bone_pose(pose,'bone_017',unreal.AnimPoseSpaces.WORLD).translation
  check(head.z>foot.z+60,leaf+' head above foot in locked runtime pose')
 for leaf in ['Blueprints/BP_MHWI_Hunter','Blueprints/ABP_MHWI_Hunter','Blueprints/BP_MHWI_TrainingGameMode']:
  bp=unreal.load_asset(root+'/'+leaf)
  check(bool(bp.generated_class()),leaf+' generated class persists')
 result['passed']=True
except Exception as e: result['error']=str(e)
Path(unreal.Paths.project_saved_dir(),'MHWIImport/asset-persistence.json').write_text(json.dumps(result,indent=2),encoding='utf8')
assert result['passed'],result

