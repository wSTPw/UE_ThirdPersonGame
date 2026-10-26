"""Blender-side source metadata/dependency inventory used during acquisition."""
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
ADDON = ROOT / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main'
NATIVE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/nativePC'
package = types.ModuleType('mhw_suite')
package.__path__ = [str(ADDON)]
sys.modules['mhw_suite'] = package
Mod3Parser = importlib.import_module('mhw_suite.mod3.mod3_parser').Mod3Parser
Mrl3Parser = importlib.import_module('mhw_suite.mrl3.mrl3_parser').Mrl3Parser
LmtParser = importlib.import_module('mhw_suite.lmt.lmt_parser').LmtParser
report = dict(models=[], animations=[], texture_dependencies=[])
for path in sorted(NATIVE.rglob('*.mod3')):
    bones, meshes = Mod3Parser(path=str(path)).read()
    report['models'].append(dict(path=str(path.relative_to(NATIVE)),
        bones=len(bones or []), bone_ids=[b['remap'] for b in (bones or [])],
        meshes=len(meshes), vertices=sum(len(m['positions']) for m in meshes if m['lod'] == 0)))
for path in sorted(NATIVE.rglob('*.mrl3')):
    materials = Mrl3Parser(path=str(path)).read()
    for mat in materials.values():
        for texture in mat['textures'].values():
            normalized = texture.replace('\\', '/').strip('/') + '.tex'
            if not (NATIVE / normalized).exists():
                report['texture_dependencies'].append(normalized)
for rel in ['hm/wp/wp03/mot/w03_00/w03_00.lmt', 'hm/common/mot/co00_00/co00_00.lmt']:
    animations = LmtParser(path=str(NATIVE / rel)).read()
    for animation in animations:
        bone_ids = list(animation['bone_action'])
        times = [t for bone in animation['bone_action'].values()
                 for kind in ('pos', 'rot', 'scl') for t in bone.get(kind, {})]
        report['animations'].append(dict(source=rel, name=animation['name'],
            bone_ids=bone_ids, frames=[min(times, default=0), max(times, default=0)],
            root_track=-1 in bone_ids))
report['texture_dependencies'] = sorted(set(report['texture_dependencies']))
destination = NATIVE.parent / 'source-inventory.json'
destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('SOURCE_INVENTORY', json.dumps(dict(models=len(report['models']),
    animations=len(report['animations']), missing_textures=report['texture_dependencies'])), flush=True)
