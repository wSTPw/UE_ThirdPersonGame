import unreal,json
from pathlib import Path
seq=unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_001')
r={name:str(getattr(unreal.AnimPoseExtensions,name).__doc__) for name in ['get_anim_pose_at_time','get_reference_pose','get_bone_pose']}
r['options']=str(unreal.AnimPoseEvaluationOptions.__doc__)
Path(unreal.Paths.project_saved_dir(),'MHWIImport/pose-api.json').write_text(json.dumps(r,indent=2),encoding='utf8')
