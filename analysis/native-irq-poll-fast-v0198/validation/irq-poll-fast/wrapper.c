#include "source_irq.h"
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
