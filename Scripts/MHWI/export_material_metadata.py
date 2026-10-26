"""Read Blender source material provenance for UE material authoring."""
import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
blend = root / 'ArtSource/ThirdParty/MHWLongSword/Converted/MHW_Hunter_LongSword_Actions.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
materials = {}
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    for slot in obj.material_slots:
        mat = slot.material
        if mat and 'mhw_material_source' in mat:
            materials[mat.name] = dict(hash=str(mat.get('name_hash', '')),
                                      textures=json.loads(mat['mhw_material_source']))
destination = root / 'Scripts/MHWI/material_bindings.json'
destination.write_text(json.dumps(materials, indent=2), encoding='utf-8')
print('MATERIAL_BINDINGS', len(materials), flush=True)
