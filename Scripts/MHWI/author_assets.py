"""UE MHWI authoring stages: materials, data, character and training map."""
import json
import re
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/MHWIImport'
ROOT_ASSET = '/Game/MHWI'

BEHAVIOR_MOVE_FIELDS = ['turn_start_time', 'turn_end_time', 'turn_max_angle', 'turn_speed',
                        'return_turn_start_time', 'return_turn_end_time', 'return_turn_max_angle']
BEHAVIOR_DATA_FIELDS = ['helm_air_vertical_speed', 'helm_air_forward_speed', 'helm_air_gravity',
                        'helm_strike_speed', 'helm_strike_start_time']


def behavior_fields_ready():
    """Fail before authoring if the A shared reflection contract is not compiled in."""
    missing = []
    probe = unreal.MHWIMoveDefinition()
    for name in BEHAVIOR_MOVE_FIELDS:
        try:
            probe.get_editor_property(name)
        except Exception:
            missing.append('FMHWIMoveDefinition.' + name)
    try:
        unreal.MHWIRoute().get_editor_property('require_drawn')
    except Exception:
        missing.append('FMHWIRoute.require_drawn')
    data_class = unreal.load_class(None, '/Script/IntroCpp.MHWIMovesetData')
    data_probe = unreal.get_default_object(data_class) if data_class else None
    if data_probe is None:
        missing.append('UMHWIMovesetData class defaults')
    else:
        for name in BEHAVIOR_DATA_FIELDS:
            try:
                data_probe.get_editor_property(name)
            except Exception:
                missing.append('UMHWIMovesetData.' + name)
    if missing:
        raise RuntimeError('MHWI behaviour reflection fields missing: ' + ', '.join(missing))
    return True


def asset(path):
    obj = unreal.load_asset(path)
    if not obj:
        raise RuntimeError('Required asset missing: ' + path)
    return obj


def create(name, folder, cls, factory):
    path = ROOT_ASSET + '/' + folder + '/' + name
    existing = unreal.load_asset(path)
    return existing or unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,
                ROOT_ASSET + '/' + folder, cls, factory)


def texture_path(source):
    parts = source.replace('\\', '/').strip('/').split('/')
    return ROOT_ASSET + '/Textures/' + '/'.join(parts[:-1]) + '/T_' + parts[-1]


