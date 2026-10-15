"""Record original pitch returnedHL and caller unwind in isolated fixtures."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-pitch-v0180';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-table-envelope-v0180/z80-envelope-unit.txt').read_text()
 anchor='static unsigned gaw_prefix_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned gaw_pitch_hl;\n__declspec(dllexport) unsigned gaw_pitch_return_hl(void) { return gaw_pitch_hl; }')
 anchor='gaw_prefix_count++;';assert source.count(anchor)==1
 modified=source.replace(anchor,'gaw_pitch_hl=HLD;'+anchor).encode();target=folder/'z80-pitch-unit.txt'
 if target.exists():assert target.read_bytes()==modified
 else:
  with target.open('xb') as f:f.write(modified)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_pitch_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-pitch-core-build.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only original pitch unit core built.')

if __name__=='__main__':main()
