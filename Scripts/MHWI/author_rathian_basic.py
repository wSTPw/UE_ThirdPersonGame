"""Basic Rathian asset authoring; UE5.8 AnimPoseExtensions/IAnimationDataController.
Only /Game/MHWI/Rathian/Basic assets may be written. Imported originals remain read-only.
Official mechanism: https://dev.epicgames.com/documentation/unreal-engine/API/Editor/AnimationBlueprintLibrary/UAnimationBlueprintLibrary
"""
import unreal, json, math
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/"Saved/RathianBasic-Assets-20261107"
BASE="/Game/MHWI/Rathian/Basic"
SOURCE="/Game/MHWI/Rathalos/Animations/"
# Semantic choices and windows are engineering configuration, not original action-ID proof.
CLIPS=[
 ("A_Rathian_Idle","00_003",0,None,"origin"),
 ("A_Rathian_Walk","00_065",0,None,"linear_xy"),
 ("A_Rathian_WalkHealthy","00_007",0,None,"linear_xy"),
 ("A_Rathian_Run","00_067",0,None,"linear_xy"),
 ("A_Rathian_Death","03_031",0,None,"origin"),
 ("A_Rathian_Bite","02_001",0,None,"origin"),
 ("A_Rathian_FireWindup","08_008",0,1.5,"fixed"),
 ("A_Rathian_FireRelease","08_008",1.5,None,"fixed"),
 ("A_Rathian_TailTakeoff","08_002",0,0.3,"fixed"),
 ("A_Rathian_TailFlip","08_002",0.3,None,"fixed"),
 ("A_Rathian_Landing","08_103",0,None,"fixed"),
 ("A_Rathian_ChargeWindup","00_003",0,0.4,"origin"),
 ("A_Rathian_Charge","00_067",0,1.65,"linear_xy"),
 ("A_Rathian_ChargeRecovery","02_001",1.3,None,"origin"),
 ("A_Rathian_BiteSmooth","02_001",0,None,"linear_xy"),
 ("A_Rathian_ChargeRecoverySmooth","02_001",1.3,None,"linear_xy"),
 ("A_Rathian_SpitWindup","00_081",0,0.7,"stationary_xy"),
 ("A_Rathian_SpitRelease","00_081",0.7,None,"stationary_xy"),
 ("A_Rathian_LandingGround","08_005",0,None,"actor_flight"),
 ("A_Rathian_LandingDescend","08_005",0,0.633333333333,"actor_flight"),
 ("A_Rathian_LandingRecovery","08_005",0.633333333333,None,"stationary_xy"),
 # Source-qualified clips added for the Basic engineering fixture; imported originals remain untouched.
 ("A_Rathian_SingleFireWindup","02_078",0,None,"stationary_xy"),
 ("A_Rathian_SingleFireShot","02_081",0,None,"stationary_xy"),
 ("A_Rathian_ChargeStart","00_067",0,.4,"linear_xy"),
 ("A_Rathian_ChargeRun","00_067",.4,2.05,"linear_xy"),
 ("A_Rathian_ChargeStop","00_008",0,None,"linear_xy"),
]
def vec(v): return [float(v.x),float(v.y),float(v.z)]
def qvec(q,v):
    # q normalized; rotate vector, no hardcoded Armature roll.
    x,y,z=v; qx,qy,qz,qw=float(q.x),float(q.y),float(q.z),float(q.w)
    tx,ty,tz=2*(qy*z-qz*y),2*(qz*x-qx*z),2*(qx*y-qy*x)
    return [x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx]
def inv_position(t,v):
    delta=[v[i]-vec(t.translation)[i] for i in range(3)]
    q=t.rotation
    qr=unreal.Quat(-q.x,-q.y,-q.z,q.w)
    result=qvec(qr,delta); scale=vec(t.scale3d)
    if any(abs(s)<1e-8 for s in scale): raise RuntimeError("Zero parent scale")
    return unreal.Vector(*[result[i]/scale[i] for i in range(3)])
def load(path):
    a=unreal.load_asset(path)
    if not a: raise RuntimeError("Missing "+path)
    return a
