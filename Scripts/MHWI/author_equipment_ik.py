"""Create/read back the project-only R30 IK profile and bind it to the ABP CDO."""
import json
from pathlib import Path

import unreal

ASSET_PATH = '/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile'
ABP_PATH = '/Game/MHWI/Blueprints/ABP_MHWI_Hunter'
OUT = Path(unreal.Paths.project_saved_dir(), 'MHWIRestoration/B19-20261026/equipment-ik-profile.json')


def set_chain(profile, field, root, mid, end):
    chain = profile.get_editor_property(field).copy()
    chain.set_editor_property('root_bone', unreal.Name(root))
    chain.set_editor_property('mid_bone', unreal.Name(mid))
    chain.set_editor_property('end_bone', unreal.Name(end))
    profile.set_editor_property(field, chain)


def run():
    profile = unreal.load_asset(ASSET_PATH)
    if not profile:
        profile = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'DA_MHWI_EquipmentIK_Profile', '/Game/MHWI/Data',
            unreal.MHWIEquipmentIKProfile, unreal.DataAssetFactory())
    if not profile:
        raise RuntimeError('Unable to create ' + ASSET_PATH)
    set_chain(profile, 'left_arm', 'bone_006', 'bone_007', 'bone_008')
    set_chain(profile, 'right_arm', 'bone_010', 'bone_011', 'bone_012')
    set_chain(profile, 'left_foot', 'bone_014', 'bone_015', 'bone_016')
    set_chain(profile, 'right_foot', 'bone_018', 'bone_019', 'bone_020')
    profile.set_editor_property('foot_trace_up', 35.0)
    profile.set_editor_property('foot_trace_down', 65.0)
    profile.set_editor_property('foot_sole_offset_z', 0.0)
    profile.set_editor_property('arm_alpha', 1.0)
    profile.set_editor_property('foot_alpha', 1.0)
    if not unreal.EditorAssetLibrary.save_asset(ASSET_PATH, only_if_is_dirty=False):
        raise RuntimeError('Profile save failed')

    blueprint_class = unreal.load_class(None, ABP_PATH + '.' + ABP_PATH.rsplit('/', 1)[-1] + '_C')
    if not blueprint_class:
        raise RuntimeError('ABP generated class not found')
    cdo = unreal.get_default_object(blueprint_class)
    cdo.set_editor_property('equipment_ik_profile', profile)
    unreal.BlueprintEditorLibrary.compile_blueprint(unreal.load_asset(ABP_PATH))
    if not unreal.EditorAssetLibrary.save_asset(ABP_PATH, only_if_is_dirty=False):
        raise RuntimeError('ABP save failed')

    report = {'passed': True, 'profile': ASSET_PATH,
              'chains': {field: {key: str(profile.get_editor_property(field).get_editor_property(key))
                                 for key in ('root_bone', 'mid_bone', 'end_bone')}
                         for field in ('left_arm', 'right_arm', 'left_foot', 'right_foot')},
              'cdo_profile': str(cdo.get_editor_property('equipment_ik_profile'))}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
