"""Import authored R06 clips into an isolated /Game/MHWI library, no tests.

No production montage/DataAsset replacement. Never overwrite existing packages.
Records authoring results only; asset fidelity/runtime acceptance is a later phase.
"""
import json
from pathlib import Path


def run(manifest_relative='ArtSource/ThirdParty/MHWLongSword/R06Staging-20261025/export-manifest.json',
        journal_relative='Saved/MHWIRestoration/B07-20261025/r06-import-journal.json',
        destination='/Game/MHWI/Animations/R06Staging'):
    import unreal
    from import_assets import fbx_options
    root = Path(unreal.Paths.project_dir()).resolve()
    source = root/manifest_relative
    export = json.loads(source.read_text(encoding='utf8'))
    skeleton_path = '/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton'
    skeleton = unreal.load_asset(skeleton_path)
    if not isinstance(skeleton, unreal.Skeleton):
        raise RuntimeError('Expected actual production Skeleton at '+skeleton_path)
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop PIE before asset authoring')
    out = root/journal_relative
    if out.exists():
        raise RuntimeError('Preserve existing import journal; review partial writes before continuing')
    unreal.EditorAssetLibrary.make_directory(destination)
    journal = dict(status='asset_authoring_in_progress', tests_executed=False,
        skeleton=skeleton.get_path_name(), skeleton_evidence='import_option_not_readback',
        imports=[], formal_moveset_changed=False)
    def save():
        out.write_text(json.dumps(journal, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    save()
    for clip in export['clips']:
        name = 'A_'+clip['clip']
        package = destination+'/'+name
        if unreal.EditorAssetLibrary.does_asset_exist(package):
            raise RuntimeError('Preserve pre-existing package: '+package)
        task = unreal.AssetImportTask()
        task.filename = str(root/clip['fbx']['path'])
        task.destination_path = destination
        task.destination_name = name
        task.automated = True
        task.replace_existing = False
        task.save = False
        task.options = fbx_options('animation', skeleton)
        task.factory = unreal.FbxFactory()
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset = unreal.load_asset(package)
        if not isinstance(asset, unreal.AnimSequence):
            raise RuntimeError('Animation import did not produce AnimSequence: '+package)
        asset.set_editor_property('enable_root_motion', True)
        asset.set_editor_property('force_root_lock', False)
        asset.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        journal['imports'].append(dict(motion=clip['motion'], asset=asset.get_path_name(),
            class_name=asset.get_class().get_name(), skeleton=skeleton.get_path_name(),
            source=clip['fbx'], status='imported_pending_next_stage_tests', tests_executed=False))
        save()
    journal['status'] = 'staging_imported_pending_next_stage_tests'
    save()
    return dict(imported=len(journal['imports']), tests_executed=False, formal_moveset_changed=False)
