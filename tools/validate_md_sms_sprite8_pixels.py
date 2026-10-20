"""Compare physical MD RGB viewport against the independent SMS sprite-layer oracle."""
import gzip,hashlib,json
from pathlib import Path
from PIL import Image
from md_sms_sprite8_fixture import inputs
from validate_sms_sprite8 import source_plane
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-sprite8-real-rgb','class0-sprite8-overflow','class0-sprite8-wrap','class0-sprite8-empty','class0-sprite8-capacity','class0-sprite8-source-proof']
def sha(b):return hashlib.sha256(b).hexdigest()

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/md-sms-sprite8-v0203';manifest=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
 if name in manifest['files']:
  b=(archive/name).read_bytes();assert sha(b)==manifest['files'][name];return b
 item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==item['raw_sha256'] and len(b)==item['raw_bytes'];return b
def main():
 baseline=json.loads((ROOT/'analysis/md_z80_psg_class0_refresh_native_prep_report.json').read_bytes());calibration=json.loads((ROOT/'analysis/md_sprite8_palette_report.json').read_bytes());rows=[]
 for variant in VARIANTS:
  r=json.loads((ROOT/('analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json')).read_bytes());case=r['scene_sprite8_case'];sat,patterns,reg=inputs(case);plane,overflow,count=source_plane(sat,patterns,reg[0],reg[2])
  for rr in r['results']:
   region=rr['region'];old=next(x for x in baseline['results'] if x['region']==region)
   old_image=ROOT/('validation/md-z80-psg-class0-refresh-native-prep/'+region+'-plain')/f"frame_{old['frame']:05d}.png";assert sha(old_image.read_bytes())==old['video']['image_sha256']
   folder=ROOT/('validation/md-z80-psg-'+variant+'/'+region+'-plain');path=folder/f"frame_{rr['frame']:05d}.png";assert sha(path.read_bytes())==rr['video']['image_sha256']
   actual=Image.open(path).convert('RGB');expected=Image.open(old_image).convert('RGB');assert actual.size==expected.size==(256,224)
   raw=read(folder/f"vram_{rr['frame']:05d}.bin");assert sha(raw)==rr['video']['vram_sha256'];v=bytes(raw[n^1] for n in range(65536));regs=read(folder/f"vdp_regs_{rr['frame']:05d}.bin");assert sha(regs)==rr['video']['registers_sha256'];bg=(regs[2]&0x38)<<10
   calibrated=next(x for x in calibration['results'] if x['region']==region)
   cram=read(folder/f"cram_{rr['frame']:05d}.bin");assert sha(cram)==rr['video']['cram_sha256'];assert [int.from_bytes(cram[n*2:n*2+2],'little') for n in range(16,32)]==calibrated['palette_packed']
   colors=[tuple(color) for color in calibrated['colors']]
   painted=0;priority_hidden=0
   for y in range(192):
    for x in range(256):
     color=plane[y*256+x]
     if not color:continue
     address=bg+((y//8+2)*64+x//8)*2;attr=int.from_bytes(v[address:address+2],'big');xx=x&7;yy=y&7
     if attr&0x800:xx=7-xx
     if attr&0x1000:yy=7-yy
     tile=attr&2047;pixel=(int.from_bytes(v[tile*32+yy*4:tile*32+yy*4+4],'big')>>((7-xx)*4))&15
     if attr&0x8000 and pixel:priority_hidden+=1;continue
     expected.putpixel((x,y+16),colors[color]);painted+=1
   # The prototype legend is outside the compared viewport; color calibration is independent.
   a=actual.crop((0,0,256,216));b=expected.crop((0,0,256,216))
   differences=sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
   b.save(folder/'sprite8-expected.png');a.save(folder/'sprite8-actual.png')
   assert not differences,(variant,region,differences)
   if case==4:assert count==64 and overflow and priority_hidden>0
   rows.append(dict(variant=variant,region=region,case=case,sprites=count,overflow=overflow,compared_pixels=256*216,differences=differences,painted_sprite_pixels=painted,priority_hidden_pixels=priority_hidden,actual_image_sha256=sha(path.read_bytes()),expected_viewport_sha256=sha(b.tobytes()),input_sprite_plane_sha256=sha(plane)))
   print(variant,region,painted,priority_hidden,'zero RGB differences')
 report=dict(results=rows,limits=['Physical MD image matches an independent planar SMS sprite oracle composited over a separately verified native class0 background, including background priority. Actual PAL1 colors come from an independently verified calibration ROM with exactly matching CRAM colors. The prototype legend outside the compared viewport is excluded; its generator has been corrected for future kernels. Inputs are renderer fixtures from one source SAT/pattern snapshot or deliberate derivatives, not native actor production or a full-game screenshot equivalence claim. Empty input overwrites a deliberately seeded old64entry SAT.'])
 (ROOT/'analysis/md_sms_sprite8_pixel_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
