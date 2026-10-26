"""Matrix and FBX round-trip checks for independently owned native FBXs.

Imported only by export_native_animation.py, or run inside Blender with
--python .../verify_native_animation.py -- --manifest PATH.
No UE API, protected source writes, or plugin registration occurs here.
"""
from __future__ import annotations

import math


class Metric:
    def __init__(self):
        self.count = 0
        self.total = 0.0
        self.maximum = 0.0
        self.worst = None

    def add(self, value, identity):
        self.count += 1
        self.total += value
        if value >= self.maximum:
            self.maximum, self.worst = value, identity

    def result(self):
        return dict(count=self.count, max=self.maximum,
                    mean=self.total / max(1, self.count), worst=self.worst)


def matrix_delta(a, b):
    return max(abs(a[r][c] - b[r][c]) for r in range(4) for c in range(4))


def angle_delta(a, b):
    # mathutils quaternion .angle is float32 and floors small angles to zero.
    qa, qb = a.to_quaternion().normalized(), b.to_quaternion().normalized()
    diff = min(math.sqrt(sum((x-y)**2 for x, y in zip(qa, qb))),
               math.sqrt(sum((x+y)**2 for x, y in zip(qa, qb))))
    return math.degrees(4 * math.asin(min(1., diff / 2)))


def expected_matrices(arm, evaluation, frame, rest):
    """Compose source absolute L/R/S, independently of generated FCurves.

    This existing hunter skeleton has unit bind scales and NONE inherit_scale.
    Strip parent pose scale while composing a child's local source components;
    source joint scale stays on its own matrix. This matches that rig contract.
    Root/action convention is explicitly the production raw root convention.
    """
    from mathutils import Matrix, Quaternion, Vector
    source = evaluation.sample(frame)
    output = {}
    for bone in arm.data.bones:
        loc, rot, scl = rest[bone.name]
        target = None if bone.name == 'bone_root' else bone.name
        root_offset = 3 if target is None else 0
        loc = Vector(source.get((target, root_offset+1), loc))
        rot = Quaternion(source.get((target, root_offset), rot)).normalized()
        scl = Vector(source.get((target, root_offset+2), scl))
        local = Matrix.LocRotScale(loc, rot, scl)
        if bone.parent:
            parent = output[bone.parent.name]
            if bone.inherit_scale == 'NONE':
                pl, pr, _ = parent.decompose()
                parent = Matrix.LocRotScale(pl, pr, Vector((1, 1, 1)))
            local = parent @ local
        output[bone.name] = local
    return output


def sample_matrices(arm, frame, world=False):
    import bpy
    bpy.context.scene.frame_set(int(math.floor(frame)), subframe=frame % 1.)
    evaluated = arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return {b.name: (evaluated.matrix_world @ b.matrix if world else b.matrix.copy())
            for b in evaluated.pose.bones}


