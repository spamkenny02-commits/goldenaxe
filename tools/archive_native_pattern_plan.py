"""Freeze ROM-derived decoded patterns,command work and planned-chain proofs."""
import hashlib,json
from actor_reference import ROOT
from validate_native_room_finish import MODULES

def main():
 folder=ROOT/'analysis/native-pattern-plan-v0198';paths=set();refs=[]
 for name in MODULES:
  for suffix in ['.c','.h']:
   p=ROOT/'megadrive/src'/(name+suffix)
   if p.exists():paths.add(p.relative_to(ROOT).as_posix())
 for name in ['validate_pattern_clock_batch','validate_pattern_windows_68k','validate_native_room_finish','validate_native_room_finish_68k','profile_native_loading_budget','archive_native_pattern_plan','generate_pattern_plan']:paths.add('tools/'+name+'.py')
 for name in ['pattern_clock_batch_report.json','native_room_finish_report.json','native_room_finish_68k_report.json','native_loading_budget_bare_report.json','native_pattern_plan_milestone.md','pattern_plan_assets_report.json','pattern_plan_phases_68k_report.json','native_planned_room_finish_report.json','native_planned_room_finish_68k_report.json','native_planned_loading_budget_report.json','native_planned_loading_budget_bare_report.json']:paths.add('analysis/'+name)
 paths.update(['build.ps1','megadrive/src/source_pattern_plan_generated.h'])
 assert (ROOT/'validation/native-planned-room-finish/cases.json').read_bytes()==(ROOT/'validation/native-room-finish/cases.json').read_bytes()
 for name in ['reference.c','fast.c','scalar.c','planned.c']:paths.add('validation/pattern-clock-batch/'+name)
 old=ROOT/'analysis/native-command-batching-v0198/validation/native-room-finish/cases.json'
 assert old.read_bytes()==(ROOT/'validation/native-room-finish/cases.json').read_bytes()
 refs.extend([old.relative_to(ROOT).as_posix(),'analysis/native-pattern-windows-v0198/analysis/native_loading_budget_bare_report.json'])
 for base in ['validation/pattern-plan-phases-68k','validation/native-planned-room-finish/kernel','validation/native-planned-loading-budget','validation/native-planned-loading-budget-bare','validation/native-loading-budget','validation/native-loading-budget-bare','validation/native-room-finish/kernel']:
  for name in ['src/main.c','src/fast.c','src/scalar.c','src/reference.c','src/wrapper.c','src/expected.h','src/profile_counters.c','out/release/rom.bin','out/release/symbol.txt','build.log']:
   path=base+'/'+name
   if (ROOT/path).exists():paths.add(path)
 manifest=[]
 for name in sorted(paths):
  raw=(ROOT/name).read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
  else:target.write_bytes(raw)
  manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 raw=(json.dumps(dict(files=manifest,external_immutable_references=[dict(file=n,sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in refs]),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==raw
 else:target.write_bytes(raw)
 print('Archived',len(manifest),'files; generated headers/kernel binaries retained locally.')

if __name__=='__main__':main()
