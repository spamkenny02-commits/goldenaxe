"""Read-only checkpoints before world graphics and after pattern decoding."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/graphics-prefix-phase-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/reveal-phase-research-v0183/z80-reveal-phase.txt').read_text()
 anchor='if(pc!=0x1fa7 && pc!=0x0aa4 && pc!=0x0bb3 && pc!=0x0ac0 && pc!=0x0ace) return;'
 assert source.count(anchor)==1
 modified=source.replace(anchor,anchor.replace(') return;',' && pc!=0x16d0 && pc!=0x1706) return;')).encode()
 target=folder/'z80-graphics-prefix-phase.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_graphicsprefixphase_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/graphics-prefix-phase-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics prefix observer built; original core source restored.')
if __name__=='__main__':main()
