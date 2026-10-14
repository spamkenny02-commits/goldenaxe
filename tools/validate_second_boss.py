"""Compare type65 core and type66 satellites against original instructions."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# kind,state,timer,flash,pool_count,x,y,previous_dir,select,turn,gate,radius,phase
ROWS=[(0,s,t,f,c,128,96,3,1,0,255,16,0) for s,t,f,c in itertools.product([0,2,4,6,8],[0,1,32],[0,1],[0,3,4,8])]
ROWS += [(0,4,0,0,8,x,y,d,s,t,255,16,0) for d,s,t,(x,y) in itertools.product(range(8),[0,1,32,255],[0,3,32,255],[(32,32),(128,96),(224,144)])]
ROWS += [(0,6,0,0,3,128,96,0,s,0,g,16,0) for s,g in itertools.product([0,63,64,255],[0,7,8,255])]
ROWS += [(2,6,0,0,c,128,96,3,s,32,g,16,0) for s,g,c in itertools.product([0,1,32,255],[0,7,8,255],[0,3,8])]
ROWS += [(0,8,10,0,p%9,128,96,p&1,0,0,255,p&31,p) for p in range(256)]
ROWS += [(0,8,10,0,c,128,96,d,0,0,255,r,p) for c,d,r,p in itertools.product([0,8],[0,1],[0,15,31,255],[0,64,128,192])]
ROWS += [(1,s,0,0,0,x,y,0,0,0,0,dx,dy) for s,x,y,(dx,dy) in itertools.product([0,2],[0,24,25,231,232],[0,16,17,151,152],[(0,0),(255,255),(16,16),(128,128),(31,224)])]
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
 for i in range(13):emit(f'dd7e{i:02x}32{0x10+i:02x}c0')
 emit('dd2100c6dd3600653a15c0dd77133a16c0dd77112180c71130000608')
 label('pool');emit('36001910fb2180c73a14c047b7');jp('ca','pool_ready')
 label('occupied');emit('36661910fb')
 label('pool_ready');emit('3a10c0fe01');jp('ca','satellite')
 emit('3a11c0dd77013a12c0dd7704dd772f3a13c0dd77053a17c0dd7720e601dd772a3a14c0dd772b3a1bc0dd77283a1cc0dd7729dd362e00')
 emit('3a10c0fe02');jp('c2','countdown_ready');emit('dd362e14');label('countdown_ready')
 store(224,0xc313);store(144,0xc311);emit('3a18c0473a19c04fcd7150');jp('c3','ready')
 label('satellite');emit('dd2180c7dd3600663a11c0dd77013a1bc0dd77203a1cc0dd7721cd2b51')
 label('ready');store(1,0xc002);emit('0603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0110d00192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3da5 and len(ROWS)*13<0x4000
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*13]=bytes(v for row in ROWS for v in row)
 for pos,op in [(0x4ed5,0x78),(0x4ebe,0x79),(0xa935,0x78)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([op,0])
 image[0x4e1:0x4e5]=bytes.fromhex('3a1ac0c9')
 folder=ROOT/'validation/second-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/second_boss_cases.inc').write_text('static const u8 second_boss_cases[][13]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in ROWS)+'};\n')
 return rom,image,folder
def main():
 rom,image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/second-boss-harness'
 for n in ['main.c','actors.c']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS))
 print(len(expected),'original core/satellite cases captured',flush=True)
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
 result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),core_cases=sum(row[0]!=1 for row in ROWS),satellite_cases=sum(row[0]==1 for row in ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Three LD A,R instructions use explicit B/C byte inputs; 04E1 random-byte function is replaced with an explicit fixture input. All other core/satellite/chooser/boundary/orbit instructions execute original code.','Every phase 0..255 exercised; selected extreme radius/direction/pool cases, five core states, 20-segment countdown, source selection branches and satellite wrapping/boundaries. Not all possible input combinations.','Original random/refresh sequence, natural combat, pixel/SAT equality, complete audio and hardware timing remain unverified.'])
 (ROOT/'validation/second_boss_unit_report.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checked),'native core/satellite cases exact')
if __name__=='__main__':main()