def materials():
    bindings = json.loads((ROOT / 'Scripts/MHWI/material_bindings.json').read_text(encoding='utf-8'))
    edit = unreal.MaterialEditingLibrary
    master = create('M_MHWI_Surface', 'Materials', unreal.Material, unreal.MaterialFactoryNew())
    edit.delete_all_material_expressions(master)
    albedo = edit.create_material_expression(master, unreal.MaterialExpressionTextureSampleParameter2D, -520, -80)
    albedo.set_editor_property('parameter_name', 'BaseColor')
    albedo.set_editor_property('texture', asset(ROOT_ASSET + '/Textures/Assets/default_tex/T_null_white'))
    normal = edit.create_material_expression(master, unreal.MaterialExpressionTextureSampleParameter2D, -520, 180)
    normal.set_editor_property('parameter_name', 'NormalMap')
    normal.set_editor_property('texture', asset(ROOT_ASSET + '/Textures/Assets/default_tex/T_null_NM'))
    normal.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    roughness = edit.create_material_expression(master, unreal.MaterialExpressionScalarParameter, -260, 330)
    roughness.set_editor_property('parameter_name', 'Roughness')
    roughness.set_editor_property('default_value', 0.65)
    edit.connect_material_property(albedo, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    edit.connect_material_property(normal, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    edit.connect_material_property(roughness, '', unreal.MaterialProperty.MP_ROUGHNESS)
    master.set_editor_property('two_sided', True)
    edit.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master)
    instances = {}
    for name, entry in bindings.items():
        safe = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        mi = create('MI_' + safe, 'Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        edit.set_material_instance_parent(mi, master)
        for kind, parameter in [('tAlbedoMap', 'BaseColor'), ('tNormalMap', 'NormalMap')]:
            source = next((v for k, v in entry['textures'].items() if k.startswith(kind)), None)
            if source:
                texture = asset(texture_path(source))
                edit.set_material_instance_texture_parameter_value(mi, parameter, texture)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        instances[name] = mi
    assigned = []
    for path in ['/Character/SK_MHWI_Hunter', '/Weapons/SK_MHWI_LongSword', '/Weapons/SK_MHWI_Scabbard']:
        mesh = asset(ROOT_ASSET + path)
        mats = mesh.get_editor_property('materials')
        for index, slot in enumerate(mats):
            names = [str(slot.get_editor_property('imported_material_slot_name')),
                     str(slot.get_editor_property('material_slot_name'))]
            match = next((instances[name] for name in names if name in instances), None)
            if not match:
                # FBX may add its node's material prefix or suffix; only accept a unique match.
                matches = [value for key, value in instances.items() if any(key in name for name in names)]
                if len(matches) == 1:
                    match = matches[0]
            if not match:
                raise RuntimeError(f'No unambiguous material for {path} slot {names}')
            slot.set_editor_property('material_interface', match)
            mats[index] = slot
            assigned.append(dict(mesh=path, slot=index, material=match.get_path_name()))
        mesh.set_editor_property('materials', mats)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    (OUT / 'materials.json').write_text(json.dumps(assigned, indent=2), encoding='utf-8')
    return dict(instances=len(instances), slots=len(assigned))


def montage_for(move_id, clip, common=False):
    sequence = asset(ROOT_ASSET + '/Animations/' + ('Common/' if common else 'LongSword/') + 'A_' + clip)
    name = 'M_' + move_id
    factory = unreal.AnimMontageFactory()
    factory.set_editor_property('target_skeleton', sequence.get_editor_property('skeleton'))
    factory.set_editor_property('source_animation', sequence)
    montage = create(name, 'Montages', unreal.AnimMontage, factory)
    for property_name, seconds in [('blend_in', 0.10), ('blend_out', 0.12)]:
        blend = montage.get_editor_property(property_name)
        blend.set_editor_property('blend_time', seconds)
        montage.set_editor_property(property_name, blend)
    if move_id in ['SpecialSheathe', 'HelmAir', 'SpiritHelmBreaker']:
        montage.set_editor_property('enable_auto_blend_out', False)
    unreal.EditorAssetLibrary.save_loaded_asset(montage)
    return montage


def route(command, next_move, hit=False, counter=False, drawn=False):
    value = unreal.MHWIRoute()
    enum_name = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', command).upper()
    value.set_editor_property('input', getattr(unreal.MHWIInput, enum_name))
    value.set_editor_property('next_move', next_move)
    value.set_editor_property('require_hit', hit)
    value.set_editor_property('require_counter', counter)
    value.set_editor_property('require_drawn', drawn)
    return value


def moveset():
    if (ROOT / 'Tools/MHW/r06-runtime-adapter.json').exists():
        raise RuntimeError('R06 owns connector playback. Legacy moveset regeneration would restore the obsolete 129 prefix; use targeted authoring.')
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level.is_in_play_in_editor():
        raise RuntimeError('Stop PIE before rebuilding the MHWI moveset')
    behavior_fields_ready()
    mapping = json.loads((ROOT / 'Scripts/MHWI/moveset_mapping.json').read_text(encoding='utf-8'))
    # Reject a regenerated stale source table before creating any montage: the
    # earlier table reversed 140/170 and labelled 140 as the helm-breaker opener.
    for name, clip, node, action, collision in [
            ('SpiritThrust', 'w03_00_170', 45, 87, [[84.0, 97.0]]),
            ('ForesightSlash', 'w03_00_140', 28, 86, [[70.0, 80.0]]),
            ('FadeSlashLeft', 'w03_00_128', 9, 83, [[27.0, 42.0]]),
            ('FadeSlashRight', 'w03_00_127', 8, 82, [[27.0, 43.0]])]:
        source = mapping['moves'][name]
        if (source['clip'] != clip or source['fsm_node_id'] != node
                or source['fsm_action_no'] != action
                or source['collision_active_frames'] != collision):
            raise RuntimeError('moveset_mapping.json has a stale %s entry; expected %s node %s action %s collision %s'
                               % (name, clip, node, action, collision))
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.MHWIMovesetData)
    data = create('DA_MHWI_LongSword', 'Data', unreal.MHWIMovesetData, factory)
    definitions = {}
    authored = []
    damage = {'StepSlash': 26, 'OverheadSlash': 26, 'FadeSlash': 24, 'FadeSlashLeft': 24,
              'FadeSlashRight': 24, 'SpiritI': 28, 'Thrust': 14, 'RisingSlash': 18,
              'SpiritII': 30, 'SpiritIII': 12, 'SpiritRoundslash': 38, 'SpiritStepSlash': 22,
              'SpiritThrust': 18, 'ForesightSlash': 26, 'IaiSlash': 16, 'IaiSpiritSlash': 42}
    for move_id, source in mapping['moves'].items():
        definition = unreal.MHWIMoveDefinition()
        montage = montage_for(move_id, source['clip'])
        definition.set_editor_property('display_name', unreal.Text(move_id))
        definition.set_editor_property('montage', montage)
        length = montage.get_play_length()
        if move_id in ['SpiritThrust', 'ForesightSlash', 'FadeSlashLeft', 'FadeSlashRight']:
            expected = source['source_frames'] / 60.0
            if abs(length - expected) > 0.001:
                raise RuntimeError('Replace M_%s slot segment with A_%s (%.4fs) through MCP before moveset()'
                                   % (move_id, source['clip'], expected))
        windows = []
        for start, end in source['collision_active_frames']:
            if move_id in ['SpiritHelmBreaker', 'HelmLand', 'IaiSpiritSlashWhite', 'IaiSpiritSlashYellow', 'IaiSpiritSlashRed']:
                continue
            hit = unreal.MHWIHitWindow()
            hit.set_editor_property('start_time', start / 60.0)
            hit.set_editor_property('end_time', end / 60.0)
            hit.set_editor_property('damage', float(damage.get(move_id, 15)))
            hit.set_editor_property('spirit_gain', 9.0 if not move_id.startswith('Spirit') and not move_id.startswith('IaiSpirit') else 0.0)
            windows.append(hit)
        definition.set_editor_property('damage_windows', windows)
        final_hit = max((pair[1] / 60.0 for pair in source['collision_active_frames']), default=length * 0.45)
        # Source input-bit meanings are not fully decoded: these are explicit local adapter values.
        definition.set_editor_property('cancel_start', min(length - 0.08, final_hit + 2.0 / 60.0))
        definition.set_editor_property('cancel_end', max(0.0, length - 0.03))
        speeds = source.get('source_motion_speed', [])
        if speeds:
            definition.set_editor_property('source_play_rates', {float(f) / 60.0: float(rate) for f, rate in speeds[0]})
        definitions[move_id] = definition
        authored.append(dict(move=move_id, clip=source['clip'], length=length,
                             windows=source['collision_active_frames'], mapping_status=source['mapping_status']))
    for name, clip, common in [('Draw', 'w03_00_002', False), ('Sheathe', 'w03_00_003', False),
                               ('Roll', 'w03_00_011', False), ('RollSheathed', 'co00_00_130', True)]:
        definition = unreal.MHWIMoveDefinition()
        montage = montage_for(name, clip, common)
        definition.set_editor_property('display_name', unreal.Text(name))
        definition.set_editor_property('montage', montage)
        definition.set_editor_property('cancel_start', max(0.0, montage.get_play_length() * 0.68))
        definition.set_editor_property('cancel_end', max(0.0, montage.get_play_length() - 0.03))
        if name.startswith('Roll'):
            definition.set_editor_property('invulnerable', True)
            definition.set_editor_property('counter_start', 0.06)
            definition.set_editor_property('counter_end', 0.4)
            definition.set_editor_property('unsheath_at_start', False)
        if name == 'Sheathe':
            definition.set_editor_property('sheath_at_end', True)
            definition.set_editor_property('unsheath_at_start', False)
        definitions[name] = definition
    definitions['Roll'].set_editor_property('sheathed_montage', definitions['RollSheathed'].get_editor_property('montage'))
    # Drawn roll recovery Light enters the dedicated 129->101 step slash. While a
    # sheathed Roll is still active, the low-priority non-drawn fallback routes the
    # same Light input to DrawSlash instead of swallowing it; A matches drawn first.
    definitions['Roll'].set_editor_property('routes', [route('Light', 'RollStepSlash', drawn=True),
        route('Light', 'DrawSlash')])
    definitions['Roll'].set_editor_property('turn_start_time', 0.0)
    definitions['Roll'].set_editor_property('turn_end_time', 0.0)
    definitions['Roll'].set_editor_property('turn_max_angle', 0.0)
    definitions['Roll'].set_editor_property('turn_speed', 360.0)
    definitions['DrawSlash'] = definitions['StepSlash'].copy()
    definitions['DrawSlash'].set_editor_property('display_name', unreal.Text('Draw Slash'))
    for name in ['StepSlash', 'DrawSlash', 'OverheadSlash', 'RisingSlash', 'Thrust', 'IaiSlash']:
        light = 'Thrust' if name == 'OverheadSlash' else ('RisingSlash' if name == 'Thrust' else 'OverheadSlash')
        # Project RMB cycle: Thrust <-> RisingSlash. Other moves still enter Thrust.
        thrust = 'RisingSlash' if name == 'Thrust' else 'Thrust'
        definitions[name].set_editor_property('routes', [route('Light', light), route('Thrust', thrust),
            route('Spirit', 'SpiritI'), route('HelmBreaker', 'SpiritThrust')])
    for name in ['FadeSlash', 'FadeSlashLeft', 'FadeSlashRight']:
        definitions[name].set_editor_property('routes', [route('Light', 'RisingSlash'), route('Thrust', 'Thrust'),
            route('Spirit', 'SpiritStepSlash'), route('HelmBreaker', 'SpiritThrust')])
        # The three fade clips already carry their own lateral root motion. Their entry
        # direction is chosen from camera-relative input before selection, so no extra
        # programmatic turn may rotate that displacement afterwards (project tuning).
        definitions[name].set_editor_property('turn_start_time', 0.0)
        definitions[name].set_editor_property('turn_end_time', 0.0)
        definitions[name].set_editor_property('turn_max_angle', 0.0)
        definitions[name].set_editor_property('turn_speed', 360.0)
    for name, following in [('SpiritI', 'SpiritII'), ('SpiritII', 'SpiritIII'), ('SpiritIII', 'SpiritRoundslash'), ('SpiritStepSlash', 'SpiritIII')]:
        light = 'SpiritComboThrust' if name == 'SpiritI' else (
            'SpiritComboRisingSlash' if name == 'SpiritII' else 'Thrust')
        routes = [route('Spirit', following), route('Light', light)]
        if name in ['SpiritI', 'SpiritII']:
            routes.append(route('Thrust', light))
        definitions[name].set_editor_property('routes', routes)
        definitions[name].set_editor_property('spirit_cost', 12.0)
    definitions['SpiritRoundslash'].set_editor_property('spirit_cost', 12.0)
    definitions['SpiritRoundslash'].set_editor_property('raise_spirit_on_hit', True)
    definitions['SpiritRoundslash'].set_editor_property('sheath_at_end', True)
    foresight = definitions['ForesightSlash']
    foresight.set_editor_property('counter', True)
    foresight.set_editor_property('require_nonzero_gauge', True)
    foresight.set_editor_property('consume_all_gauge', True)
    foresight.set_editor_property('counter_start', 8.0 / 60.0)
    foresight.set_editor_property('counter_end', 42.0 / 60.0)
    foresight.set_editor_property('routes', [route('Spirit', 'SpiritRoundslash', hit=True, counter=True), route('Light', 'OverheadSlash')])
    # Shared default entry turn (project tuning), plus the separate return-slash window.
    # Source frames 46..68 are the project-chosen return swing; 45 degrees total.
    foresight.set_editor_property('turn_start_time', 0.0)
    foresight.set_editor_property('turn_end_time', 0.12)
    foresight.set_editor_property('turn_max_angle', 25.0)
    foresight.set_editor_property('turn_speed', 360.0)
    foresight.set_editor_property('return_turn_start_time', 46.0 / 60.0)
    foresight.set_editor_property('return_turn_end_time', 68.0 / 60.0)
    foresight.set_editor_property('return_turn_max_angle', 45.0)
    # Insertion identities reuse the checked 105/107 main montages. Their connector
    # frames (118/121/124) are project blends and own no damage window.
    for combo, base, light, thrust, spirit in [
            ('SpiritComboThrust', 'Thrust', 'RisingSlash', 'RisingSlash', 'SpiritII'),
            ('SpiritComboRisingSlash', 'RisingSlash', 'OverheadSlash', 'Thrust', 'SpiritIII')]:
        combo_definition = definitions[base].copy()
        combo_definition.set_editor_property('display_name', unreal.Text(combo))
        combo_definition.set_editor_property('routes', [route('Light', light), route('Thrust', thrust),
            route('Spirit', spirit)])
        combo_definition.set_editor_property('auto_follow_up', 'None')
        combo_definition.set_editor_property('auto_follow_up_on_hit', 'None')
        combo_definition.set_editor_property('auto_follow_up_time', 0.0)
        combo_definition.set_editor_property('spirit_cost', 0.0)
        definitions[combo] = combo_definition
        authored.append(dict(move=combo, clip=('w03_00_105' if base == 'Thrust' else 'w03_00_107'),
                             reused_montage='M_' + base,
                             mapping_status='project_insertion_identity_reuses_checked_main_montage',
                             connection_frames='project blend only; connector clips 118/121/124 add no damage window'))
    # Drawn Roll Light exit. M_RollStepSlash is a composite (129 then trimmed 101);
    # the segment write is an explicit MCP step, so this authoring stage only fills
    # timings that match an already-composited montage.
    roll_montage = montage_for('RollStepSlash', 'w03_00_129')
    roll_slash = unreal.MHWIMoveDefinition()
    roll_slash.set_editor_property('display_name', unreal.Text('Roll Step Slash'))
    roll_slash.set_editor_property('montage', roll_montage)
    roll_slash.set_editor_property('routes', [route('Light', 'OverheadSlash')])
    roll_length = roll_montage.get_play_length()
    if abs(roll_length - 2.183333333333333) < 0.001:
        roll_hit = unreal.MHWIHitWindow()
        roll_hit.set_editor_property('start_time', 0.6)
        roll_hit.set_editor_property('end_time', 0.7833333333333333)
        roll_hit.set_editor_property('damage', 26.0)
        roll_hit.set_editor_property('spirit_gain', 9.0)
        roll_slash.set_editor_property('damage_windows', [roll_hit])
        roll_slash.set_editor_property('cancel_start', 0.8166666666666667)
        roll_slash.set_editor_property('cancel_end', 2.1533333333333333)
        roll_segments = 'composited_129_0_29_then_101_48_150'
    else:
        # Base montage is still clip 129 alone; do not author hit timing beyond its end.
        roll_slash.set_editor_property('damage_windows', [])
        roll_slash.set_editor_property('cancel_start', max(0.0, roll_length * 0.68))
        roll_slash.set_editor_property('cancel_end', max(0.0, roll_length - 0.03))
        roll_segments = 'pending_mcp_add_montage_segment_101_48_150'
    definitions['RollStepSlash'] = roll_slash
    authored.append(dict(move='RollStepSlash', clip='w03_00_129', montage_length=roll_length,
                         segments=roll_segments,
                         mapping_status='project_roll_light_link_129_into_101',
                         damage_windows=([[0.6, 0.7833333333333333]]
                                         if roll_segments.startswith('composited') else []),
                         note='damage/cancel offsets are relative to the 29-frame 129 segment plus the 101 entry trim'))

    special = definitions['SpecialSheathe']
    special.set_editor_property('holds_special_sheath', True)
    special.set_editor_property('special_sheath_hold_time', 73.0 / 60.0)
    special.set_editor_property('cancel_start', 63.0 / 60.0)
    special.set_editor_property('routes', [route('Light', 'IaiSlash'), route('Spirit', 'IaiSpiritSlash'), route('Evade', 'Roll')])
    iai = definitions['IaiSpiritSlash']
    iai.set_editor_property('counter', True)
    iai.set_editor_property('counter_only_for_iai', True)
    iai.set_editor_property('counter_start', 0.0)
    iai.set_editor_property('counter_end', 13.0 / 60.0)
    iai.set_editor_property('spend_spirit_level', True)
    iai.set_editor_property('preserve_level_on_counter', True)
    iai.set_editor_property('spirit_level_montages', {i: definitions[name].get_editor_property('montage') for i, name in enumerate(
        ['IaiSpiritSlash', 'IaiSpiritSlashWhite', 'IaiSpiritSlashYellow', 'IaiSpiritSlashRed'])})
    iai.set_editor_property('empowered_source_play_rates', {0.0: 1.0, 23.0 / 60.0: 2.0, 40.0 / 60.0: 1.0})
    iai.set_editor_property('routes', [route('Spirit', 'SpiritIII'), route('HelmBreaker', 'SpiritThrust')])
    thrust = definitions['SpiritThrust']
    thrust.set_editor_property('require_spirit_level', True)
    thrust.set_editor_property('auto_follow_up', 'None')
    thrust.set_editor_property('auto_follow_up_on_hit', 'HelmRise')
    # Clip 170 collision ends at source frame 97, so the automatic rise starts there.
    thrust.set_editor_property('auto_follow_up_time', 97.0 / 60.0)
    definitions['HelmRise'].set_editor_property('use_full_root_motion', True)
    definitions['HelmRise'].set_editor_property('auto_follow_up', 'HelmAir')
    definitions['HelmRise'].set_editor_property('auto_follow_up_time',
        max(0.0, definitions['HelmRise'].get_editor_property('montage').get_play_length() - 0.04))
    # Air/Strike/Land are driven by the runtime air phase: no automatic exit and no
    # generic cancel. Only Rise keeps full root motion. Air/Strike may aim during the
    # first 25 source frames (project tuning), which is also the strike start time.
    for name in ['HelmAir', 'SpiritHelmBreaker', 'HelmLand']:
        definition = definitions[name]
        definition.set_editor_property('use_full_root_motion', False)
        definition.set_editor_property('auto_follow_up', 'None')
        definition.set_editor_property('auto_follow_up_on_hit', 'None')
        definition.set_editor_property('auto_follow_up_time', 0.0)
        definition.set_editor_property('cancel_start', 9999.0)
        definition.set_editor_property('cancel_end', 9999.0)
    for name in ['HelmAir', 'SpiritHelmBreaker']:
        definitions[name].set_editor_property('turn_start_time', 0.0)
        definitions[name].set_editor_property('turn_end_time', 25.0 / 60.0)
        definitions[name].set_editor_property('turn_max_angle', 120.0)
        definitions[name].set_editor_property('turn_speed', 720.0)
    # Original helm-breaker uses delayed shell damage. Model its seven commits at landing,
    # rather than pretending the single broad source collision interval means seven blade sweeps.
    seven = []
    for frame in [3, 5, 7, 9, 11, 13, 15]:
        hit = unreal.MHWIHitWindow()
        hit.set_editor_property('start_time', frame / 60.0)
        hit.set_editor_property('end_time', (frame + 0.5) / 60.0)
        hit.set_editor_property('damage', 20.0)
        hit.set_editor_property('spirit_gain', 0.0)
        seven.append(hit)
    definitions['HelmLand'].set_editor_property('damage_windows', seven)
    definitions['HelmLand'].set_editor_property('spend_spirit_level', True)
    # Apply the same source-qualified B01 fields as the targeted migration.
    # This pass does not infer missing native timings or rebuild animation links.
    import author_reference_basics
    definitions, _native_basics = author_reference_basics.apply_to_copies(definitions)
    import author_spirit_branches
    definitions, _native_branches = author_spirit_branches.apply_to_copies(definitions)
    data.set_editor_property('moves', definitions)
    for name, path in [('idle', 'LongSword/A_w03_00_001'), ('walk', 'LongSword/A_w03_00_004'),
                       ('run', 'LongSword/A_w03_00_004'), ('sheathed_idle', 'Common/A_co00_00_001'),
                       ('sheathed_walk', 'Common/A_co00_00_203'), ('sheathed_run', 'Common/A_co00_00_090')]:
        import author_locomotion_fidelity
        sequence = author_locomotion_fidelity.preferred(asset(ROOT_ASSET + '/Animations/' + path))
        sequence.set_editor_property('enable_root_motion', False)
        sequence.set_editor_property('force_root_lock', True)
        sequence.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
        unreal.EditorAssetLibrary.save_loaded_asset(sequence)
        data.set_editor_property(name, sequence)
        if name in ['sheathed_walk', 'sheathed_run']:
            source_speed = mapping['sheathed_locomotion']['source_speed_cm_s']['walk' if name == 'sheathed_walk' else 'run']
            speed = data.get_editor_property('walk_speed' if name == 'sheathed_walk' else 'run_speed')
            sequence.set_editor_property('rate_scale', speed / source_speed)
            unreal.EditorAssetLibrary.save_loaded_asset(sequence)
    unreal.EditorAssetLibrary.save_loaded_asset(data)
    (OUT / 'moveset-authoring.json').write_text(json.dumps(dict(moves=authored, adapter_notes=[
        'Cancel/counter/iframes are explicit project tuning, not decoded original flags',
        'Source mMotionSpeed keys use local linear interpolation',
        'Seven delayed helm commits are represented in landing montage',
        'CharacterMovement locomotion; locked sequence root, montage-only attack root motion',
        'SpiritThrust maps to clip 170/node45/ActionNo87; ForesightSlash maps to clip 140/node28/ActionNo86; replace both montage segments through MCP before runtime use',
        'SpiritComboThrust/SpiritComboRisingSlash reuse M_Thrust/M_RisingSlash; connector frames are project blends and own no damage window',
        'RollStepSlash requires M_RollStepSlash to be composited from 129 frames 0..29 then 101 frames 48..150; data timings shift by 29/60 plus the 101 trim']), indent=2), encoding='utf-8')
    import author_locomotion_fidelity
    author_locomotion_fidelity.run(save=True, report_name='base-authoring.json')
    return dict(data=data.get_path_name(), moves=len(definitions))


def blueprint(name, parent):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property('parent_class', parent)
    value = create(name, 'Blueprints', unreal.Blueprint, factory)
    unreal.BlueprintEditorLibrary.compile_blueprint(value)
    return value


def character():
    hunter = asset(ROOT_ASSET + '/Character/SK_MHWI_Hunter')
    abp = asset(ROOT_ASSET + '/Blueprints/ABP_MHWI_Hunter')
    bp = blueprint('BP_MHWI_Hunter', unreal.MHWICharacter)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('moveset', asset(ROOT_ASSET + '/Data/DA_MHWI_LongSword'))
    cdo.get_editor_property('mesh').set_skeletal_mesh_asset(hunter)
    cdo.get_editor_property('mesh').set_anim_instance_class(abp.generated_class())
    cdo.get_editor_property('weapon_mesh').set_skeletal_mesh_asset(asset(ROOT_ASSET + '/Weapons/SK_MHWI_LongSword'))
    cdo.get_editor_property('scabbard_mesh').set_skeletal_mesh_asset(asset(ROOT_ASSET + '/Weapons/SK_MHWI_Scabbard'))
    attachment_defaults(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    gm = blueprint('BP_MHWI_TrainingGameMode', unreal.GameModeBase)
    defaults = unreal.get_default_object(gm.generated_class())
    defaults.set_editor_property('default_pawn_class', bp.generated_class())
    defaults.set_editor_property('hud_class', unreal.MHWIHUD)
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    unreal.EditorAssetLibrary.save_loaded_asset(gm)
    return dict(character=bp.get_path_name(), game_mode=gm.get_path_name())


def stage_material(name, color):
    mat = create(name, 'Materials', unreal.Material, unreal.MaterialFactoryNew())
    edit = unreal.MaterialEditingLibrary
    edit.delete_all_material_expressions(mat)
    node = edit.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
    node.set_editor_property('constant', unreal.LinearColor(*color))
    edit.connect_material_property(node, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = edit.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.set_editor_property('r', 0.8)
    edit.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    edit.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def training_map():
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    path = ROOT_ASSET + '/Maps/L_MHWI_Training'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if not editor.load_level(path):
            raise RuntimeError('Could not load MHWI training map')
        return dict(map=path, already_exists=True)
    if not editor.new_level(path):
        raise RuntimeError('Could not create MHWI training map')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    gm = asset(ROOT_ASSET + '/Blueprints/BP_MHWI_TrainingGameMode')
    world.get_world_settings().set_editor_property('default_game_mode', gm.generated_class())
    ground = stage_material('M_MHWI_TrainingGround', (0.085, 0.11, 0.105, 1))
    target_material = stage_material('M_MHWI_TrainingTarget', (0.34, 0.19, 0.075, 1))

    def spawn(cls, label, position, rotation=None):
        actor = actors.spawn_actor_from_class(cls, unreal.Vector(*position), rotation or unreal.Rotator())
        if not actor:
            raise RuntimeError('Could not spawn ' + label)
        actor.set_actor_label(label)
        return actor

    floor = spawn(unreal.StaticMeshActor, 'MHWI_Floor', (0, 0, -10))
    floor.static_mesh_component.set_static_mesh(asset('/Engine/BasicShapes/Cube'))
    floor.static_mesh_component.set_material(0, ground)
    floor.set_actor_scale3d(unreal.Vector(45, 45, 0.2))
    spawn(unreal.PlayerStart, 'MHWI_PlayerStart', (0, 0, 110))
    sun = spawn(unreal.DirectionalLight, 'MHWI_Sun', (0, 0, 1000), unreal.Rotator(pitch=-50, yaw=-30))
    sun.light_component.set_editor_property('intensity', 5.0)
    sun.light_component.set_editor_property('light_color', unreal.Color(255, 240, 210, 255))
    sky = spawn(unreal.SkyLight, 'MHWI_SkyLight', (0, 0, 300))
    sky.light_component.set_editor_property('intensity', 1.5)
    sky.light_component.set_editor_property('light_color', unreal.Color(180, 205, 230, 255))
    spawn(unreal.SkyAtmosphere, 'MHWI_Atmosphere', (0, 0, 0))
    spawn(unreal.ExponentialHeightFog, 'MHWI_Fog', (0, 0, 0))
    for i, position in enumerate([(430, 0, 90), (300, -400, 90), (650, 400, 90)]):
        target = spawn(unreal.MHWITrainingTarget, 'MHWI_CounterTarget' if i == 0 else f'MHWI_Target_{i}', position)
        # Ordinary animation/combos practice must not receive invisible periodic damage.
        # Counter practice is an explicit per-target EnableAttacks opt-in.
        target.set_editor_property('enable_attacks', False)
        target.get_editor_property('target_mesh').set_material(0, target_material)
    header = spawn(unreal.TextRenderActor, 'MHWI_TrainingSign', (950, 0, 240), unreal.Rotator(yaw=180))
    text = header.text_render
    text.set_text(unreal.Text('MHWI  /  LONGSWORD TRAINING'))
    text.set_world_size(32.0)
    text.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    editor.save_current_level()
    return dict(map=path, player_start=[0, 0, 110], targets=3)


def passive_training_targets():
    """CHG-005: update the existing training level without rebuilding its contents."""
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert not level.is_in_play_in_editor(), 'Stop PIE before changing saved map defaults'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world and world.get_path_name().startswith(ROOT_ASSET + '/Maps/L_MHWI_Training.'), 'Open the training map first'
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    targets = [a for a in actors if isinstance(a, unreal.MHWITrainingTarget)]
    assert len(targets) == 3, 'Expected the three existing MHWI targets'
    changes = []
    for target in targets:
        before = target.get_editor_property('enable_attacks')
        target.set_editor_property('enable_attacks', False)
        changes.append({'actor': target.get_path_name(), 'label': target.get_actor_label(),
                        'before': before, 'after': target.get_editor_property('enable_attacks')})
    assert level.save_current_level(), 'Training level save failed'
    (OUT/'training-passive-authoring.json').write_text(json.dumps(changes, indent=2), encoding='utf8')
    return changes


def polish():
    for name in ['BS_MHWI_Drawn', 'BS_MHWI_Sheathed']:
        blend = asset(ROOT_ASSET + '/Animations/' + name)
        blend.set_editor_property('target_weight_interpolation_speed_per_sec', 8.0)
        blend.set_editor_property('target_weight_interpolation_ease_in_out', True)
        parameters = blend.get_editor_property('interpolation_param')
        parameters[0].set_editor_property('interpolation_time', 0.14)
        parameters[0].set_editor_property('damping_ratio', 1.0)
        blend.set_editor_property('interpolation_param', parameters)
        unreal.EditorAssetLibrary.save_loaded_asset(blend)
    bp = asset(ROOT_ASSET + '/Blueprints/ABP_MHWI_Hunter')
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    # Shader propagation can dirty material instances after their individual save.
    unreal.EditorAssetLibrary.save_directory(ROOT_ASSET, only_if_is_dirty=True, recursive=True)
    return dict(polished=True)




def attachment_defaults(blueprint_asset=None):
    """Persist the reviewed, single-source attachment fit to the hunter Blueprint."""
    bp = blueprint_asset or asset(ROOT_ASSET + '/Blueprints/BP_MHWI_Hunter')
    cdo = unreal.get_default_object(bp.generated_class())
    fit = json.loads((ROOT / 'Scripts/MHWI/attachment_fit.json').read_text(encoding='utf-8'))
    backup = {key: str(cdo.get_editor_property(key)) for key in list(fit['bones']) + list(fit['transforms'])}
    backup_file = OUT / 'attachment-defaults-before.json'
    if not backup_file.exists():
        backup_file.write_text(json.dumps(backup, indent=2), encoding='utf-8')
    for key, value in fit['bones'].items():
        cdo.set_editor_property(key, unreal.Name(value))
    for key, value in fit['transforms'].items():
        cdo.set_editor_property(key, unreal.Transform(
            location=unreal.Vector(*value['location']),
            rotation=unreal.Rotator(pitch=value['rotation'][0], yaw=value['rotation'][1], roll=value['rotation'][2]),
            scale=unreal.Vector(*value['scale'])))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    return dict(blueprint=bp.get_path_name(), fit='Scripts/MHWI/attachment_fit.json', bones=fit['bones'])


def animation_corrections():
    """Apply CHG-004 data after explicit MCP montage/BlendSpace segment replacements.

    Kept separate from moveset() to preserve unrelated manual move tuning.
    Requires M_SpiritII -> 106, M_RisingSlash -> 107 and sheathed BS samples 203/090.
    """
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
    mapping = json.loads((ROOT / 'Scripts/MHWI/moveset_mapping.json').read_text(encoding='utf8'))
    data = asset(ROOT_ASSET + '/Data/DA_MHWI_LongSword')
    definitions = data.get_editor_property('moves')
    report = {'moves': {}, 'routes': {}, 'locomotion': {}}
    for name in ['SpiritII', 'RisingSlash']:
        source = mapping['moves'][name]
        sequence = asset(ROOT_ASSET + '/Animations/LongSword/A_' + source['clip'])
        montage = asset(ROOT_ASSET + '/Montages/M_' + name)
        assert abs(montage.get_play_length() - sequence.get_play_length()) < .001, 'Replace montage sequence first: ' + name
        sequence.set_editor_property('enable_root_motion', True)
        sequence.set_editor_property('force_root_lock', False)
        sequence.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
        unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False)
        definition = definitions[name].copy()
        if name == 'SpiritII':
            definition.set_editor_property('spirit_cost', 12.0)
        old_windows = definition.get_editor_property('damage_windows')
        assert old_windows
        windows = []
        for start, end in source['collision_active_frames']:
            window = old_windows[0].copy()
            window.set_editor_property('start_time', start/60.0)
            window.set_editor_property('end_time', end/60.0)
            windows.append(window)
        definition.set_editor_property('damage_windows', windows)
        definition.set_editor_property('cancel_start', min(montage.get_play_length()-.08, max(v[1] for v in source['collision_active_frames'])/60.0+2/60.0))
        definition.set_editor_property('cancel_end', montage.get_play_length()-.03)
        speeds = source.get('source_motion_speed', [])
        definition.set_editor_property('source_play_rates', {f/60.0: r for f, r in speeds[0]} if speeds else {})
        definitions[name] = definition
        report['moves'][name] = {'clip': source['clip'], 'frames': source['collision_active_frames'], 'length': montage.get_play_length()}
    for name in ['StepSlash', 'DrawSlash']:
        definition = definitions[name].copy()
        routes = definition.get_editor_property('routes')
        for i, link in enumerate(routes):
            if link.get_editor_property('input') == unreal.MHWIInput.LIGHT:
                link.set_editor_property('next_move', 'OverheadSlash')
                routes[i] = link
        definition.set_editor_property('routes', routes)
        definitions[name] = definition
        report['routes'][name] = {'Light': 'OverheadSlash'}
    import author_reference_basics
    definitions, _native_basics = author_reference_basics.apply_to_copies(definitions)
    import author_spirit_branches
    definitions, _native_branches = author_spirit_branches.apply_to_copies(definitions)
    data.set_editor_property('moves', definitions)
    for name, number, speed_property, source_speed in [
            ('sheathed_walk', 203, 'walk_speed', 135.0417565734742),
            ('sheathed_run', 90, 'run_speed', 365.51273290259655)]:
        import author_locomotion_fidelity
        seq = author_locomotion_fidelity.preferred(asset(f'{ROOT_ASSET}/Animations/Common/A_co00_00_{number:03}'))
        seq.set_editor_property('enable_root_motion', False)
        seq.set_editor_property('force_root_lock', True)
        seq.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
        seq.set_editor_property('rate_scale', data.get_editor_property(speed_property) / source_speed)
        data.set_editor_property(name, seq)
        unreal.EditorAssetLibrary.save_loaded_asset(seq, only_if_is_dirty=False)
        report['locomotion'][name] = {'sequence': seq.get_path_name(), 'rate': seq.get_editor_property('rate_scale')}
    # Retained former locomotion clips keep their original locking configuration.
    for number in [34, 37]:
        seq = asset(f'{ROOT_ASSET}/Animations/Common/A_co00_00_{number:03}')
        seq.set_editor_property('enable_root_motion', False)
        seq.set_editor_property('force_root_lock', True)
        unreal.EditorAssetLibrary.save_loaded_asset(seq, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False)
    for name in ['BS_MHWI_Sheathed', 'BS_MHWI_Drawn']:
        unreal.EditorAssetLibrary.save_loaded_asset(asset(ROOT_ASSET + '/Animations/' + name))
    bp = asset(ROOT_ASSET + '/Blueprints/ABP_MHWI_Hunter')
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    import author_locomotion_fidelity
    author_locomotion_fidelity.run(save=True, report_name='animation-corrections.json')
    (OUT/'animation-corrections.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    return report
