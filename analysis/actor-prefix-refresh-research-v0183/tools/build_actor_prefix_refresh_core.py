"""Observe global M1 and logical R at original foreground load checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/actor-prefix-refresh-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/history-refresh-v0183-r1/z80-history-refresh.txt').read_text()
 anchor=' && pc!=0x4fd) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x4fd && pc!=0x17ae && pc!=0x17de && pc!=0x1805 && pc!=0x1839 && pc!=0x1853) return;')
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned char gaw_actor_context[32768][769];\n__declspec(dllexport) const unsigned char *gaw_actor_load_context_events(void) { return (const unsigned char *)gaw_actor_context; }')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'memcpy(gaw_actor_context[gaw_fore_phase_count],work_ram+0x600,768);gaw_actor_context[gaw_fore_phase_count][768]=work_ram[0xa2];'+anchor)
 modified=source.encode();target=folder/'z80-actor-prefix-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_actorprefixrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/actor-prefix-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics load M1/R observer built; original core source restored.')
if __name__=='__main__':main()
