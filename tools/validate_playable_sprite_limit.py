"""Playable ROM SMS eight-sprites-per-line overflow and natural-route regression."""
import contextlib,io,json,re
from pathlib import Path
from run_core import run,ROOT
from validate_actor_tick import PRESSES
from validate_sprite_scene_timed import sha
from validate_md_game_sprite_frame import physical_plane

def symbols(path):return {m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in path.read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
def reference(v,base,limit):
 raw=bytes(v[n^1] for n in range(65536));entries=[];index=0;seen=set()
 while index not in seen:
  seen.add(index);e=raw[base+index*8:base+index*8+8];entries.append(e);index=e[3]&127
  if not index:break
 out=bytearray(49152)
 for y in range(192):
  rows=[(e,y-((int.from_bytes(e[:2],'big')&511)-144)) for e in entries if (int.from_bytes(e[:2],'big')&511)-144<=y<(int.from_bytes(e[:2],'big')&511)-136][:limit]
  for e,row in reversed(rows):
   x=(int.from_bytes(e[6:8],'big')&511)-128;tile=int.from_bytes(e[4:6],'big')&2047;pixels=int.from_bytes(raw[tile*32+row*4:tile*32+row*4+4],'big')
   for c in range(8):
    color=(pixels>>((7-c)*4))&15
    if color and 0<=x+c<256:out[y*256+x+c]=color
 return bytes(out),[(e[:4]+e[6:8]).hex() for e in entries]
def ordered_reference(old,new,base):
 oldraw=bytearray(old[n^1] for n in range(65536));newraw=bytes(new[n^1] for n in range(65536));mapping={};index=0
 while True:
  e=oldraw[base+index*8:base+index*8+8];mapping[bytes(e[:2]+e[6:8])]=bytes(e[4:6]);index=e[3]&127
  if not index:break
 index=0
 while True:
  e=newraw[base+index*8:base+index*8+8];original=mapping[bytes(e[:2]+e[6:8])];oldraw[base+index*8:base+index*8+8]=e;oldraw[base+index*8+4:base+index*8+6]=original;index=e[3]&127
  if not index:break
 return bytes(oldraw[n^1] for n in range(65536))
def main():
 new=ROOT/'gaw-megadrive.bin';old=ROOT/'versions/v0203-7660a4b5/gaw-megadrive-v0203.bin';folder=ROOT/'validation/playable-sprite-limit-v0210';folder.mkdir(exist_ok=True);results=[]
 for region in ['auto','pal']:
  samples={}
  for tag,rom,syfile in [('old',old,ROOT/'analysis/scroll-publish-v0203/megadrive/out/release/symbol.txt'),('new',new,ROOT/'megadrive/out/release/symbol.txt')]:
   sy=symbols(syfile);states={};planes={};template=bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630]);actors=bytearray(768)
   for slot in range(12):
    e=bytearray(template);e[3]=1;e[4]=120;e[5]=0;e[6]=255;e[0x11]=64+(slot%3)*3;e[0x13]=16+slot*18;actors[slot*48:(slot+1)*48]=e
   writes=[(f,sy['world_actor_state'],bytes(actors)) for f in range(3127,3141)]
   def ram(f,r):
    if f>=3127:states[f]={name:int.from_bytes(bytes(r[(sy[name]+i)^1] for i in range(2)),'big') for name in ['game_state','room_id','hero_x','hero_y']}
   def video(f,v):
    if f>=3129:
     planes[f]=(reference(v,0xf400,8),reference(v,0xf400,16));(folder/(region+'-'+tag+'-'+str(f)+'-vram.bin')).write_bytes(v)
   captures={60,120,300,800,1000,1500,2300,2700,3000,3120,3130}
   with contextlib.redirect_stdout(io.StringIO()):run(rom,3140,folder/(region+'-'+tag),captures,PRESSES,ram_writes=writes,ram_observer=ram,vram_observer=video,core_options={'genesis_plus_gx_region_detect':region})
   samples[tag]=(states,planes)
  changed=0
  for f in range(3129,3141):
   assert samples['old'][0][f]==samples['new'][0][f],(region,f,'gameplay cadence')
   old8,old16=samples['old'][1][f];new8,new16=samples['new'][1][f]
   assert sorted(p[:4]+p[8:] for p in old8[1])==sorted(p[:4]+p[8:] for p in new16[1]),(region,f,'sprite positions')
   unmasked=ordered_reference((folder/(region+'-old-'+str(f)+'-vram.bin')).read_bytes(),(folder/(region+'-new-'+str(f)+'-vram.bin')).read_bytes(),0xf400)
   expected,_=reference(unmasked,0xf400,8);before,_=reference(unmasked,0xf400,16)
   assert expected==new16[0],(region,f,'SMS row-limit pixels');changed+=sum(a!=b for a,b in zip(before,new16[0]))
  assert changed>0,(region,'fixture did not expose overflow')
  natural=[60,120,300,800,1000,1500,2300,2700,3000,3120]
  natural_changes=[]
  for f in natural:
   if (folder/(region+'-old')/f'frame_{f:05d}.png').read_bytes()==(folder/(region+'-new')/f'frame_{f:05d}.png').read_bytes():continue
   a=(folder/(region+'-old')/f'vram_{f:05d}.bin').read_bytes();b=(folder/(region+'-new')/f'vram_{f:05d}.bin').read_bytes();expected,_=reference(ordered_reference(a,b,0xf400),0xf400,8);actual,_=reference(b,0xf400,16)
   assert expected==actual,(region,f,'natural SMS row limit')
   assert region=='pal' and f==3120,(region,f,'unexpected natural image change')
   from PIL import Image,ImageChops
   difference=ImageChops.difference(Image.open(folder/(region+'-old')/f'frame_{f:05d}.png').convert('RGB'),Image.open(folder/(region+'-new')/f'frame_{f:05d}.png').convert('RGB'))
   assert difference.getbbox()==(160,35,168,36),(region,f,'unrelated pixels changed')
   natural_changes.append(dict(frame=f,corrected_box=[160,35,168,36],physical_plane_exact=True))
  results.append(dict(region=region,overflow_frames=12,corrected_sprite_pixels=changed,natural_frames_identical=[f for f in natural if f not in [r['frame'] for r in natural_changes]],natural_sms_limit_corrections=natural_changes,simulation_states_identical=True,sprite_positions_identical=True,ordering_phase_comparison=False));print(results[-1],flush=True)
 (ROOT/'analysis/playable_sprite_limit_v0210_report.json').write_text(json.dumps(dict(md_sha256=sha(new.read_bytes()),baseline_sha256=sha(old.read_bytes()),cases=results,scope='Playable full boot/title/menu/name/game route plus controlled12-actor overlap. Physical VRAM output follows eight-entry source Y scan; transparent/offscreen entries count. Reference uses actual current sprite order with unmasked baseline tiles; ordering-phase fidelity is not established. No full-game or complete timing claim.'),indent=2)+'\n')
if __name__=='__main__':main()
