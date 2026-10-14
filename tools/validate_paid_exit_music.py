"""Actual paid-exit B0 fade/world-music ordering and native fade dispatch."""
import hashlib,json
from actor_reference import ROOT
from profile_paid_passage_loader_phases import main as profile

def main():
 rows=[];routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
 for town,target,*_ in routes:
  for mask in [0,255]:
   output=f'paid-exit-music/{town:02x}-{mask:02x}'
   profile(town,mask,output,'genesis_plus_gx_hero_libretro.dll',capture_music=True)
   for region in ['auto','pal']:
    folder=ROOT/'validation'/output;path=folder/f'{region}-profiles.json';p=json.loads(path.read_text());changes={}
    later_changes={};transition_end={}
    for tag,frames in p.items():
     sequence=[];previous=None
     for f,r in frames.items():
      if r['music_track']!=previous:sequence.append(dict(frame=int(f),command=r['music_track']));previous=r['music_track']
     # Combat after the first exit can knock the hero through a house door.
     # Bound this assertion by actual destination idle, retaining later commands.
     initialized=next(int(f) for f,r in frames.items() if r['room']==target and r['hero'][0]==0)
     end=next(int(f) for f,r in frames.items() if int(f)>initialized and r['room']==target and r['hero'][0]==1 and (tag=='sms' or r['resume_phase']==0))
     transition_end[tag]=end
     later_changes[tag]=[v for v in sequence if v['frame']>end]
     sequence=[v for v in sequence if v['frame']<=end]
     assert [v['command'] for v in sequence]==[0x87,0xb0,0x82],(town,mask,region,tag,sequence)
     b0,world=sequence[1]['frame'],sequence[2]['frame']
     assert any(int(f)>=b0 and int(f)<world and bytes.fromhex(r['music_fade'])[0]==12 for f,r in frames.items()),(town,mask,region,tag,'B0 not dispatched')
     changes[tag]=sequence
    events=json.loads((folder/f'{region}-cycle-events.json').read_text())
    source_reveal=next(e[0] for e in events if e[1]==0x1fa7 and e[4]==target)
    native_fade=next(int(f) for f,r in p['md'].items() if r['resume_phase']==3)
    assert changes['sms'][2]['frame']<=source_reveal
    assert changes['md'][2]['frame']<=native_fade
    rows.append(dict(town=town,target=target,mask=mask,region=region,command_sequences=changes,first_destination_idle_frame=transition_end,later_uncontrolled_music_commands=later_changes,source_reveal_frame=source_reveal,native_fade_frame=native_fade,fade_command_dispatched_both=True,world_music_before_reveal_both=True,raw_profiles_path=str(path.relative_to(ROOT)),raw_profiles_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   print('Paid-exit music hooks exact',hex(town),hex(target),mask,flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=rows,full_game_ported=False,limits=[
  'Actual unpatched source/native paid exits,six routes,empty/full destination masks,PAL/NTSC. Door/hero/initial clock/pre-entry masks controlled;no audio request,state or per-choice RNG injected. Observes sourceC065/DE06/DE0B..0D and native latches/reader fade fields.',
  '87->B0->82 order,B0 reader dispatch and world-music request before reveal compare on24 paths. Native loader/physical duration differs,so command timestamps and complete PSG waveforms are not asserted equal.',
  'Ordering assertion stops at first destination idle;later uncontrolled combat/door re-entry commands are retained separately. Other door/loading callers,source audio IRQ cost/phase,full natural progression and whole faithful port remain unproved.'])
 (ROOT/'validation/paid_exit_music_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
