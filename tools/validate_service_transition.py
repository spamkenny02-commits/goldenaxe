"""Check every captured portrait frame against original SMS reveal images."""
import hashlib,json
from PIL import Image
from actor_reference import ROOT

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();results=[];roi=(16,8,96,88)
 for name in ['key','feather','oil','poor','keys_full','feather_owned','oil_owned']:
  a=ROOT/f'validation/sms-merchant-{name}';b=ROOT/f'validation/md-merchant-{name}'
  assert json.loads((b/'capture.json').read_text())['rom_sha256']==digest
  colors=set(Image.open(a/'frame_03600.png').convert('RGB').getdata());reference={}
  for f in range(3340,3451):
   key=Image.open(a/f'frame_{f:05}.png').convert('RGB').crop(roi).tobytes();reference.setdefault(key,[]).append(f)
  matches=[];errors=[];states=[]
  for f in range(3340,3451):
   im=Image.open(b/f'frame_{f:05}.png').convert('RGB').crop((0,16,256,208))
   if im.getpixel((0,0))!=(0,0,0):continue # The room before its playfield is hidden.
   conversion={c:min(colors,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(im.getdata())}
   normalized=Image.new('RGB',im.size);normalized.putdata([conversion[c] for c in im.getdata()]);key=normalized.crop(roi).tobytes()
   if key not in reference:errors.append(f)
   else:
    source_frame=reference[key][0];matches.append([f,source_frame])
    if not states or states[-1]['source_first_frame']!=source_frame:states.append(dict(native_first_frame=f,source_first_frame=source_frame))
  assert not errors,(name,'corrupted/unknown portrait images',errors)
  assert len(matches)>=90 and len(states)>=9,(name,'missing reveal states',states)
  assert [x['source_first_frame'] for x in states]==sorted(x['source_first_frame'] for x in states),(name,'reveal goes backwards')
  results.append(dict(case=name,clean_portrait_frames=len(matches),portrait_roi_px=80*80,normalized_source_pixels_exact=True,ordered_states=states,unknown_or_corrupted_portrait_frames=errors))
 report=dict(md_sha256=digest,cases=results,scope='First-village merchant entry: blank area, portrait frame and all visible reveal stages. Pixel comparison normalizes SMS/MD DAC colors; settled purchases, HUD and exit are checked separately by validate_merchant.py.',full_playfield_pixel_timing_exact=False)
 (ROOT/'validation/service_transition_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Seven merchant entries: every visible portrait frame matches an original SMS state')
if __name__=='__main__':main()
