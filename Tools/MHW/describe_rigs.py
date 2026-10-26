"""Report source bind matrices while preparing the merged hunter rig."""
import importlib
import json
from pathlib import Path
import sys
import types
from mathutils import Matrix

root = Path(__file__).resolve().parents[2]
package = types.ModuleType('mhw_suite')
package.__path__ = [str(root / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main')]
sys.modules['mhw_suite'] = package
parser = importlib.import_module('mhw_suite.mod3.mod3_parser').Mod3Parser
native = root / 'ArtSource/ThirdParty/MHWLongSword/nativePC'
for file in (native / 'pl').rglob('*.mod3'):
    bones, _ = parser(path=str(file)).read()
    for b in bones:
        if b['remap'] not in (0, 1, 2, 3, 4, 150):
            continue
        local = Matrix(b['local_matrix']).transposed()
        inverse_bind = Matrix(b['global_matrix']).transposed()
        print(file.stem, b['remap'], 'parent', b['parent'],
              'local', tuple(round(v, 3) for v in local.to_translation()),
              'global', tuple(round(v, 3) for v in inverse_bind.to_translation()),
              'global_inv', tuple(round(v, 3) for v in inverse_bind.inverted_safe().to_translation()), flush=True)
