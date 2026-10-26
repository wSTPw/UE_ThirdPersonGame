import unreal,json
from pathlib import Path
r={}
seq=unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_001')
lib=unreal.AnimPoseExtensions
poses={'ref':lib.get_reference_pose(seq.get_editor_property('skeleton'))}
for ext in [False,True]:
 opt=unreal.AnimPoseEvaluationOptions(extract_root_motion=ext,incorporate_root_motion_into_pose=not ext)
 poses['anim_'+str(ext)]=lib.get_anim_pose_at_time(seq,0,opt)
for k,pose in poses.items():
 r[k]={n:str(lib.get_bone_pose(pose,n,unreal.AnimPoseSpaces.WORLD)) for n in ['bone_root','bone_000','bone_003','bone_017']}
Path(unreal.Paths.project_saved_dir(),'MHWIImport/pose-raw.json').write_text(json.dumps(r,indent=2),encoding='utf8')
