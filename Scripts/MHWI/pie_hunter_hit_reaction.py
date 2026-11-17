"""Basic-only PIE regression: final Hunter bone pose and actual displacement.
Uses fresh Basic PIE per case; never writes assets. Report passed is authoritative.
"""
import unreal,sys,json,math,datetime,time,traceback
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0,str(ROOT/"Scripts/MHWI"))
import pie_rathian_basic as basic
OUT=ROOT/"Saved/RathianHitReaction-20261107/regression"
BONES=["bone_root","bone_000","bone_001","bone_002","bone_003","bone_004","bone_005"]
def v(x):return [float(x.x),float(x.y),float(x.z)]
def q(x):return [float(x.x),float(x.y),float(x.z),float(x.w)]
def mul(a,b):
    x,y,z,w=a;X,Y,Z,W=b
    return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def inv(a):return [-a[0],-a[1],-a[2],a[3]]
def angle(a,b):return math.degrees(2*math.acos(min(1.,abs(sum(x*y for x,y in zip(a,b))))))
def pose(mesh):
    result={}
    for name in BONES:
        t=mesh.get_socket_transform(name,unreal.RelativeTransformSpace.RTS_COMPONENT)
        result[name]={"p":v(t.translation),"q":q(t.rotation)}
    return result
class ReactionCase(basic.Case):
    def __init__(self,move,stance,mode,fps,tag):
        super().__init__(move+("_drawn" if stance=="drawn" else "")+"_knockback",None)
        self.move=move;self.mode=mode;self.fps=float(fps);self.tag=tag;self.hurt=None;self.anchor=None;self.hurt_anchor=None;self.baseline=None;self.input_sent=False
        self.pm=self.target.mesh;self.poses=[]
        self.old_throttle=unreal.get_default_object(unreal.load_class(None,"/Script/UnrealEd.EditorPerformanceSettings")).get_editor_property("bThrottleCPUWhenNotForeground")
        self.report.update(script_revision=2,case_id=tag,scope="Actual mesh component-space pose, root-relative rotations, source correlation and physical position; engineering profile, not MHWI runtime equivalence.",reaction_samples=self.poses)
        self.options=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.RAW,should_retarget=False,extract_root_motion=False,incorporate_root_motion_into_pose=True)
    def begin(self):
        result=super().begin()
        self.anchor=v(self.target.get_actor_location());self.baseline=pose(self.pm)
        if self.fps:unreal.SystemLibrary.execute_console_command(self.w,"t.MaxFPS "+str(self.fps))
        settings=unreal.get_default_object(unreal.load_class(None,"/Script/UnrealEd.EditorPerformanceSettings"))
        settings.set_editor_property("bThrottleCPUWhenNotForeground",False)
        return result
    def sample(self,t):
        if self.mode in ["attack","spam"] and not self.input_sent and t>.65:
            self.input_sent=True;self.report["attack_input_accepted"]=self.target.request_input(unreal.MHWIInput.LIGHT)
        state=super().sample(t);now=pose(self.pm);hp=float(self.a.get_current_health())
        if hp>=self.hp:self.baseline=now
        if hp<self.hp and self.hurt is None:
            self.hurt=t;self.hurt_anchor=v(self.target.get_actor_location());self.hit_sheathed=self.target.is_sheathed()
            self.report["stance_at_hit"]="sheathed" if self.hit_sheathed else "drawn"
        if self.mode=="spam" and self.hurt is not None:
            self.report.setdefault("repeated_attack_inputs",[]).append({"t":t,"accepted":self.target.request_input(unreal.MHWIInput.LIGHT)})
        control=str(self.target.get_control_state());diag=self.target.get_native_playback_diagnostic()
        row={"t":t,"hp":hp,"armor":self.target.get_counter_armor_remaining(),"control":control,"native":diag,"position":v(self.target.get_actor_location()),"pose":now}
        if self.hurt is not None and "FLINCH" in control.upper():
            fields=dict(x.split("=",1) for x in diag.split() if "=" in x)
            if fields.get("bank") in ["co00_00","w03_00","co00_01"] and (fields.get("bank")=="co00_01" or fields.get("body") in ["61","62","63","70","71","72"]):
                folder="DamageSource" if fields["bank"]=="co00_01" else "R06Remaining"
                seq=unreal.load_asset("/Game/MHWI/Animations/%s/A_%s_%03d"%(folder,fields["bank"],int(fields["body"])))
                frame=max(0,min(seq.get_editor_property("data_model_interface").get_number_of_frames(),round(float(fields["frame"]))))
                src=unreal.AnimPoseExtensions.get_anim_pose_at_frame(seq,frame,self.options)
                root=unreal.AnimPoseExtensions.get_bone_pose(src,"bone_root",unreal.AnimPoseSpaces.WORLD)
                actual_root=now["bone_root"];errors=[];changes=[]
                for bone in BONES[2:]:
                    tr=unreal.AnimPoseExtensions.get_bone_pose(src,bone,unreal.AnimPoseSpaces.WORLD)
                    actual=mul(inv(actual_root["q"]),now[bone]["q"])
                    expected=mul(inv(q(root.rotation)),q(tr.rotation))
                    base=mul(inv(self.baseline["bone_root"]["q"]),self.baseline[bone]["q"])
                    errors.append(angle(actual,expected));changes.append(angle(actual,base))
                hip=math.dist(now["bone_000"]["p"],self.baseline["bone_000"]["p"])
                row.update(source_frame=frame,source_rotation_mean_error_deg=sum(errors)/len(errors),changed_spine_bones=sum(x>12 for x in changes),hip_component_delta_cm=hip)
                row["visible_correlated_reaction"]=frame>0 and (sum(x>12 for x in changes)>=2 or hip>12) and sum(errors)/len(errors)<12
        self.poses.append(row)
        return state
    def check_player_impact(self):
        tier="small" if self.move=="bite" else ("medium" if self.move=="fire" else "large")
        rows=[s for s in self.poses if tier in s["control"].lower()]
        self.check(bool(rows),"correct reaction tier present",tier=tier)
        damage=[s for s in rows if "bank=co00_01" in s["native"] and any("body=%d "%m in s["native"] for m in (92,93,94,96,104,105,106,107))]
        self.check(bool(damage),"impact plays Common DAMAGE_S bank, not STEP",count=len(damage),sources=[s["native"] for s in damage[:3]])
        if tier=="large":
            getup=[s for s in self.poses if "bank=co00_01" in s["native"] and "body=7 " in s["native"]]
            self.check(bool(getup),"launched Large chains into DOWN stand-up after landing",getup_samples=len(getup))
            if getup:
                self.check(all("FLINCH" in str(s["control"]).upper() for s in getup),"stand-up keeps input locked",controls=sorted(set(str(s["control"]) for s in getup)))
        visible=[s for s in rows if s.get("visible_correlated_reaction")]
        self.check(bool(visible),"final evaluated mesh visibly changes and correlates with reaction source",qualifying_samples=len(visible),minimum_error_deg=min([s.get("source_rotation_mean_error_deg",180) for s in rows] or [180]))
        # Exclude approach/draw/attack movement before HP actually decreases.
        post=[s for s in self.poses if self.hurt is not None and s["t"]>=self.hurt]
        origin=self.hurt_anchor or self.anchor
        dx=max([math.hypot(s["position"][0]-origin[0],s["position"][1]-origin[1]) for s in post] or [0])
        dz=max([s["position"][2]-origin[2] for s in post] or [0])
        self.check(dx>8,"actual capsule moves horizontally",distance_cm=dx)
        if tier!="small":self.check(dz>15,"actual capsule rises",height_cm=dz)
        else:self.check(dz<20,"small impact stays near ground",height_cm=dz)
        if self.fps:self.check(max(self.report.get("game_tick_deltas",[0]))>.25,"low-FPS case has real long game ticks",max_dt=max(self.report.get("game_tick_deltas",[0])))
        if self.mode in ["attack","spam"]:self.check(self.report.get("attack_input_accepted") is True,"production attack started before hit")
    def finish(self,error=None):
        if self.done:return
        try:
            settings=unreal.get_default_object(unreal.load_class(None,"/Script/UnrealEd.EditorPerformanceSettings"))
            settings.set_editor_property("bThrottleCPUWhenNotForeground",self.old_throttle)
            if self.report.get("done"):return
            super().finish(error)
        finally:
            old=basic.OUT/("PIE-"+self.name+".json")
            if old.exists():
                destination=basic.OUT/("PIE-"+self.tag+".json")
                if old!=destination:old.replace(destination)