def own_world():
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if editor.is_in_play_in_editor(): raise RuntimeError("Stop PIE before asset authoring")
    w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not w or not w.get_path_name().startswith(BASE+"/Maps/L_RathianBasic."): raise RuntimeError("Wrong world")
    return w
def inspect_source():
    seq=load(SOURCE+"A_em001_00_067")
    m=seq.get_editor_property("data_model_interface")
    result={"rate":str(m.get_frame_rate()),"rate_fields":dir(m.get_frame_rate()),"frames":m.get_number_of_frames(),"keys":m.get_number_of_keys(),"tracks":[str(x) for x in m.get_bone_track_names()],"controller_doc":str(seq.get_editor_property("controller").set_bone_track_keys.__doc__)}
    (OUT/"basic-author-api.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    return json.dumps(result)
def author_clips(names=None):
    own_world()
    source_auxiliary_report()  # Fail closed before creating any target if retiming non-bone data is required.
    lib=unreal.AnimPoseExtensions
    opts=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.RAW,should_retarget=False,extract_root_motion=False,incorporate_root_motion_into_pose=True)
    results=json.loads((OUT/"authored-clips.json").read_text(encoding="utf8")) if (OUT/"authored-clips.json").exists() else []
    for dest,suffix,begin,end,mode in CLIPS:
        if names and dest not in names: continue
        path=BASE+"/Animations/"+dest
        if unreal.EditorAssetLibrary.does_asset_exist(path): raise RuntimeError("Refuse overwrite existing clip "+path)
        source=load(SOURCE+"A_em001_"+suffix); model=source.get_editor_property("data_model_interface")
        rate=model.get_frame_rate(); fps=float(rate.numerator)/float(rate.denominator)
        first=round(begin*fps); last=model.get_number_of_frames() if end is None else min(model.get_number_of_frames(),round(end*fps))
        if last<=first: raise RuntimeError("Empty clip")
        bones=[str(x) for x in model.get_bone_track_names()]
        if not {"bone_root","armature_em001_00"}.issubset({b.lower() for b in bones}): raise RuntimeError("Required root/parent track missing")
        tracks={b:[[],[],[]] for b in bones}; roots=[]; parents=[]
        for frame in range(first,last+1):
            pose=lib.get_anim_pose_at_frame(source,frame,opts)
            for bone in bones:
                t=lib.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.LOCAL)
                tracks[bone][0].append(t.translation); tracks[bone][1].append(t.rotation); tracks[bone][2].append(t.scale3d)
            roots.append(lib.get_bone_pose(pose,"bone_root",unreal.AnimPoseSpaces.WORLD).translation)
            parents.append(lib.get_bone_pose(pose,"Armature_em001_00",unreal.AnimPoseSpaces.WORLD))
        initial=vec(roots[0]); delta=[vec(roots[-1])[i]-initial[i] for i in range(3)]
        for i,root in enumerate(roots):
            p=vec(root); a=i/float(last-first)
            # Actor owns flight height in these engineering phase copies; preserve all hip/limb rotations and translations.
            if mode in ["fixed","actor_flight"]: p=[0.,0.,0.]
            elif mode=="stationary_xy": p=[0.,0.,p[2]]
            elif mode=="linear_xy": p=[p[0]-initial[0]-delta[0]*a,p[1]-initial[1]-delta[1]*a,p[2]]
            else: p=[p[0]-initial[0],p[1]-initial[1],p[2]]
            tracks["bone_root"][0][i]=inv_position(parents[i],p)
        target=unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),path)
        if not target: raise RuntimeError("Duplicate failed "+path)
        ctrl=target.get_editor_property("controller")
        ctrl.open_bracket("Basic owned animation resample",False)
        try:
            ctrl.set_number_of_frames(unreal.FrameNumber(last-first),False)
            for bone,keys in tracks.items():
                if not ctrl.set_bone_track_keys(bone,keys[0],keys[1],keys[2],False): raise RuntimeError("Track write failed "+bone)
        finally: ctrl.close_bracket(False)
        target.set_editor_property("enable_root_motion",False)
        target.set_editor_property("force_root_lock",False)
        target.set_editor_property("rate_scale",1.)
        if target.get_editor_property("skeleton")!=source.get_editor_property("skeleton"): raise RuntimeError("Skeleton changed")
        m=target.get_editor_property("data_model_interface")
        if m.get_number_of_keys()!=last-first+1: raise RuntimeError("Key count mismatch")
        # Validate output root positions after writing; rotation/scale are source samples.
        actual=[]
        for frame in [0,(last-first)//2,last-first]:
            pose=lib.get_anim_pose_at_frame(target,frame,opts)
            actual.append(vec(lib.get_bone_pose(pose,"bone_root",unreal.AnimPoseSpaces.WORLD).translation))
        if mode in ["fixed","actor_flight"] and any(abs(x)>0.05 for v in actual for x in v): raise RuntimeError("Root normalization failed")
        if mode=="linear_xy" and any(abs(actual[j][k])>0.05 for j in [0,2] for k in [0,1]): raise RuntimeError("XY endpoint normalization failed")
        if not unreal.EditorAssetLibrary.save_loaded_asset(target,only_if_is_dirty=False): raise RuntimeError("Save failed "+path)
        results.append({"path":target.get_path_name(),"source":source.get_path_name(),"source_frames":[first,last],"fps":fps,"mode":mode,"frames":last-first,"keys":m.get_number_of_keys(),"duration":target.get_play_length(),"source_root_initial":initial,"source_root_delta":delta,"output_root_0_mid_end":actual})
        (OUT/"authored-clips.json").write_text(json.dumps(results,indent=2),encoding="utf8")
    return json.dumps(results)

def owned_asset(name,folder,cls,factory):
    path=BASE+"/"+folder+"/"+name
    ledger_path=OUT/"owned-config-created.json"
    ledger=json.loads(ledger_path.read_text(encoding="utf8")) if ledger_path.exists() else []
    existing=unreal.load_asset(path)
    if existing:
        if path not in ledger: raise RuntimeError("Existing unowned configuration "+path)
        if not isinstance(existing,cls): raise RuntimeError("Wrong owned class "+path)
        return existing
    result=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,BASE+"/"+folder,cls,factory)
    if not result: raise RuntimeError("Create failed "+path)
    ledger.append(path);ledger_path.write_text(json.dumps(ledger,indent=2),encoding="utf8")
    return result
