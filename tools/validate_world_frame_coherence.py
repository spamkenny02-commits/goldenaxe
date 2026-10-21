"""Independent MD VRAM/CRAM composition checks sprite publication coherence."""
import contextlib,io,json
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from validate_sprite_scene_timed import sha

def render(vram,cram,regs):
 v=bytes(vram[n^1] for n in range(65536));word=lambda a:int.from_bytes(v[a:a+2],'big');colors=[]
 for n in range(64):
  c=int.from_bytes(cram[n*2:n*2+2],'little');r=(c&7)*2;g=((c>>3)&7)*2;b=((c>>6)&7)*2;rgb565=r<<12|(r>>3)<<11|g<<7|(g>>2)<<5|b<<1|b>>3
  colors.append((((rgb565>>11)&31)*255//31,((rgb565>>5)&63)*255//63,(rgb565&31)*255//31))
 width=[32,64,32,128][regs[16]&3];height=[32,64,32,128][(regs[16]>>4)&3];bases=[(regs[2]&56)<<10,(regs[4]&7)<<13];hs=(regs[13]&63)<<10;mode=regs[11]&3;assert not regs[11]&4
 def plane(which,x,y):
  line=y if mode==3 else y&~7 if mode==2 else 0;sx=(x-(word(hs+line*4+which*2)&1023))%(width*8);sy=y%(height*8);a=word(bases[which]+((sy//8)*width+sx//8)*2);row=sy%8;col=sx%8
  if a&4096:row=7-row
  if a&2048:col=7-col
  data=word((a&2047)*32+row*4+(col//4)*2);pixel=(data>>((3-col%4)*4))&15
  return (pixel+((a>>13)&3)*16,a>>15) if pixel else (0,0)
 base=(regs[5]&127)<<9;entries=[];index=0;seen=set()
 while index not in seen:
  seen.add(index);e=[word(base+index*8+off) for off in [0,2,4,6]];entries.append(e);index=e[1]&127
  if not index:break
 out=Image.new('RGB',(256,224));pixels=[]
 for y in range(224):
  sprites=[]
  for e in entries:
   top=(e[0]&511)-128;h=(((e[1]>>8)&3)+1)*8
   if top<=y<top+h:sprites.append((e,y-top))
  sprites=sprites[:16];line=[(0,0)]*256
  for e,row in reversed(sprites):
   w=(((e[1]>>10)&3)+1)*8;h=(((e[1]>>8)&3)+1)*8;left=(e[3]&511)-128;a=e[2]
   for col in range(w):
    x=left+col
    if not 0<=x<256:continue
    rr=h-1-row if a&4096 else row;cc=w-1-col if a&2048 else col;tile=((a&2047)+(cc//8)*(h//8)+rr//8)&2047;data=word(tile*32+(rr%8)*4+((cc%8)//4)*2);color=(data>>((3-cc%4)*4))&15
    if color:line[x]=(color+((a>>13)&3)*16,a>>15)
  for x in range(256):
   a,ap=plane(0,x,y);b,bp=plane(1,x,y);s,sp=line[x];bg,bgpri=(a,ap) if a and (ap or not bp) else (b,bp)
   if s and (sp or not bgpri):color=s
   else:color=bg or regs[7]&63
   pixels.append(colors[color])
 out.putdata(pixels);return out

def main():
 folder=ROOT/'validation/world-frame-coherence-v0218';folder.mkdir(exist_ok=True);rom=ROOT/'gaw-megadrive.bin';results=[];sy=symbols(ROOT/'megadrive/out/release/symbol.txt')
 for region in ['auto','pal']:
  captures={3000,3118,3119,3120,3121,3122}
  with contextlib.redirect_stdout(io.StringIO()):run(rom,3123,folder/region,captures,PRESSES,core_options={'genesis_plus_gx_region_detect':region})
  for f in sorted(captures):
   d=folder/region;expected=render((d/f'vram_{f:05d}.bin').read_bytes(),(d/f'cram_{f:05d}.bin').read_bytes(),(d/f'vdp_regs_{f:05d}.bin').read_bytes());actual=Image.open(d/f'frame_{f:05d}.png').convert('RGB');differences=[(x,y) for y in range(16,216) for x in range(256) if expected.getpixel((x,y))!=actual.getpixel((x,y))];expected.save(d/f'expected_{f:05d}.png')
   ram=(d/f'ram_{f:05d}.bin').read_bytes();value=lambda name:int.from_bytes(bytes(ram[(sy[name]+i)^1] for i in range(2)),'big');assert value('sound_unhandled_command')==0 and value('world_tile_job_count')<=68
   result=dict(audio_unhandled_command=value('sound_unhandled_command'),queued_tile_jobs=value('world_tile_job_count'),region=region,frame=f,differing_pixels=len(differences),first_differences=differences[:12]);results.append(result);print(result,flush=True)
 report=dict(md_sha256=sha(rom.read_bytes()),cases=results,passed=not any(r['differing_pixels'] for r in results),scope='Independent snapshot VRAM/CRAM composition of51200 viewport/HUD pixels at six natural gameplay frames per region. Includes planes, tile flips/priority, sprite Y limit/linking, palettes and hscroll. Column Vscroll and shadow/highlight excluded by configured game mode. Not full-game/source cadence proof.')
 (ROOT/'analysis/world_frame_coherence_v0218_report.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],results
if __name__=='__main__':main()
