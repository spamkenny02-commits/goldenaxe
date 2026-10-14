"""Read-only source/native audio command ordering on current paid-exit loader."""
import hashlib,json
from actor_reference import ROOT
from profile_paid_passage_loader_phases import main as profile

def main():
 output='paid-exit-music-baseline-v0177'
 profile(0x6d,0,output,'genesis_plus_gx_hero_libretro.dll',capture_music=True)
 rows=[]
 for region in ['auto','pal']:
  path=ROOT/f'validation/{output}/{region}-profiles.json';profiles=json.loads(path.read_text());sequences={}
  for tag,p in profiles.items():
   changes=[];last=None
   for f,r in p.items():
    if r['music_track']!=last:changes.append(dict(frame=int(f),command=r['music_track'],phase=r['resume_phase'],fade=r['music_fade']));last=r['music_track']
   sequences[tag]=changes
  source_commands=[r['command'] for r in sequences['sms']];native_commands=[r['command'] for r in sequences['md']]
  assert 0xb0 in source_commands and source_commands.index(0xb0)<source_commands.index(0x82)
  assert 0xb0 not in native_commands,('baseline no longer reproduces missing fade command',region,native_commands)
  native_fade=next(int(f) for f,r in profiles['md'].items() if r['resume_phase']==3)
  native_world=next(r['frame'] for r in sequences['md'] if r['command']==0x82)
  assert native_world>native_fade
  rows.append(dict(region=region,sequences=sequences,native_fade_frame=native_fade,native_world_music_frame=native_world,raw_profile_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 report=dict(diagnostic_only=True,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=rows,missing_native_B0_fade_command_reproduced=True,native_world_music_starts_after_reveal_begins=True,production_ROM_changed=False,full_game_ported=False,limits=['Actual6D->96 paid exit,empty mask,controlled door/hero/initial clock. Observes sourceC065/DE06/DE0B..0D and native music latches/reader fade bytes. No source command patch or per-choice RNG injection.','This verifies a missing/reordered native command hook,not waveform equivalence or full physical load timing. Source16D0 requestsB0;1CAF requests82 before1FA7. Native helper has neither operation at those phases;fix remains pending.'])
 (ROOT/'analysis/paid_exit_music_baseline_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PAL/NTSC baseline:missing nativeB0 and late world-music command reproduced.',flush=True)

if __name__=='__main__':main()
