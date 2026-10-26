"""Small B04 binary/parser checks; no game, UE, asset edits or long suites."""
import hashlib
import json
import struct
from pathlib import Path
import native_connector_source as native


def run():
    pin = native.sources()
    blob = (native.ROOT/pin['mbd']['path']).read_bytes()
    parsed = native.parse_mbd(blob)
    assert native.encode_mbd(parsed) == blob
    # Independent fixed byte anchors, not offsets returned by the reader.
    anchors = [(101,129,4102,48), (105,118,5294,14), (108,124,5681,9)]
    for main,previous,offset,value in anchors:
        assert struct.unpack_from('<i',blob,offset)[0] == value
        assert native.entry_record(main,previous,parsed)['start_frame'] == value
    invalid = [blob[:n] for n in (0,15,len(blob)-1)] + [b'BAD!'+blob[4:],blob+b'\0']
    for bad in invalid:
        try: native.parse_mbd(bad)
        except ValueError: pass
        else: raise AssertionError('Accepted corrupt/truncated MBD')
    try: native.entry_record(170,308,parsed)
    except ValueError: pass
    else: raise AssertionError('Silently selected a phase/frame-dependent duplicate')
    report = native.run()
    assert len(report['connections'])==32
    assert len({r['id'] for r in report['connections']})==32
    assert sum(not r['mapping_matches'] for r in report['connections'])==2
    assert all(r['connector_exit_frame'] is None for r in report['connections'])
    assert not any(r['exit_phase_keys'] for r in report['connections'])
    assert report['implemented_new_connections']==0
    import author_behavior_corrections as author
    assert author.ROLL_STEP_ENTRY_FRAME == native.entry_frame(101,129)
    original = json.loads((native.OUT/'before-assets.json').read_text())
    current = {str(p.relative_to(native.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (native.ROOT/'Content/MHWI').rglob('*') if p.is_file()}
    assert original == current, 'Unexpected asset changes'
    for name in ('native_connector_source.py','verify_connector_source.py',
                 'author_behavior_corrections.py','audit_behavior_links.py'):
        compile((native.ROOT/'Scripts/MHWI'/name).read_text(encoding='utf-8-sig'),name,'exec')
    result = dict(passed=True,mbd_bytes=len(blob),entries=len(parsed['entries']),
                  blocks=report['mbd_blocks'],roundtrip=True,anchors=anchors,
                  corrupt_inputs_rejected=len(invalid),ambiguous_pair_rejected=True,
                  connector_nodes=30,references=32,target_mapping_conflicts=2,
                  explicit_exit_phase_keys=0,new_connections_implemented=0,
                  asset_files_unchanged=len(current),syntax_passed=True,
                  original_game_or_PIE_run=False)
    (native.OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result))
    return result


if __name__=='__main__': run()
