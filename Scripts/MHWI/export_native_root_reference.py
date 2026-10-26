"""Blender: source-root reference for UE qualification, without exporting assets.

Run with the same pinned sampler and production rig as export_native_animation.
The production importer removes the Armature object node. Its raw root track
uses armature-local centimeters, before the component axis basis, with FBX's
right-handed Y converted to UE's left-handed Y (FFbxDataConverter::ConvertPos).
"""
from pathlib import Path
import json
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_animation_source as native
import verify_native_animation as verify


def main():
    manifest = json.loads((native.OUTPUT / 'export-manifest.json').read_text(encoding='utf8'))
    bpy.ops.wm.open_mainfile(filepath=str(native.BLEND))
    arm = bpy.data.objects['Armature']
    rest = {b.name: native.rest_local(arm, b.name).decompose() for b in arm.data.bones}
    result = {'clips': [], 'boundary': 'Direct native sampler, production raw-root convention; UE centimeters.'}
    for item in manifest['clips']:
        if not item.get('eligible_for_runtime'):
            continue
        evaluation = native.compiled_action(arm, item['clip'])
        end = item['frame_count'] - 1
        frames = sorted({0, end // 4, end // 2, end * 3 // 4, end})
        samples = []
        for frame in frames:
            root = verify.expected_matrices(arm, evaluation, frame, rest)['bone_root']
            position = root.translation
            samples.append({'frame': frame, 'position_cm': [position.x, -position.y, position.z]})
        result['clips'].append({'clip': item['clip'], 'fbx_sha256': item['sha256'], 'samples': samples})
    result['dependencies'] = native.dependency_evidence()
    target = native.ROOT / 'Saved/MHWIImport/NativeFidelity-20261024/native-root-reference.json'
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('ROOT_REFERENCE_COMPLETE', len(result['clips']), flush=True)


if __name__ == '__main__':
    main()
