import unreal,json
from pathlib import Path
r={}
for path in ['/Game/MHWI/Character/SK_MHWI_Hunter','/Game/MHWI/Weapons/SK_MHWI_LongSword']:
 m=unreal.load_asset(path)
 r[path]=[str(s) for s in m.get_editor_property('materials')]
seq=unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_001')
r['seq']=str(seq.get_editor_property('root_motion_root_lock'))
r['pose_lib']=str(unreal.AnimPoseExtensions.__doc__)
r['pose_methods']=[s for s in dir(unreal.AnimPoseExtensions) if 'pose' in s]
Path(unreal.Paths.project_saved_dir(),'MHWIImport/asset-inspect.json').write_text(json.dumps(r,indent=2),encoding='utf8')
