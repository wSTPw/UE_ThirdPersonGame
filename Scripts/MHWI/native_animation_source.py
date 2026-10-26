"""Pinned, read-only native LMT sampling for the existing Feuleur hunter rig.

The upstream add-on is loaded as a namespace only: no installation, registration,
updater, or top-level add-on code is executed. Blender and the portable tool cache
are explicit local dependencies. This module never writes sources or UE assets.
"""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'ArtSource/ThirdParty/MHWLongSword'
BLEND = BASE / 'Converted/MHW_Hunter_LongSword_Actions.blend'
OUTPUT = BASE / 'NativeFidelity'
UPSTREAM = ROOT / 'Saved/MHWIImport/SourceFidelity-20261023/timing-mhw-anim-tools/mhw-anim-tools-main'
LEGACY = ROOT / 'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main'
SOURCES = {
    'w03_00': BASE / 'nativePC/hm/wp/wp03/mot/w03_00/w03_00.lmt',
    'co00_00': BASE / 'nativePC/hm/common/mot/co00_00/co00_00.lmt',
}
FOCUS = [f'w03_00_{i:03}' for i in (2, 3, 129, 173, 306, 308, 309, 310, 311)]


def evidence(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                sha256=digest.hexdigest())


def native_modules():
    name = '_mhwi_native_fidelity'
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(UPSTREAM)]
        sys.modules[name] = package
    return tuple(importlib.import_module(name + '.' + suffix) for suffix in (
        'core.formats.lmt.reader', 'core.formats.lmt.pose_evaluation'))


def dependency_evidence():
    return [evidence(p) for p in [BLEND, *SOURCES.values(),
        LEGACY / 'lmt/lmt_loader.py', LEGACY / 'lmt/lmt_parser.py',
        UPSTREAM / 'LICENSE', *sorted((UPSTREAM / 'core').rglob('*.py'))]]


def load_action(name):
    family, index = name.rsplit('_', 1)
    reader, pose = native_modules()
    bank = reader.read_lmt_file(SOURCES[family])
    action = next(a for a in bank.actions if a.id == int(index))
    return bank, action


def inspect_rig(arm):
    """Serializable bind hierarchy; transforms use source-centimeter rig units."""
    rows = {}
    for bone in arm.data.bones:
        local = bone.parent.matrix_local.inverted() @ bone.matrix_local if bone.parent else bone.matrix_local
        rows[bone.name] = dict(parent=bone.parent.name if bone.parent else None,
            inherit_scale=bone.inherit_scale,
            local_matrix=[list(row) for row in local],
            matrix_local=[list(row) for row in bone.matrix_local])
    return dict(bone_count=len(rows), bones=rows,
                matrix_world=[list(row) for row in arm.matrix_world])


def function_map(arm):
    result = {}
    for bone in arm.data.bones:
        if bone.name.startswith('bone_') and bone.name[5:].isdigit():
            function = int(bone.name[5:])
            if 0 <= function < 512:
                result[function] = bone.name
    return result


def reset_pose(arm):
    import bpy
    arm.animation_data_create()
    arm.animation_data.action = None
    for bone in arm.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def create_bind_reference_mesh(arm):
    """Tiny, disposable skin to carry all original bind matrices in FBX.

    Animation-only FBX lacks skin clusters; importers can reinterpret node T0
    defaults as rest and absorb constant scale into bone lengths. One triangle
    per bone pins the unchanged 225-bone skin bind without exporting character
    meshes. UE animation import explicitly ignores this reference geometry.
    """
    import bpy
    verts, faces = [], []
    for bone in arm.data.bones:
        head = bone.head_local
        first = len(verts)
        verts.extend([tuple(head), (head.x+.001, head.y, head.z),
                      (head.x, head.y+.001, head.z)])
        faces.append((first, first+1, first+2))
    data = bpy.data.meshes.new('NativeFidelity_BindReference')
    data.from_pydata(verts, [], faces)
    mesh = bpy.data.objects.new('NativeFidelity_BindReference', data)
    bpy.context.scene.collection.objects.link(mesh)
    mesh.parent = arm
    modifier = mesh.modifiers.new('BindReference', 'ARMATURE')
    modifier.object = arm
    for index, bone in enumerate(arm.data.bones):
        mesh.vertex_groups.new(name=bone.name).add([index*3, index*3+1, index*3+2], 1., 'REPLACE')
    return mesh


