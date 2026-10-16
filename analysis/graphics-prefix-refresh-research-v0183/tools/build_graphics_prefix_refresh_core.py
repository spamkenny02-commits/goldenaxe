"""Observe global M1 and logical R at original foreground prefix checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/graphics-prefix-refresh-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/graphics-prefix-phase-v0183/z80-graphics-prefix-phase.txt').read_text()
 anchor='#define R Z80.r';assert source.count(anchor)==1;source=source.replace(anchor,'static unsigned long long gaw_M1_fetches;\n'+anchor)
 assert source.count('R++;')==5;source=source.replace('R++;','R++;gaw_M1_fetches++;')
 anchor='R += (cycles / cyclesum) * opcodes;';assert source.count(anchor)==1;source=source.replace(anchor,anchor+'gaw_M1_fetches += (cycles / cyclesum) * opcodes;')
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
struct gaw_fore_M1 { unsigned long long fetches;unsigned refresh,pad; };
static struct gaw_fore_M1 gaw_fore_M1_records[32768];
__declspec(dllexport) const unsigned char *gaw_foreground_m1_events(void) { return (const unsigned char *)gaw_fore_M1_records; }
''')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_fore_M1_records[gaw_fore_phase_count].fetches=gaw_M1_fetches;gaw_fore_M1_records[gaw_fore_phase_count].refresh=(R&127)|R2;'+anchor)
 modified=source.encode();target=folder/'z80-graphics-prefix-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_graphicsprefixrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/graphics-prefix-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics prefix M1/R observer built; original core source restored.')
if __name__=='__main__':main()
