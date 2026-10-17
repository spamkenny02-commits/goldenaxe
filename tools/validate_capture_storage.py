"""Verify optional full-state storage leaves SMS/MD captures unchanged."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 rows=[]
 for tag,rom in [('md',ROOT/'gaw-megadrive.bin'),('sms',ROOT/'input/original.sms')]:
  folders={}
  # Fresh processes avoid retained emulator RAM between game loads.
  for saved in [False,True]:
   folder=ROOT/f'validation/capture-storage-isolated-{tag}-{saved}';folders[saved]=folder
   args=[sys.executable,str(ROOT/'tools/run_core.py'),str(rom),'--frames','100','--capture','60,100','--out',str(folder)]+(['--save-states'] if saved else [])
   subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
  for f in [60,100]:
   for prefix,ext in [('frame','png'),('ram','bin'),('vram','bin'),('cram','bin'),('vdp_regs','bin')]:
    name=f'{prefix}_{f:05d}.{ext}';assert (folders[False]/name).read_bytes()==(folders[True]/name).read_bytes(),(tag,name)
  assert not list(folders[False].glob('state_*.bin'))
  states=list(folders[True].glob('state_*.bin'));assert len(states)==2
  rows.append(dict(console=tag,frames=[60,100],extracted_files_identical=10,optional_state_bytes=sum(p.stat().st_size for p in states)))
  for p in states:
   assert p.resolve().is_relative_to((ROOT/'validation').resolve());p.unlink()
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=rows,default_full_states=False,optional_states_tested=True,isolated_core_processes=True)
 (ROOT/'validation/capture_storage_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
