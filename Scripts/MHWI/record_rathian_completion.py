"""Publish compact completion evidence after live editor verification."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BATCH=ROOT/'Saved/RathianAnimationCompletion-20261030'
def main():
    verification=json.loads((BATCH/'verification.json').read_text())
    assert verification['passed']
    exp=json.loads((BATCH/'export.json').read_text())
    imp=json.loads((BATCH/'import.json').read_text())
    assert len(imp['imported'])==len(exp['exported'])
    result=dict(schema=1,monster='em001 Rathian',destination='/Game/MHWI/Rathalos/Animations',skeleton='/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton',verification=verification,
                sources=json.loads((ROOT/'ArtSource/ThirdParty/MHWRathalos/extraction-manifest.json').read_text())['source'],
                added=[dict(name=r['name'],bank=r['bank'],source_frames=r['source_frames'],expected_seconds=r['expected_seconds'],fbx_sha256=r['sha256']) for r in exp['exported']],
                existing=exp['existing'],import_readback=imp['imported'],
                scripts={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['Tools/MHW/complete_rathian_animations.py','Scripts/MHWI/complete_rathian_import.py','Scripts/MHWI/verify_rathian_completion.py']},
                boundary='Source motion-bank coverage and UE asset readback only. Legacy 24 assets preserved; no original-game pose/overlay/behavior fidelity claim.')
    (ROOT/'Tools/MHW/rathian-animation-completion.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:verification[k] for k in ['total','added','preserved']}))
if __name__=='__main__':main()
