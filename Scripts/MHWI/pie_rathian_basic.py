"""Actual Basic Rathian PIE evidence; transient instances only, no asset writes."""
import unreal,json,time,math,traceback,datetime,sys
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/"Saved/RathianBasic-Assets-20261107"
sys.path.insert(0,str(ROOT/"Scripts/MHWI"))
import author_rathian_basic as author
_ACTIVE=None
def v(p): return [float(p.x),float(p.y),float(p.z)]
def world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
def monster():
    found=unreal.GameplayStatics.get_all_actors_of_class(world(),unreal.MHWIRathianApproxPawn)
    if len(found)!=1: raise RuntimeError("Need exactly one production Rathian")
    return found[0]
class Case:
    def __init__(self,name,target_path):
        self.name=name;self.w=world();
        if not self.w or "/Game/MHWI/Rathian/Basic/Maps/UEDPIE_" not in self.w.get_path_name(): raise RuntimeError("Only dedicated Basic PIE is allowed")
        self.r=monster();self.body=self.r.get_editor_property("body");self.target=unreal.find_object(None,target_path) if target_path else unreal.GameplayStatics.get_player_pawn(self.w,0)
        if not self.target: raise RuntimeError("Target missing")
        self.stance_was_sheathed=self.target.is_sheathed() if isinstance(self.target,unreal.MHWICharacter) else None
        self.a=self.target.get_component_by_class(unreal.AttributeComponent)
        self.report={"case":name,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"world":self.w.get_path_name(),"passed":False,"done":False,"checks":[],"samples":[],"events":[]}
        self.maxz=142.;self.landing=False;self.projectiles=set();self.peak_vz=0.;self.peak_xy=0.;self.wall_start=time.monotonic();self.start=unreal.GameplayStatics.get_time_seconds(self.w);self.last_sample=-1.;self.old_debug=unreal.SystemLibrary.get_console_variable_int_value("mhwi.RathianApprox.DebugBoxes");self.old_fps=unreal.SystemLibrary.get_console_variable_float_value("t.MaxFPS");self.done=False;self.changed=False;self.handle=None
    def check(self,ok,description,**data): self.report["checks"].append({"passed":bool(ok),"description":description,**data})
    def begin(self):
        if self.r.get_health_percent()<=0: raise RuntimeError("Need fresh PIE for dead Rathian")
        if self.r.get_current_attack_name(): raise RuntimeError("Wait for current attack before controlled case")
        self.r.set_actor_tick_enabled(False)
        self.r.set_actor_location(unreal.Vector(0,0,142),False,True);self.r.set_actor_rotation(unreal.Rotator(yaw=0),True)
        p=unreal.GameplayStatics.get_player_pawn(self.w,0)
        if self.target!=p: p.set_actor_location(unreal.Vector(-8000,5000,94.15),False,True)
        x=400. if self.name.startswith("bite") else (1000. if self.name.startswith("charge") else (1200. if self.name.startswith("fire") else 450.))
        if self.name=="bite_miss": x=1800.
        self.target.set_actor_location(unreal.Vector(x,0,94.15 if isinstance(self.target,unreal.Character) else 90.),False,True)
        self.a.set_health(self.a.get_max_health())
        self.hp=float(self.a.get_current_health())
        self.r.set_combat_target(self.target)
        name="ACTION::BITE" if self.name.startswith("bite") else ("ACTION::DASH_BITE2" if self.name.startswith("charge") else ("ACTION::FIRE_BREATH" if self.name.startswith("fire") else "ACTION::ROLLING_TAIL_ATTACK2_L"))
        self.check(self.r.request_basic_attack(name),"production RequestBasicAttack accepted",attack=name)
        self.run=self.r.get_attack_run_id();self.maxz=142.;self.landing=False;self.projectiles=set();self.changed=False;self.forced=False
        unreal.SystemLibrary.execute_console_command(self.w,"mhwi.RathianApprox.DebugBoxes 1")
        self.target_initial=v(self.target.get_actor_location())
        if self.name=="bite_lowfps": unreal.SystemLibrary.execute_console_command(self.w,"t.MaxFPS 5")
        self.r.set_actor_tick_enabled(True)
        unreal.EditorPythonScripting.set_keep_python_script_alive(True)
        self.handle=unreal.register_slate_post_tick_callback(self.tick)
        return str(OUT/("PIE-"+self.name+".json"))
    def sample(self,elapsed):
        r=self.r;b=self.body
        if hasattr(self,"last_tick_elapsed") and elapsed-self.last_tick_elapsed>.0001:self.report.setdefault("game_tick_deltas",[]).append(elapsed-self.last_tick_elapsed)
        self.last_tick_elapsed=elapsed
        hp=float(self.a.get_current_health()) if unreal.SystemLibrary.is_valid(self.a) else -1
        if hp!=getattr(self,"last_hp",self.hp): self.report["events"].append({"t":elapsed,"hp_before":getattr(self,"last_hp",self.hp),"hp_after":hp})
        velocity=self.target.get_velocity() if unreal.SystemLibrary.is_valid(self.target) else unreal.Vector()
        self.peak_vz=max(self.peak_vz,float(velocity.z));self.peak_xy=max(self.peak_xy,math.hypot(velocity.x,velocity.y))
        self.last_hp=hp
        z=float(r.get_actor_location().z);self.maxz=max(self.maxz,z)
        state=r.get_current_state_name();self.landing=self.landing or state=="Landing"
        projectiles=unreal.GameplayStatics.get_all_actors_of_class(self.w,unreal.MHWIRathianApproxFireball)
        for p in projectiles:self.projectiles.add(p.get_path_name())
        if elapsed-self.last_sample>=.03:
            anim=b.get_anim_instance();montage=anim.get_current_active_montage()
            boxes=[]
            for m in r.get_editor_property("moveset_data").get_editor_property("moves"):
                if m.get_editor_property("registry_name")!=r.get_current_attack_name():continue
                for phase in m.get_editor_property("phases"):
                    if not phase.get_editor_property("attack_window_enabled"):continue
                    for box in phase.get_editor_property("hit_boxes"):
                        t=b.get_socket_transform(box.get_editor_property("bone_name"),unreal.RelativeTransformSpace.RTS_WORLD)
                        off=box.get_editor_property("local_offset_cm");scale=t.scale3d
                        d=author.qvec(t.rotation,[off.x*scale.x,off.y*scale.y,off.z*scale.z])
                        boxes.append({"bone":str(box.get_editor_property("bone_name")),"center":[v(t.translation)[i]+d[i] for i in range(3)]})
            self.report["samples"].append({"t":elapsed,"state":state,"attack":r.get_current_attack_name(),"run":r.get_attack_run_id(),"location":v(r.get_actor_location()),"target_hp":hp,"target_velocity":v(self.target.get_velocity()) if unreal.SystemLibrary.is_valid(self.target) else None,"hip_component":v(b.get_socket_transform("bone_000",unreal.RelativeTransformSpace.RTS_COMPONENT).translation),"head":v(b.get_socket_location("bone_003")),"tail":v(b.get_socket_location("bone_146")),"montage":montage.get_name() if montage else None,"montage_position":anim.montage_get_position(montage) if montage else None,"configured_boxes":boxes,"player_control":str(self.target.get_control_state()) if isinstance(self.target,unreal.MHWICharacter) else None,"player_native":self.target.get_native_playback_diagnostic() if isinstance(self.target,unreal.MHWICharacter) else None,"projectiles":len(projectiles)})
            self.last_sample=elapsed
        return state
    def tick(self,delta):
        try:
            elapsed=unreal.GameplayStatics.get_time_seconds(self.w)-self.start
            if time.monotonic()-self.wall_start>35: raise TimeoutError("PIE case wall timeout")
            state=self.sample(elapsed)
            if self.name=="fire_death":
                if elapsed>.8 and not self.changed:
                    self.changed=True;self.r.get_editor_property("attributes").apply_damage(99999.,None)
                if elapsed>1.8:
                    live=unreal.GameplayStatics.get_all_actors_of_class(self.w,unreal.MHWIRathianApproxFireball)
                    self.check(state=="Dead","fireball source death is terminal")
                    self.check(len(self.projectiles)==1 and len(live)==0,"death clears a previously spawned owned projectile",spawned=len(self.projectiles),live=len(live))
                    self.check(abs(self.hp-float(self.a.get_current_health()))<.1,"destroyed fireball cannot damage target after source death")
                    self.finish()
                return
            if self.name in ["tail_loss","tail_death","tail_interrupt"] and elapsed>.65 and not self.changed:
                self.changed=True
                if self.name=="tail_loss":
                    self.r.set_combat_target(None)
                    # The player is kept beyond detection range for this loss case.
                elif self.name=="tail_death":
                    self.r.get_editor_property("attributes").apply_damage(99999.,None)
                    self.r.configure_approx()
                else:self.body.get_anim_instance().montage_stop(.05)
            if self.name=="tail_death":
                if elapsed>3.0:
                    self.check(state=="Dead" and self.r.get_health_percent()==0.,"air death remains terminal after ConfigureApprox")
                    self.check(abs(self.r.get_actor_location().z-142)<5.,"dead airborne actor returned to floor",z=self.r.get_actor_location().z)
                    self.check(not self.r.get_current_attack_name(),"dead attack cancelled")
                    self.finish();return
                return
            if not self.r.get_current_attack_name() and self.r.get_attack_run_id()==self.run and elapsed>.25 and state not in ["Landing","Attack"]:
                # Allow a released projectile to travel after the source animation ends.
                if self.name.startswith("fire") and elapsed<2.8:
                    self.r.set_actor_tick_enabled(False)
                    return
                if self.name.startswith("tail"):
                    if self.name=="tail_blocked":self.check(200.<self.maxz<350.,"ceiling blocked the swept flight root",max_z=self.maxz)
                    else:self.check(self.maxz>700.,"tail takeoff lifted collision root",max_z=self.maxz)
                    self.check(abs(self.r.get_actor_location().z-142)<5.,"tail returns to floor",z=self.r.get_actor_location().z)
                    if self.name not in ["tail_hit","tail_knockback","tail_drawn_knockback"]:self.check(self.landing,"interrupted/lost target used Landing")
                    else:
                        self.check(not self.landing,"normal tail sequence avoids emergency landing fallback")
                        self.check(abs(self.hp-float(self.a.get_current_health())-40.)<.1,"tail active phase damages target exactly once",damage=self.hp-float(self.a.get_current_health()))
                        if self.name.endswith("_knockback"):self.check_player_impact()
                else:
                    loss=self.hp-float(self.a.get_current_health())
                    expected=0 if self.name in ["bite_miss","bite_wall","fire_wall","charge_wall"] else (20 if self.name.startswith("bite") else (35 if self.name.startswith("charge") else 30))
                    self.check(abs(loss-expected)<.1,"exact damage and phase target dedup",damage=loss,expected=expected)
                    if self.name.endswith("_knockback"):self.check_player_impact()
                    if self.name=="bite_lowfps":self.check(max(self.report.get("game_tick_deltas",[0]))>.15,"actual game tick crossed low-frame interval",max_dt=max(self.report.get("game_tick_deltas",[0])))
                    if self.name=="charge_wall":self.check(max(s["location"][0] for s in self.report["samples"])<415.,"collision root stopped before wall")
                    if self.name.startswith("fire"):self.check(len(self.projectiles)==1,"exactly one fireball spawned",count=len(self.projectiles))
                self.finish();return
            if elapsed>9:raise TimeoutError("Attack did not complete: "+state)
        except Exception:self.finish(traceback.format_exc())
    def check_player_impact(self):
        tier="small" if self.name.startswith("bite") else ("medium" if self.name.startswith("fire") else "large")
        samples=[s for s in self.report["samples"] if tier in str(s.get("player_control","")).lower()]
        self.check(bool(samples),"player selected configured "+tier+" reaction",controls=sorted(set(str(s.get("player_control")) for s in self.report["samples"])))
        bodies=[]
        for sample in samples:
            values=dict(v.split("=",1) for v in str(sample.get("player_native","")).split() if "=" in v)
            if "body" in values:bodies.append(values["body"])
        expected=str((70 if self.stance_was_sheathed else 61)+{"small":0,"medium":1,"large":2}[tier])
        self.check(expected in bodies,"actual Hunter reaction motion matches stance and tier",expected_motion=expected,motions=sorted(set(bodies)))
        if tier=="small": self.check(self.peak_vz<40.,"small bite does not launch Hunter upward",peak_vz=self.peak_vz)
        else:
            threshold=400. if self.name.startswith("tail") else (240. if self.name.startswith("charge") else 100.)
            self.check(self.peak_vz>threshold and self.peak_xy>100.,"Hunter physical launch matches move strength",peak_vz=self.peak_vz,peak_xy=self.peak_xy)
    def finish(self,error=None):
        if self.done:return
        self.done=True
        try:
            if unreal.SystemLibrary.is_valid(self.r):self.r.set_actor_tick_enabled(False)
            self.report.update(done=True,error=error,passed=error is None and all(c["passed"] for c in self.report["checks"]),max_z=self.maxz,landing_seen=self.landing,projectile_count=len(self.projectiles),session_cleanup="dedicated PIE end requested; editor assets untouched")
            (OUT/("PIE-"+self.name+".json")).write_text(json.dumps(self.report,indent=2),encoding="utf8")
        finally:
            if self.handle:
                unreal.unregister_slate_post_tick_callback(self.handle);self.handle=None
            if unreal.SystemLibrary.is_valid(self.w):
                unreal.SystemLibrary.execute_console_command(self.w,"mhwi.RathianApprox.DebugBoxes "+str(self.old_debug))
                unreal.SystemLibrary.execute_console_command(self.w,"t.MaxFPS "+str(self.old_fps))
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
            unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def run_case(case_name,target_path=None,wall_path=None):
    global _ACTIVE
    if _ACTIVE and not _ACTIVE.done:raise RuntimeError("Case already running")
    previous=getattr(unreal,"_rathian_basic_case",None)
    if previous and not previous.done: raise RuntimeError("Another Basic case is still running")
    if case_name not in ["bite_hit","bite_miss","bite_wall","bite_lowfps","bite_knockback","fire_knockback","charge_knockback","tail_knockback","bite_drawn_knockback","fire_drawn_knockback","charge_drawn_knockback","tail_drawn_knockback","fire_death","tail_blocked","charge_hit","charge_wall","fire_hit","fire_wall","tail_hit","tail_loss","tail_interrupt","tail_death"]: raise RuntimeError("Unknown Basic case")
    _ACTIVE=Case(case_name,target_path)
    unreal._rathian_basic_case=_ACTIVE
    try:
        if case_name.endswith("_wall") or case_name=="tail_blocked":
            wall=unreal.find_object(None,wall_path) if wall_path else None
            if not wall or not wall.actor_has_tag("UEMCP_TransientVerification"):raise RuntimeError("Need owned transient wall")
            mesh=wall.get_component_by_class(unreal.StaticMeshComponent)
            mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
            cube=unreal.load_asset("/Engine/BasicShapes/Cube")
            mesh.set_static_mesh(cube)
            if mesh.get_editor_property("static_mesh")!=cube:raise RuntimeError("Wall cube assignment failed")
            mesh.set_collision_profile_name("BlockAll")
            wall.set_actor_scale3d(unreal.Vector(15,15,1) if case_name=="tail_blocked" else unreal.Vector(1,10,8))
            x=200. if case_name.startswith("bite") else (700. if case_name.startswith("fire") else 600.)
            wall.set_actor_location(unreal.Vector(0,0,500) if case_name=="tail_blocked" else unreal.Vector(x,0,400),False,True)
            _ACTIVE.report["wall_fixture"]={"path":wall.get_path_name(),"mesh":mesh.get_editor_property("static_mesh").get_path_name(),"profile":str(mesh.get_collision_profile_name()),"object_type":str(mesh.get_collision_object_type()),"location":v(wall.get_actor_location()),"scale":v(wall.get_actor_scale3d())}
        return _ACTIVE.begin()
    except Exception:
        _ACTIVE.finish(traceback.format_exc())
        raise

