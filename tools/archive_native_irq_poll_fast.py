"""Preserve direct V-counter wait proofs and both CPU profiles."""
import hashlib,json
from actor_reference import ROOT
from validate_native_room_finish import MODULES

def main():
 folder=ROOT/'analysis/native-irq-poll-fast-v0198';paths=set();refs=[]
 for name in MODULES:
  for suffix in ['.c','.h']:
   path=ROOT/'megadrive/src'/(name+suffix)
   if not path.exists():continue
   if name in ['source_irq','source_irq_context','source_clock']:paths.add(path.relative_to(ROOT).as_posix())
   else:
    old=ROOT/'analysis/native-command-batching-v0198'/path.relative_to(ROOT)
    assert path.read_bytes()==old.read_bytes(),path
    refs.append(old.relative_to(ROOT).as_posix())
 for name in ['validate_irq_poll_fast','validate_native_source_irq','validate_native_source_irq_68k','validate_native_source_irq_boundaries','validate_native_irq_context_boundaries','profile_native_loading_budget','validate_native_room_finish','validate_native_room_finish_68k','archive_native_irq_poll_fast']:paths.add('tools/'+name+'.py')
 for name in ['irq_poll_fast_report.json','native_source_irq_report.json','native_source_irq_68k_report.json','native_source_irq_boundaries_report.json','native_irq_context_boundaries_report.json','native_room_finish_report.json','native_room_finish_68k_report.json','native_loading_budget_report.json','native_loading_budget_bare_report.json','native_irq_poll_fast_milestone.md']:paths.add('analysis/'+name)
 for name in ['cases.json','extension-cases.json']:
  old=ROOT/'analysis/native-source-irq-v0194/validation/native-source-irq'/name
  assert old.read_bytes()==(ROOT/'validation/native-source-irq'/name).read_bytes()
  refs.append(old.relative_to(ROOT).as_posix())
 refs.append('analysis/native-command-batching-v0198/megadrive/src/source_irq.c')
 refs.append('analysis/native-command-batching-v0198/analysis/native_loading_budget_report.json')
 for base in ['validation/irq-poll-fast','validation/native-loading-budget','validation/native-loading-budget-bare','validation/native-room-finish/kernel',*['validation/native-source-irq-68k/part-'+str(n) for n in range(9)]]:
  for name in ['reference.c','wrapper.c','src/main.c','src/wrapper.c','src/expected.h','src/profile_counters.c','out/release/rom.bin','out/release/symbol.txt','build.log']:
   path=base+'/'+name
   if (ROOT/path).exists():paths.add(path)
 manifest=[]
 for name in sorted(paths):
  raw=(ROOT/name).read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
  else:target.write_bytes(raw)
  manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 references=[dict(file=name,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()) for name in sorted(refs)]
 raw=(json.dumps(dict(files=manifest,external_immutable_references=references),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==raw
 else:target.write_bytes(raw)
 print('Archived',len(manifest),'files and',len(references),'verified immutable references; generated headers/kernel binaries retained locally.')

if __name__=='__main__':main()
