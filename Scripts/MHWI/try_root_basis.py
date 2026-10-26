import unreal
seq=unreal.load_asset('/Game/MHWI/Animations/LongSword/A_w03_00_001')
seq.set_editor_property('root_motion_root_lock',unreal.RootMotionRootLock.REF_POSE)
