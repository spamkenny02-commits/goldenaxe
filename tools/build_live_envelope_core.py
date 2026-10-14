"""Observe original854B input/output and direct reader returns after unwind."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-envelope-live-v0180';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-irq-v0180/z80-audio-irq.txt').read_text()
 declarations='''
struct gaw_envelope_record { unsigned ix,de_before,de_after,a,cost,unwind;unsigned char before[400],after[400]; };
static struct gaw_envelope_record gaw_envelope_records[8192];
static unsigned gaw_live_envelope_count,gaw_live_envelope_active;
static unsigned long long gaw_live_envelope_start;
__declspec(dllexport) unsigned gaw_live_envelope_samples(void) { return gaw_live_envelope_count; }
__declspec(dllexport) const unsigned char *gaw_live_envelope_events(void) { return (const unsigned char *)gaw_envelope_records; }
static void gaw_live_envelope_observe(unsigned pc)
{
  struct gaw_envelope_record *e;
  if(work_ram[0x1fff]!=6 || gaw_live_envelope_count>=8192) return;
  e=gaw_envelope_records+gaw_live_envelope_count;
  if(pc==0x854b) {
    e->ix=IXD;e->de_before=DED;gaw_live_envelope_active=1;
    gaw_live_envelope_start=gaw_elapsed;memcpy(e->before,work_ram+0x1e00,400);
  }
  if(gaw_live_envelope_active && (pc==0x8530 || pc==0x803b || pc==0x8046 || pc==0x8051 || pc==0x805c || pc==0x8067 || pc==0x8072 || pc==0x807d)) {
    e->de_after=DED;e->a=A;e->cost=(gaw_elapsed-gaw_live_envelope_start)/15;e->unwind=(pc!=0x8530);
    memcpy(e->after,work_ram+0x1e00,400);gaw_live_envelope_active=0;gaw_live_envelope_count++;
  }
}
'''
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+declarations)
 anchor='gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=gaw_audio_count=0;';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=gaw_audio_count=gaw_live_envelope_count=gaw_live_envelope_active=0;',1)
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1
 modified=source.replace(anchor,anchor+'\n  gaw_live_envelope_observe(pc);',1).encode();target=folder/'z80-live-envelopes.txt'
 if target.exists():assert target.read_bytes()==modified
 else:
  with target.open('xb') as f:f.write(modified)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_liveenvelope_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-envelope-live-core-build.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only original live envelope core built.')

if __name__=='__main__':main()
