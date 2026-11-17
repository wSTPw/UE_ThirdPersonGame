"""Rebuild MHW monster materials as plain Principled BSDF and export a UE-usable FBX.

The Feuleur suite wires materials through custom shader node groups (WorldShader /
EM100_pre / EM100_post ...), which the FBX exporter cannot translate: the exported
FBX keeps material names only, with no texture links. This script keeps the geometry
and rig from the same loaders, but replaces each material tree with a minimal
Principled setup pointing at the suite's already-converted `*.tex.png` files, so the
FBX carries real texture references.

Only base colour / normal / emissive are wired. RMT (metal-rough) and CMM (tint)
packing is not converted here - see the report field 'unwired'.

Usage (from project root):
  blender.exe --background --factory-startup --python-exit-code 1 \
    --python Tools/MHW/rebuild_monster_materials.py -- \
    --mod3 <x.mod3> --mrl3 <x.mrl3> --tex-root <nativePC> --out <x.fbx> [--report <r.json>]
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
parser.add_argument('--mrl3', required=True)
parser.add_argument('--tex-root', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--report')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

mod3 = Path(args.mod3).resolve()
mrl3 = Path(args.mrl3).resolve()
tex_root = Path(args.tex_root).resolve()
out = Path(args.out).resolve()
for path in (mod3, mrl3):
    if not path.is_file():
        raise SystemExit(f'missing input: {path}')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

objects = load_mod3(str(mod3), LOD=0, fix_rotation=True, fix_scale=True,
                    rename_bones=False, connect_bones=False)
with bpy.data.libraries.load(str(ADDON / 'mrl3/materials_groups.blend'), link=False) as (src, dst):
    dst.node_groups = src.node_groups
mrl3_error = None
try:
    load_mrl3(str(tex_root), str(mrl3), use_loaded_tex=True, use_png_cache=True)
except Exception as error:  # noqa: BLE001 - geometry result must survive material failure
    mrl3_error = f'{type(error).__name__}: {error}'

report = {'mod3': str(mod3), 'status': 'started', 'materials': [], 'unwired': [], 'missing_png': []}


def pick(images, wanted):
    """First image whose stem ends with one of the wanted suffixes (e.g. BML, NM).

    Placeholder images (NoImage_*) are skipped: wiring one into Emission makes the
    whole mesh glow white and drowns the base colour.
    """
    for suffix in wanted:
        for image in images:
            if Path(Path(image.name).stem).stem.lower().startswith('noimage'):
                continue
            stem = Path(image.name).stem          # em001_00_BML.tex
            base = Path(stem).stem                 # em001_00_BML
            if base.endswith(suffix):
                return image
    return None


def png_for(image):
    """The suite writes <name>.tex.png next to the source .tex; prefer that file."""
    original = Path(bpy.path.abspath(image.filepath))
    for candidate in (original.with_suffix(original.suffix + '.png'),
                      Path(str(original) + '.png'),
                      original.with_suffix('.png')):
        if candidate.is_file():
            return candidate
    return None


for material in [m for m in bpy.data.materials if m.use_nodes]:
    images = [n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    if not images:
        continue
    base = pick(images, ('BML', 'BM', 'ALBM', 'BC'))
    normal = pick(images, ('NM', 'NRM'))
    emissive = pick(images, ('EM',))

    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (250, 0)
    principled.inputs['Roughness'].default_value = 0.65
    principled.inputs['Metallic'].default_value = 0.0
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    entry = {'name': material.name, 'base': None, 'normal': None, 'emissive': None}

    def wire(image, socket, y):
        png = png_for(image)
        if not png:
            report['missing_png'].append({'material': material.name, 'image': image.name})
            return None
        tex = tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(png), check_existing=True)
        tex.location = (-150, y)
        tex.label = png.name
        tree.links.new(tex.outputs['Color'], socket)
        return png.name

    if base:
        entry['base'] = wire(base, principled.inputs['Base Color'], 200)
    if normal:
        tex = tree.nodes.new('ShaderNodeTexImage')
        png = png_for(normal)
        if png:
            tex.image = bpy.data.images.load(str(png), check_existing=True)
            tex.location = (-150, -100)
            tex.label = png.name
            normal_map = tree.nodes.new('ShaderNodeNormalMap')
            normal_map.location = (60, -100)
            tree.links.new(tex.outputs['Color'], normal_map.inputs['Color'])
            tree.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
            entry['normal'] = png.name
        else:
            report['missing_png'].append({'material': material.name, 'image': normal.name})
    if emissive:
        entry['emissive'] = wire(emissive, principled.inputs['Emission Color'], -300)
        if entry['emissive']:
            principled.inputs['Emission Strength'].default_value = 1.0

    for image in images:
        base_name = Path(Path(image.name).stem).stem
        if base_name.endswith(('RMT', 'CMM', 'CMML', 'FM', 'damage_RMT')):
            report['unwired'].append({'material': material.name, 'image': image.name})
    report['materials'].append(entry)

out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.export_scene.fbx(filepath=str(out), use_selection=True,
    object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
    bake_anim=False, path_mode='COPY', embed_textures=False)

report['mrl3_error'] = mrl3_error
report['export'] = {'path': str(out), 'bytes': out.stat().st_size if out.is_file() else 0}
report['status'] = 'exported'
if args.report:
    Path(args.report).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
print('REBUILD ' + json.dumps({k: v for k, v in report.items() if k != 'materials'}, ensure_ascii=False))
print('MATS ' + json.dumps(report['materials'], ensure_ascii=False))
