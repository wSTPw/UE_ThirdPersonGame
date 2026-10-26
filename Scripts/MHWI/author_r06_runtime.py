"""Migrate RollStepSlash to an unprefixed main; no tests or verification calls.

The native runtime now owns 129. Existing composite remains as a historical asset.
Save only the copied RollStepSlash definition, with a disk backup before mutation.
"""
import json
from pathlib import Path
import shutil


def run():
    import unreal
    root = Path(unreal.Paths.project_dir()).resolve()
    out = root/'Saved/MHWIRestoration/B08-20261025'
    out.mkdir(parents=True, exist_ok=True)
    journal = out/'roll-main-migration.json'
    if journal.exists():
        raise RuntimeError('Preserve the existing migration journal; do not apply a second clock conversion')
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Asset authoring requires editor world')
    data = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Expected formal MHWIMovesetData')
    definitions = dict(data.get_editor_property('moves'))
    keys = {str(k): k for k in definitions}
    definition = definitions[keys['RollStepSlash']].copy()
    old = definition.get_editor_property('montage')
    main_definition = definitions[keys['StepSlash']]
    main = main_definition.get_editor_property('montage')
    old_tracks, new_tracks = old.get_editor_property('slot_anim_tracks'), main.get_editor_property('slot_anim_tracks')
    if len(old_tracks) != 1 or len(new_tracks) != 1:
        raise RuntimeError('Unsupported slot topology')
    old_segments = old_tracks[0].get_editor_property('anim_track').get_editor_property('anim_segments')
    new_segments = new_tracks[0].get_editor_property('anim_track').get_editor_property('anim_segments')
    if len(old_segments) != 2 or len(new_segments) != 1:
        raise RuntimeError('Expected the legacy composite and a single unprefixed main')
    if old_segments[0].get_editor_property('anim_reference').get_name() != 'A_w03_00_129':
        raise RuntimeError('Preserve an unrecognized predecessor asset')
    source, dest = old_segments[1], new_segments[0]
    old_sequence, new_sequence = source.get_editor_property('anim_reference'), dest.get_editor_property('anim_reference')
    if old_sequence != new_sequence or new_sequence.get_name() != 'A_w03_00_101':
        raise RuntimeError('Migration must retain the actual qualified 101 main sequence')
    def parameters(segment):
        sequence = segment.get_editor_property('anim_reference')
        return dict(position=float(segment.get_editor_property('start_pos')),
                    start=float(segment.get_editor_property('anim_start_time')),
                    rate=float(segment.get_editor_property('anim_play_rate')) * float(sequence.get_editor_property('rate_scale')))
    old_clock, new_clock = parameters(source), parameters(dest)
    if old_clock['rate'] <= 0 or new_clock['rate'] <= 0:
        raise RuntimeError('Reverse motion needs a different native clock adapter')
    def convert(value):
        source_time = old_clock['start'] + (float(value) - old_clock['position']) * old_clock['rate']
        return new_clock['position'] + (source_time - new_clock['start']) / new_clock['rate']
    relative = Path('Content/MHWI/Data/DA_MHWI_LongSword.uasset')
    backup = out/'Backup'/relative
    if backup.exists():
        raise RuntimeError('Preserve the existing asset backup')
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root/relative, backup)
    changed = {}
    for prop in ('cancel_start', 'cancel_end', 'turn_start_time', 'turn_end_time'):
        previous = float(definition.get_editor_property(prop))
        value = convert(previous)
        definition.set_editor_property(prop, value)
        changed[prop] = dict(previous=previous, value=value)
    for prop in ('return_turn_start_time', 'return_turn_end_time'):
        previous = float(definition.get_editor_property(prop))
        if previous >= 0:
            value = convert(previous)
            definition.set_editor_property(prop, value)
            changed[prop] = dict(previous=previous, value=value)
    for prop, fields in (('damage_windows', ('start_time', 'end_time')), ('routes', ('cancel_start', 'cancel_end'))):
        rows = []
        report = []
        for original in definition.get_editor_property(prop):
            row = original.copy()
            values = {}
            for field in fields:
                before = float(row.get_editor_property(field))
                if prop == 'routes' and before < 0:
                    continue  # Inherited endpoints remain inherited.
                value = convert(before)
                row.set_editor_property(field, value)
                values[field] = dict(previous=before, value=value)
            rows.append(row)
            report.append(values)
        definition.set_editor_property(prop, rows)
        changed[prop] = report
    # These are the existing event/rate tracks of the exact same full main clip.
    # The prefix has no main damage event; it is handled by native connector data.
    for prop in ('weapon_motion_events', 'source_play_rates', 'empowered_source_play_rates'):
        definition.set_editor_property(prop, main_definition.get_editor_property(prop))
    definition.set_editor_property('montage', main)
    definitions[keys['RollStepSlash']] = definition
    record = dict(status='prepared', tests_executed=False, data=data.get_path_name(),
                  old_montage=old.get_path_name(), new_montage=main.get_path_name(),
                  old_clock=old_clock, new_clock=new_clock, changed=changed,
                  backup=backup.relative_to(root).as_posix(), untouched_other_definitions=True)
    journal.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    data.set_editor_property('moves', definitions)
    if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
        raise RuntimeError('Formal DataAsset save failed; keep journal and backup')
    record['status'] = 'saved_not_readback_or_tested'
    journal.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    marker = root/'Tools/MHW/r06-runtime-adapter.json'
    marker.write_text(json.dumps(dict(schema=1, status='source_implemented_uncompiled_untested',
        roll_main_migrated=True, data=data.get_path_name(), main=main.get_path_name(),
        journal=journal.relative_to(root).as_posix(), tests_executed=False), indent=2)+'\n', encoding='utf8')
    return dict(saved=True, tests_executed=False, move='RollStepSlash', new_montage=main.get_path_name())


