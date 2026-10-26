"""Read source actions' actual track encodings and transform keys; Blender supplies numpy."""
import importlib.util,json,collections
from pathlib import Path
root=Path(__file__).resolve().parents[2]
path=root/'Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main/lmt/lmt_parser.py'
s=importlib.util.spec_from_file_location('source_lmt',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
report={}
for relative,indices in [('hm/common/mot/co00_00/co00_00.lmt',[1,10,34,35,37]),('hm/wp/wp03/mot/w03_00/w03_00.lmt',[101,102,104,105,106,107,108])]:
 records=m.LmtParser(str(root/'ArtSource/ThirdParty/MHWLongSword/nativePC'/relative)).read()
 for a in records:
  if int(a['name'].rsplit('_',1)[1]) not in indices:continue
  sample={}
  for b in [-1,0,1,5,6,7,8,9,10,11,12,13,14,17,18]:
   item=a['bone_action'].get(b,{})
   sample[str(b)]={k:({str(t):v for t,v in list(values.items())[:2]} if isinstance(values,dict) else values) for k,values in item.items()}
  report[a['name']]=sample
(root/'Saved/MHWIImport/source-track-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('SOURCE_TRACK_AUDIT',len(report))
