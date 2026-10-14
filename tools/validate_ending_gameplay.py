"""Actual final-room ending, credits state stream and normalized scene captures."""
import hashlib,json
from PIL import Image
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ticks(case):
 return {r['tick']:r for r in case['credit_trace'] if r['tick']>0}
def picture(folder,frame):return Image.open(ROOT/folder/f'frame_{frame:05d}.png').convert('RGB')
def image_difference(a,b):
 colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
 return sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()))
def main():
 source=json.loads((ROOT/'validation/ending_source_terminal_profile.json').read_text());native=json.loads((ROOT/'validation/ending_native_terminal_profile.json').read_text());assert native['md_sha256']==sha(ROOT/'gaw-megadrive.bin')
 cases=[]
 for a,b in zip(source['cases'],native['cases']):
  x,y=ticks(a),ticks(b);assert set(x)==set(y)==set(range(1,7425)),(a['region'],len(x),len(y))
  for tick in x:assert (x[tick]['state'],x[tick]['vscroll'])==(y[tick]['state'],y[tick]['vscroll']),(a['region'],tick,x[tick],y[tick])
  captures=[]
  for sa,ma in zip(a['credit_captures'],b['credit_captures']):
   assert sa['tick']==ma['tick']
   difference=image_difference(picture(a['capture_folder'],sa['frame']),picture(b['capture_folder'],ma['frame']).crop((0,16,256,208)))
   assert difference==0,(a['region'],sa,ma,difference)
   captures.append(dict(tick=sa['tick'],source_frame=sa['frame'],native_frame=ma['frame'],normalized_differing_pixels=difference))
  assert len(captures)==5 and any(c['tick']==7001 for c in captures)
  # Gem positions/visible flags/collider publication use real source0940.
  sr=(ROOT/a['capture_folder']/'ram_04200.bin').read_bytes()
  import re
  sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
  mr=(ROOT/b['capture_folder']/'ram_04200.bin').read_bytes();actors=bytes(mr[(sy['world_actor_state']+i)^1] for i in range(768));assert actors==sr[0x600:0x900],(a['region'],'actual nine-gem records',[(i,x,y) for i,(x,y) in enumerate(zip(sr[0x600:0x900],actors)) if x!=y][:12])
  gem_difference=image_difference(picture(a['capture_folder'],4200),picture(b['capture_folder'],4200).crop((0,16,256,208)))
  assert gem_difference==0,(a['region'],'gem scene image',gem_difference)
  assert a['returned_to_title']==b['returned_to_title']==19000
  for command in [0x8d,0x88]:assert next(f for f,c in a['music_requests'] if c==command)==next(f for f,c in b['music_requests'] if c==command)
  cases.append(dict(region=a['region'],credits_state_and_vscroll_steps_exact=7424,credits_images=captures,nine_gem_all_768_actor_bytes_exact=True,nine_gem_normalized_image_exact=True,music_8D_88_request_frames_exact=True,ending_entered_source=a['ending_entered'],ending_entered_native=b['ending_entered'],first_credit_tick_source=x[1]['frame'],first_credit_tick_native=y[1]['frame'],final_credit_tick_source=x[7424]['frame'],final_credit_tick_native=y[7424]['frame'],source_credit_stream_frames=x[7424]['frame']-x[1]['frame']+1,native_credit_stream_frames=y[7424]['frame']-y[1]['frame']+1,returned_after_normal_C=True))
  print(a['region'],'7424 credits states, five full normalized captures, gem records/image, music requests and return exact',flush=True)
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),cases=cases,ending_integrated=True,full_game_ported=False,limits=['Controlled actual14C entry, terminal boss-death state4 and hero-state12 checkpoint at3700; this avoids unaligned death-particle randomness. Initial native world clock is explicitly aligned to source at3700. Real final death handoff, automatic centering, gem reveal, palette erase, credits and normal C return execute in production.','Credits compare by original arithmetic tick, not absolute frame; captured source/native frames and stream lengths expose residual initialization/IRQ timing differences. Source NTSC can take one extra display frame during row work. Images normalize MD colors to source and crop its16-pixel borders.','Separate full death-state0 profile executes particles through ending/return, but original RNG causes different final-particle drain cadence. Natural final dungeon victory, all intermediate framebuffer/audio frames, exact loading/IRQ cadence and hardware remain unproved.'])
 (ROOT/'validation/ending_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
