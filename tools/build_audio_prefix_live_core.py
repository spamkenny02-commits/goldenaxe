"""Capture original tempo/fade helper inputs,outputs and wall costs during play."""
import subprocess,sys
from actor_reference import ROOT

def main(arbitration=False):
 folder=ROOT/('analysis/audio-arbitration-v0180' if arbitration else 'analysis/audio-prefix-v0180');folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-irq-v0180/z80-audio-irq.txt').read_text()
 declarations='''
struct gaw_live_prefix_record { unsigned kind,cost;unsigned char before[400],after[400]; };
static struct gaw_live_prefix_record gaw_live_prefix_records[4096];
static unsigned gaw_live_prefix_count,gaw_live_prefix_active;
static unsigned long long gaw_live_prefix_start;
__declspec(dllexport) unsigned gaw_live_prefix_samples(void) { return gaw_live_prefix_count; }
__declspec(dllexport) const unsigned char *gaw_live_prefix_events(void) { return (const unsigned char *)gaw_live_prefix_records; }
static void gaw_live_prefix_observe(unsigned pc)
{
  struct gaw_live_prefix_record *e;
  if(work_ram[0x1fff]!=6 || gaw_live_prefix_count>=4096) return;
  e=gaw_live_prefix_records+gaw_live_prefix_count;
  if(pc==0x807e || pc==0x80c8) {
    e->kind=(pc==0x80c8);gaw_live_prefix_active=e->kind+1;
    gaw_live_prefix_start=gaw_elapsed;memcpy(e->before,work_ram+0x1e00,400);
  }
  if((pc==0x8012 && gaw_live_prefix_active==1) || (pc==0x8015 && gaw_live_prefix_active==2)) {
    e->cost=(gaw_elapsed-gaw_live_prefix_start)/15;
    memcpy(e->after,work_ram+0x1e00,400);gaw_live_prefix_active=0;gaw_live_prefix_count++;
  }
}
'''
 if arbitration:
  declarations=declarations.replace('pc==0x807e || pc==0x80c8','pc==0x807e || pc==0x80c8 || pc==0x8097')
  declarations=declarations.replace('e->kind=(pc==0x80c8);','e->kind=pc==0x8097?2:(pc==0x80c8);')
  declarations=declarations.replace('(pc==0x8015 && gaw_live_prefix_active==2)', '(pc==0x8015 && gaw_live_prefix_active==2) || (pc==0x800f && gaw_live_prefix_active==3)')
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+declarations)
 anchor='gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=gaw_audio_count=0;';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=gaw_audio_count=gaw_live_prefix_count=gaw_live_prefix_active=0;',1)
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1
 modified=source.replace(anchor,anchor+'\n  gaw_live_prefix_observe(pc);',1).encode()
 target=folder/'z80-live-prefix.txt'
 if target.exists():assert target.read_bytes()==modified
 else:
  with target.open('xb') as f:f.write(modified)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_arbitration_libretro.dll' if arbitration else 'genesis_plus_gx_liveprefix_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/('validation/audio-arbitration-live-core-build.log' if arbitration else 'validation/audio-prefix-live-core-build.log')).write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only live prefix core built.')

if __name__=='__main__':main('--arbitration' in sys.argv)
