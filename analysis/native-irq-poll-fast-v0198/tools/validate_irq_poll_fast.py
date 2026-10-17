"""Every input raster tick and V-counter threshold versus immutable scalar IRQ."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
WRAPPER='''#include "source_irq.h"
u8 scalar_irq(u8*,const SourceIrqInput*,const SourceClockWork*,SourceIrqOutput*);
u32 sweep(u16 lines,u8 compensation,u32 *bad)
{
 u32 raster,n,period=(u32)lines*3420,cases=0;u8 a[336],b[336];
 SourceIrqInput input={0};SourceClockWork reader={123,45};SourceIrqOutput oa,ob;
 input.lines=lines;input.compensation=compensation;input.reset_mask=16;
 for(raster=0;raster<period;raster++)
 {
  input.raster=raster;
  for(n=0;n<336;n++) a[n]=b[n]=0;
  a[0x2e]=b[0x2e]=1;a[0x35]=b[0x35]=0xdd;
  if(!source_irq(a,&input,&reader,&oa) || !scalar_irq(b,&input,&reader,&ob)) {*bad=raster;return 0;}
  for(n=0;n<336;n++) if(a[n]!=b[n]) {*bad=raster;return 0;}
  for(n=0;n<SOURCE_IRQ_STAGES;n++) if(oa.stages[n].tstates!=ob.stages[n].tstates || oa.stages[n].fetches!=ob.stages[n].fetches) {*bad=raster;return 0;}
  if(oa.whole.tstates!=ob.whole.tstates || oa.whole.fetches!=ob.whole.fetches || oa.palette_taken!=ob.palette_taken || oa.reset_requested!=ob.reset_requested) {*bad=raster;return 0;}
  cases++;
 }
 return cases;
}
'''
def main():
 base=ROOT/'validation/irq-poll-fast';base.mkdir(exist_ok=True)
 reference=ROOT/'analysis/native-command-batching-v0198/megadrive/src/source_irq.c'
 (base/'reference.c').write_text(reference.read_text().replace('u8 source_irq(','u8 scalar_irq('));(base/'wrapper.c').write_text(WRAPPER)
 sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(base/'reference.c'),str(base/'wrapper.c'),str(ROOT/'megadrive/src/source_irq.c'),'-o',str(base/'sweep.dll')],env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
 dll=c.CDLL(str(base/'sweep.dll'));fn=dll.sweep;fn.argtypes=[c.c_uint16,c.c_uint8,c.POINTER(c.c_uint32)];fn.restype=c.c_uint32;rows=[]
 for lines in [262,313]:
  for compensation in [0,128]:
   bad=c.c_uint32();cases=fn(lines,compensation,c.byref(bad));assert cases==lines*3420,(lines,compensation,bad.value)
   rows.append(dict(lines=lines,compensation=compensation,cases=cases));print(rows[-1],flush=True)
 report=dict(rows=rows,cases=sum(r['cases'] for r in rows),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq.c').read_bytes()).hexdigest(),limits=['Host exact state,all nine T/M1 stages,total work,palette polling count,reset flag for every raster master tick in PAL/NTSC with both threshold modes. One valid full IRQ queue state.','Original SMS stage vectors and compiled68000 runs are independent checks; no hardware timing claim.'])
 (ROOT/'analysis/irq_poll_fast_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
