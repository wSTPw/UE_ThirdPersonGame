"""Read focused sequences' evaluated poses and settings, no asset writes."""
import unreal,json
from pathlib import Path
lib=unreal.AnimPoseExtensions;report={}
for leaf in ['Common/A_co00_00_001','Common/A_co00_00_034','Common/A_co00_00_035','Common/A_co00_00_037','LongSword/A_w03_00_104','LongSword/A_w03_00_107','LongSword/A_w03_00_105','LongSword/A_w03_00_102']:
 s=unreal.load_asset('/Game/MHWI/Animations/'+leaf)
 frames=[]
 for time in [0,s.get_play_length()*.25,s.get_play_length()*.5]:
  pose=lib.get_anim_pose_at_time(s,time,unreal.AnimPoseEvaluationOptions(extract_root_motion=True,incorporate_root_motion_into_pose=False))
  frames.append({'t':time,'bones':{n:str(lib.get_bone_pose(pose,n,unreal.AnimPoseSpaces.WORLD)) for n in ['bone_root','bone_000','bone_008','bone_012']}})
 report[leaf]={'length':s.get_play_length(),'root_lock':str(s.get_editor_property('root_motion_root_lock')),'frames':frames}
Path(unreal.Paths.project_saved_dir(),'MHWIImport/animation-review-before.json').write_text(json.dumps(report,indent=2),encoding='utf8')
