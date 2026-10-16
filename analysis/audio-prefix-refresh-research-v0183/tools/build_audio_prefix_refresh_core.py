"""Read-only cumulative M1 counter and R observations around original helper calls."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-prefix-refresh-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-prefix-v0180/z80-prefix-snapshots.txt').read_text()
 anchor='#define R Z80.r';assert source.count(anchor)==1
 source=source.replace(anchor,'static unsigned long long gaw_M1_fetches;\n'+anchor)
 assert source.count('R++;')==5;source=source.replace('R++;','R++;gaw_M1_fetches++;')
 anchor='R += (cycles / cyclesum) * opcodes;';assert source.count(anchor)==1;source=source.replace(anchor,anchor+'gaw_M1_fetches += (cycles / cyclesum) * opcodes;')
 anchor='static unsigned long long gaw_prefix_start,gaw_prefix_cost;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
static unsigned long long gaw_prefix_M1_start,gaw_prefix_M1_cost;
static unsigned gaw_prefix_R_before,gaw_prefix_R_after;
__declspec(dllexport) unsigned long long gaw_prefix_m1_fetches(void) { return gaw_prefix_M1_cost; }
__declspec(dllexport) unsigned gaw_prefix_refresh_before(void) { return gaw_prefix_R_before; }
__declspec(dllexport) unsigned gaw_prefix_refresh_after(void) { return gaw_prefix_R_after; }
''')
 anchor='gaw_prefix_start=gaw_elapsed;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'gaw_prefix_M1_start=gaw_M1_fetches;gaw_prefix_R_before=(R&127)|R2;')
 anchor='gaw_prefix_cost=(gaw_elapsed-gaw_prefix_start)/15-17;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'gaw_prefix_M1_cost=gaw_M1_fetches-gaw_prefix_M1_start-1;gaw_prefix_R_after=(R&127)|R2;')
 modified=source.encode();target=folder/'z80-audio-prefix-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_prefixrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-prefix-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Audio prefix M1/R observer built;original source restored.')
if __name__=='__main__':main()
