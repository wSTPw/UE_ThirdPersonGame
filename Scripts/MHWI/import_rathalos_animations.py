"""UE editor import: monster LMT animations onto the existing Rathalos skeleton.

Run inside the live editor via MCP (editor.run_python_file) or
ExecutePythonScript. Imports the per-action FBX files produced by
Tools/MHW/convert_monster_animations.py as AnimationSequences on
SK_EM001_Body_Skeleton, confined to /Game/MHWI/Rathalos/Animations.
"""
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.get_project_file_path()).resolve().parent
SRC = ROOT / 'Saved/MHWProbe-20261030/anim'
DEST = '/Game/MHWI/Rathalos/Animations'
SKEL = '/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton'
REPORT = ROOT / 'Saved/MHWProbe-20261030/anim/import-report.json'
report = {'src': str(SRC), 'dest': DEST, 'imported': [], 'errors': []}

unreal.EditorAssetLibrary.make_directory(DEST)
skeleton = unreal.load_asset(SKEL)
if not skeleton:
    raise SystemExit(f'missing skeleton: {SKEL}')

fbxs = sorted(SRC.glob('*.fbx'))
for fbx in fbxs:
    name = 'A_' + fbx.stem
    options = unreal.FbxImportUI()
    options.set_editor_property('automated_import_should_detect_type', False)
    options.set_editor_property('import_mesh', False)
    options.set_editor_property('import_animations', True)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property('skeleton', skeleton)
    data = options.get_editor_property('anim_sequence_import_data')
    data.set_editor_property('use_default_sample_rate', False)
    data.set_editor_property('custom_sample_rate', 60)
    data.set_editor_property('remove_redundant_keys', False)
    data.set_editor_property('import_bone_tracks', True)
    task = unreal.AssetImportTask()
    task.filename = str(fbx)
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.options = options
    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        seq = unreal.load_asset(f'{DEST}/{name}')
        entry = {'name': name, 'ok': bool(seq)}
        if seq:
            for prop in ('sequence_length', 'play_length'):
                try:
                    entry['length'] = seq.get_editor_property(prop)
                    break
                except Exception:  # noqa: BLE001 - property names vary across versions
                    entry['length'] = None
        report['imported'].append(entry)
    except Exception as error:  # noqa: BLE001 - report and continue with remaining files
        report['errors'].append({'fbx': fbx.name, 'error': f'{type(error).__name__}: {error}'})

try:
    unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=True)
except Exception as error:  # noqa: BLE001
    report['errors'].append({'save': f'{type(error).__name__}: {error}'})

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
ok = sum(1 for r in report['imported'] if r['ok'])
print('ANIM_IMPORT imported=%d/%d errors=%d' % (ok, len(report['imported']), len(report['errors'])))
