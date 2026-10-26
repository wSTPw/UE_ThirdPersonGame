"""Qualify explicit shared LMT track blocks and adapt the three Iai colour clips.

This is not a generic NeedsParent evaluator. An alias is permitted only when a
NeedsParent entry points to the exact same skeletal track block as an already
qualified non-parent entry and every sampling-affecting field/record agrees.
The unresolved native layer context is retained as a limitation. No rest pose
or adjacent clip is guessed as a missing base.

Outside Unreal: ``python Scripts/MHWI/qualify_native_parent_pose.py`` writes a
read-only source qualification report. Inside Unreal, the coordinator previews
``author_aliases(save=False)`` and explicitly saves with ``save=True``. Only the
three existing coloured Montage segment references change; their identities,
events, crops and playback data remain intact. The formal DataAsset is not saved.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import re
import shutil

import native_animation_source as native

ROOT = native.ROOT
OUT = ROOT / 'Saved/MHWIImport/NativeParentPose-20261024'
MANIFEST = native.OUTPUT / 'export-manifest.json'
BIND = native.OUTPUT / 'rig-bind.json'
TIMING = ROOT / 'Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json'
BASE_ID = 308
TARGETS = {309: 'IaiSpiritSlashWhite', 310: 'IaiSpiritSlashYellow', 311: 'IaiSpiritSlashRed'}
NATIVE_ASSET = '/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_308'
DATA_PATH = '/Game/MHWI/Data/DA_MHWI_LongSword'
EXPECTED_SOURCE_SHA256 = '2406ee8f61fe7ba21008f200881be6d339c93af07a9ff7ada9260f0c58a8c42b'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _plain(value):
    if dataclasses.is_dataclass(value):
        return _plain(dataclasses.asdict(value))
    if isinstance(value, bytes):
        return {'hex': value.hex()}
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _source_tracks(action):
    rows = []
    for index, track in enumerate(action.tracks):
        rows.append({'slot': index, 'header': _plain(track.header),
                     'buffer_sha256': hashlib.sha256(track.raw_buffer).hexdigest(),
                     'lerp_basis': _plain(track.lerp_basis)})
    return rows


def _timing_tracks(entry):
    return {(group['name'], track['name']): track
            for group in entry['groups'] for track in group['tracks']}


def qualify(write_report=True):
    """Read only original files, pinned sampler, bind and qualified 308 FBX."""
    source = native.SOURCES['w03_00']
    before_sha = _sha(source)
    if before_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError('Original w03_00 LMT fingerprint changed')
    reader, pose = native.native_modules()
    bank = reader.read_lmt_file(source)
    actions = {action.id: action for action in bank.actions}
    bind = json.loads(BIND.read_text(encoding='utf8'))
    mapping = {int(name[5:]): name for name in bind['bones']
               if name.startswith('bone_') and name[5:].isdigit() and int(name[5:]) < 512}
    manifest = json.loads(MANIFEST.read_text(encoding='utf8'))
    base_row = next(row for row in manifest['clips'] if row['index'] == BASE_ID and row['bank'] == 'w03_00')
    if not base_row.get('eligible_for_runtime') or not base_row.get('passed'):
        raise RuntimeError('308 must already have passed native source/FBX qualification')
    if _sha(ROOT / base_row['fbx']) != base_row['sha256']:
        raise RuntimeError('Qualified 308 FBX fingerprint changed')
    base = actions[BASE_ID]
    if base.header.flags2 & 1:
        raise RuntimeError('Chosen shared-track representative must not require parent')
    compiled_base = pose.compile_pose_evaluation(base, mapping, version=bank.header.version)
    if not compiled_base.supported:
        raise RuntimeError('308 sampling context unsupported')
    timing = json.loads(TIMING.read_text(encoding='utf8'))
    if timing['source']['sha256'] != before_sha:
        raise RuntimeError('TIML evidence is from a different source')
    timing_entries = {row['index']: row for row in timing['source']['entries']}
    base_timl = _timing_tracks(timing_entries[BASE_ID])
    ignored_header_fields = {'id', 'flags2', 'timl_offset'}
    source_bytes = source.read_bytes()
    raw_block = source_bytes[base.header.fcurve_offset:
                             base.header.fcurve_offset + base.header.fcurve_count * reader.TRACK_STRUCT.size]
    report = {'schema': 1, 'status': 'source_shared_track_qualification',
              'original_source': native.evidence(source),
              'qualified_base': {'index': BASE_ID, 'manifest_sha256': _sha(MANIFEST),
                                 'fbx': base_row['fbx'], 'fbx_sha256': base_row['sha256'],
                                 'source_verification': base_row['source_verification'],
                                 'fbx_verification': base_row['fbx_verification']},
              'sampler_rule': pose.RULE_VERSION, 'rig_bind_sha256': _sha(BIND),
              'bone_count': bind['bone_count'], 'skeletal_track_count': len(base.tracks),
              'raw_track_block_offset': base.header.fcurve_offset,
              'raw_track_block_bytes': len(raw_block),
              'raw_track_block_sha256': hashlib.sha256(raw_block).hexdigest(),
              'base_header': _plain(base.header), 'base_track_records': _source_tracks(base),
              'generic_needs_parent_semantics_resolved': False,
              'native_parent_motion_index_found': False,
              'adaptation': 'Share qualified 308 skeletal sequence only; retain colour-specific Montage identity and TIML/gameplay data.',
              'base_context_boundary': ('The file explicitly aliases the same track block. This proves identical authored skeletal channels and holes, '
                                        'not the game layer/default pose for omitted channels. Reusing the already qualified 308 complete project pose '
                                        'is a conservative project adaptation; no missing channel is filled from a guessed neighbouring motion.'),
              'upstream_base_contract': 'NeedsParent requires caller-supplied ACTION base/context; no automatic parent ID is resolved by the upstream helper.',
              'upstream_evidence': [native.evidence(native.UPSTREAM / path) for path in [
                  'core/formats/lmt/model.py', 'core/formats/lmt/reader.py',
                  'core/formats/lmt/pose_evaluation.py', 'blender_adapter/pose_helpers.py',
                  'docs/duplicate-track-baking-integration.md']],
              'targets': [], 'passed': False, 'UE_asset_changes': False}
    for index, move in TARGETS.items():
        action = actions[index]
        equal_sampling_header = all(getattr(base.header, field.name) == getattr(action.header, field.name)
                                    for field in dataclasses.fields(base.header) if field.name not in ignored_header_fields)
        candidates = [candidate.id for candidate in bank.actions
                      if not candidate.header.flags2 & 1
                      and candidate.header.fcurve_offset == action.header.fcurve_offset
                      and candidate.header.fcurve_count == action.header.fcurve_count
                      and candidate.tracks == action.tracks]
        if candidates != [BASE_ID] or not equal_sampling_header or action.header.flags2 != 1:
            raise RuntimeError('%s: explicit unique source-track alias qualification failed' % index)
        if action.tracks != base.tracks:
            raise RuntimeError('%s: record/buffer/quantization/basis mismatch' % index)
        compiled = pose.compile_pose_evaluation(action, mapping, version=bank.header.version)
        if not compiled.supported or compiled.bindings != compiled_base.bindings:
            raise RuntimeError('%s: binding/remap/sampler plans differ' % index)
        sample_count = (action.header.frame_count - 1) * 4 + 1
        max_component_error, comparisons = 0.0, 0
        # Sample every integer frame and quarter frame. Identical missing-channel
        # sets and bindings establish equality for any identical explicit base.
        for quarter in range(sample_count):
            frame = quarter / 4.0
            source_sample = compiled.sample(frame)
            reference_sample = compiled_base.sample(frame)
            if source_sample.keys() != reference_sample.keys():
                raise RuntimeError('%s: component coverage differs' % index)
            for key, value in source_sample.items():
                other = reference_sample[key]
                max_component_error = max(max_component_error, *(abs(a-b) for a, b in zip(value, other)))
                comparisons += len(value)
        if max_component_error != 0:
            raise RuntimeError('%s: aliased source curve samples are not exactly equal' % index)
        target_timl = _timing_tracks(timing_entries[index])
        timl_differences = []
        order_differences = []
        for key in sorted(base_timl.keys() | target_timl.keys()):
            left, right = base_timl.get(key), target_timl.get(key)
            # Adding a colour-specific common track shifts later display orders;
            # distinguish that metadata from changed values/times/interpolation.
            content_left = {k: v for k, v in left.items() if k != 'order'} if left else None
            content_right = {k: v for k, v in right.items() if k != 'order'} if right else None
            if content_left != content_right:
                timl_differences.append({'group': key[0], 'property': key[1], 'base': left, 'target': right})
            elif left != right:
                order_differences.append({'group': key[0], 'property': key[1],
                                          'base_order': left.get('order'), 'target_order': right.get('order')})
        common = 'nTimelineParam::PlMotionCommon'
        weapon_keys_equal = base_timl[(common, 'mWeaponMotionNo')]['keys'] == target_timl[(common, 'mWeaponMotionNo')]['keys']
        collision_keys_equal = (base_timl[('nTimelineParam::CollisionTimelineObject', 'mFlag')]['keys']
                                == target_timl[('nTimelineParam::CollisionTimelineObject', 'mFlag')]['keys'])
        if not weapon_keys_equal or not collision_keys_equal:
            raise RuntimeError('Colour-specific weapon/collision timing changed; review adapter manually')
        report['targets'].append({'index': index, 'move': move,
            'header_differences': {field.name: {'base': _plain(getattr(base.header, field.name)),
                                               'target': _plain(getattr(action.header, field.name))}
                                   for field in dataclasses.fields(base.header)
                                   if getattr(base.header, field.name) != getattr(action.header, field.name)},
            'explicit_nonparent_shared_block_candidates': candidates,
            'same_track_pointer': True, 'same_sampling_header_except_needs_parent_flag': True,
            'all_track_headers_buffers_basis_and_weights_identical': True,
            'all_compiled_bindings_and_selected_record_indices_identical': True,
            'same_authored_and_missing_component_sets': True,
            'sample_frames': sample_count, 'sample_step': .25,
            'sample_range': [0, action.header.frame_count - 1],
            'component_comparisons': comparisons, 'max_component_error': max_component_error,
            'timl_differences_preserve_in_gameplay': timl_differences,
            'timl_order_only_differences': order_differences,
            'weapon_motion_event_keys_identical': weapon_keys_equal,
            'collision_active_keys_identical': collision_keys_equal,
            'source_motion_speed_keys_preserve': target_timl[(common, 'mMotionSpeed')]['keys'],
            'eligible_for_shared_track_adapter': True,
            'generic_native_parent_evaluation_qualified': False})
    report['protected_source_unchanged'] = _sha(source) == before_sha
    report['passed'] = report['protected_source_unchanged'] and len(report['targets']) == 3
    if write_report:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'source-parent-alias-qualification.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return report


def _segment_snapshot(segment):
    sequence = segment.get_editor_property('anim_reference')
    return {'sequence': sequence.get_path_name() if sequence else None,
            **{field: float(segment.get_editor_property(field))
               for field in ['start_pos', 'anim_start_time', 'anim_end_time', 'anim_play_rate']},
            'looping_count': int(segment.get_editor_property('looping_count'))}


def _stable_value(value):
    """Serialize known public values; never compare a StructBase repr/address."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, 'get_path_name'):
        return value.get_path_name()
    if isinstance(value, (tuple, list)):
        return [_stable_value(item) for item in value]
    # Unreal Name and EnumBase have stable textual values. A StructBase repr
    # contains its native allocation address and must never be accepted here.
    import unreal
    if isinstance(value, (unreal.Name, unreal.EnumBase)):
        result = str(value)
        if re.search(r'0x[0-9a-fA-F]+', result):
            raise TypeError('Unexpected pointer in a supposedly stable name/enum')
        return result
    raise TypeError('Explicit stable serialization required for ' + type(value).__name__)


