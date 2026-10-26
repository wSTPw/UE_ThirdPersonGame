"""Save in editor mode; leave a user-started PIE session running."""
import unreal
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if level.is_in_play_in_editor():
    unreal.log('MHWI fit was saved before PIE regression; leave the active user session running.')
else:
    bp=unreal.load_asset('/Game/MHWI/Blueprints/BP_MHWI_Hunter')
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
    settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
    settings.set_editor_property('bThrottleCPUWhenNotForeground',True)
    unreal.log('MHWI_ATTACHMENT_FIX_SAVED_EDITOR_IDLE')
