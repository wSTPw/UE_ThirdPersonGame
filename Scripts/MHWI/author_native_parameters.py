"""Batch-apply only named, supported W03P values to the existing formal DA.

All rules carry source field/offset/conversion. Anonymous physics blocks, raw
input flags, delayed shell scheduling and native IK are deliberately not guessed.
"""
from pathlib import Path
import hashlib
import json
import shutil

import extract_native_longsword_params as native

ROOT = native.ROOT
OUT = ROOT / 'Saved/MHWIImport/NativeParameterResearch-20261024'
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'


def reference_guard(moves):
    result = {}
    for name, value in moves.items():
        montages = [value.get_editor_property(key) for key in ('montage', 'sheathed_montage')]
        montages += list(value.get_editor_property('spirit_level_montages').values())
        result[str(name)] = dict(montages=[m.get_path_name() if m else None for m in montages],
            weapons=[(e.get_editor_property('time'), e.get_editor_property('motion_no'))
                     for e in value.get_editor_property('weapon_motion_events')],
            routes=[(str(r.get_editor_property('input')), str(r.get_editor_property('next_move')),
                     r.get_editor_property('require_hit'), r.get_editor_property('require_counter'),
                     r.get_editor_property('require_drawn'), r.get_editor_property('cancel_start'),
                     r.get_editor_property('cancel_end'), r.get_editor_property('require_full_spirit_cost'))
                    for r in value.get_editor_property('routes')])
    return result


