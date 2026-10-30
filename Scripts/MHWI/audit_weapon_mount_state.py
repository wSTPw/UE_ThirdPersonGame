"""Read-only extraction of the native weapon mount-state flag per action.

Reads the already-archived source audit (TIML tracks) and the project header.
Writes one report under Saved/MHWIRestoration; no UE, no game files, no assets.

The candidate bit is PlMotionCommon::mFlag bit 24 (0x01000000). It is reported
because it flips only inside draw/sheathe/iai actions, never inside attacks or
locomotion. Its exact native consumer is not decoded here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json'
HEADER = ROOT / 'Source/IntroCpp/MHWI/MHWIWeaponAttachment.h'
OUT = ROOT / 'Saved/MHWIRestoration/B21-20261028/weapon-mount-state.json'

BIT = 0x01000000
COMMON = 'nTimelineParam::PlMotionCommon'


def header_windows() -> dict[str, float]:
    """Project transfer windows, in frames, parsed from the shipped defaults."""
    text = HEADER.read_text(encoding='utf-8')
    rows: dict[str, float] = {}
    for name, num, den in re.findall(r'float (\w+)\s*=\s*([\d.]+)f\s*/\s*([\d.]+)f', text):
        rows[name] = round(float(num) / float(den) * 60.0, 4)
    return rows


def tracks_of(entry: dict) -> dict[tuple[str, str], list]:
    return {(g['name'], t['name']): t['keys'] for g in entry['groups'] for t in g['tracks']}


def flag_transitions(keys: list, bit: int) -> list[dict]:
    out: list[dict] = []
    if int(keys[0]['value']) & bit:
        out.append({'frame': keys[0]['frame'], 'state': 'ON', 'source': 'clip_start'})
    for a, b in zip(keys, keys[1:]):
        if (int(a['value']) & bit) != (int(b['value']) & bit):
            out.append({'frame': b['frame'], 'state': 'ON' if int(b['value']) & bit else 'OFF',
                        'source': 'key'})
    return out


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    windows = header_windows()
    clips = []
    for entry in audit['source']['entries']:
        tracks = tracks_of(entry)
        flag = tracks.get((COMMON, 'mFlag'))
        motion = tracks.get((COMMON, 'mWeaponMotionNo'))
        if not flag and not motion:
            continue
        events = [{'frame': k['frame'], 'motion_no': k['value']} for k in (motion or [])
                  if int(k['value']) >= 0]
        clips.append({
            'index': entry['index'],
            'frame_count': entry['source_frame_count'],
            'seconds': round((entry['source_frame_count'] - 1) / 60.0, 4),
            'flag_bit24_start': bool(int(flag[0]['value']) & BIT) if flag else None,
            'flag_bit24_transitions': flag_transitions(flag, BIT) if flag else [],
            'weapon_motion_events': events,
        })

    toggling = [c for c in clips if c['flag_bit24_transitions']]
    switching = [c for c in clips if c['weapon_motion_events']]
    report = {
        'schema_version': 1,
        'status': 'source_static_only_not_ue_or_game_runtime',
        'source': {'audit': str(AUDIT.relative_to(ROOT)), 'bit': hex(BIT),
                   'class': COMMON, 'track': 'mFlag'},
        'interpretation': 'candidate native weapon mount/state bit; consumer not decoded',
        'clip_count': len(clips),
        'clips_with_flag_track': sum(1 for c in clips if c['flag_bit24_start'] is not None),
        'clips_toggling_bit24': len(toggling),
        'clips_with_weapon_motion': len(switching),
        'project_windows_frames': windows,
        'toggling_clips': toggling,
        'clips': clips,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')

    print(f'clips analysed {len(clips)}; bit24 toggles in {len(toggling)}; weapon-motion clips {len(switching)}')
    for c in toggling:
        flips = ', '.join(f"{t['frame']:g}->{t['state']}" for t in c['flag_bit24_transitions'])
        evs = ', '.join(f"{e['frame']:g}:m{e['motion_no']}" for e in c['weapon_motion_events']) or '-'
        print(f"  w03_00_{c['index']:03d} {c['frame_count']:>4}f  flag {flips:<28} motion {evs}")
    print('project windows (frames):', windows)
    print('report', OUT.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
