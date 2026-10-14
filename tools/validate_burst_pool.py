"""Real36/37 source emissions with0..8 free transient records."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_actor_ai import random_word
from validate_house_dialogue import native

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for t in [0x36,0x37]:
  for free in range(9):
   data=bytearray(768);data[0]=t;data[1]=10;data[2]=6;data[3]=0x28;data[8:10]=bytes.fromhex('b789');data[12]=2;data[13]=10;data[0x11]=80;data[0x13]=120;data[0x18]=30
   for s in range(8+free,16):
    n=s*48;data[n]=0x10;data[n+1]=2;data[n+3]=0x28;data[n+4]=100;data[n+0x11]=144;data[n+0x13]=240
   source={};a=ROOT/f'validation/sms-burst-pool-{t}-{free}';b=ROOT/f'validation/md-burst-pool-{t}-{free}'
   def observe(f,raw):
    if f>=3102:source[f]=raw
   sw=[w for f in range(3102,3166) for w in [(f,0x600,bytes(data)),(f,0x1600,bytes(1536)),(f,0x1b,b'\0')]]
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,set(),[(200,220,0)]+PRESSES,ram_writes=sw,ram_observer=observe)
   f=next((f for f,raw in source.items() if raw[0x780]==(0x19 if t==0x36 else 0x1e)),None) if free else 3102
   assert f is not None,(t,free,'no source emission')
   src=source[f];e=src[0x600:0x630];mask=15 if t==0x36 else 7
   seed=next(n for n in range(1,65536) if random_word(n)&mask==0 and (6 if (random_word(random_word(n))&15)<2 or (random_word(random_word(n))&15)>=8 else 8)==e[1])
   actors=src[0x600:0x900]
   for phase in [0,1]:
    tw=[(f,sy['world_actor_state'],bytes(data)),(f,sy['sms_vram']+0x3800,bytes(1536)),(f,sy['randbase'],seed.to_bytes(2,'big')),(f,sy['world_clock_shift'],phase.to_bytes(4,'big'))]
    with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',f,b,{f},PRESSES,ram_writes=tw)
    dst=native(b,f)[sy['world_actor_state']:sy['world_actor_state']+768]
    if not free or t==0x37 or actors[404:408]==dst[404:408]:break
   for s in range(16):
    x=actors[s*48:(s+1)*48];y=dst[s*48:(s+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(t,free,f,s,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q])
   count=min(free,4 if t==0x36 else 1)
   assert sum(actors[n*48]==(0x19 if t==0x36 else 0x1e) for n in range(8,16))==count
   if t==0x36:assert [actors[(8+n)*48+10] for n in range(count)]==[3,2,1,0][:count]
   cases.append(dict(type=t,free_slots=free,source_frame=f,emitted=count,source_records=actors.hex(),native_random_and_clock_controlled=True,source_overflow_bit_cleared=True))
   print(f'{t:02X}: {free} free slots, {count} emitted OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,collision_descriptor_bytes_excluded=[27,28],overflow_suppression_verified=False,natural_gameplay_verified=False)
 (ROOT/'validation/burst_pool_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
