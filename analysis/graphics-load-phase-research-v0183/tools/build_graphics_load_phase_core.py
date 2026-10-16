"""Read-only checkpoints covering the complete ordinary class0 graphics routine."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/graphics-load-phase-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/graphics-prefix-phase-research-v0183/z80-graphics-prefix-phase.txt').read_text()
 anchor=' && pc!=0x1706) return;';assert source.count(anchor)==1
 modified=source.replace(anchor,' && pc!=0x1706 && pc!=0x170e && pc!=0x1720 && pc!=0x1733 && pc!=0x1748 && pc!=0x24b9) return;').encode()
 target=folder/'z80-graphics-load-phase.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_graphicsloadphase_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/graphics-load-phase-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Complete graphics observer built; original core source restored.')
if __name__=='__main__':main()