def cleanup_previous_cases():
    import gc
    removed=0
    for obj in gc.get_objects():
        try:
            typ=type(obj)
            if typ.__name__!="Case" or not hasattr(typ,"tick"):continue
            if Path(typ.tick.__code__.co_filename).resolve()!=Path(__file__).resolve():continue
            if getattr(obj,"handle",None):
                unreal.unregister_slate_post_tick_callback(obj.handle);obj.handle=None;obj.done=True;removed+=1
        except (AttributeError,ReferenceError):continue
    return removed


class BehaviorCase(Case):
    def begin(self):
        self.target.set_actor_location(unreal.Vector(-8000,5000,94.15),False,True)
        self.a.set_max_health(10000.);self.a.set_health(10000.)
        self.hp=10000.;self.run=self.r.get_attack_run_id()
        self.r.set_combat_target(None);self.r.set_actor_location(unreal.Vector(0,0,142),False,True)
        self.r.set_actor_rotation(unreal.Rotator(yaw=0),True);self.r.set_actor_tick_enabled(True)
        self.stage=0;self.patrol=[];self.approach=[];self.previous_location=None;self.previous_t=None;self.death_hips=[]
        if self.name=="ground_death":
            self.r.get_editor_property("attributes").apply_damage(99999.,None);self.r.configure_approx()
        unreal.EditorPythonScripting.set_keep_python_script_alive(True)
        self.handle=unreal.register_slate_post_tick_callback(self.tick)
        return str(OUT/("PIE-"+self.name+".json"))
    def tick(self,delta):
        try:
            t=unreal.GameplayStatics.get_time_seconds(self.w)-self.start
            if time.monotonic()-self.wall_start>35:raise TimeoutError("Behavior wall timeout")
            state=self.sample(t);location=self.r.get_actor_location()
            if self.name=="ground_death":
                if t>1.6:
                    hip=self.body.get_socket_transform("bone_000",unreal.RelativeTransformSpace.RTS_COMPONENT).translation.z
                    self.death_hips.append(float(hip))
                if t>2.6:
                    self.check(state=="Dead" and self.r.get_health_percent()==0.,"HP zero and repeated ConfigureApprox remain Dead")
                    self.check(not self.r.request_basic_attack("ACTION::BITE"),"dead actor refuses attacks")
                    self.check(len(self.death_hips)>5 and max(self.death_hips)<80. and max(self.death_hips)-min(self.death_hips)<1.,"nonlooping death end pose holds",hip_samples=self.death_hips)
                    self.finish();return
            else:
                speed=None
                if self.previous_t is not None and t-self.previous_t>.0001:
                    speed=math.hypot(location.x-self.previous_location.x,location.y-self.previous_location.y)/(t-self.previous_t)
                self.previous_location=location;self.previous_t=t
                hip=self.body.get_socket_transform("bone_000",unreal.RelativeTransformSpace.RTS_COMPONENT).translation.z
                if self.stage==0:
                    if state=="Patrol" and speed is not None and t>.4:self.patrol.append((speed,float(hip)))
                    if t>1.8:
                        forward=self.r.get_actor_forward_vector()
                        self.target.set_actor_location(unreal.Vector(location.x+forward.x*3500,location.y+forward.y*3500,94.15),False,True)
                        self.stage=1
                elif state=="Approach" and speed is not None:self.approach.append((speed,float(hip)))
                elif state=="Attack" and self.stage==1:
                    patrol=[x[0] for x in self.patrol];approach=[x[0] for x in self.approach]
                    self.check(len(patrol)>10 and abs(sum(patrol)/len(patrol)-333.21946)<5.,"actual patrol speed matches Walk source",count=len(patrol),mean=sum(patrol)/max(1,len(patrol)))
                    self.check(len(approach)>5 and abs(max(approach)-1248.35)<20.,"automatic discovery leads to sustained approach at Run speed",count=len(approach),max=max(approach,default=0))
                    self.check(self.r.get_current_attack_name() in ["ACTION::BITE","ACTION::DASH_BITE2","ACTION::FIRE_BREATH","ACTION::ROLLING_TAIL_ATTACK2_L"],"single production decision policy selected a configured attack",attack=self.r.get_current_attack_name())
                    self.check(sum(x[1] for x in self.patrol)/max(1,len(self.patrol))>345.,"Patrol uses evaluated Walk pose instead of full Run")
                    self.check(abs(location.z-142)<3.,"walking/approach maintain safe floor clearance",z=location.z)
                    self.finish();return
            if t>12:raise TimeoutError("Behavior did not reach expected state "+state)
        except Exception:self.finish(traceback.format_exc())
