"""Original boss-death state branches and particle placement with explicit inputs."""
import contextlib,hashlib,io,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
ROWS=[(0,x,y,roll,slot) for x,y in [(128,96),(24,24),(232,152),(0,0)] for roll in range(256) for slot in [0,3,7]]
ROWS += [(1,d,state,timer,0) for d in [1,9,10,255] for state in [0,2,4] for timer in [1,2,180]]
def sha(b):return hashlib.sha256(b).hexdigest()
def generate():
 rom=(ROOT/'input/original.sms').read_bytes();code=bytearray();labels={};fix=[];base=0x3000
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=base+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def store(v,a):emit(f'3e{v:02x}32{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e0f32ffff')
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c0')
 label('case');store(0,0xc002)
 emit('2100c61101c601ff0236a7edb021cec011cfc001ff003600edb0')
 store(1,0xc301);store(12,0xc01d);store(8,0xc0a2);store(0,0xde08)
 emit('dd2a06c0dd7e003210c0dd7e013211c0dd7e023212c0dd7e033213c0dd7e043214c0')
 emit('dd2100c6dd360007dd360100dd361160dd3613803a10c0b7');jp('c2','phase')
 emit('3a11c0dd77133a12c0dd77112180c71130003a14c0b7');jp('ca','slot_ready')
 label('slot');emit('193d');jp('c2','slot')
 label('slot_ready');emit('3600e5fde13a13c0cd0c4c');jp('c3','ready')
 label('phase');emit('3a11c03237c03a12c0dd77013a13c0dd7728cda44b')
 label('ready');store(1,0xc002);emit('0603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0110500192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x4000 and len(ROWS)*5<0x4000
 image=bytearray(rom);image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code;image[0x3c000:0x3c000+len(ROWS)*5]=bytes(v for row in ROWS for v in row)
 assert image[0x4ba4:0x4c5d]==rom[0x4ba4:0x4c5d]
 folder=ROOT/'validation/boss-death';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/boss_death_cases.inc').write_text('static const u8 boss_death_cases[][5]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in ROWS)+'};\n')
 return rom,image,folder

def main():
 rom,image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/boss-death-harness'
 for n in ['main.c','actors.c']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else n)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[]
 def sms(f,r):
  if r[4]:done.append(f)
  if not r[2]:return
  case=int.from_bytes(r[:2],'little')
  expected.setdefault(case,(bytes(r[0x600:0x900]),bytes(r[0xce:0x1ce]),r[0x301],r[0x1d],r[0x1e08],r[0xa2]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',25000,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS))
 print(len(expected),'original boss-death/particle cases captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  def data(n,size,off=0):return bytes(r[(sy[n]+off+i)^1] for i in range(size))
  def w(n):return int.from_bytes(data(n,2),'big')
  if w('harness_done'):done.append(f)
  if not w('harness_ready'):return
  case=w('harness_case')
  if case in checked:return
  actual=(data('world_actor_state',768),data('harness_progress',256),w('harness_hero'),w('harness_game'),w('harness_effect'),w('harness_count'))
  assert actual==expected[case],(case,ROWS[case],[(i,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:16] if isinstance(a,bytes) else (a,b)) for i,(a,b) in enumerate(zip(expected[case],actual)) if a!=b])
  checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',25000,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS),(len(checked),len(ROWS))
 result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),particle_placement_cases=3072,state_cases=36,original_routines_executed=['4C0C..4C3E with explicit A/IX/IY placement inputs','4BA4..4C5C with occupied transient slots in state 2'],all_actor_records_progression_hero_game_state_effect_and_count_fields_exact=True,full_game_ported=False,limits=['Particle inputs enumerate 256 random-byte values, four interior/boundary positions and first-free transient slots 0,3,7; source fixture provides the corresponding IY slot. Native helper scans the actual occupied pool.','State cases cover dungeon bytes 1,9,10,FF, states 0,2,4 and counters 1,2,180. Occupied slots suppress particle spawning in state 2 without altering original LD A,R.','The original random stream, natural boss fights, final ending execution, exact video timing and full rendered particles are not proved.'])
 (ROOT/'validation/boss_death_unit_report.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checked),'native boss-death/particle cases exact')
if __name__=='__main__':main()
