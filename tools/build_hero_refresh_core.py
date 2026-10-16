"""Observe global M1 and logical R at original foreground load checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/hero-refresh-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/actor-graphics-refresh-v0183/z80-actor-graphics-refresh.txt').read_text()
 anchor=' && pc!=0x18e1) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x18e1 && pc!=0x2c63 && pc!=0x369f && pc!=0x2c8a && pc!=0x2ca6 && pc!=0x2d3e && pc!=0x24e7) return;')
 modified=source.encode();target=folder/'z80-hero-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_herorefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/hero-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics load M1/R observer built; original core source restored.')
if __name__=='__main__':main()
