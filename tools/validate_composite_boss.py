"""Execute original type67 states with explicit refresh-byte inputs."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# slot,state,timer,hp,damage,parent_type,parent_state,formation,spawn_mode,pool_count,roll[4]
ROWS=[(0,s,t,60,d,0x67,8,f,0,0,0,0,0,15) for s,t,f,d in itertools.product(range(0,16,2),[0,1,39],range(3),[0,1,60])]
ROWS += [(slot,s,t,0,0,pt,ps,f,0,0,0,0,0,15) for slot,s,t,(pt,ps),f in itertools.product(range(1,6),range(16,24,2),[0,1,48],[(0x67,8),(0x67,14),(7,0)],range(3))]
ROWS += [(0,6,0,60,0,0x67,8,f,0,0,0,r,0,15) for f,r in itertools.product(range(3),range(8))]
ROWS += [(0,14,0,60,0,0x67,8,f,0,0,r,0,0,15) for f,r in itertools.product(range(3),range(4))]
ROWS += [(slot,20,0,0,0,0x67,8,0,0,c,0,0,d,r) for slot,c,d,r in itertools.product([1,5],[0,3,8],[0,15],[0,3,4,15])]
ROWS += [(slot,18,0,0,0,0x67,8,f,0,0,0,0,d,15) for slot,f,d in itertools.product(range(1,6),range(3),[0,15])]
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
 for i in range(14):emit(f'dd7e{i:02x}32{0x10+i:02x}c0')
 for i in range(4):emit(f'3a{0x1a+i:02x}c032{0x20+i:02x}c0')
 emit('2180c71130000608')
 label('pool');emit('36001910fb2180c73a19c047b7');jp('ca','pool_ready')
 label('occupied');emit('36011910fb')
 label('pool_ready');emit('3a15c03200c63a16c03201c63a17c03221c62100c61130003a10c0b7');jp('ca','target')
 label('slot');emit('193d');jp('c2','slot')
 label('target');emit('e5dde1dd3600673a11c0dd77013a12c0dd77043a13c0dd77183a14c0dd771d3a17c0dd77213a18c0dd7720dd361380dd3611603a10c0c6103246c0cd9351')
 store(1,0xc002);emit('0603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0110e00192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*14<0x4000
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*14]=bytes(v for row in ROWS for v in row)
 # RST30 + inline index: preserve BC/DE/HL/IX/IY and return past inline byte.
 image[0x30:0x33]=bytes.fromhex('c3003a')
 handler=bytes.fromhex('e5d5210400395e23561a13722b732120c0856f7ed1e1c9')
 image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0xa9d0,0),(0xaa2a,1),(0xaad1,2),(0xaaed,3),(0xaafa,2)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 folder=ROOT/'validation/composite-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/composite_boss_cases.inc').write_text('static const u8 composite_boss_cases[][14]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in ROWS)+'};\n')
 return rom,image,folder
def main():
 rom,image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/composite-boss-harness'
 for n in ['main.c','actors.c']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS))
 print(len(expected),'original composite boss cases captured',flush=True)
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
 result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Five LD A,R sites replaced with a register-preserving RST30 input shim and explicit formation/position/duration/fire bytes. Other original type67 routines and allocator execute unchanged.','All twelve states, five apparition slots, three formations, selected waits/damage/random boundaries and occupied projectile pools. Not all possible field combinations.','Original random/refresh sequence, natural full fight, SAT/framebuffer/audio and hardware timing remain unverified.'])
 (ROOT/'validation/composite_boss_unit_report.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checked),'native composite boss cases exact')
if __name__=='__main__':main()
