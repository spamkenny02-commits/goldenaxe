"""Observe global M1 and logical R at original foreground load checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/loader-tail-refresh-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/loader-hero-refresh-v0183/z80-loader-hero-refresh.txt').read_text()
 anchor=' && pc!=0x24e7) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x24e7 && pc!=0x5b20 && pc!=0x1caf && pc!=0x1cf8 && pc!=0x24ed) return;')
 anchor='if(pc==0x16d0 && gaw_loader_entry_count<128)';assert source.count(anchor)==1;source=source.replace(anchor,'if((pc==0x16d0 || pc==0xace) && gaw_loader_entry_count<128)')
 modified=source.encode();target=folder/'z80-loader-tail-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_loadertailrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/loader-tail-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics load M1/R observer built; original core source restored.')
if __name__=='__main__':main()