def promote_native_thrust():
    """Bind Action71 to the constructor-proven 112, retaining existing gameplay tuning."""
    import unreal
    root = Path(unreal.Paths.project_dir()).resolve()
    out = root/'Saved/MHWIRestoration/B08-20261025'
    journal = out/'native-thrust-migration.json'
    if journal.exists():
        raise RuntimeError('Preserve existing native-thrust migration journal')
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Asset authoring requires editor world')
    data = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
    sequence = unreal.load_asset('/Game/MHWI/Animations/R06Staging/A_w03_00_112')
    if not isinstance(data, unreal.MHWIMovesetData) or not isinstance(sequence, unreal.AnimSequence):
        raise RuntimeError('Formal moveset and authored native 112 are required')
    definitions = dict(data.get_editor_property('moves'))
    key = next(k for k in definitions if str(k) == 'SpiritComboThrust')
    definition = definitions[key].copy()
    original = definition.get_editor_property('montage')
    package = '/Game/MHWI/Montages/M_SpiritComboThrustNative'
    if unreal.EditorAssetLibrary.does_asset_exist(package):
        raise RuntimeError('Preserve existing native insertion montage')
    backup = out/'Backup-Thrust/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    if backup.exists():
        raise RuntimeError('Preserve existing intermediate DataAsset backup')
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root/'Content/MHWI/Data/DA_MHWI_LongSword.uasset', backup)
    montage = unreal.EditorAssetLibrary.duplicate_asset(original.get_path_name(), package)
    if not isinstance(montage, unreal.AnimMontage):
        raise RuntimeError('Montage duplication failed')
    tracks = list(montage.get_editor_property('slot_anim_tracks'))
    if len(tracks) != 1:
        raise RuntimeError('Native insertion montage needs a single slot')
    track = tracks[0].get_editor_property('anim_track')
    segments = list(track.get_editor_property('anim_segments'))
    if len(segments) != 1 or segments[0].get_editor_property('anim_reference').get_name() != 'A_w03_00_105':
        raise RuntimeError('Preserve an unrecognized existing insertion animation')
    # Original 112 and 105 share the exact 82-track table and pose header; their
    # CollisionTimelineObject bit-0 keys are both 22..33. No pose/timing guess.
    segments[0].set_editor_property('anim_reference', sequence)
    track.set_editor_property('anim_segments', segments)
    tracks[0].set_editor_property('anim_track', track)
    montage.set_editor_property('slot_anim_tracks', tracks)
    if not unreal.EditorAssetLibrary.save_loaded_asset(montage, only_if_is_dirty=False):
        raise RuntimeError('Native insertion montage save failed')
    definition.set_editor_property('montage', montage)
    definitions[key] = definition
    record = dict(status='prepared', tests_executed=False, move=str(key),
        old_montage=original.get_path_name(), new_montage=montage.get_path_name(),
        sequence=sequence.get_path_name(), native_action=[3, 71], native_main=112,
        constructor='0x1417fe9e0', main_store='0x1417fe9f1', connector=118, main_start_frame=14,
        source='Tools/MHW/native-main-motion-bindings.json',
        gameplay_tuning_preserved=True, backup=backup.relative_to(root).as_posix())
    journal.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    data.set_editor_property('moves', definitions)
    if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
        raise RuntimeError('Native insertion DataAsset save failed')
    record['status'] = 'saved_not_readback_or_tested'
    journal.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    return dict(saved=True, tests_executed=False, native_main=112, montage=montage.get_path_name())
