"""Export MHW monster LMT motions to per-action FBX files (headless Blender).

Mirrors the hunter pipeline in build_asset_bundle.py: load_mod3 for the armature,
load_lmt to create actions, then bake one action per FBX. Bone naming matches the
suite default (bone_XXX), which is also what our model FBX used, so the resulting
animations retarget onto SK_EM001_*_Skeleton in UE.

Usage:
  blender.exe --background --factory-startup --python-exit-code 1 \
    --python Tools/MHW/convert_monster_animations.py -- \
    --mod3 <x.mod3> --lmt <x.lmt> --out-dir <dir> [--max-actions 30] [--report <r.json>]
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
load_lmt = importlib.import_module('mhw_suite.lmt.lmt_loader').load_lmt

parser = argparse.ArgumentParser()
parser.add_argument('--mod3', required=True)
parser.add_argument('--lmt', required=True)
parser.add_argument('--out-dir', required=True)
parser.add_argument('--max-actions', type=int, default=30)
parser.add_argument('--report')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

mod3 = Path(args.mod3).resolve()
lmt = Path(args.lmt).resolve()
out_dir = Path(args.out_dir).resolve()
for path in (mod3, lmt):
    if not path.is_file():
        raise SystemExit(f'missing input: {path}')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps = 60
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

objects = load_mod3(str(mod3), LOD=0, fix_rotation=True, fix_scale=True,
                    rename_bones=False, connect_bones=False)
armature = next(o for o in objects if o.type == 'ARMATURE')
armature.animation_data_create()

load_lmt(str(lmt), armature.data, set_fake_user=True)
actions = sorted((a for a in bpy.data.actions if a.users), key=lambda a: a.name)
report = {
    'lmt': str(lmt), 'mod3': str(mod3), 'armature': armature.name,
    'bones': len(armature.data.bones), 'actions_total': len(actions),
    'exported': [], 'status': 'started',
}
out_dir.mkdir(parents=True, exist_ok=True)

for action in actions[:args.max_actions]:
    armature.animation_data.action = action
    frame_end = int(action.frame_range[1])
    path = out_dir / f'{action.name}.fbx'
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in (armature,):
            obj.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
            object_types={'ARMATURE'}, add_leaf_bones=False,
            axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
            bake_anim=True, bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False, bake_anim_step=1,
            bake_anim_simplify_factor=0.0,
            path_mode='COPY', embed_textures=False)
        report['exported'].append({'action': action.name, 'frames': frame_end,
                                   'bytes': path.stat().st_size if path.is_file() else 0})
    except Exception as error:  # noqa: BLE001 - one bad action must not stop the batch
        report['exported'].append({'action': action.name, 'error': f'{type(error).__name__}: {error}'})

ok = sum(1 for e in report['exported'] if e.get('bytes', 0) > 0)
report['exported_ok'] = ok
report['status'] = 'done'
if args.report:
    Path(args.report).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
print('ANIM_EXPORT ' + json.dumps({'total': report['actions_total'], 'exported_ok': ok,
      'out': str(out_dir), 'bones': report['bones']}, ensure_ascii=False))
