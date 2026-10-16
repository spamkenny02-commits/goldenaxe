"""Observe global M1 and logical R at original foreground load checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/history-refresh-v0183-r1';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/wait-refresh-v0183/z80-wait-refresh.txt').read_text()
 anchor=' && pc!=0x24bf) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x24bf && pc!=0x24c5 && pc!=0x1780 && pc!=0x1c40 && pc!=0x4e1 && pc!=0x4f7 && pc!=0x4fd) return;')
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned char gaw_history_context[32768][277];\n__declspec(dllexport) const unsigned char *gaw_history_context_events(void) { return (const unsigned char *)gaw_history_context; }')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_history_context[gaw_fore_phase_count][274]=A;gaw_history_context[gaw_fore_phase_count][275]=L;gaw_history_context[gaw_fore_phase_count][276]=H;memcpy(gaw_history_context[gaw_fore_phase_count],work_ram+0xb9,2);memcpy(gaw_history_context[gaw_fore_phase_count]+2,work_ram+0x1cf0,16);memcpy(gaw_history_context[gaw_fore_phase_count]+18,work_ram+0x200,256);'+anchor)
 modified=source.encode();target=folder/'z80-history-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_historyrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/history-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics load M1/R observer built; original core source restored.')
if __name__=='__main__':main()
