"""Measure actual background frames against SMS before/after audio optimization."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def sprite_mask(folder,f,sms):
 v=(folder/f'vram_{f:05d}.bin').read_bytes();regs=(folder/f'vdp_regs_{f:05d}.bin').read_bytes();rect=[]
 if sms:
  base=(regs[5]&126)<<7
  for n in range(64):
   y=v[base+n]
   if y==208:break
   y=(y+1)&255
   if y>=224:y-=256
   x=v[base+128+n*2]-(8 if regs[0]&8 else 0);rect.append((x,y,8,16 if regs[1]&2 else 8))
 else:
  base=(regs[5]&127)<<9;slot=0;seen=set()
  while slot not in seen:
   seen.add(slot);p=base+slot*8;w=lambda off:int.from_bytes(v[p+off:p+off+2],'little');size=w(2)
   rect.append(((w(6)&511)-128,(w(0)&511)-144,(((size>>10)&3)+1)*8,(((size>>8)&3)+1)*8));slot=size&127
   if not slot:break
 return {(xx,yy) for x,y,w,h in rect for yy in range(max(0,y-1),min(160,y+h+1)) for xx in range(max(0,x-1),min(256,x+w+1))}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--rom',type=Path,default=ROOT/'gaw-megadrive.bin');args=parser.parse_args()
 md_sha=hashlib.sha256(args.rom.read_bytes()).hexdigest();source_sha=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest()
 rows=[]
 for reg in ['auto','pal']:
  source=ROOT/f'validation/vertical-cadence-source-{reg}';before=ROOT/f'validation/scroll-publish-vertical-{reg}';after=ROOT/f'validation/audio-stream-vertical-{reg}'
  assert json.loads((after/'capture.json').read_text())['rom_sha256']==md_sha,'Captures belong to a different diagnostic ROM; supply --rom'
  assert json.loads((source/'capture.json').read_text())['rom_sha256']==source_sha
  for direction,frames in [('south',range(3020,3090)),('north',range(3220,3280))]:
   errors={tag:[] for tag in ['before','after']};checked=0
   for f in frames:
    a=Image.open(source/f'frame_{f:05d}.png').convert('RGB');source_mask=sprite_mask(source,f,True);palette=set(a.getdata())
    for tag,folder in [('before',before),('after',after)]:
     b=Image.open(folder/f'frame_{f:05d}.png').convert('RGB').crop((0,16,256,176));mapping={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};mask=source_mask|sprite_mask(folder,f,False)
     points=[(x,y) for y in range(160) for x in range(256) if (x,y) not in mask];count=sum(a.getpixel(p)!=mapping[b.getpixel(p)] for p in points)
     if tag=='after':checked+=len(points)
     if count:errors[tag].append(dict(frame=f,pixels=count))
   row=dict(region=reg,direction=direction,frames=len(frames),after_checked_background_pixels=checked,before_mismatch_frames=errors['before'],after_mismatch_frames=errors['after']);rows.append(row);print(reg,direction,'before',len(errors['before']),'after',len(errors['after']),errors['after'][:8],flush=True)
 report=dict(md_sha256=md_sha,source_sha256=source_sha,baseline_md_sha256=json.loads((ROOT/'validation/scroll-publish-vertical-auto/capture.json').read_text())['rom_sha256'],cases=rows,limits=['Natural exterior south/north routes, 256x160 playfield, hardware sprite rectangles plus one-pixel border excluded. Pixel RGBs normalized to nearest source palette. Reports remaining differences explicitly; no whole-game or complete cadence equivalence claim.'])
 (ROOT/'validation/vertical_audio_stream_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
