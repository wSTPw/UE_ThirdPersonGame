"""Runtime-only attachment preview. Camera captures must share a paused pose."""
import json,time
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/MHWIImport'
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
def pawn():return unreal.GameplayStatics.get_player_character(editor.get_game_world(),0)
def transform(v):
 return unreal.Transform(location=unreal.Vector(*v['location']),rotation=unreal.Rotator(pitch=v['rotation'][0],yaw=v['rotation'][1],roll=v['rotation'][2]),scale=unreal.Vector(*v.get('scale',[1,1,1])))
def apply():
 p=pawn();d=json.loads((ROOT/'Scripts/MHWI/attachment_fit.json').read_text(encoding='utf8'))
 for key,v in d['bones'].items():p.set_editor_property(key,unreal.Name(v))
 for key,v in d['transforms'].items():p.set_editor_property(key,transform(v))
 special=p.is_special_sheath_holding()
 for comp_name,bone_key,trans_key in [('weapon_mesh','special_scabbard_bone' if special else ('sheathed_weapon_bone' if p.is_sheathed() else 'weapon_bone'),'special_weapon_relative_transform' if special else ('sheathed_weapon_relative_transform' if p.is_sheathed() else 'weapon_relative_transform')),('scabbard_mesh','special_scabbard_bone' if special else 'scabbard_bone','special_scabbard_relative_transform' if special else 'scabbard_relative_transform')]:
  c=p.get_editor_property(comp_name)
  assert c.attach_to_component(p.mesh,d['bones'][bone_key],unreal.AttachmentRule.SNAP_TO_TARGET,unreal.AttachmentRule.SNAP_TO_TARGET,unreal.AttachmentRule.SNAP_TO_TARGET,False)
  c.set_relative_transform(transform(d['transforms'][trans_key]),False,True)
 dump()
def dump():
 p=pawn();r={'actor':str(p.get_actor_transform()),'xyz':list(p.get_actor_location().to_tuple()),'move':str(p.get_current_move()),'sheathed':p.is_sheathed(),'hold':p.is_special_sheath_holding(),'bones':{},'components':{}}
 for n in ['bone_002','bone_008','bone_012']:
  t=p.mesh.get_socket_transform(n);r['bones'][n]={'xyz':list(t.translation.to_tuple()),'transform':str(t)}
 for n in ['weapon_mesh','scabbard_mesh']:
  c=p.get_editor_property(n);t=c.get_socket_transform(unreal.Name());r['components'][n]={'transform':str(t),'socket':str(c.get_attach_socket_name()),'points':{str(v):list(t.transform_location(unreal.Vector(*v)).to_tuple()) for v in [(0,0,0),(0,21,0),(0,-60,0),(0,240,0)]}}
 (OUT/'attachment-preview.json').write_text(json.dumps(r,indent=2),encoding='utf8')
def pose(name):
 w=editor.get_game_world();unreal.GameplayStatics.set_game_paused(w,False);p=pawn()
 p.set_editor_property('custom_time_dilation',1.0);p.mesh.set_editor_property('global_anim_rate_scale',1.0);p.interrupt_move()
 p.set_actor_location(unreal.Vector(0,0,94.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
 assert p.start_move(name)
 state={'at':time.monotonic(),'settle':0}
 def tick(dt):
  ready=p.is_special_sheath_holding() if name=='SpecialSheathe' else p.get_current_move().is_none()
  if ready:
   state['settle']+=1
   if state['settle']>=3:
    unreal.GameplayStatics.set_game_paused(w,True);unreal.unregister_slate_post_tick_callback(state['handle']);apply();unreal.log('MHWI_ATTACHMENT_POSE '+name)
  elif time.monotonic()-state['at']>12:
   unreal.unregister_slate_post_tick_callback(state['handle']);unreal.log_error('attachment pose timeout '+name)
 state['handle']=unreal.register_slate_post_tick_callback(tick)
def drawn():pose('Draw')
def sheathed():pose('Sheathe')
def special():pose('SpecialSheathe')
