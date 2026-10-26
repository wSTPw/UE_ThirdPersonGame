"""Read-only selective MHW Iceborne extraction, based on MHWNoChunk (MIT).

Format/key reference: Source/MHWNoChunk-master/MHWNoChunk/Chunk.cs.
Upstream: https://github.com/JodoZT/MHWNoChunk
No game files or proprietary compression libraries are bundled by this script.
"""
import argparse
import ctypes
import functools
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct

HERE = Path(__file__).resolve().parent
BLOCK = 0x40000


class Archive:
    def __init__(self, path, oodle):
        self.path = path
        self.stream = path.open('rb')
        magic, count = struct.unpack('<II', self.stream.read(8))
        if magic != 0x504D43 or not 0 < count < 2_000_000:
            raise ValueError(f'Unexpected Iceborne chunk header: {path}')
        table = self.stream.read(count * 8)
        self.blocks = []
        for i in range(count):
            entry = table[i * 8:(i + 1) * 8]
            raw = int.from_bytes(bytes([entry[0] >> 4]) + entry[1:3], 'little')
            self.blocks.append((int.from_bytes(entry[3:8], 'little'), (raw >> 4) + (raw & 15)))
        reference = HERE / 'Source/MHWNoChunk-master/MHWNoChunk'
        source = (reference / 'Chunk.cs').read_text(encoding='utf-8-sig')
        self.keys = [bytes.fromhex(x) for x in re.findall(r'//\d+ ([0-9a-f]{32})', source)]
        keyfile = (reference / 'Resources/chunk.key').read_bytes()
        start, end = struct.unpack_from('<II', keyfile)
        self.key_start = start - 1
        self.pattern = keyfile[8:8 + end - start + 1]
        self.decompress = oodle.OodleLZ_Decompress
        self.decompress.restype = ctypes.c_ssize_t
        self.decompress.argtypes = [ctypes.c_void_p, ctypes.c_ssize_t, ctypes.c_void_p,
                                   ctypes.c_ssize_t] + [ctypes.c_ssize_t] * 10
        self.cached_block = functools.lru_cache(maxsize=32)(self.block)

    def close(self):
        self.cached_block.cache_clear()
        self.stream.close()

    def block(self, index):
        offset, size = self.blocks[index]
        self.stream.seek(offset)
        raw = self.stream.read(size or BLOCK)
        if size:
            target = ctypes.create_string_buffer(BLOCK)
            length = self.decompress(raw, len(raw), target, BLOCK, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3)
            if length != BLOCK:
                raise ValueError(f'Decompression failed: {self.path.name}, block {index}, result {length}')
            raw = target.raw
        if len(raw) != BLOCK:
            raise ValueError('Truncated subchunk')
        key_id = self.pattern[index - self.key_start]
        key = self.keys[key_id if key_id < 16 else 0] * (BLOCK // 16)
        return (int.from_bytes(raw, 'little') ^ int.from_bytes(key, 'little')).to_bytes(BLOCK, 'little')

    def read(self, offset, size):
        pieces = []
        while size:
            index, within = divmod(offset, BLOCK)
            amount = min(size, BLOCK - within)
            pieces.append(self.cached_block(index)[within:within + amount])
            offset += amount
            size -= amount
        return b''.join(pieces)

    def entries(self):
        header = self.read(0, 256)
        if header[:4] != b'PKG ':
            raise ValueError(f'Invalid decompressed PKG magic: {header[:16].hex()}')
        parent_count = struct.unpack_from('<I', header, 12)[0]
        position = 256
        for _ in range(parent_count):
            parent = self.read(position, 84)
            children = struct.unpack_from('<I', parent, 80)[0]
            position += 84
            for _ in range(children):
                entry = self.read(position, 184)
                size, offset, kind = struct.unpack_from('<QQI', entry, 160)
                position += 184
                if kind == 0:
                    name = entry[:160].replace(b'\0', b'').decode('ascii').replace('\\', '/').lstrip('/')
                    yield name, dict(archive=self.path.name, offset=offset, size=size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--oodle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pattern', help='Regex over original archive paths; omit to index only')
    parser.add_argument('--max-mb', type=int, default=2048)
    args = parser.parse_args()
    game = args.game.resolve()
    output = args.output.resolve()
    if output.is_relative_to(game) or game.is_relative_to(output):
        raise ValueError('Output must be separate from game installation')
    output.mkdir(parents=True, exist_ok=True)
    oodle = ctypes.CDLL(str(args.oodle.resolve()))
    catalog_path = output / 'archive-index.json'
    archives = sorted((game / 'chunk').glob('chunkG*.bin'),
                      key=lambda p: int(re.search(r'G(\d+)', p.name)[1]))
    stamps = {p.name: [p.stat().st_size, p.stat().st_mtime_ns] for p in archives}
    if catalog_path.exists():
        cached = json.loads(catalog_path.read_text(encoding='utf-8'))
        if cached['archives'] != stamps or cached['source'] != str(game):
            raise ValueError('Archive index does not match source; use a fresh output folder')
        catalog = {k.lstrip('/'): v for k, v in cached['files'].items()}
    else:
        catalog = {}
        for path in archives:
            archive = Archive(path, oodle)
            try:
                catalog.update(archive.entries())
                print(f'Indexed {path.name}: {len(catalog)} merged files', flush=True)
            finally:
                archive.close()
        catalog_path.write_text(json.dumps(dict(source=str(game), archives=stamps, files=catalog)), encoding='utf-8')
    if not args.pattern:
        candidates = [dict(path=k, **v) for k, v in catalog.items()
                      if (k.endswith('.lmt') and k.startswith('pl/')) or
                      (k.endswith('.mod3') and k.startswith('pl/') and '000' in k)]
        (output / 'player-candidates.json').write_text(json.dumps(candidates, indent=2), encoding='utf-8')
        print(f'{len(catalog)} files indexed; {len(candidates)} player candidates')
        return
    selected = {k: v for k, v in catalog.items() if re.search(args.pattern, k, re.I)}
    if not selected:
        raise ValueError('No archive entries match the requested pattern')
    total = sum(v['size'] for v in selected.values())
    if total > args.max_mb * 1024 ** 2:
        raise ValueError(f'Selection exceeds {args.max_mb} MB budget ({total} bytes)')
    opened = {}
    records = []
    try:
        for name, info in sorted(selected.items()):
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or ':' in name:
                raise ValueError(f'Unsafe archive path: {name}')
            target = output / 'nativePC' / relative
            if not target.resolve().is_relative_to(output / 'nativePC'):
                raise ValueError(f'Output path escapes nativePC: {name}')
            if info['archive'] not in opened:
                opened[info['archive']] = Archive(game / 'chunk' / info['archive'], oodle)
            data = opened[info['archive']].read(info['offset'], info['size'])
            digest = hashlib.sha256(data).hexdigest()
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise FileExistsError(f'Refusing to replace different file: {target}')
            target.write_bytes(data)
            records.append(dict(path=name, sha256=digest, **info))
            print(f'Extracted {name}: {len(data)} bytes', flush=True)
    finally:
        for archive in opened.values():
            archive.close()
    (output / 'extraction-manifest.json').write_text(json.dumps(dict(source=str(game),
        pattern=args.pattern, total_bytes=total, files=records), indent=2), encoding='utf-8')
    print(f'Extracted {len(records)} files, {total / 1024 ** 2:.2f} MiB')


if __name__ == '__main__':
    main()
