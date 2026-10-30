"""Adjudicate actual B20 prefix/main samples against pinned original references.

One sampled pipeline does not certify every incoming identity or human-input
precondition. The orphan N86 is verified as a static negative, never played.
"""
import hashlib
import json
from pathlib import Path
import native_connector_source as source
from read_source_fsm import XfsReader

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'Saved/MHWIRestoration/B20-20261027'
OUT = ROOT / 'Tools/MHW/b20-r06-runtime-coverage.json'


def fields(text):
    return dict(token.split('=', 1) for token in text.split())


def main():
    pins = source.sources()
    policy = json.loads((ROOT / 'Tools/MHW/native-link-motion-policy.json').read_text(encoding='utf-8'))
    fsm = XfsReader((ROOT / pins['fsm']['path']).read_bytes()).parse()['root']
    nodes = {row['mId']: row for row in fsm['mpRootCluster']['mpNodeList']}
    refs = {row['id']: row for row in policy['references']}
    samples = {key: [] for key in refs}
    report_files = []
    for filename in ('PIE-r06-connections.json', 'PIE-r06-impact-matrix.json'):
        path = BATCH / filename
        data = json.loads(path.read_text(encoding='utf-8'))
        if not data.get('passed'):
            raise AssertionError('Actual matrix failed: ' + filename)
        report_files.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for row in data['cases']:
            entry = fields(row.get('entry', row.get('source_entry', '')))
            prefix, main = row['prefix'], row['first_main']
            if filename == 'PIE-r06-connections.json':
                candidate_refs = [row['reference']]
            else:
                # Common standing steps152/151 are dedicated overrides, not
                # proof of the weapon-only generic N53/N60 record lists.
                candidate_refs = [key for key in ('R06-N53-P0', 'R06-N60-P0', 'R06-N60-P1')
                                  if entry['target'] == '/'.join(map(str, refs[key]['target_native_identity']))
                                  and int(entry['phase']) == refs[key]['phase']
                                  and int(prefix['body']) == refs[key]['connector_motion']
                                  and entry['previous'].startswith('3/')]
            for key in candidate_refs:
                ref = refs[key]
                if (int(prefix['body']) != ref['connector_motion'] or int(entry['phase']) != ref['phase']
                        or entry['target'] != '/'.join(map(str, ref['target_native_identity']))
                        or int(main['timeline']) != ref['project_main_motion']):
                    raise AssertionError('Actual request differs from the original reference: ' + key)
                allowed = set()
                for incoming in ref['incoming']:
                    number = nodes[incoming['source_node']]['mpProcessList']['mpParameter']['ActionNo']['EnumValue']
                    override = policy['weapon_identity_overrides'].get(str(number)) or policy['common_identity_overrides'].get(str(number))
                    if override:
                        allowed.update(tuple(pair) for pair in override['pairs'])
                    else:
                        allowed.add((3, number))
                previous = tuple(map(int, entry['previous'].split('/')))
                if previous not in allowed:
                    raise AssertionError('Actual source is not an incoming owner: ' + key + str(previous))
                starts = {b['start_frame'] for b in ref['mbd_main_candidates'] if b['animation_id'] == int(prefix['body']) and b['declaration'] == prefix['bank']}
                if len(starts) != 1:
                    raise AssertionError('Independent original main entry is ambiguous: ' + key)
                start = next(iter(starts))
                if not start <= float(main['frame']) < start+6:
                    raise AssertionError('Actual main clock differs from MBD entry: ' + key)
                if prefix['serial'] != main['serial'] or prefix['instance'] == main['instance']:
                    raise AssertionError('Main transaction/instance replacement failed: ' + key)
                if prefix['gauge_start'] != main['gauge_start'] or prefix['gauge'] != main['gauge']:
                    raise AssertionError('Observed resource changed across this prefix commit: ' + key)
                # Runtime node13 deliberately accepts two native forward-roll
                # identities after proving they request the same plan. The
                # diagnostic prints its first candidate; do not turn that into
                # evidence that action18 specifically ran instead of action19.
                ambiguous = key == 'R06-N52-P0' and row.get('source', {}).get('move') == 'Roll'
                candidates = [[3, 18], [3, 19]] if ambiguous else [list(previous)]
                samples[key].append(dict(report=filename, previous_identity=None if ambiguous else list(previous),
                                         previous_identity_candidates=candidates, exact_previous_identity=not ambiguous, entry=entry,
                                         prefix=prefix, first_main=main, expected_mbd_frame=start,
                                         same_execution_new_instance=True, no_second_charge_observed=True))
    rows = []
    for key, ref in refs.items():
        if key == 'R06-N86-P0':
            if ref['incoming'] or ref['runtime_record_count'] != 0 or samples[key]:
                raise AssertionError('Orphan reference must remain unreachable')
            status = 'static_unreachable_negative_verified'
        elif samples[key]:
            status = 'representative_pipeline_runtime_verified'
        else:
            raise AssertionError('No actual prefix/main sample for reference: ' + key)
        rows.append(dict(id=key, status=status, native_identity_record_count=ref['runtime_record_count'],
                         observed_previous_identities=sorted({tuple(s['previous_identity']) for s in samples[key] if s['exact_previous_identity']}),
                         ambiguous_candidate_sets=[s['previous_identity_candidates'] for s in samples[key] if not s['exact_previous_identity']],
                         sample_count=len(samples[key]), samples=samples[key],
                         boundary='Representative actual project route and MBD clock only; no blanket full incoming-owner, original mode0, or native input-window certification'))
    out = dict(schema=1, passed=True, scope=__doc__, original_source_pins=pins, reports=report_files,
               runtime_references=sum(bool(samples[key]) for key in samples), static_negative_references=1,
               total_references=len(rows), rows=rows,
               remaining='N53/N60 other owners/phase boundaries, Action78 predecessor for332/333/334, native mode0 MotionTree and R07 input semantics remain separate open work')
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, runtime_references=out['runtime_references'], static_negative_references=1, total_references=len(rows))))


if __name__ == '__main__':
    main()
