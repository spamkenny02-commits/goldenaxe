"""Read-only pitch returned-HL observation plus existing M1/R/unwind hooks."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-pitch-refresh-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-envelope-refresh-v0183/z80-envelope-refresh.txt').read_text();anchor='static unsigned gaw_prefix_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned gaw_pitch_hl;\n__declspec(dllexport) unsigned gaw_pitch_return_hl(void) { return gaw_pitch_hl; }')
 anchor='gaw_prefix_count++;';assert source.count(anchor)==1;modified=source.replace(anchor,'gaw_pitch_hl=HLD;'+anchor).encode();target=folder/'z80-pitch-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_pitchrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-pitch-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Pitch M1/R/HL/unwind observer built;original source restored.')
if __name__=='__main__':main()
