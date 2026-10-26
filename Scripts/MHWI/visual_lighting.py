import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
for light in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.SkyLight):
 light.light_component.set_editor_property('real_time_capture',True)
 light.light_component.set_editor_property('intensity',3.0)
 light.light_component.recapture_sky()
# Soft counterpart to the key light keeps the hunter's front legible from both sides.
transform=unreal.Transform(location=unreal.Vector(0,0,500),rotation=unreal.Rotator(pitch=-35,yaw=140))
light=unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(w,unreal.DirectionalLight,transform,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN)
unreal.GameplayStatics.finish_spawning_actor(light,transform)
light.light_component.set_editor_property('intensity',3.0)
light.light_component.set_editor_property('light_color',unreal.Color(195,215,255,255))

