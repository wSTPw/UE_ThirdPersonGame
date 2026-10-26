"""Re-trace the pinned B13 follow-up functions and compare their snapshots.

Reads the fixed-version local analysis text and the tracked follow-up manifest.
The output is a local verification record; no game code or installation file is
executed or modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from trace_outstanding_evidence import Evidence

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / 'Tools/MHW/native-outstanding-followup.json'
DEFAULT_OUTPUT = ROOT / 'Saved/MHWIRestoration/B17-20261026/followup-function-revalidation.json'
FIELDS = ('entry', 'requested', 'spans', 'instructions', 'gaps', 'switches')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT,
                        help='Local output JSON path (default: ignored Saved directory)')
    args = parser.parse_args()

    source = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    evidence = Evidence()
    expected_exe = source['pins']['exe']['sha256']
    expected_text = source['pins']['text']['sha256']
    actual_exe = evidence.tr.pin['exe']['sha256']
    actual_text = evidence.tr.pin['text']['sha256']
    if (actual_exe, actual_text) != (expected_exe, expected_text):
        raise ValueError('Follow-up snapshot source pins do not match the local analysis source')

    checks = []
    for saved in source['functions']:
        requested = saved['requested']
        current = evidence.function(int(requested, 0))
        mismatches = [field for field in FIELDS if current[field] != saved[field]]
        checks.append(dict(requested=requested, match=not mismatches,
                           matched_fields=[field for field in FIELDS if field not in mismatches],
                           mismatched_fields=mismatches,
                           instruction_count_saved=len(saved['instructions']),
                           instruction_count_current=len(current['instructions']),
                           gap_count_saved=len(saved['gaps']),
                           gap_count_current=len(current['gaps'])))

    result = dict(schema=1,
        scope='re-trace of fixed-version local analysis text; direct reachable CFG only; no game execution',
        exe_sha256=actual_exe, analysis_text_sha256=actual_text,
        source_snapshot=SNAPSHOT.relative_to(ROOT).as_posix(),
        snapshot_sha256=sha256(SNAPSHOT), count=len(checks),
        matched=sum(row['match'] for row in checks), checks=checks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=result['matched'] == result['count'],
                          count=result['count'], matched=result['matched'],
                          output=args.output.as_posix())))
    if result['matched'] != result['count']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
