"""Compare native recent-room rules with unchanged SMS 1C15..1C96, controlled draws."""
import ctypes as c,hashlib,json,os,random,subprocess
from pathlib import Path
from run_core import ROOT,run

def main():
 folder=ROOT/'validation/room-history';folder.mkdir(exist_ok=True)
 (folder/'types.h').write_text('#include <stdint.h>\ntypedef uint8_t u8;typedef uint16_t u16;\n')
 env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-shared','-Wall','-Wextra','-Werror','-I'+str(folder),'-I'+str(ROOT/'megadrive/src'),str(ROOT/'megadrive/src/source_room_history.c'),'-o',str(folder/'history.dll')],env=env,check=True)
 lib=c.CDLL(str(folder/'history.dll'));Draw=c.CFUNCTYPE(c.c_uint8,c.c_void_p);arr=c.POINTER(c.c_uint8)
 lib.source_room_history.argtypes=[c.c_uint16,arr,arr,Draw,c.c_void_p];lib.source_room_history.restype=c.c_uint8
 original=(ROOT/'input/original.sms').read_bytes();assert original[0x1c91:0x1c97]==bytes.fromhex('1e5e9cb8bec9')
 # Only boot and RNG input service replaced. 1C15..1C96 remain unmodified.
 rom=bytearray(original);rom[:3]=bytes.fromhex('c30030')
 boot=bytes.fromhex('f331e0df2100c01101c001ff1f3600edb0')
 # wait at3011; command C000 set by fixture; call real1C15, acknowledge.
 boot+=bytes.fromhex('3a00c0b728faaf3286c0cd151caf3200c018ec')
 rom[0x3000:0x3000+len(boot)]=boot
 thunk=bytes.fromhex('d53a86c06f26001180c0193c3286c07ed1c9')
 rom[0x4e1:0x4e1+len(thunk)]=thunk
 assert rom[0x1c15:0x1c97]==original[0x1c15:0x1c97]
 cartridge=folder/'controlled.sms';cartridge.write_bytes(rom)
 cases=[]
 for value in range(256):
  for dungeon in [0,1]:
   for protected in [0,1]:
    for mask in [0,1,255]:
     for already in [0,1]:
      history=bytearray([0x70]*16);room=0x95+(dungeon<<8)
      if protected:history[1]=value
      if already:history[0]=0x95
      masks=bytearray([0]*256);masks[value]=mask
      cases.append((room,bytes(history),bytes(masks),bytes([value]*5)))
 rng=random.Random(0x1c15)
 for i in range(512):
  cases.append((rng.randrange(0x300),rng.randbytes(16),bytes(rng.choice([0,0,1,0x80,255]) for _ in range(256)),rng.randbytes(5)))
 pending=[];results=[];draw_index=[0];draws=[b'']
 @Draw
 def draw(ctx):
  value=draws[0][draw_index[0]];draw_index[0]+=1;return value
 def prepare(index,frame):
  room,h,m,d=cases[index];pending[:]=[(frame,0xb9,room.to_bytes(2,'little')),(frame,0x1cf0,h),(frame,0x200,m),(frame,0x80,d),(frame,0,b'\1')]
 def observe(frame,ram):
  if frame<10:return
  index=frame-10
  if index>=len(cases):return
  room,h,m,d=cases[index];hist=(c.c_uint8*16).from_buffer_copy(h);masks=(c.c_uint8*256).from_buffer_copy(m);draws[0]=d;draw_index[0]=0
  count=lib.source_room_history(room,hist,masks,draw,None)
  assert ram[0]==0,('SMS routine not finished',index,ram[0])
  assert bytes(hist)==ram[0x1cf0:0x1d00],('history',index,room,bytes(hist).hex(),ram[0x1cf0:0x1d00].hex())
  assert bytes(masks)==ram[0x200:0x300],('masks',index,room)
  assert draw_index[0]==ram[0x86]==(5 if room>>8 else 3),('draw count',index)
  assert count==sum(a==0 and b==255 for a,b in zip(m,masks))
  results.append(count)
  if index+1<len(cases):prepare(index+1,frame+1)
 prepare(0,10)
 run(cartridge,len(cases)+9,folder/'sms',set(),[],ram_writes=pending,skip_intro=False,ram_observer=observe)
 assert len(results)==len(cases)
 case_digest=hashlib.sha256(b''.join(r.to_bytes(2,'little')+h+m+d for r,h,m,d in cases)).hexdigest()
 report=dict(passed=True,cases=len(cases),restored=sum(results),cases_sha256=case_digest,source_sha256=hashlib.sha256(original).hexdigest(),source_range='1C15..1C96 unchanged',controlled_draws=True,limits=['RNG inputs are controlled; source R/IRQ stream and natural campaign are not validated.'],module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_room_history.c').read_bytes()).hexdigest())
 (ROOT/'analysis/room_history_rules_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
