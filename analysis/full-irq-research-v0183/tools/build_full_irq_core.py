"""Read-only full gatedIRQ stages,palette-loop decisions and bounded RAM snapshots."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/full-irq-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/save-wait-v0183/z80-save-wait.txt').read_text()
 declaration='''
struct gaw_full_record { unsigned long long points[12];unsigned values[8];unsigned char before[336],after[336]; };
static struct gaw_full_record gaw_full_records[8192];
static unsigned gaw_full_count,gaw_full_active,gaw_full_nested;
__declspec(dllexport) unsigned gaw_full_irq_samples(void) { return gaw_full_count; }
__declspec(dllexport) unsigned gaw_full_irq_nested(void) { return gaw_full_nested; }
__declspec(dllexport) const unsigned char *gaw_full_irq_records(void) { return (const unsigned char *)gaw_full_records; }
static void gaw_full_observe(unsigned pc)
{
 struct gaw_full_record *e=gaw_full_records+gaw_full_count;
 if(gaw_full_count>=8192) return;
 if(pc==0x0137 && work_ram[0x2e]) {
  if(gaw_full_active) gaw_full_nested++;
  memset(e,0,sizeof(*e));gaw_full_active=1;e->points[0]=gaw_elapsed;e->points[1]=gaw_irq_elapsed;e->points[11]=SP;
  e->values[4]=work_ram[0x1e03];e->values[5]=work_ram[0x1ffc];
  memcpy(e->before,work_ram,80);memcpy(e->before+80,work_ram+0x1d00,256);
 }
 if(!gaw_full_active) return;
 switch(pc) {
 case 0x0164:e->points[2]=gaw_elapsed;break;
 case 0x016d:e->points[3]=gaw_elapsed;break;
 case 0x0170:e->points[4]=gaw_elapsed;break;
 case 0x0173:e->points[5]=gaw_elapsed;break;
 case 0x0186:e->values[A<H ? 0 : 1]++;break;
 case 0x0199:e->points[6]=gaw_elapsed;break;
 case 0x019c:e->points[7]=gaw_elapsed;break;
 case 0x01a2:e->points[8]=gaw_elapsed;break;
 case 0x01a5:e->points[9]=gaw_elapsed;break;
 case 0x01bf:e->values[2]=A;break;
 case 0x01cc:e->values[3]=A;break;
 case 0x01e2:
  e->points[10]=gaw_elapsed;e->points[11]|=(unsigned long long)SP<<16;e->values[6]=work_ram[0x1ffc];
  memcpy(e->after,work_ram,80);memcpy(e->after+80,work_ram+0x1d00,256);gaw_full_active=0;gaw_full_count++;break;
 }
}
'''
 anchor='static unsigned gaw_irq_sp[32];';assert source.count(anchor)==1;source=source.replace(anchor,anchor+declaration)
 anchor='gaw_wait_count=gaw_wait_active=gaw_wait_nested=0;';assert source.count(anchor)==1;source=source.replace(anchor,'gaw_wait_count=gaw_wait_active=gaw_wait_nested=gaw_full_count=gaw_full_active=gaw_full_nested=0;')
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1;modified=source.replace(anchor,anchor+'\n gaw_full_observe(pc);',1).encode();target=folder/'z80-full-irq.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_fullirq_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/full-irq-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Full gatedIRQ observer built;emulator source restored.')
if __name__=='__main__':main()
