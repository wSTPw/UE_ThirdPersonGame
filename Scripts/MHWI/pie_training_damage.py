"""Trace actual incoming damage; validate passive training and explicit counter practice.

run('diagnose') uses the saved map's current defaults. run('verify') requires
passive saved targets, without silently switching them off as earlier combat tests did.
All actor repositioning and attack opt-in below happen only in the disposable PIE world.
"""
import json
import time
import traceback
from pathlib import Path
import unreal


def run(mode='verify'):
    assert mode in ['diagnose', 'verify']
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not level.is_in_play_in_editor(), 'End the current PIE session first'
    settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
    state = {'phase': 'load', 'wall': time.monotonic(), 'at': time.monotonic(),
             'throttle': settings.get_editor_property('bThrottleCPUWhenNotForeground')}
    settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
    report = {'passed': False, 'mode': mode, 'checks': [], 'damage_events': [], 'moves': []}
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def check(ok, label):
        report['checks'].append({'check': label, 'passed': bool(ok)})
        if not ok: raise AssertionError(label)

    def phase(name): state.update(phase=name, at=time.monotonic())

    def hp(): return state['attrs'].get_current_health()

    def received(amount, source):
        report['damage_events'].append({'amount': amount, 'source': source.get_path_name() if source else None,
            'self': source == state['pawn'], 'phase': state['phase'],
            'move': str(state['pawn'].get_current_move()), 'hp': hp(),
            'world_seconds': unreal.GameplayStatics.get_time_seconds(state['world'])})

    def align():
        p = state['pawn']; loc = p.get_actor_location()
        state['target'].set_actor_location(loc+p.get_actor_forward_vector()*150+unreal.Vector(0,0,-4), False, False)

    def finish(error=None):
        report['passed'] = error is None
        if error: report['error'] = error; unreal.log_error(error)
        if 'attrs' in state:
            state['attrs'].get_editor_property('on_damaged').remove_callable(received)
            report['final_player_hp'] = hp()
        settings.set_editor_property('bThrottleCPUWhenNotForeground', state['throttle'])
        Path(unreal.Paths.project_saved_dir(),f'MHWIImport/PIE-training-damage-{mode}.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        unreal.unregister_slate_post_tick_callback(state['handle'])
        if level.is_in_play_in_editor(): level.editor_request_end_play()
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)

    def tick(dt):
        try:
            if time.monotonic()-state['wall'] > 75: raise TimeoutError(state['phase'])
            stage = state['phase']; elapsed = time.monotonic()-state['at']
            if stage == 'load':
                check(level.load_level('/Game/MHWI/Maps/L_MHWI_Training'), 'training map loads from saved defaults'); phase('start')
            elif stage == 'start': level.editor_request_begin_play(); phase('wait')
            elif stage == 'wait':
                world = editor.get_game_world()
                p = unreal.GameplayStatics.get_player_character(world,0) if world else None
                if not p: return
                targets = list(unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MHWITrainingTarget))
                check(len(targets)==3, 'three saved training targets spawn')
                state.update(world=world,pawn=p,attrs=p.get_editor_property('attributes'))
                state['target'] = next((t for t in targets if t.get_editor_property('enable_attacks')),targets[0])
                state['target_attrs'] = state['target'].get_editor_property('attributes')
                report['saved_targets'] = [{'actor':t.get_name(),'attacks':t.get_editor_property('enable_attacks')} for t in targets]
                p.disable_input(unreal.GameplayStatics.get_player_controller(world,0))
                p.set_actor_location(unreal.Vector(0,0,94.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
                state['attrs'].get_editor_property('on_damaged').add_callable(received)
                check(hp()==100, 'fresh player starts at full health')
                align()
                if mode=='diagnose':
                    check(any(t.get_editor_property('enable_attacks') for t in targets), 'current map has an auto-attacking target')
                    phase('observe_source')
                else:
                    check(all(not t.get_editor_property('enable_attacks') for t in targets), 'saved defaults are passive; test does not override them')
                    phase('idle_safe')
            elif stage=='observe_source':
                align()
                if report['damage_events']:
                    event=report['damage_events'][0]
                    check(event['source']==state['target'].get_path_name(), 'incoming damage identifies the training target as source')
                    check(not event['self'] and event['move']=='None', 'damage occurs while idle without any self attack')
                    check(event['amount']==12 and hp()==88, 'target periodic hit matches reported 12 HP loss')
                    finish()
            elif stage=='idle_safe':
                align()
                if elapsed>5.0:
                    check(hp()==100 and not report['damage_events'], 'standing inside attack range over 4 seconds does not lose HP')
                    state.update(index=0,started=False,hp_before=state['target_attrs'].get_current_health())
                    state['sequence']=['DrawSlash','OverheadSlash','Thrust','RisingSlash','StepSlash','OverheadSlash',
                                       'SpiritI','SpiritII','SpiritIII','SpiritRoundslash']
                    phase('attacks_safe')
            elif stage=='attacks_safe':
                align();p=state['pawn']
                if not state.get('checked_'+str(state['index'])):
                    check(hp()==100 and not report['damage_events'], 'player HP stays full during '+state['sequence'][state['index']])
                state['checked_'+str(state['index'])]=True
                if not state['started']:
                    name=state['sequence'][state['index']]
                    check(p.start_move(name), name+' starts with normal authored costs')
                    report['moves'].append(name);state['started']=True
                elif p.get_current_move().is_none():
                    state['index']+=1;state['started']=False
                    if state['index']==len(state['sequence']):
                        check(hp()==100 and not report['damage_events'], 'normal and spirit attacks never damage their owner')
                        damage=state['hp_before']-state['target_attrs'].get_current_health();report['target_damage']=damage
                        check(abs(damage-268)<.1, 'training target receives all configured normal and spirit hits')
                        check(p.get_spirit_level()==1, 'roundslash remains effective')
                        state['target'].set_editor_property('enable_attacks',True)
                        state['target'].set_editor_property('attack_interval',1.0)
                        state['target'].reset_target();phase('explicit_target_damage')
            elif stage=='explicit_target_damage':
                align()
                if report['damage_events']:
                    event=report['damage_events'][0]
                    check(event['source']==state['target'].get_path_name() and not event['self'], 'explicitly enabled target is recorded as external damage source')
                    check(hp()==88, 'normal incoming damage still deducts exactly 12 HP')
                    state['target'].reset_target();state['counter_requested']=False;phase('counter')
            elif stage=='counter':
                align();p=state['pawn']
                if not state['counter_requested'] and elapsed>.65:
                    check(p.start_move('ForesightSlash'), 'foresight starts for opt-in counter practice')
                    state['counter_requested']=True
                if state['counter_requested'] and p.get_spirit_gauge()>99:
                    check(hp()==88 and len(report['damage_events'])==1, 'real target hit inside foresight window is intercepted')
                    check('Counter successful' in p.get_move_status(), 'counter confirms and fills spirit gauge')
                    finish()
        except Exception: finish(traceback.format_exc())
    state['handle']=unreal.register_slate_post_tick_callback(tick)
    return {'started':mode,'result_file':f'Saved/MHWIImport/PIE-training-damage-{mode}.json'}
