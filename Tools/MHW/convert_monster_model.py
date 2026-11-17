"""Convert one MHW monster .mod3 to FBX with the local Feuleur suite (headless Blender).

Read-only on the extracted source; writes only the requested --out file and an
optional JSON report. Materials are optional because they trigger texture
conversion and can fail independently of geometry.

Usage (from project root):
  blender.exe --background --factory-startup --python-exit-code 1 \
    --python Tools/MHW/convert_monster_model.py -- \
    --mod3 <path.mod3> --out <path.fbx> [--mrl3 <path.mrl3>] [--report <path.json>]
"""
import argparse
import importlib
import json
import sys
import types
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
ADDON = ROOT / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main'
package = types.ModuleType('mhw_suite')
package.__path__ = [str(ADDON)]
sys.modules['mhw_suite'] = package
load_mod3 = importlib.import_module('mhw_suite.mod3.mod3_loader').load_mod3
load_mrl3 = importlib.import_module('mhw_suite.mrl3.mrl3_loader').load_mrl3

parser = argparse.ArgumentParser()
parser.add_argument('--mod3', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--mrl3')
parser.add_argument('--tex-root')
parser.add_argument('--report')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

mod3 = Path(args.mod3).resolve()
out = Path(args.out).resolve()
if not mod3.is_file():
    raise SystemExit(f'missing input: {mod3}')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

report = {'mod3': str(mod3), 'status': 'started', 'export': None, 'materials': None}

objects = load_mod3(str(mod3), LOD=0, fix_rotation=True, fix_scale=True,
                    rename_bones=False, connect_bones=False)
armatures = [o for o in objects if o.type == 'ARMATURE']
meshes = [o for o in objects if o.type == 'MESH']
if not armatures:
    raise SystemExit('no armature produced by mod3 loader')

report['objects'] = len(objects)
report['armatures'] = [{'name': a.name, 'bones': len(a.data.bones)} for a in armatures]
report['meshes'] = [{
    'name': m.name,
    'polygons': len(m.data.polygons),
    'vertices': len(m.data.vertices),
    'materials': [s.material.name for s in m.material_slots if s.material],
} for m in meshes]

if args.mrl3:
    mrl3 = Path(args.mrl3).resolve()
    tex_root = Path(args.tex_root).resolve() if args.tex_root else mod3.parent
    try:
        # The mrl3 loader expects the suite's shader node groups to exist already.
        with bpy.data.libraries.load(str(ADDON / 'mrl3/materials_groups.blend'), link=False) as (src, dst):
            dst.node_groups = src.node_groups
        load_mrl3(str(tex_root), str(mrl3), use_loaded_tex=True, use_png_cache=True)
        report['materials'] = 'loaded'
    except Exception as error:  # noqa: BLE001 - material failure must not hide geometry result
        report['materials'] = f'failed: {type(error).__name__}: {error}'

out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.export_scene.fbx(filepath=str(out), use_selection=True,
    object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
    bake_anim=False, path_mode='COPY', embed_textures=False)

report['export'] = {'path': str(out), 'bytes': out.stat().st_size if out.is_file() else 0}
report['status'] = 'exported'
if args.report:
    Path(args.report).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