def shared_curve_owner(bank, source):
    """Resolve an explicit physical alias, never synthesize a layered base.

    Some original entries (112/105, 309..311/308) point at the identical LMT
    track table. Only accept an unflagged owner with identical pose header data.
    TIML remains the requested entry's own resource and is never substituted.
    """
    h = source.header
    if not h.flags2 & 1 or not h.fcurve_offset or not h.fcurve_count:
        return None
    def signature(a):
        x = a.header
        return (x.fcurve_offset, x.fcurve_count, x.frame_count, x.loop_frame,
                x.translation, x.rotation_lerp, x.flags, x.flags2 & ~1)
    return next((a for a in bank.actions if not a.header.flags2 & 1
                 and signature(a) == signature(source)), None)


def compiled_action(arm, name):
    bank, source = load_action(name)
    _, pose = native_modules()
    result = pose.compile_pose_evaluation(source, function_map(arm), version=bank.header.version)
    if not result.supported:
        raise ValueError('; '.join(d.message for d in result.diagnostics if d.level == 'ERROR'))
    if source.header.flags2 & 1 and shared_curve_owner(bank, source) is None:
        raise ValueError(f'{name}: NeedsParent source requires an explicit layered base')
    return result


def rest_local(arm, name):
    bone = arm.data.bones[name]
    return bone.parent.matrix_local.inverted() @ bone.matrix_local if bone.parent else bone.matrix_local.copy()


def converted_value(arm, name, usage, value):
    """Convert source components into this copied rig's pose-basis channels.

    Feuleur stores centimeter/Y-up bones under an object with +90 X and .01
    scale. Its dedicated root is identity. Root/action channels retain the
    existing raw action-space convention, preserving the production root basis.
    Ordinary source channels are absolute parent-local L/R/S. Translation must
    be unrotated by rest rotation (the legacy loader only subtracted rest L).
    Quaternion key lengths are retained for native raw-endpoint NLERP.
    """
    from mathutils import Quaternion, Vector
    import math
    local = rest_local(arm, name)
    loc, rot, scale = local.decompose()
    if usage in (3, 4):
        if max(abs(local[r][c] - (1 if r == c else 0)) for r in range(4) for c in range(4)) > 1e-5:
            raise ValueError('Root/action convention requires an unchanged identity bone_root bind')
        return tuple(value)
    if usage == 0:
        norm = math.sqrt(sum(v * v for v in value))
        converted = rot.inverted() @ Quaternion(value).normalized()
        return tuple(v * norm for v in converted)
    if usage == 1:
        delta = rot.inverted() @ (Vector(value) - loc)
        return tuple(delta[i] / scale[i] for i in range(3))
    if usage == 2:
        return tuple(value[i] / scale[i] for i in range(3))
    raise ValueError(f'Unsupported usage {usage}')


def build_action(arm, name, evaluation=None):
    """Exact source-key curves, with explicit rest defaults for missing channels."""
    import bpy
    evaluation = evaluation or compiled_action(arm, name)
    end = evaluation.source.header.frame_count - 1
    action = bpy.data.actions.new('Native_' + name)
    selected = {(b.target or 'bone_root', b.usage % 3): b for b in evaluation.bindings}
    channels = (('rotation_quaternion', (1., 0., 0., 0.)),
                ('location', (0., 0., 0.)), ('scale', (1., 1., 1.)))
    for bone in arm.data.bones:
        for kind, (transform, default) in enumerate(channels):
            binding = selected.get((bone.name, kind))
            if binding:
                curve = binding.curve
                times = sorted({0, end, *(f for f in curve.frames if f <= end)})
                values = [(t, converted_value(arm, bone.name, binding.usage, curve.raw_sample(t))) for t in times]
                if kind == 0:
                    lifted = []
                    for time, value in values:
                        if lifted and sum(a*b for a, b in zip(lifted[-1][1], value)) < 0:
                            value = tuple(-v for v in value)
                        lifted.append((time, value))
                    values = lifted
            else:
                values = [(0, default), (end, default)] if end else [(0, default)]
            path = f'pose.bones["{bone.name}"].{transform}'
            for index in range(len(default)):
                fc = action.fcurves.new(path, index=index, action_group=bone.name)
                fc.keyframe_points.add(len(values))
                fc.keyframe_points.foreach_set('co', [v for t, value in values for v in (t, value[index])])
                for point in fc.keyframe_points:
                    point.interpolation = 'LINEAR'
                fc.update()
    action['native_frame_count'] = evaluation.source.header.frame_count
    action['native_loop_frame'] = evaluation.source.header.loop_frame
    action['native_pose_rule'] = native_modules()[1].RULE_VERSION
    action['native_source_name'] = name
    action.use_fake_user = True
    action.use_frame_range = True
    action.frame_start, action.frame_end = 0, end
    return action
