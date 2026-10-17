"""Compare title fades, 33 cape poses and 8 logo rows against live SMS execution."""
import contextlib,hashlib,io,json,re,sys
from PIL import Image
from run_core import ROOT,run
from extract_title import rle_planes,map_decode

def main():
 pal='--pal' in sys.argv;natural='--natural' in sys.argv
 suffix=('-pal' if pal else '')+('-natural' if natural else '')
 options={'genesis_plus_gx_region_detect':'pal'} if pal else {}
 symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 bank=(ROOT/'input/original.sms').read_bytes()[0x1c000:0x20000]
 p,_=rle_planes(bank,16,bytearray(0x4000),0,4);p,base,_=map_decode(bank,p);_,anim,_=map_decode(bank,p)
 for n in range(10):base[0x5ab+2*n]|=8
 cape=[]
 for k in range(3):
  v=bytearray(base)
  for row in range(9):v[0x3c4+row*64:0x3c4+row*64+26]=anim[0x200+k*234+row*26:0x200+k*234+(row+1)*26]
  cape.append(bytes(v))
 logo=[];v=bytearray(base)
 for row in range(8):v[row*64:(row+1)*64]=anim[row*64:(row+1)*64];logo.append(bytes(v))
 expected_maps=cape*11+[bytes(base)]+logo
 first_palette=bytes(16 if n in (0,12,13,14,16,17) else 0 for n in range(32))
 traces={};count=6900 if natural else 1000;press=[] if natural else [(200,220,0)]
 for tag in ('sms','md'):
  maps=[];colors=[]
  def append(events,f,value):
   if not events or events[-1][1]!=value:events.append((f,value))
  def ram(f,d):
   if tag=='sms':value=d[0x1ca0:0x1cc0]
   else:
    d=bytearray(d);d[::2],d[1::2]=d[1::2],d[::2]
    p=symbols['sms_palette'];value=bytes(d[p+1:p+64:2])
   append(colors,f,value)
  def vram(f,v):
   if tag=='sms':value=v[0x3900:0x3f00]
   else:
    # SGDK BG_A=$E000, 64 cells per row, 192 lines start at row 2.
    value=bytearray()
    for row in range(24):
     for col in range(32):
      p=0xe000+(row+2)*128+col*2;m=int.from_bytes(v[p:p+2],'little')
      s=((m&0x7ff)-16)&511;s|=((m>>13)&1)<<11|((m>>15)&1)<<12|((m>>12)&1)<<10|((m>>11)&1)<<9
      value.extend(s.to_bytes(2,'little'))
    value=bytes(value)
   append(maps,f,value)
  out=ROOT/f'validation/{tag}-title-cadence{suffix}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if tag=='sms' else 'gaw-megadrive.bin'),count,out,set(),press,skip_intro=False,ram_observer=ram,vram_observer=vram,core_options=options)
  start=next(i for i,x in enumerate(maps) if x[1]==cape[0]);selected=maps[start:start+len(expected_maps)]
  assert [x[1] for x in selected]==expected_maps,(tag,'title map progression')
  start=next(i for i,x in enumerate(colors) if x[1]==first_palette);selected_colors=colors[start:start+18]
  assert len(selected_colors)==18
  traces[tag]=dict(maps=selected,colors=selected_colors,out=out,all_maps=maps)
 a=traces['sms'];b=traces['md']
 assert [x[1] for x in a['colors']]==[x[1] for x in b['colors']],'Palette progression differs'
 offsets=[y[0]-x[0] for x,y in zip(a['maps'],b['maps'])];poff=[y[0]-x[0] for x,y in zip(a['colors'],b['colors'])]
 assert max(offsets)-min(offsets)<=1,offsets
 assert max(poff)-min(poff)<=1,poff
 for tag,t in traces.items():
  assert [t['maps'][i+1][0]-t['maps'][i][0] for i in range(32)]==[6]*32
  assert [t['maps'][i+1][0]-t['maps'][i][0] for i in range(34,41)]==[1]*7
  assert [t['colors'][i+1][0]-t['colors'][i][0] for i in list(range(8))+list(range(9,17))]==[2]*8+[6]*8,(tag,[(f,values.hex()) for f,values in t['colors']])
 # Re-run representative real video frames: all cape poses, nine warrior fade
 # steps, and eight logo rows. One following video frame exposes completed VBlank writes.
 picks=list(range(3))+list(range(34,42))
 frames={tag:{t['maps'][i][0]+1 for i in picks}|{x[0]+1 for x in t['colors'][9:]} for tag,t in traces.items()}
 for tag,t in traces.items():
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if tag=='sms' else 'gaw-megadrive.bin'),max(frames[tag]),t['out'],frames[tag],press,skip_intro=False,core_options=options)
 pairs=[(a['maps'][i][0]+1,b['maps'][i][0]+1) for i in picks]+[(x[0]+1,y[0]+1) for x,y in zip(a['colors'][9:],b['colors'][9:])]
 pixels=[]
 for x,y in pairs:
  original=Image.open(a['out']/f'frame_{x:05d}.png').convert('RGB');native=Image.open(b['out']/f'frame_{y:05d}.png').convert('RGB').crop((0,16,256,208))
  palette=set(original.getdata());mapping={c:min(palette,key=lambda p:sum((u-v)**2 for u,v in zip(c,p))) for c in set(native.getdata())}
  mismatch=sum(u!=mapping[v] for u,v in zip(original.getdata(),native.getdata()))
  pixels.append(dict(sms_frame=x,md_frame=y,normalized_pixel_mismatches=mismatch))
 assert all(x['normalized_pixel_mismatches']==0 for x in pixels),pixels
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),region='pal' if pal else 'auto',natural_boot=natural,no_ram_mutations=True,reference='Live original SMS ROM, official Genesis Plus GX',cape_poses=33,cape_pose_frames=6,initial_palette_steps=9,initial_palette_step_frames=2,warrior_palette_steps=9,warrior_palette_step_frames=6,title_rows=8,title_row_frames=1,map_start_offsets=offsets,palette_start_offsets=poff,relative_timing_exact=True,absolute_boot_timing_exact=False,pixel_checks=pixels,sms_map_frames=[x[0] for x in a['maps']],md_map_frames=[x[0] for x in b['maps']],sms_palette_frames=[x[0] for x in a['colors']],md_palette_frames=[x[0] for x in b['colors']])
 (ROOT/f'validation/title_cadence{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Title cadence verified',suffix,'cape 6, warrior fade 6, logo rows 1 frame; pixel checks',len(pixels))
if __name__=='__main__':main()
