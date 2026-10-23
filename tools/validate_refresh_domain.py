"""Production refresh-domain inputs vs original 4EB7/4E0A chooser and bounds."""
import ctypes as c,hashlib,json,os,subprocess
from pathlib import Path
from run_core import ROOT,run

def body(text,name):
 start=text.rfind('\n',0,text.index(name+'('))+1
 end=text.index('{',text.index(name+'('));depth=1;i=end+1
 while depth:
  if text[i]=='{':depth+=1
  elif text[i]=='}':depth-=1
  i+=1
 return text[start:i]

def main():
 folder=ROOT/'validation/refresh-domain';folder.mkdir(exist_ok=True);original=(ROOT/'input/original.sms').read_bytes();assert b'\xed\x4f' not in original
 source=(ROOT/'megadrive/src/actors.c').read_text();functions='\n'.join(body(source,n) for n in ['second_boss_direction','dungeon_phase_refresh','dungeon_phase_move'])
 pre='#include <stdint.h>\n#include <string.h>\ntypedef uint8_t u8;typedef uint16_t u16;\nstatic u16 samples[2],count;\nstatic u16 test_random(void){return samples[count++];}\n#define random test_random\n'
 for name,offset,size in [('second_boss_turns',0x4efb,32),('second_boss_fast',0x4f1b,41)]:pre+='static const u8 '+name+'[]={'+','.join(str(v) for v in original[offset:offset+size])+'};\n'
 wrapper='''
u16 probe(u16 kind,u16 previous,u16 x,u16 y,u16 select,u16 turn,u16 explicit_input,u8 *out)
{u8 e[48]={0},roll[4]={0,0,select,turn};e[0]=kind;e[0x20]=previous;e[0x13]=x;e[0x11]=y;
 count=0;samples[0]=kind>=0x49?select:turn;samples[1]=turn;
 dungeon_phase_move(e,200,100,explicit_input?roll:0);memcpy(out,e,48);return count;}
'''
 (folder/'probe.c').write_text(pre+functions+wrapper);env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-shared','-Wall','-Wextra','-Werror',str(folder/'probe.c'),'-o',str(folder/'probe.dll')],env=env,check=True)
 lib=c.CDLL(str(folder/'probe.dll'));lib.probe.argtypes=[c.c_uint16]*7+[c.POINTER(c.c_uint8)];lib.probe.restype=c.c_uint16
 # Boot command loop; only the two R input instructions are replaced.
 rom=bytearray(original);rom[:3]=bytes.fromhex('c30030');boot=bytes.fromhex('f331e0df2100c01101c001ff1f3600edb0')
 # 3011 wait; choose D, store it, apply original bounds then acknowledge.
 boot+=bytes.fromhex('3a00c0b728fadd2100c6cdb74edd7220cd0a4eaf3200c0c31130')
 rom[0x3000:0x3000+len(boot)]=boot;rom[0x30:0x33]=bytes.fromhex('c3003a')
 handler=bytes.fromhex('e5d5210400395e23561a13722b732180c0856f7ed1e1c9');rom[0x3a00:0x3a00+len(handler)]=handler
 for address,index in [(0x4ed5,0),(0x4ebe,1)]:assert rom[address:address+2]==b'\xed\x5f';rom[address:address+2]=bytes([0xf7,index])
 cartridge=folder/'chooser.sms';cartridge.write_bytes(rom);cases=[]
 for kind in [0x47,0x49,0x65]:
  for previous in range(8):
   for x,y in [(128,88),(32,32),(224,144)]:
    for select in [0,1]:
     for turn in range(256):cases.append((kind,previous,x,y,select,turn))
 pending=[];checked=[0];changed=[0];outputs=[]
 def prepare(i,f):
  kind,previous,x,y,select,turn=cases[i];e=bytearray(48);e[0]=kind;e[0x20]=previous;e[0x13]=x;e[0x11]=y
  pending[:]=[(f,0x600,bytes(e)),(f,0x80,bytes([select&127,turn&127])),(f,0x313,bytes([200])),(f,0x311,bytes([100])),(f,0,b'\1')]
 def observe(f,ram):
  if f<10:return
  i=f-10
  if i>=len(cases):return
  kind,previous,x,y,select,turn=cases[i];out=(c.c_uint8*48)();count=lib.probe(kind,previous,x,y,select,turn,0,out)
  assert not ram[0] and out[0x20]==ram[0x620],('source direction',i,cases[i],out[0x20],ram[0x620])
  assert count==(2 if kind>=0x49 and not(select&1) else 1),('draw order',i,count)
  expected=original[0x4f1c+out[0x20]*5:0x4f21+out[0x20]*5];assert bytes(out[0x14:0x18])==expected[:4] and out[10]==expected[4]
  old=(c.c_uint8*48)();assert lib.probe(kind,previous,x,y,select,turn,1,old)==0
  changed[0]+=out[0x20]!=old[0x20];outputs.append(out[0x20]);checked[0]+=1
  if i+1<len(cases):prepare(i+1,f+1)
 prepare(0,10);run(cartridge,len(cases)+9,folder/'sms',set(),[],skip_intro=False,ram_writes=pending,ram_observer=observe)
 assert checked[0]==len(cases) and changed[0]>0
 report=dict(passed=True,cases=checked[0],changed_directions_vs_unprojected_inputs=changed[0],source_sha256=hashlib.sha256(original).hexdigest(),rom_ld_r_a_occurrences=0,raw_sites={'4EBE':original[0x4ebe:0x4ec4].hex(),'4ED5':original[0x4ed5:0x4eda].hex()},outputs_sha256=hashlib.sha256(bytes(outputs)).hexdigest(),scope='Actual C production move body vs original chooser/bounds with controlled source R inputs. Explicit fixture bytes remain unmodified.',limits=['Cold-reset R7=0 reference; no BIOS-precondition claim.','Projection corrects allowed input range only. SGDK draws remain provisional; source clock/IRQ random sequence is not integrated.'])
 (ROOT/'analysis/refresh_domain_rules_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
