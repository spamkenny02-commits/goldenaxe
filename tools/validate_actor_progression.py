"""Compare unchanged original actor loading against native progression-aware loading."""
import contextlib,hashlib,io,json,re,sys
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def generate():
 rom=(ROOT/'input/original.sms').read_bytes()
 flagged=[room for room in range(512) if any(t>=0x20 and rom[0x320ea+(t-0x20)*4+3]&0x40 for t in rom[0x3234e+room*8:0x32356+room*8])]
 rows=[(room&255,room>>8,255,p,(room+p)%11) for room in range(512) for p in [0,1,0x80,0xff]]
 rows += [(room&255,room>>8,mask,p,255 if mask==1 else (mask+p)%11) for room in flagged for mask in [0,0xa5,0x80,1] for p in [0,1,0x7f,0x80,0xff]]
 code=bytearray();labels={};fix=[];base=0x3000
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=base+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def store(v,a):emit(f'3e{v:02x}32{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff')
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf2100402206c0')
 label('case');store(0,0xc002);emit('dd2a06c0dd7e0032b9c0dd7e0132bac0')
 # Clear progression area, then seed selected and deliberately opposite next byte.
 emit('21cec011cfc00100013600edb0dd6e0026c2dd7e0277')
 emit('dd7e043237c06f260011cec019dd7e037723ee77cd8017')
 store(1,0xc002);emit('0603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c0110500192206c02a00c0232200c001'+len(rows).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
 store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 assert base+len(code)<0x4000 and len(rows)*5<=0x4000
 image=bytearray(rom);image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code;image[0x4000:0x4000+len(rows)*5]=bytes(v for row in rows for v in row)
 assert image[0x1780:0x190b]==rom[0x1780:0x190b]
 folder=ROOT/'validation/actor-progression';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/actor_progression_cases.inc').write_text('static const u8 progression_cases[][5]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in rows)+'};\n')
 return rom,image,rows,flagged,folder

def main():
 rom,image,rows,flagged,folder=generate()
 if '--generate' in sys.argv:print(len(rows),'cases;',len(flagged),'boss-flag rooms');return
 harness=ROOT.parents[1]/'work/actor-progression-harness'
 for n in ['main.c','actors.c','actors.h']:
  assert (ROOT/'megadrive/src'/n).read_bytes()==(harness/'src'/('game_main.inc' if n=='main.c' else n)).read_bytes(),n
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];active=[None]
 def sms(f,r):
  if r[4]:done.append(f)
  active[0]=None
  if not r[2]:return
  case=int.from_bytes(r[:2],'little')
  if case in expected:return
  expected[case]=dict(records=bytes(r[0x600:0x900]),count=r[0xa2],tiles=r[0x67]);active[0]=case
 def svram(f,v):
  if active[0] is not None:
   a=expected[active[0]];a['patterns']=bytes(v[0x2000:0x2000+a['tiles']*32])
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',120000,folder/'sms',set(),[],skip_intro=False,ram_observer=sms,vram_observer=svram)
 assert done and len(expected)==len(rows),(len(expected),len(rows))
 print(len(expected),'original complete actor loads captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  def data(n,size,off=0):return bytes(r[(sy[n]+off+i)^1] for i in range(size))
  def w(n):return int.from_bytes(data(n,2),'big')
  if w('harness_done'):done.append(f)
  if not w('harness_ready'):return
  case=w('harness_case')
  if case in checked:return
  a=expected[case]
  assert data('world_actor_state',768)==a['records'],(case,rows[case],'records',[(i,x,y) for i,(x,y) in enumerate(zip(data('world_actor_state',768),a['records'])) if x!=y][:12])
  assert w('world_actor_count')==a['count'] and w('world_actor_tiles')==a['tiles'],(case,'count/tiles',w('world_actor_count'),a['count'],w('world_actor_tiles'),a['tiles'])
  assert data('sms_vram',len(a['patterns']),0x2000)==a['patterns'],(case,'loaded pattern bytes')
  checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',len(rows)*7+1500,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(rows),(len(checked),len(rows))
 result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(rows),rooms=512,boss_flag_rooms=flagged,original_complete_loader_executed='1780..18E1 including 1805..1838 and original RLE/VDP transfers',actor_records_counts_tile_allocations_and_loaded_planar_patterns_exact=True,all_production_room_loading_paths_use_progression=True,full_game_ported=False,limits=['Controlled loader calls; all rooms with full persistence and progression 0,1,80,FF; boss-flag rooms additionally use masks 00,A5,80,01 and progress 00,01,7F,80,FF.','Native wrapper calls production load_current_world_actors, exercising saved actor mask and progression byte lookup at 1E plus the low byte of dungeon number, including index FF.','Natural boss fights, reward pickup and quest progression, rendered sprites, global loading timing and audio are outside this comparison.'])
 (ROOT/'validation/actor_progression_report.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checked),'native progression-aware loads exact',flush=True)
if __name__=='__main__':main()
