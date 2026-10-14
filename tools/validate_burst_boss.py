"""Original/native54D3/4457 states and57F8 explicit placement inputs."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# kind,parent_type,state,timer,animation,phase,pool_or_own_counter,dir,frame,slot,x,y,hx,hy,terrain_or_class,roll
ROWS=[(0,typ,s,t,a,0,0,1,0,0,128,56,224,144,0,0) for typ,s,t,a in itertools.product([0x6a,0x6b],range(0,16,2),[0,1,56],[0,5,6])]
ROWS += [(0,typ,8,0,0,0,c,1,0,0,128,56,224,144,0,0) for typ,c in itertools.product([0x6a,0x6b],range(9))]
ROWS += [(0,0x6a,14,0,0,3,0,1,0,0,128,56,224,144,terrain,r) for terrain,r in itertools.product([0,2],range(128))]
ROWS += [(0,0x6b,14,0,0,2,0,1,0,0,128,56,hx,hy,terrain,r) for r,(hx,hy),terrain in itertools.product([1,7,65,119],[(24,32),(24,144),(224,32),(224,144),(128,96)],[0,3,1,58,2])]
ROWS += [(0,0x6a,14,0,0,1,0,1,f,slot,128,56,224,144,0,7) for f,slot in itertools.product(range(8),range(8))]
ROWS += [(1,typ,0,0,0,0,0,d,0,8,128,96,224,144,0,0) for typ,d in itertools.product([0x6a,0x6b],range(8))]
ROWS += [(1,typ,s,t,0,0,c,1,0,8,128,96,224,144,0,0) for typ,s,t,c in itertools.product([0x6a,0x6b],range(0,12,2),[0,1,12],[0,1,24,32,56])]
ROWS += [(1,0x6b,6,t,0,0,0,1,0,8,x,y,224,144,cls,0) for t,x,y,cls in itertools.product([0,1],[7,31,32,223,224,247,248],[7,31,32,135,136,151,152],[0,1])]
def sha(b):return hashlib.sha256(b).hexdigest()
def generate():
 rom=(ROOT/'input/original.sms').read_bytes();image=bytearray(rom);code=bytearray();labels={};fix=[];base=0x3000
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=base+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def store(v,a):emit(f'3e{v:02x}32{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff')
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c0')
 label('case');store(0,0xc002);store(15,0xffff)
 emit('2100c61101c601ff0236a7edb0dd2a06c0')
 for i in range(16):emit(f'dd7e{i:02x}32{0x10+i:02x}c0')
 emit('3a1fc03220c03a15c03221c03a1ec032bac02100dc1101dc019f003a1ec077edb02180c71130000608')
 label('pool');emit('36001910fb3a10c0b7');jp('c2','parent_ready')
 emit('2180c73a16c047b7');jp('ca','parent_ready')
 label('occupied');emit('36a71910fb')
 label('parent_ready');emit('3a11c03200c63a1cc03213c33a1dc03211c33a18c0322fc03a19c0c6103246c0dd2100c63a10c0b7');jp('ca','target')
 emit('dd2180c7dd360074')
 label('target');emit('3a12c0dd77013a13c0dd77043a14c0dd770b3a15c0dd770e3a16c0dd77223a17c0dd770a3a1ac0dd77133a1bc0dd7711fd2100803a10c0b7');jp('c2','projectile')
 emit('cdd354');jp('c3','ready')
 label('projectile');emit('cd5744')
 label('ready');store(1,0xc002);emit('0603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0111000192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*16<=0x4000
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*16]=bytes(v for row in ROWS for v in row)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732120c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x5806,0),(0x585a,1)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 folder=ROOT/'validation/burst-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/burst_boss_cases.inc').write_text('static const u8 burst_boss_cases[][16]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in ROWS)+'};\n')
 return rom,image,folder
def main():
 rom,image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/burst-boss-harness'
 for n in ['main.c','actors.c']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS))
 print(len(expected),'original burst/placement/projectile cases captured',flush=True)
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
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),boss_cases=sum(not row[0] for row in ROWS),projectile_cases=sum(row[0] for row in ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Two57F8 LD A,R sites replaced by register-preserving explicit input shim. Other original54D3/AB40/57F8/4457/3DAF/3DFA and allocator instructions execute.','Selected eight boss/six projectile states, parent variants, waits/animation, all128 placement candidates with accepted/rejected terrain plus proximity/phase cases, partial/full pools. Full pools supply ROM-resident IY8000; writes ignored as on source. Inherited RAM IY for an already-full pool is not reproduced.','Original RNG/refresh and global placement clock phase, natural fights, complete video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/burst_boss_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native burst/placement/projectile cases exact')
if __name__=='__main__':main()
