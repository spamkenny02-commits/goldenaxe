"""Read-only400-byte helper snapshots and costs for original bank6 unit fixtures."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-prefix-v0180';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/hero-init-v0177/z80-hero-snapshots.txt').read_text()
 declarations='''
static unsigned char gaw_prefix_before[400],gaw_prefix_after[400];
static unsigned gaw_prefix_count;
static unsigned long long gaw_prefix_start,gaw_prefix_cost;
__declspec(dllexport) unsigned gaw_prefix_samples(void) { return gaw_prefix_count; }
__declspec(dllexport) const unsigned char *gaw_prefix_entry(void) { return gaw_prefix_before; }
__declspec(dllexport) const unsigned char *gaw_prefix_return(void) { return gaw_prefix_after; }
__declspec(dllexport) unsigned long long gaw_prefix_tstates(void) { return gaw_prefix_cost; }
'''
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+declarations)
 source=source.replace('gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=0;','gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=gaw_prefix_count=0;',1)
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1
 hook='''
  if(pc==0x3000) { memcpy(gaw_prefix_before,work_ram+0x1e00,400);gaw_prefix_start=gaw_elapsed; }
  if(pc==0x3003) { memcpy(gaw_prefix_after,work_ram+0x1e00,400);gaw_prefix_cost=(gaw_elapsed-gaw_prefix_start)/15-17;gaw_prefix_count++; }
'''
 modified=source.replace(anchor,anchor+hook,1).encode()
 target=folder/'z80-prefix-snapshots.txt'
 if target.exists():assert target.read_bytes()==modified
 else:
  with target.open('xb') as f:f.write(modified)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_prefix_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-prefix-core-build.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only original audio helper snapshot core built.')

if __name__=='__main__':main()
