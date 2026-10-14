"""Observe original gated IRQ/audio costs without altering emulated instructions."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-irq-v0180';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/hero-init-v0177/z80-hero-snapshots.txt').read_text()
 declarations='''
static unsigned gaw_audio_count;
static unsigned long long gaw_audio_events[32768][14];
__declspec(dllexport) unsigned gaw_audio_irq_count(void) { return gaw_audio_count; }
__declspec(dllexport) const unsigned long long *gaw_audio_irq_events(void) { return &gaw_audio_events[0][0]; }
static void gaw_audio_observe(unsigned pc)
{
  unsigned long long *e;
  if(pc!=0x0137 && pc!=0x01e3 && pc!=0x0202 && pc!=0x0205 && pc!=0x0226 && pc!=0x01a2 && pc!=0x01a5 && pc!=0x01e2) return;
  if(gaw_audio_count>=32768) return;
  e=gaw_audio_events[gaw_audio_count++];
  e[0]=pc;e[1]=gaw_elapsed;e[2]=gaw_irq_elapsed;e[3]=SP;
  e[4]=work_ram[0x2e];e[5]=work_ram[0x2f];e[6]=work_ram[0x30];
  e[7]=work_ram[0x65];e[8]=work_ram[0x1e06];
  e[9]=work_ram[0x1e0b];e[10]=work_ram[0x1e0c];e[11]=work_ram[0x1e0d];
  e[12]=work_ram[0x1fff];e[13]=work_ram[0x1e03];
}
'''
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+declarations)
 source=source.replace('gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=0;','gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=gaw_audio_count=0;',1)
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1
 modified=source.replace(anchor,anchor+'\n  gaw_audio_observe(pc);',1).encode()
 for name,data in [('z80-before-audio.txt',original),('z80-audio-irq.txt',modified)]:
  target=folder/name
  if target.exists():assert target.read_bytes()==data
  else:
   with target.open('xb') as f:f.write(data)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_audioirq_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-irq-core-build.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only audio IRQ timing core built;working emulator source restored.')

if __name__=='__main__':main()
