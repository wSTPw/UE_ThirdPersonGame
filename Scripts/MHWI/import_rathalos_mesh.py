"""UE editor import for the Rathalos skeletal mesh + textures (runs inside UE python).

Confined to /Game/MHWI/Rathalos. Creates no gameplay assets and touches no existing
MHWI asset. Intended for a headless run:

  UnrealEditor.exe IntroCpp.uproject -unattended -nosplash -stdout \
    -ExecutePythonScript="Scripts/MHWI/import_rathalos_mesh.py"

Writes Saved/MHWProbe-20261030/model-ue/import-report.json and quits the editor.
"""
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SRC = ROOT / 'Saved/MHWProbe-20261030/model-ue'
DEST = '/Game/MHWI/Rathalos'
REPORT = SRC / 'import-report.json'
report = {'source': str(SRC), 'dest': DEST, 'imports': [], 'textures': [], 'errors': []}


def save_report():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')


def make_dirs():
    for folder in ('Mesh', 'Textures', 'Materials'):
        unreal.EditorAssetLibrary.make_directory(f'{DEST}/{folder}')


def fbx_options():
    options = unreal.FbxImportUI()
    options.set_editor_property('automated_import_should_detect_type', False)
    options.set_editor_property('import_materials', True)
    options.set_editor_property('import_textures', True)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('import_mesh', True)
    options.set_editor_property('import_animations', False)
    options.set_editor_property('create_physics_asset', False)
    options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    data = options.get_editor_property('skeletal_mesh_import_data')
    data.set_editor_property('convert_scene', True)
    data.set_editor_property('convert_scene_unit', True)
    data.set_editor_property('force_front_x_axis', False)
    data.set_editor_property('use_t0_as_ref_pose', False)
    data.set_editor_property('update_skeleton_reference_pose', False)
    data.set_editor_property('import_morph_targets', False)
    data.set_editor_property('import_meshes_in_bone_hierarchy', True)
    return options


def import_mesh(fbx, name):
    task = unreal.AssetImportTask()
    task.filename = str(fbx)
    task.destination_path = f'{DEST}/Mesh'
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.options = fbx_options()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property('imported_object_paths'))
    asset = unreal.load_asset(f'{DEST}/Mesh/{name}')
    entry = {'fbx': fbx.name, 'name': name, 'imported': [str(p) for p in paths],
             'asset': asset.get_path_name() if asset else None}
    if asset:
        entry['skeleton'] = asset.get_editor_property('skeleton').get_path_name() if asset.get_editor_property('skeleton') else None
        mats = []
        for slot in asset.get_editor_property('materials'):
            try:
                mats.append(str(slot.get_editor_property('material_interface')))
            except Exception:  # noqa: BLE001 - slot introspection differs across versions
                mats.append(str(slot))
        entry['materials'] = mats
        try:
            entry['lod_count'] = len(asset.get_editor_property('lod_info'))
        except Exception:  # noqa: BLE001 - lod_info was renamed/removed in newer versions
            entry['lod_count'] = None
        try:
            skeleton = asset.get_editor_property('skeleton')
            bones = skeleton.get_editor_property('bone_tree') if skeleton else None
            entry['bone_count'] = len(bones) if bones is not None else None
        except Exception:  # noqa: BLE001
            entry['bone_count'] = None
    report['imports'].append(entry)
    return asset


