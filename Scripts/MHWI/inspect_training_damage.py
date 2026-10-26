"""Read training targets and Python damage-delegate support; no saved edits."""
import json
from pathlib import Path
import unreal

def audit(output_name='training-targets-before.json'):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rows = [{'path': a.get_path_name(), 'label': a.get_actor_label(),
             'attacks': a.get_editor_property('enable_attacks'),
             'damage': a.get_editor_property('damage'), 'range': a.get_editor_property('attack_range'),
             'interval': a.get_editor_property('attack_interval')}
            for a in subsystem.get_all_level_actors() if isinstance(a, unreal.MHWITrainingTarget)]
    Path(unreal.Paths.project_saved_dir(),'MHWIImport',output_name).write_text(json.dumps(rows,indent=2),encoding='utf8')
    return rows

def delegate_api():
    cdo = unreal.get_default_object(unreal.load_asset('/Game/MHWI/Blueprints/BP_MHWI_Hunter').generated_class())
    d = cdo.get_editor_property('attributes').get_editor_property('on_damaged')
    return {n: str(getattr(d,n).__doc__) for n in dir(d) if n.startswith(('add_', 'remove_'))}
