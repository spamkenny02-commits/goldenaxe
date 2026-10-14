"""Original500E/501A teleport emitters56/59/5A and17/71 projectile state and allocation comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# type,state,timer,anim,phase,period,split20,clock21,dirA,x,y,hx,hy,roomlo,slot,
# terrain,r0..r4,hp,damage,frame,freeLo,freeHi,counter2C,flash,4 reserved

def row(typ=0x4f,s=8,t=0,a=0,p=0,period=10,split=0,clock=0,d=1,x=128,y=80,hx=224,hy=144,room=0x13,slot=0,terrain=0,r0=1,r1=1,r2=0,r3=15,r4=15,hp=8,damage=0,frame=0,free=0,branch=16,flash=0):
 return (typ,s,t,a,p,period,split,clock,d,x,y,hx,hy,room,slot,terrain,r0,r1,r2,r3,r4,hp,damage,frame,free&255,(free>>8)&255,branch,flash,0,0,0,0)
ROWS=[row(typ=typ,s=state,t=t,flash=flash,d=d) for typ,state,t,flash,d in itertools.product([0x56,0x59,0x5a],range(0,10,2),[0,1,32],[0,1,32],range(4))]
ROWS += [row(typ=typ,s=0,r0=c,terrain=terrain) for typ,c,terrain in itertools.product([0x56,0x59,0x5a],range(128),[0,3,128])]
ROWS += [row(typ=typ,s=0,frame=f,slot=slot) for typ,f,slot in itertools.product([0x56,0x59,0x5a],range(8),range(8))]
ROWS += [row(typ=typ,s=0,r0=0x37,hx=hx,hy=hy) for typ,hx,hy in itertools.product([0x59,0x5a],[0,64,120,128,136,255],[0,32,64,80,96,255])]
ROWS += [row(typ=typ,s=4,t=t,free=free,d=d,r3=r) for typ,t,free,d,r in itertools.product([0x56,0x59,0x5a],[0,1],[0,0xff00,0xfe00,0x8000],range(4),[0,3])]
ROWS += [row(typ=typ,s=state,r2=r,r4=r) for typ,state,r in itertools.product([0x56,0x59,0x5a],[2,8],range(16))]
ROWS += [row(typ=typ,s=state,t=t,d=d,x=x,y=y,slot=8) for typ,state,t,d,(x,y) in itertools.product([0x17,0x71],[0,2],[0,1],range(4),[(31,80),(32,32),(128,80),(223,135),(224,136),(8,8)])]
rom=(ROOT/'input/original.sms').read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def generate():
 image=bytearray(rom);code=bytearray();labels={};fix=[];base=0x3000
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=base+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def store(v,a):emit(f'3e{v:02x}32{a&255:02x}{a>>8:02x}')
 # C080..C09F keeps input rows separate from original actor index C046.
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff')
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c0');store(10,0xc008)
 label('case');store(0,0xc002);emit('3a08c032ffff2100c61101c601ff0236a7edb0dd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i in range(5):field(16+i,0xc030+i)
 field(11,0xc313);field(12,0xc311);field(13,0xc0b9);store(1,0xc0ba);field(23,0xc02f)
 emit('3a8ec0c6103246c0');field(15,0xdc00);emit('2100dc1101dc019f00edb0')
 # Tilemap high bytes are uniformly blocked/unblocked. The routine only reads it.
 field(15,0xd600);emit('2100d61101d601ff047eedb0')
 for n in range(16):
  emit(f'3a{0x98+n//8:02x}c0e6{1<<(n&7):02x}');jp('ca',f'pool{n}');store(0,0xc600+n*48);label(f'pool{n}')
 # True parent slot: IX=C600+48*slot, independent of source actor indexC046.
 emit('3a8ec06f260029292929545d29191100c619e5dde1')
 for i,a in [(0,0),(1,1),(2,4),(3,11),(4,14),(5,13),(6,0x20),(7,0x21),(8,10),(9,0x13),(10,0x11),(21,0x18),(22,0x1d),(26,0x2c),(27,5)]:emit(f'3a{0x80+i:02x}c0dd77{a:02x}')
 emit('dd360302dd360c02dd7e00fe71');jp('c2','p17');emit('cdaf43');jp('c3','ready');label('p17');emit('fe17');jp('c2','teleport');emit('cd0640');jp('c3','ready');label('teleport');emit('fe56');jp('c2','aimed');emit('cd0e50');jp('c3','ready');label('aimed');emit('cd1a50')
 label('ready');store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','saveptr');emit('2100803a08c03c3208c0')
 label('saveptr');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*32<=0x18000,len(ROWS)
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732130c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x5806,0),(0x585a,1),(0xa2dc,2),(0xa2f4,3),(0xa164,4)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 folder=ROOT/'validation/dungeon-teleport';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/dungeon_teleport_cases.inc').write_text('static const u8 dungeon_teleport_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/dungeon-teleport-harness'
 for n in ['main.c','actors.c']:assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original dungeon-teleport cases captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  def data(n,size):return bytes(r[(sy[n]+i)^1] for i in range(size))
  def w(n):return int.from_bytes(data(n,2),'big')
  if w('harness_done'):done.append(f)
  if not w('harness_ready'):return
  case=w('harness_case')
  if case in checked:return
  actual=data('world_actor_state',768)
  assert actual==expected[case],(case,ROWS[case],[(j,x,y) for j,(x,y) in enumerate(zip(expected[case],actual)) if x!=y][:24])
  checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS),(len(checked),len(ROWS))
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Five sourceLD A,R sites use explicit register-preserving input shim. Original500E/501A/57F8/5020/4965/4006/43AF execute.','Five states, all128 spawn candidates on three terrains, eight scheduling phases and slots, aimed orientation/ties, timer-vs-flash gates, cooldown outputs, full/first-free shot pool,17/71 initialization and dungeon culling.','Original RNG/global clock, natural rooms/gameplay, complete video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_teleport_allocation_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native dungeon-teleport cases exact')
if __name__=='__main__':main()
