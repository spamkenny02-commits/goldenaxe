"""Verify and freeze the fast clocked-audio milestone without copying old vectors."""
import hashlib,json,shutil,subprocess
from pathlib import Path
from validate_native_room_finish import MODULES
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/name).read_text())

def main():
 out=ROOT/'analysis/audio-stream-fast-v0203';assert not out.exists(),'Milestone archive is immutable'
 eq=read('validation/audio_stream_equivalence_report.json');digest=sha(ROOT/'gaw-megadrive.bin')
 assert eq['md_sha256']==digest=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
 assert not eq['production_fast_audio_wired'] and eq['source_vector_cases']==25644 and eq['mutated_cases']==3000
 for name in ['main.c','sound.inc']:
  assert (ROOT/'megadrive/src'/name).read_bytes()==subprocess.check_output(['git','show','8f8e451:megadrive/src/'+name],cwd=ROOT)
 reader=read('analysis/native_audio_fast_reader_68k_report.json');assert reader['fast'] and reader['cases']==25644
 assert sum(r['cases'] for r in reader['results'])==51288 and all(r['done'] and not r['failures'] for r in reader['results'])
 for r in [eq,reader]:
  for n,h in r['module_sha256'].items():assert sha(ROOT/'megadrive/src'/f'{n}.c')==h,n
 reports=['analysis/native_audio_fast_reader_68k_report.json','validation/audio_stream_equivalence_report.json',
  'analysis/native_planned_room_finish_report.json','analysis/native_planned_room_finish_68k_report.json',
  'analysis/native_planned_loading_budget_bare_report.json','analysis/native_planned_loading_budget_bare_precise_report.json',
  'analysis/native_planned_loading_budget_bare_precise_baseline_audio_report.json','analysis/graphics_classes_prefix_report.json',
  'analysis/graphics_classes_prefix_68k_report.json','analysis/native_audio_tone_report.json','analysis/native_audio_noise_report.json',
  'validation/cleanup_states_plan.json','validation/vertical_audio_stream_report.json','validation/vertical_publication_profile.json',
  'analysis/audio-channel-backup-baseline-v0203/vertical_publication_profile.json']
 for name in reports[2:4]:
  r=read(name);assert r['cases']==24 and not r['production_clock_wired']
  for n,h in r['helpers'].items():assert sha(ROOT/'megadrive/src'/f'{n}.c')==h,(name,n)
  if 'results' in r:assert all(x['done'] and not x['failures'] for x in r['results'])
 for suffix,flag in [('',True),('_baseline_audio',False)]:
  r=read(f'analysis/native_planned_loading_budget_bare_precise{suffix}_report.json');assert r['clock_audio_fast']==flag and r['precise_read_only_observer']
  for n,h in r['helpers'].items():assert sha(ROOT/'megadrive/src'/n)==h,n
  if flag:assert all(x['remaining_source_master']>0 for reg in r['results'] for x in reg['rows'])
 refs={}
 for n in ['cases.json','extension-cases.json']:
  old=ROOT/'analysis/native-audio-reader-v0194/validation/native-audio-reader'/n;live=ROOT/'validation/native-audio-reader'/n
  assert sha(old)==sha(live);refs[str(old.relative_to(ROOT)).replace('\\','/')]=sha(old)
 files=set(reports)|{'analysis/audio_stream_fast_milestone.md','validation/native-planned-room-finish/cases.json','validation/graphics-classes-prefix/cases.json'}
 files.update('tools/'+n for n in ['validate_audio_stream_equivalence.py','validate_native_audio_reader.py','validate_native_audio_reader_68k.py','profile_native_loading_budget.py','profile_vertical_publication.py','audit_vertical_audio_stream.py','archive_audio_stream_fast.py'])
 for n in set(MODULES)|{'main','sound','source_pattern_plan_generated'}:
  for ext in ['.c','.h','.inc']:
   if (ROOT/'megadrive/src'/(n+ext)).exists():files.add('megadrive/src/'+n+ext)
 for name in sorted(files):
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
 (out/'retained_vector_references.json').write_text(json.dumps(refs,indent=2)+'\n')
 manifest={str(p.relative_to(out)).replace('\\','/'):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
 (out/'manifest.json').write_text(json.dumps(dict(playable_sha256=digest,production_fast_audio_wired=False,files=manifest),indent=2)+'\n')
 print(len(manifest),'source/proof files frozen; old audio vectors referenced by SHA, playable ROM remains v0203.')

if __name__=='__main__':main()
