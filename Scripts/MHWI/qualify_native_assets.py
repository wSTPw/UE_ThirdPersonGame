"""Read-only UE checks after native FBX import, including runtime source identity."""
from pathlib import Path
import datetime
import hashlib
import json
import math

import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024'


def _angle(a, b):
    left = [a.x, a.y, a.z, a.w]
    right = [b.x, b.y, b.z, b.w]
    dot = abs(sum(x*y for x, y in zip(left, right)))
    dot /= math.sqrt(sum(x*x for x in left) * sum(x*x for x in right))
    return math.degrees(2 * math.acos(min(1., dot)))


def run():
    manifest = json.loads((ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json').read_text(encoding='utf8'))
    root_reference = {r['clip']: r for r in json.loads((OUT / 'native-root-reference.json').read_text(encoding='utf8'))['clips']}
    result = {'passed': False, 'utc_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'checks': [], 'clips': [], 'correction_samples': [],
              'boundary': 'Native CPU sampler/FBX qualification plus actual UE poses; not an original-game execution comparison.'}
    def check(condition, label):
        result['checks'].append({'check': label, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(label)
    try:
        for item in manifest['clips']:
            if not item['eligible_for_runtime']:
                continue
            clip = item['clip']
            bank = 'Common' if clip.startswith('co00') else 'LongSword'
            path = '/Game/MHWI/Animations/NativeFidelity/' + bank + '/A_' + clip
            new = unreal.load_asset(path)
            old = unreal.load_asset('/Game/MHWI/Animations/' + bank + '/A_' + clip)
            check(isinstance(new, unreal.AnimSequence) and old is not None, clip + ': imported and legacy sequences exist')
            check(new.get_editor_property('skeleton') == old.get_editor_property('skeleton'), clip + ': original Skeleton identity retained')
            check(abs(new.get_play_length() - old.get_play_length()) < .0001, clip + ': exact duration preserved')
            check(abs(new.get_play_length() - item['duration']) < .0001, clip + ': native frame range preserved')
            check(new.get_editor_property('root_motion_root_lock') == unreal.RootMotionRootLock.REF_POSE,
                  clip + ': REF_POSE root basis retained')
            max_root_error = 0.
            max_root_angle = 0.
            max_endpoint_error = 0.
            max_source_root_error = 0.
            options = unreal.AnimPoseEvaluationOptions(extract_root_motion=False, incorporate_root_motion_into_pose=True)
            reference = root_reference[clip]
            check(reference['fbx_sha256'] == item['sha256'], clip + ': source-root reference matches qualified FBX')
            for sample in reference['samples']:
                frame = sample['frame']
                seconds = frame / 60.
                a = unreal.AnimPoseExtensions.get_anim_pose_at_time(old, seconds, options)
                b = unreal.AnimPoseExtensions.get_anim_pose_at_time(new, seconds, options)
                check(len(unreal.AnimPoseExtensions.get_bone_names(b)) == 225, clip + ': full 225-bone pose at frame%d' % frame)
                ra = unreal.AnimPoseExtensions.get_bone_pose(a, 'bone_root', unreal.AnimPoseSpaces.WORLD)
                rb = unreal.AnimPoseExtensions.get_bone_pose(b, 'bone_root', unreal.AnimPoseSpaces.WORLD)
                max_root_error = max(max_root_error, float((ra.translation-rb.translation).length()))
                max_root_angle = max(max_root_angle, _angle(ra.rotation, rb.rotation))
                if frame in (0, item['frame_count'] - 1):
                    max_endpoint_error = max(max_endpoint_error, float((ra.translation-rb.translation).length()))
                expected = unreal.Vector(*sample['position_cm'])
                max_source_root_error = max(max_source_root_error, float((rb.translation-expected).length()))
                if clip in ('w03_00_129', 'w03_00_173'):
                    for bone in ('bone_030', 'bone_048'):
                        pa = unreal.AnimPoseExtensions.get_bone_pose(a, bone, unreal.AnimPoseSpaces.LOCAL)
                        pb = unreal.AnimPoseExtensions.get_bone_pose(b, bone, unreal.AnimPoseSpaces.LOCAL)
                        result['correction_samples'].append({'clip': clip, 'bone': bone, 'seconds': seconds,
                            'rotation_change_degrees': _angle(pa.rotation, pb.rotation)})
            # Legacy interpolation is one of the defects being repaired. Match
            # the native reference at interior frames, not the old curve shape.
            check(max_source_root_error < .01, clip + ': UE root matches direct source sampler within .01cm')
            check(max_endpoint_error < .5, clip + ': root endpoints retain legacy displacement within .5cm')
            check(max_root_angle < 2., clip + ': root axis/rotation compatibility within 2deg')
            result['clips'].append({'clip': clip, 'asset': path, 'length': new.get_play_length(),
                                    'max_root_difference_cm': max_root_error, 'max_root_difference_deg': max_root_angle,
                                    'max_root_endpoint_difference_cm': max_endpoint_error,
                                    'max_source_root_error_cm': max_source_root_error})
        for clip in ('w03_00_129', 'w03_00_173'):
            measured = [r['rotation_change_degrees'] for r in result['correction_samples'] if r['clip'] == clip]
            check(max(measured) > 5., clip + ': corrected compressed rotation reaches the UE asset')
        data = unreal.load_asset('/Game/MHWI/Data/DA_MHWI_LongSword')
        defs = data.get_editor_property('moves')
        check(len(defs) == 32, 'formal moveset keeps 32 move identities')
        check(len(data.get_editor_property('weapon_motions')) == 6, 'formal moveset uses six independent weapon clips')
        references = []
        for key, definition in defs.items():
            montage = definition.get_editor_property('montage')
            if not montage:
                continue
            for track in montage.get_editor_property('slot_anim_tracks'):
                for segment in track.get_editor_property('anim_track').get_editor_property('anim_segments'):
                    seq = segment.get_editor_property('anim_reference')
                    references.append({'move': str(key), 'montage': montage.get_path_name(), 'sequence': seq.get_path_name()})
        result['formal_references'] = references
        result['passed'] = True
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'ue-assets-qualification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'passed': result['passed'], 'clips': len(result['clips']), 'checks': len(result['checks'])}))
    return result
