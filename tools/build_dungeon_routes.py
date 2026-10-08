#!/usr/bin/env python3
from pathlib import Path
import re,json,collections,hashlib
import argparse
from embed_rom import REFERENCE_SHA256
parser=argparse.ArgumentParser(description='Derive dungeon routes from the original map masks and checked native callback tables')
parser.add_argument('--rom',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent;rom=args.rom.read_bytes()
if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=REFERENCE_SHA256:
 raise ValueError('Dungeon routes require the verified original ROM revision')
cb=[int(n,16) for n in re.findall(r'0x([0-9A-Fa-f]+)',(root/'src/world_callbacks_512.inc').read_text())]
core=(root/'src/core.c').read_text();links={}
for t,pos,dest in re.findall(r'\{0x([0-9A-F]+)u,0x([0-9A-F]+)u,0x([0-9A-F]+)u,[01],[01]\}',core):links[int(t,16)]=(int(pos,16),0x100|int(dest,16))
for t,pos,dest in re.findall(r'case 0x([0-9A-F]+)u:[^\n]*?world_trigger_linked_room\(0x([0-9A-F]+)u,0x([0-9A-F]+)u\)',core):links[int(t,16)]=(int(pos,16),0x100|int(dest,16))
entries={}
for line in (root/'src/world_key_room_callbacks.inc').read_text().splitlines():
 t,pos,k=[int(n,16) for n in re.findall(r'0x([0-9A-Fa-f]+)',line)];entries[k]=(cb.index(t),pos)
entries[5]=(cb.index(0xAF4A),0x314);entries[6]=(cb.index(0xB0D9),0x31c)
starts=[0x11c,0x1e4,0x171,0x1f8,0x1f0,0x186,0x187,0x1db,0x1ea,0x1fc,0x18d]
arenas=json.loads((root/'tests/scenarios/boss_arenas.json').read_text())
def xy(pos):
 for y in range(16,161,8):
  for x in range(16,241,8):
   if ((((y-12)&248)<<3)+(((x-12)>>2)&62)+126)&65535==pos:return [x,y]
 raise ValueError(pos)
def tiles(c):
 b=rom[(8+c//128)*16384:(9+c//128)*16384];p=int.from_bytes(b[(c%128)*2:(c%128)*2+2],'little')-0x8000;v=[]
 while b[p]:
  n=b[p];p+=1
  if n&128:v.extend(b[p:p+(n&127)]);p+=n&127
  else:v.extend([b[p]]*n);p+=1
 return v
actions={}
for name in ('world_progress_gate_callbacks','world_finalize_callbacks','world_finalize_gate_callbacks'):
 block=core.split(name+'[]={',1)[1].split('};',1)[0]
 for t,pos in re.findall(r'\{0x([0-9A-F]+)u,0x([0-9A-F]+)u',block):actions[int(t,16)]=int(pos,16)
for t,pos in re.findall(r'case 0x([0-9A-F]+)u:[^\n]*?world_try_(?:finalize(?:_gate|_explicit)?|progress_bits)_at\(0x([0-9A-F]+)u',core):actions[int(t,16)]=int(pos,16)
for t in (0xB586,0xB698,0xB65F):actions[t]=0x168
out=[]
for k in range(1,11):
 p=4*16384+0x3c8c+k*9;base=rom[p];cells=[0x100|((base+y*16)&240)|((base+x)&15) for y in range(8) for x in range(8) if rom[p+1+y]&rom[0x45+x]]
 graph={}
 for c in cells:
  v=tiles(c);edges=[]
  for dest,i,dir,target in ((c-16,7,'up',[128,8]),(c+16,151,'down',[128,168]),((c&0x1f0)|((c-1)&15),64,'left',[8,80]),((c&0x1f0)|((c+1)&15),79,'right',[248,80])):
   if (k,c,dest) not in ((3,0x1E2,0x1E3),(4,0x1F0,0x1E0),(6,0x167,0x168),(5,0x174,0x173)) and dest in cells and v[i]=={'up':0x29,'down':0x80,'left':0x13,'right':0x1D}[dir] and tiles(dest)[{'up':151,'down':7,'left':79,'right':64}[dir]]=={'up':0x80,'down':0x29,'left':0x1D,'right':0x13}[dir]:edges.append({'from':c,'to':dest,'direction':dir,'target':target})
  if cb[c] in links:
   pos,dest=links[cb[c]]
   if dest in cells:edges.append({'from':c,'to':dest,'target':xy(pos),'stairs':True})
  graph[c]=edges
 boss=next(a for a in arenas if a['index']==k)
 def path(a,b,avoid=()):
  q=collections.deque([(a,[])]);seen={a}
  while q:
   c,route=q.popleft()
   if c==b:return route
   for e in graph[c]:
    if e['to'] not in seen and e['to'] not in avoid:seen.add(e['to']);q.append((e['to'],route+[e]))
  raise ValueError((k,hex(a),hex(b)))
 route=path(starts[k],boss['cell'])
 if k==3:
  split=next(i for i,e in enumerate(route) if e['from']==0x1E3)
  route=route[:split]+path(0x1E3,0x1F3)+[{'from':0x1F3,'to':0x1F2,'direction':'left','target':[8,80]},{'from':0x1F2,'to':0x1E2,'direction':'up','target':[128,8]}]+[{'from':0x1E2,'to':0x1E3,'direction':'right','target':[248,80]}] + route[split:]
 if k==5:
  split=next(i for i,e in enumerate(route) if e['from']==0x154)
  detour=[{'from':a,'to':b,'direction':d,'target':{'right':[248,80],'left':[8,80],'down':[128,168],'up':[128,8]}[d]} for a,b,d in [(0x154,0x155,'right'),(0x155,0x165,'down'),(0x165,0x164,'left'),(0x164,0x154,'up')]]
  route=route[:split]+detour+route[split:]
 if k==6:
  split=next(i for i,e in enumerate(route) if e['from']==0x138)
  route=route[:split]+path(0x138,0x139)+path(0x139,0x138)+route[split:]
  split=next(i for i,e in enumerate(route) if e['from']==0x118)
  route=route[:split]+path(0x118,0x127,avoid=(0x117,))+path(0x127,0x117)+path(0x117,0x127)+path(0x127,0x118,avoid=(0x117,))+path(0x118,0x117)+route[split+1:]
 if k==10:
  split=next(i for i,e in enumerate(route) if e['from']==0x16D)
  route=route[:split]+path(0x16D,0x18D)+path(0x18D,0x15D,avoid=(0x17D,0x16D))+[{'from':0x15D,'to':0x16D,'direction':'down','target':[128,168]}]+route[split:]
  # 16C has two disconnected floor regions. Enter the western region from
  # 16B after the stair circuit, rather than trying to cross its solid wall.
  split=next(i for i,e in enumerate(route) if e['from']==0x16C)
  route=route[:split]+path(0x16C,0x14D)+path(0x14D,0x16B,avoid=(0x16C,))+path(0x16B,0x16C)+route[split:]
 if k==9:
  route=path(starts[k],boss['cell'],avoid=(0x1ED,0x1DD))
  # $B686 closes the western gate while fighting, then opens the upper
  # gate. Reach BC through AE/9E and its stairs instead of the sealed exit.
  split=next(i for i,e in enumerate(route) if e['from']==0x1BE)
  route=route[:split]+path(0x1BE,boss['cell'],avoid=(0x1BD,))
  # BC's switch opens the east gate; BD's $B679 sets BC's north bit.
  split=next(i for i,e in enumerate(route) if e['from']==0x1BC)
  route=route[:split]+path(0x1BC,0x1BD)+path(0x1BD,0x1BC)+route[split:]
 if k==8:
  # Reach the remote switches through the stairs before returning to 1C8.
  split=next(i for i,e in enumerate(route) if e['from']==0x1C8)
  route=route[:split]+path(0x1C8,0x1EB)+path(0x1EB,0x1EC)+path(0x1EC,starts[k])+path(starts[k],0x1C8)+route[split:]
  # $B5BA in 19A sets bit 2 in D8, opening its western gate. The shortest
  # geometric route skipped this dependency and stopped at the closed gate.
  split=next(i for i,e in enumerate(route) if e['from']==0x1D8)
  route=route[:split]+path(0x1D8,0x19A,avoid=(0x1D7,))+path(0x19A,0x1D8)+route[split:]
 back=path(boss['cell'],starts[k]);cell,pos=entries[k]
 if k==5:
  # Return via the stairs: the eastern room locks its western doorway.
  back=path(0x163,0x173)+path(0x173,0x162,avoid=(0x174,))+path(0x162,0x153)+path(0x153,0x154)+path(0x154,0x164)+path(0x164,starts[k],avoid=(0x174,0x154))
 o={'index':k,'outside_cell':cell,'entry_target':xy(pos),'entrance':starts[k],'boss':boss,'rooms':cells,'outbound':route,'return':back,'actions':{str(c):xy(actions[cb[c]]) for c in cells if cb[c] in actions},'avoid':{str(c):[xy(links[cb[c]][0])] for c in cells if cb[c] in links}}
 o['puzzles']={str(c):{'target':[(tile%16)*16+8,(tile//16)*16+24],'tile':tile} for c in cells for t,tile in [(0xB42D,0x7B),(0xB459,0x43),(0xB574,0x4A)] if cb[c]==t}
 out.append(o);print(k,hex(cell),xy(pos),'->',' '.join(f"{e['from']:03X}>{e['to']:03X}{'s' if e.get('stairs') else ''}" for e in route),'back',len(back))
(root/'tests/scenarios/dungeon_routes.json').write_text(json.dumps(out,indent=2)+'\n')
