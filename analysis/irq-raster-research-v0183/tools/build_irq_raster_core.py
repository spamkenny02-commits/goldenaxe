"""Read-only raster phase at each completed fullIRQ,without VCounter function calls."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/irq-raster-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes();source=(ROOT/'analysis/full-irq-v0183/z80-full-irq.txt').read_text()
 declaration='''
static unsigned gaw_irq_phases[8192][8];
__declspec(dllexport) const unsigned *gaw_irq_phase_events(void) { return &gaw_irq_phases[0][0]; }
static void gaw_irq_phase_observe(unsigned pc)
{
 unsigned *e;
 if(pc!=0x0137 || !work_ram[0x2e] || gaw_full_count>=8192) return;
 e=gaw_irq_phases[gaw_full_count];e[0]=Z80.cycles;e[1]=v_counter;e[2]=mcycles_vdp;
 e[3]=lines_per_frame;e[4]=vc_max;e[5]=interlaced;e[6]=reg[1];e[7]=system_hw;
}
'''
 anchor='static void gaw_full_observe(unsigned pc)';assert source.count(anchor)==1;source=source.replace(anchor,declaration+'\n'+anchor)
 anchor=' gaw_full_observe(pc);';assert source.count(anchor)==1;modified=source.replace(anchor,' gaw_irq_phase_observe(pc);\n'+anchor,1).encode();target=folder/'z80-irq-raster.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_irqraster_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/irq-raster-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Raster-phase observer built; emulator source restored.')
if __name__=='__main__':main()
