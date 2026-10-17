"""Freeze batching proofs and CPU profile without replacing previous archives."""
import hashlib,json
from actor_reference import ROOT
from validate_native_room_finish import MODULES

def main():
 folder=ROOT/'analysis/native-clock-batching-v0198';paths=set()
 for name in MODULES:
  for suffix in ['.c','.h']:
   p=ROOT/'megadrive/src'/(name+suffix)
   if p.exists():paths.add(p.relative_to(ROOT).as_posix())
 for name in ['validate_clock_repeat_fast','validate_clock_repeat_fast_68k','validate_pattern_clock_batch','validate_ram_clock_batch','profile_native_loading_budget','validate_native_room_finish','validate_native_room_finish_68k','validate_native_hud_values','archive_native_clock_batching']:paths.add('tools/'+name+'.py')
 for name in ['clock_repeat_fast_report.json','clock_repeat_fast_68k_report.json','pattern_clock_batch_report.json','ram_clock_batch_report.json','native_loading_budget_report.json','native_room_finish_report.json','native_room_finish_68k_report.json','native_hud_values_report.json','native_clock_batching_milestone.md']:paths.add('analysis/'+name)
 for name in ['baseline-budget-counted.json','baseline-room-finish-68k.json']:paths.add('validation/native-clock-batching/'+name)
 for base in ['clock-repeat-fast','pattern-clock-batch','ram-clock-batch','native-room-finish']:
  for name in ['cases.json','wrapper.c','reference.c','fast.c','scalar.c']:
   path=f'validation/{base}/{name}'
   if (ROOT/path).exists():paths.add(path)
 for base in ['clock-repeat-fast-68k','native-loading-budget','native-room-finish/kernel']:
  for name in ['src/main.c','src/wrapper.c','src/expected.h','out/release/rom.bin','out/release/symbol.txt','build.log']:
   path=f'validation/{base}/{name}'
   if (ROOT/path).exists():paths.add(path)
 manifest=[]
 for name in sorted(paths):
  raw=(ROOT/name).read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
  else:target.write_bytes(raw)
  manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 target=folder/'manifest.json';raw=(json.dumps(manifest,indent=2)+'\n').encode()
 if target.exists():assert target.read_bytes()==raw
 else:target.write_bytes(raw)
 print('Archived',len(manifest),'files; generated headers and kernel binaries retained locally.')

if __name__=='__main__':main()
