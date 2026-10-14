"""Execute original first-boss branches with explicit refresh-byte inputs."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
PAIRS=[(5,0),(1,4),(0,5)]
ROWS=[(s,d,t,p,g,c,8,0) for s,d,t,p,g,c in itertools.product([0,2,4,6,8,10],[0,1],[0,1,32],range(3),[0,3,4,15],[0,12,13])]
ROWS += [(s,d,0,0,0,0,free,0) for s,d,free in itertools.product([8,10],[0,1],[1,2,3,4,5,7])]
ROWS += [(0,0,1,x,y,slot,0,1) for x,y,slot in itertools.product([32,128,224],[16,96,144],range(8,16))]
ROWS += [(0,d,1,128,96,8,0,2) for d in range(5)]
ROWS += [(2,1,t,x,y,8,cls,kind) for t,x,y,cls,kind in itertools.product([0,1],[7,31,32,223,224,247,248],[7,31,32,135,136,151,152],[0,1],[1,2])]
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
 for i in range(8):emit(f'dd7e{i:02x}32{0x10+i:02x}c0')
 emit('dd2100c63a10c0dd77013a11c0dd770a3a12c0dd7704dd361160dd3613803a17c0b7');jp('c2','shot')
 emit('dd3600643a13c08721')
 pair_addr_pos=len(code);emit('0000856f3001247edd7720237edd7721')
 # Mark the final free slots empty; preceding occupied records retain A7 bytes.
 emit('3e083a16c0473e0890472180c711300078b7');jp('ca','free')
 label('occupied');emit('1910fd')
 label('free');emit('3a16c047')
 label('empty');emit('36001910fb')
 emit('3a14c0473a15c04fcd6b50');jp('c3','ready')
 label('shot');emit('3a13c03213c33a14c03211c33a10c0b7');jp('ca','shot_pos_ready')
 emit('3a13c0dd77133a14c0dd7711')
 label('shot_pos_ready');emit('3a15c0c6103246c03a16c032bac03a17c0fe01');jp('c2','fan')
 emit('dd360072cdd243');jp('c3','ready')
 label('fan');emit('dd360073cd2b44')
 label('ready');store(1,0xc002);emit('0603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0110800192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 label('pairs');code.extend(bytes(v for p in PAIRS for v in p));code[pair_addr_pos:pair_addr_pos+2]=labels['pairs'].to_bytes(2,'little')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3da5 and len(ROWS)*8<0x4000
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x3c000:0x3c000+len(ROWS)*8]=bytes(v for row in ROWS for v in row)
 assert image[0xa7b9:0xa7bb]==b'\xed\x5f' and image[0xa7cb:0xa7cd]==b'\xed\x5f'
 image[0xa7b9:0xa7bb]=b'\x78\x00';image[0xa7cb:0xa7cd]=b'\x79\x00'
 folder=ROOT/'validation/first-boss';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/first_boss_cases.inc').write_text('static const u8 first_boss_cases[][8]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in ROWS)+'};\n')
 return rom,image,folder
def main():
 rom,image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/first-boss-harness'
 for n in ['main.c','actors.c']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS))
 print(len(expected),'original boss/projectile cases captured',flush=True)
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
 result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),boss_cases=sum(row[7]==0 for row in ROWS),projectile_cases=sum(row[7]!=0 for row in ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Only two LD A,R instructions are replaced with explicit B/C byte inputs, preserving all other first-boss instructions and callees. Original random/refresh sequence is not reproduced.','Direct state tests: six boss states, both directions, three timers, three counters, gate/choice boundaries, eight free slots and partially occupied pools.','Projectile tests execute original 43D2/442B, initialization, octants, absolute slots 8..15, five fan directions, exterior/dungeon bounds and lifetime.','Already-full fan pool inherited IY side effects, full frame integration, natural boss fight, exact graphics/audio and hardware timing are not proved.'])
 (ROOT/'validation/first_boss_unit_report.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checked),'native boss/projectile cases exact')
if __name__=='__main__':main()
