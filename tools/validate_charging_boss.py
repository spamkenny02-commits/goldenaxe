"""Original/native 51AE state, pursuit, attack and rebound comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# type,state,timer,x,y,hx,hy,dir,segments,attempts,reserved,attack,direction,aim,bounce,inherited_E
ROWS=[(typ,s,t,128,96,224,144,1,128,13,0,32,0,8,0,0) for typ,s,t in itertools.product([0x68,0x69,0x7a,0x7b],range(0,20,2),[0,1,32])]
ROWS += [(typ,s,0,x,y,hx,hy,1,128,13,0,r,0,8,0,0) for typ,s,(x,y),(hx,hy),r in itertools.product([0x68,0x69],[4,6],[(48,48),(208,136),(128,96)],[(32,32),(128,32),(224,32),(32,96),(128,96),(224,96),(32,144),(128,144),(224,144)],[0,6,32])]
ROWS += [(0x69,16,0,128,96,hx,hy,1,128,13,0,32,d,a,0,0) for d,a,(hx,hy) in itertools.product(range(8),[0,7,8,15],[(32,32),(128,96),(224,144)])]
ROWS += [(0x69,18,t,x,y,224,144,1,128,n,0,32,0,a,b,0) for t,(x,y),n,a,b in itertools.product([0,1],[(128,55),(128,144),(47,96),(208,96),(128,96)],[1,2,13],[0,8],[0,4,8,12])]
ROWS += [(typ,18,0,128,96,224,144,1,1,n,0,32,0,8,0,e) for typ,n,e in itertools.product([0x68,0x69],[1,2],range(4))]
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
 for a,b in [(0x1c,0x20),(0x1d,0x21),(0x1e,0x22),(0x1b,0x23)]:emit(f'3a{a:02x}c032{b:02x}c0')
 emit('dd2100c63a10c0dd77003a11c0dd77013a12c0dd77043a13c0dd77133a14c0dd77113a15c03213c33a16c03211c33a17c0dd770add7720dd77223a18c0dd77213a19c0dd77253a1fc05f1600cdae51')
 store(1,0xc002);emit('0603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0111000192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*16<0x4000
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*16]=bytes(v for row in ROWS for v in row)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732120c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x52dc,0),(0x52e3,1),(0x53b7,2),(0x53e3,2),(0x540f,2),(0x543b,2)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 image[0x4e1:0x4e5]=bytes.fromhex('3a23c0c9')
 folder=ROOT/'validation/charging-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/charging_boss_cases.inc').write_text('static const u8 charging_boss_cases[][16]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in ROWS)+'};\n')
 return rom,image,folder
def main():
 rom,image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/charging-boss-harness'
 for n in ['main.c','actors.c']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS))
 print(len(expected),'original pursuit/charge cases captured',flush=True)
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
 result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Six LD A,R sites replaced by register-preserving explicit-input shim; 04E1 random byte replaced with fixture input. Other original51AE/577F/3F07 state/aim/bounds arithmetic executes unchanged.','All ten states and four shared types, selected chase axes/bounds, charge octants/aim modes, rebound choices, counters and inherited E values0..3. Not all field combinations.','Original RNG/refresh, inherited caller E on degenerate interior128-segment expiry in production, natural fights, full graphics/audio and hardware timing remain unverified.'])
 (ROOT/'validation/charging_boss_unit_report.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checked),'native pursuit/charge cases exact')
if __name__=='__main__':main()
