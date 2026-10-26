"""Read native weapon curves and qualified export hashes, without starting UE.

This audits source consistency only. It does not validate the C++ fitting,
rendered contact, body penetration, or gameplay. Output goes under Saved/.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

import native_animation_source as native

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'Saved/MHWIImport/WeaponPlacement-20261024'


def run():
    manifest_path = ROOT / 'Saved/MHWIImport/NativeFidelity-20261024/weapon-animation-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    reader, pose = native.native_modules()
    source = ROOT / manifest['source']['path']
    bank = reader.read_lmt_file(source)
    motions = {}
    for action in bank.actions:
        curves = {track.header.usage: pose.compile_pose_curve(track) for track in action.tracks}
        motions[action.id] = dict(
            frames=action.header.frame_count,
            animated_functions=sorted({track.header.bone_id for track in action.tracks}),
            first_translation=list(curves[1].sample(0)),
            last_translation=list(curves[1].sample(action.header.frame_count - 1)))

    def near(left, right):
        return max(abs(x - y) for x, y in zip(left, right)) < .01

    checks = dict(
        six_native_internal_motions=set(motions) == set(range(6)),
        native2_starts_at_sheathed0=near(motions[2]['first_translation'], motions[0]['first_translation']),
        native2_ends_at_drawn1=near(motions[2]['last_translation'], motions[1]['first_translation']),
        native3_starts_at_drawn1=near(motions[3]['first_translation'], motions[1]['first_translation']),
        native3_ends_at_sheathed0=near(motions[3]['last_translation'], motions[0]['first_translation']))
    protected = [manifest['source'], manifest['source_blend'],
                 *[clip['fbx'] for clip in manifest['clips']]]
    sources = []
    for entry in protected:
        path = ROOT / entry['path']
        actual = native.evidence(path)['sha256']
        sources.append(dict(path=entry['path'], sha256=actual,
                            matches_qualified_export=actual == entry['sha256']))
    checks['qualified_sources_unchanged'] = all(row['matches_qualified_export'] for row in sources)
    report = dict(status='offline_source_consistency_only',
        utc_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        passed=all(checks.values()), checks=checks, motions=motions,
        protected_sources=sources, ue_pie_executed=False,
        visual_acceptance='reserved_for_user')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / 'source-consistency.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(dict(passed=report['passed'], checks=checks, report=str(path))))
    if not report['passed']:
        raise RuntimeError('Native weapon source consistency failed; see ' + str(path))
    return report


if __name__ == '__main__':
    run()
