"""Author R06 runtime source tables. Extraction only: no tests or editor calls."""
import json
from pathlib import Path
from read_source_fsm import XfsReader
from audit_native_timing import parse_lmt, names
from native_connector_source import sources

ROOT = Path(__file__).resolve().parents[2]


def run():
    policy = json.loads((ROOT/'Tools/MHW/native-link-motion-policy.json').read_text(encoding='utf8'))
    main_bindings = json.loads((ROOT/'Tools/MHW/native-main-motion-bindings.json').read_text(encoding='utf8'))['bindings']
    pin = sources()
    fsm = XfsReader((ROOT/pin['fsm']['path']).read_bytes()).parse()['root']
    mapping = json.loads((ROOT/pin['mapping']['path']).read_text(encoding='utf8'))
    labels = ROOT/'Saved/MHWIImport/SourceFidelity-20261023/timing-FreeHK-upstream/MHW-Free-HyperKinetics-main/struct'
    bank = parse_lmt(ROOT/pin['lmt']['path'], names(labels/'TIMLTimelineParam.txt'), names(labels/'TIMLDatatypes.txt', True))
    identities = []
    for node in fsm['mpRootCluster']['mpNodeList']:
        action = node['mpProcessList']['mpParameter'].get('ActionNo')
        if action is None:
            continue
        number = action['EnumValue']
        row = policy['weapon_identity_overrides'].get(str(number)) or policy['common_identity_overrides'].get(str(number))
        for pair in row['pairs'] if row else [[3, number]]:
            identities.append(dict(node=node['mId'], identity=pair))
    moves = {name: value['fsm_node_id'] for name, value in mapping['moves'].items()}
    # Existing project aliases, read from author_assets/reference_basics/spirit_branches.
    # These identify the existing action adapter; they do not assert MotionNo=ActionNo.
    moves.update(DrawSlash=11, RollStepSlash=11, SpiritComboThrust=23,
                 SpiritComboRisingSlash=38, Roll=13, WalkOnSlash=41,
                 RollRight=14, RollBack=15, RollLeft=16)
    # Native source action 34 is CreepSingleMotion, NOT the project's Draw(002).
    # Native 1002 resolves StepS/M/L variants, NOT the project's sheathed Roll.
    connectors = {r['connector_motion'] for r in policy['references']}
    motion_rows = []
    weapons = []
    phase_keys = []
    for m in bank['entries']:
        motion_rows.append(dict(motion=m['index'], frames=m['source_frame_count'], loop=m['source_loop_frame']))
        for g in m['groups']:
            for t in g['tracks']:
                if t['name'] == 'mLinkMotionPhase':
                    if t['kind'] != 0 or any(k['transition'] != 1 for k in t['keys']):
                        raise ValueError('New Phase interpolation needs native consumer review')
                    phase_keys.extend(dict(bank='w03_00', motion=m['index'], frame=k['frame'], value=k['value']) for k in t['keys'])
                if m['index'] in connectors and t['name'] == 'mWeaponMotionNo':
                    weapons.extend(dict(motion=m['index'], frame=k['frame'], value=k['value'],
                                        transition=k['transition']) for k in t['keys'])
    common_path = ROOT/'ArtSource/ThirdParty/MHWLongSword/nativePC/hm/common/mot/co00_00/co00_00.lmt'
    common = parse_lmt(common_path, names(labels/'TIMLTimelineParam.txt'), names(labels/'TIMLDatatypes.txt', True))
    for m in common['entries']:
        for g in m['groups']:
            for t in g['tracks']:
                if t['name'] == 'mLinkMotionPhase':
                    if t['kind'] != 0 or any(k['transition'] != 1 for k in t['keys']):
                        raise ValueError('Common-bank Phase interpolation needs native review')
                    phase_keys.extend(dict(bank='co00_00', motion=m['index'], frame=k['frame'], value=k['value']) for k in t['keys'])
    def f(v):
        s = format(float(v), '.9g')
        return s + ('.0' if '.' not in s and 'e' not in s.lower() else '') + 'f'
    lines = ['// Source extraction by build_link_runtime_data.py; not test evidence.',
             '#pragma once', 'namespace MHWI::Native {', 'inline const FNodeIdentity NodeIdentities[] = {']
    lines += ['    {%d, {%d, %d}},' % (r['node'], *r['identity']) for r in identities]
    lines += ['};', 'inline const FMoveNode MoveNodes[] = {']
    lines += ['    {FName(TEXT("%s")), %d},' % (k, v) for k, v in moves.items()]
    lines += ['};', 'inline const FMoveTimeline MoveTimelines[] = {']
    lines += ['    {FName(TEXT("%s")), %d},' % (k, int(v['clip'].rsplit('_', 1)[1]))
              for k, v in mapping['moves'].items()]
    lines += ['};', 'inline const FMainMotionBinding MainMotionBindings[] = {']
    lines += ['    {%d, %d},' % (r['node'], r['main_motion']) for r in main_bindings]
    lines += ['};', 'inline const FMotionInfo MotionInfos[] = {']
    lines += ['    {%d, %d, %d},' % (r['motion'], r['frames'], r['loop']) for r in motion_rows]
    lines += ['};', 'inline const FPhaseKey PhaseKeys[] = {']
    lines += ['    {FName(TEXT("%s")), %d, %s, %d},' % (r['bank'], r['motion'], f(r['frame']), r['value']) for r in phase_keys]
    lines += ['};', 'inline const FConnectorWeaponKey ConnectorWeaponKeys[] = {']
    lines += ['    {%d, %s, %d},' % (r['motion'], f(r['frame']), r['value']) for r in weapons]
    lines += ['};', 'inline const int32 ConnectorMotions[] = {',
              '    '+', '.join(str(n) for n in sorted(connectors)), '};', '}']
    (ROOT/'Source/IntroCpp/MHWI/MHWILinkRuntimeData.inl').write_text('\n'.join(lines)+'\n', encoding='utf8')
    out = ROOT/'Saved/MHWIRestoration/B10-20261025'
    out.mkdir(parents=True, exist_ok=True)
    (out/'runtime-source-data.json').write_text(json.dumps(dict(
        tests_executed=False, sources=pin, node_identities=identities, project_move_nodes=moves,
        motions=motion_rows, phase_keys=phase_keys, connector_weapon_keys=weapons, main_bindings=main_bindings,
        common_phase_source=dict(path=common['path'], sha256=common['sha256']),
        native_phase_consumer=['1424a7440','1424a8580','1424a8770'],
        boundary='Project aliases are existing adapters, not native main-motion constructor proof.'
    ), ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(authored=True, tests_executed=False, motions=len(motion_rows))))


if __name__ == '__main__':
    run()
