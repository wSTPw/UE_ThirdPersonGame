"""Read the affected saved move fields without changing any assets."""
import json
from pathlib import Path
import unreal
data = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
moves = data.get_editor_property('moves')
result = {n: {k: str(moves[n].get_editor_property(k)) for k in
    ['montage', 'spirit_cost', 'spirit_gain_on_start', 'consume_all_gauge', 'damage_windows', 'cancel_start', 'cancel_end']}
    for n in ['DrawSlash', 'OverheadSlash', 'Thrust', 'RisingSlash', 'SpiritI', 'SpiritII', 'SpiritIII', 'SpiritRoundslash']}
Path(unreal.Paths.project_saved_dir(),'MHWIImport/correction-data-readback.json').write_text(json.dumps(result, indent=2), encoding='utf8')

assert float(result['SpiritII']['spirit_cost']) == 12.0, 'Preview leaked into authored data'


def reload_and_verify():
    """Reload only clean affected packages; refuse prompts/unsaved package replacement."""
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
    root = '/Game/MHWI/'
    for number in [39, 89]:
        unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset(f'{root}Animations/Common/A_co00_00_{number:03}'))
    paths = ['Data/DA_MHWI_LongSword', 'Animations/BS_MHWI_Sheathed',
        'Montages/M_SpiritII', 'Montages/M_RisingSlash',
        'Animations/LongSword/A_w03_00_106', 'Animations/LongSword/A_w03_00_107',
        'Animations/Common/A_co00_00_203', 'Animations/Common/A_co00_00_090']
    packages = [unreal.load_asset(root+p).get_outermost() for p in paths]
    status = unreal.EditorLoadingAndSavingUtils.reload_packages(packages, unreal.ReloadPackagesInteractionMode.ASSUME_NEGATIVE)
    report = {'passed': False, 'reload': str(status), 'checks': []}
    def check(ok, label):
        report['checks'].append({'check': label, 'passed': bool(ok)})
        if not ok: raise AssertionError(label)
    try:
        check(status[0] and not str(status[1]), 'clean affected packages reload from disk')
        data = unreal.load_asset(root+'Data/DA_MHWI_LongSword'); moves = data.get_editor_property('moves')
        check(abs(moves['SpiritII'].get_editor_property('spirit_cost')-12) < .001, 'formal SpiritII cost remains 12 after safe preview and disk reload')
        for name, seconds in [('SpiritII', 2), ('RisingSlash', 136/60)]:
            check(abs(moves[name].get_editor_property('montage').get_play_length()-seconds) < .001, name+' montage duration persists')
        for name in ['StepSlash', 'DrawSlash']:
            links = moves[name].get_editor_property('routes')
            check(any(link.get_editor_property('input') == unreal.MHWIInput.LIGHT and str(link.get_editor_property('next_move')) == 'OverheadSlash' for link in links), name+' left-click route persists')
        for prop, number, rate in [('sheathed_walk', 203, 1.33292105), ('sheathed_run', 90, 1.14907078)]:
            seq = data.get_editor_property(prop)
            check(seq.get_name() == f'A_co00_00_{number:03}', prop+' sequence persists')
            check(abs(seq.get_editor_property('rate_scale')-rate) < .0001, prop+' speed matching persists')
            check(not seq.get_editor_property('enable_root_motion') and seq.get_editor_property('force_root_lock') and seq.get_editor_property('root_motion_root_lock') == unreal.RootMotionRootLock.REF_POSE, prop+' locomotion root configuration persists')
        report['passed'] = True
    finally:
        Path(unreal.Paths.project_saved_dir(),'MHWIImport/animation-persistence.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    return report
