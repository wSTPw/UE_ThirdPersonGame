"""Staged UE asset import/promotion for the source-fidelity implementation.

Imports new parallel sequences only. Promotion preserves montage segment times,
notifies, routes and gameplay tuning, and takes a disk backup before writing.
No third-party or original source FBX is edited.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil

import unreal
import import_assets

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024'
SOURCE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeFidelity'
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'
CLIP_RE = re.compile(r'A_((?:w03|co00)_00_\d+)')


def _save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def _preflight():
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before importing or promoting assets')


def _backup(obj):
    relative = Path('Content') / (obj.get_path_name().split('.')[0][6:] + '.uasset')
    source = ROOT / relative
    target = OUT / 'Backup' / relative
    if not source.is_file():
        raise RuntimeError('No disk asset for backup: ' + str(source))
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return str(relative)


def _import(path, destination, skeleton, root_motion):
    name = 'A_' + path.stem
    asset_path = destination + '/' + name
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        sequence = unreal.load_asset(asset_path)
    else:
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', str(path))
        task.set_editor_property('destination_path', destination)
        task.set_editor_property('destination_name', name)
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', False)
        task.set_editor_property('save', True)
        task.set_editor_property('factory', unreal.FbxFactory())
        task.set_editor_property('options', import_assets.fbx_options('animation', skeleton))
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        sequence = unreal.load_asset(asset_path)
    if not isinstance(sequence, unreal.AnimSequence) or sequence.get_editor_property('skeleton') != skeleton:
        raise RuntimeError('Import/skeleton mismatch: ' + asset_path)
    sequence.set_editor_property('enable_root_motion', bool(root_motion))
    sequence.set_editor_property('force_root_lock', False)
    sequence.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
    return sequence


def import_weapons():
    _preflight()
    manifest = json.loads((OUT / 'weapon-animation-manifest.json').read_text(encoding='utf8'))
    if manifest['family'] != 'wg03_00' or not manifest['protected_sources_unchanged']:
        raise RuntimeError('Weapon family/source evidence failed')
    skeleton = unreal.load_asset(manifest['target_skeleton'])
    _backup(skeleton)
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    rows = []
    for row in manifest['clips']:
        path = ROOT / row['fbx']['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['fbx']['sha256']:
            raise RuntimeError('Weapon FBX changed: ' + str(path))
        sequence = _import(path, row['animation_path'].rsplit('/', 1)[0], skeleton, False)
        if abs(sequence.get_play_length() - row['exported_duration_seconds']) > .0001:
            raise RuntimeError('Weapon duration mismatch: ' + str(row['motion_no']))
        rows.append({'motion_no': row['motion_no'], 'asset': sequence.get_path_name(),
                     'duration': sequence.get_play_length()})
    _save('weapon-ue-import.json', {'status': 'imported_not_enabled', 'clips': rows})
    return {'imported': len(rows)}


def _source_weapon_events(montage, by_clip):
    result = []
    if not montage:
        return result
    for track in montage.get_editor_property('slot_anim_tracks'):
        for segment in track.get_editor_property('anim_track').get_editor_property('anim_segments'):
            sequence = segment.get_editor_property('anim_reference')
            match = CLIP_RE.match(sequence.get_name()) if sequence else None
            if not match:
                raise RuntimeError('Unrecognized source clip in ' + montage.get_path_name())
            start = segment.get_editor_property('anim_start_time')
            end = segment.get_editor_property('anim_end_time')
            rate = segment.get_editor_property('anim_play_rate')
            offset = segment.get_editor_property('start_pos')
            if rate <= 0 or segment.get_editor_property('looping_count') != 1:
                raise RuntimeError('Unqualified reversed/looped weapon event segment')
            for event in by_clip.get(match.group(1), []):
                at = event['frame'] / 60.
                if start <= at <= end:
                    result.append((offset + (at-start)/rate, event['motion_no']))
    return sorted(result, key=lambda e: e[0])


def enable_weapon_events():
    _preflight()
    manifest = json.loads((OUT / 'weapon-animation-manifest.json').read_text(encoding='utf8'))
    data = unreal.load_asset(DATA)
    _backup(data)
    motions = {int(r['motion_no']): unreal.load_asset(r['animation_path']) for r in manifest['clips']}
    if len(motions) != 6 or not all(motions.values()):
        raise RuntimeError('Six imported weapon clips required')
    by_clip = {}
    for event in manifest['hunter_motion_events']:
        by_clip.setdefault(event['hunter_clip'], []).append(event)
    definitions = dict(data.get_editor_property('moves'))
    authored = []
    for key, original in definitions.items():
        definition = original.copy()
        montage = definition.get_editor_property('montage')
        source_events = _source_weapon_events(montage, by_clip)
        variants = list(definition.get_editor_property('spirit_level_montages').values())
        sheathed = definition.get_editor_property('sheathed_montage')
        if sheathed:
            variants.append(sheathed)
        for variant in variants:
            actual = [(t, n) for t, n in _source_weapon_events(variant, by_clip) if n >= 0]
            if actual != [(t, n) for t, n in source_events if n >= 0]:
                raise RuntimeError('Variant needs separate weapon event track: ' + str(key))
        events = []
        for at, motion in source_events:
            value = unreal.MHWIWeaponMotionEvent()
            value.set_editor_property('time', at)
            value.set_editor_property('motion_no', motion)
            events.append(value)
        definition.set_editor_property('weapon_motion_events', events)
        definitions[key] = definition
        authored.append({'move': str(key), 'events': [
            {'time': e.get_editor_property('time'), 'motion_no': e.get_editor_property('motion_no')}
            for e in events]})
    data.set_editor_property('weapon_motions', motions)
    data.set_editor_property('moves', definitions)
    unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False)
    _save('weapon-events-authored.json', {'status': 'saved', 'family': 'wg03_00', 'definitions': authored,
        'boundary': 'Internal weapon motions only; fixed whole-equipment mounts remain project fitting.'})
    return {'definitions': len(authored), 'events': sum(len(r['events']) for r in authored)}


def import_hunter(clips=None):
    _preflight()
    manifest = json.loads((SOURCE / 'export-manifest.json').read_text(encoding='utf8'))
    skeleton = unreal.load_asset('/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton')
    _backup(skeleton)
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    rows = []
    for row in manifest['clips']:
        clip = row.get('clip', row.get('name'))
        if clips is not None and clip not in clips:
            continue
        if not row.get('eligible_for_runtime', False):
            continue
        info = row['fbx']
        path = ROOT / (info['path'] if isinstance(info, dict) else info)
        sha256 = info['sha256'] if isinstance(info, dict) else row['sha256']
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
            raise RuntimeError('Hunter FBX changed: ' + str(path))
        bank = 'Common' if clip.startswith('co00') else 'LongSword'
        sequence = _import(path, '/Game/MHWI/Animations/NativeFidelity/' + bank, skeleton, True)
        if abs(sequence.get_play_length() - row.get('duration_seconds', row.get('duration'))) > .0001:
            raise RuntimeError('Hunter duration mismatch: ' + clip)
        rows.append({'clip': clip, 'asset': sequence.get_path_name(), 'duration': sequence.get_play_length()})
    _save('hunter-ue-import.json', {'status': 'imported_not_promoted', 'clips': rows})
    return {'imported': len(rows)}


def promote_hunter(clips):
    """After qualification, replace actual segment references, never recreate montages."""
    _preflight()
    data = unreal.load_asset(DATA)
    _backup(data)
    manifest = json.loads((SOURCE / 'export-manifest.json').read_text(encoding='utf8'))
    qualified = {r['clip']: r for r in manifest['clips'] if r.get('eligible_for_runtime') and r.get('passed')}
    replacements = {}
    for clip in clips:
        if clip not in qualified:
            raise RuntimeError('Not qualified by native export verification: ' + clip)
        bank = 'Common' if clip.startswith('co00') else 'LongSword'
        sequence = unreal.load_asset('/Game/MHWI/Animations/NativeFidelity/' + bank + '/A_' + clip)
        if not isinstance(sequence, unreal.AnimSequence):
            raise RuntimeError('Missing qualified parallel sequence: ' + clip)
        replacements['A_' + clip] = sequence
    montages, rows = {}, []
    for value in data.get_editor_property('moves').values():
        for property_name in ('montage', 'sheathed_montage'):
            montage = value.get_editor_property(property_name)
            if montage:
                montages[montage.get_path_name()] = montage
        for montage in value.get_editor_property('spirit_level_montages').values():
            if montage:
                montages[montage.get_path_name()] = montage
    for path, montage in montages.items():
        tracks = list(montage.get_editor_property('slot_anim_tracks'))
        changed = False
        for track in tracks:
            anim_track = track.get_editor_property('anim_track')
            segments = list(anim_track.get_editor_property('anim_segments'))
            for segment in segments:
                old = segment.get_editor_property('anim_reference')
                replacement = replacements.get(old.get_name()) if old else None
                if replacement and old != replacement:
                    _backup(montage)
                    if abs(old.get_play_length() - replacement.get_play_length()) > .0001:
                        raise RuntimeError('Promotion must preserve duration: ' + old.get_name())
                    rows.append({'montage': path, 'old': old.get_path_name(), 'new': replacement.get_path_name(),
                                 'start': segment.get_editor_property('anim_start_time'),
                                 'end': segment.get_editor_property('anim_end_time')})
                    segment.set_editor_property('anim_reference', replacement)
                    changed = True
            anim_track.set_editor_property('anim_segments', segments)
            track.set_editor_property('anim_track', anim_track)
        if changed:
            montage.set_editor_property('slot_anim_tracks', tracks)
            unreal.EditorAssetLibrary.save_loaded_asset(montage, only_if_is_dirty=False)
    previous_path = OUT / 'hunter-promotion.json'
    previous = json.loads(previous_path.read_text(encoding='utf8')).get('segments', []) if previous_path.exists() else []
    _save('hunter-promotion.json', {'status': 'saved', 'utc_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                  'segments': previous + rows, 'preserved': 'segment ranges, montage identities, notifies, gameplay tuning'})
    return {'segments_promoted': len(rows)}
