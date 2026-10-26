"""Read source-declared IK fields and inventory raw equipment/control resources.

The four IK XFS19 resources declare the member names and scalar type IDs in
their own definitions. Matrix19/Vector35 widths are checked by every nested
record boundary and complete file consumption. No UE IK solver is inferred.
"""
from pathlib import Path
import hashlib
import json
import struct

from read_source_fsm import XfsReader

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'ArtSource/ThirdParty/MHWLongSword/NativeParameters'
OUTPUT = ROOT / 'Saved/MHWIImport/NativeParameterResearch-20261024'


class IKReader(XfsReader):
    def __init__(self, data):
        super().__init__(data)
        self.field_spans = []

    def read_value(self, kind):
        if kind == 19:
            return self.read('16f')
        if kind == 35:
            return self.read('3f')
        return super().read_value(kind)

    def read_class(self):
        record_offset = self.pos
        class_id, variable_id = self.read('HH')
        if class_id // 2 >= len(self.defs):
            raise ValueError('Unknown XFS class %d' % class_id)
        size_start = self.pos
        size = self.read('Q')
        result = {'_class_id': class_id, '_variable_id': variable_id}
        for name, kind in self.defs[class_id // 2]:
            count = self.read('I')
            offset = self.pos
            values = [self.read_value(kind) for _ in range(count)]
            result[name] = values[0] if count == 1 else values
            self.field_spans.append(dict(record_offset=record_offset, class_id=class_id,
                variable_id=variable_id, name=name, type_id=kind, count=count,
                offset=offset, serialized_bytes=self.pos-offset))
        if self.pos != size_start + size:
            raise ValueError(('class_size', class_id, self.pos, size_start + size))
        return result


def run():
    manifest = json.loads((SOURCE / 'extraction-manifest.json').read_text(encoding='utf8'))
    resources, ik = [], []
    for original in manifest['files']:
        path = SOURCE / 'nativePC' / original['path'].lstrip('/')
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != original['sha256']:
            raise ValueError('Extracted resource changed: ' + str(path))
        row = dict(path=path.relative_to(ROOT).as_posix(), sha256=digest, bytes=len(data),
                   magic_hex=data[:8].hex(), archive=original['archive'])
        if path.suffix == '.ik':
            reader = IKReader(data)
            parsed = reader.parse()
            if reader.pos != len(data):
                raise ValueError('Unconsumed IK bytes: ' + str(path))
            body = parsed['root']
            joints = body['mJoint'] if isinstance(body['mJoint'], list) else [body['mJoint']]
            active = [j['mJntNo'] for j in joints[:body['mJointNum']]]
            ik.append(dict(**row, parsed=parsed, field_spans=reader.field_spans,
                           complete_consumption=True, active_joint_numbers=active,
                           binding_boundary='Native joint IDs, not automatically verified UE compact-pose indices.'))
            row.update(resource_class='rCnsIK', parsed=True)
        elif path.suffix == '.cms':
            row.update(resource_class='rCameraSetting', parsed=False,
                       disposition='Camera configuration; excluded from weapon mount inference.')
        else:
            row.update(resource_class={'.ctm': 'rContactManager', '.arm_mgr': 'rArmManager',
                '.leg_mgr': 'rLegManager', '.ikctrl': 'rIKCtrl'}.get(path.suffix), parsed=False)
        resources.append(row)
    result = dict(schema=1, passed=True, source_manifest_sha256=hashlib.sha256(
        (SOURCE/'extraction-manifest.json').read_bytes()).hexdigest(), resources=resources, ik=ik,
        class_reference='https://gist.github.com/Andoryuuta/7520bcded08f8d5830baaee4b3b99671',
        serialization_sizes={'19': '16 float32, source field mOffsetMat', '35': '3 float32, source fields mCenterPosOffset/mTransScale'},
        boundaries=['IK structure is decoded, not an implementation of the original IK solver or weapon attachment.',
                    'Non-XFS manager/CTM records remain raw; no guessed transforms are applied.'])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT/'equipment-native-parameters.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed': True, 'resources': len(resources), 'ik_complete': len(ik),
                      'chains': {Path(r['path']).name: r['active_joint_numbers'] for r in ik}}))
    return result


if __name__ == '__main__':
    run()
