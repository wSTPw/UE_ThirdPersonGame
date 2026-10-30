"""B20 pinned native locomotion consumers. Never executes native game code."""
import hashlib,json,struct
from pathlib import Path
from trace_outstanding_evidence import Evidence
from extract_native_longsword_params import decrypt_resource
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Tools/MHW/native-locomotion-evidence.json'

def build():
 e=Evidence();actions=e.actions(); selected=[actions[i] for i in (0,1,2,3,4,65,66)]
 path=ROOT/'ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/hm/wp/wp03/wp03_param.w03p'
 data=decrypt_resource(path)
 # Base loader: twenty 17-byte rows, two floats, six-float substructure,
 # then five floats through runtime+348. The gate is the fifth of those.
 offset=8+20*17+2*4+6*4+4*4
 assert offset==0x18c and struct.unpack_from('<f',data,offset)[0]==70.0
 f=e.function(0x141387920);r=e.function(0x1413a39a0)
 assert any(i['va']=='0x1413879e3' and i['operands']=='dword ptr [rdi + 0x348], xmm0' for i in f['instructions'])
 assert sum(i['mnemonic']=='call' and i['operands']=='qword ptr [rax + 0x48]' for i in r['instructions'])==6
 names={x['action']:x['name'] for x in selected}
 assert names[65]=='WP_03::DODGE_TO_MOVE' and names[66]=='WP_03::DODGE_TO_TURN'
 assert any(i['operands']=='edx, 0xc00e' for i in actions[65]['entry']['instructions'])
 assert any(i['operands']=='dword ptr [rbx + 0x30], 0xc00f' for i in actions[66]['constructor']['instructions'])
 functions={}
 for x in selected:
  for k in ('constructor','entry','update'):
   fn=x[k];functions[fn['entry']]=fn
 for va in (0x141387920,0x1413a39a0,0x142176240,0x142176590):
  fn=e.function(va);functions[fn['entry']]=fn
 return dict(schema=1,exe=e.tr.pin['exe'],analysis_text=e.tr.pin['text'],
  action_bindings=[dict(action=x['action'],name=x['name'],constructor=x['constructor']['entry'],entry=x['entry']['entry'],update=x['update']['entry']) for x in selected],
  motion_bindings={'5':'WALK entry, small direction angle','6':'WALK entry, one horizontal cross sign','7':'WALK entry, opposite horizontal cross sign','8':'WALK_END','14':'DODGE_TO_MOVE','15':'DODGE_TO_TURN'},
  angle_gate=dict(source=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),file_offset=hex(offset),runtime_offset='0x348',degrees=70.0),
  functions=list(functions.values()),boundary='Pinned byte/consumer evidence only. UE trigger sequencing, physics and IK are separately documented project adapters; 014/015 are not landing animations.')

def main(write=False):
 result=build()
 if write:OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 elif result!=json.loads(OUT.read_text(encoding='utf-8')):raise ValueError('Locomotion source evidence changed')
 print(json.dumps(dict(passed=True,functions=len(result['functions']),bindings=len(result['motion_bindings']))))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');main(p.parse_args().write)
