"""Read-only original hero entry/return RAM snapshots; restore working source."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/hero-init-v0177';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/transition-timing-v0176/z80-transition-markers.txt').read_text()
 declarations='''static unsigned char gaw_hero_before[8192],gaw_hero_after[8192];
static unsigned gaw_hero_active,gaw_hero_count;
__declspec(dllexport) const unsigned char *gaw_hero_entry(void) { return gaw_hero_before; }
__declspec(dllexport) const unsigned char *gaw_hero_return(void) { return gaw_hero_after; }
__declspec(dllexport) unsigned gaw_hero_samples(void) { return gaw_hero_count; }
'''
 source=source.replace('static unsigned gaw_irq_active, gaw_event_count;',declarations+'static unsigned gaw_irq_active, gaw_event_count;',1)
 source=source.replace('gaw_event_count=gaw_irq_active=0;','gaw_event_count=gaw_irq_active=gaw_hero_count=gaw_hero_active=0;',1)
 anchor='static void gaw_timing_observe(unsigned pc)\n{'
 hook='''
  if(pc==0x2c63) { memcpy(gaw_hero_before,work_ram,8192);gaw_hero_active=1; }
  if(pc==0x24e7 && gaw_hero_active) { memcpy(gaw_hero_after,work_ram,8192);gaw_hero_active=0;gaw_hero_count++; }
'''
 assert source.count(anchor)==1;modified=source.replace(anchor,anchor+hook,1).encode()
 for name,data in [('z80-before-hero.txt',original),('z80-hero-snapshots.txt',modified)]:
  target=folder/name
  if target.exists():assert target.read_bytes()==data
  else:
   with target.open('xb') as handle:handle.write(data)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_hero_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/hero-core-build.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only hero timing core built;working source restored.')

if __name__=='__main__':main()