def run(save=False):
    import unreal
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before importing native parameters')
    source = native.run()
    fields = {row['path']: row for row in source['fields']}
    data = unreal.load_asset(DATA)
    original = data.get_editor_property('moves')
    moves = {key: value.copy() for key, value in original.items()}
    names = {str(key): key for key in moves}
    before_guard = reference_guard(original)
    mutations, globals_to_write = [], {}

    def change(move, prop, field, conversion='identity'):
        raw = fields[field]['value']
        value = float(format(raw * 100., '.7g')) if conversion == 'fraction_to_percent_f32_7digits' else raw
        target = moves[names[move]] if move else data
        previous = target.get_editor_property(prop)
        if move:
            target.set_editor_property(prop, value)
        else:
            globals_to_write[prop] = value
        mutations.append(dict(move=move, property=prop, source_field=field, source_offset=fields[field]['offset'],
                              raw_value=raw, conversion=conversion, value=value, previous=previous))

    percent = 'fraction_to_percent_f32_7digits'
    for move, field in [('SpiritI','Spirit_Blade_1_Cost'), ('SpiritII','Spirit_Blade_2_Cost'),
                        ('SpiritIII','Spirit_Blade_3_Cost'), ('SpiritRoundslash','Spirit_Round_Slash_Cost'),
                        ('SpiritStepSlash','Spirit_Jumping_Slash_Cost')]:
        change(move, 'spirit_cost', field, percent)
    gauge = 'Gauge_Required_to_Active_Foresight_That_Gives_45_I_Frames'
    change('ForesightSlash', 'counter_minimum_gauge', gauge, percent)
    change('ForesightSlash', 'spirit_cost', gauge, percent)
    change('ForesightSlash', 'counter_damage_multiplier', 'Foresight_Slash_Damage_Multiplier_on_Successful_Evasion')
    change('ForesightSlash', 'counter_hyper_armor_seconds', 'Foresight_Slash_Super_Armor_Time_on_Successful_Evasion')
    for move in ['IaiSlash','IaiSpiritSlash','IaiSpiritSlashWhite','IaiSpiritSlashYellow','IaiSpiritSlashRed']:
        if move in names:
            change(move,'counter_hyper_armor_seconds','Iai_Super_Armor_on_Successful_Counter')
    change('IaiSlash','gauge_regen_on_hit_seconds','Spirit_Regeneration_After_Iai_Slash_Duration_in_Seconds_')
    change('IaiSlash','counter_gauge_regen_on_hit_seconds','Spirit_Regeneration_After_Timed_Iai_Slash_Duration_in_Seconds_')
    change('SpiritHelmBreaker','gauge_regen_on_commit_seconds','Spirit_Regeneration_Duration_After_Helm_Breaker_In_Seconds_')
    change('SpiritHelmBreaker','red_gauge_regen_on_commit_seconds','Spirit_Regeneration_After_Red_Gauge_Spirit_Helm_Breaker_Duration_in_Seconds_')
    change(None,'special_sheath_hold_seconds','Iai_Sheathed_Time')
    change(None,'spirit_decay_pause_on_raise_seconds','Gauge_No_Decay_Time_after_Spirit_Gauge_Upgrade')
    duration_fields = ['Gauge_Duration_White','Gauge_Duration_Yellow','Gauge_Duration_Red']
    globals_to_write['spirit_level_durations'] = [0.] + [fields[name]['value'] for name in duration_fields]
    regen_fields = [row for key,row in fields.items() if key.startswith('Spirit_Regeneration_After_') and '_Regen_Lower_' in key]
    denominators = {row['value'] for row in regen_fields}
    if len(regen_fields) != 4 or len(denominators) != 1 or next(iter(denominators)) <= 0:
        raise RuntimeError('One shared supported regen period no longer fits the native file; implement per-effect periods first')
    globals_to_write['gauge_regen_per_second'] = 100. / next(iter(denominators))
    if reference_guard(moves) != before_guard:
        raise RuntimeError('Parameter import must preserve animation, weapon and input routing')
    report = dict(schema=1, saved=False, source_sha256=source['source_sha256'], mutations=mutations,
                  globals=globals_to_write, source_layout=source['upstream']['commit'],
                  globals_previous={key: (list(data.get_editor_property(key)) if isinstance(value,list)
                                          else data.get_editor_property(key)) for key,value in globals_to_write.items()},
                  derived_sources={'spirit_level_durations': [fields[key] for key in duration_fields],
                                   'gauge_regen_per_second': {'formula': '100 / common native regen period', 'fields': regen_fields}},
                  preserved='Montage/sequence/weapon events/routes; separate defense window durations remain from their independently qualified evidence.',
                  not_applied=['Anonymous ActionParam block-to-action mapping', 'Iai speed consumer and quick-sheathe integration',
                               'Helmbreaker shell delay scheduling', 'IK solver and equipment attachment',
                               'Raw input mask/trigger consumption semantics'])
    if save:
        asset = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup = OUT / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        if not backup.exists():
            backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(asset, backup)
        data.set_editor_property('moves',moves)
        for key,value in globals_to_write.items():
            data.set_editor_property(key,value)
        if not unreal.EditorAssetLibrary.save_loaded_asset(data,only_if_is_dirty=False):
            raise RuntimeError('Native parameter save failed')
        if reference_guard(data.get_editor_property('moves')) != before_guard:
            raise RuntimeError('Saved reference guard failed')
        for row in mutations:
            obj = data.get_editor_property('moves')[names[row['move']]] if row['move'] else data
            actual = float(obj.get_editor_property(row['property']))
            if abs(actual-row['value']) > 1e-5:
                raise RuntimeError('Parameter readback mismatch: '+row['property'])
        for key, expected in globals_to_write.items():
            actual = data.get_editor_property(key)
            if isinstance(expected, list):
                if len(actual) != len(expected) or any(abs(a-b) > 1e-5 for a,b in zip(actual,expected)):
                    raise RuntimeError('Global array readback mismatch: '+key)
            elif abs(actual-expected) > 1e-5:
                raise RuntimeError('Global scalar readback mismatch: '+key)
        report.update(saved=True,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest())
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/('native-parameters-authored.json' if save else 'native-parameters-preview.json')).write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return dict(saved=save,move_properties=sum(r['move'] is not None for r in mutations),
                global_properties=len(globals_to_write),source_sha256=source['source_sha256'])
