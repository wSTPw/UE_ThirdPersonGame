import unreal,json
from pathlib import Path
s=unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_306');lib=unreal.AnimPoseExtensions
r=[]
for f in [0,30,60,73,90,120,150,180,210,240,270]:
 pose=lib.get_anim_pose_at_time(s,f/60,unreal.AnimPoseEvaluationOptions(extract_root_motion=True,incorporate_root_motion_into_pose=False))
 r.append({'frame':f,'bones':{n:list(lib.get_bone_pose(pose,n,unreal.AnimPoseSpaces.WORLD).translation.to_tuple()) for n in ['bone_008','bone_012','bone_003']}})
Path(unreal.Paths.project_saved_dir(),'MHWIImport/special-pose-frames.json').write_text(json.dumps(r,indent=2),encoding='utf8')
