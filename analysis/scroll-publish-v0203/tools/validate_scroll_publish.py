"""Catch outgoing-map flashes in rendered frames at scroll completion."""
import argparse,contextlib,hashlib,io,json,re
from pathlib import Path
from PIL import Image
from run_core import run
from validate_actor_tick import PRESSES
ROOT=Path(__file__).resolve().parents[1]

def symbols(path):
 return {m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in path.read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',action='store_true');ap.add_argument('--reuse',action='store_true');args=ap.parse_args()
 rom=ROOT/('versions/v0202-f55643bb/gaw-megadrive-v0202.bin' if args.baseline else 'gaw-megadrive.bin')
 sy=symbols(ROOT/('analysis/pattern-pairs-v0202/megadrive/out/release/symbol.txt' if args.baseline else 'megadrive/out/release/symbol.txt'))
 rows=[];comparisons=[]
 for region in ['auto','pal']:
  for route,inputs in [('horizontal',PRESSES[:11]+[(3000,3100,7)]),('vertical',PRESSES[:11]+[(3000,3060,5),(3220,3360,4)])]:
   folder=ROOT/f'validation/scroll-publish-{route}-{region}{"-baseline" if args.baseline else ""}'
   states={}
   def observe(f,r):
    if f>=2700:states[f]={n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big') for n in ['game_state','room_id','transition_direction','transition_stage','transition_step']}
   if args.reuse:
    assert json.loads((folder/'capture.json').read_text())['rom_sha256']==hashlib.sha256(rom.read_bytes()).hexdigest()
    for f in range(2700,3451):observe(f,(folder/f'ram_{f:05d}.bin').read_bytes())
   else:
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3450,folder,set(range(2700,3451)),inputs,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   completions=[]
   for f,s in states.items():
    extent=32 if s['transition_direction']>=2 else 20
    if s['game_state']==10 and s['transition_step']==extent and states.get(f-1,{}).get('transition_step')==extent-1:completions.append(f)
   expected=[2,3] if route=='horizontal' else [2,1,0]
   assert [states[f]['transition_direction'] for f in completions]==expected,(region,route,completions)
   for f in completions:
    # Vertical rendering already holds the penultimate pose for one extra
    # NTSC frame. Check stability after that publication, and report the
    # hold separately instead of declaring its cadence faithful to SMS.
    start=f+(1 if states[f]['transition_direction']>=2 else 2)
    frames=list(range(start,start+3));images=[Image.open(folder/f'frame_{g:05d}.png').convert('RGB') for g in frames]
    mask=set()
    # Exclude hardware sprite rectangles in adjacent frames. Every other
    # playfield pixel, including the outgoing-map flash area, is checked.
    for g in range(f,f+5):
     v=(folder/f'vram_{g:05d}.bin').read_bytes();regs=(folder/f'vdp_regs_{g:05d}.bin').read_bytes();base=(regs[5]&127)<<9;slot=0;seen=set()
     while slot not in seen:
      seen.add(slot);p=base+slot*8;word=lambda off:int.from_bytes(v[p+off:p+off+2],'little')
      x=(word(6)&511)-128;y=(word(0)&511)-128;size=word(2);w=(((size>>10)&3)+1)*8;h=(((size>>8)&3)+1)*8
      mask.update((xx,yy) for yy in range(max(16,y-1),min(176,y+h+1)) for xx in range(max(0,x-1),min(256,x+w+1)))
      slot=size&127
      if not slot:break
    points=[(x,y) for y in range(16,176) for x in range(256) if (x,y) not in mask]
    differences=[sum(im.getpixel(p)!=images[0].getpixel(p) for p in points) for im in images[1:]]
    early=Image.open(folder/f'frame_{f+1:05d}.png').convert('RGB');previous=Image.open(folder/f'frame_{f:05d}.png').convert('RGB')
    held=all(early.getpixel(p)==previous.getpixel(p) for p in points) and any(early.getpixel(p)!=images[-1].getpixel(p) for p in points)
    rows.append(dict(region=region,route=route,direction=states[f]['transition_direction'],room=states[f]['room_id'],frames=frames,background_pixels_per_frame=len(points),different_pixels=differences,previous_pose_held_one_frame=held))
    print(region,route,rows[-1],flush=True)
   if not args.baseline:
    old=ROOT/f'validation/scroll-publish-{route}-{region}-baseline'
    old_rom=ROOT/'versions/v0202-f55643bb/gaw-megadrive-v0202.bin'
    assert json.loads((old/'capture.json').read_text())['rom_sha256']==hashlib.sha256(old_rom.read_bytes()).hexdigest()
    old_sy=symbols(ROOT/'analysis/pattern-pairs-v0202/megadrive/out/release/symbol.txt')
    changed=[];evidence=[]
    for f,s in states.items():
     raw=(old/f'ram_{f:05d}.bin').read_bytes()
     before={n:int.from_bytes(bytes(raw[(old_sy[n]+i)^1] for i in range(2)),'big') for n in s}
     assert before==s,(region,route,f,'simulation cadence changed',before,s)
     a=(old/f'frame_{f:05d}.png').read_bytes();b=(folder/f'frame_{f:05d}.png').read_bytes()
     if a!=b:
      changed.append(f);evidence.append(dict(frame=f,before_png_sha256=hashlib.sha256(a).hexdigest(),after_png_sha256=hashlib.sha256(b).hexdigest()))
    expected=([2814,3114] if route=='horizontal' else [2814]) if region=='auto' else []
    assert changed==expected,(region,route,'unexpected rendered frame changes',changed)
    comparisons.append(dict(region=region,route=route,frames=len(states),simulation_states_identical=True,changed_rendered_frames=changed,evidence=evidence))
 report=dict(md_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),baseline=args.baseline,cases=rows,passed=all(not any(r['different_pixels']) for r in rows),limits=['Natural initial exterior routes; horizontal final pose, origin reset and following frame; vertical stability after final publication. Hardware sprite rectangles excluded. Existing one-frame hold of the penultimate vertical pose in NTSC is reported separately, unchanged. No complete source timing or whole-game claim.'])
 if comparisons:report['baseline_comparisons']=comparisons
 path=ROOT/f'validation/scroll_publish{"_baseline" if args.baseline else ""}_report.json';path.write_text(json.dumps(report,indent=2)+'\n')
 if not args.baseline:assert report['passed'],report

if __name__=='__main__':main()