def _notify_snapshot(montage):
    """Public API copies protected UAnimSequenceBase::Notifies for inspection.

    The API returns FAnimNotifyEvent copies. Their script-visible object,
    trigger and filter fields are inspected explicitly. Trigger time/duration
    and track membership use library functions; raw offsets and TrackIndex are
    not Python-visible UPROPERTY fields even though C++ declares them public.
    """
    import unreal
    library = unreal.AnimationLibrary
    fields = ['notify_name', 'notify', 'notify_state_class',
              'trigger_weight_threshold', 'montage_tick_type',
              'notify_trigger_chance', 'notify_filter_type', 'notify_filter_lod',
              'can_be_filtered_via_request', 'trigger_on_dedicated_server', 'trigger_on_follower']
    def snapshot(event):
        row = {field: _stable_value(event.get_editor_property(field)) for field in fields}
        row['trigger_time'] = float(library.get_anim_notify_event_trigger_time(event))
        row['duration'] = float(library.get_anim_notify_event_duration(event))
        return row
    track_names = list(library.get_animation_notify_track_names(montage))
    return {'api': 'AnimationLibrary.get_animation_notify_events',
            'track_names': [str(name) for name in track_names],
            'events': [snapshot(event) for event in library.get_animation_notify_events(montage)],
            'events_by_track': [{'track_name': str(name),
                                 'events': [snapshot(event) for event in library.get_animation_notify_events_for_track(montage, name)]}
                                for name in track_names],
            'scope': 'all returned event identities, actual trigger times, durations, script-visible trigger/filter properties and public API track membership; protected native offsets/parent-link internals excluded'}


