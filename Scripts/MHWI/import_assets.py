"""UE editor authoring: staged, resumable import confined to /Game/MHWI."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/Converted'
OUT = ROOT / 'Saved/MHWIImport'
OUT.mkdir(parents=True, exist_ok=True)
STATE = OUT / 'import-state.json'


def state():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else dict(imported={}, errors=[])


def save(data):
    STATE.write_text(json.dumps(data, indent=2), encoding='utf-8')


def import_one(source, destination, name, options, data):
    asset_path = destination + '/' + name
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.load_asset(asset_path)
    unreal.EditorAssetLibrary.make_directory(destination)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.destination_name = name
    task.automated = True
    task.replace_existing = False
    task.save = True
    task.options = options
    if isinstance(options, unreal.FbxImportUI):
        factory = unreal.FbxFactory()
        task.factory = factory
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.imported_object_paths)
    data['imported'][str(source.relative_to(SOURCE))] = paths
    save(data)
    asset = unreal.load_asset(asset_path)
    if not asset:
        meshes = [unreal.load_asset(path) for path in paths]
        asset = next((obj for obj in meshes if isinstance(obj, unreal.SkeletalMesh)), None)
    if not asset:
        raise RuntimeError(f'Import did not produce requested asset: {source}: {paths}')
    return asset


def fbx_options(kind, skeleton=None):
    options = unreal.FbxImportUI()
    options.set_editor_property('automated_import_should_detect_type', False)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('import_mesh', kind == 'mesh')
    options.set_editor_property('import_animations', kind == 'animation')
    options.set_editor_property('create_physics_asset', False)
    options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH if kind == 'mesh'
                                else unreal.FBXImportType.FBXIT_ANIMATION)
    if skeleton:
        options.set_editor_property('skeleton', skeleton)
    import_data = options.get_editor_property('skeletal_mesh_import_data' if kind == 'mesh' else 'anim_sequence_import_data')
    import_data.set_editor_property('convert_scene', True)
    import_data.set_editor_property('convert_scene_unit', True)
    import_data.set_editor_property('force_front_x_axis', False)
    if kind == 'mesh':
        import_data.set_editor_property('use_t0_as_ref_pose', False)
        import_data.set_editor_property('update_skeleton_reference_pose', False)
        import_data.set_editor_property('import_morph_targets', False)
        import_data.set_editor_property('import_meshes_in_bone_hierarchy', True)
    else:
        import_data.set_editor_property('use_default_sample_rate', False)
        import_data.set_editor_property('custom_sample_rate', 60)
        import_data.set_editor_property('remove_redundant_keys', False)
        import_data.set_editor_property('import_bone_tracks', True)
    return options


def meshes():
    data = state()
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    for folder in ['Character', 'Weapons', 'Textures', 'Materials', 'Animations/LongSword',
                   'Animations/Common', 'Montages', 'Data', 'Blueprints', 'Maps']:
        unreal.EditorAssetLibrary.make_directory('/Game/MHWI/' + folder)
    hunter = import_one(SOURCE / 'SK_MHW_Hunter_pl001.fbx', '/Game/MHWI/Character',
                        'SK_MHWI_Hunter', fbx_options('mesh'), data)
    data['hunter'] = hunter.get_path_name()
    data['skeleton'] = hunter.get_editor_property('skeleton').get_path_name()
    for source_name, name in [('swo001.fbx', 'SK_MHWI_LongSword'), ('saya001.fbx', 'SK_MHWI_Scabbard')]:
        obj = import_one(SOURCE / source_name, '/Game/MHWI/Weapons', name, fbx_options('mesh'), data)
        data[name] = obj.get_path_name()
    save(data)
    return dict(hunter=data['hunter'], skeleton=data['skeleton'], imported=len(data['imported']))


def animations(start=0, count=12, common=False):
    data = state()
    skeleton = unreal.load_asset(data['skeleton'])
    if not skeleton:
        raise RuntimeError('Import hunter skeleton first')
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    source_folder = SOURCE / ('Common' if common else 'Animations')
    destination = '/Game/MHWI/Animations/' + ('Common' if common else 'LongSword')
    files = sorted(source_folder.glob('*.fbx'))
    completed = []
    for path in files[int(start):int(start) + int(count)]:
        name = 'A_' + path.stem
        sequence = import_one(path, destination, name, fbx_options('animation', skeleton), data)
        if isinstance(sequence, unreal.AnimSequence):
            sequence.set_editor_property('enable_root_motion', True)
            sequence.set_editor_property('root_motion_root_lock', unreal.RootMotionRootLock.REF_POSE)
            sequence.set_editor_property('force_root_lock', False)
            unreal.EditorAssetLibrary.save_loaded_asset(sequence)
        completed.append(name)
    data['longsword_total'] = len(files) if not common else data.get('longsword_total', 0)
    save(data)
    return dict(completed=completed, next_start=int(start) + len(completed), total=len(files))


def textures(start=0, count=12):
    data = state()
    files = sorted((SOURCE / 'Textures').rglob('*.png'))
    tasks = []
    for path in files[int(start):int(start) + int(count)]:
        relative = path.relative_to(SOURCE / 'Textures')
        destination = '/Game/MHWI/Textures/' + relative.parent.as_posix()
        asset_path = destination + '/T_' + path.stem
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            continue
        unreal.EditorAssetLibrary.make_directory(destination)
        task = unreal.AssetImportTask()
        task.filename = str(path)
        task.destination_path = destination
        task.destination_name = 'T_' + path.stem
        task.automated = True
        task.replace_existing = False
        task.save = True
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for task in tasks:
        paths = list(task.imported_object_paths)
        data['imported'][str(Path(task.filename).relative_to(SOURCE))] = paths
        for path in paths:
            texture = unreal.load_asset(path)
            if isinstance(texture, unreal.Texture2D):
                name = texture.get_name().upper()
                if name.endswith('_NM'):
                    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
                    texture.set_editor_property('srgb', False)
                elif any(name.endswith(suffix) for suffix in ('_RMT', '_CMM', '_LIN', '_XM')):
                    texture.set_editor_property('srgb', False)
                    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
                unreal.EditorAssetLibrary.save_loaded_asset(texture)
    save(data)
    return dict(imported=len(tasks), next_start=int(start) + min(int(count), len(files) - int(start)), total=len(files))