def props(obj,**values):
    for k,v in values.items(): obj.set_editor_property(k,v)
    return obj
def clip(name): return load(BASE+"/Animations/A_Rathian_"+name)
def box(bone,center,extent):
    return props(unreal.MHWIRathianAttackBox(),bone_name=bone,local_offset_cm=unreal.Vector(*center),half_extent_cm=unreal.Vector(*extent),qualification=unreal.MHWIRathianApproxQualification.ENGINEERING_FIXTURE)
def phase(kind,animation,**values):
    q=unreal.MHWIRathianApproxQualification.ENGINEERING_FIXTURE
    defaults=dict(kind=getattr(unreal.MHWIRathianAttackPhaseKind,kind),animation=clip(animation),window_qualification=q,impact_size_qualification=q,movement_qualification=q,flight_qualification=q,fireball_spawn_qualification=q,blend_in_seconds=.18,blend_out_seconds=.18)
    defaults.update(values)
    return props(unreal.MHWIRathianAttackPhase(),**defaults)
def move(name,minimum,maximum,angle,cooldown,phases):
    q=unreal.MHWIRathianApproxQualification.ENGINEERING_FIXTURE
    return props(unreal.MHWIRathianApproxMove(),registry_name=name,kind=unreal.MHWIRathianApproxMoveKind.ATTACK,anim_qualification=q,attack_window_qualification=q,damage_qualification=q,decision_qualification=q,animation=phases[0].get_editor_property("animation"),preferred_min_distance_cm=minimum,preferred_max_distance_cm=maximum,attack_range_cm=maximum,max_angle_degrees=angle,cooldown_seconds=cooldown,phases=phases)
