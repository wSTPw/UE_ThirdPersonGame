"""Targeted public-reference defense/resource migration; import is inert.

run(save=False) previews on copied structs. Only the formal moveset is saved.
The production Montage/sequence/route/weapon-event references are retained.
"""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / 'Saved/MHWIImport/CombatFidelity-20261024'
DATA = '/Game/MHWI/Data/DA_MHWI_LongSword'
GENERAL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5HFkHnEP74gD-SCVta9syb9GaF1_nSmMFgV4hxvZt9iu4HmfhGlP2KbnIbC-cAx5kkvsd8L7oB0Uy/pubhtml/sheet?headers=false&gid=82408715'
ATTACKS = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTEYb4wGpijtIpFVopiYl1V83m48d7g1AHmTwOBKJ5RXdlz1sfxCyEmnhbgHLWQsGiXnodyBsUlPzc3/pubhtml/sheet?headers=false&gid=362236353'


def _references(definition):
    result = [definition.get_editor_property(p).get_path_name() if definition.get_editor_property(p) else None
              for p in ('montage', 'sheathed_montage')]
    result += [m.get_path_name() for m in definition.get_editor_property('spirit_level_montages').values()]
    result += [(float(e.get_editor_property('time')), int(e.get_editor_property('motion_no')))
               for e in definition.get_editor_property('weapon_motion_events')]
    return result


def run(save=False):
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before data migration')
    data = unreal.load_asset(DATA)
    if not isinstance(data, unreal.MHWIMovesetData):
        raise RuntimeError('Wrong formal moveset class')
    before = data.get_editor_property('moves')
    definitions = {key: value.copy() for key, value in before.items()}
    by_name = {str(key): key for key in definitions}
    report = {'saved': False, 'utc_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'sources': [GENERAL, ATTACKS], 'moves': {}, 'data': {},
              'boundary': 'No Evade Window/Mantle or full sharpness/hitzone/stun/part-damage model. Route timing is separately authored project tuning.'}

    def configure(name, **values):
        obj = definitions[by_name[name]]
        for key, value in values.items():
            obj.set_editor_property(key, value)
        report['moves'].setdefault(name, {}).update(values)
        return obj

    for key, obj in definitions.items():
        # Migrate rolls without losing their prior project-tuned evade interval.
        configure(str(key), independent_defense_windows=True,
                  invulnerability_start=float(obj.get_editor_property('counter_start')),
                  invulnerability_end=float(obj.get_editor_property('counter_end'))
                    if obj.get_editor_property('invulnerable') else 0.,
                  empowered_invulnerability_end=-1., low_gauge_invulnerability_end=-1.,
                  counter_minimum_gauge=0., counter_hyper_armor_seconds=0.,
                  counter_restores_gauge_on_hit=False, counter_damage_multiplier=1.,
                  gauge_regen_on_hit_seconds=0., counter_gauge_regen_on_hit_seconds=-1.,
                  gauge_regen_on_commit_seconds=0., red_gauge_regen_on_commit_seconds=-1.)

    for name, cost in [('SpiritI', 15.), ('SpiritII', 15.), ('SpiritIII', 20.), ('SpiritRoundslash', 25.)]:
        configure(name, spirit_cost=cost)
    spirit = configure('SpiritI', allow_weak_spirit_attack=True,
                       weak_damage_multiplier=14./26., weak_spirit_gain=10.)
    spirit_windows = list(spirit.get_editor_property('damage_windows'))
    for window in spirit_windows:
        window.set_editor_property('damage', 26.)
        window.set_editor_property('spirit_gain', 10.)
    spirit.set_editor_property('damage_windows', spirit_windows)
    report['moves']['SpiritI']['hit_windows'] = [{'damage': 26., 'spirit_gain': 10.} for _ in spirit_windows]

    configure('ForesightSlash', counter=True, invulnerable=True, counter_only_for_iai=False,
              counter_start=0., counter_end=33./60., invulnerability_start=0., invulnerability_end=45./60.,
              counter_minimum_gauge=10., low_gauge_invulnerability_end=13./60.,
              counter_restores_gauge_on_hit=True, counter_hyper_armor_seconds=1., counter_damage_multiplier=1.3,
              require_nonzero_gauge=False, consume_all_gauge=True, spirit_cost=10.,
              allow_weak_spirit_attack=True, weak_damage_multiplier=12./26., weak_spirit_gain=10.)
    foresight = definitions[by_name['ForesightSlash']]
    foresight_windows = list(foresight.get_editor_property('damage_windows'))
    for window in foresight_windows:
        window.set_editor_property('damage', 26.)
        window.set_editor_property('spirit_gain', 10.)
    foresight.set_editor_property('damage_windows', foresight_windows)
    report['moves']['ForesightSlash']['hit_windows'] = [{'damage': 26., 'spirit_gain': 10.} for _ in foresight_windows]
    configure('IaiSlash', counter=True, counter_only_for_iai=True, invulnerable=True,
              counter_start=0., counter_end=5./60., invulnerability_start=0., invulnerability_end=5./60.,
              counter_hyper_armor_seconds=2., gauge_regen_on_hit_seconds=15., counter_gauge_regen_on_hit_seconds=30.)
    iai = definitions[by_name['IaiSlash']]
    iai_windows = list(iai.get_editor_property('damage_windows'))
    for window in iai_windows:
        window.set_editor_property('spirit_gain', 0.)
    iai.set_editor_property('damage_windows', iai_windows)
    for name in ('IaiSpiritSlash', 'IaiSpiritSlashWhite', 'IaiSpiritSlashYellow', 'IaiSpiritSlashRed'):
        if name in by_name:
            configure(name, counter=True, counter_only_for_iai=True, invulnerable=True,
                      counter_start=0., counter_end=12./60., invulnerability_start=0., invulnerability_end=12./60.,
                      empowered_invulnerability_end=14./60., counter_hyper_armor_seconds=2.,
                      preserve_level_on_counter=True, spend_spirit_level=True)
    configure('SpiritHelmBreaker', gauge_regen_on_commit_seconds=10., red_gauge_regen_on_commit_seconds=15.)

    for key, obj in definitions.items():
        if _references(obj) != _references(before[key]):
            raise RuntimeError('Migration changed animation or weapon event references: ' + str(key))
        if len(obj.get_editor_property('routes')) != len(before[key].get_editor_property('routes')):
            raise RuntimeError('Migration changed routes: ' + str(key))
    report['data'] = {'spirit_level_durations': [0., 195., 135., 60.], 'gauge_regen_per_second': 100./15.,
                      'spirit_decay_pause_on_raise_seconds': 10., 'counter_armor_damage_multiplier': .5}
    if save:
        path = ROOT / 'Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        backup = OUT / 'Backup/Content/MHWI/Data/DA_MHWI_LongSword.uasset'
        if not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
        data.set_editor_property('moves', definitions)
        for key, value in report['data'].items():
            data.set_editor_property(key, value)
        if not unreal.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False):
            raise RuntimeError('Formal moveset save failed')
        report['saved'] = True
        report['asset_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('combat-authored.json' if save else 'combat-preview.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return {'saved': save, 'moves': len(definitions), 'report': str(OUT)}