def verify_action(arm, evaluation, action, legacy, quarter_frames=True):
    import native_animation_source as native
    rest = {b.name: native.rest_local(arm, b.name).decompose() for b in arm.data.bones}
    if any(max(abs(v-1) for v in scale) > 1e-4 for _, _, scale in rest.values()):
        raise ValueError('Verifier only qualified for this unit-scale bind hierarchy')
    end = evaluation.source.header.frame_count - 1
    if quarter_frames:
        times = [i / 4 for i in range(end*4+1)]
    else:
        # Bulk qualification still covers every native integer frame, plus
        # three fractional offsets near start, middle, two-thirds and end.
        times = sorted({*range(end+1), *(min(end, max(0, base+offset))
            for base in (0, end//3, 2*end//3, max(0, end-1))
            for offset in (.25, .5, .75))})
    metrics = {k: Metric() for k in ('matrix_component_cm', 'position_cm', 'rotation_deg',
                                    'legacy_position_cm', 'legacy_rotation_deg')}
    root_native, root_legacy = [], []
    # Assign each action once. Reassigning at every sample rebuilds Blender's
    # dependency relations thousands of times and is needlessly expensive.
    arm.animation_data.action = action
    native_samples = {}
    for frame in times:
        actual = sample_matrices(arm, frame)
        native_samples[frame] = actual
        expected = expected_matrices(arm, evaluation, frame, rest)
        for name, matrix in actual.items():
            identity = dict(bone=name, frame=frame)
            metrics['matrix_component_cm'].add(matrix_delta(matrix, expected[name]), identity)
            metrics['position_cm'].add((matrix.translation-expected[name].translation).length, identity)
            metrics['rotation_deg'].add(angle_delta(matrix, expected[name]), identity)
        if frame in (0, end):
            root_native.append(list(actual['bone_root'].translation))
    if legacy:
        arm.animation_data.action = legacy
        for frame in times:
            old = sample_matrices(arm, frame)
            for name, matrix in native_samples[frame].items():
                identity = dict(bone=name, frame=frame)
                metrics['legacy_position_cm'].add((matrix.translation-old[name].translation).length, identity)
                metrics['legacy_rotation_deg'].add(angle_delta(matrix, old[name]), identity)
            if frame in (0, end):
                root_legacy.append(list(old['bone_root'].translation))
    arm.animation_data.action = action
    result = {name: metric.result() for name, metric in metrics.items()}
    result.update(sample_frames=len(times), sample_step=.25 if quarter_frames else None,
                  all_integer_frames=True, subframe_samples=sum(t % 1. != 0 for t in times),
                  matrix_units_note='4x4 max mixes centimeter translation and dimensionless linear components',
                  native_root_endpoints_cm=root_native, legacy_root_endpoints_cm=root_legacy,
                  native_root_displacement_cm=[b-a for a, b in zip(*root_native)],
                  tolerances=dict(matrix_component_cm=.002, position_cm=.003, rotation_deg=.003))
    result['passed'] = (result['matrix_component_cm']['max'] < .002
                        and result['position_cm']['max'] < .003
                        and result['rotation_deg']['max'] < .003)
    return result


def verify_fbx(path, arm, frame_count, sample_step=1):
    """Reimport FBX and compare actual world matrices, hierarchy and bind pose.

    Blender FBX import uses automatic Euler curves; final UE importer is separate.
    Source rig coordinates are centimeters with .01 object scale. Metrics below
    convert world meters back to centimeters, matching the in-memory checks.
    """
    import bpy
    from io_scene_fbx import parse_fbx
    before_obj = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    expected_action = arm.animation_data.action
    end = frame_count - 1
    times = list(range(0, end+1, sample_step))
    if end not in times:
        times.append(end)
    # Cache only sampled matrices; importing Blender FBX moves the active action.
    expected = {frame: sample_matrices(arm, frame, world=True) for frame in times}
    expected_rest = {b.name: (arm.matrix_world @ b.matrix_local).copy() for b in arm.data.bones}
    raw, _ = parse_fbx.parse(str(path))
    fbx_objects = next(e for e in raw.elems if e.id == b'Objects')
    raw_scale = {}
    for model in fbx_objects.elems:
        if model.id != b'Model' or model.props[-1] != b'LimbNode':
            continue
        name = model.props[1].split(b'\x00')[0].decode('utf8')
        properties = next((e for e in model.elems if e.id == b'Properties70'), None)
        scaling = next((e.props[4:7] for e in properties.elems if e.id == b'P'
                        and e.props[0] == b'Lcl Scaling'), [1., 1., 1.]) if properties else [1., 1., 1.]
        raw_scale[name] = scaling
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=True, anim_offset=0,
                             automatic_bone_orientation=False, force_connect_children=False)
    created = set(bpy.data.objects) - before_obj
    imported = next(o for o in created if o.type == 'ARMATURE')
    if imported.animation_data is None or imported.animation_data.action is None:
        raise ValueError('FBX reimport has no animation action')
    action = imported.animation_data.action
    imported_range = list(action.frame_range)
    # Blender FBX adds no arbitrary time offset: the export starts at source0.
    shift = imported_range[0]
    metrics = {k: Metric() for k in ('matrix_component_cm', 'position_cm', 'rotation_deg',
                                    'bind_matrix_component_cm', 'uncorrected_matrix_component_cm',
                                    'raw_default_scale_error')}
    missing = sorted(set(arm.data.bones.keys())-set(imported.data.bones.keys()))
    hierarchy = []
    for b in arm.data.bones:
        other = imported.data.bones.get(b.name)
        if other is None:
            continue
        parent = b.parent.name if b.parent else None
        other_parent = other.parent.name if other.parent else None
        if parent != other_parent:
            hierarchy.append(dict(bone=b.name, expected=parent, actual=other_parent))
        actual_bind = imported.matrix_world @ other.matrix_local
        wanted_local = expected[0][b.name]
        if b.parent:
            wanted_local = expected[0][b.parent.name].inverted() @ wanted_local
        else:
            wanted_local = arm.matrix_world.inverted() @ wanted_local
        metrics['raw_default_scale_error'].add(max(abs(x-y) for x, y in
            zip(wanted_local.to_scale(), raw_scale[b.name])), dict(bone=b.name))
        # The disposable reference skin carries original bind matrices, so
        # this must match the production reference pose rather than source T0.
        metrics['bind_matrix_component_cm'].add(
            matrix_delta(actual_bind, expected_rest[b.name])*100, dict(bone=b.name))
    for frame in times:
        actual = sample_matrices(imported, frame+shift, world=True)
        for name, wanted in expected[frame].items():
            if name not in actual:
                continue
            original = actual[name]
            matrix = original
            identity = dict(bone=name, frame=frame)
            metrics['uncorrected_matrix_component_cm'].add(matrix_delta(original, wanted)*100, identity)
            metrics['matrix_component_cm'].add(matrix_delta(matrix, wanted)*100, identity)
            metrics['position_cm'].add((matrix.translation-wanted.translation).length*100, identity)
            metrics['rotation_deg'].add(angle_delta(matrix, wanted), identity)
    result = {name: metric.result() for name, metric in metrics.items()}
    result.update(bone_count=len(imported.data.bones), missing_bones=missing,
                  hierarchy_mismatches=hierarchy, imported_frame_range=imported_range,
                  duration_frames=imported_range[1]-imported_range[0], time_shift_frames=shift,
                  samples=len(times), tolerances=dict(position_cm=.01, rotation_deg=.02,
                  matrix_component_cm=.02, bind_position_cm=.01))
    result['node_defaults_note'] = ('A disposable 225-triangle reference skin pins '
        'the original skeleton bind matrices. Default nodes represent source T0; '
        'raw Lcl Scaling is checked separately. World pose matrices are compared '
        'directly without axis, scale, or bind compensation. UE imports animation '
        'only onto existing Skeleton with reference-pose update disabled.')
    result['passed'] = (not missing and not hierarchy and len(imported.data.bones) == len(arm.data.bones)
        and abs(result['duration_frames']-end) < .001
        and result['position_cm']['max'] < .01 and result['rotation_deg']['max'] < .02
        and result['matrix_component_cm']['max'] < .02
        and result['raw_default_scale_error']['max'] < .0001
        and result['bind_matrix_component_cm']['max'] < .01)
    for obj in created:
        bpy.data.objects.remove(obj, do_unlink=True)
    for created_action in set(bpy.data.actions)-before_actions:
        bpy.data.actions.remove(created_action)
    arm.animation_data.action = expected_action
    return result
