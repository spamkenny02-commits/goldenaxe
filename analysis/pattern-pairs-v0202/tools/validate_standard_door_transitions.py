"""Check captured standard doors; retain physical timing differences explicitly."""
import hashlib,json
from actor_reference import ROOT

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 diagnostic=json.loads((ROOT/'analysis/standard_door_music_report.json').read_text())
 assert diagnostic['md_sha256']==digest
 results=[]
 for case in diagnostic['cases']:
  folder=ROOT/f"validation/standard-door-music/{case['name']}-{case['region']}"
  profiles=json.loads((folder/'profiles.json').read_text())
  events=json.loads((folder/'source-events.json').read_text())
  phases=[]
  for frame,row in profiles['md'].items():
   if not phases or phases[-1][1]!=row['resume_phase']:phases.append((int(frame),row['resume_phase']))
  assert [p for f,p in phases]==[0,1,2,3,4,0,1,2,3,4,0],phases
  music={}
  for tag,p in profiles.items():
   sequence=[]
   for f,row in p.items():
    if not sequence or sequence[-1]!=row['track']:sequence.append(row['track'])
   music[tag]=sequence[sequence.index(0xb0):]
  assert music['sms']==music['md'] and len(music['md'])==4,music
  transitions=[]
  for index in [1,6]:
   start,load,fade,reveal,end=[phases[index+n][0] for n in range(5)]
   assert load-start==18 and reveal-fade in [18,19] and end-reveal==32
   assert all(not profiles['md'][str(f)]['display_enabled'] for f in range(load,fade))
   assert all(profiles['md'][str(f)]['display_enabled'] for f in range(fade,end))
   assert profiles['md'][str(load-1)]['resume_fade_step']==9
   assert profiles['md'][str(reveal-1)]['resume_fade_step']==9
   assert profiles['md'][str(end)]['resume_contour']==16
   source=[]
   for pc in [0xb12,0xb24,0xace,0x1fb6,0x2002]:
    samples=[e for e in events if e[1]==pc]
    assert len(samples)==2,(hex(pc),len(samples))
    source.append(samples[0 if index==1 else 1])
   source_clock=lambda a,b:(b[5]-a[5])&255
   assert source_clock(source[0],source[1])==18
   assert source_clock(source[2],source[3])==18
   assert source_clock(source[3],source[4])==32
   transitions.append(dict(native_phase_frames=[start,load,fade,reveal,end],native_fade_out_frames=load-start,native_hidden_load_frames=fade-load,native_fade_in_frames=reveal-fade,native_contour_frames=end-reveal,source_phase_observer_frames=[e[0] for e in source],source_clock_durations=[18,18,32],nine_color_steps_each_direction=True,sixteen_contours=True))
  results.append(dict(name=case['name'],region=case['region'],music_after_first_fade=music,transitions=transitions,profiles_sha256=hashlib.sha256((folder/'profiles.json').read_bytes()).hexdigest(),events_sha256=hashlib.sha256((folder/'source-events.json').read_bytes()).hexdigest()))
 report=dict(md_sha256=digest,source_sha256=diagnostic['source_sha256'],cases=results,full_game_ported=False,absolute_transition_timing_exact=False,limits=diagnostic['limits']+['Four controlled door roundtrips only. Native fade-in sampled18 or19 frames;pending VBlank affects phase boundary. Full load duration,intermediate pixels,sprite palette and waveforms are not established by this test.'])
 (ROOT/'validation/standard_door_transitions_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Four standard door roundtrips: fades,hidden loading,16 contours and music command order checked.')

if __name__=='__main__':main()
