"""Additional real Enhanced Input movement, sprint, stance-roll and side-fade checks."""
import unreal,json,time,traceback
from pathlib import Path
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
state=dict(phase='load',at=time.monotonic(),wall=time.monotonic(),throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground'))
settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
report=dict(passed=False,checks=[])
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
def check(v,label):
 report['checks'].append(dict(check=label,passed=bool(v)))
 if not v: raise AssertionError(label)
def phase(p): state.update(phase=p,at=time.monotonic())
def current(): return str(state['player'].get_current_move())
def idle(): return state['player'].get_current_move().is_none()
def inject(name,xyz):
 state['subsystem'].inject_input_vector_for_action(state['actions'][name],unreal.Vector(*xyz),[],[])
def finish(error=None):
 report['passed']=error is None
 if error: report['error']=error;unreal.log_error(error)
 Path(unreal.Paths.project_saved_dir(),'MHWIImport/PIE-edges.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 settings.set_editor_property('bThrottleCPUWhenNotForeground',state['throttle'])
 unreal.unregister_slate_post_tick_callback(handle)
 level.editor_request_end_play()
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(delta):
 try:
  elapsed=time.monotonic()-state['at'];p=state['phase']
  if time.monotonic()-state['wall']>75: raise TimeoutError(p)
  if p=='load':
   check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'),'training map loads');phase('start')
  elif p=='start': level.editor_request_begin_play();phase('wait')
  elif p=='wait':
   w=editor.get_game_world();player=unreal.GameplayStatics.get_player_character(w,0) if w else None
   if not player:return
   for t in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.MHWITrainingTarget): t.set_editor_property('enable_attacks',False)
   contexts=[o for o in unreal.ObjectIterator(unreal.InputMappingContext) if o.get_outer()==player]
   subs=[]
   for sub in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem):
    present=sub.has_mapping_context(contexts[0])
    if present[0] if isinstance(present,tuple) else present: subs.append(sub)
   state.update(player=player,subsystem=subs[0],actions={o.get_name():o for o in unreal.ObjectIterator(unreal.InputAction) if o.get_outer()==player},origin=player.get_actor_location())
   unreal.GameplayStatics.get_player_controller(w,0).set_control_rotation(unreal.Rotator())
   phase('sprint')
  elif p=='sprint':
   inject('MHWI_Move',(0,1,0));inject('MHWI_Sprint',(1,0,0))
   if elapsed>1:
    travel=(state['player'].get_actor_location()-state['origin']).length()
    check(travel>300,'Enhanced Input move and sprint advance capsule over 300 cm')
    check(state['player'].is_sprinting(),'sprint binding enters running stance')
    report['sprint_travel_cm']=travel
    inject('MHWI_Move',(0,0,0));inject('MHWI_Sprint',(0,0,0));phase('release')
  elif p=='release' and elapsed>.25:
   check(not state['player'].is_sprinting(),'released sprint binding clears running stance')
   check(state['player'].request_input(unreal.MHWIInput.EVADE),'sheathed evade starts')
   check(state['player'].mesh.get_anim_instance().get_current_active_montage().get_name()=='M_RollSheathed','sheathed evade selects common root-motion roll')
   phase('roll')
  elif p=='roll' and idle():
   state['player'].set_actor_location(unreal.Vector(0,0,94.15),False,True)
   check(state['player'].request_input(unreal.MHWIInput.TOGGLE_SHEATHE),'draw request accepted');phase('draw')
  elif p=='draw' and idle():
   check(not state['player'].is_sheathed(),'drawn stance reached')
   inject('MHWI_Move',(-1,0,0));phase('left_input')
  elif p=='left_input':
   check(state['player'].request_input(unreal.MHWIInput.FADE_SLASH),'left fade request accepted')
   check(current()=='FadeSlashLeft','left movement modifier selects left fade')
   inject('MHWI_Move',(0,0,0));phase('left')
  elif p=='left' and idle():
   inject('MHWI_Move',(1,0,0));phase('right_input')
  elif p=='right_input':
   check(state['player'].request_input(unreal.MHWIInput.FADE_SLASH),'right fade request accepted')
   check(current()=='FadeSlashRight','right movement modifier selects right fade')
   inject('MHWI_Move',(0,0,0));phase('right')
  elif p=='right' and idle():
   check(not state['player'].request_input(unreal.MHWIInput.SPECIAL_SHEATHE),'neutral special sheathe rejected')
   check(state['player'].start_move('OverheadSlash'),'attack for special sheath starts');phase('special_prepare')
  elif p=='special_prepare' and elapsed>1.06:
   check(state['player'].request_input(unreal.MHWIInput.SPECIAL_SHEATHE),'special sheathe buffers from attack');phase('special_wait')
  elif p=='special_wait' and state['player'].is_special_sheath_holding(): phase('hold_expiry')
  elif p=='hold_expiry' and idle():
   check(state['player'].is_sheathed(),'special sheath timeout retains sheathed stance')
   check(not state['player'].is_special_sheath_holding(),'special sheath timeout releases hold')
   check(state['player'].request_input(unreal.MHWIInput.LIGHT),'input works after hold timeout')
   state['player'].interrupt_move()
   check(idle(),'explicit interrupt releases new foreground action');finish()
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
