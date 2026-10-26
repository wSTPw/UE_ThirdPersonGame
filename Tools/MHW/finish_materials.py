"""Finish the converted source bundle with portable PNG/basic FBX materials.

This is an asset production step, not a render/PIE/import validation.
The original MHW shader remains available through raw MRL3/TEX files.
"""
import importlib
import json
from pathlib import Path
import sys
import types
import bpy

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'ArtSource/ThirdParty/MHWLongSword'
NATIVE = BASE / 'nativePC'
OUT = BASE / 'Converted'
package = types.ModuleType('mhw_suite')
package.__path__ = [str(ROOT / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main')]
sys.modules['mhw_suite'] = package
load_tex = importlib.import_module('mhw_suite.tex.tex_loader').load_tex
Mrl3Parser = importlib.import_module('mhw_suite.mrl3.mrl3_parser').Mrl3Parser
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'MHW_Hunter_LongSword_Actions.blend'))
report = json.loads((BASE / 'conversion-report.json').read_text(encoding='utf-8'))
images = {}
converted_textures = []
unconverted_textures = []
for path in sorted(NATIVE.rglob('*.tex')):
    try:
        image = load_tex(str(path), use_loaded=False, use_png_cache=False)
    except RuntimeError as error:
        if 'Texture data format not supported' not in str(error):
            raise
        unconverted_textures.append(dict(source=path.relative_to(NATIVE).as_posix(), reason=str(error)))
        print('TEXTURE_RETAINED_RAW', path.relative_to(NATIVE), str(error), flush=True)
        continue
    relative = path.relative_to(NATIVE).with_suffix('.png')
    target = OUT / 'Textures' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    image.file_format = 'PNG'
    image.filepath_raw = str(target)
    image.save()
    images[path.relative_to(NATIVE).as_posix().lower()] = image
    converted_textures.append(str(target.relative_to(BASE)))
    print('TEXTURE_CONVERTED', relative, flush=True)

material_sources = {}
for path in NATIVE.rglob('*.mrl3'):
    for hashed, mat in Mrl3Parser(path=str(path)).read().items():
        material_sources[str(hashed)] = mat

def texture_for(mat, token):
    for key, path in mat['textures'].items():
        if key.startswith(token):
            return images.get((path.replace('\\', '/').strip('/') + '.tex').lower())
    return None


mapped = []
for material in bpy.data.materials:
    data = material_sources.get(str(material.get('name_hash', '')))
    if data is None:
        continue
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Roughness'].default_value = 0.65
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    albedo = texture_for(data, 'tAlbedoMap')
    if albedo:
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = albedo
        tex.label = 'MHW albedo'
        links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    normal = texture_for(data, 'tNormalMap')
    if normal:
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = normal
        tex.image.colorspace_settings.name = 'Non-Color'
        normal_node = nodes.new('ShaderNodeNormalMap')
        links.new(tex.outputs['Color'], normal_node.inputs['Color'])
        links.new(normal_node.outputs['Normal'], shader.inputs['Normal'])
    material['mhw_material_source'] = json.dumps(data['textures'])
    material['conversion_note'] = 'Basic portable material. Original layered masks/RMT shader not recreated.'
    mapped.append(material.name)
if not mapped:
    raise RuntimeError('No source materials matched the converted model')

master = bpy.data.objects['Armature']
for filename, objects in [
    ('SK_MHW_Hunter_pl001.fbx', [master] + [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.parent == master]),
    ('saya001.fbx', [obj for obj in bpy.data.objects if obj.name.startswith('Armature_saya001') or (obj.parent and obj.parent.name.startswith('Armature_saya001'))]),
    ('swo001.fbx', [obj for obj in bpy.data.objects if obj.name.startswith('Armature_swo001') or (obj.parent and obj.parent.name.startswith('Armature_swo001'))]),
]:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(obj for obj in objects if obj.type == 'ARMATURE')
    bpy.ops.export_scene.fbx(filepath=str(OUT / filename), use_selection=True,
        object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
        axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
        bake_anim=False, path_mode='COPY', embed_textures=False)
    if filename != 'SK_MHW_Hunter_pl001.fbx':
        for obj in objects:
            obj.hide_set(True)
for image in images.values():
    image.pack()
bpy.context.view_layer.objects.active = master
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'MHW_Hunter_LongSword_Actions.blend'))
report['textures_converted'] = converted_textures
report['textures_unconverted'] = unconverted_textures
report['portable_materials'] = mapped
report['material_note'] = 'Basic albedo/normal only; original layered MHW shader not fully recreated'
(BASE / 'conversion-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('MATERIALS_FINISHED', len(converted_textures), 'textures', len(mapped), 'materials', flush=True)
