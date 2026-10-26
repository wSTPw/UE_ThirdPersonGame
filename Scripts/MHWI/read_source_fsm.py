"""Read-only MT Framework XFS19 inspector for the supplied MHW FSM.

Layout reference: https://github.com/Strackeror/MHW-Fsm/blob/main/fsm_handling.py
This deliberately does not rebuild game files or invoke the game/editor.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


class XfsReader:
    def __init__(self, data: bytes):
        self.data, self.pos, self.defs = data, 0, []

    def read(self, fmt):
        result = struct.unpack_from('<' + fmt, self.data, self.pos)
        self.pos += struct.calcsize('<' + fmt)
        return result[0] if len(result) == 1 else list(result)

    def string(self):
        end = self.data.index(0, self.pos)
        value = self.data[self.pos:end].decode('utf8')
        self.pos = end + 1
        return value

    def read_class(self):
        class_id, variable_id = self.read('HH')
        if class_id // 2 >= len(self.defs):
            return None
        size_start = self.pos
        size = self.read('Q')
        result = {'_class_id': class_id, '_variable_id': variable_id}
        for name, kind in self.defs[class_id // 2]:
            count = self.read('I')
            values = [self.read_value(kind) for _ in range(count)]
            result[name] = values[0] if count == 1 else values
        if self.pos != size_start + size:
            raise ValueError(('class_size', class_id, self.pos, size_start + size))
        return result

    def read_value(self, kind):
        if kind in (1, 2):
            return self.read_class()
        if kind == 14:
            return self.string()
        formats = {3:'B', 4:'B', 5:'H', 6:'I', 7:'Q', 8:'b', 9:'h', 10:'i',
                   11:'q', 12:'f', 13:'d', 15:'4B', 16:'Q', 20:'4f', 21:'4f', 22:'4f'}
        if kind not in formats:
            raise ValueError(('unsupported_kind', kind, self.pos))
        return self.read(formats[kind])

    def parse(self):
        if self.data[:4] != b'XFS\0':
            raise ValueError('not XFS')
        self.pos = 4
        version, kind, count_hint, definition_count, definition_size = self.read('HHQII')
        if version != 19:
            raise ValueError(('unsupported_version', version))
        origin = self.pos
        pointers = [self.read('Q') for _ in range(definition_count)]
        for pointer in pointers:
            self.pos = origin + pointer
            type_hash, member_count = self.read('QQ')
            members = []
            for _ in range(member_count):
                member_start = self.pos
                name_ptr, member_type = self.read('QB')
                self.pos = origin + name_ptr
                members.append((self.string(), member_type))
                self.pos = member_start + 80
            self.defs.append(members)
        self.pos = origin + definition_size
        return {'version': version, 'root': self.read_class()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    parsed = XfsReader(args.source.read_bytes()).parse()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding='utf8')
    print(args.output)
