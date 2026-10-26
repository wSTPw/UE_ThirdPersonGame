import unreal,json
from pathlib import Path
root='/Game/MHWI'
fixed=[]
for path in unreal.EditorAssetLibrary.list_assets(root+'/Animations',recursive=True,include_folder=False):
 obj=unreal.load_asset(path)
 if isinstance(obj,unreal.AnimSequence):
  obj.set_editor_property('root_motion_root_lock',unreal.RootMotionRootLock.REF_POSE)
  unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False)
  fixed.append(path)
# SkeletalMaterial wrappers may mutate in place without marking their owner dirty.
# The material author forces mesh saves; assert the complete slot readback here.
slots=[]
for leaf in ['Character/SK_MHWI_Hunter','Weapons/SK_MHWI_LongSword','Weapons/SK_MHWI_Scabbard']:
 mesh=unreal.load_asset(root+'/'+leaf)
 mats=mesh.get_editor_property('materials')
 assert all(s.get_editor_property('material_interface') for s in mats),leaf+' has null material'
 slots.extend([str(s.get_editor_property('material_interface').get_path_name()) for s in mats])
unreal.EditorAssetLibrary.save_directory(root,only_if_is_dirty=True,recursive=True)
Path(unreal.Paths.project_saved_dir(),'MHWIImport/basis-material-fix.json').write_text(json.dumps(dict(root_lock='REF_POSE',sequences=len(fixed),materials=slots),indent=2),encoding='utf8')