def create_data():
    own_world()
    q=unreal.MHWIRathianApproxQualification.ENGINEERING_FIXTURE
    f=unreal.DataAssetFactory();f.set_editor_property("data_asset_class",unreal.MHWIRathianApproxStatsData)
    stats=owned_asset("DA_RathianBasic_Stats","Data",unreal.MHWIRathianApproxStatsData,f)
    props(stats,max_health=3000.,max_health_qualification=q,patrol_speed_cm_per_second=333.21946,approach_speed_cm_per_second=1248.35,patrol_radius_cm=1000.,sight_range_cm=4000.,lose_target_range_cm=5500.,sight_half_angle_degrees=80.,decision_cooldown_seconds=.5,turn_speed_deg_per_second=200.,decision_qualification=q)
    mouth=[box("bone_004",(0,16,103),(60,48,105))]
    charge=[box("bone_003",(0,-20,22),(110,95,120)),box("bone_000",(0,-25,-70),(130,135,105))]
    tail=[box("bone_142",(0,-9,-42),(65,60,90)),box("bone_144",(0,-1,-75),(105,70,110)),box("bone_146",(0,-1,-80),(56,46,98))]
    small=unreal.MHWIImpactSize.SMALL;large=unreal.MHWIImpactSize.LARGE
    bite=phase("ACTIVE","BiteSmooth",attack_window_enabled=True,use_legacy_seconds_window=True,window_start_seconds=.05,window_end_seconds=.3833,hit_boxes=mouth,damage=20.,impact_size=small,knockback_velocity=unreal.Vector(300,0,0),blend_in_seconds=.2,blend_out_seconds=.2)
    cw=phase("WINDUP","ChargeStart",move_speed_cm_per_second=450.,blend_in_seconds=.24,blend_out_seconds=.10)
    ca=phase("ACTIVE","ChargeRun",attack_window_enabled=True,window_start=.02,window_end=.96,hit_boxes=charge,damage=35.,impact_size=large,knockback_velocity=unreal.Vector(850,0,380),move_speed_cm_per_second=1248.35,blend_in_seconds=.10,blend_out_seconds=.18)
    cr=phase("RECOVERY","ChargeStop",move_speed_cm_per_second=180.,blend_in_seconds=.18,blend_out_seconds=.25)
    fw=phase("WINDUP","SingleFireWindup",blend_in_seconds=.24,blend_out_seconds=.06)
    fr=phase("ACTIVE","SingleFireShot",spawn_fireball_at_start=True,fireball_spawn_time_seconds=23./60.,fireball_socket_name="bone_003",fireball_local_offset_cm=unreal.Vector(0,15,140),damage=30.,impact_size=unreal.MHWIImpactSize.MEDIUM,knockback_velocity=unreal.Vector(550,0,260),blend_in_seconds=.06,blend_out_seconds=.25)
    tt=phase("TAIL_TAKEOFF","TailTakeoff",takeoff_height_cm=835.6,blend_in_seconds=.24,blend_out_seconds=.04)
    ta=phase("ACTIVE","TailFlip",attack_window_enabled=True,window_start=0.,window_end=.62,hit_boxes=tail,damage=40.,impact_size=large,knockback_velocity=unreal.Vector(600,0,620),blend_in_seconds=.04,blend_out_seconds=.12)
    tl=phase("TAIL_LANDING","LandingDescend",blend_in_seconds=.12,blend_out_seconds=.10)
    tr=phase("RECOVERY","LandingRecovery",blend_in_seconds=.10,blend_out_seconds=.25)
    f=unreal.DataAssetFactory();f.set_editor_property("data_asset_class",unreal.MHWIRathianApproxMovesetData)
    data=owned_asset("DA_RathianBasic_Moveset","Data",unreal.MHWIRathianApproxMovesetData,f)
    props(data,idle_animation=clip("Idle"),walk_animation=clip("WalkHealthy"),run_animation=clip("Run"),death_animation=clip("Death"),moves=[
        move("ACTION::BITE",260.,650.,80.,2.,[bite]),
        move("ACTION::DASH_BITE2",700.,2200.,40.,4.,[cw,ca,cr]),
        move("ACTION::FIRE_BREATH",900.,2400.,35.,5.,[fw,fr]),
        move("ACTION::ROLLING_TAIL_ATTACK2_L",200.,900.,170.,5.,[tt,ta,tl,tr])])
    for obj in [stats,data]:
        if not unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False): raise RuntimeError("Configuration save failed")
    return verify_data()
