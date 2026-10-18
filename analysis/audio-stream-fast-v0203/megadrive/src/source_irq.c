#include "source_irq.h"
#ifdef SGDK_GCC
#include <memory.h>
#endif

static void copy_state(u8 *to,const u8 *from)
{
#ifdef SGDK_GCC
    memcpy(to,from,336);
#else
    __builtin_memcpy(to,from,336);
#endif
}

static u8 address_index(u16 address,u16 *index)
{
    if(address>=0xc000 && address<0xc050) {*index=address-0xc000;return 1;}
    if(address>=0xdd00 && address<0xde00) {*index=80+address-0xdd00;return 1;}
    return 0;
}

static u8 read(const u8 *state,u16 address,u8 *value)
{u16 index;if(!address_index(address,&index)) return 0;*value=state[index];return 1;}
static u8 write(u8 *state,u16 address,u8 value)
{u16 index;if(!address_index(address,&index)) return 0;state[index]=value;return 1;}

static void clear(SourceIrqOutput *output)
{
    u16 n;for(n=0;n<SOURCE_IRQ_STAGES;n++) output->stages[n].tstates=output->stages[n].fetches=0;
    output->whole.tstates=output->whole.fetches=0;output->palette_taken=output->reset_requested=0;
}

u8 source_irq(u8 *state,const SourceIrqInput *input,const SourceClockWork *reader,SourceIrqOutput *output)
{
    u8 old[336],value,bank,count_byte,height_byte,width_byte,previous,pause;
    u16 count,height,width,pointer,iy,guard,n;u32 t,m,loop,sample,period,prefix,target;
    clear(output);
    if((input->lines!=262 && input->lines!=313) || input->raster>=(u32)input->lines*3420 ||
       input->joy>63 || (input->reset_mask!=0 && input->reset_mask!=16)) return 0;
    if(!state[0x2e])
    {
        t=state[0x30]?454:442;m=state[0x30]?49:47;
        /* The audio-only path can reject before its sole RAM mutation.
         * It therefore needs no full rollback snapshot. */
        if(reader->tstates>0xffffffffUL-t-82 || reader->fetches>0xffffffffUL-m-7) return 0;
        if(state[0x30]) state[0x30]--;
        output->whole.tstates=82+t+reader->tstates;output->whole.fetches=7+m+reader->fetches;
        return 1;
    }
    copy_state(old,state);
    output->stages[SOURCE_IRQ_SAT64].tstates=27+10+10+3*(16+12)+7+13+4+11+7+11+7+10+17+64*16+10;
    output->stages[SOURCE_IRQ_SAT64].fetches=3+2+3*(2+2)+9+64*2+1;
    output->stages[SOURCE_IRQ_SAT128].tstates=4+11+4+11+17+128*16+10;
    output->stages[SOURCE_IRQ_SAT128].fetches=4+1+128*2+1;
    t=17;m=2;
    if(!state[0x42]) {t+=11;m++;}
    else
    {
        pointer=state[0x43]|((u16)state[0x44]<<8);
        if(state[0x42]>=16 || pointer>=0xc000 || !input->tile_count || input->tile_count>256) goto reject;
        count=input->tile_count;state[0x42]=0;
        t+=5+13+16+7+6+7+11+7+11+4+13+7+(u32)count*(24*16+8*11+4+10)+10;
        m+=12+(u32)count*(24*2+8+1+1)+1;
    }
    output->stages[SOURCE_IRQ_TILES].tstates=17+t;output->stages[SOURCE_IRQ_TILES].fetches=1+m;
    t=17;m=2;
    if(state[0x33]) {t+=11;m++;}
    else
    {
        t+=25;m+=3;
        if(!(state[0x45]&3)) {t+=11;m++;}
        else {state[0x45]=0;t+=5+4+4+7+11+4+7+11+4+13+7+7+13+10+60*16+10;m+=14+60*2+1;}
    }
    output->stages[SOURCE_IRQ_HUD].tstates=17+t;output->stages[SOURCE_IRQ_HUD].fetches=1+m;
    t=17;m=2;
    if(state[0x33]) {t+=12;m++;}
    else
    {
        prefix=13+4+7+10+13+4+(input->compensation?12:11);
        period=(u32)input->lines*3420;
        t=0;for(n=0;n<SOURCE_IRQ_PALETTE;n++) t+=output->stages[n].tstates;
        sample=(input->raster+(t+prefix+11)*15)%period;
        /* Each failed V-counter poll advances405 master ticks. The accepted
         * ranges are wider than one polling step, so ceil(distance/405)
         * gives the identical first successful read without emulating every
         * division. PAL has an additional accepted range before line243's
         * counter discontinuity. NTSC's counter wraps at line219. */
        if(input->lines==262) target=(input->compensation?230UL:246UL)*3420;
        else if(sample<243UL*3420) target=(input->compensation?224UL:240UL)*3420;
        else target=(input->compensation?281UL:297UL)*3420;
        guard=sample<target?(u16)((target-sample+404)/405):0;
        output->palette_taken=guard;
        t=prefix+(u32)guard*27+22+4+11+7+11+10+10+32*(16+13)-5;
        m+=4+(input->compensation?1:2)+(u32)guard*3+3+6+32*3;
    }
    output->stages[SOURCE_IRQ_PALETTE].tstates=t;output->stages[SOURCE_IRQ_PALETTE].fetches=m;
    pointer=state[0x34]|((u16)state[0x35]<<8);
    if(!write(state,pointer,0)) goto reject;
    t=40;m=4;iy=0xdd00;
    for(guard=0;guard<128;guard++)
    {
        if(!read(state,iy,&value)) goto reject;
        t+=36;m+=4;
        if(value==1)
        {
            if(!read(state,iy+1,&bank) || !read(state,iy+6,&count_byte)) goto reject;
            count=count_byte?count_byte:256;
            t+=7+19+11+19+11+19+19+19+4+10;m+=15;
            loop=(u32)count*(7+32*(16+13)-5+4+12)-5;
            if(bank&128) {t+=17+4+13+7+13+10+19+loop+10+15+17+13+7+13+4+10+12;m+=6+2+(u32)count*(1+32*3+1+1)+3+6+1;}
            else {t+=13+19+loop+10+15+12;m+=3+(u32)count*(1+32*3+1+1)+4;}
            iy+=7;
        }
        else if(!value)
        {
            t+=10+10+16+7+10;m+=5;state[0x34]=0;state[0x35]=0xdd;
            if(!write(state,0xdd00,0)) goto reject;
            break;
        }
        else
        {
            if(!read(state,iy+1,&height_byte) || !read(state,iy+2,&width_byte)) goto reject;
            height=height_byte?height_byte:256;width=(u8)(width_byte*2);if(!width) width=256;
            t+=10+7+19+19+(u32)height*(4+10+11+4+11+4+11+4+4+19+4+(u32)width*(16+4+10)+10+11+23+12)-5+10+15+10;
            m+=6+(u32)height*(12+(u32)width*4+5)+4;
            if(!write(state,iy+1,0)) goto reject;
            iy+=5;
        }
    }
    if(guard==128) goto reject;
    output->stages[SOURCE_IRQ_QUEUE].tstates=17+t;output->stages[SOURCE_IRQ_QUEUE].fetches=1+m;
    output->stages[SOURCE_IRQ_MAP_AUDIO].tstates=24;output->stages[SOURCE_IRQ_MAP_AUDIO].fetches=3;
    if(reader->tstates>0xffffffffUL-17 || reader->fetches>0xffffffffUL-1) goto reject;
    output->stages[SOURCE_IRQ_AUDIO].tstates=17+reader->tstates;output->stages[SOURCE_IRQ_AUDIO].fetches=1+reader->fetches;
    t=17;m=2;pause=0;
    if(state[0x1c]) {pause=1;state[0x1c]--;t+=31;m+=4;}
    else {t+=12;m++;}
    previous=state[0x22];state[0x22]=pause;state[0x23]=pause&~previous;
    previous=state[0x20];state[0x20]=input->joy;state[0x21]=input->joy&~previous;
    t+=10+4+7+7+6+4+7+11+4+7+10+4+7+7+6+4+7+11+7+10;
    m+=20;
    if(!input->reset_mask) output->reset_requested=1;
    else
    {
        t+=17;m+=2;
        if(state[0x30]) {state[0x30]--;t+=24;m+=3;}
        else {t+=12;m++;}
        state[0x2f]++;state[0x2e]=0;t+=10+11+4+13+10;m+=5;
    }
    output->stages[SOURCE_IRQ_POST_AUDIO].tstates=t;output->stages[SOURCE_IRQ_POST_AUDIO].fetches=m;
    output->whole.tstates=72+(output->reset_requested?0:10);output->whole.fetches=6+(output->reset_requested?0:1);
    for(n=0;n<SOURCE_IRQ_STAGES;n++)
    {
        if(output->stages[n].tstates>0xffffffffUL-output->whole.tstates ||
           output->stages[n].fetches>0xffffffffUL-output->whole.fetches) goto reject;
        output->whole.tstates+=output->stages[n].tstates;output->whole.fetches+=output->stages[n].fetches;
    }
    return 1;
reject:
    copy_state(state,old);clear(output);return 0;
}
