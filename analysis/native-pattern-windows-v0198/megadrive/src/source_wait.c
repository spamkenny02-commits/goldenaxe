#include "source_wait.h"

u8 source_wait(SourceClock *clock,SourceIrqContext *context,SourceWaitOutput *output)
{
    static const u8 prefix[]={11,11,11,11,4,4,11,11,11,11,15,15,13,11,7,13,4};
    u16 n,guard,batch;u8 value=0;
    output->taken=output->error=0;
    if(clock->period!=(u32)context->input.lines*3420) {output->error=1;return 0;}
    for(n=0;n<17;n++)
    {
        if(!source_clock_execute(clock,prefix[n],(n==10 || n==11)?2:1,
                                  n==16?SOURCE_CLOCK_EI:SOURCE_CLOCK_NONE,source_irq_interrupt,context)) goto reject;
        if(n==14) value=1;
        if(n==15) context->ram[0x2e]=value;
    }
    for(guard=0;guard<8192;guard++)
    {
        if(context->ram[0x2e])
        {
            batch=source_clock_repeat(clock,29,3,8192-guard);
            if(batch) {output->taken+=batch;guard+=batch-1;continue;}
        }
        if(!source_clock_execute(clock,13,1,SOURCE_CLOCK_NONE,source_irq_interrupt,context)) goto reject;
        value=context->ram[0x2e];
        if(!source_clock_execute(clock,4,1,SOURCE_CLOCK_NONE,source_irq_interrupt,context)) goto reject;
        if(!source_clock_execute(clock,value?12:7,1,SOURCE_CLOCK_NONE,source_irq_interrupt,context)) goto reject;
        if(value) output->taken++;
        else
        {
            if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) goto reject;
            return 1;
        }
    }
reject:
    output->error=1;return 0;
}
