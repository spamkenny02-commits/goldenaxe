"""Capture wait-entry raster,interrupt latches and cost-relevant RAM/audio state."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/wait-raster-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes();source=(ROOT/'analysis/irq-raster-v0183/z80-irq-raster.txt').read_text()
 declaration='''
struct gaw_wait_entry { unsigned phase[12];unsigned char ram[336],sound[400]; };
static struct gaw_wait_entry gaw_wait_entries[8192];
__declspec(dllexport) const unsigned char *gaw_wait_entry_events(void) { return (const unsigned char *)gaw_wait_entries; }
static void gaw_wait_entry_observe(unsigned pc)
{
 struct gaw_wait_entry *e;
 if(pc!=0x0b95 || gaw_wait_count>=8192) return;
 e=gaw_wait_entries+gaw_wait_count;e->phase[0]=Z80.cycles;e->phase[1]=v_counter;e->phase[2]=mcycles_vdp;
 e->phase[3]=lines_per_frame;e->phase[4]=vc_max;e->phase[5]=interlaced;e->phase[6]=reg[1];e->phase[7]=system_hw;
 e->phase[8]=IFF1;e->phase[9]=Z80.after_ei;e->phase[10]=Z80.irq_state;e->phase[11]=reg[0];
 memcpy(e->ram,work_ram,80);memcpy(e->ram+80,work_ram+0x1d00,256);memcpy(e->sound,work_ram+0x1e00,400);
}
'''
 anchor='static void gaw_wait_observe(unsigned pc)';assert source.count(anchor)==1;source=source.replace(anchor,declaration+'\n'+anchor)
 anchor=' gaw_wait_observe(pc);';assert source.count(anchor)==1;modified=source.replace(anchor,' gaw_wait_entry_observe(pc);\n'+anchor,1).encode();target=folder/'z80-wait-raster.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_waitraster_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/wait-raster-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Wait-entry observer built; source restored.')
if __name__=='__main__':main()
