#include <genesis.h>
#include "../../../../megadrive/src/source_irq.h"
#include "expected.h"
volatile u32 gaw_irq_cases,gaw_irq_failures;
volatile u16 gaw_irq_done;
int main(bool hard_reset)
{
 u32 row;u16 n;u8 state[336],accepted;SourceIrqOutput output;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) state[n]=cases[row].before[n];
  accepted=source_irq(state,&cases[row].input,&cases[row].reader,&output);
  if(!accepted || output.palette_taken!=cases[row].output.palette_taken || output.reset_requested ||
     output.whole.tstates!=cases[row].output.whole.tstates || output.whole.fetches!=cases[row].output.whole.fetches) gaw_irq_failures++;
  for(n=0;n<SOURCE_IRQ_STAGES;n++)
   if(output.stages[n].tstates!=cases[row].output.stages[n].tstates || output.stages[n].fetches!=cases[row].output.stages[n].fetches) gaw_irq_failures++;
  for(n=0;n<336;n++) if(state[n]!=cases[row].after[n]) gaw_irq_failures++;
  gaw_irq_cases++;
 }
 gaw_irq_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