def run_behavior(case_name="behavior"):
    global _ACTIVE
    if case_name not in ["behavior","ground_death"]:raise RuntimeError("Unknown behavior case")
    previous=getattr(unreal,"_rathian_basic_case",None)
    if previous and not previous.done:raise RuntimeError("Another case running")
    _ACTIVE=BehaviorCase(case_name,None);unreal._rathian_basic_case=_ACTIVE
    try:return _ACTIVE.begin()
    except Exception:
        _ACTIVE.finish(traceback.format_exc())
        raise


def case_status():
    c=getattr(unreal,"_rathian_basic_case",None)
    if not c:return json.dumps({"exists":False})
    return json.dumps({"exists":True,"case":c.name,"done":c.done,"passed":c.report.get("passed"),"error":c.report.get("error"),"checks":c.report.get("checks"),"sample_count":len(c.report.get("samples",[]))})

def prepare_drawn():
    w=world()
    if not w or "/Game/MHWI/Rathian/Basic/Maps/UEDPIE_" not in w.get_path_name():raise RuntimeError("Only Basic PIE")
    r=monster();r.set_actor_tick_enabled(False);r.set_combat_target(None)
    p=unreal.GameplayStatics.get_player_pawn(w,0)
    p.set_actor_location(unreal.Vector(-5000,0,94.15),False,True)
    if p.is_sheathed() and not p.request_input(unreal.MHWIInput.LIGHT):raise RuntimeError("DrawSlash input rejected")
    return json.dumps({"requested":True})
def drawn_ready():
    p=unreal.GameplayStatics.get_player_pawn(world(),0)
    return json.dumps({"ready":not p.is_sheathed() and p.get_current_move().is_none(),"sheathed":p.is_sheathed(),"move":str(p.get_current_move())})
