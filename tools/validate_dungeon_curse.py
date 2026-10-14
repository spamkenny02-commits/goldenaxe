"""Original4FF3 cursed hunter and defense/palette state and allocation comparisons."""
import contextlib,hashlib,io,itertools,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
# type,state,timer,anim,phase,period,split20,clock21,dirA,x,y,hx,hy,roomlo,slot,
# terrain,r0..r4,hp,damage,frame,freeLo,freeHi,branch22,flash,dyLo,dyHi,dxLo,dxHi

def row(s=8,t=0,a=0,p=0,period=10,split=0,clock=0,d=1,x=128,y=80,hx=224,hy=144,room=0x14,slot=0,terrain=0,r0=1,r1=1,r2=0,r3=15,r4=15,hp=8,curse=0,frame=0,armor=1,shield=1,flags=2,dy=0,dx=0):
 return (0x53,s,t,a,p,period,split,clock,d,x,y,hx,hy,room,slot,terrain,r0,r1,r2,r3,r4,hp,curse,frame,armor,shield,0,flags,dy&255,(dy>>8)&255,dx&255,(dx>>8)&255)
ROWS=[row(s=s,t=t,a=a,d=d,flags=flags,curse=curse) for s,t,a,d,flags,curse in itertools.product(range(0,12,2),[0,1],[0,3],range(4),[2,6],[0,1,255])]
ROWS += [row(s=4,r2=r,x=x,y=y,terrain=terrain) for r,(x,y),terrain in itertools.product(range(4),[(16,24),(17,25),(128,80),(231,151),(232,152),(40,40)],[0,32,128])]
ROWS += [row(s=8,hx=hx,hy=hy,d=d,r3=r) for (hx,hy),d,r in itertools.product(itertools.product([32,128,224],[32,80,144]),range(4),[0,1,2,15])]
ROWS += [row(s=6,t=1,armor=armor,shield=shield,frame=frame,curse=curse,flags=flags) for armor,shield,frame,curse,flags in itertools.product(range(1,4),range(1,4),range(8),[0,1,255],[2,6])]
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
 field(11,0xc313);field(12,0xc311);field(13,0xc0b9);store(1,0xc0ba);field(23,0xc02f);field(22,0xc0bf);field(24,0xc0f1);field(25,0xc0f2)
 emit('3a8ec0c6103246c0');field(15,0xdc00);emit('2100dc1101dc019f00edb0')
 # Tilemap high bytes are uniformly blocked/unblocked. The routine only reads it.
 field(15,0xd600);emit('2100d61101d601ff047eedb0')
 # True parent slot: IX=C600+48*slot, independent of source actor indexC046.
 emit('3a8ec06f260029292929545d29191100c619e5dde1')
 for i,a in [(0,0),(1,1),(2,4),(3,11),(4,14),(5,13),(6,0x20),(7,0x21),(8,10),(9,0x13),(10,0x11),(21,0x18),(22,0x1d),(26,0x22),(27,3),(28,0x14),(29,0x15),(30,0x16),(31,0x17)]:emit(f'3a{0x80+i:02x}c0dd77{a:02x}')
 emit('dd360500dd360c02cdf34fcd8d2ccdf61d')
 label('ready');store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','saveptr');emit('2100803a08c03c3208c0')
 label('saveptr');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x3a00 and len(ROWS)*32<=0x18000,len(ROWS)
 image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
 image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 image[0x30:0x33]=bytes.fromhex('c3003a');handler=bytes.fromhex('e5d5210400395e23561a13722b732130c0856f7ed1e1c9');image[0x3a00:0x3a00+len(handler)]=handler
 for pos,index in [(0x5806,0),(0x585a,1),(0x4859,2),(0x9fc3,3)]:
  assert image[pos:pos+2]==b'\xed\x5f';image[pos:pos+2]=bytes([0xf7,index])
 image[0x2ca6]=0xc9 # Stop original defense routine before unrelated hero setup.
 folder=ROOT/'validation/dungeon-curse';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/dungeon_curse_cases.inc').write_text('static const u8 dungeon_curse_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'cases generated');return
 harness=ROOT.parents[1]/'work/dungeon-curse-harness'
 for n in ['main.c','actors.c']:assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else 'actors.inc')).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*5+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x600:0x900])+bytes([r[0xbf],r[0x31a],r[0x1cb6],r[0x1cb7]]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original dungeon-curse cases captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  def data(n,size):return bytes(r[(sy[n]+i)^1] for i in range(size))
  def w(n):return int.from_bytes(data(n,2),'big')
  if w('harness_done'):done.append(f)
  if not w('harness_ready'):return
  case=w('harness_case')
  if case in checked:return
  actual=data('world_actor_state',768)+bytes([w('harness_curse'),w('harness_defense'),w('harness_palette0'),w('harness_palette1')])
  assert actual==expected[case],(case,ROWS[case],[(j,x,y) for j,(x,y) in enumerate(zip(expected[case],actual)) if x!=y][:24])
  checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS),(len(checked),len(ROWS))
 report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(ROWS),all_768_actor_bytes_curse_defense_palette_exact=True,full_game_ported=False,limits=['Four sourceLD A,R sites use explicit register-preserving input shim. Original4FF3/9F81/57F8/4859/48F3/4A15 and curse wrapper execute. Original2C8D is stopped by a RET at2CA6; original1DF6 executes for palette.','Six even states; bounds/pursuit/terrain and contact, prior status0/1/255. All armor/shield1..3 and eight clock phases verify original defense and palette. State0 requires loader animation0.','Original RNG/global clock, natural rooms/gameplay, complete video/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_curse_allocation_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native dungeon-curse cases exact')
if __name__=='__main__':main()
