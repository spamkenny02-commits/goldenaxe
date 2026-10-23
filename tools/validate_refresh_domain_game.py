"""Exercise the actual playable ROM with controlled SGDK seeds and real actor dispatch."""
import ctypes as c,hashlib,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols

def step(v):
 v^=v>>5;v^=(v<<9)&65535;v^=v>>7;return v&65535

def find(predicate,count):
 for seed in range(1,65536):
  values=[];v=seed
  for _ in range(count):v=step(v);values.append(v)
  if predicate([x&255 for x in values]):return seed,values
 raise AssertionError('No seed')

def main():
 sy=symbols(ROOT/'megadrive/out/release/symbol.txt');folder=ROOT/'validation/refresh-domain';lib=c.CDLL(str(folder/'probe.dll'));lib.probe.argtypes=[c.c_uint16]*7+[c.POINTER(c.c_uint8)];lib.probe.restype=c.c_uint16;rom=(ROOT/'input/original.sms').read_bytes();cases=[]
 for value in [0,31,32,127,128,143,159,255]:cases.append(dict(name=f'47-turn-{value}',kind=0x47,state=4,seed=find(lambda v:v[0]==value,1)[0]))
 cases += [dict(name='49-two-reads',kind=0x49,state=4,seed=find(lambda v:not(v[0]&1) and 128<=v[1]<160,2)[0]),dict(name='49-aimed',kind=0x49,state=4,seed=find(lambda v:v[0]>=128 and v[0]&1,1)[0]),dict(name='65-two-reads',kind=0x65,state=4,seed=find(lambda v:not(v[0]&1) and 128<=v[1]<160,2)[0]),dict(name='65-full-gate',kind=0x65,state=6,seed=find(lambda v:v[0]==128 and not(v[1]&1),3)[0]),dict(name='65-pause',kind=0x65,state=6,seed=find(lambda v:v[0]<8 and v[1]>=128,2)[0])]
 results=[];before=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 for region in ['auto','pal']:
  for case in cases:
   kind=case['kind'];v=case['seed'];draws=[]
   def draw():
    nonlocal v
    v=step(v);draws.append(v);return v&255
   gate=draw() if case['state']==6 else None;moving=gate is None or gate>=8
   if moving:
    select=draw() if kind>=0x49 else 0;turn=0 if select&1 else draw();expected=(c.c_uint8*48)();lib.probe(kind,3,128,88,select,turn,0,expected);direction=expected[0x20];table=rom[0xa949:0xa972] if kind==0x65 else rom[0x4f1b:0x4f44];movement=table[1+direction*5:1+direction*5+4]
   else:pause=draw();direction=3;movement=bytes(4)
   entities=bytearray(768);entities[0]=kind;entities[1]=case['state'];entities[3]=1;entities[8:10]=(0x9a02 if kind==0x65 else 0x9227).to_bytes(2,'little');entities[10]=1;entities[12]=2;entities[13]=4;entities[0x11]=88;entities[0x13]=128;entities[0x18]=16;entities[0x20]=3;entities[0x28]=16;entities[0x2b]=8
   seen={};writes=[(3000,sy['world_actor_state'],bytes(entities)),(3000,sy['world_loot_state'],bytes(336)),(3000,sy['world_spell_state'],bytes(48)),(3000,sy['randbase'],case['seed'].to_bytes(2,'big')),(3000,sy['hero_x'],(200<<8).to_bytes(2,'big')),(3000,sy['hero_y'],(100<<8).to_bytes(2,'big')),(3000,sy['hero_counter'],bytes(2)),(3000,sy['hero_state'],b'\0\1'),(3000,sy['game_state'],b'\0\x0c')]
   def observe(frame,ram):
    if frame<3000:return
    d=lambda name,n:bytes(ram[(sy[name]+i)^1] for i in range(n));e=d('world_actor_state',48);seed=int.from_bytes(d('randbase',2),'big')
    if seed==case['seed']:return
    assert seed==v,('draw sequence',region,case['name'],frame,seed,v,draws)
    assert e[0x20]==direction and e[0x14:0x18]==movement,('direction/vector',region,case['name'],frame,e.hex(),direction,movement.hex())
    assert e[1]==(6 if moving else 8),('branch',region,case['name'],frame,e[1])
    if not moving:assert e[0x2f]==(pause&63)+63
    seen.update(frame=frame,direction=e[0x20],state=e[1],pause=e[0x2f],seed=seed)
   run(ROOT/'gaw-megadrive.bin',3005,folder/f"game-{region}-{case['name']}",set(),PRESSES[:8],ram_writes=writes,ram_observer=observe,stop_when=lambda:bool(seen),core_options={'genesis_plus_gx_region_detect':region})
   assert seen,(region,case);results.append(dict(region=region,input=case,raw_draws=draws,**seen))
 report=dict(passed=True,md_sha256=before,source_sha256=hashlib.sha256(rom).hexdigest(),actors_sha256=hashlib.sha256((ROOT/'megadrive/src/actors.c').read_bytes()).hexdigest(),cases=results,rules=json.loads((ROOT/'analysis/refresh_domain_rules_report.json').read_bytes()),limits=['Controlled seed/entity fixtures execute the actual production dispatch on NTSC/PAL. Native directions, vectors, branch and exact number/order of SGDK draws are checked.','Gate 04E1 stays eight-bit; direct-R direction inputs are projected to seven bits. SGDK sequence is still provisional.','No complete campaign, exact source global clock/RNG, source-aligned raster/audio or hardware proof.'])
 assert before==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();(ROOT/'analysis/refresh_domain_v0275_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Playable ROM refresh-domain cases passed:',len(results))
if __name__=='__main__':main()
