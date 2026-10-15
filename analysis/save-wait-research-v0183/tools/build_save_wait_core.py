"""Read-only original0B95 wait-loop counts alongside full reader observations."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/save-wait-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-reader-complete-live-v0183/z80-live-reader.txt').read_text()
 declaration='''
static unsigned gaw_wait_count,gaw_wait_active,gaw_wait_nested;
static unsigned long long gaw_wait_records[8192][14];
__declspec(dllexport) unsigned gaw_wait_samples(void) { return gaw_wait_count; }
__declspec(dllexport) unsigned gaw_wait_nested_calls(void) { return gaw_wait_nested; }
__declspec(dllexport) const unsigned long long *gaw_wait_events(void) { return &gaw_wait_records[0][0]; }
static void gaw_wait_observe(unsigned pc)
{
 unsigned long long *e=gaw_wait_records[gaw_wait_count];
 if(gaw_wait_count>=8192) return;
 if(pc==0x0b95) {
  if(gaw_wait_active) gaw_wait_nested++;
  memset(e,0,14*sizeof(*e));e[0]=gaw_elapsed;e[1]=gaw_irq_elapsed;
  e[6]=work_ram[0x2e];e[8]=work_ram[0x2f];e[10]=SP;gaw_wait_active=1;
 }
 if(!gaw_wait_active) return;
 if(pc==0x0bac) { e[12]=gaw_elapsed;e[13]=gaw_irq_elapsed; }
 if(pc==0x0bb1) e[A ? 4 : 5]++;
 if(pc==0x0bb3) {
  e[2]=gaw_elapsed;e[3]=gaw_irq_elapsed;e[7]=work_ram[0x2e];e[9]=work_ram[0x2f];e[11]=SP;
  gaw_wait_active=0;gaw_wait_count++;
 }
}
'''
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1;source=source.replace(anchor,anchor+declaration)
 anchor='gaw_audio_count=gaw_live_envelope_count=gaw_live_envelope_active=0;';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_audio_count=gaw_live_envelope_count=gaw_live_envelope_active=gaw_wait_count=gaw_wait_active=gaw_wait_nested=0;')
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1
 modified=source.replace(anchor,anchor+'\n gaw_wait_observe(pc);',1).encode();target=folder/'z80-save-wait.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_savewait_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/save-wait-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Original wait observer built; emulator source restored.')
if __name__=='__main__':main()
