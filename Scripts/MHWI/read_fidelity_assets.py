"""UE editor-only, read saved MHWI defaults for the source-fidelity investigation.

No PIE, component edits, dirtying or save_asset calls. Writes only an audit JSON.
"""
from pathlib import Path
import datetime
import hashlib
import json

import unreal


def run():
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    da = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
    props = [
        'cancel_start', 'cancel_end', 'play_rate', 'source_play_rates',
        'empowered_source_play_rates', 'turn_start_time', 'turn_end_time',
        'turn_max_angle', 'turn_speed', 'return_turn_start_time',
        'return_turn_end_time', 'return_turn_max_angle', 'counter_start',
        'counter_end', 'auto_follow_up', 'auto_follow_up_time', 'auto_follow_up_on_hit',
    ]
    rows = {}
    for key, value in da.get_editor_property('moves').items():
        row = {p: str(value.get_editor_property(p)) for p in props}
        montage = value.get_editor_property('montage')
        row['montage'] = montage.get_path_name() if montage else None
        row['segments'] = []
        if montage:
            for track in montage.get_editor_property('slot_anim_tracks'):
                for segment in track.get_editor_property('anim_track').get_editor_property('anim_segments'):
                    sequence = segment.get_editor_property('anim_reference')
                    row['segments'].append({
                        'sequence': sequence.get_path_name() if sequence else None,
                        **{p: str(segment.get_editor_property(p)) for p in (
                            'start_pos', 'anim_start_time', 'anim_end_time', 'anim_play_rate', 'looping_count')},
                    })
        row['routes'] = [{
            'input': str(r.get_editor_property('input')),
            'next_move': str(r.get_editor_property('next_move')),
            'require_hit': r.get_editor_property('require_hit'),
            'require_counter': r.get_editor_property('require_counter'),
            'require_drawn': r.get_editor_property('require_drawn'),
        } for r in value.get_editor_property('routes')]
        rows[str(key)] = row
    bp = unreal.load_asset('/Game/MHWI/Blueprints/BP_MHWI_Hunter')
    cdo = unreal.get_default_object(bp.generated_class())
    components = {}
    for name in ['WeaponMesh', 'ScabbardMesh']:
        comp = cdo.get_editor_property(name)
        mesh = comp.get_editor_property('skeletal_mesh_asset')
        components[name] = {
            'mesh': mesh.get_path_name() if mesh else None,
            'animation_mode': str(comp.get_editor_property('animation_mode')),
            'anim_class': str(comp.get_editor_property('anim_class')),
        }
    defaults = {p: str(cdo.get_editor_property(p)) for p in [
        'weapon_bone', 'scabbard_bone', 'sheathed_weapon_bone', 'special_scabbard_bone',
        'weapon_relative_transform', 'scabbard_relative_transform',
        'sheathed_weapon_relative_transform', 'special_scabbard_relative_transform',
        'special_weapon_relative_transform',
    ]}
    protected = [root / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset',
                 root / 'Content/MHWI/Blueprints/BP_MHWI_Hunter.uasset']
    report = {
        'status': 'editor_read_only_saved_asset_inspection_not_PIE',
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'data_asset': da.get_path_name(), 'move_count': len(rows),
        'input_buffer_seconds': da.get_editor_property('input_buffer_seconds'),
        'moves': rows, 'components': components, 'attachment_defaults': defaults,
        'disk_asset_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in protected},
    }
    path = root / 'Saved/MHWIImport/SourceFidelity-20261024/editor-readback.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'move_count': len(rows), 'components': components}))
    return report
