"""Fresh PIE regression for persisted MHWI attachment fit and stance hand-offs."""
import unreal,json,time,traceback
from pathlib import Path
OUT=Path(unreal.Paths.project_saved_dir())/'MHWIImport'
FIT=json.loads((Path(unreal.Paths.project_dir())/'Scripts/MHWI/attachment_fit.json').read_text(encoding='utf8'))
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
state={'phase':'load','at':time.monotonic(),'wall':time.monotonic(),'throttle':settings.get_editor_property('bThrottleCPUWhenNotForeground')}
settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
report={'passed':False,'checks':[],'measurements':{}}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
def check(v,label):
 report['checks'].append(dict(check=label,passed=bool(v)))
 if not v: raise AssertionError(label)
def phase(p):state.update(phase=p,at=time.monotonic(),frames=0)
def p():return state['player']
def idle():return p().get_current_move().is_none()
def comp(n):return p().get_editor_property(n)
def world_transform(c):return c.get_socket_transform(unreal.Name())
def socket(n):return str(comp(n).get_attach_socket_name())
def overlap(label):
 a=world_transform(comp('weapon_mesh'));b=world_transform(comp('scabbard_mesh'))
 check((a.translation-b.translation).length()<.01,label+' sword and sheath origins coincide')
 check(abs(a.rotation.x*b.rotation.x+a.rotation.y*b.rotation.y+a.rotation.z*b.rotation.z+a.rotation.w*b.rotation.w)>.99999,label+' sword and sheath axes coincide')
def finish(error=None):
 report['passed']=error is None
 if error:report['error']=error;unreal.log_error(error)
 else:
  report['review_pawn_xyz']=list(p().get_actor_location().to_tuple())
  unreal.GameplayStatics.set_game_paused(state['world'],True)
 settings.set_editor_property('bThrottleCPUWhenNotForeground',state['throttle'])
 (OUT/'PIE-attachments.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 unreal.unregister_slate_post_tick_callback(handle)
 if error:level.editor_request_end_play()
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
 try:
  stage=state['phase'];elapsed=time.monotonic()-state['at']
  if time.monotonic()-state['wall']>65:raise TimeoutError(stage)
  if stage=='load':
   check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'),'training map loads');phase('start')
  elif stage=='start':level.editor_request_begin_play();phase('wait')
  elif stage=='wait':
   w=editor.get_game_world();player=unreal.GameplayStatics.get_player_character(w,0) if w else None
   if not player:return
   state.update(world=w,player=player)
   for target in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.MHWITrainingTarget):target.set_editor_property('enable_attacks',False)
   pc=unreal.GameplayStatics.get_player_controller(w,0);player.disable_input(pc)
   for key,v in FIT['bones'].items():check(str(player.get_editor_property(key))==v,key+' persists on fresh pawn')
   for key,v in FIT['transforms'].items():
    t=player.get_editor_property(key);e=unreal.Rotator(pitch=v['rotation'][0],yaw=v['rotation'][1],roll=v['rotation'][2]).quaternion()
    check((t.translation-unreal.Vector(*v['location'])).length()<.01,key+' position persists')
    check(abs(t.rotation.x*e.x+t.rotation.y*e.y+t.rotation.z*e.z+t.rotation.w*e.w)>.99999,key+' rotation persists')
    check((t.scale3d-unreal.Vector(.7,.7,.7)).length()<.001,key+' shared scale persists')
   check(socket('weapon_mesh')=='bone_002' and socket('scabbard_mesh')=='bone_002','fresh sheathed pawn mounts both to upper spine')
   overlap('initial sheath');check(player.start_move('Draw'),'draw starts');phase('draw')
  elif stage=='draw' and idle():
   check(socket('weapon_mesh')=='bone_012','drawn sword mounts to right wrist')
   check(socket('scabbard_mesh')=='bone_002','drawn sheath remains on upper spine')
   palm=p().mesh.get_socket_transform('bone_012').transform_location(unreal.Vector(-7,2,0))
   grip=world_transform(comp('weapon_mesh')).transform_location(unreal.Vector(0,-12,0))
   error=(palm-grip).length();report['measurements']['drawn_grip_error_cm']=error
   check(error<.1,'drawn hilt grip aligns to right palm')
   t=world_transform(comp('weapon_mesh'));axis=(t.transform_location(unreal.Vector(0,1,0))-t.translation).normal()
   check(axis.dot(p().get_actor_forward_vector())>.2,'drawn blade extends outward rather than into body')
   check(p().start_move('OverheadSlash'),'normal attack starts with fitted weapon');phase('attack')
  elif stage=='attack':
   m=p().mesh.get_anim_instance().get_current_active_montage()
   if m and p().mesh.get_anim_instance().montage_get_position(m)>=1.06:
    check(p().request_input(unreal.MHWIInput.SPECIAL_SHEATHE),'attack routes to special sheath');phase('special')
  elif stage=='special' and p().is_special_sheath_holding():
   state['frames']+=1
   if state['frames']<3:return
   check(socket('weapon_mesh')=='bone_008' and socket('scabbard_mesh')=='bone_008','special sheath mounts both to left wrist')
   overlap('special sheath')
   left=p().mesh.get_socket_transform('bone_008').transform_location(unreal.Vector(-7,2,0))
   right=p().mesh.get_socket_transform('bone_012').transform_location(unreal.Vector(-7,2,0))
   t=world_transform(comp('weapon_mesh'));mouth=t.transform_location(unreal.Vector(0,21,0));grip=t.transform_location(unreal.Vector(0,FIT['special_fit']['hilt_grip_source_y'],0))
   errors={'special_mouth_error_cm':(left-mouth).length(),'special_hilt_error_cm':(right-grip).length()}
   report['measurements'].update(errors)
   check(errors['special_mouth_error_cm']<.2,'special sheath mouth aligns to left palm')
   check(errors['special_hilt_error_cm']<1.5,'special hilt grip aligns to right palm')
   check(p().request_input(unreal.MHWIInput.LIGHT),'Iai slash starts from fitted hold')
   check(socket('weapon_mesh')=='bone_012','Iai transfers sword back to right wrist')
   check(socket('scabbard_mesh')=='bone_008','Iai retains sheath in left hand');phase('iai')
  elif stage=='iai' and idle():
   check(socket('scabbard_mesh')=='bone_002','Iai completion restores back sheath')
   check(p().start_move('Sheathe'),'normal sheathe starts');phase('sheath')
  elif stage=='sheath' and idle():
   check(p().is_sheathed(),'normal sheath finishes')
   check(socket('weapon_mesh')=='bone_002' and socket('scabbard_mesh')=='bone_002','normal sheath restores matching back mounts');overlap('final sheath')
   check(p().start_move('SpecialSheathe'),'special sheath can reenter for visual review');phase('review')
  elif stage=='review' and p().is_special_sheath_holding():
   state['frames']+=1
   if state['frames']>=3:finish()
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