def run(move="charge",stance="sheathed",mode="idle",fps=0,tag=None):
    if move not in ["bite","fire","charge","tail"] or stance not in ["sheathed","drawn"] or mode not in ["idle","attack","spam"]:raise ValueError("Unknown case")
    previous=getattr(unreal,"_rathian_basic_case",None)
    if previous and not previous.done:raise RuntimeError("A Basic case is active")
    basic.OUT=OUT;OUT.mkdir(parents=True,exist_ok=True)
    p=unreal.GameplayStatics.get_player_pawn(basic.world(),0)
    if not isinstance(p,unreal.MHWICharacter) or (stance=="drawn")!= (not p.is_sheathed()):raise RuntimeError("Need requested actual stance; use prepare_drawn/drawn_ready before run")
    tag=tag or ("%s-%s-%s-%s"%(move,stance,mode,str(fps)))
    case=ReactionCase(move,stance,mode,fps,tag)
    unreal._rathian_basic_case=case
    try:case.begin()
    except Exception:case.finish(traceback.format_exc());raise
    return str(OUT/("PIE-"+tag+".json"))
def status():
    case=getattr(unreal,"_rathian_basic_case",None)
    return json.dumps({"done":case.done if case else None,"passed":case.report.get("passed") if case else None,"checks":case.report.get("checks") if case and case.done else None})
