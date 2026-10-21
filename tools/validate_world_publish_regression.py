"""World IRQ publication: transition cadence and final-map stability."""
import contextlib,io,json
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_end import prior_symbols,entries
from validate_playable_sprite_limit import symbols
from validate_sprite_scene_timed import sha

def main():
 folder=ROOT/'validation/world-publish-regression-v0218';folder.mkdir(exist_ok=True);new=ROOT/'gaw-megadrive.bin';old=ROOT/'versions/v0210-4678a4f4/gaw-megadrive-v0210.bin';old_symbols=prior_symbols();results=[]
 fields=['game_state','room_id','transition_direction','transition_stage','transition_step','hero_x','hero_y']
 for region in ['auto','pal']:
  for route,presses in [('horizontal',PRESSES[:11]+[(3000,3100,7)]),('vertical',PRESSES[:11]+[(3000,3060,5),(3220,3360,4)])]:
   states={};completions={};folders={}
   for tag,rom,syfile in [('old',old,old_symbols),('new',new,ROOT/'megadrive/out/release/symbol.txt')]:
    sy=symbols(syfile);data={};done=[];captures=set();d=folder/(region+'-'+route+'-'+tag);folders[tag]=d
    def ram(f,r):
     if f<2700:return
     s={n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big') for n in fields};data[f]=s;extent=32 if s['transition_direction']>=2 else 20
     if s['game_state']==10 and s['transition_step']==extent-1:captures.update(range(f+1,f+7))
     if s['game_state']==10 and s['transition_step']==extent and data.get(f-1,{}).get('transition_step')==extent-1:done.append(f)
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3450,d,captures,presses,ram_observer=ram,core_options={'genesis_plus_gx_region_detect':region})
    states[tag]=data;completions[tag]=done;(d/'states.json').write_text(json.dumps(data)+'\n')
   core=['game_state','room_id','transition_direction','transition_step']
   unchanged_core=sum(all(s[n]==states['old'][f][n] for n in core) for f,s in states['new'].items())
   if route=='horizontal':assert unchanged_core==len(states['new']),(region,route,'horizontal cadence changed')
   source={}
   def sms_ram(f,r):
    if f>=2700:source[f]=dict(game_state=r[0x1d],room_id=int.from_bytes(r[0xb9:0xbb],'little'),hero_x=int.from_bytes(r[0x312:0x314],'little'),hero_y=int.from_bytes(r[0x310:0x312],'little'))
   sms_dir=folder/(region+'-'+route+'-sms')
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3450,sms_dir,set(),[(200,220,0)]+presses,ram_observer=sms_ram,core_options={'genesis_plus_gx_region_detect':region})
   (sms_dir/'states.json').write_text(json.dumps(source)+'\n')
   source_scores={}
   for tag in ['old','new']:
    source_scores[tag]={n:sum(s[n]!=states[tag][f][n] for f,s in source.items()) for n in ['game_state','room_id','hero_x','hero_y']}

   assert len(completions['old'])==len(completions['new']);expected=[2,3] if route=='horizontal' else [2,1,0];assert [states['new'][f]['transition_direction'] for f in completions['new']]==expected
   checks=[]
   for old_completion,f in zip(completions['old'],completions['new']):
    mask=set()
    for tag in ['old','new']:
     anchor=f if tag=='new' else old_completion
     for g in range(anchor,anchor+5):
      for e in entries((folders[tag]/f'vram_{g:05d}.bin').read_bytes()):
       y=(int.from_bytes(e[:2],'big')&511)-128;x=(int.from_bytes(e[6:8],'big')&511)-128;shape=int.from_bytes(e[2:4],'big');w=(((shape>>10)&3)+1)*8;h=(((shape>>8)&3)+1)*8
       mask.update((xx,yy) for yy in range(max(16,y-1),min(176,y+h+1)) for xx in range(max(0,x-1),min(256,x+w+1)))
    points=[(x,y) for y in range(16,176) for x in range(256) if (x,y) not in mask];images=[Image.open(folders['new']/f'frame_{g:05d}.png').convert('RGB') for g in range(f+1,f+4)];differences=[sum(im.getpixel(p)!=images[0].getpixel(p) for p in points) for im in images[1:]]
    assert not any(differences),(region,route,f,'postscroll background instability',differences)
    oldframes=[Image.open(folders['old']/f'frame_{g:05d}.png').convert('RGB') for g in range(old_completion,old_completion+3)]
    held=all(oldframes[1].getpixel(p)==oldframes[0].getpixel(p) for p in points) and any(oldframes[1].getpixel(p)!=oldframes[2].getpixel(p) for p in points)
    checks.append(dict(frame=f,old_completion_frame=old_completion,direction=states['new'][f]['transition_direction'],background_pixels=len(points),post_completion_differences=differences,old_penultimate_pose_held=held,new_final_map_stable_from_first_post_completion_frame=True))
   cadence=[]
   if route=='vertical':
    original=json.loads((ROOT/'analysis/source_scroll_cadence_report.json').read_bytes());source_groups=next(r['scrolls'] for r in original['results'] if r['region']==region)
    for group in source_groups:
     direction=group['direction'];native=[];previous=0
     for frame,state in states['new'].items():
      if state['game_state']==10 and state['transition_direction']==direction and state['transition_step']!=previous:
       if state['transition_step']:native.append(dict(step=state['transition_step'],prepared_frame=frame))
       previous=state['transition_step']
     assert [r['step'] for r in native]==list(range(1,21)),(region,direction,native)
     intervals=[b['prepared_frame']-a['prepared_frame'] for a,b in zip(native,native[1:])];assert intervals==group['frame_intervals'],(region,direction,'source scroll cadence',intervals,group['frame_intervals'])
     offsets=[n['prepared_frame']+1-s['frame'] for n,s in zip(native,group['steps'])];assert len(set(offsets))==1,(region,direction,offsets)
     cadence.append(dict(direction=direction,source_intervals=group['frame_intervals'],native_intervals=intervals,native_publication_minus_source_completion_frames=offsets[0]))
   results.append(dict(region=region,route=route,scroll_state_frames_identical=unchanged_core,source_scroll_cadence=cadence,source_mismatched_frames=source_scores,transitions=checks));print(results[-1],flush=True)
 (ROOT/'analysis/world_publish_regression_v0218_report.json').write_text(json.dumps(dict(md_sha256=sha(new.read_bytes()),reference_sha256=sha(old.read_bytes()),cases=results,passed=True,scope='Natural exterior horizontal/vertical routes. Room/state/direction/step cadence compares on3004 frames. Exact source hero timing is not established; regional source mismatch counts are retained, not hidden. Source vertical20-step cadence matches every interval; remaining absolute offsets are recorded. Ten final map transitions stable from first following frame, excluding union of hardware sprite rectangles. Not all rooms or full source timing.'),indent=2)+'\n')
if __name__=='__main__':main()
