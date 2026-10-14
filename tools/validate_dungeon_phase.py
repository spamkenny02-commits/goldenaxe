"""Original/native4D32/4D38 explicit state, placement and motion comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# type,state,timer,anim,phase,period,walks,delay,dir20,x,y,hx,hy,roomlo,slot,
# terrain,r0,r1,r2,r3,r4,heightlo,heighthi,frame, eight reserved bytes
def row(typ=0x47,s=0,t=0,a=0,p=0,period=4,walks=0,delay=1,d=0,x=128,y=80,hx=224,hy=144,room=0x12,slot=0,terrain=0,r0=1,r1=1,r2=0,r3=0,r4=15,height=0,frame=0,free=0):
 return (typ,s,t,a,p,period,walks,delay,d,x,y,hx,hy,room,slot,terrain,r0,r1,r2,r3,r4,height&255,(height>>8)&255,frame)+tuple([free]+[0]*7)
ROWS=[row(typ=typ,s=s,t=t,a=a,period=period) for typ in range(0x46,0x4a) for s,t,a,period in itertools.product(range(0,10 if typ==0x46 else 12,2),[0,1],[0,3],[4,10])]
ROWS += [row(r0=c) for c in range(128)]
ROWS += [row(r0=c,terrain=terrain) for c,terrain in itertools.product([0,1,7,65,119,127],[1,3,58])]
ROWS += [row(typ=typ,s=4,d=d,x=x,y=y,r2=sel,r3=turn) for typ,(x,y),d,sel,turn in itertools.product(range(0x47,0x4a),[(48,32),(192,128),(128,80)],range(8),[0,1],[0,35])]
ROWS += [row(typ=typ,s=s,period=period,delay=delay,a=a) for typ,s,period,delay,a in itertools.product(range(0x47,0x4a),[8,10],[4,9,10],[1,32,64],[0,1])]
ROWS += [row(typ=0x46,s=6,x=x,y=y,r0=15,r1=d,terrain=terrain) for d,(x,y),terrain in itertools.product(range(8),[(128,80),(40,48),(216,128)],[0,0xe0])]
ROWS += [row(typ=0x46,s=6,hx=hx,hy=hy,r0=0) for hx,hy in itertools.product([32,128,224],[32,80,144])]
ROWS += [row(typ=0x46,s=2,hx=hx,hy=hy) for hx,hy in itertools.product([99,100,127,128,155,156,157],[51,52,79,80,107,108,109])]
ROWS += [row(typ=0x46,room=room,slot=slot) for room,slot in itertools.product([0x12,0x1d,0x6d,0x7c,0x9b,0xd2,0xe3],range(4))]
ROWS += [row(typ=0x46,s=8,height=h,r2=v&255,r3=(v>>8)&255) for h,v in itertools.product([0,1,500,65535],[0,528,65504,65008])]
ROWS += [row(typ=0x49,s=10,delay=32,d=d,free=1<<slot) for d,slot in itertools.product(range(4),range(8))]
ROWS += [row(typ=typ,s=10,delay=32,free=255) for typ in [0x47,0x48,0x49]]
# Room loader initializes animation to zero before state0; shared984F falls
# into the unrelated43..45 table for stale animation3, beyond its valid indices.
ROWS=[r for r in ROWS if not (r[0]>=0x47 and r[1]==0 and r[3]!=0)]
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
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c0');store(14,0xc008)
 label('case');store(0,0xc002);emit('3a08c032ffff2100c61101c601ff0236a7edb0dd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i in range(5):field(16+i,0xc030+i)
 field(11,0xc313);field(12,0xc311);field(13,0xc0b9);store(1,0xc0ba);field(23,0xc02f)
 emit('3a8ec0c6103246c0');field(15,0xdc00);emit('2100dc1101dc019f00edb0')
 # Tilemap high bytes are uniformly blocked/unblocked. The routine only reads it.
 field(15,0xd600);emit('2100d61101d601ff047eedb0')
 for n in range(8):
  emit(f'3a98c0e6{1<<n:02x}');jp('ca',f'pool{n}');store(0,0xc780+n*48);label(f'pool{n}')
 emit('dd2100c6')
 for i,a in [(0,0),(1,1),(2,4),(3,11),(4,14),(5,13),(6,0x2e),(7,0x2f),(8,0x20),(9,0x13),(9,0x23),(10,0x11),(10,0x27),(21,0x2a),(22,0x2b)]:emit(f'3a{0x80+i:02x}c0dd77{a:02x}')
 emit('dd360302dd360a01dd360c02dd362100dd362200dd362400dd362500dd3626003a80c0fe46');jp('c2','phase')
 emit('dd362ee0dd362fff3a92c0dd77283a93c0dd7729cd324d');jp('c3','ready')
 label('phase');emit('cd384d')
 label('ready');store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','saveptr');emit('2100803a08c03c3208c0')
 label('saveptr');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*32<=0x8000,len(ROWS)
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x38000:0x38000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732130c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x5806,0),(0x585a,1),(0x4ebe,3),(0x4ed5,2),(0x4a57,0),(0x4a5f,1)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 image[0x4e1:0x4e5]=bytes.fromhex('3a34c0c9')
 folder=ROOT/'validation/dungeon-phase';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/dungeon_phase_cases.inc').write_text('static const u8 dungeon_phase_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/dungeon-phase-harness'
 for n in ['main.c','actors.c']:assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original dungeon-phase cases captured',flush=True)
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
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_exact=True,full_game_ported=False,limits=['Six LD A,R sites use explicit register-preserving input shim;04E1 supplies explicit gate byte. Other original4D32/4D38/57F8/5878/4A57 and shared motion instructions execute.','Four types/states, fixed placements,128 spawn candidates and rejected terrain, selection/bounds, pause transitions,49 firing with a full and partially free projectile pools (first-free allocation and failure), proximity, jump vector/bounds/terrain and ballistic height.','State0 uses loader-initialized animation0; stale animation3 enters an unrelated out-of-range movement table and is outside the fixture.','Original RNG/global clock, natural rooms/routes, complete video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_phase_allocation_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native dungeon-phase cases exact')
if __name__=='__main__':main()
