"""Observe original RNG R samples/output without altering the source CPU state."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/rng-refresh-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/map-hud-phase-research-v0183/z80-map-hud-phase.txt').read_text()
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 declaration='''
static unsigned long long gaw_rng_refresh[32768][8];
static unsigned gaw_rng_refresh_count;
__declspec(dllexport) unsigned gaw_rng_refresh_samples(void) { return gaw_rng_refresh_count; }
__declspec(dllexport) const unsigned long long *gaw_rng_refresh_events(void) { return &gaw_rng_refresh[0][0]; }
static void gaw_rng_refresh_observe(unsigned pc) {
 unsigned long long *e;
 if(pc!=0x4e1 && pc!=0x4f7 && pc!=0x4fd) return;
 if(gaw_rng_refresh_count>=32768) return;
 e=gaw_rng_refresh[gaw_rng_refresh_count++];e[0]=pc;e[1]=gaw_elapsed;e[2]=gaw_irq_elapsed;
 e[3]=work_ram[0x28]|(work_ram[0x29]<<8);e[4]=HLD;e[5]=A;e[6]=(R&127)|R2;e[7]=work_ram[0]|(work_ram[1]<<8);
}
'''
 source=source.replace(anchor,anchor+declaration)
 anchor='gaw_fore_phase_count=0;';assert source.count(anchor)==1;source=source.replace(anchor,'gaw_fore_phase_count=gaw_rng_refresh_count=0;')
 anchor=' gaw_fore_phase_observe(pc);';assert source.count(anchor)==1;source=source.replace(anchor,anchor+'\n gaw_rng_refresh_observe(pc);')
 modified=source.encode();target=folder/'z80-rng-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_rngrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/rng-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('RNG refresh observer built; original core source restored.')
if __name__=='__main__':main()
