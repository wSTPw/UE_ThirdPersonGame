import importlib.util,json
from pathlib import Path
p=Path('Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main/lmt/lmt_parser.py')
s=importlib.util.spec_from_file_location('weapon_lmt',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out={}
for name in ['wg03_00','wg03_00_fs','wg03_01']:
 p=Path('ArtSource/ThirdParty/MHWLongSword/nativePC/wp/swo/mot')/name/(name+'.lmt')
 records=m.LmtParser(str(p)).read()
 out[name]=records
 print(name,len(records),str(records[:2])[:2200])
Path('Saved/MHWIImport/weapon-motion-source.json').write_text(json.dumps(out,default=lambda o:o.tolist() if hasattr(o,'tolist') else str(o)),encoding='utf8')
