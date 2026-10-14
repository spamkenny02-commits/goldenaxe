"""Original/native54D9,4518 and46B4 one-call state comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# kind,state,timer,anim,phase,count22,dir,count23,occupied,x,y,hx,hy,
# parentx,parenty,dylo,dyhi,dxlo,dxhi,flags,variant20,variant21,roll0,roll1
def row(kind=0,state=0,timer=0,anim=0,phase=0,count=0,direction=1,shots=0,occupied=0,x=128,y=96,hx=224,hy=144,px=128,py=96,dy=0,dx=0,flags=0x43,v20=0,v21=0,r0=15,r1=0):
 return (kind,state,timer,anim,phase,count,direction,shots,occupied,x,y,hx,hy,px,py,dy&255,(dy>>8)&255,dx&255,(dx>>8)&255,flags,v20,v21,r0,r1)
ROWS=[row(state=s,timer=t,anim=a,count=0,shots=1) for s,t,a in itertools.product(range(0,20,2),[0,1,64],[0,2])]
ROWS += [row(state=4,x=x,y=y,hx=hx,hy=hy,r0=r) for (x,y),(hx,hy),r in itertools.product([(48,48),(208,136),(128,96)],[(32,32),(128,32),(224,32),(32,96),(128,96),(224,96),(32,144),(128,144),(224,144)],[0,15])]
ROWS += [row(state=6,count=d) for d in range(8)]
ROWS += [row(state=s,r0=r) for s,r in itertools.product([4,8],range(16))]
ROWS += [row(state=12,shots=c,occupied=n) for c,n in itertools.product([0,1,2,255],[0,7,8])]
ROWS += [row(state=16,anim=2,occupied=n,r1=r) for n,r in itertools.product(range(9),range(4))]
ROWS += [row(state=18,occupied=n) for n in range(9)]
ROWS += [row(kind=1,hx=hx,hy=hy) for hx,hy in itertools.product([32,128,224],[32,96,144])]
ROWS += [row(kind=1,state=s,count=c,x=x,y=y,dx=dx,dy=dy,flags=fl,v21=back) for s,c,(x,y),(dx,dy),fl,back in itertools.product([2,4],[1,48,49,192],[(39,31),(216,144),(128,96)],[(-512,512),(512,-512)],[0x13,0x17],[0,1])]
ROWS += [row(kind=1,state=4,count=80,x=x,y=y,dx=v,dy=v) for x,y,v in itertools.product([112,128,143],[72,96,119],[-512,0,512])]
ROWS += [row(kind=1,state=s,count=80,x=x,y=y,dx=v,dy=v) for s,(x,y),v in itertools.product([2,4],[(127,95),(128,96),(129,97),(224,144)],[-800,-768,-767,-544,-512,-1,0,511,512,736,767,768])]
rom=(ROOT/'input/original.sms').read_bytes()
for variant,branch in itertools.product(range(4),range(4)):
 address=int.from_bytes(rom[0x4745+variant*8+branch*2:0x4747+variant*8+branch*2],'little')
 terminal=next(n for n in range(8) if rom[address+n*2]==255)
 ROWS += [row(kind=2,state=2,count=n,v20=variant,v21=branch) for n in range(terminal+1)]
ROWS += [row(kind=2,state=s,anim=a,phase=p,v20=0,v21=0) for s,a,p in itertools.product([0,4],[0,2,3],[0,4,5])]
ROWS += [row(kind=2,state=2,px=x,py=y,v20=0,v21=0) for x,y in itertools.product([24,25,128,231,232],[24,25,96,144,145])]
def sha(b):return hashlib.sha256(b).hexdigest()
def generate():
 image=bytearray(rom);code=bytearray();labels={};fix=[];base=0x3000
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=base+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def store(v,a):emit(f'3e{v:02x}32{a&255:02x}{a>>8:02x}')
 def field(i,a):emit(f'3a{0x40+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff')
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c0')
 label('case');store(0,0xc002);store(15,0xffff)
 emit('2100c61101c601ff0236a7edb0dd2a06c0')
 for i in range(24):emit(f'dd7e{i:02x}32{0x40+i:02x}c0')
 field(22,0xc030);field(23,0xc031)
 emit('2180c71130000608');label('pool');emit('36001910fb')
 emit('3a48c047b7');jp('ca','parent');emit('2180c7');label('occupied');emit('36a71910fb')
 label('parent');store(0x6c,0xc600);field(13,0xc613);field(14,0xc611);field(11,0xc313);field(12,0xc311)
 emit('dd2100c63a40c0b7');jp('ca','target')
 emit('dd2180c7c674dd7700fe76');jp('c2','target');emit('dd360c04dd360d06')
 label('target')
 for i,a in [(1,1),(2,4),(3,11),(4,14),(5,0x22),(6,10),(7,0x23),(9,0x13),(10,0x11),(15,0x14),(16,0x15),(17,0x16),(18,0x17),(19,3),(20,0x20),(21,0x21)]:emit(f'3a{0x40+i:02x}c0dd77{a:02x}')
 emit('fd2100803a40c0b7');jp('ca','boss');emit('3d');jp('ca','shot');emit('cdb446');jp('c3','ready')
 label('boss');emit('cdd954');jp('c3','ready');label('shot');emit('cd1845')
 label('ready');store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0111800192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*24<=0x4000,len(ROWS)
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*24]=bytes(v for r in ROWS for v in r)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732130c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x554c,0),(0x5731,1)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 folder=ROOT/'validation/sword-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/sword_boss_cases.inc').write_text('static const u8 sword_boss_cases[][24]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/sword-boss-harness'
 for n in ['main.c','actors.c']:assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original sword boss/shot/path cases captured',flush=True)
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
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),boss_cases=sum(r[0]==0 for r in ROWS),projectile_cases=sum(r[0]==1 for r in ROWS),satellite_cases=sum(r[0]==2 for r in ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Two LD A,R sites use explicit register-preserving inputs. Other original54D9/577F/5467/4518/46B4 instructions execute.','Selected ten boss/three shot/three satellite states, chase limits, attraction caps, returning axes, bounce/counter, path end and bounds. Already-full allocation fixtures supply ROM IY8000; inherited RAM IY effects remain unsupported.','Original RNG/global clock, natural fights/routes, full video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/sword_boss_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native sword boss/shot/path cases exact')
if __name__=='__main__':main()
