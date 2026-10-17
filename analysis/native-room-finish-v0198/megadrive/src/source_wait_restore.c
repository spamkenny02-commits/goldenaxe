#include "source_wait_restore.h"

u8 source_wait_restore(SourceClock *clock,SourceIrqContext *context)
{
    static const u8 ticks[]={10,13,14,14,10,10,10,10,4,4,10,10,10,10,10};
    u16 n;
    if(clock->period!=(u32)context->input.lines*3420) return 0;
    for(n=0;n<15;n++)
        if(!source_clock_execute(clock,ticks[n],(n==2 || n==3)?2:1,SOURCE_CLOCK_NONE,
                                  source_irq_interrupt,context)) return 0;
    return source_clock_checkpoint(clock,source_irq_interrupt,context);
}

u8 source_wait_complete(SourceClock *clock,SourceIrqContext *context,SourceWaitOutput *output)
{
    if(!source_wait(clock,context,output)) return 0;
    if(source_wait_restore(clock,context)) return 1;
    output->error=1;return 0;
}
