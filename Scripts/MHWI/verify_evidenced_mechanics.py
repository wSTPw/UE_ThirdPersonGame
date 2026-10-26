"""Verify B14 retained-source values and its saved DA snapshot; no UE/PIE."""
import argparse
import json
from pathlib import Path

from author_b14_evidenced_mechanics import source_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--da', type=Path, required=True,
                        help='Saved B14 authored.json (not a historical B12 snapshot)')
    args = parser.parse_args()
    errors = []
    checks = []

    def check(condition, label):
        checks.append(label)
        if not condition:
            errors.append(label)

    globals_expected, evidence = source_values()
    check(globals_expected['spirit_gauge_decay_time_scale'] == 120.0, 'Q time scale is 120')
    check(abs(globals_expected['spirit_gauge_decay_fraction'] - 0.05) < 1e-6, 'Q decay fraction is 0.05')
    check(globals_expected['spirit_decay_pause_on_raise_seconds'] == 10.0, 'Roundslash colour pause is 10 seconds')
    check(abs(globals_expected['helm_shell_first_delay'] - 0.4) < 1e-6, 'Helm first delay is 0.4 seconds')
    check(abs(globals_expected['helm_shell_interval'] - 0.05) < 1e-6, 'Helm interval is 0.05 seconds')
    check(globals_expected['helm_shell_hit_limit'] == 7, 'Helm hit limit is seven')
    check(globals_expected['helm_shell_damage_by_level'] == [0., 10., 15., 25.], 'Helm shell colour bases')
    check(globals_expected['iai_shell_delay'] == 0.5, 'Iai second-hit delay is 0.5 seconds')
    check(globals_expected['iai_shell_damage_by_level'] == [0., 55., 72., 86.], 'Iai shell colour bases')
    check(globals_expected['evasion_protection_frames'] == [13., 15., 17., 19., 22., 25.], 'PLP evade table')
    check(globals_expected['evasion_mantle_protection_frames'] == 30.0, 'PLP mantle protection is 30 frames')
    check(globals_expected['special_sheath_hold_seconds'] == 3.5, 'Special-sheathe wait is 3.5 seconds')

    if not args.da.is_file():
        errors.append('B14 DA snapshot missing: ' + str(args.da))
    else:
        report = json.loads(args.da.read_text(encoding='utf-8'))
        check(report.get('saved') is True, 'B14 snapshot is a saved asset report')
        check(report.get('idempotent') is True, 'B14 authoring is idempotent')
        check(report.get('protected_fields_unchanged') is True, 'B14 full move protection passed')
        moves = report.get('after', {})
        helm_windows = moves.get('SpiritHelmBreaker', {}).get('damage_windows', [])
        check(len(helm_windows) == 1, 'DA has one aerial COL#28 window')
        if len(helm_windows) == 1:
            window = helm_windows[0]
            check(window.get('col_record_index') == 28, 'DA aerial hit remains COL#28')
            check(abs(float(window.get('damage', 0.)) - 126.) < 1e-4, 'DA aerial MV remains 126')
            check(abs(float(window.get('hit_lag_seconds', -1.))) < 1e-6, 'DA aerial hit-stop is zero')
        check(moves.get('HelmLand', {}).get('damage_windows') == [], 'DA has no direct landing seven-window damage')
        check(report.get('globals_after') == globals_expected, 'DA globals equal the source-derived B14 values')
        check(report.get('source_evidence', {}).get('plp_availability', '').startswith('reviewed manifest'),
              'Report explicitly bounds PLP evidence to the reviewed manifest')

    result = {'passed': not errors, 'checks': len(checks), 'errors': errors,
              'scope': 'retained source bytes/manifest plus B14 saved DA snapshot; no original game, UE or PIE',
              'external_cross_sources': evidence['external_cross_sources']}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
