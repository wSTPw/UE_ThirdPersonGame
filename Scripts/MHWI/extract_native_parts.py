"""Read pinned melee records and em001 part/hitzone rows. Offline only."""
import hashlib
import json
from pathlib import Path
import struct

from extract_native_longsword_params import decrypt_resource, pinned_sources

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'Saved/MHWIRestoration/B13-20261026'
LAYOUT = ROOT/'Tools/MHW/native-parts-layout.json'
FORMATS = {'UInt32':'I','Int32':'i','UInt16':'H','Int16':'h',
           'Single':'f','Byte':'B','SByte':'b'}


class Reader:
    def __init__(self, data, layout):
        self.data, self.layout, self.pos = data, layout, 0
        self.spans = []

    def row(self, section):
        begin = self.pos
        row = {}
        for field in self.layout[section]:
            fmt = '<'+FORMATS[field['type']]
            size = struct.calcsize(fmt)
            if self.pos+size > len(self.data):
                raise ValueError('Truncated '+section)
            row[field['name']] = struct.unpack_from(fmt,self.data,self.pos)[0]
            self.pos += size
        self.spans.append(dict(section=section,offset=begin,size=self.pos-begin))
        return row

    def rows(self, section, count):
        if not 0 <= count <= len(self.data):
            raise ValueError('Invalid row count')
        return [self.row(section) for _ in range(count)]

    def finish(self, expected_zero_tail=0):
        tail = self.data[self.pos:]
        if len(tail) != expected_zero_tail or any(tail):
            raise ValueError('Unconsumed non-padding bytes')
        return dict(bytes=len(self.data), consumed=self.pos, unmapped_zero_tail=len(tail),spans=self.spans)


def run():
    pinned_sources()
    layout=json.loads(LAYOUT.read_text(encoding='utf-8'))
    wp=OUT/'resources/nativePC/common/equip/l_sword.wp_dat'
    raw=wp.read_bytes()
    r=Reader(raw,layout['sources']['Weapons/Melee.cs']['classes'])
    header=r.row('Header')
    if header['Magic_1']!=0x18091001:
        raise ValueError('Unsupported melee table')
    melee=dict(header=header,entries=r.rows('Entries',header['Entry_Count']))
    melee.update(r.finish())
    path=OUT/'resources-parts/nativePC/em/em001/00/data/em001.dtt_epg'
    data=decrypt_resource(path,'DTT_EPG_KEY')
    r=Reader(data,layout['sources']['Monsters/MonsterParts.cs']['classes'])
    header=r.row('Monster_Parts')
    if header['Magic_1']!=0x18091001 or header['Magic_2']!=35:
        raise ValueError('Unsupported part table version')
    flinches=[]
    for _ in range(header['Flinches_Count']):
        row=r.row('Flinches')
        typ=row['Parts_Type']
        if typ not in (1,2,3):
            raise ValueError('Unknown part mapping variant')
        row['parts']=r.row('Parts'+str(typ))
        flinches.append(row)
    hit_header=r.row('Hitzone_Header')
    hitzones=r.rows('Hitzones',hit_header['Hitzone_Count'])
    sever_header=r.row('Sever_Header')
    severs=r.rows('Severs',sever_header['Sever_Count'])
    unknown_header=r.row('Unk_Header')
    unknown=r.rows('Unknowns',unknown_header['Unk_Count'])
    tail=r.row('Unknown')
    parts=dict(header=header,flinches=flinches,hitzones=hitzones,severs=severs,
               unknown=unknown,unknown_tail=tail,**r.finish(expected_zero_tail=9))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(schema=1,layout_sha256=sha(LAYOUT),
                sources=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in [wp,path]],
                melee=melee,parts=parts,
                boundary='Resource rows only; no damage formula or geometry consumer is inferred from labels.')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'native-parts.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (OUT/'em001.dtt_epg.decrypted.bin').write_bytes(data)
    print(json.dumps(dict(melee_entries=len(melee['entries']),flinches=len(flinches),
                          hitzones=len(hitzones),severs=len(severs),
                          consumed=parts['consumed'],unmapped_zero_tail=parts['unmapped_zero_tail'])))
    return report


if __name__=='__main__':
    run()
