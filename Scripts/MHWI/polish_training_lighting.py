"""Improve readability in the independent training map, without touching gameplay."""
import unreal
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if level.is_in_play_in_editor(): level.editor_request_end_play()
def apply(delta):
 if level.is_in_play_in_editor(): return
 unreal.unregister_slate_post_tick_callback(handle)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for actor in actors.get_all_level_actors():
  if isinstance(actor,unreal.SkyLight):
   actor.light_component.set_editor_property('real_time_capture',True)
   actor.light_component.set_editor_property('intensity',2.5)
 existing=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=='MHWI_FillLight'),None)
 fill=existing or actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,500),unreal.Rotator(pitch=-35,yaw=145))
 fill.set_actor_label('MHWI_FillLight')
 fill.light_component.set_editor_property('intensity',3.0)
 fill.light_component.set_editor_property('light_color',unreal.Color(205,220,255,255))
 fill.light_component.set_editor_property('cast_shadows',False)
 fill.light_component.set_editor_property('atmosphere_sun_light',False)
 assert level.save_current_level()
 unreal.log('MHWI_LIGHTING_SAVED')
handle=unreal.register_slate_post_tick_callback(apply)