def _blend_snapshot(args):
    return {field: _stable_value(args.get_editor_property(field))
            for field in ['blend_time', 'blend_option', 'custom_curve']}


def _montage_guard(montage):
    # Native public getters avoid protected Notifies and private FAlphaBlend
    # internals. Each snapshot consists solely of JSON scalars/object paths.
    return {'notifies': _notify_snapshot(montage),
            'section_names': [str(montage.get_section_name(index))
                              for index in range(montage.get_num_sections())],
            'section_guard_scope': 'public section count and ordered names; section links/times are not independently inspected by this guard',
            'blend_in': _blend_snapshot(montage.get_blend_in_args()),
            'blend_out': _blend_snapshot(montage.get_blend_out_args()),
            **{field: _stable_value(montage.get_editor_property(field)) for field in [
                'enable_auto_blend_out', 'rate_scale', 'blend_out_trigger_time',
                'blend_mode_in', 'blend_mode_out', 'blend_profile_in', 'blend_profile_out']}}


def capture_metadata(label='before'):
    """Read-only UE snapshot usable around native set_montage_sequence calls.

    Writes evidence JSON under Saved only. It neither authorizes nor performs
    the segment mutation and can be used instead of the Python writer.
    """
    import unreal
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', label):
        raise ValueError('Metadata label must be a simple evidence filename')
    rows = []
    for index, move in TARGETS.items():
        path = '/Game/MHWI/Montages/M_' + move
        montage = unreal.load_asset(path)
        if not isinstance(montage, unreal.AnimMontage):
            raise RuntimeError('Missing coloured Montage: ' + path)
        rows.append({'source_colour_id': index, 'montage': montage.get_path_name(),
                     'metadata': _montage_guard(montage),
                     'slots': [{'slot_name': str(track.get_editor_property('slot_name')),
                                'segments': [_segment_snapshot(segment) for segment in
                                    track.get_editor_property('anim_track').get_editor_property('anim_segments')]}
                               for track in montage.get_editor_property('slot_anim_tracks')]})
    report = {'schema': 1, 'status': 'read_only_UE_metadata_snapshot', 'label': label,
              'data_asset_sha256': _sha(ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'),
              'montages': rows, 'UE_asset_changes': False}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('alias-metadata-' + label + '.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return report


def compare_metadata(before_label='before', after_label='after'):
    """Validate native/Python replacement snapshots without requiring Unreal."""
    for label in (before_label, after_label):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', label):
            raise ValueError('Metadata labels must be simple evidence filenames')
    before = json.loads((OUT / ('alias-metadata-' + before_label + '.json')).read_text(encoding='utf8'))
    after = json.loads((OUT / ('alias-metadata-' + after_label + '.json')).read_text(encoding='utf8'))
    if before['data_asset_sha256'] != after['data_asset_sha256']:
        raise RuntimeError('Formal DataAsset disk contents changed during alias replacement')
    if len(before['montages']) != 3 or len(after['montages']) != 3:
        raise RuntimeError('Expected three coloured Montage snapshots')
    result = []
    for left, right in zip(before['montages'], after['montages']):
        if (left['montage'] != right['montage'] or left['source_colour_id'] != right['source_colour_id']
                or left['metadata'] != right['metadata']):
            raise RuntimeError('Coloured Montage identity/observed metadata changed')
        if len(left['slots']) != len(right['slots']):
            raise RuntimeError('Montage slot count changed')
        count = 0
        for old_slot, new_slot in zip(left['slots'], right['slots']):
            if old_slot['slot_name'] != new_slot['slot_name'] or len(old_slot['segments']) != len(new_slot['segments']):
                raise RuntimeError('Montage slot/segment layout changed')
            for old, new in zip(old_slot['segments'], new_slot['segments']):
                if new['sequence'].split('.')[0] != NATIVE_ASSET:
                    raise RuntimeError('Segment does not reference qualified Native308')
                expected_old = '/Game/MHWI/Animations/LongSword/A_w03_00_%03d' % left['source_colour_id']
                if old['sequence'].split('.')[0] not in (expected_old, NATIVE_ASSET):
                    raise RuntimeError('Unexpected baseline sequence')
                if {k: v for k, v in old.items() if k != 'sequence'} != {k: v for k, v in new.items() if k != 'sequence'}:
                    raise RuntimeError('Montage crop/rate/offset changed during alias replacement')
                count += 1
        if count != 1:
            raise RuntimeError('Expected the original single-segment colour Montage layout')
        result.append({'montage': right['montage'], 'observed_metadata_equal': True,
                       'segments': count, 'replacement': NATIVE_ASSET})
    report = {'schema': 1, 'passed': True, 'montages': result,
              'data_asset_unchanged': True,
              'notification_guard': 'public API event identities/time/duration/trigger/filter/track fields, including empty arrays',
              'section_guard_boundary': 'section count/names observed; protected native parent-link and section time/link internals not independently verified',
              'generic_needs_parent_semantics_resolved': False}
    (OUT / 'alias-metadata-comparison.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return report


def author_aliases(save=False):
    """Coordinator-only UE entry: preview/save three segment-reference changes."""
    import unreal
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before shared-track alias authoring')
    qualification = qualify(write_report=True)
    if not qualification['passed']:
        raise RuntimeError('Original source-track alias qualification failed')
    replacement = unreal.load_asset(NATIVE_ASSET)
    expected_skeleton = unreal.load_asset('/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton')
    if not isinstance(replacement, unreal.AnimSequence) or replacement.get_editor_property('skeleton') != expected_skeleton:
        raise RuntimeError('Expected qualified NativeFidelity308 on production hunter skeleton')
    expected_duration = 176.0 / 60.0
    if abs(replacement.get_play_length() - expected_duration) > .0001:
        raise RuntimeError('Qualified308 duration changed')
    if not replacement.get_editor_property('enable_root_motion') or replacement.get_editor_property('force_root_lock'):
        raise RuntimeError('Qualified308 root-motion configuration changed')
    if 'REF_POSE' not in str(replacement.get_editor_property('root_motion_root_lock')):
        raise RuntimeError('Qualified308 production root basis changed')
    data = unreal.load_asset(DATA_PATH)
    definitions = {str(key): value for key, value in data.get_editor_property('moves').items()}
    variants = definitions['IaiSpiritSlash'].get_editor_property('spirit_level_montages')
    plans = []
    for level, (index, move) in enumerate(TARGETS.items(), start=1):
        path = '/Game/MHWI/Montages/M_' + move
        montage = unreal.load_asset(path)
        if not isinstance(montage, unreal.AnimMontage) or variants.get(level) != montage:
            raise RuntimeError('Formal colour variant identity changed: ' + move)
        if definitions[move].get_editor_property('montage') != montage:
            raise RuntimeError('Formal colour definition disagrees: ' + move)
        tracks = [track.copy() for track in montage.get_editor_property('slot_anim_tracks')]
        before, after = [], []
        changes = 0
        for track in tracks:
            anim_track = track.get_editor_property('anim_track').copy()
            segments = [segment.copy() for segment in anim_track.get_editor_property('anim_segments')]
            for segment in segments:
                old = segment.get_editor_property('anim_reference')
                allowed = '/Game/MHWI/Animations/LongSword/A_w03_00_%03d' % index
                if not old or old.get_path_name().split('.')[0] not in (allowed, NATIVE_ASSET):
                    raise RuntimeError('Unexpected custom segment; preserve and review: ' + move)
                if old.get_editor_property('skeleton') != expected_skeleton or abs(old.get_play_length() - expected_duration) > .0001:
                    raise RuntimeError('Coloured source duration/skeleton mismatch: ' + move)
                before.append(_segment_snapshot(segment))
                if old != replacement:
                    segment.set_editor_property('anim_reference', replacement)
                    changes += 1
                after.append(_segment_snapshot(segment))
            anim_track.set_editor_property('anim_segments', segments)
            track.set_editor_property('anim_track', anim_track)
        if len(before) != 1 or abs(montage.get_play_length() - expected_duration) > .0001:
            raise RuntimeError('Unexpected coloured Montage arrangement: ' + move)
        for old, new in zip(before, after):
            if {k: v for k, v in old.items() if k != 'sequence'} != {k: v for k, v in new.items() if k != 'sequence'}:
                raise RuntimeError('Alias must preserve segment crops/rate/offset')
        metadata = _montage_guard(montage)
        plans.append({'montage': montage, 'tracks': tracks, 'guard': metadata,
                      'row': {'move': move, 'montage': path, 'source_colour_id': index,
                              'shared_source_id': BASE_ID, 'before': before, 'after': after,
                              'metadata_before': metadata,
                              'segments_changed': changes}})
    data_file = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
    data_sha = _sha(data_file)
    report = {'schema': 1, 'status': 'preview', 'saved': False,
              'source_qualification_sha256': _sha(OUT / 'source-parent-alias-qualification.json'),
              'adaptation': qualification['adaptation'],
              'generic_needs_parent_semantics_resolved': False,
              'replacement': replacement.get_path_name(),
              'replacement_asset_sha256': _sha(ROOT / 'Content/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_308.uasset'),
              'montages': [plan['row'] for plan in plans], 'data_asset_sha256_before': data_sha,
              'preserved': ['colour Montage identities', 'slot/segment crops/rates/offsets',
                            'Montage events/notifies/sections/blends', 'all formal DataAsset values',
                            'colour-specific TIML speed/collision/defence/resource and weapon event data'],
              'runtime_validation': 'not_executed_by_this_script'}
    json.dumps(report, indent=2)
    if not save:
        return report
    # Preflight all three before touching any formal object; back up all packages.
    for plan in plans:
        asset_rel = 'Content/MHWI/Montages/M_' + plan['row']['move'] + '.uasset'
        backup = OUT / 'Backup' / asset_rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(ROOT / asset_rel, backup)
        plan['row']['backup'] = str(backup.relative_to(ROOT))
        plan['row']['backup_sha256'] = _sha(backup)
    for plan in plans:
        montage = plan['montage']
        if plan['row']['segments_changed']:
            montage.set_editor_property('slot_anim_tracks', plan['tracks'])
            if _montage_guard(montage) != plan['guard']:
                raise RuntimeError('Unexpected Montage metadata mutation before save')
            if not unreal.EditorAssetLibrary.save_loaded_asset(montage, only_if_is_dirty=False):
                raise RuntimeError('Coloured Montage save failed: ' + plan['row']['move'])
        readback = [_segment_snapshot(segment)
                    for track in montage.get_editor_property('slot_anim_tracks')
                    for segment in track.get_editor_property('anim_track').get_editor_property('anim_segments')]
        if readback != plan['row']['after'] or _montage_guard(montage) != plan['guard']:
            raise RuntimeError('Coloured Montage readback mismatch: ' + plan['row']['move'])
        plan['row']['readback'] = readback
        plan['row']['metadata_after'] = _montage_guard(montage)
    report['data_asset_sha256_after'] = _sha(data_file)
    if report['data_asset_sha256_after'] != data_sha:
        raise RuntimeError('Formal DataAsset changed unexpectedly during alias authoring')
    report['saved'] = True
    report['status'] = 'three_colour_shared_skeletal_aliases_saved_runtime_validation_pending'
    (OUT / 'author-parent-aliases.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return report


if __name__ == '__main__':
    report = qualify()
    print(json.dumps({'passed': report['passed'], 'targets': len(report['targets']),
                      'source_unchanged': report['protected_source_unchanged'],
                      'sample_frames_per_target': report['targets'][0]['sample_frames'],
                      'max_component_error': max(row['max_component_error'] for row in report['targets']),
                      'generic_needs_parent_semantics_resolved': False,
                      'report': str((OUT / 'source-parent-alias-qualification.json').relative_to(ROOT))}, indent=2))
