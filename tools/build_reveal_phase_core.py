"""Read-only phase/state checkpoints for original reveal foreground code."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/reveal-phase-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes();source=(ROOT/'analysis/wait-raster-v0183/z80-wait-raster.txt').read_text()
 declaration='''
struct gaw_fore_phase { unsigned long long pc,master;unsigned phase[12];unsigned char ram[336],sound[400]; };
static struct gaw_fore_phase gaw_fore_phases[32768];
static unsigned gaw_fore_phase_count;
__declspec(dllexport) unsigned gaw_foreground_phase_samples(void) { return gaw_fore_phase_count; }
__declspec(dllexport) const unsigned char *gaw_foreground_phase_events(void) { return (const unsigned char *)gaw_fore_phases; }
static void gaw_fore_phase_observe(unsigned pc)
{
 struct gaw_fore_phase *e;
 if(pc!=0x1fa7 && pc!=0x0aa4 && pc!=0x0bb3 && pc!=0x0ac0 && pc!=0x0ace) return;
 if(gaw_fore_phase_count>=32768) return;
 e=gaw_fore_phases+gaw_fore_phase_count++;e->pc=pc;e->master=gaw_elapsed;
 e->phase[0]=Z80.cycles;e->phase[1]=v_counter;e->phase[2]=mcycles_vdp;e->phase[3]=lines_per_frame;e->phase[4]=vc_max;
 e->phase[5]=interlaced;e->phase[6]=reg[1];e->phase[7]=system_hw;e->phase[8]=IFF1;e->phase[9]=Z80.after_ei;e->phase[10]=Z80.irq_state;e->phase[11]=reg[0];
 memcpy(e->ram,work_ram,80);memcpy(e->ram+80,work_ram+0x1d00,256);memcpy(e->sound,work_ram+0x1e00,400);
}
'''
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1;source=source.replace(anchor,anchor+declaration)
 anchor='gaw_full_count=gaw_full_active=gaw_full_nested=0;';assert source.count(anchor)==1;source=source.replace(anchor,'gaw_full_count=gaw_full_active=gaw_full_nested=gaw_fore_phase_count=0;')
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1;modified=source.replace(anchor,anchor+'\n gaw_fore_phase_observe(pc);',1).encode();target=folder/'z80-reveal-phase.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_revealphase_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/reveal-phase-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Reveal phase observer built;source restored.')
if __name__=='__main__':main()