def verify_data():
    stats=load(BASE+"/Data/DA_RathianBasic_Stats")
    data=load(BASE+"/Data/DA_RathianBasic_Moveset")
    skeleton=load("/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton")
    result={"stats":stats.get_path_name(),"moveset":data.get_path_name(),"stats_properties":{k:str(stats.get_editor_property(k)) for k in ["max_health","patrol_speed_cm_per_second","approach_speed_cm_per_second","sight_range_cm","lose_target_range_cm"]},"moves":[],"locomotion":{}}
    for field in ["idle_animation","walk_animation","run_animation","death_animation"]:
        a=soft_asset(data.get_editor_property(field))
        if not a or a.get_editor_property("skeleton")!=skeleton: raise RuntimeError("Invalid locomotion "+field)
        result["locomotion"][field]=a.get_path_name()
    for m in data.get_editor_property("moves"):
        row={"name":m.get_editor_property("registry_name"),"phases":[]}
        for p in m.get_editor_property("phases"):
            a=soft_asset(p.get_editor_property("animation"))
            if not a or a.get_editor_property("skeleton")!=skeleton: raise RuntimeError("Invalid phase sequence")
            row["phases"].append({"animation":a.get_path_name(),"duration":a.get_play_length(),"properties":p.export_text()})
        result["moves"].append(row)
    (OUT/"basic-data-readback.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    return json.dumps(result)
def setup_scene():
    world=own_world()
    stats=load(BASE+"/Data/DA_RathianBasic_Stats");data=load(BASE+"/Data/DA_RathianBasic_Moveset")
    f=unreal.BlueprintFactory();f.set_editor_property("parent_class",unreal.MHWIRathianApproxPawn)
    bp=owned_asset("BP_RathianBasic","Blueprints",unreal.Blueprint,f)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo=unreal.get_default_object(bp.generated_class())
    props(cdo,stats_data=stats,moveset_data=data,body_ground_offset_cm=-142.)
    cdo.get_editor_property("body").set_relative_rotation(unreal.Rotator(yaw=-90.),False,False)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False): raise RuntimeError("Pawn BP save failed")
    f=unreal.BlueprintFactory();f.set_editor_property("parent_class",unreal.GameModeBase)
    gm=owned_asset("BP_RathianBasicGameMode","Blueprints",unreal.Blueprint,f)
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    g=unreal.get_default_object(gm.generated_class())
    props(g,default_pawn_class=load("/Game/MHWI/Blueprints/BP_MHWI_Hunter").generated_class(),hud_class=unreal.MHWIHUD)
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    unreal.EditorAssetLibrary.save_loaded_asset(gm,only_if_is_dirty=False)
    world.get_world_settings().set_editor_property("default_game_mode",gm.generated_class())
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors=subsystem.get_all_level_actors()
    for actor in actors:
        if actor.get_actor_label()=="RathianBasic_Preview": subsystem.destroy_actor(actor)
    floor=next(a for a in actors if a.get_actor_label()=="Floor")
    floor.static_mesh_component.set_static_mesh(load("/Engine/BasicShapes/Cube"))
    floor.set_actor_scale3d(unreal.Vector(200.,200.,.2))
    floor.set_actor_location(unreal.Vector(0,0,-10),False,True)
    start=next(a for a in actors if isinstance(a,unreal.PlayerStart))
    start.set_actor_location(unreal.Vector(-5000,0,110),False,True)
    start.set_actor_rotation(unreal.Rotator(yaw=0),True)
    r=next((a for a in actors if a.get_actor_label()=="RathianBasic"),None)
    if not r:
        r=subsystem.spawn_actor_from_class(bp.generated_class(),unreal.Vector(0,0,140),unreal.Rotator(yaw=180.))
        r.set_actor_label("RathianBasic")
    props(r,stats_data=stats,moveset_data=data,body_ground_offset_cm=-142.)
    r.get_editor_property("body").set_relative_rotation(unreal.Rotator(yaw=-90),False,False)
    r.get_editor_property("body").set_relative_location(unreal.Vector(0,0,-142),False,False)
    # A simple neutral fill makes shape and hit boxes readable in this dedicated test map.
    for a in actors:
        if isinstance(a,unreal.SkyLight):
            a.light_component.set_editor_property("intensity",2.)
            a.light_component.recapture_sky()
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(): raise RuntimeError("Map save failed")
    result={"world":world.get_path_name(),"pawn":r.get_path_name(),"parent":str(isinstance(unreal.get_default_object(bp.generated_class()),unreal.MHWIRathianApproxPawn)),"stats":r.get_editor_property("stats_data").get_path_name(),"moveset":r.get_editor_property("moveset_data").get_path_name(),"body_relative_rotation":str(r.get_editor_property("body").get_editor_property("relative_rotation")),"body_relative_location":str(r.get_editor_property("body").get_editor_property("relative_location")),"game_mode":gm.generated_class().get_path_name(),"player_start":vec(start.get_actor_location())}
    (OUT/"basic-scene-readback.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    return json.dumps(result)


def open_basic():
    e=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if e.is_in_play_in_editor(): raise RuntimeError("Stop PIE before opening map")
    if unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(): raise RuntimeError("Refuse switching dirty world")
    if not e.load_level(BASE+"/Maps/L_RathianBasic"): raise RuntimeError("Load Basic failed")
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
def soft_asset(value):
    return value if isinstance(value,unreal.Object) else unreal.load_asset(str(value))


def runtime_state():
    w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not w: raise RuntimeError("No PIE game world")
    monsters=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.MHWIRathianApproxPawn)
    p=unreal.GameplayStatics.get_player_pawn(w,0)
    rows=[]
    for r in monsters:
        b=r.get_editor_property("body")
        rows.append({"path":r.get_path_name(),"state":r.get_current_state_name(),"attack":r.get_current_attack_name(),"run":r.get_attack_run_id(),"hp":r.get_health_percent(),"location":vec(r.get_actor_location()),"rotation":str(r.get_actor_rotation()),"body_rotation":str(b.get_editor_property("relative_rotation")),"body_location":str(b.get_editor_property("relative_location")),"anim_class":b.get_anim_instance().get_class().get_path_name() if b.get_anim_instance() else None,"bones":{bone:vec(b.get_socket_transform(bone,unreal.RelativeTransformSpace.RTS_COMPONENT).translation) for bone in ["bone_root","bone_000","bone_003","bone_016","bone_020"]}})
    result={"world":w.get_path_name(),"time":unreal.GameplayStatics.get_time_seconds(w),"player":p.get_path_name() if p else None,"player_location":vec(p.get_actor_location()) if p else None,"monsters":rows}
    (OUT/"runtime-current.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    return json.dumps(result)


def probe_runtime_motion():
    w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    r=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.MHWIRathianApproxPawn)[0]
    r.set_actor_tick_enabled(False)
    initial=r.get_actor_location()
    result={"initial":vec(initial),"sphere":str(r.get_editor_property("hit_proxy").get_editor_property("sphere_radius"))}
    for height in [0.,2.,5.]:
        r.set_actor_location(initial+unreal.Vector(0,0,height),False,True)
        hit=r.set_actor_location(initial+unreal.Vector(100,0,height),True,False)
        result[str(height)]={"location":vec(r.get_actor_location()),"hit":str(hit)}
    r.set_actor_location(initial,False,True)
    r.set_actor_tick_enabled(True)
    (OUT/"runtime-motion-probe.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    return json.dumps(result)


def source_auxiliary_report():
    result=[]
    for suffix in sorted(set(c[1] for c in CLIPS)):
        seq=load(SOURCE+"A_em001_"+suffix)
        model=seq.get_editor_property("data_model_interface")
        row={"source":seq.get_path_name(),"float_curves":model.get_number_of_float_curves(),"transform_curves":model.get_number_of_transform_curves(),"notifies":len(unreal.AnimationLibrary.get_animation_notify_events(seq)),"sync_markers":len(unreal.AnimationLibrary.get_animation_sync_markers(seq)),"attributes":len(model.get_editor_property("AnimatedBoneAttributes"))}
        result.append(row)
    (OUT/"source-auxiliary.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    if any(row[k] for row in result for k in ["float_curves","transform_curves","notifies","sync_markers","attributes"]): raise RuntimeError("Auxiliary source data requires explicit retiming")
    return json.dumps(result)
def blueprint_registry_report():
    result={}
    for name in ["BP_RathianBasic","BP_RathianBasicGameMode"]:
        result[name]={str(k):str(v) for k,v in unreal.EditorAssetLibrary.get_tag_values(BASE+"/Blueprints/"+name).items() if str(k) in ["GeneratedClass","ParentClass","NativeParentClass","IsDataOnly"]}
    (OUT/"basic-blueprint-registry.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    return json.dumps(result)


def verify_authored_clips():
    opts=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.RAW,should_retarget=False,extract_root_motion=False,incorporate_root_motion_into_pose=True)
    lib=unreal.AnimPoseExtensions
    rows=json.loads((OUT/"authored-clips.json").read_text(encoding="utf8"))
    results=[]
    for row in rows:
        source=load(row["source"]);target=load(row["path"])
        first,last=row["source_frames"];mode=row["mode"];n=last-first
        sr=[]
        for frame in [first,last]:
            pose=lib.get_anim_pose_at_frame(source,frame,opts)
            sr.append(vec(lib.get_bone_pose(pose,"bone_root",unreal.AnimPoseSpaces.WORLD).translation))
        delta=[sr[1][j]-sr[0][j] for j in range(3)]
        max_error=0.;pose_error=0.
        for frame in range(n+1):
            src_pose=lib.get_anim_pose_at_frame(source,first+frame,opts)
            dst_pose=lib.get_anim_pose_at_frame(target,frame,opts)
            p=vec(lib.get_bone_pose(src_pose,"bone_root",unreal.AnimPoseSpaces.WORLD).translation)
            actual=vec(lib.get_bone_pose(dst_pose,"bone_root",unreal.AnimPoseSpaces.WORLD).translation)
            if mode in ["fixed","actor_flight"]: expected=[0.,0.,0.]
            elif mode=="stationary_xy": expected=[0.,0.,p[2]]
            elif mode=="linear_xy": expected=[p[0]-sr[0][0]-delta[0]*frame/n,p[1]-sr[0][1]-delta[1]*frame/n,p[2]]
            elif mode=="origin": expected=[p[0]-sr[0][0],p[1]-sr[0][1],p[2]]
            else: raise RuntimeError("Unknown root mode")
            max_error=max(max_error,math.sqrt(sum((actual[j]-expected[j])**2 for j in range(3))))
            if frame in [0,n//2,n]:
                for bone in ["bone_000","bone_003","bone_016","bone_020","bone_146"]:
                    sb=vec(lib.get_bone_pose(src_pose,bone,unreal.AnimPoseSpaces.WORLD).translation)
                    db=vec(lib.get_bone_pose(dst_pose,bone,unreal.AnimPoseSpaces.WORLD).translation)
                    pose_error=max(pose_error,math.sqrt(sum(((db[j]-actual[j])-(sb[j]-p[j]))**2 for j in range(3))))
        results.append({"path":row["path"],"mode":mode,"keys_checked":n+1,"root_max_error_cm":max_error,"relative_pose_error_cm":pose_error,"passed":max_error<.05 and pose_error<.05})
    report={"passed":all(x["passed"] for x in results),"clips":results}
    (OUT/"authored-clips-verification.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    if not report["passed"]:raise RuntimeError("Authored animation validation failed; inspect report")
    return json.dumps({"passed":True,"clips":len(results),"keys_checked":sum(r["keys_checked"] for r in results),"max_root_error_cm":max(r["root_max_error_cm"] for r in results),"max_relative_pose_error_cm":max(r["relative_pose_error_cm"] for r in results)})
