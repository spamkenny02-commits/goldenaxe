"""Original5043 wandering thief5B and grabbed hero/gold state and allocation comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# type,state,timer,anim,phase,period,split20,clock21,dirA,x,y,hx,hy,roomlo,slot,
# terrain,r0..r4,hp,damage,frame,freeLo,freeHi,counter2C,flash,4 reserved

def row(s=8,t=0,a=0,p=0,period=10,esc=0,steal=16,d=1,x=128,y=80,hx=224,hy=144,room=0x13,slot=0,terrain=0,r0=1,r1=1,r2=0,r3=15,r4=15,hp=8,hero_hp=24,frame=0,hero_state=1,hero_counter=0,hero_anim=3,gold=32,pressed=0,flags=2,hxlow=0,hylow=0):
 return (0x5b,s,t,a,p,period,esc,steal,d,x,y,hx,hy,room,slot,terrain,r0,r1,r2,r3,r4,hp,hero_hp,frame,hero_state,hero_counter,hero_anim,gold,pressed,flags,hxlow,hylow)
ROWS=[row(s=state,t=t,a=anim,d=d) for state,t,anim,d in itertools.product(range(0,14,2),[0,1],[0,3],range(4))]
ROWS += [row(s=0,r0=c,terrain=terrain) for c,terrain in itertools.product(range(128),[0,3,128])]
ROWS += [row(s=8,hx=hx,hy=hy,d=d,terrain=terrain,r3=r) for hx,hy,d,terrain,r in itertools.product([32,128,224],[32,80,144],range(4),[0,32,128],[0,1,2,15])]
ROWS += [row(s=10,hx=hx,hy=hy,hero_state=hs,t=t) for hx,hy,hs,t in itertools.product([0,119,120,128,136,137,255],[0,71,72,80,88,89,255],[1,12],[0,1])]
ROWS += [row(s=12,hero_hp=hp,hero_state=hs,hero_counter=hc,esc=esc,steal=steal,gold=gold,pressed=pressed,hxlow=17,hylow=29) for hp,hs,hc,esc,steal,gold,pressed in itertools.product([0,24],[1,12],[0,1],[0,5,6,255],[0,1,2,16],[0,1,255],[0,1,15,16])]
ROWS += [row(s=12,frame=f,pressed=p,steal=1) for f,p in itertools.product(range(8),range(16))]
ROWS=[r for r in ROWS if not (r[1]==0 and r[3]!=0)]
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
 for i,address in [(24,0xc301),(25,0xc304),(26,0xc30b),(22,0xc318),(27,0xc0dd),(28,0xc021),(30,0xc312),(31,0xc310)]:field(i,address)
 store(0,0xde08)
 field(11,0xc313);field(12,0xc311);field(13,0xc0b9);store(1,0xc0ba);field(23,0xc02f)
 emit('3a8ec0c6103246c0');field(15,0xdc00);emit('2100dc1101dc019f00edb0')
 # Tilemap high bytes are uniformly blocked/unblocked. The routine only reads it.
 field(15,0xd600);emit('2100d61101d601ff047eedb0')
 # True parent slot: IX=C600+48*slot, independent of source actor indexC046.
 emit('3a8ec06f260029292929545d29191100c619e5dde1')
 for i,a in [(0,0),(1,1),(2,4),(3,11),(4,14),(5,13),(6,0x20),(7,0x21),(8,10),(9,0x13),(10,0x11),(21,0x18)]:emit(f'3a{0x80+i:02x}c0dd77{a:02x}')
 emit('3a9dc0dd7703dd360c02dd361d00dd360500cd4350')
 label('ready');store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','saveptr');emit('2100803a08c03c3208c0')
 label('saveptr');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*32<=0x18000,len(ROWS)
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732130c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x5806,0),(0x585a,1),(0x4859,2),(0xa34b,3)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 folder=ROOT/'validation/dungeon-thief';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/dungeon_thief_cases.inc').write_text('static const u8 dungeon_thief_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/dungeon-thief-harness'
 for n in ['main.c','actors.c']:assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900])+bytes([r[0x301],r[0x304],r[0x30b],r[0x318],r[0xdd],r[0x1e08]])+bytes(r[0x310:0x314]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original dungeon-thief cases captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  def data(n,size):return bytes(r[(sy[n]+i)^1] for i in range(size))
  def w(n):return int.from_bytes(data(n,2),'big')
  if w('harness_done'):done.append(f)
  if not w('harness_ready'):return
  case=w('harness_case')
  if case in checked:return
  actual=data('world_actor_state',768)+bytes(w('harness_'+n) for n in ['state','counter','anim','hp','gold','sound'])+w('harness_y').to_bytes(2,'little')+w('harness_x').to_bytes(2,'little')
  assert actual==expected[case],(case,ROWS[case],[(j,x,y) for j,(x,y) in enumerate(zip(expected[case],actual)) if x!=y][:24])
  checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS),(len(checked),len(ROWS))
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_and_hero_state_counter_animation_hp_gold_xy_sound_request_exact=True,full_game_ported=False,limits=['Four sourceLD A,R sites use explicit register-preserving input shim. Original5043/A302/984F/57F8/4859/48F3/4A15 and gold/escape side effects execute.','Seven even states; spawn terrain, pursuit, strict9-pixel capture/exclusion for grabbed hero, attachment with HP0/live and hero movement counter, all gold/steal/escape boundaries, directional vs non-directional input and clock-bit1 sway. State0 requires loader animation0.','Original RNG/global clock, natural rooms/gameplay, complete video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_thief_allocation_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native dungeon-thief cases exact')
if __name__=='__main__':main()
