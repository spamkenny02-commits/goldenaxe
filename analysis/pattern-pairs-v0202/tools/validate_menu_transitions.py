"""Verify actual black playfield frames, retained HUD and silent inventory close."""
import hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 path=ROOT/'validation/menu_transition_profile.json';d=json.loads(path.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');assert d['production_roms_unmodified'] and not d['ram_injections'];cases=[]
 for case in d['cases']:
  frames={};hashes={};hud={};resume={}
  for tag in ['sms','md']:
   folder=ROOT/f"validation/menu-transition-{case['name']}-{case['region']}-{tag}";frames[tag]=[];hashes[tag]={};hud[tag]=[]
   capture=json.loads((folder/'capture.json').read_text());assert capture['rom_sha256']==(d['source_sha256'] if tag=='sms' else d['md_sha256'])
   for f in list(range(3348,3371))+list(range(3398,3441)):
    p=folder/f'frame_{f:05}.png';im=Image.open(p).convert('RGB');dy=0 if tag=='sms' else 16
    top=im.crop((0,dy,256,dy+160));bottom=im.crop((0,dy+160,256,dy+192))
    if not any(top.tobytes()):frames[tag].append(f)
    if len(bottom.getcolors(100000))>2:hud[tag].append(f)
    hashes[tag][str(f)]=sha(p)
   rows=case['results'][tag]['rows'];assert all(r['effect_latch']==0 for r in rows if 3398<=r['frame']<=3440),(case['name'],case['region'],tag,'unexpected close sound')
   resume[tag]=next(r['frame'] for r in rows if r['frame']>3400 and r['state']==12)
  assert frames['sms']==frames['md'],(case['name'],case['region'],frames)
  assert set(frames['sms'])<=set(hud['md']),(case['name'],case['region'],'HUD blanked')
  assert resume['sms']==resume['md'],(case['name'],case['region'],resume)
  cases.append(dict(name=case['name'],region=case['region'],blank_frames_exact=frames['sms'],entry_blank_frames=sum(f<3400 for f in frames['sms']),exit_blank_frames=sum(f>=3400 for f in frames['sms']),gameplay_resume_frame=resume['sms'],hud_retained_during_blank=True,close_sound_latches_both_zero=True,capture_png_hashes=hashes))
 assert len(cases)==6
 report=dict(md_sha256=d['md_sha256'],source_sha256=d['source_sha256'],profile_sha256=sha(path),cases=cases,ram_injections=False,full_game_ported=False,limits=['Natural initial exterior and two village shops, PAL and NTSC.','Actual top160 pixel black windows and gameplay-resume frame match; bottom32 pixel HUD stays visible. Complete transition framebuffer, incremental pattern uploads and global clock are not claimed exact.','Resource work plus approximate room/HUD reserve scales the wait by graphics class; all ownership combinations, other houses and dungeon menus remain unverified.'])
 (ROOT/'validation/menu_transition_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Six natural menu routes: black windows, retained HUD, silent closure and gameplay resume verified.')
if __name__=='__main__':main()