def relocate_textures():
    """import_textures drops Texture2D next to the mesh; move them to Textures/."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    moved = []
    for data in registry.get_assets_by_path(f'{DEST}/Mesh', recursive=False):
        if data.asset_class_path.asset_name != 'Texture2D':
            continue
        old = str(data.package_name)
        name = str(data.asset_name)
        new = f'{DEST}/Textures/{name}'
        if unreal.EditorAssetLibrary.does_asset_exist(new):
            unreal.EditorAssetLibrary.delete_asset(old)
            moved.append({'name': name, 'action': 'deleted_duplicate'})
            continue
        if unreal.EditorAssetLibrary.rename_asset(old, new):
            moved.append({'name': name, 'action': 'moved'})
        else:
            report['errors'].append({'texture': name, 'error': 'rename failed'})
    return moved


def relocate_materials():
    """Materials created by import_materials also land next to the mesh."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    moved = []
    for data in registry.get_assets_by_path(f'{DEST}/Mesh', recursive=False):
        if data.asset_class_path.asset_name != 'Material':
            continue
        old = str(data.package_name)
        name = str(data.asset_name)
        new = f'{DEST}/Materials/{name}'
        if unreal.EditorAssetLibrary.does_asset_exist(new):
            unreal.EditorAssetLibrary.delete_asset(old)
            moved.append({'name': name, 'action': 'deleted_duplicate'})
            continue
        if unreal.EditorAssetLibrary.rename_asset(old, new):
            moved.append({'name': name, 'action': 'moved'})
        else:
            report['errors'].append({'material': name, 'error': 'rename failed'})
    return moved


def fix_textures():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_path(f'{DEST}/Textures', recursive=True)
    for data in assets:
        asset = data.get_asset()
        if not asset:
            continue
        name = asset.get_name()
        is_normal = name.upper().endswith('NM') or '_NM' in name.upper() or 'NORMAL' in name.upper()
        try:
            if is_normal:
                asset.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
                asset.set_editor_property('srgb', False)
            else:
                asset.set_editor_property('srgb', True)
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
            report['textures'].append({'name': name, 'normal_map': is_normal})
        except Exception as error:  # noqa: BLE001 - texture setting failure must be reported, not fatal
            report['errors'].append({'texture': name, 'error': f'{type(error).__name__}: {error}'})


def wire_rmt(rmt_textures):
    """Wire RMT: R -> Roughness, G -> Metallic.

    Channel roles measured from the texture itself: R has a wide 0.55-0.95 spread
    (roughness), G is uniformly 0 for this organic monster (metallic).
    """
    lib = unreal.MaterialEditingLibrary
    wired = []
    for mat_name, tex_path in rmt_textures.items():
        mat = unreal.load_asset(f'{DEST}/Materials/{mat_name}')
        if not mat:
            report['errors'].append({'material': mat_name, 'error': 'missing material'})
            continue
        existing = [e for e in lib.get_material_expressions(mat) if e.get_name() == 'RMT']
        node = existing[0] if existing else lib.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -520, -260)
        node.set_editor_property('texture', unreal.load_asset(tex_path))
        if not existing:
            node.set_editor_property('material_expression_editor_x', -520)
        for channel, prop in (('R', unreal.MaterialProperty.MP_ROUGHNESS),
                              ('G', unreal.MaterialProperty.MP_METALLIC)):
            lib.connect_material_property(node, channel, prop)
        lib.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
        wired.append(mat_name)
    return wired


def main():
    if not SRC.is_dir():
        raise SystemExit(f'missing source dir: {SRC}')
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    make_dirs()
    for fbx, name in ((SRC / 'SK_EM001_Body.fbx', 'SK_EM001_Body'),
                      (SRC / 'SK_EM001_Tail.fbx', 'SK_EM001_Tail')):
        if fbx.is_file():
            try:
                import_mesh(fbx, name)
            except Exception as error:  # noqa: BLE001
                report['errors'].append({'fbx': str(fbx), 'error': f'{type(error).__name__}: {error}'})
    report['relocated'] = relocate_textures()
    report['rmt_wired'] = wire_rmt({
        'Ch_EM001_Mt__2': f'{DEST}/Textures/em001_00_RMT_tex',
        'Ch_EM001_Mt__damage': f'{DEST}/Textures/em001_00_damage_RMT_tex',
        'FakeEye_Mt__4': f'{DEST}/Textures/em001_00_eye_RMT_tex',
    })
    report['materials_relocated'] = relocate_materials()
    fix_textures()
    try:
        unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=True)
    except Exception as error:  # noqa: BLE001
        report['errors'].append({'save': f'{type(error).__name__}: {error}'})
    report['status'] = 'done'
    save_report()
    print('RATHALOS_IMPORT ' + json.dumps(report, ensure_ascii=False))


main()
try:
    unreal.SystemLibrary.quit_editor()
except Exception:
    pass
