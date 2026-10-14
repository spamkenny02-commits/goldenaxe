"""Original/native55F1 state and post-state damage-filter comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# state,timer,flash,anim,phase,shots,occupied,x,y,hx,hy,dir,count22,flags,
# pending,selected,weapon,roll0,roll1,dylo,dyhi,dxlo,dxhi,reserved
def row(s=0,t=0,f=0,a=0,p=0,shots=3,occ=0,x=128,y=72,hx=224,hy=144,d=1,c=0,flags=0x43,damage=8,item=1,weapon=2,r0=15,r1=0,dy=64,dx=-64):
 return (s,t,f,a,p,shots,occ,x,y,hx,hy,d,c,flags,damage,item,weapon,r0,r1,dy&255,(dy>>8)&255,dx&255,(dx>>8)&255,0)
ROWS=[row(s=s,t=t,f=f,a=a) for s,t,f,a in itertools.product(range(0,20,2),[0,1],[0,1],[0,2])]
ROWS += [row(s=s,item=i,weapon=w) for s,i,w in itertools.product(range(0,20,2),[0,1,2,255],[0,1,2,3])]
ROWS += [row(s=s,x=x,y=y,hx=hx,hy=hy) for s,(x,y),(hx,hy) in itertools.product([2,4,6],[(48,48),(208,136),(128,96)],[(32,0),(128,15),(224,16),(32,32),(128,96),(224,128),(32,144),(128,152),(224,255)])]
ROWS += [row(s=8,r0=r,hy=hy) for r,hy in itertools.product(range(16),[0,15,16,87,88])]
ROWS += [row(s=12,shots=c,occ=n) for c,n in itertools.product([0,1,2,3,255],[0,7,8])]
ROWS += [row(s=16,a=2,occ=n,r1=r) for n,r in itertools.product(range(9),range(4))]
ROWS += [row(s=18,occ=n,t=t) for n,t in itertools.product(range(9),[0,1])]
ROWS += [row(s=10,t=0,a=a,p=p) for a,p in itertools.product([0,1,2,3],[0,7,15])]
rom=(ROOT/'input/original.sms').read_bytes()
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
 field(17,0xc030);field(18,0xc031);field(15,0xc0df);field(16,0xc0e1);field(9,0xc313);field(10,0xc311)
 emit('2180c71130000608');label('pool');emit('36001910fb')
 emit('3a46c047b7');jp('ca','target');emit('2180c7');label('occupied');emit('36a71910fb')
 label('target');emit('dd2100c6dd36006d')
 for i,a in [(0,1),(1,4),(2,5),(3,11),(4,14),(5,0x23),(7,0x13),(8,0x11),(11,10),(12,0x22),(13,3),(14,0x1d),(19,0x14),(20,0x15),(21,0x16),(22,0x17)]:emit(f'3a{0x40+i:02x}c0dd77{a:02x}')
 emit('fd210080cdf155')
 store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0111800192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*24<=0x4000,len(ROWS)
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*24]=bytes(v for r in ROWS for v in r)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732130c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x568c,0),(0x5731,1)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 folder=ROOT/'validation/final-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/final_boss_cases.inc').write_text('static const u8 final_boss_cases[][24]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/final-boss-harness'
 for n in ['main.c','actors.c']:assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original final-boss states/filter cases captured',flush=True)
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
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Two LD A,R sites use explicit register-preserving inputs. Other original55F1 state dispatch, post-state weapon filter,577F/5467 and shared satellite allocator instructions execute.','Ten states, selected item/weapon level matrix, heroY-16 byte wrap, chase bounds, attack gates, shot counters, partial/full allocations and wait pool. Full pools supply ROM IY8000; inherited RAM IY effects remain unsupported.','Original RNG/global clock, natural fight, ending, complete video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/final_boss_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native final-boss states/filter cases exact')
if __name__=='__main__':main()
