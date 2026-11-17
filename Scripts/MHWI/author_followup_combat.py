"""B23: remove only the thrust-entry colour gate; preserve the HelmRise gate."""
import json
import shutil
from pathlib import Path
import unreal

ASSET='/Game/MHWI/Data/DA_MHWI_LongSword'

def run(save=False):
    data=unreal.load_asset(ASSET)
    assert isinstance(data, unreal.MHWIMovesetData)
    moves={k:v.copy() for k,v in data.get_editor_property('moves').items()}
    index=next(k for k in moves if str(k)=='SpiritThrust')
    old=bool(moves[index].get_editor_property('require_spirit_level'))
    out=Path(unreal.Paths.project_dir())/'Saved/MHWIRestoration/B23-20261030'
    out.mkdir(parents=True,exist_ok=True)
    report={'asset':data.get_path_name(),'old_require_spirit_level':old,'new_require_spirit_level':False,'saved':False}
    if save and old:
        disk=Path(unreal.Paths.project_content_dir())/'MHWI/Data/DA_MHWI_LongSword.uasset'
        backup=out/'Backup/DA_MHWI_LongSword.uasset'
        backup.parent.mkdir(parents=True,exist_ok=True)
        assert not backup.exists(), 'Do not overwrite original backup'
        shutil.copy2(disk,backup)
        before={k:d.export_text() for k,d in moves.items()}
        updated=moves[index].copy()
        updated.set_editor_property('require_spirit_level',False)
        moves[index]=updated
        data.set_editor_property('moves',moves)
        actual=dict(data.get_editor_property('moves'))
        assert all(d.export_text()==before[i] for i,d in actual.items() if i!=index)
        check=actual[index].copy();check.set_editor_property('require_spirit_level',True)
        assert check.export_text()==before[index], 'Only one field may change'
        assert unreal.EditorAssetLibrary.save_loaded_asset(data,False)
        report['saved']=True
    report['readback_require_spirit_level']=bool(data.get_editor_property('moves')[index].get_editor_property('require_spirit_level'))
    if save: assert not report['readback_require_spirit_level']
    (out/('author-combat-saved.json' if save else 'author-combat-preview.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
